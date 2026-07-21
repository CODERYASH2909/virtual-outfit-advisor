from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .detector import ClothingDetector, normalize_label


class _Value:
    def __init__(self, value):
        self.value = value

    def __getitem__(self, index):
        return self.value


class _XYXY:
    def __init__(self, coords):
        self.coords = coords

    def __getitem__(self, index):
        return self

    def tolist(self):
        return self.coords


class _Box:
    def __init__(self, class_id, confidence, coords):
        self.cls = _Value(class_id)
        self.conf = _Value(confidence)
        self.xyxy = _XYXY(coords)


class _Result:
    def __init__(self, boxes):
        self.boxes = boxes


class _FakeModel:
    names = {0: "person", 1: "handbag", 2: "long_sleeve_shirt"}

    def __init__(self, weights):
        self.weights = weights
        self.calls = []

    def __call__(self, image_path, conf, verbose):
        self.calls.append({"image_path": image_path, "conf": conf, "verbose": verbose})
        return [
            _Result(
                [
                    _Box(0, 0.99, [0, 0, 10, 10]),
                    _Box(1, 0.87654, [1.234, 2.345, 30.456, 40.567]),
                    _Box(2, 0.65432, [5, 6, 70, 80]),
                ]
            )
        ]


class ClothingDetectorTests(SimpleTestCase):
    def tearDown(self):
        ClothingDetector._instance = None

    def test_normalize_label_handles_common_model_name_formats(self):
        self.assertEqual(normalize_label("Long_Sleeve-Shirt"), "long sleeve shirt")
        self.assertEqual(normalize_label("  T   SHIRT  "), "t shirt")

    @override_settings(
        CLOTHING_DETECTION={
            "CONFIDENCE_THRESHOLD": 0.4,
            "CUSTOM_WEIGHTS_PATH": None,
            "DEFAULT_WEIGHTS": "yolov8n.pt",
        }
    )
    def test_detect_maps_known_labels_and_skips_unknown_classes(self):
        detector = ClothingDetector()

        with patch.dict("sys.modules", {"ultralytics": SimpleNamespace(YOLO=_FakeModel)}):
            detections = detector.detect(Path("sample.jpg"))

        self.assertEqual(
            detections,
            [
                {
                    "category": "Bag",
                    "confidence": 0.8765,
                    "bounding_box": [1.23, 2.35, 30.46, 40.57],
                },
                {
                    "category": "Shirt",
                    "confidence": 0.6543,
                    "bounding_box": [5.0, 6.0, 70.0, 80.0],
                },
            ],
        )
        self.assertEqual(detector._model.weights, "yolov8n.pt")
        self.assertEqual(detector._model.calls[0]["conf"], 0.4)

    @override_settings(
        CLOTHING_DETECTION={
            "CONFIDENCE_THRESHOLD": 0.25,
            "CUSTOM_WEIGHTS_PATH": "C:/fashion/best.pt",
            "DEFAULT_WEIGHTS": "yolov8n.pt",
        }
    )
    @patch("pathlib.Path.is_file", return_value=True)
    def test_custom_weights_path_is_used_when_file_exists(self, _mock_is_file):
        detector = ClothingDetector()

        with patch.dict("sys.modules", {"ultralytics": SimpleNamespace(YOLO=_FakeModel)}):
            detector.detect("sample.jpg")

        self.assertEqual(Path(detector._model.weights), Path("C:/fashion/best.pt"))
