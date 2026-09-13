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
uv run ingest.py "/path/to/photos" --pet Izzy
uv run render.py --photos "/path/to/photos" --out izzy.html
```

`ingest.py` writes `moments.json` (media, moments, eras, milestones).
`render.py` embeds every thumbnail as a data URI, so the HTML is one
portable file with no image directory — about 7.7 MB for 549 moments.
Lower `--thumb` or `--quality` if it grows past ~15 MB.

## Results on the Izzy archive

| | |
|---|---|
| Files in | 1,274 |
| Contained a detectable dog | 1,144 (90%) |
| Moments after burst clustering | 549 (2.1× compression) |
| Chapters | 6 life years, anchored on the first photo |
| Undated files held out | 32 |

Detection alone was sufficient — no individual pet ID — which answers §9's
first question for a single-pet household. The archive is single-contributor
(device succession, not three people), so it does **not** test D6.

## Notes

- Photos, `moments.json`, generated HTML and model weights are gitignored.
  Nothing from the real archive is committed.
- Output contains personal photos. It is deliberately a local file, not a
  published page.
