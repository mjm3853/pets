"""
The feed: the fewest, most meaningful moments for right now (issue #16, D18).

The timeline is the archive — everything, in order, good for sitting down
with. This is the front door: one to three moments, readable in under a
minute, different tomorrow. The vision's whole bet is that retention lives on
the consumption side, and nothing until now tested it.

The ranking is the product; the delivery is deliberately dumb. Signals are
things people already did, never things they were asked to enter.

    uv run feed.py                 # today
    uv run feed.py --date 2022-07-28 --n 3
"""

import argparse
import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from cache import Cache, Digests
from render import CSS, Images, nav, pretty

# What a moment is worth, and why. Every one of these is behaviour already
# recorded, not a rating anybody was asked for.
WEIGHTS = {
    "on_this_day": 3.0,    # the resurfacing hook; the reason to open it at all
    "new_old": 2.5,        # backfill just surfaced something old (I1)
    "burst": 1.4,          # people keep shooting when it matters
    "milestone": 1.2,      # near an anniversary or a first
    "together": 1.0,       # more than one pet in frame
    "co_attended": 0.9,    # both contributors were shooting the same event
    "people": 0.6,         # someone is in frame with the animal
    "rotation": 1.1,       # see below
}
NEW_OLD_WINDOW = 14   # days since a file first entered the system
NEW_OLD_AGE = 90      # ...and how much older than that the photo must be


def score(m: dict, ctx: dict) -> tuple[float, list[str]]:
    """Returns the score and the reasons, because the page shows the reason."""
    parts, why = {}, []
    t = datetime.fromisoformat(m["started_at"])

    years = int(ctx["today"][:4]) - int(m["date"][:4])
    if m["date"][5:] == ctx["today"][5:] and years > 0:
        parts["on_this_day"] = 1.0
        why.append(f"on this day, {years} year{'' if years == 1 else 's'} ago")

    ing = ctx["ingested"].get(m["id"])
    # Only interesting when it distinguishes something. On a first ingest every
    # file is "new", so the signal is true of everything and says nothing.
    if ctx["new_old_useful"] and ing and (ctx["now"] - ing).days <= NEW_OLD_WINDOW \
            and (ing - t).days >= NEW_OLD_AGE:
        parts["new_old"] = 1.0
        why.append("only just added, but years old")

    n = m["media_count"]
    if n > 1:
        parts["burst"] = min(n / 12, 1.0)
        if n >= 6:
            why.append(f"{n} frames in one go")

    near = ctx["milestones"].get(m["id"])
    if near:
        parts["milestone"] = 1.0
        why.append(near.lower())

    if len(m["appearances"]) > 1:
        parts["together"] = 1.0
        why.append(" and ".join(ctx["names"].get(a["pet"], a["pet"])
                                for a in m["appearances"]) + " together")

    if m["co_attended"]:
        parts["co_attended"] = 1.0
        why.append("both of you were shooting")

    if m["with_people"]:
        parts["people"] = 1.0

    # Without this the same three highest-scoring moments win every day and
    # the feed is a poster, not a feed. Seeded on the date so it is stable
    # within a day and different tomorrow, and weighted low enough that a real
    # anniversary still beats it.
    seed = hashlib.sha256(f'{m["id"]}{ctx["today"]}'.encode()).digest()
    parts["rotation"] = int.from_bytes(seed[:4], "big") / 2**32

    total = sum(WEIGHTS[k] * v for k, v in parts.items())
    return total, why


def build_context(d: dict, today: str) -> dict:
    ingested = {}
    by_file = {x["file"]: x for x in d["media"]}
    for m in d["moments"]:
        stamps = [by_file[f]["ingested_at"] for f in m["files"] if f in by_file]
        if stamps:
            ingested[m["id"]] = datetime.fromisoformat(max(stamps))
    near = {}
    for p in d["pets"]:
        for ms in p.get("milestones", []):
            if ms.get("moment"):
                near[ms["moment"]] = ms["label"]
    now = datetime.now()
    fresh = sum(1 for v in ingested.values() if (now - v).days <= NEW_OLD_WINDOW)
    return {"today": today, "now": now, "ingested": ingested,
            "milestones": near,
            "new_old_useful": bool(ingested) and fresh / len(ingested) < 0.25,
            "names": {p["id"]: p["name"] for p in d["pets"]}}


def pick(d: dict, today: str, n: int) -> list[tuple[dict, list[str]]]:
    """Top moments, spread out. Three shots from one afternoon is not a feed."""
    ctx = build_context(d, today)
    cands = [m for m in d["moments"]
             if m["appearances"] and m["dated"] and not m.get("before_anchor")]
    ranked = sorted(((*score(m, ctx), m) for m in cands), key=lambda r: -r[0])
    out, used_days, used_pets = [], set(), []
    for sc, why, m in ranked:
        if len(out) >= n:
            break
        if m["date"] in used_days:
            continue
        pets = {a["pet"] for a in m["appearances"]}
        # Don't show the same animal twice while another has something to say.
        if used_pets and pets <= set().union(*used_pets) and len(used_pets) < len(d["pets"]):
            continue
        used_days.add(m["date"])
        used_pets.append(pets)
        out.append((m, why))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("moments.json"))
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--out", type=Path, default=Path("feed.html"))
    ap.add_argument("--assets", choices=("external", "inline"), default="external")
    ap.add_argument("--cache", type=Path, default=Path(__file__).resolve().parent / ".cache")
    args = ap.parse_args()

    d = json.loads(args.data.read_text())
    picks = pick(d, args.date, max(1, min(args.n, 5)))
    if not picks:
        raise SystemExit("nothing to show")

    digests = Digests(args.cache)
    assets = Images(Cache(args.cache, "crops"), digests, args.out,
                    args.assets == "external", True)
    names = {p["id"]: p["name"] for p in d["pets"]}
    when = datetime.fromisoformat(args.date)

    cards = []
    for m, why in picks:
        img = assets.wide(Path(m["hero_path"]), m["hero_box"], 1100, 80)
        who = " and ".join(names.get(a["pet"], a["pet"]) for a in m["appearances"])
        years = when.year - int(m["date"][:4])
        ago = ("today" if m["date"] == args.date
               else f"{years} year{'' if years == 1 else 's'} ago" if years > 0
               else "earlier this year" if m["date"] < args.date
               else "later that year")
        extra = ""
        if m["media_count"] > 1:
            extra = (f' &middot; {m["media_count"]} frames'
                     f'{" over " + str(m["span_seconds"] // 60) + " min" if m["span_seconds"] > 90 else ""}')
        cards.append(f"""<article class="fcard">
  <img src="{img}" alt="{who}, {pretty(m['date'])}">
  <div class="fmeta">
    <p class="eyebrow">{why[0] if why else 'from the archive'}</p>
    <h2>{who}</h2>
    <p class="fwhen">{pretty(m['date'])} &middot; {ago}{extra}</p>
    {f'<p class="fwhy">{" &middot; ".join(why[1:])}</p>' if len(why) > 1 else ''}
  </div>
</article>""")

    digests.save()
    assets.finish()
    html = f"""<meta charset="utf-8">
<title>Today with the pets</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}
.feed {{ max-width:760px; margin:0 auto; padding:0 24px 70px; }}
.fhead {{ padding:44px 0 6px; }}
.fhead h1 {{ font-size:clamp(38px,7vw,62px); }}
.fcard {{ margin-top:34px; }}
.fcard img {{ width:100%; aspect-ratio:4/3; object-fit:cover; border-radius:5px;
  display:block; box-shadow:var(--shadow); background:var(--rule); }}
.fmeta {{ padding-top:14px; }}
.fmeta h2 {{ font-size:27px; margin-top:5px; }}
.fwhen {{ font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--accent);
  margin:8px 0 0; }}
.fwhy {{ font-size:14.5px; color:var(--soft); margin:6px 0 0; }}
.fdone {{ margin-top:52px; padding-top:22px; border-top:1px solid var(--rule);
  color:var(--faint); font-size:13.5px; }}
.fdone a {{ color:var(--accent); }}
</style>

{nav([p for p in d["pets"] if p["moments"]], None)}

<div class="feed">
  <div class="fhead">
    <p class="eyebrow">{when.strftime('%A, %B %-d')}</p>
    <h1>Today</h1>
  </div>
  {"".join(cards)}
  <p class="fdone">That is everything for today &mdash; {len(picks)} moment{"" if len(picks) == 1 else "s"}
  out of {sum(p['moments'] for p in d['pets'])}. The rest is not going anywhere:
  <a href="index.html">all the pets</a>.</p>
</div>
"""
    args.out.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out} for {args.date}")
    for m, why in picks:
        print(f"  {m['date']}  {', '.join(why) or 'highest scoring'}")


if __name__ == "__main__":
    main()
