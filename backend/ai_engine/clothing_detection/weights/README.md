# YOLO Model Weights — DeepFashion2 YOLOv8s

This directory holds the YOLO model weights used by the clothing detector.

## Current Model

**`deepfashion2_yolov8s-seg.pt`** from [Bingsu/adetailer](https://huggingface.co/Bingsu/adetailer)

Saved here as `best.pt` (the filename the settings point to).

### 13 Clothing Classes

| Index | Model Label         | Mapped Category |
|-------|---------------------|-----------------|
| 0     | short sleeve top    | T-Shirt         |
| 1     | long sleeve top     | Shirt           |
| 2     | short sleeve outwear| Jacket          |
| 3     | long sleeve outwear | Jacket          |
| 4     | vest                | Sweater         |
| 5     | sling               | T-Shirt         |
| 6     | shorts              | Shorts          |
| 7     | trousers            | Pants           |
| 8     | skirt               | Skirt           |
| 9     | short sleeve dress  | Dress           |
| 10    | long sleeve dress   | Dress           |
| 11    | vest dress          | Dress           |
| 12    | sling dress         | Dress           |

## Download

### Option A — Automated (recommended)

```bash
cd backend
pip install huggingface_hub
python download_fashion_model.py
```

### Option B — Manual

1. Go to <https://huggingface.co/Bingsu/adetailer/tree/main>
2. Download `deepfashion2_yolov8s-seg.pt`
3. Save it here as `best.pt`

## Notes

- `best.pt` is **git-ignored** — do not commit model weights.
- The detector reads the model's `names` vocabulary automatically; label → category
  mappings live in `clothing_detection/detector.py → LABEL_TO_CATEGORY`.
- To swap models, replace `best.pt` with any Ultralytics-compatible `.pt` file.
