"""
The front door: every pet, the moments they share, and the ones needing a
person's eye. Called by render.py --all (issue #34).

Together is the point. A friend opening their own dog's page sees only their
dog; what they have never seen is the overlap — the days two households were
photographing the same afternoon.
"""

import json

from render import CSS, burst_script, cell, nav, pretty


def build(d: dict, pets: list[dict], thumbs: dict, heroes: dict,
          order: list[str], detail: dict) -> str:
    moments = {m["id"]: m for m in d["moments"]}
    together = [m for m in d["moments"]
                if len(m["appearances"]) > 1 and m["dated"]]
    review = [m for m in d["moments"] if m.get("needs_review") and m["dated"]]
    by_id = {p["id"]: p for p in pets}

    cards = []
    for p in pets:
        tag = "no timeline &mdash; fragments" if p["sparse"] else f"{len(p['eras'])} chapters"
        span = (f"{pretty(p['first_seen'])} &ndash; {pretty(p['last_seen'])}"
                if p["first_seen"] else "no dated moments")
        who = [c for c in p["contributors"] if c != "unknown"]
        cards.append(f"""<a class="card" href="{p['id']}.html">
  <img src="{heroes.get(p['id'], '')}" alt="{p['name']}" loading="lazy">
  <div class="body">
    <h3>{p['name']}</h3>
    <p class="meta">{p['moments']} moments &middot; {p['media']} photos<br>{span}<br>
    {', '.join(who) if who else 'contributor unknown'}</p>
    <span class="tag">{tag}</span>
  </div></a>""")

    def pairs(ms):
        out = {}
        for m in ms:
            k = tuple(sorted(a["pet"] for a in m["appearances"]))
            out[k] = out.get(k, 0) + 1
        return out

    combos = "".join(
        f'<span class="mark"><b>{" + ".join(by_id[x]["name"] for x in k if x in by_id)}</b>'
        f' &middot; {n} moment{"" if n == 1 else "s"}</span>'
        for k, n in sorted(pairs(together).items(), key=lambda kv: -kv[1]))

    tog_sheet = "".join(cell(m, thumbs[m["id"]], "", order)
                        for m in together if m["id"] in thumbs)
    rev_sheet = "".join(cell(m, thumbs[m["id"]], "", order)
                        for m in review if m["id"] in thumbs)

    total_media = sum(p["media"] for p in pets)
    return f"""<meta charset="utf-8">
<title>The pets</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style>

{nav(pets, None)}

<header><div class="wrap">
  <p class="eyebrow">{len(pets)} pets &middot; {total_media:,} photos</p>
  <h1 style="font-size:clamp(52px,10vw,110px)">The pets</h1>
  <p class="dek">Several people's photo albums of several animals, merged on
  timestamps alone. <b>Each pet has its own page. The interesting part is where
  they overlap.</b></p>
</div></header>

<section><div class="wrap">
  <div class="shead"><h2>Everyone</h2></div>
  <div class="cards">{"".join(cards)}</div>
</div></section>

<section id="together"><div class="wrap">
  <div class="shead"><h2>Together</h2>
  <p class="eyebrow">{len(together)} moments</p></div>
  <p class="lede">Moments holding more than one animal &mdash; the same afternoon,
  photographed by people who were not sharing an album. Nobody assembled these;
  they fell out of matching timestamps.</p>
  <div class="marks">{combos}</div>
  <div class="sheet">{tog_sheet}</div>
</div></section>

<section id="review"><div class="wrap">
  <div class="shead"><h2>Needs review</h2>
  <p class="eyebrow">{len(review)} moments</p></div>
  <p class="lede">These rest on an album alone, and an album is a hint rather than
  proof &mdash; hand-checking a sample of one found it <b>32% wrong</b>, because
  people build a pet's album out of the occasions that pet was around and both
  animals end up in frame. Open any of them and say who is actually there; the
  tray collects your answers.</p>
  <div class="sheet">{rev_sheet}</div>
</div></section>

<footer><div class="wrap tight">
  Nothing here was chosen by a person except which album each photo came from.
  Chapters, anniversaries, bursts and overlaps are all derived.
</div></footer>

{burst_script(detail, pets)}
"""
