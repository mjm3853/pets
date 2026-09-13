# Implementing an issue

Read this before starting any issue. It is short on purpose. Every issue
links here rather than repeating it.

## What you are building, and for whom

A pet's life timeline that assembles itself from camera rolls with **zero
human tagging**. The product bet (docs/product-vision.md) is that the value
is in *consumption* — resurfacing, recaps, a feed — not in capture. The
differentiator is merging **several people's** photos of one pet (D6). The
first real users are Matt and Renee and their dog Izzy, plus a friend's dog
who visits. Everything you build gets judged against those two rolls.

Before touching code, read [decisions.md](decisions.md) end to end. Fifteen
minutes. Every decision there was paid for with a real bug or a real
measurement, and several of them are non-obvious enough that a reasonable
engineer would reintroduce the bug by accident.

## Orientation

Everything lives in `experiments/timeline/`. Three files matter:

| file | what it is | entry points |
|---|---|---|
| `ingest.py` | photos → `moments.json` | `scan()` per roll · `detect()` · `build_moments()` · `find_anchor()` · `build_eras()` · `build_milestones()` · `build_merge_report()` · `main()` |
| `render.py` | `moments.json` → HTML | `crop()` / `wide()` encode · `Images` caches and delivers · `cell()` one sheet cell · `main()` holds the CSS, the page template and the JS |
| `cache.py` | content-hash cache | `Digests.of(path)` · `Cache.get/put(_json)` · `param_key()` |

`moments.json` is the whole data layer. Its top level is `pet`, `source`,
`merge`, `stats`, `eras`, `milestones`, `moments`, `media`. The shapes you
will touch most:

```
media    file id path contributor ingested_at taken_at time_source kind
         device gps width height pet people box score
moment   id started_at ended_at date span_seconds media_count pet_count
         has_pet dated hero_quality with_people kinds device gps
         hero hero_path hero_box hero_by contributors co_attended files
         before_anchor
era      id index label eyebrow start end moments media with_people hero
milestone kind date label moment value runner_up margin provisional
```

A moment is **the** unit. Media are storage. Never show media directly.

`pet.json` (gitignored, next to the scripts) holds what the user owns:
`anchor`, `species`. Read it, extend it, never derive over it.

## The fast loop

Nothing here should take more than a few seconds to iterate on:

```bash
uv run ingest.py --pet Izzy --rebuild moments.json      # ~2s, no model
uv run render.py --out izzy.html                        # ~1s warm
python3 -m http.server 8000                             # then open the page
```

`--rebuild` recomputes everything downstream of detection. Detection and
crops are cached on content hash in `.cache/`; a full cold ingest is ~6 min
and you should almost never need one. If you are waiting on the model, you
are probably doing it wrong.

## Rules that must survive your change

These are the decisions most likely to be broken by accident. Each one was a
real bug.

1. **Nothing is identified by position or sort order.** Moment ids are a
   hash of member media ids (D13). If you add an entity, give it a content
   or membership-derived id. A test: re-ingest with one extra photo, and the
   ids of everything unchanged must be identical.
2. **No user-visible fact is a raw min or max** (D15). Two misdetected
   photos moved the anchor 2.5 years. Anchors need a sustained-run test;
   superlatives carry their runner-up and a `provisional` flag. If you add a
   "most" or "first" or "longest", it needs an outlier story.
3. **Never place undated or suspicious media silently** (D11, D16). Held-out
   media is reported with filename and contributor. Guessing a date and
   dropping it in the spine is the worst outcome available.
4. **The detector says "an animal is present", never which animal** (D17).
   `species` comes from `pet.json`. Do not majority-vote detector labels; 294
   files in a dog archive are labelled sheep, horse, cat, cow, bird or bear
   and every one is a dog.
5. **`taken_at` and `ingested_at` are different fields for different jobs**
   (D8, issue #6). Resurfacing keys off when a photo *happened*; "what
   changed" keys off when it *arrived*. Confusing them fires 400
   notifications for old photos.
6. **The single-pet path stays exactly as fast and as automatic as today**
   (D19). Multi-pet and multi-person features pay their cost only where a
   second animal or person actually exists.
7. **Photos never enter git.** `*.jpg`, `*.json`, `*.html`, `*_assets/`,
   `.cache/` are ignored. Check `git status` before every commit. Output is
   private and stays local.
8. **Copy is plain.** Names, dates, counts. "With her people", not "her
   pawrents". Let the photos carry the feeling.

## How to think about it

**Cheapest thing that answers the question.** Most issues here are really
questions about the product wearing a feature's clothes. Before building the
full version, ask what the smallest thing is that would tell you whether the
full version is worth it. A script that regenerates a static page daily
tests "will they open a feed" as well as an app would.

**Measure before and after.** Every change that touches ingest should be
checked against the numbers in `experiments/timeline/README.md` — 4,403
files, 3,924 with an animal, 1,378 moments, 81 co-attended, day coverage
772. If a number moves and the issue did not intend it to, stop.

**Look at the actual photos.** Twice today a plausible heuristic was
disproven in five minutes by cropping a dozen detections and looking. Do
that before trusting any signal derived from the detector.

**Write down what surprised you.** `docs/log.md` is append-only; add a dated
entry for anything measured or learned, especially things that did not work.
The negative results in there are worth more than the features.

**Set up the next thing.** Each issue says what depends on it. If your
change makes that next thing harder, the design is wrong even if the issue
is satisfied.

## Definition of done

An issue is done when all of these are true:

- The change is verified against the real archive, not a toy — with the
  specific checks listed in the issue's *Verify* section, and the numbers
  reported in the closing comment.
- The single-roll and two-roll ingests still produce the counts in the
  README, or the issue explains why they changed.
- Nothing from the archive is staged (`git diff --cached --name-only`
  contains no `.jpg`, `.json`, `.html`).
- A dated entry in `docs/log.md` says what was learned, including anything
  that did not go as expected.
- The closing comment on the issue has the measurements — cold/warm timings,
  counts before and after, what was looked at — not just "done".
- If a decision was made or changed, it is in `docs/decisions.md` with
  status and reasoning. Chat history does not count.

## When you are stuck or something looks wrong

Do not paper over it. The most valuable moments today were a re-ingest that
renumbered everything, two stray dogs that broke the chapters, and a
"sheep" at 94% confidence — all of them caught because someone stopped and
looked instead of forcing the numbers to match. Write what you found in the
log, file an issue if it is out of scope, and say so in your report.
