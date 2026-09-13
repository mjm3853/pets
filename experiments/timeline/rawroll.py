"""
Measure what a Google Photos album was hiding (issue #32, D22).

Every archive so far was a platform-curated pet album, so every number the
project rests on — 90% detection, single-pet inference being right almost
always — describes album input. This runs the same detector over a raw
camera roll and asks: of everything it flags as an animal, how much is
actually the pet?

    uv run rawroll.py ~/dcim-pull --pet Izzy --album "pics/extracted/Izzy Pics"

Prints the automatic numbers, then writes review.html — a contact sheet of
sampled detections with one-key tagging. Tag a hundred, paste the tally
back, and the precision question is answered.
"""

import argparse
import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

from cache import Cache, Digests, param_key
from ingest import MEDIA_EXTS, VIDEO_EXTS, detect, parse_time
from render import CSS, Images
from ultralytics import YOLO

TAGS = [("pet", "The pet"), ("other-dog", "Another dog"),
        ("other-animal", "Other animal"), ("none", "No animal")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roll", type=Path, help="a raw DCIM pull, not an album")
    ap.add_argument("--pet", default="the pet")
    ap.add_argument("--album", type=Path, action="append", default=[],
                    help="an album folder to compare against; repeatable")
    ap.add_argument("--sample", type=int, default=100)
    ap.add_argument("--out", type=Path, default=Path("review.html"))
    ap.add_argument("--conf", type=float, default=0.30)
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--cache", type=Path, default=Path(__file__).resolve().parent / ".cache")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    paths = sorted(p for p in args.roll.rglob("*")
                   if p.suffix.lower() in MEDIA_EXTS | VIDEO_EXTS)
    if not paths:
        raise SystemExit(f"no media under {args.roll}")
    in_album = {p.name for a in args.album for p in a.rglob("*")
                if p.suffix.lower() in MEDIA_EXTS | VIDEO_EXTS}

    digests, cache = Digests(args.cache), Cache(args.cache, "detect")
    model, rows = YOLO(args.model), []
    print(f"Scanning {len(paths)} files from {args.roll}")
    for i, path in enumerate(paths, 1):
        if i % 200 == 0:
            print(f"  {i}/{len(paths)}")
        if path.suffix.lower() in VIDEO_EXTS:
            continue
        key = param_key(digests.of(path), args.model, args.conf)
        det = cache.get_json(key)
        if det is None:
            try:
                det = detect(model, path, args.conf)
                cache.put_json(key, det)
            except Exception:
                continue
        rows.append({"path": path, "name": path.name, "album": path.name in in_album,
                     "taken": parse_time(path, {})[0], **det})
    digests.save()

    animals = [r for r in rows if r["pet"]]
    album_rows = [r for r in rows if r["album"]]
    hidden = [r for r in animals if not r["album"]]
    print(f"\nRAW ROLL — {len(rows)} photos")
    print(f"  detector flagged an animal: {len(animals)} ({len(animals)/len(rows):.1%})")
    if in_album:
        print(f"  also present in the album:  {len(album_rows)} ({len(album_rows)/len(rows):.1%})")
        print(f"  album photos the detector missed: "
              f"{sum(1 for r in album_rows if not r['pet'])}")
        print(f"  flagged but NOT in the album: {len(hidden)}"
              f"  <- what the album excluded, and the number that matters")
    print(f"  detector labels: {dict(Counter(r.get('species') for r in animals).most_common())}")

    random.seed(args.seed)
    pick = random.sample(animals, min(args.sample, len(animals)))
    pick.sort(key=lambda r: r["taken"] or "")
    print(f"\nSampling {len(pick)} detections for review")

    assets = Images(Cache(args.cache, "crops"), digests, args.out, True, True)
    cells = []
    for r in pick:
        try:
            src = assets.crop(r["path"], r["box"], 190, 70)
        except Exception:
            continue
        cells.append(
            f'<figure data-k="{r["name"]}" data-album="{int(r["album"])}" tabindex="0">'
            f'<img src="{src}" alt="" loading="lazy">'
            f'<figcaption>{(r["taken"] or "")[:10]}'
            f'{" &middot; in album" if r["album"] else ""}</figcaption></figure>')
    assets.finish()

    html = f"""<meta charset="utf-8">
<title>Raw roll review</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
  gap:14px; margin-top:28px; }}
.grid figure {{ margin:0; cursor:pointer; border:2px solid transparent; border-radius:5px;
  padding:4px; background:var(--raise); }}
.grid figure:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
.grid img {{ width:100%; aspect-ratio:1; object-fit:cover; border-radius:3px; display:block; }}
.grid figcaption {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px;
  color:var(--faint); margin-top:6px; }}
.grid figure[data-t="pet"] {{ border-color:var(--accent); }}
.grid figure[data-t="other-dog"] {{ border-color:#C2603A; }}
.grid figure[data-t="other-animal"] {{ border-color:var(--sage); }}
.grid figure[data-t="none"] {{ border-color:var(--faint); opacity:.45; }}
.grid figure[data-t]::after {{ content:attr(data-t); font-family:"IBM Plex Mono",monospace;
  font-size:10px; color:var(--soft); }}
.bar {{ position:sticky; top:0; z-index:9; background:var(--paper);
  border-bottom:1px solid var(--rule); padding:13px 0; display:flex; gap:10px;
  align-items:center; flex-wrap:wrap; font-family:"IBM Plex Mono",monospace; font-size:12px; }}
.bar b {{ color:var(--accent); }}
.k {{ border:1px solid var(--rule); border-radius:999px; padding:4px 11px; color:var(--soft); }}
textarea {{ width:100%; height:80px; font-family:"IBM Plex Mono",monospace; font-size:11px;
  border:1px solid var(--rule); border-radius:4px; padding:8px; background:var(--raise);
  color:var(--ink); margin-top:10px; }}
</style>

<div class="wrap">
  <header style="padding:44px 0 10px">
    <p class="eyebrow">Issue #32 &middot; what the album was hiding</p>
    <h1 style="font-size:54px">Raw roll</h1>
    <p class="dek">{len(animals):,} of {len(rows):,} photos in this camera roll tripped the
    animal detector. Tag a sample so we know how many are actually {args.pet} &mdash;
    <b>that number decides whether the product can read a camera roll, or only an album.</b></p>
  </header>
  <div class="bar">
    <span>Click a photo, or focus it and press:</span>
    {"".join(f'<span class="k">{i+1} {lab}</span>' for i, (_, lab) in enumerate(TAGS))}
    <span style="margin-left:auto">tagged <b id="n">0</b>/{len(cells)}</span>
  </div>
  <div class="grid" id="g">{"".join(cells)}</div>
  <div style="padding:30px 0 60px">
    <h2 style="font-size:22px">Tally</h2>
    <p class="lede" id="tally">Nothing tagged yet.</p>
    <textarea id="out" readonly></textarea>
  </div>
</div>

<script>
const TAGS = {json.dumps([t for t, _ in TAGS])};
const R = {{}};
const g = document.getElementById('g');

function paint() {{
  const n = Object.keys(R).length;
  document.getElementById('n').textContent = n;
  const c = {{}};
  for (const v of Object.values(R)) c[v] = (c[v] || 0) + 1;
  const pet = c['pet'] || 0;
  document.getElementById('tally').innerHTML = n
    ? TAGS.map(t => t + ': <b>' + (c[t] || 0) + '</b>').join(' &middot; ')
      + ' &mdash; precision of "any animal = the pet" is <b>'
      + (100 * pet / n).toFixed(0) + '%</b>'
    : 'Nothing tagged yet.';
  document.getElementById('out').value = JSON.stringify(
    {{tagged: n, counts: c, precision: n ? pet / n : null, tags: R}}, null, 1);
}}

function tag(fig, t) {{
  R[fig.dataset.k] = t;
  fig.dataset.t = t;
  paint();
  const next = fig.nextElementSibling;
  if (next) next.focus();
}}

g.addEventListener('click', e => {{
  const f = e.target.closest('figure');
  if (!f) return;
  const cur = TAGS.indexOf(f.dataset.t || '');
  tag(f, TAGS[(cur + 1) % TAGS.length]);
}});
g.addEventListener('keydown', e => {{
  const f = e.target.closest('figure');
  if (!f || !/^[1-9]$/.test(e.key)) return;
  e.preventDefault();
  if (TAGS[Number(e.key) - 1]) tag(f, TAGS[Number(e.key) - 1]);
}});
paint();
</script>
"""
    args.out.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out} — open it, tag the sample, paste the tally into the issue")


if __name__ == "__main__":
    main()
