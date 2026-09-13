# Detection pass

De-risking step 1 from `docs/product-vision.md` §9, adapted for an Android
household (`docs/decisions.md` D7): pull photos off each phone, run a
pretrained detector (YOLOv8n, COCO weights) over them, and record which
contain an animal along with the capture date. One results file per person
so the multi-contributor merge test (D6) can be run on top.

## Getting photos off an Android phone

Fastest path is USB with `adb`. Install once with `brew install
android-platform-tools`, enable USB debugging on the phone (Settings →
About phone → tap Build number 7× → Developer options → USB debugging), then:

```bash
adb pull /sdcard/DCIM/Camera sample_photos/<name>
```

This copies only photos still on the device. Anything Google Photos has
removed via "Free up space" is not there, and that gap is itself something to
measure (D7). To include those, use Google Takeout for Google Photos; the
export ships each photo with a `.json` sidecar containing `photoTakenTime`.

Alternative without `adb`: Android File Transfer or Google's Files app
sharing to the Mac. Slower, same result.

## Run it

```bash
uv run detect.py sample_photos/<name> --contributor <name>
```

Weights (`yolov8n.pt`) download on first run. Photos, weights, and results
are all gitignored.

## Output

Console: count, % containing an animal, species breakdown, date span.
`results_<name>.json`: per-photo detections, bounding boxes, and
`taken_at`, sorted by date. Bounding boxes are kept so step 2 (crop, embed,
cluster for individual ID) can reuse this output without re-running
detection.

## What comes next

- **Step 2, clustering:** only needed if a contributor's roll has animals
  that aren't the household pet. Crop the boxes, embed, cluster, check purity.
- **Step 3, the timeline:** render all `results_*.json` files interleaved
  into one dated static page and look at it. Whether the merged view beats a
  single person's view is the D6 test.
