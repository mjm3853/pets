"""
The front door: every pet, the moments they share, and the ones needing a
person's eye. Called by render.py --all (issue #34).

Together is the point. A friend opening their own dog's page sees only their
dog; what they have never seen is the overlap — the days two households were
photographing the same afternoon.
"""

import json

from render import CSS, burst_script, cell, nav, pretty


def build(d: dict, all_pets: list[dict], thumbs: dict, heroes: dict,
          order: list[str], detail: dict) -> str:
    pets = [p for p in all_pets if p["moments"]]
    moments = {m["id"]: m for m in d["moments"]}
    together = [m for m in d["moments"]
                if len(m["appearances"]) > 1 and m["dated"]]
    review = [m for m in d["moments"]
              if (m.get("needs_review") or m.get("unassigned")) and m["dated"]]
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
    # Group the queue by pet and island: six moments from one forgotten
    # fortnight on one old phone are a single question, not six.
    islands = [(p, i) for p in pets for i in p.get("islands", []) if i["review"]]
    islands.sort(key=lambda pi: (-pi[1]["review"], pi[1]["start"]))
    seen_ids, blocks = set(), []
    for pet, isl in islands:
        ms = [moments[i] for i in isl["ids"]
              if i in moments and moments[i].get("needs_review") and i not in seen_ids]
        if not ms:
            continue
        seen_ids.update(m["id"] for m in ms)
        span = (pretty(isl["start"]) if isl["start"] == isl["end"]
                else f'{pretty(isl["start"])} &ndash; {pretty(isl["end"])}')
        picks = "".join(
            f'<button class="pick" type="button" data-island="{isl["start"]}"'
            f' data-pet="{q["id"]}">{q["name"]}</button>' for q in all_pets)
        blocks.append(f"""<div class="island" data-ids="{",".join(m["id"] for m in ms)}">
  <div class="ihead">
    <div><b>{pet["name"]}</b> &middot; {span}
      <span class="imeta">{len(ms)} to check &middot; {", ".join(isl["devices"]) or "device unknown"}</span></div>
    <div class="iacts"><span class="lab">All of these are</span>{picks}</div>
  </div>
  <div class="sheet">{"".join(cell(m, thumbs[m["id"]], "", order)
                              for m in ms if m["id"] in thumbs)}</div>
</div>""")
    # A moment answered "not sure" leaves every pet and would otherwise leave
    # the queue too, unreachable forever. It is the one thing a person has
    # already looked at and could not place — it belongs at the top.
    loose = [m for m in d["moments"] if m.get("unassigned") and m["dated"]
             and m["id"] in thumbs]
    if loose:
        picks = "".join(
            f'<button class="pick" type="button" data-island="loose"'
            f' data-pet="{q["id"]}">{q["name"]}</button>' for q in all_pets)
        blocks.insert(0, f"""<div class="island" data-ids="{",".join(m["id"] for m in loose)}">
  <div class="ihead">
    <div><b>Not sure</b>
      <span class="imeta">{len(loose)} moment{"" if len(loose) == 1 else "s"} you looked at and could not place</span></div>
    <div class="iacts"><span class="lab">All of these are</span>{picks}</div>
  </div>
  <div class="sheet">{"".join(cell(m, thumbs[m["id"]], "", order) for m in loose)}</div>
</div>""")
    rev_sheet = "".join(blocks)

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
  animals end up in frame. They are grouped by the stretch of time they came
  from, because a run of photos from one forgotten fortnight on one old phone
  is usually <b>one question, not twenty</b>. Answer a whole group at once, or
  open any single moment to be specific.</p>
  {rev_sheet}
</div></section>

<footer><div class="wrap tight">
  Nothing here was chosen by a person except which album each photo came from.
  Chapters, anniversaries, bursts and overlaps are all derived.
</div></footer>

{burst_script(detail, all_pets)}
"""
