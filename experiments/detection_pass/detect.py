"""
Step 1 of the de-risking plan (docs/product-vision.md, §9): run a pretrained
detector over a folder of camera-roll photos and report what fraction
contain an animal, broken down by class (dog/cat/bird/horse/...).

Usage:
    uv run detect.py /path/to/photos [--out results.json]

Point --photos at a real export from your camera roll (Photos.app: select
a range, File > Export > Export N Photos... to sample_photos/, or a
smaller subfolder). Not committed to git — see sample_photos/.gitkeep.
"""

import argparse
import json
from pathlib import Path

from ultralytics import YOLO

ANIMAL_CLASSES = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("photos", type=Path, nargs="?", default=Path("sample_photos"))
    parser.add_argument("--out", type=Path, default=Path("results.json"))
    parser.add_argument("--conf", type=float, default=0.35)
    args = parser.parse_args()

    paths = sorted(p for p in args.photos.rglob("*") if p.suffix.lower() in IMAGE_EXTS)
    if not paths:
        raise SystemExit(f"No images found under {args.photos}")

    model = YOLO("yolov8n.pt")
    results = []
    animal_count = 0

    for path in paths:
        preds = model(str(path), conf=args.conf, verbose=False)[0]
        names = [preds.names[int(c)] for c in preds.boxes.cls]
        animal_hits = [n for n in names if n in ANIMAL_CLASSES]
        if animal_hits:
            animal_count += 1
        results.append({"file": str(path), "detections": names, "animal_hits": animal_hits})

    args.out.write_text(json.dumps(results, indent=2))

    print(f"Scanned {len(paths)} photos")
    print(f"Contain an animal: {animal_count} ({animal_count / len(paths):.0%})")
    from collections import Counter
    breakdown = Counter(h for r in results for h in r["animal_hits"])
    for cls, n in breakdown.most_common():
        print(f"  {cls}: {n}")
    print(f"\nFull results written to {args.out}")


if __name__ == "__main__":
    main()
