# Detection pass

De-risking step 1 from `docs/product-vision.md` §9: run a pretrained detector
(YOLOv8n, COCO weights) over a sample of your own camera roll and see what
fraction of photos contain an animal, and which species.

## Run it

1. Export a batch of real photos (Photos.app: select a range → File → Export →
   Export N Photos...) into `sample_photos/`. Not committed to git.
2. `uv run detect.py`

Weights (`yolov8n.pt`) download automatically on first run and are gitignored.

## Reading the output

- Console: total scanned, % containing an animal, breakdown by species.
- `results.json`: per-photo detections, for spot-checking false positives/negatives.

This only answers "is there enough raw material, and is detection alone
enough for a single-pet household?" Step 2 (clustering/individual ID) and
step 3 (the actual timeline demo) are separate, later scripts — see the
vision doc.
