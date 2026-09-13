# Timeline

Steps 1 and 3 of the de-risking plan (`docs/product-vision.md` §9), run on a
real archive: 1,274 files of one dog across five years and three phones.

`ingest.py` turns a folder of photos into a moment graph; `render.py` turns
that into a self-contained page. Findings live in
[`docs/data-model.md`](../../docs/data-model.md).

## Getting photos off an Android phone

Fastest path is USB with `adb` (`brew install android-platform-tools`), with
USB debugging enabled on the phone (Settings → About phone → tap Build number
7× → Developer options → USB debugging):

```bash
adb pull /sdcard/DCIM/Camera sample_photos/<name>
```

This copies only photos still on the device. Anything Google Photos has
removed via "Free up space" is not there, and measuring that gap is itself an
open question (D7). To include those, use Google Takeout, which ships each
photo with a `.json` sidecar containing `photoTakenTime`.

## Run

```bash
uv run ingest.py --pet Izzy --roll "Matt=/path/to/matt" --roll "Renee=/path/to/renee"
uv run render.py --out izzy.html
```

One `--roll` per contributor. Paths travel in `moments.json`, so `render.py`
needs no photo path of its own.

`ingest.py` writes `moments.json` (media, moments, eras, milestones).
`render.py` writes the page plus a sibling `<name>_assets/` folder of
JPEGs. Pass `--assets inline` for a single portable file with every image
base64'd in — bigger and slower to open, but one file you can send someone.

Both scripts cache on content hash (`.cache/`, gitignored), so re-running
after a change costs only what actually changed:

| | cold | warm |
|---|---|---|
| `ingest.py`, 4,383 files | 6m25s | **4.8s** |
| `render.py`, 1,378 moments | 3m11s | **0.8s** |

Output is byte-identical either way. `--no-cache` forces recompute,
`--rebuild moments.json` recomputes everything downstream of detection
without touching the model.

## Results on the Izzy archive

Two rolls, Matt's and Renee's:

| | |
|---|---|
| Files in | 4,403 (20 shared copies kept once) |
| Contained a detectable dog | 3,924 (90%) |
| Moments after burst clustering | 1,378 (2.8× compression) |
| Chapters | 6 life years, anchored on first sustained photography |
| Built from both rolls at once | 81 moments |
| Held out | 163 undated, 2 pre-anchor (another dog) |

**Day coverage: Matt 484, Renee 490, merged 772** — the merge adds 58% more
days than the better single roll. That is the D6 wedge, measured.

Detection alone is sufficient for the timeline; no individual pet ID. But
Renee's roll contains two photos of other people's dogs from 2018–19, and
before D15 those 0.05% dragged the anchor back 2.5 years and destroyed the
chapter structure.

## Notes

- Photos, `moments.json`, generated HTML and model weights are gitignored.
  Nothing from the real archive is committed.
- Output contains personal photos. It is deliberately a local file, not a
  published page.
