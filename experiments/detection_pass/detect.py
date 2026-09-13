"""
Step 1 of the de-risking plan (docs/product-vision.md §9, docs/decisions.md
D6/D7): run a pretrained detector over photos pulled from an Android phone
and report what fraction contain an animal, with capture dates so the output
can be rendered as a timeline.

Usage:
    uv run detect.py sample_photos/<contributor> --contributor <name>

Run once per household member, each into their own results file, so the
merge test (D6) can interleave them later.
"""

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import Base as ExifTag
from ultralytics import YOLO

ANIMAL_CLASSES = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def capture_time(path: Path) -> str | None:
    try:
        exif = Image.open(path).getexif()
        raw = exif.get(ExifTag.DateTimeOriginal) or exif.get(ExifTag.DateTime)
        if raw:
            return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S").isoformat()
    except Exception:
        pass
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("photos", type=Path, nargs="?", default=Path("sample_photos"))
    parser.add_argument("--contributor", default="me")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--conf", type=float, default=0.35)
    args = parser.parse_args()
    out = args.out or Path(f"results_{args.contributor}.json")

    paths = sorted(p for p in args.photos.rglob("*") if p.suffix.lower() in IMAGE_EXTS)
    if not paths:
        raise SystemExit(f"No images found under {args.photos}")

    model = YOLO("yolov8n.pt")
    results = []

    for path in paths:
        preds = model(str(path), conf=args.conf, verbose=False)[0]
        names = [preds.names[int(c)] for c in preds.boxes.cls]
        boxes = [[round(v) for v in b] for b in preds.boxes.xyxy.tolist()]
        animal_hits = [n for n in names if n in ANIMAL_CLASSES]
        results.append({
            "file": str(path),
            "contributor": args.contributor,
            "taken_at": capture_time(path),
            "detections": names,
            "boxes": boxes,
            "animal_hits": animal_hits,
        })

    results.sort(key=lambda r: r["taken_at"])
    out.write_text(json.dumps(results, indent=2))

    with_animal = sum(1 for r in results if r["animal_hits"])
    print(f"Scanned {len(paths)} photos from {args.contributor}")
    print(f"Contain an animal: {with_animal} ({with_animal / len(paths):.0%})")
    for cls, n in Counter(h for r in results for h in r["animal_hits"]).most_common():
        print(f"  {cls}: {n}")
    dated = [r["taken_at"][:10] for r in results if r["animal_hits"]]
    if dated:
        print(f"Animal photos span {dated[0]} to {dated[-1]}")
    print(f"\nWritten to {out}")


if __name__ == "__main__":
    main()
