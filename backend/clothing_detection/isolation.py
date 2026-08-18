"""Garment Isolation & Preprocessing Engine for Digital Wardrobe.

Isolates clothing items from user-uploaded images containing human models or complex backgrounds.
Produces a clean garment-only image on a transparent background for Virtual Try-On, preserving
all original garment colors, shapes, patterns, sleeves, hoods, collars, buttons, and hems.

Pipeline:
    1. Run YOLO segmentation → pixel-accurate mask at original resolution
    2. Light mask cleanup (fill tiny holes, remove tiny blobs)
    3. Apply mask to original image → RGBA with transparent background
    4. Validate mask integrity (not fragmented, covers reasonable area)
    5. Crop to garment bounding box with padding → save clean transparent PNG
"""

from __future__ import annotations

import os
import logging
import uuid
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageOps
from django.conf import settings

from .detector import ClothingDetector

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category mapping: detector canonical label → WardrobeItem.CATEGORY_CHOICES
# ---------------------------------------------------------------------------
DETECTOR_CATEGORY_TO_WARDROBE_CATEGORY: dict[str, str] = {
    # Tops
    "Shirt": "top",
    "T-Shirt": "top",
    "Hoodie": "top",
    "Sweater": "top",
    # Outerwear (treated as separate category)
    "Jacket": "outerwear",
    "Blazer": "outerwear",
    # Bottoms
    "Jeans": "bottom",
    "Pants": "bottom",
    "Shorts": "bottom",
    # Skirt
    "Skirt": "bottom",
    # Full body
    "Dress": "dress",
    # Footwear
    "Shoes": "footwear",
    "Sneakers": "footwear",
    "Sandals": "footwear",
    # Headwear
    "Cap": "headwear",
    "Hat": "headwear",
    # Accessories
    "Belt": "accessory",
    "Bag": "bag",
}

# Categories that are "top" type — used for garment-specific validation
TOP_CATEGORIES = {"Shirt", "T-Shirt", "Hoodie", "Sweater"}
BOTTOM_CATEGORIES = {"Jeans", "Pants", "Shorts", "Skirt"}
DRESS_CATEGORIES = {"Dress"}
OUTERWEAR_CATEGORIES = {"Jacket", "Blazer"}


def _cleanup_mask(mask: np.ndarray, min_blob_ratio: float = 0.01) -> np.ndarray:
    """Light mask cleanup: fill small holes and remove tiny disconnected blobs.

    Args:
        mask: Binary mask (uint8, 0 or 1).
        min_blob_ratio: Blobs smaller than this fraction of the largest blob are removed.

    Returns:
        Cleaned binary mask (uint8, 0 or 1).
    """
    if mask.sum() == 0:
        return mask

    # 1. Morphological close to fill tiny aliasing gaps (3×3 kernel, 1 iteration)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(mask * 255, cv2.MORPH_CLOSE, kernel, iterations=1)

    # 2. Fill small interior holes using flood-fill approach
    # Invert, find external contours (these are holes), fill small ones
    filled = closed.copy()
    contours_holes, _ = cv2.findContours(
        255 - filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    total_mask_area = float(np.count_nonzero(filled))
    if total_mask_area > 0:
        for cnt in contours_holes:
            hole_area = cv2.contourArea(cnt)
            if hole_area < total_mask_area * 0.05:  # fill holes < 5% of mask
                cv2.drawContours(filled, [cnt], -1, 255, cv2.FILLED)

    # 3. Remove tiny disconnected blobs
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(filled, connectivity=8)
    if num_labels <= 1:
        return (filled > 127).astype(np.uint8)

    # Find the largest component (excluding background label 0)
    areas = stats[1:, cv2.CC_STAT_AREA]
    max_area = areas.max()
    threshold_area = max_area * min_blob_ratio

    clean = np.zeros_like(filled)
    for label_id in range(1, num_labels):
        if stats[label_id, cv2.CC_STAT_AREA] >= threshold_area:
            clean[labels == label_id] = 255

    result = (clean > 127).astype(np.uint8)
    logger.debug(
        "Mask cleanup: %d components found, %d kept (threshold=%d px)",
        num_labels - 1,
        np.count_nonzero(np.unique(labels[clean > 127])),
        int(threshold_area),
    )
    return result


def _validate_mask(
    mask: np.ndarray,
    bbox: list[float],
    category: str,
    min_coverage: float = 0.15,
    max_components: int = 5,
) -> tuple[bool, str]:
    """Validate that the segmentation mask is not fragmented or too small.

    Args:
        mask: Binary mask (uint8, 0 or 1).
        bbox: [x1, y1, x2, y2] bounding box from YOLO.
        category: Detected canonical category name.
        min_coverage: Minimum fraction of bbox area that mask must cover.
        max_components: Maximum allowed connected components.

    Returns:
        (is_valid, reason_if_invalid)
    """
    mask_pixels = int(mask.sum())
    if mask_pixels < 500:
        return False, f"Segmentation mask too small ({mask_pixels} pixels)"

    # Check coverage relative to bounding box
    x1, y1, x2, y2 = bbox
    bbox_area = (x2 - x1) * (y2 - y1)
    if bbox_area > 0:
        coverage = mask_pixels / bbox_area
        if coverage < min_coverage:
            return False, (
                f"Garment mask covers only {coverage:.1%} of the detection bounding box "
                f"(minimum {min_coverage:.0%} required). The garment may be fragmented."
            )
        logger.info("  Mask coverage: %.1f%% of bbox area", coverage * 100)

    # Check connected components
    mask_255 = (mask * 255).astype(np.uint8)
    num_labels, _, _, _ = cv2.connectedComponentsWithStats(mask_255, connectivity=8)
    num_components = num_labels - 1  # exclude background
    if num_components > max_components:
        return False, (
            f"Garment mask is severely fragmented ({num_components} disconnected pieces). "
            f"Please upload a clearer image."
        )
    logger.info("  Mask components: %d (max allowed: %d)", num_components, max_components)

    return True, ""


def isolate_garment(image_input: str | Path | Any) -> tuple[bool, str, str | None, str | None]:
    """Isolate garment from uploaded image, removing person body & background.

    Uses YOLO segmentation mask as the primary garment boundary. No rembg.
    No aggressive skin removal. Validates mask integrity before saving.

    Args:
        image_input: Path to uploaded image file.

    Returns:
        tuple of (success, message, clean_image_path, detected_wardrobe_category)
    """
    image_path = str(image_input)
    if not os.path.exists(image_path):
        return (
            False,
            "Could not process the uploaded image. File does not exist.",
            None,
            None,
        )

    # ── 1. Run YOLO clothing detector ────────────────────────────────
    detector = ClothingDetector.get_instance()
    try:
        detections = detector.detect(image_path)
    except Exception as exc:
        logger.warning("YOLO detection failed on %s: %s", image_path, exc)
        return (
            False,
            "Clothing detection failed. Please try again with a different image.",
            None,
            None,
        )

    # Filter by minimum confidence
    min_confidence = 0.30
    valid_detections = [d for d in detections if d.get("confidence", 0) >= min_confidence]

    if not valid_detections:
        logger.warning(
            "No clothing detected with confidence >= %.2f in %s (raw detections: %d)",
            min_confidence, image_path, len(detections),
        )
        return (
            False,
            "Could not detect any clothing item in the uploaded photo. "
            "Please upload a clear image of a single garment.",
            None,
            None,
        )

    # Pick the detection with highest confidence
    primary_det = max(valid_detections, key=lambda x: x["confidence"])
    detected_category = primary_det["category"]
    raw_label = primary_det.get("raw_label", "unknown")
    confidence = primary_det["confidence"]
    wardrobe_category = DETECTOR_CATEGORY_TO_WARDROBE_CATEGORY.get(detected_category)

    logger.info(
        "Primary detection: raw_label=%r → category=%s → wardrobe=%s (conf=%.4f)",
        raw_label, detected_category, wardrobe_category, confidence,
    )

    # ── 2. Verify we have a segmentation mask ────────────────────────
    mask_data = primary_det.get("mask_data")
    if mask_data is None:
        logger.warning("No segmentation mask available for detection in %s", image_path)
        return (
            False,
            "The clothing detection model could not produce a segmentation mask. "
            "Please try a different image.",
            None,
            wardrobe_category,
        )

    # ── 3. Open original image ───────────────────────────────────────
    try:
        with Image.open(image_path) as orig_img:
            img = ImageOps.exif_transpose(orig_img).convert("RGBA")
            orig_w, orig_h = img.size
            img_array = np.array(img)  # (H, W, 4)

        logger.info("Original image: %dx%d", orig_w, orig_h)

    except Exception as exc:
        logger.error("Failed to open image %s: %s", image_path, exc)
        return (
            False,
            "Could not process the uploaded image. Please ensure it is a valid image file.",
            None,
            None,
        )

    # ── 4. Ensure mask matches image dimensions ──────────────────────
    mask_h, mask_w = mask_data.shape[:2]
    if (mask_h, mask_w) != (orig_h, orig_w):
        logger.info(
            "Resizing mask from %dx%d to %dx%d to match image",
            mask_w, mask_h, orig_w, orig_h,
        )
        mask_data = cv2.resize(
            mask_data.astype(np.uint8), (orig_w, orig_h),
            interpolation=cv2.INTER_NEAREST,
        )

    # ── 5. Clean up the mask (fill tiny holes, remove small blobs) ──
    clean_mask = _cleanup_mask(mask_data, min_blob_ratio=0.01)
    logger.info(
        "Mask after cleanup: %d garment pixels (was %d)",
        int(clean_mask.sum()), int(mask_data.sum()),
    )

    # ── 6. Validate mask integrity ───────────────────────────────────
    is_valid, reason = _validate_mask(
        clean_mask, primary_det["bounding_box"], detected_category,
    )
    if not is_valid:
        logger.warning("Mask validation failed for %s: %s", image_path, reason)
        return (False, reason, None, wardrobe_category)

    # ── 7. Apply mask to original image → transparent RGBA ───────────
    # Set alpha channel: 255 where garment, 0 where not
    result_array = img_array.copy()
    result_array[:, :, 3] = clean_mask * 255

    result_img = Image.fromarray(result_array, mode="RGBA")

    # ── 8. Crop to non-transparent bounding box with padding ─────────
    alpha_channel = result_img.split()[-1]
    bbox = alpha_channel.getbbox()
    if not bbox:
        return (
            False,
            "Could not isolate the garment — the resulting image was empty. "
            "Please try a different photo.",
            None,
            wardrobe_category,
        )

    pad = 10
    final_crop_box = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(orig_w, bbox[2] + pad),
        min(orig_h, bbox[3] + pad),
    )
    final_garment = result_img.crop(final_crop_box)

    crop_w = final_crop_box[2] - final_crop_box[0]
    crop_h = final_crop_box[3] - final_crop_box[1]
    logger.info(
        "Final garment crop: %dx%d (from bbox [%d,%d,%d,%d] + %dpx padding)",
        crop_w, crop_h, bbox[0], bbox[1], bbox[2], bbox[3], pad,
    )

    # ── 9. Final quality check ───────────────────────────────────────
    final_alpha = np.array(final_garment.split()[-1])
    solid_pixels = np.count_nonzero(final_alpha > 0)
    if solid_pixels < 1000:
        return (
            False,
            "The isolated garment is too small or incomplete. "
            "Please upload a clearer, larger image of the clothing item.",
            None,
            wardrobe_category,
        )

    # ── 10. Save clean transparent PNG ───────────────────────────────
    clean_dir = Path(settings.MEDIA_ROOT) / "wardrobe" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    filename = f"garment_clean_{uuid.uuid4().hex[:12]}.png"
    target_path = clean_dir / filename

    final_garment.save(target_path, "PNG")
    rel_path = f"wardrobe/clean/{filename}"

    logger.info(
        "✓ Garment isolated successfully: path=%s, category=%s→%s, "
        "confidence=%.4f, raw_label=%r, solid_pixels=%d, size=%dx%d",
        rel_path, detected_category, wardrobe_category,
        confidence, raw_label, solid_pixels, crop_w, crop_h,
    )

    return True, "Garment successfully isolated.", rel_path, wardrobe_category
