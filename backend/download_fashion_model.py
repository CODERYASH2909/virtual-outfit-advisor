#!/usr/bin/env python
"""Download the DeepFashion2 YOLOv8s model weights from Hugging Face.

Usage:
    python download_fashion_model.py

No extra dependencies required -- uses only the Python standard library.

The script downloads `deepfashion2_yolov8s-seg.pt` from the
Bingsu/adetailer repository and saves it to:
    ai_engine/clothing_detection/weights/best.pt
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

# Direct download URL (bypasses the xet CDN that can be flaky)
DOWNLOAD_URL = (
    "https://huggingface.co/Bingsu/adetailer/resolve/main/"
    "deepfashion2_yolov8s-seg.pt"
)
TARGET_DIR = Path(__file__).resolve().parent / "ai_engine" / "clothing_detection" / "weights"
TARGET_PATH = TARGET_DIR / "best.pt"


def _download_with_progress(url: str, dest: Path) -> None:
    """Download a file with a simple progress indicator."""
    req = urllib.request.Request(url, headers={"User-Agent": "VOA-Backend/1.0"})
    with urllib.request.urlopen(req) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 256  # 256 KB

        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 / total
                    mb_done = downloaded / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    print(
                        f"\r  {mb_done:.1f} / {mb_total:.1f} MB ({pct:.0f}%)",
                        end="",
                        flush=True,
                    )
        print()  # newline after progress


def main() -> None:
    if TARGET_PATH.is_file() and TARGET_PATH.stat().st_size > 0:
        size_mb = TARGET_PATH.stat().st_size / (1024 * 1024)
        print(f"[OK] Model already exists at {TARGET_PATH} ({size_mb:.1f} MB)")
        print("  Delete the file and re-run this script to re-download.")
        return

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    print("Downloading DeepFashion2 YOLOv8s weights...")
    print(f"  Source: {DOWNLOAD_URL}")
    print(f"  Target: {TARGET_PATH}")

    try:
        _download_with_progress(DOWNLOAD_URL, TARGET_PATH)
    except Exception as exc:
        # Clean up partial download
        if TARGET_PATH.exists():
            TARGET_PATH.unlink()
        print(f"\n[FAIL] Download failed: {exc}", file=sys.stderr)
        sys.exit(1)

    size_mb = TARGET_PATH.stat().st_size / (1024 * 1024)
    if size_mb < 1:
        TARGET_PATH.unlink()
        print("[FAIL] Downloaded file is too small -- likely not valid weights.")
        sys.exit(1)

    print(f"[OK] Saved to {TARGET_PATH} ({size_mb:.1f} MB)")
    print()
    print("You can now start the server. The detector will load this model automatically.")


if __name__ == "__main__":
    main()
