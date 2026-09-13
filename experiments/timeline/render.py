"""
Render the moment graph as a self-contained page — step 3 of the de-risking
plan (docs/product-vision.md §9): look at it and see whether it lands.

Every thumbnail is cropped on the detected pet box, so the contact sheet is
auto-framed. Nothing on the page was entered by a human.

Usage:
    uv run render.py --photos "/path/to/photos" --out izzy.html
"""

import argparse
import base64
import io
import json
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from PIL import Image, ImageOps

from cache import Cache, Digests, param_key

PAD = 0.34
RECIPE = 1  # bump when crop/wide geometry changes: cached bytes key off it

CSS = """
:root {
  --paper:#F5F4F1; --raise:#FFFFFF; --ink:#17181B; --soft:#5C5E63; --faint:#8E9096;
  --rule:#DEDCD6; --accent:#A8712F; --accent-soft:#E3D3BC; --sage:#6F7D68;
  --shadow:0 1px 2px rgba(20,18,14,.07), 0 8px 24px rgba(20,18,14,.06);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper:#111214; --raise:#191A1D; --ink:#EDECE8; --soft:#A2A4A9; --faint:#74767C;
    --rule:#2B2D31; --accent:#D6A05A; --accent-soft:#4A3C27; --sage:#93A389;
    --shadow:0 1px 2px rgba(0,0,0,.5), 0 10px 30px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"] {
  --paper:#111214; --raise:#191A1D; --ink:#EDECE8; --soft:#A2A4A9; --faint:#74767C;
  --rule:#2B2D31; --accent:#D6A05A; --accent-soft:#4A3C27; --sage:#93A389;
  --shadow:0 1px 2px rgba(0,0,0,.5), 0 10px 30px rgba(0,0,0,.35);
}
* { box-sizing:border-box; }
body {
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
  font-size:16px; line-height:1.6; -webkit-font-smoothing:antialiased;
}
.wrap { max-width:1180px; margin:0 auto; padding:0 28px; }
.tight { max-width:660px; }
h1,h2,h3 { font-family:Fraunces,Georgia,"Times New Roman",serif; text-wrap:balance;
  font-weight:600; margin:0; line-height:1.08; letter-spacing:-.012em; }
.mono { font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  font-variant-numeric:tabular-nums; }
.eyebrow { font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  font-size:11px; letter-spacing:.18em; text-transform:uppercase; color:var(--faint); }

/* masthead */
header { padding:76px 0 44px; }
h1 { font-size:clamp(64px,13vw,152px); font-optical-sizing:auto;
  font-variation-settings:"SOFT" 30,"WONK" 1; margin:14px 0 0; }
.dek { font-size:20px; color:var(--soft); max-width:46ch; margin:26px 0 0; }
.dek b { color:var(--ink); font-weight:600; }
.facts { display:flex; flex-wrap:wrap; gap:0; margin:44px 0 0;
  border-top:1px solid var(--rule); border-bottom:1px solid var(--rule); }
.fact { flex:1 1 150px; padding:20px 22px 18px; border-right:1px solid var(--rule); }
.fact:last-child { border-right:0; }
.fact .n { font-family:Fraunces,Georgia,serif; font-size:34px; line-height:1;
  font-variant-numeric:tabular-nums; display:block; }
.fact .l { font-size:12.5px; color:var(--faint); margin-top:7px; display:block; letter-spacing:.01em; }

section { padding:60px 0; border-top:1px solid var(--rule); }
.shead { display:flex; align-items:baseline; justify-content:space-between;
  gap:20px; flex-wrap:wrap; margin-bottom:8px; }
h2 { font-size:clamp(26px,3.4vw,38px); }
.lede { color:var(--soft); max-width:60ch; margin:14px 0 0; }

/* rhythm ribbon */
.ribbon { margin-top:36px; }
.bars { display:flex; align-items:flex-end; gap:2px; height:168px;
  padding-bottom:0; border-bottom:1px solid var(--ink); }
.bar { flex:1 1 0; min-width:0; background:var(--accent); opacity:.82;
  border-radius:1.5px 1.5px 0 0; position:relative; }
.bar.lo { background:var(--accent-soft); }
.bar:hover { opacity:1; }
.bar::after { content:attr(data-tip); position:absolute; bottom:calc(100% + 7px);
  left:50%; transform:translateX(-50%); background:var(--ink); color:var(--paper);
  font-family:"IBM Plex Mono",monospace; font-size:11px; white-space:nowrap;
  padding:4px 8px; border-radius:4px; opacity:0; pointer-events:none; transition:opacity .12s; z-index:5; }
.bar:hover::after { opacity:1; }
.yearline { display:flex; gap:2px; margin-top:9px; }
.yearline span { flex-grow:0; font-family:"IBM Plex Mono",monospace; font-size:11.5px;
  color:var(--faint); border-left:1px solid var(--rule); padding-left:6px; }
.note { margin-top:20px; color:var(--soft); font-size:15px; max-width:62ch; }

/* strips + sheets */
.strip { display:flex; gap:12px; overflow-x:auto; padding:28px 0 6px; }
.strip figure { margin:0; flex:0 0 186px; }
.strip img, .sheet img, .hero img { display:block; width:100%; height:auto;
  background:var(--rule); }
.strip img { aspect-ratio:1; object-fit:cover; border-radius:3px; }
.strip figcaption { font-family:"IBM Plex Mono",monospace; font-size:11.5px;
  color:var(--faint); margin-top:8px; }

.chapter { padding:72px 0; border-top:1px solid var(--rule); }
.chead { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(0,1fr);
  gap:38px; align-items:end; }
.hero img { width:100%; aspect-ratio:4/3; object-fit:cover; border-radius:4px;
  box-shadow:var(--shadow); }
.cmeta h3 { font-size:clamp(30px,4vw,46px); }
.cdates { font-family:"IBM Plex Mono",monospace; font-size:13px; color:var(--accent);
  margin-top:12px; letter-spacing:.01em; }
.cstats { list-style:none; padding:0; margin:22px 0 0; border-top:1px solid var(--rule); }
.cstats li span { display:flex; align-items:center; gap:7px; }
.cstats li { display:flex; justify-content:space-between; gap:16px;
  padding:9px 0; border-bottom:1px solid var(--rule); font-size:14px; color:var(--soft); }
.cstats b { color:var(--ink); font-weight:600; font-family:"IBM Plex Mono",monospace;
  font-variant-numeric:tabular-nums; }
/* day heatmap */
.heat { margin-top:30px; overflow-x:auto; padding-bottom:4px; }
.heatgrid { display:grid; grid-auto-flow:column; grid-template-rows:repeat(7,11px);
  gap:3px; width:max-content; }
.hc { display:inline-block; width:11px; height:11px; border-radius:2px; background:var(--rule);
  border:0; padding:0; cursor:default; }
.hc.pad { background:transparent; }
.hc.l1 { background:var(--accent); opacity:.28; }
.hc.l2 { background:var(--accent); opacity:.48; }
.hc.l3 { background:var(--accent); opacity:.72; }
.hc.l4 { background:var(--accent); opacity:1; }
.hc.l1,.hc.l2,.hc.l3,.hc.l4 { cursor:pointer; }
.hc:focus-visible, .sheet figure:focus-visible { outline:2px solid var(--accent);
  outline-offset:2px; }
.hmonths { display:grid; grid-auto-flow:column; gap:3px; width:max-content;
  margin-bottom:6px; font-family:"IBM Plex Mono",monospace; font-size:10.5px;
  color:var(--faint); }
.hlegend { display:flex; align-items:center; gap:7px; margin-top:12px;
  font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--faint); }
.hlegend .hc { cursor:default; }

/* contact sheet */
.sheet { display:grid; grid-template-columns:repeat(auto-fill,minmax(84px,1fr));
  grid-auto-flow:row dense; gap:5px; margin-top:30px; }
.sheet figure { margin:0; position:relative; cursor:zoom-in; border:0; padding:0;
  background:none; border-radius:2px; }
.sheet figure.s2 { grid-column:span 2; grid-row:span 2; }
.sheet figure.s3 { grid-column:span 3; grid-row:span 3; }
.sheet img { aspect-ratio:1; object-fit:cover; border-radius:2px; width:100%;
  height:100%; display:block; }
.sheet figure.open img { outline:2px solid var(--accent); outline-offset:1px; }
.sheet figure.flash img { animation:flash 1.5s ease-out; }
@keyframes flash { 0%,40% { outline:3px solid var(--accent); outline-offset:2px; }
  100% { outline:3px solid transparent; outline-offset:2px; } }
.who { position:absolute; left:0; right:0; bottom:0; height:3px;
  border-radius:0 0 2px 2px; pointer-events:none; }
.who.c0 { background:var(--accent); opacity:.85; }
.who.c1 { background:var(--sage); opacity:.9; }
.who.both { background:linear-gradient(90deg,var(--accent) 50%,var(--sage) 50%); }
.sheet figure.s2 .who, .sheet figure.s3 .who { height:4px; }
.badge { position:absolute; right:3px; bottom:3px; font-family:"IBM Plex Mono",monospace;
  font-size:9.5px; line-height:1; padding:2.5px 4px; border-radius:3px;
  background:rgba(0,0,0,.62); color:#fff; letter-spacing:.02em; pointer-events:none; }
.sheet figure.s2 .badge, .sheet figure.s3 .badge { font-size:11px; padding:3.5px 6px; }

/* expanded burst */
.det { grid-column:1/-1; background:var(--raise); border:1px solid var(--rule);
  border-radius:5px; padding:20px 20px 16px; margin:5px 0; }
.dethead { display:flex; justify-content:space-between; align-items:baseline;
  gap:18px; flex-wrap:wrap; margin-bottom:4px; }
.dethead h4 { margin:0; font-family:Fraunces,Georgia,serif; font-size:20px; font-weight:600; }
.detsub { font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--soft); }
.detsub b { color:var(--accent); font-weight:500; }
.detclose { border:1px solid var(--rule); background:none; color:var(--soft);
  font:inherit; font-size:12px; border-radius:999px; padding:4px 12px; cursor:pointer; }
.detclose:hover { color:var(--ink); border-color:var(--soft); }
.frames { display:flex; gap:7px; overflow-x:auto; padding:14px 0 6px; }
.frames figure { margin:0; flex:0 0 132px; cursor:default; }
.frames img { width:132px; height:132px; object-fit:cover; border-radius:3px; display:block; }
.frames figcaption { font-family:"IBM Plex Mono",monospace; font-size:10.5px;
  color:var(--faint); margin-top:5px; }
.frames .hero figcaption { color:var(--accent); }

/* contributors */
.rolls { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr));
  gap:0; margin-top:34px; border-top:1px solid var(--rule);
  border-bottom:1px solid var(--rule); }
.roll { padding:22px 24px; border-right:1px solid var(--rule); }
.roll:last-child { border-right:0; }
.roll h3 { font-size:25px; display:flex; align-items:center; gap:9px; }
.dot { width:10px; height:10px; border-radius:2px; display:inline-block; flex:0 0 auto; }
.dot.c0 { background:var(--accent); } .dot.c1 { background:var(--sage); }
.roll .cstats { margin-top:16px; border-top:0; }
.together { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
  gap:18px; margin-top:30px; }
.tog { background:var(--raise); border:1px solid var(--rule); border-radius:5px;
  padding:19px 20px 17px; }
.tog .n { font-family:Fraunces,Georgia,serif; font-size:37px; line-height:1;
  font-variant-numeric:tabular-nums; display:block; }
.tog .l { font-size:13px; color:var(--soft); margin-top:9px; display:block; }
.key { display:flex; flex-wrap:wrap; gap:16px; margin-top:22px;
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--faint); }
.key span { display:flex; align-items:center; gap:6px; }
.key i { width:16px; height:3px; border-radius:2px; display:inline-block; }
.marks { display:flex; flex-wrap:wrap; gap:8px; margin-top:26px; }
.mark { font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--soft);
  border:1px solid var(--rule); border-radius:999px; padding:5px 12px; background:var(--raise); }
.mark b { color:var(--accent); font-weight:500; }

/* coda */
.coda { background:var(--raise); border-top:1px solid var(--rule); padding:64px 0 80px; }
.coda h2 { font-size:30px; }
.rows { margin-top:30px; border-top:1px solid var(--rule); }
.row { display:grid; grid-template-columns:118px minmax(0,1fr); gap:24px;
  padding:17px 0; border-bottom:1px solid var(--rule); align-items:baseline; }
.row .k { font-family:"IBM Plex Mono",monospace; font-size:21px; color:var(--accent);
  font-variant-numeric:tabular-nums; }
.row .v { color:var(--soft); font-size:14.5px; }
.row .v b { color:var(--ink); font-weight:600; }
footer { padding:34px 0 60px; color:var(--faint); font-size:13px; }

@media (max-width:760px) {
  .chead { grid-template-columns:1fr; gap:26px; }
  .bars { height:120px; }
  .sheet { grid-template-columns:repeat(auto-fill,minmax(64px,1fr)); }
  .wrap { padding:0 18px; }
}
@media (prefers-reduced-motion:reduce) { * { transition:none !important; } }
"""


def crop(path: Path, box, px: int, quality: int, pad: float = PAD) -> bytes:
    """Square crop centred on the detected pet, encoded as JPEG."""
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    W, H = img.size
    if box:
        x0, y0, x1, y1 = box[0] * W, box[1] * H, box[2] * W, box[3] * H
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        side = max(x1 - x0, y1 - y0) * (1 + pad)
    else:
        cx, cy, side = W / 2, H / 2, min(W, H)
    side = min(max(side, 64), min(W, H))
    cx = min(max(cx, side / 2), W - side / 2)
    cy = min(max(cy, side / 2), H - side / 2)
    out = img.crop((int(cx - side / 2), int(cy - side / 2),
                    int(cx + side / 2), int(cy + side / 2))).resize((px, px), Image.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()


def wide(path: Path, box, px: int, quality: int) -> bytes:
    """4:3 hero framed around the pet but keeping the scene."""
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    W, H = img.size
    tw, th = px, int(px * 3 / 4)
    scale = max(tw / W, th / H)
    img = img.resize((max(int(W * scale), tw), max(int(H * scale), th)), Image.LANCZOS)
    W, H = img.size
    cx = (box[0] + box[2]) / 2 * W if box else W / 2
    cy = (box[1] + box[3]) / 2 * H if box else H / 2
    left = int(min(max(cx - tw / 2, 0), W - tw))
    top = int(min(max(cy - th / 2, 0), H - th))
    buf = io.BytesIO()
    img.crop((left, top, left + tw, top + th)).save(
        buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()


class Images:
    """Encode once, deliver per mode: a data URI, or a file and a relative URL.

    The cache key is the source file's content digest plus every parameter that
    reaches the encoder, so a changed --thumb or a re-detected box misses while
    an untouched photo hits forever.
    """

    def __init__(self, cache: Cache, digests: Digests, out: Path,
                 external: bool, read: bool):
        self.cache, self.digests, self.read = cache, digests, read
        self.dir = out.with_name(out.stem + "_assets") if external else None
        self.written = set()
        if self.dir:
            self.dir.mkdir(exist_ok=True)

    def crop(self, path: Path, box, px: int, quality: int, pad: float = PAD) -> str:
        key = self._key(path, "crop", box, px, quality, pad)
        return self._ref(key, lambda: crop(path, box, px, quality, pad))

    def wide(self, path: Path, box, px: int, quality: int) -> str:
        key = self._key(path, "wide", box, px, quality)
        return self._ref(key, lambda: wide(path, box, px, quality))

    def _key(self, path: Path, kind: str, box, *params) -> str:
        return param_key(self.digests.of(path), RECIPE, kind,
                         json.dumps(box, separators=(",", ":")), *params)

    def _ref(self, key: str, encode) -> str:
        data = self.cache.get(key, ".jpg") if self.read else None
        if data is None:
            data = encode()
            self.cache.put(key, data, ".jpg")
        if self.dir is None:
            return "data:image/jpeg;base64," + base64.b64encode(data).decode()
        if key not in self.written:
            (self.dir / f"{key}.jpg").write_bytes(data)
            self.written.add(key)
        return f"{self.dir.name}/{key}.jpg"

    def finish(self) -> tuple[int, int]:
        """Drop assets left over from earlier parameters, then measure."""
        if self.dir is None:
            return 0, 0
        for p in self.dir.glob("*.jpg"):
            if p.stem not in self.written:
                p.unlink()
        return len(self.written), sum(p.stat().st_size for p in self.dir.glob("*.jpg"))


def pretty(d: str) -> str:
    return datetime.fromisoformat(d).strftime("%b %-d, %Y")


def chapter_split(inside: list[dict], order: list[str]) -> str:
    """Per-chapter moment counts by whose roll they came from."""
    if len(order) < 2:
        return ""
    rows = []
    for i, who in enumerate(order):
        n = sum(1 for m in inside if who in m["contributors"])
        if n:
            rows.append(f'<li><span><i class="dot c{i % 4}"></i> {who}</span><b>{n}</b></li>')
    both = sum(1 for m in inside if m["co_attended"])
    if both:
        rows.append(f'<li><span>Both shooting</span><b>{both}</b></li>')
    return "".join(rows)


def cell(m: dict, src: str, name: str, order: list[str]) -> str:
    """One contact-sheet cell. Size encodes how hard the moment was shot,
    the stripe along the bottom says whose roll it came out of."""
    n = m["media_count"]
    size = "s3" if n >= 12 else "s2" if n >= 6 else ""
    badge = f'<span class="badge">{n}</span>' if n > 1 else ""
    who = m["contributors"]
    stripe = "both" if len(who) > 1 else f"c{order.index(who[0]) % 4}" if who else ""
    label = (f'{pretty(m["date"])}, {n} frame{"" if n == 1 else "s"}'
             f'{" · " + " and ".join(who) if who else ""}')
    return (f'<figure class="{size}" data-m="{m["id"]}" data-date="{m["date"]}" '
            f'tabindex="0" role="button" aria-label="{label}" title="{label}">'
            f'<img src="{src}" alt="{name}, {pretty(m["date"])}" loading="lazy">'
            f'{badge}<i class="who {stripe}"></i></figure>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("moments.json"))
    ap.add_argument("--photos", type=Path, help="unused; paths travel in the data")
    ap.add_argument("--out", type=Path, default=Path("timeline.html"))
    ap.add_argument("--thumb", type=int, default=200)
    ap.add_argument("--quality", type=int, default=68)
    ap.add_argument("--frame", type=int, default=152, help="burst frame size")
    ap.add_argument("--frame-quality", type=int, default=64)
    ap.add_argument("--max-frames", type=int, default=9,
                    help="burst frames encoded per moment")
    ap.add_argument("--assets", choices=("external", "inline"), default="external",
                    help="external: sibling <out>_assets/ folder; inline: base64 in the page")
    ap.add_argument("--cache", type=Path, default=Path(__file__).resolve().parent / ".cache")
    ap.add_argument("--no-cache", action="store_true",
                    help="re-encode everything; still writes the cache")
    args = ap.parse_args()

    digests = Digests(args.cache)
    assets = Images(Cache(args.cache, "crops"), digests, args.out,
                    args.assets == "external", not args.no_cache)

    d = json.loads(args.data.read_text())
    name = d["pet"]["name"]
    moments = [m for m in d["moments"]
               if m["has_pet"] and m["dated"] and not m.get("before_anchor")]
    by_id = {m["id"]: m for m in moments}
    files = {m["id"]: Path(m["hero_path"]) for m in moments}

    print(f"Encoding {len(moments)} thumbnails at {args.thumb}px")
    thumbs = {}
    for i, m in enumerate(moments, 1):
        if i % 100 == 0:
            print(f"  {i}/{len(moments)}")
        try:
            thumbs[m["id"]] = assets.crop(files[m["id"]], m["hero_box"], args.thumb, args.quality)
        except Exception as e:
            print(f"  skip {m['hero']}: {e}")

    # ---- rhythm ribbon: one bar per month across the whole archive
    months = Counter(m["date"][:7] for m in moments)
    first, last = min(months), max(months)
    seq, y, mo = [], int(first[:4]), int(first[5:7])
    while (y, mo) <= (int(last[:4]), int(last[5:7])):
        seq.append(f"{y:04d}-{mo:02d}")
        y, mo = (y + 1, 1) if mo == 12 else (y, mo + 1)
    peak = max(months.values())
    bars = "".join(
        f'<div class="bar{"" if months.get(k,0) > peak*.22 else " lo"}" '
        f'style="height:{max(months.get(k,0)/peak*100, 1.4):.1f}%" '
        f'data-tip="{datetime.strptime(k,"%Y-%m").strftime("%b %Y")} · '
        f'{months.get(k,0)} moment{"" if months.get(k,0)==1 else "s"}"></div>'
        for k in seq)
    ylabels = "".join(
        f'<span style="flex-grow:{sum(1 for k in seq if k[:4]==yr)}">{yr}</span>'
        for yr in sorted({k[:4] for k in seq}))

    # ---- on this day
    today = date.today()
    key = today.strftime("%m-%d")
    onthis = [m for m in moments if m["date"][5:] == key]
    if not onthis:
        onthis = sorted(moments, key=lambda m: abs(
            (datetime.fromisoformat(m["date"]).timetuple().tm_yday - today.timetuple().tm_yday)))[:5]
    onthis = onthis[:6]
    strip = "".join(
        f'<figure><img src="{thumbs[m["id"]]}" alt="{name} on {pretty(m["date"])}" loading="lazy">'
        f'<figcaption>{pretty(m["date"])}<br>{today.year - int(m["date"][:4])} years ago</figcaption></figure>'
        for m in onthis if m["id"] in thumbs)

    # ---- chapters
    marks_by_era = {}
    for ms in d["milestones"]:
        for e in d["eras"]:
            if e["start"] <= ms["date"] <= e["end"]:
                marks_by_era.setdefault(e["id"], []).append(ms)
                break

    order = list(d["source"]["rolls"]) if "rolls" in d["source"] else []
    mg = d.get("merge", {})

    # ---- burst frames: every non-hero frame in a multi-frame moment
    by_name = {x["file"]: x for x in d["media"]}
    todo = [(m, f) for m in moments if m["media_count"] > 1
            for f in m["files"][:args.max_frames] if f != m["hero"]]
    print(f"Encoding {len(todo)} burst frames at {args.frame}px")
    bursts = {}
    for i, (m, fname) in enumerate(todo, 1):
        if i % 200 == 0:
            print(f"  {i}/{len(todo)}")
        row = by_name.get(fname, {})
        try:
            src = assets.crop(Path(row["path"]), row.get("box"), args.frame, args.frame_quality)
        except Exception:
            continue
        off = int((datetime.fromisoformat(row["taken_at"])
                   - datetime.fromisoformat(m["started_at"])).total_seconds())
        bursts.setdefault(m["id"], []).append(
            {"s": src, "t": off, "k": row.get("kind", "photo"),
             "w": row.get("contributor", "")})

    def offset(m):
        return int((datetime.fromisoformat(
            by_name[m["hero"]]["taken_at"]) - datetime.fromisoformat(m["started_at"])
        ).total_seconds()) if m["hero"] in by_name else 0

    detail = {m["id"]: {
        "d": datetime.fromisoformat(m["started_at"]).strftime("%A, %B %-d, %Y"),
        "c": datetime.fromisoformat(m["started_at"]).strftime("%-I:%M %p").lower(),
        "n": m["media_count"], "sp": m["span_seconds"], "p": m["with_people"],
        "dev": m["device"] or "", "ht": offset(m), "f": bursts.get(m["id"], []),
        "hw": m.get("hero_by", ""), "who": m.get("contributors", []),
        "trunc": max(0, m["media_count"] - args.max_frames),
    } for m in moments}

    print("Encoding chapter heroes")
    chapters = []
    for e in d["eras"]:
        hero_m = next((m for m in moments if m["hero"] == e["hero"]), None)
        hero = assets.wide(Path(hero_m["hero_path"]) if hero_m else files[moments[0]["id"]],
                           hero_m["hero_box"] if hero_m else None, 1300, 80)
        inside = [m for m in moments if e["start"] <= m["date"] <= e["end"]]

        # day heatmap, one column per week, Sunday at the top
        per_day = Counter()
        for m in inside:
            per_day[m["date"]] += m["media_count"]
        counts = sorted(per_day.values())
        lo = datetime.fromisoformat(e["start"]).date()
        hi = datetime.fromisoformat(e["end"]).date()
        lo -= timedelta(days=(lo.weekday() + 1) % 7)
        steps = [counts[int(len(counts) * q)] for q in (.5, .78, .93)] if counts else [1, 2, 3]
        cells, labels, day, week = [], [], lo, 0
        while day <= hi:
            n = per_day.get(day.isoformat(), 0)
            lvl = 0 if not n else 1 + sum(n > s for s in steps)
            inside_era = datetime.fromisoformat(e["start"]).date() <= day <= hi
            if not inside_era and n == 0:
                cells.append('<div class="hc pad"></div>')
            else:
                cells.append(
                    f'<button class="hc l{lvl}" data-date="{day.isoformat()}" '
                    f'aria-label="{day.strftime("%b %-d, %Y")}: {n} photo{"" if n == 1 else "s"}" '
                    f'title="{day.strftime("%b %-d, %Y")} · {n} photo{"" if n == 1 else "s"}"></button>')
            if day.weekday() == 5:  # Saturday closes a column
                labels.append(day.strftime("%b") if day.day <= 7 else "")
                week += 1
            day += timedelta(days=1)
        while len(labels) < week + 1:
            labels.append("")
        heat = (f'<div class="heat"><div class="hmonths">'
                f'{"".join(f"<span>{l}</span>" for l in labels)}</div>'
                f'<div class="heatgrid">{"".join(cells)}</div></div>'
                f'<div class="hlegend"><span>quieter</span>'
                f'{"".join(f"<span class=%r></span>" % f"hc l{i}" for i in range(5))}'
                f'<span>busier &mdash; click a day to find it below</span></div>')

        sheet = "".join(cell(m, thumbs[m["id"]], name, order)
                        for m in inside if m["id"] in thumbs)
        marks = "".join(
            f'<span class="mark"><b>{ms["label"]}</b> · {pretty(ms["date"])}</span>'
            for ms in marks_by_era.get(e["id"], []))
        days = (datetime.fromisoformat(e["end"]) - datetime.fromisoformat(e["start"])).days + 1
        chapters.append(f"""
<article class="chapter"><div class="wrap">
  <div class="chead">
    <div class="hero"><img src="{hero}" alt="{name}, {e['label']}" loading="lazy"></div>
    <div class="cmeta">
      <p class="eyebrow">Chapter {e['index'] + 1}</p>
      <h3>{e['label']}</h3>
      <p class="cdates">{pretty(e['start'])} &ndash; {pretty(e['end'])}</p>
      <ul class="cstats">
        <li><span>Moments</span><b>{e['moments']}</b></li>
        <li><span>Photos kept</span><b>{e['media']}</b></li>
        <li><span>With her people</span><b>{e['with_people']}</b></li>
        {chapter_split(inside, order)}
        <li><span>Days covered</span><b>{days}</b></li>
      </ul>
    </div>
  </div>
  {heat}
  {f'<div class="marks">{marks}</div>' if marks else ''}
  <div class="sheet">{sheet}</div>
</div></article>""")

    merge_section = ""
    if len(order) > 1 and mg:
        cards = []
        for i, who in enumerate(order):
            r = mg["per_roll"][who]
            cards.append(f"""<div class="roll">
      <h3><span class="dot c{i % 4}"></span>{who}</h3>
      <ul class="cstats">
        <li><span>Photos of {name}</span><b>{r['media']:,}</b></li>
        <li><span>Moments</span><b>{r['moments']}</b></li>
        <li><span>Days only they have</span><b>{r['days_only_theirs']}</b></li>
        <li><span>Goes back to</span><b>{pretty(r['earliest'])}</b></li>
      </ul></div>""")
        first = min(mg["per_roll"].items(), key=lambda kv: kv[1]["earliest"])
        merge_section = f"""
<section><div class="wrap">
  <div class="shead"><h2>Two rolls, one dog</h2>
  <p class="eyebrow">{len(order)} contributors</p></div>
  <p class="lede">Neither phone holds the whole story. These are two camera
  rolls that were never shared, never synced and never organised, merged on
  nothing but timestamps and a detector that knows what a dog looks like.</p>
  <div class="rolls">{''.join(cards)}</div>
  <div class="together">
    <div class="tog"><span class="n">{mg['days_shared']}</span>
      <span class="l">days both of them were photographing her, out of
      {mg['days_total']} days with any photo at all</span></div>
    <div class="tog"><span class="n">{mg['co_attended_moments']}</span>
      <span class="l">moments built from both rolls at once — the same event,
      two cameras, stitched by time</span></div>
    <div class="tog"><span class="n">{mg['shared_copies']}</span>
      <span class="l">files that were the same photo in both rolls, texted
      between them at some point, kept once</span></div>
  </div>
  <p class="note">The earliest photo in the whole archive is
  <strong>{first[0]}&rsquo;s</strong>, from {pretty(first[1]['earliest'])}. One
  roll alone would have started the story later.</p>
  <div class="key">
    {''.join(f'<span><i style="background:var(--{"accent" if i == 0 else "sage"})"></i>{w} only</span>' for i, w in enumerate(order))}
    <span><i style="background:linear-gradient(90deg,var(--accent) 50%,var(--sage) 50%)"></i>both</span>
    <span>&mdash; the stripe under each thumbnail below</span>
  </div>
</div></section>"""

    s, src = d["stats"], d["source"]
    span = datetime.fromisoformat(moments[-1]["date"]) - datetime.fromisoformat(moments[0]["date"])
    yrs, rem = divmod(span.days, 365)
    gap = next((m for m in d["milestones"] if m["kind"] == "longest_gap"), None)
    burst = next((m for m in d["milestones"] if m["kind"] == "busiest_moment"), None)
    compression = s["media_with_pet"] / max(s["moments_with_pet"], 1)

    html = f"""<meta charset="utf-8">
<title>{name}, In Order</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style>

<header><div class="wrap">
  <p class="eyebrow">An archive nobody assembled</p>
  <h1>{name}</h1>
  <p class="dek">{yrs} years, {rem // 30} months of photographs, pulled out of a
  camera roll and put in order. <b>Nothing here was tagged, titled, sorted or
  chosen by a person.</b></p>
  <div class="facts">
    <div class="fact"><span class="n">{src['media_files']:,}</span><span class="l">files in the dump</span></div>
    <div class="fact"><span class="n">{s['media_with_pet']:,}</span><span class="l">contained {name}</span></div>
    <div class="fact"><span class="n">{s['moments_with_pet']}</span><span class="l">distinct moments</span></div>
    <div class="fact"><span class="n">{s['moments_with_people']}</span><span class="l">with a person in frame</span></div>
    <div class="fact"><span class="n">{len(d['eras'])}</span><span class="l">chapters</span></div>
  </div>
</div></header>

<section><div class="wrap">
  <div class="shead"><h2>The rhythm of paying attention</h2>
  <p class="eyebrow">{len(seq)} months</p></div>
  <p class="lede">One bar per month. The shape is the story: a puppy photographed
  relentlessly, a middle stretch where she is simply part of the furniture, and
  attention returning later.</p>
  <div class="ribbon">
    <div class="bars">{bars}</div>
    <div class="yearline">{ylabels}</div>
  </div>
  <p class="note">In {span.days:,} days, the longest {name} went unphotographed was
  <strong>{gap['label'].split('— ')[-1] if gap else 'n/a'}</strong>.</p>
</div></section>

{merge_section}

<section><div class="wrap">
  <div class="shead"><h2>On this day</h2>
  <p class="eyebrow">{today.strftime('%B %-d')}</p></div>
  <p class="lede">Retrieved without anyone asking, because the timeline knows what
  day it is. This is the part of the product that has to earn a daily open.</p>
  <div class="strip">{strip}</div>
</div></section>

{''.join(chapters)}

<div class="coda"><div class="wrap tight">
  <p class="eyebrow">What the machine actually did</p>
  <h2>The honest version</h2>
  <div class="rows">
    <div class="row"><span class="k">90%</span><span class="v">of the dump contained a
      detectable dog. <b>Detection alone was enough</b> — no individual pet ID was needed
      for a single-pet household.</span></div>
    <div class="row"><span class="k">{compression:.1f}&times;</span><span class="v">compression from
      files to moments. People burst-shoot: <b>{s['media_with_pet']:,} photos are really
      {s['moments_with_pet']} events</b>, the largest a {burst['label'].split('— ')[-1] if burst else ''} run.</span></div>
    <div class="row"><span class="k">0</span><span class="v">fields typed by a human. Chapters
      are anchored on the first photo's date, so <b>the gotcha day and every anniversary
      fell out of the data</b>.</span></div>
    <div class="row"><span class="k">{s['undated_media']}</span><span class="v">files had no
      EXIF and no date in the filename — screenshots and saved messages.
      <b>Held out rather than guessed at.</b></span></div>
    <div class="row"><span class="k">{s.get('before_anchor_media', 0)}</span><span class="v">photos of
      the <b>wrong dog</b> — other people's animals in a contributor's roll, years before
      {name} existed. Two files out of {s['media_with_pet']:,} were enough to drag the
      timeline's anchor back 2.5 years and invent two empty chapters, because an anchor
      built from a minimum has no defence against one outlier. Now the anchor is the first
      date photography actually <b>sustains</b>.</span></div>
    <div class="row"><span class="k">{len(src['devices'])}</span><span class="v">camera models
      ({', '.join(src['devices'])}) — one person upgrading phones, not three contributors.
      <b>Device is not a contributor.</b></span></div>
  </div>
</div></div>

<footer><div class="wrap tight">
  Built from {src['media_files']:,} files with an off-the-shelf detector. Every thumbnail is
  cropped to the detected animal, which is why the contact sheets are centred on {name}.
  Cell size is burst length &mdash; how many frames were taken before moving on.
</div></footer>

<script>
const M = {json.dumps(detail, separators=(',', ':'))};
const plural = (n, w) => n + ' ' + w + (n === 1 ? '' : 's');

function dur(s) {{
  if (s < 60) return plural(s, 'second');
  const m = Math.round(s / 60);
  return m < 60 ? plural(m, 'minute') : plural(Math.round(m / 60), 'hour');
}}

function closeBurst() {{
  document.querySelectorAll('.det').forEach(d => d.remove());
  document.querySelectorAll('.sheet figure.open').forEach(f => f.classList.remove('open'));
}}

function openBurst(fig) {{
  const was = fig.classList.contains('open');
  closeBurst();
  if (was) return;
  const d = M[fig.dataset.m];
  if (!d) return;
  fig.classList.add('open');

  const multi = (d.who || []).length > 1;
  const frames = d.f.map(f => ({{ src: f.s, t: f.t, w: f.w, hero: false }}));
  frames.push({{ src: fig.querySelector('img').src, t: d.ht, w: d.hw, hero: true }});
  frames.sort((a, b) => a.t - b.t);

  const strip = frames.map(f => {{
    const off = f.t === 0 ? 'start' : '+' + dur(f.t);
    const by = f.w && multi ? '<br>' + f.w : '';
    return '<figure class="' + (f.hero ? 'hero' : '') + '">'
      + '<img src="' + f.src + '" alt="" loading="lazy">'
      + '<figcaption>' + off + (f.hero ? ' &middot; pick' : '') + by + '</figcaption></figure>';
  }}).join('');

  const bits = [plural(d.n, 'frame')];
  if (d.n > 1 && d.sp > 0) bits.push('over ' + dur(d.sp));
  if (d.p) bits.push('with a person in frame');
  if (multi) bits.push('shot by ' + d.who.join(' and '));
  if (d.trunc) bits.push('showing first ' + (d.f.length + 1) + ' of ' + d.n);
  if (d.dev) bits.push(d.dev);

  const el = document.createElement('div');
  el.className = 'det';
  el.innerHTML = '<div class="dethead"><div><h4>' + d.d + '</h4>'
    + '<p class="detsub">' + d.c + ' &middot; <b>' + bits[0] + '</b>'
    + (bits.length > 1 ? ' &middot; ' + bits.slice(1).join(' &middot; ') : '') + '</p></div>'
    + '<button class="detclose" type="button">Close</button></div>'
    + '<div class="frames">' + strip + '</div>';
  el.querySelector('.detclose').addEventListener('click', closeBurst);
  fig.after(el);
  el.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
}}

document.querySelectorAll('.sheet').forEach(sheet => {{
  sheet.addEventListener('click', e => {{
    const fig = e.target.closest('.sheet > figure');
    if (fig) openBurst(fig);
  }});
  sheet.addEventListener('keydown', e => {{
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const fig = e.target.closest('.sheet > figure');
    if (fig) {{ e.preventDefault(); openBurst(fig); }}
  }});
}});

document.querySelectorAll('.hc[data-date]').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const hit = document.querySelector('.sheet figure[data-date="' + btn.dataset.date + '"]');
    if (!hit) return;
    hit.scrollIntoView({{ block: 'center', behavior: 'smooth' }});
    hit.classList.remove('flash');
    void hit.offsetWidth;
    hit.classList.add('flash');
  }});
}});

document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeBurst(); }});
</script>
"""
    args.out.write_text(html, encoding="utf-8")
    digests.save()
    nassets, abytes = assets.finish()
    mb = len(html.encode()) / 1e6
    nframes = sum(len(v) for v in bursts.values())
    print(f"\nWrote {args.out} — {mb:.1f} MB")
    print(f"  {len(thumbs)} moment thumbnails, {nframes} burst frames, {len(chapters)} chapters")
    if assets.dir:
        print(f"  {nassets} assets in {assets.dir.name}/ — {abytes / 1e6:.1f} MB on disk")
    elif mb > 26:
        print("WARNING: very large for a single file; lower --frame or --thumb")
    print(f"  cache {assets.cache.rate}")


if __name__ == "__main__":
    main()
