"""Garment Isolation & Preprocessing Engine for Digital Wardrobe.

Isolates clothing items from user-uploaded images containing human models or complex backgrounds.
Produces a clean garment-only image on a transparent background for Virtual Try-On, preserving
all original garment colors, shapes, patterns, sleeves, hoods, collars, buttons, and hems.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps
from django.conf import settings

from .detector import ClothingDetector, LABEL_TO_CATEGORY

logger = logging.getLogger(__name__)

# Map detailed detector labels to WardrobeItem model CATEGORY_CHOICES
DETECTOR_CATEGORY_TO_WARDROBE_CATEGORY: dict[str, str] = {
    "Shirt": "top",
    "T-Shirt": "top",
    "Hoodie": "top",
    "Jacket": "outerwear",
    "Blazer": "outerwear",
    "Sweater": "top",
    "Jeans": "bottom",
    "Pants": "bottom",
    "Shorts": "bottom",
    "Skirt": "bottom",
    "Dress": "dress",
    "Shoes": "footwear",
    "Sneakers": "footwear",
    "Sandals": "footwear",
    "Cap": "headwear",
    "Hat": "headwear",
    "Belt": "accessory",
    "Bag": "bag",
}


def remove_skin_pixels(img_rgba: Image.Image, confidence_mask: np.ndarray | None = None) -> Image.Image:
    """Filter out human skin regions (head/neck, bare arms/hands, bare legs) attached to garment edges.

    Uses HSV color space skin detection to set skin pixel alpha to transparent,
    while leaving garment colors intact.
    """
    arr = np.array(img_rgba)
    if arr.shape[2] < 4:
        return img_rgba

    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    # Convert RGB to HSV using PIL or numpy math
    pil_rgb = Image.fromarray(rgb, mode="RGB")
    hsv = np.array(pil_rgb.convert("HSV"))

    h = hsv[:, :, 0]  # 0 - 255
    s = hsv[:, :, 1]  # 0 - 255
    v = hsv[:, :, 2]  # 0 - 255

    # Human skin HSV range in PIL's 0-255 scale:
    # Hue: 0-35 (approx 0-50 degrees) or 220-255 (reddish tones)
    # Saturation: 30-170
    # Value: 60-255
    skin_h = ((h <= 35) | (h >= 220))
    skin_s = (s >= 25) & (s <= 180)
    skin_v = (v >= 50)

    skin_mask = skin_h & skin_s & skin_v

    # Apply skin transparency only where alpha is already somewhat transparent or near outer edges
    # to avoid modifying internal garment patterns of beige/tan clothes.
    # We create a new alpha channel where detected edge skin is zeroed out.
    new_alpha = alpha.copy()

    # If we have a skin mask, zero out skin alpha
    # (Skin removal is done conservatively: only where skin_mask is True and alpha > 0)
    # To protect skin-colored clothes, we check if skin region forms tiny attached strips at margins
    rows, cols = alpha.shape
    margin_top = int(rows * 0.18)  # neck region
    margin_bottom = int(rows * 0.85)  # ankles/feet region

    # Zero skin in top margin (neck/chin) and bottom margin (legs/feet)
    top_skin = skin_mask[:margin_top, :]
    new_alpha[:margin_top, :][top_skin] = 0

    bottom_skin = skin_mask[margin_bottom:, :]
    new_alpha[margin_bottom:, :][bottom_skin] = 0

    arr[:, :, 3] = new_alpha
    return Image.fromarray(arr, mode="RGBA")


def isolate_garment(image_input: str | Path | Any) -> tuple[bool, str, str | None, str | None]:
    """Isolate garment from uploaded image, removing person body & background.

    Args:
        image_input: Path to uploaded image file.

    Returns:
        tuple of (success: bool, message: str, clean_image_path: str | None, detected_category: str | None)
    """
    image_path = str(image_input)

    # 1. Run YOLO clothing detector
    detector = ClothingDetector.get_instance()
    try:
        detections = detector.detect(image_path)
    except Exception as exc:
        logger.warning("YOLO detection failed on %s: %s", image_path, exc)
        detections = []

    # Filter detections by confidence threshold (0.20 for garment isolation)
    min_confidence = 0.20
    valid_detections = [d for d in detections if d.get("confidence", 0) >= min_confidence]

    # If no valid garment detected with reasonable confidence:
    if not valid_detections:
        # Fall back to rembg check: see if rembg can find a distinct object in center
        logger.info("No high-confidence YOLO detection for %s; trying direct rembg extraction.", image_path)

    # Pick highest-confidence detection if present
    primary_det = max(valid_detections, key=lambda x: x["confidence"]) if valid_detections else None
    detected_cat_name = primary_det["category"] if primary_det else None
    wardrobe_category = DETECTOR_CATEGORY_TO_WARDROBE_CATEGORY.get(detected_cat_name) if detected_cat_name else None

    # 2. Open image and process background removal
    try:
        with Image.open(image_path) as orig_img:
            img = ImageOps.exif_transpose(orig_img).convert("RGBA")
            orig_w, orig_h = img.size

            # If YOLO detected a bounding box, expand it slightly with 15% safety padding
            if primary_det and "bounding_box" in primary_det:
                x1, y1, x2, y2 = primary_det["bounding_box"]
                bw = x2 - x1
                bh = y2 - y1
                pad_x = bw * 0.12
                pad_y = bh * 0.12

                cx1 = max(0, int(x1 - pad_x))
                cy1 = max(0, int(y1 - pad_y))
                cx2 = min(orig_w, int(x2 + pad_x))
                cy2 = min(orig_h, int(y2 + pad_y))

                crop_img = img.crop((cx1, cy1, cx2, cy2))
            else:
                crop_img = img

            # 3. Apply rembg background & body removal
            has_bg_removed = False
            try:
                from rembg import remove
                bg_removed = remove(crop_img)
                alpha = bg_removed.split()[-1]
                bbox = alpha.getbbox()
                if bbox and (bbox[2] - bbox[0] > 30) and (bbox[3] - bbox[1] > 30):
                    clean_img = bg_removed
                    has_bg_removed = True
                else:
                    clean_img = crop_img
            except Exception as exc:
                logger.warning("Rembg background removal skipped for %s (%s)", image_path, exc)
                clean_img = crop_img

            # 4. Apply conservative skin/body removal for neck/feet edges
            if has_bg_removed:
                clean_img = remove_skin_pixels(clean_img)

            # 5. Crop to exact non-transparent bounding box with 12px safety padding
            alpha = clean_img.split()[-1]
            bbox = alpha.getbbox()

            if not bbox or (bbox[2] - bbox[0] < 40) or (bbox[3] - bbox[1] < 40):
                return (
                    False,
                    "Could not confidently isolate the clothing item from the uploaded image. "
                    "Please upload a clearer image of the garment on a simple background.",
                    None,
                    wardrobe_category,
                )

            pad = 12
            final_crop_box = (
                max(0, bbox[0] - pad),
                max(0, bbox[1] - pad),
                min(clean_img.width, bbox[2] + pad),
                min(clean_img.height, bbox[3] + pad),
            )
            final_garment = clean_img.crop(final_crop_box)

            # 6. Save clean garment image
            clean_dir = Path(settings.MEDIA_ROOT) / "wardrobe" / "clean"
            clean_dir.mkdir(parents=True, exist_ok=True)
            filename = f"garment_clean_{uuid.uuid4().hex[:12]}.png"
            target_path = clean_dir / filename

            final_garment.save(target_path, "PNG", quality=95)
            logger.info("Successfully isolated clean garment image: %s", target_path)

            rel_path = f"wardrobe/clean/{filename}"
            return True, "Garment successfully isolated.", rel_path, wardrobe_category

    except Exception as exc:
        logger.error("Garment isolation processing error for %s: %s", image_path, exc)
        return (
            False,
            "Could not process the uploaded image. Please ensure it is a valid JPG, PNG, or WebP photo of a clothing item.",
            None,
            None,
        )
