# Timeline

Turns a pile of camera-roll photos into a browsable life timeline, with no
tagging, sorting or naming by a human. `ingest.py` builds a moment graph;
`render.py` turns it into a web page.

Built as de-risking, not product code (`docs/product-vision.md` §9). Findings
live in [`docs/data-model.md`](../../docs/data-model.md); work is tracked in
[GitHub issues](https://github.com/mjm3853/pets/issues).

---

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/) and nothing else — it fetches
Python and the dependencies itself on first run.

```bash
cd experiments/timeline
uv run ingest.py --pet Izzy --species dog --anchor 2021-04-09 \
  --roll "Matt=/path/to/matts/photos" \
  --roll "Renee=/path/to/renees/photos"
uv run render.py --out izzy.html
open izzy.html
```

That is the whole app. No server, no database, no build step — `render.py`
writes a page you open directly from disk.

### Getting the photos off the phones

Both phones are Android, so USB with `adb` is fastest
(`brew install android-platform-tools`, then enable USB debugging: Settings →
About phone → tap Build number 7× → Developer options → USB debugging):

```bash
adb pull /sdcard/DCIM/Camera ~/izzy-photos/matt
```

This only copies photos **still on the device**. Anything Google Photos has
offloaded via "Free up space" is invisible to `adb` and to every API except
the picker — use [Google Takeout](https://takeout.google.com) to include
those. Takeout ships each photo with a `.json` sidecar holding
`photoTakenTime`, which `ingest.py` does not read yet.

---

## The two commands

### `ingest.py` — photos in, `moments.json` out

One `--roll NAME=PATH` per contributor; repeat the flag to merge people.
Duplicate captures appearing in more than one roll are kept once.

| flag | what it does |
|---|---|
| `--pet`, `--species` | profile fields; species is **yours to set**, the detector is not trusted to decide it (D17) |
| `--anchor YYYY-MM-DD` | the real adoption or birth date. Saved to `pet.json`, asked once, never moved by a later import |
| `--rebuild moments.json` | recompute everything downstream of detection without running the model |
| `--conf`, `--model` | detector threshold and weights |
| `--cache DIR`, `--no-cache` | where results are cached; bypass reads |

### `render.py` — `moments.json` in, a page out

Needs no photo paths: they travel in `moments.json`.

| flag | what it does |
|---|---|
| `--assets external` | **default.** Page plus a sibling `izzy_assets/` folder of JPEGs |
| `--assets inline` | one portable file with every image embedded |
| `--thumb`, `--quality` | contact-sheet thumbnails (default 200px) |
| `--frame`, `--frame-quality`, `--max-frames` | frames inside an expanded burst |

Current output, 1,550 moments across four pets:

| mode | page | assets | good for |
|---|---|---|---|
| `external` | 1.0 MB | 22 MB in a folder | opening locally, hosting |
| `inline` | 23 MB | none | sending one file to a person |

### Speed

Both scripts cache on content hash in `.cache/`, so a re-run only pays for
what actually changed:

| | cold | warm |
|---|---|---|
| `ingest.py`, 4,383 files | 6m25s | **4.8s** |
| `render.py`, 1,550 moments | 3m11s | **0.8s** |

Output is byte-identical either way. The cache is keyed on file contents plus
every parameter that reaches the encoder, so changing `--thumb` re-cuts the
thumbnails and leaves everything else alone. Delete `.cache/` to reclaim the
space (87 MB here); it rebuilds itself.

---

## Sharing and deployment

**Technically trivial. That is not the hard part.**

The external-mode output is already a static site — a page and a folder of
JPEGs, about 23 MB, with no server-side anything. It will run unchanged on
GitHub Pages, Netlify, Vercel, Cloudflare Pages, S3, or a USB stick.

The hard part is that it is **someone's private photo archive**, and static
hosting is unauthenticated by default. An unguessable URL is not access
control: links leak through chat apps, browser sync and referrer headers, and
a public page can be crawled. Putting this on a plain static host would place
five years of a household's photos on the open web.

Realistic options, roughly by effort:

| approach | privacy | effort |
|---|---|---|
| Send the `inline` file directly | as private as the channel | none |
| USB stick or AirDrop the folder | fully offline | none |
| Cloudflare Pages + Cloudflare Access | real auth, email allowlist, free tier | ~30 min |
| Netlify/Vercel password protection | shared password, paid tier | ~10 min + cost |
| Tailscale on a machine at home | only your devices, nothing public | ~20 min |

For a household of two, sending the single file or serving it over Tailscale
covers it. Anything shared wider wants real auth — and that is where this
stops being a static-site problem and becomes a product decision, so keep the
permission model generic (D5).

To preview exactly as a host would serve it:

```bash
python3 -m http.server 8000
```

then open `http://localhost:8000/izzy.html`. Opening the file directly with
`open` works too; the server only matters if you want to check real HTTP
behaviour.

---

## Results on the Izzy archive

Two camera rolls (Matt, Renee) plus three albums about friends' dogs:

| | |
|---|---|
| Files in | 4,547 |
| Contained a detectable animal | 4,070 (90%) |
| Moments after burst clustering | 1,550 |
| **Izzy** | 1,388 moments · prologue + 6 chapters, anchored on adoption day |
| **Oakley** | 58 moments · sparse, no timeline |
| **Ray** | 29 moments · sparse |
| **Shadow** | 19 moments · a third friend's dog found inside Ray's album |
| Moments holding more than one pet | 58 |
| Held out | 172 undated, 2 pre-anchor, 2 deliberately unassigned |
| Needing review | 0, after 62 human answers |

**Day coverage: Matt 484, Renee 490, merged 772** — merging adds 58% more
days than the better single roll, and 103 moments hold frames from both
people. That is the cross-person wedge (D6), measured.

An album is a **hint, not ground truth** (D23): Ray's album turned out to be
33 Shadow, 31 Ray, 18 Izzy-and-Ray and 3 Oakley. Sorting that out cost 62
answers — about 28 per 100 album photos — through the review queue.

---

## Notes

- Photos, `moments.json`, `pet.json`, generated pages, asset folders, the
  cache and model weights are all gitignored. Nothing from the real archive
  is committed.
- Output contains personal photos, so it stays local by default and is
  deliberately not published anywhere.
- Thumbnails top out at 200px, so nothing here is downloadable at a useful
  size yet — that needs the originals, and is
  [issue #13](https://github.com/mjm3853/pets/issues/13).
