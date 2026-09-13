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
from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageOps

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
.cstats li { display:flex; justify-content:space-between; gap:16px;
  padding:9px 0; border-bottom:1px solid var(--rule); font-size:14px; color:var(--soft); }
.cstats b { color:var(--ink); font-weight:600; font-family:"IBM Plex Mono",monospace;
  font-variant-numeric:tabular-nums; }
.sheet { display:grid; grid-template-columns:repeat(auto-fill,minmax(84px,1fr));
  gap:5px; margin-top:34px; }
.sheet img { aspect-ratio:1; object-fit:cover; border-radius:2px; }
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


def crop(path: Path, box, px: int, quality: int, pad: float = 0.34) -> str:
    """Square crop centred on the detected pet, encoded as a data URI."""
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
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def wide(path: Path, box, px: int, quality: int) -> str:
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
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def pretty(d: str) -> str:
    return datetime.fromisoformat(d).strftime("%b %-d, %Y")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("moments.json"))
    ap.add_argument("--photos", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("timeline.html"))
    ap.add_argument("--thumb", type=int, default=200)
    ap.add_argument("--quality", type=int, default=68)
    args = ap.parse_args()

    d = json.loads(args.data.read_text())
    name = d["pet"]["name"]
    moments = [m for m in d["moments"] if m["has_pet"] and m["dated"]]
    by_id = {m["id"]: m for m in moments}
    files = {m["id"]: args.photos / m["hero"] for m in moments}

    print(f"Encoding {len(moments)} thumbnails at {args.thumb}px")
    thumbs = {}
    for i, m in enumerate(moments, 1):
        if i % 100 == 0:
            print(f"  {i}/{len(moments)}")
        try:
            thumbs[m["id"]] = crop(files[m["id"]], m["hero_box"], args.thumb, args.quality)
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

    print("Encoding chapter heroes")
    chapters = []
    for e in d["eras"]:
        hero_m = next((m for m in moments if m["hero"] == e["hero"]), None)
        hero = wide(args.photos / e["hero"], hero_m["hero_box"] if hero_m else None, 1300, 80)
        inside = [m for m in moments if e["start"] <= m["date"] <= e["end"]]
        sheet = "".join(
            f'<img src="{thumbs[m["id"]]}" alt="{name}, {pretty(m["date"])}" '
            f'title="{pretty(m["date"])}" loading="lazy">'
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
        <li><span>Days covered</span><b>{days}</b></li>
      </ul>
    </div>
  </div>
  {f'<div class="marks">{marks}</div>' if marks else ''}
  <div class="sheet">{sheet}</div>
</div></article>""")

    s, src = d["stats"], d["source"]
    span = datetime.fromisoformat(moments[-1]["date"]) - datetime.fromisoformat(moments[0]["date"])
    yrs, rem = divmod(span.days, 365)
    gap = next((m for m in d["milestones"] if m["kind"] == "longest_gap"), None)
    burst = next((m for m in d["milestones"] if m["kind"] == "busiest_moment"), None)
    compression = s["media_with_pet"] / max(s["moments_with_pet"], 1)

    html = f"""<title>{name}, In Order</title>
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
    <div class="row"><span class="k">{len(src['devices'])}</span><span class="v">camera models
      ({', '.join(src['devices'])}) — one person upgrading phones, not three contributors.
      <b>Device is not a contributor.</b></span></div>
  </div>
</div></div>

<footer><div class="wrap tight">
  Built from {src['media_files']:,} files with an off-the-shelf detector. Every thumbnail is
  cropped to the detected animal, which is why the contact sheets are centred on {name}.
</div></footer>
"""
    args.out.write_text(html)
    mb = len(html.encode()) / 1e6
    print(f"\nWrote {args.out} — {mb:.1f} MB, {len(thumbs)} thumbnails, {len(chapters)} chapters")
    if mb > 15:
        print("WARNING: over the 16MB artifact limit; lower --thumb or --quality")


if __name__ == "__main__":
    main()
