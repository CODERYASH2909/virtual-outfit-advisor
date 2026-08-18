"""Model-agnostic YOLO clothing detector.

The detector does not hard-code YOLO class IDs. It loads whichever weights file
is configured, reads that model's own ``names`` vocabulary, and maps recognized
labels to the application's canonical clothing categories.

To switch from ``yolov8n.pt`` to a fashion-trained model, change only the
configured weights path. The upload view and persistence logic continue to work
with the normalized detection contract returned by ``detect()``.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


LABEL_TO_CATEGORY: dict[str, str] = {
    # Tops
    "shirt": "Shirt",
    "long sleeve top": "Shirt",
    "long sleeve shirt": "Shirt",
    "long sleeved shirt": "Shirt",
    "blouse": "Shirt",
    "t-shirt": "T-Shirt",
    "t shirt": "T-Shirt",
    "tshirt": "T-Shirt",
    "tee": "T-Shirt",
    "short sleeve top": "T-Shirt",
    "short sleeve shirt": "T-Shirt",
    "short sleeved shirt": "T-Shirt",
    "tank top": "T-Shirt",
    "sling": "T-Shirt",
    "hoodie": "Hoodie",
    "hoody": "Hoodie",
    "sweatshirt": "Hoodie",
    "jacket": "Jacket",
    "coat": "Jacket",
    "outerwear": "Jacket",
    "outwear": "Jacket",
    "short sleeve outwear": "Jacket",
    "short sleeved outwear": "Jacket",
    "long sleeve outwear": "Jacket",
    "long sleeved outwear": "Jacket",
    "blazer": "Blazer",
    "suit jacket": "Blazer",
    "sweater": "Sweater",
    "pullover": "Sweater",
    "cardigan": "Sweater",
    "jumper": "Sweater",
    "knitwear": "Sweater",
    "vest": "Sweater",
    # Bottoms
    "jeans": "Jeans",
    "denim": "Jeans",
    "pants": "Pants",
    "trousers": "Pants",
    "shorts": "Shorts",
    "short pants": "Shorts",
    "skirt": "Skirt",
    # Full body
    "dress": "Dress",
    "long sleeve dress": "Dress",
    "long sleeved dress": "Dress",
    "short sleeve dress": "Dress",
    "short sleeved dress": "Dress",
    "sling dress": "Dress",
    "vest dress": "Dress",
    "gown": "Dress",
    # Footwear
    "shoes": "Shoes",
    "shoe": "Shoes",
    "boot": "Shoes",
    "boots": "Shoes",
    "sneakers": "Sneakers",
    "sneaker": "Sneakers",
    "trainers": "Sneakers",
    "trainer": "Sneakers",
    "running shoe": "Sneakers",
    "sandals": "Sandals",
    "sandal": "Sandals",
    "flip flops": "Sandals",
    "slipper": "Sandals",
    "slippers": "Sandals",
    # Headwear
    "cap": "Cap",
    "baseball cap": "Cap",
    "hat": "Hat",
    "beanie": "Hat",
    "beret": "Hat",
    "sun hat": "Hat",
    # Accessories
    "belt": "Belt",
    "tie": "Belt",
    "bag": "Bag",
    "handbag": "Bag",
    "backpack": "Bag",
    "suitcase": "Bag",
    "purse": "Bag",
    "clutch": "Bag",
    "tote": "Bag",
    "messenger bag": "Bag",
}


def normalize_label(label: str) -> str:
    """Normalize model labels before mapping them to canonical categories."""
    return " ".join(label.replace("_", " ").replace("-", " ").lower().split())


def get_detection_settings() -> dict[str, Any]:
    """Read clothing-detection settings with safe defaults."""
    defaults: dict[str, Any] = {
        "CONFIDENCE_THRESHOLD": 0.25,
        "MAX_IMAGE_SIZE_MB": 10,
        "CUSTOM_WEIGHTS_PATH": None,
        "DEFAULT_WEIGHTS": "yolov8n.pt",
    }
    overrides = getattr(settings, "CLOTHING_DETECTION", {})
    return {**defaults, **overrides}


class ClothingDetector:
    """Thread-safe, lazy-loaded YOLO inference wrapper."""

    _instance: ClothingDetector | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._model = None
        self._class_index: dict[int, str] = {}
        self._model_lock = threading.Lock()
        self._settings = get_detection_settings()

    @classmethod
    def get_instance(cls) -> ClothingDetector:
        """Return the shared detector instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _resolve_weights_path(self) -> str:
        """Choose custom weights when present, otherwise use yolov8n.pt."""
        custom = self._settings.get("CUSTOM_WEIGHTS_PATH")
        if custom:
            custom_path = Path(custom)
            if custom_path.is_file():
                logger.info("Using custom YOLO weights: %s", custom_path)
                return str(custom_path)
            logger.info(
                "Custom weights path configured but file not found (%s); using default.",
                custom_path,
            )

        default = str(self._settings.get("DEFAULT_WEIGHTS", "yolov8n.pt"))
        logger.info("Using default YOLO weights: %s", default)
        return default

    def _build_class_index(self) -> dict[int, str]:
        """Map model class IDs to canonical clothing categories."""
        if self._model is None:
            return {}

        index: dict[int, str] = {}
        model_names = getattr(self._model, "names", {})

        for raw_class_id, raw_name in model_names.items():
            class_id = int(raw_class_id)
            category = LABEL_TO_CATEGORY.get(normalize_label(str(raw_name)))
            if category:
                index[class_id] = category
                logger.debug("Mapped model class %s (%r) to %s", class_id, raw_name, category)

        logger.info("Mapped %d of %d model classes.", len(index), len(model_names))
        return index

    def _ensure_model(self) -> None:
        """Load the YOLO model once, on first use."""
        if self._model is not None:
            return

        with self._model_lock:
            if self._model is not None:
                return

            from ultralytics import YOLO

            weights = self._resolve_weights_path()
            logger.info("Loading YOLO model from %s", weights)
            self._model = YOLO(weights)
            self._class_index = self._build_class_index()

    def detect(self, image_path: str | Path) -> list[dict[str, Any]]:
        """Run detection and return normalized clothing detections.

        Each detection dict contains:
        - category: canonical category name (e.g. "Shirt", "Pants")
        - raw_label: the original model label (e.g. "long_sleeved_shirt", "trousers")
        - confidence: detection confidence score
        - bounding_box: [x1, y1, x2, y2] in pixel coordinates
        - mask_polygon: list of [x, y] polygon vertices (original image coords)
        - mask_data: numpy array of the segmentation mask at original image resolution
        """
        self._ensure_model()

        conf_threshold = float(self._settings.get("CONFIDENCE_THRESHOLD", 0.25))
        results = self._model(str(image_path), conf=conf_threshold, verbose=False)
        detections: list[dict[str, Any]] = []

        for result in results:
            boxes = getattr(result, "boxes", None)
            masks = getattr(result, "masks", None)
            if boxes is None:
                continue

            mask_xys = getattr(masks, "xy", None) if masks is not None else None
            # masks.data is a tensor of shape (N, H, W) with float values 0..1
            mask_tensors = getattr(masks, "data", None) if masks is not None else None
            orig_shape = getattr(result, "orig_shape", None)  # (H, W)

            for idx, box in enumerate(boxes):
                class_id = int(box.cls[0])
                category = self._class_index.get(class_id)

                # Retrieve raw model label for logging/debugging
                model_names = getattr(self._model, "names", {})
                raw_label = str(model_names.get(class_id, f"unknown_{class_id}"))

                if category is None:
                    logger.debug(
                        "Skipping unmapped class %s (%r) with no category mapping",
                        class_id, raw_label,
                    )
                    continue

                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                logger.info(
                    "Detection: class=%s raw_label=%r → category=%s conf=%.4f "
                    "bbox=[%.1f, %.1f, %.1f, %.1f]",
                    class_id, raw_label, category, confidence, x1, y1, x2, y2,
                )

                det_dict: dict[str, Any] = {
                    "category": category,
                    "raw_label": raw_label,
                    "confidence": round(confidence, 4),
                    "bounding_box": [
                        round(float(x1), 2),
                        round(float(y1), 2),
                        round(float(x2), 2),
                        round(float(y2), 2),
                    ],
                    "mask_polygon": None,
                    "mask_data": None,
                }

                if mask_xys is not None and idx < len(mask_xys):
                    polygon = mask_xys[idx]
                    if hasattr(polygon, "tolist"):
                        det_dict["mask_polygon"] = polygon.tolist()
                    elif isinstance(polygon, list):
                        det_dict["mask_polygon"] = polygon

                # Provide the pixel-accurate mask tensor resized to original image dims
                if mask_tensors is not None and idx < len(mask_tensors):
                    import cv2
                    mask_tensor = mask_tensors[idx].cpu().numpy()  # (mask_H, mask_W)
                    if orig_shape is not None:
                        oh, ow = int(orig_shape[0]), int(orig_shape[1])
                        if mask_tensor.shape != (oh, ow):
                            mask_tensor = cv2.resize(
                                mask_tensor, (ow, oh),
                                interpolation=cv2.INTER_LINEAR,
                            )
                    det_dict["mask_data"] = (mask_tensor > 0.5).astype("uint8")
                    mask_pixels = int(det_dict["mask_data"].sum())
                    logger.info(
                        "  Segmentation mask: shape=%s, garment_pixels=%d",
                        det_dict["mask_data"].shape, mask_pixels,
                    )

                detections.append(det_dict)

        return detections

    def reload_model(self) -> None:
        """Clear the loaded model so the next detection reloads configured weights."""
        with self._model_lock:
            self._model = None
            self._class_index = {}
            self._settings = get_detection_settings()

    @property
    def mapped_categories(self) -> list[str]:
        """Return canonical categories supported by the loaded model."""
        self._ensure_model()
        return sorted(set(self._class_index.values()))
