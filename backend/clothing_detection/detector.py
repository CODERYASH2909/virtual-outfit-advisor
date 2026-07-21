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
    "blouse": "Shirt",
    "t-shirt": "T-Shirt",
    "t shirt": "T-Shirt",
    "tshirt": "T-Shirt",
    "tee": "T-Shirt",
    "short sleeve top": "T-Shirt",
    "short sleeve shirt": "T-Shirt",
    "tank top": "T-Shirt",
    "hoodie": "Hoodie",
    "hoody": "Hoodie",
    "sweatshirt": "Hoodie",
    "jacket": "Jacket",
    "coat": "Jacket",
    "outerwear": "Jacket",
    "blazer": "Blazer",
    "suit jacket": "Blazer",
    "sweater": "Sweater",
    "pullover": "Sweater",
    "cardigan": "Sweater",
    "jumper": "Sweater",
    "knitwear": "Sweater",
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
    "short sleeve dress": "Dress",
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
        """Run detection and return normalized clothing detections."""
        self._ensure_model()

        conf_threshold = float(self._settings.get("CONFIDENCE_THRESHOLD", 0.25))
        results = self._model(str(image_path), conf=conf_threshold, verbose=False)
        detections: list[dict[str, Any]] = []

        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            for box in boxes:
                class_id = int(box.cls[0])
                category = self._class_index.get(class_id)
                if category is None:
                    continue

                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    {
                        "category": category,
                        "confidence": round(confidence, 4),
                        "bounding_box": [
                            round(float(x1), 2),
                            round(float(y1), 2),
                            round(float(x2), 2),
                            round(float(y2), 2),
                        ],
                    }
                )

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
