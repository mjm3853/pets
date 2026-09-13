# Working log

Append-only. Newest at the bottom. **Never edit or delete a past entry** — if
something here turns out to be wrong, write a new entry saying so. The value
of this file is that it records what was believed at the time, including the
things that did not survive contact with data.

Decisions go in [decisions.md](decisions.md), open problems in
[ideas.md](ideas.md), the object model in [data-model.md](data-model.md).
This file is the narrative: what was tried, what happened, what it cost.

---

## 2026-09-13 — First real data

Started from a written product vision, nothing built. Critiqued it and found
the central weakness: the vision's wedge was auto-detection plus resurfacing,
both of which Apple Photos and Google Photos already ship for free. Reframed
the wedge as the pet as a **cross-person entity**, which neither platform
does because both are built around a single account (D6).

Household is Android plus a Mac, so the ingest path is `adb pull` from
`/sdcard/DCIM/Camera` and, later, ML Kit on-device (D7).

**First archive: 1,274 files, one dog, five years.** Detection found the pet
in 90% of files. The finding that reshaped everything: burst-clustering
collapsed 1,144 photos into 549 moments, 2.1×. A file is not a moment (D9).
Gap-based era segmentation produced a single era across five years, so
chapters became life years anchored on the first photo (D10), which derived
the gotcha day and every anniversary with no user input.

Cost: ~4 min to detect 1,274 files on CPU, ~3 min to render. Output was a
9.7 MB self-contained HTML page.

## 2026-09-13 — The past moved

A second export arrived, a clean superset: 708 new files, **all of them
earlier** than what had been the first photo. The real puppyhood, missing
from the first export entirely.

Re-ingesting moved the anchor 103 days earlier and changed 9 of 10
milestones, every chapter boundary and all five anniversaries. Worse,
**100% of 587 moment IDs were renumbered**, because they were positional.
Stale pointers did not error — each resolved to a different, plausible
photo. The "first photo" milestone silently pointed at an unrelated Tuesday.

That produced D13 (identity must never be positional) and D14 (the past is
never settled), and opened I1 as the standing writeup of the backfill
problem. This was the single most useful thing that happened to the project:
a bug class that would have shipped, caught by accident, on real data.

## 2026-09-13 — Made the sheet explorable

Added a per-chapter day-level heatmap, sized contact-sheet cells by burst
length, and made cells expand in place to show the whole burst in sequence
with seconds between frames.

The interesting bit is that **burst length is a free importance signal**.
Nobody rates their photos, but they keep shooting when something matters —
324 single-frame moments against a top of 31. No user effort, no model, and
it is strong enough to drive visual hierarchy.

Expanding a burst also shows something both platforms deliberately hide: the
retries. Eleven near-identical frames and the one that worked. For a dog that
is often the funniest thing in the archive, and it may be a real product
surface rather than a debug view.

Page reached 17.8 MB with 1,158 burst frames embedded as base64. That is the
point where storage stopped being free — see I4.

## 2026-09-13 — Second contributor

Renee's roll arrived: 2,422 files. Only **20 filenames overlap** with Matt's
1,982, so this is a genuine second camera roll, not a shared album — the
first actual test of D6, which the three-Pixel device succession in the first
archive could not provide (D12).

Two loops in the user experience came up in conversation and are written up
as I5: bulk onboarding versus ongoing maintenance. The sharp version is that
**onboarding never ends** — Renee's roll is an onboarding event arriving in
year five of steady state — and that the two loops need opposite notification
behaviour, which means ingest has to distinguish *taken-at* from
*ingested-at*. See I5.

## 2026-09-13 — The merge works, and two dogs nearly broke it

Ran both rolls together for the first time: 4,383 files after skipping 20
shared copies, 3,924 with a detected dog (90% again — the rate has now held
across three different archives), 1,378 moments.

**The D6 answer, and it is a good one.** Matt's roll alone covers 484 days
with photos. Renee's alone covers 490. Merged, 772. The merge adds **58%
more days than the better single roll**, and each of them holds close to 290
days the other has nothing for. 81 moments were built from both rolls at
once — the same event, two cameras, stitched on timestamps alone. Expanding
one of those shows six frames from Matt and then the best frame from Renee's
phone, which is the product thesis rendered literally.

Worth saying plainly: this is the first evidence that the wedge is real, and
it came from two ordinary phone exports with no shared album, no sync and no
coordination.

**Then the failure.** Renee's roll reaches back to 2018-11-21, two and a half
years before Izzy. Looked at the photos rather than assuming: a chihuahua mix
in 2018 and a beagle in 2019. Other people's dogs.

**Two files out of 3,924 — 0.05% — destroyed the chapter structure.** The
anchor moved back 2.5 years, two empty chapters appeared, every boundary
shifted from April to late November, and Izzy's actual first year got
relabelled "Year 3".

The cause is not bad detection, it is that the anchor was a **minimum**.
Extrema have no resistance to outliers by construction, so one stray photo
has unbounded leverage over the entire narrative spine. Replaced it with the
first date photography *sustains* (≥5 moments within 30 days), which restored
the six chapters and correctly quarantined both strays by name and
contributor rather than silently dropping them — they might be real for
someone else's archive, e.g. foster photos of a rescue.

This is the contamination D6 predicted for multi-contributor merging, arriving
on schedule and cheaper to find than expected. It also confirms that
individual pet ID becomes necessary the moment a second roll joins, though
notably *not* for the merge to be valuable — 0.05% contamination with a
robust anchor is entirely usable.

**Also built the rebuild path** (`--rebuild moments.json`), which recomputes
everything downstream of detection without re-running the model. Twenty
minutes became seconds. That is I4's caching premise validated on the first
try, and it is what made iterating on the anchor fix practical at all.

Page is now 23.2 MB. Single-file base64 is at the end of its useful life; see
I4 item 4.

## 2026-09-13 — Caching, and the page stops being a blob

Moved the backlog into GitHub issues (12, labelled now/next/later, with
`correctness` reserved for silent-wrong-answer risks since two of the three
real findings so far were that class). Then ran the three `now` issues as two
parallel subagents split by file, so they could not collide: detection cache
in `ingest.py`, crop cache plus external assets in `render.py`. Both landed
clean; I reviewed the diffs and re-ran everything myself rather than taking
the reports.

**The numbers are better than expected.**

| | cold | warm |
|---|---|---|
| ingest, 4,383 files | 6m25s | **4.8s** (100% hits) |
| render, 1,378 moments | 3m11s | **0.79s** (100% hits) |

Output byte-identical between cold and warm in both cases, checked section by
section on ingest (media, moments, eras, milestones, merge, stats).

**The page went from 23.2 MB to 1.1 MB** plus a 16.6 MB assets folder.
Verified in a browser with the cache moved aside: 1,389 images, zero data
URIs, all resolving from `izzy_assets/`, and an expanded burst's frames
resolving too — so the folder stands alone. `--assets inline` still emits the
single portable file, and because the cache key covers *encoding* rather than
*delivery*, that run reused the external run's cache and took 0.5s.

Two things worth remembering beyond the speed. First, iteration cost was the
real constraint all along — the anchor fix earlier today was painful only
because every attempt cost 20 minutes, and that class of pain is now gone.
Second, the cache key design is the interesting part: content digest plus
every parameter that reaches the encoder, which is tight in both directions.
Changing `--thumb` missed exactly the thumbnails and kept every frame and hero
as a hit. Too loose would have served stale images after a parameter change;
too tight would never hit at all.

Content digests were the point of the exercise as much as the speed — they
are what #4 (stable identity, D13) needs, and that is now mostly a matter of
adopting keys that already exist.

## 2026-09-13 — Correctness pass

Closed the three `correctness` issues. All small; two of them changed what the
page says, which is the point.

**#4, stable identity.** Moment ids are now a hash of their member media ids.
Tested against the exact scenario that produced 100% churn this morning: 696
moments with unchanged membership kept 100% of their ids, and of the 83 whose
membership genuinely changed, **zero** old ids still resolve. That second
number is the one that matters — a stale pointer now misses loudly instead of
landing on a different plausible photo. Membership change producing a new id is
correct, not a regression.

**#5, fragile superlatives — and it immediately caught real ones.** Each
superlative now carries the runner-up it beat. Two of three headline records
turned out to be coin flips: the 40-frame burst beat 36 by 10%, and the 22-day
quiet stretch beat 20 by 9%. They render as "close call" now. Worth sitting
with: the page had been stating both as facts, and nobody would have questioned
them. The quiet stretch is separately marked `shrinkable`, because it is the
one record an import can *falsify* rather than merely beat — it already went
36 → 22 days when Renee's roll merged.

**#6, taken-at vs ingested-at.** `ingested_at` is memoised on content digest,
so first sight survives re-runs and renames. Also the substrate for #7: "files
first seen this run" is now one query.

**#8 groundwork.** Added `--anchor` for a real adoption date. Kept the
quarantine logic on the *derived* anchor deliberately — outlier detection and
chapter-start are different jobs, and conflating them would mean a given date
could silently quarantine real moments. Matt is supplying the actual date.

Next is #9, individual pet ID, which is the heaviest remaining item and the one
that would have caught the two stray dogs automatically.

## 2026-09-13 — The anchor is a fact now, and it made a prologue

Matt gave the real adoption day: **9 Apr 2021**. The archive derives 7 Apr, so
the given date is two days *later* than the first photo.

That gap turned out to be the interesting part. Every prior assumption had the
anchor as the earliest thing in the archive, because a derived anchor is the
first photo by construction. A real anchor need not be: you photograph an
animal at the shelter before you bring them home. Those moments sit before
every chapter, and with the anchor moved they were about to fall out of the
timeline silently — not quarantined, not flagged, just absent from every
chunk.

They now get a **prologue chapter**. Here it is one five-frame moment from
7 Apr, with a person in frame: the day they met her, two days before she came
home. That is arguably the most loaded item in the whole archive and it
existed only as an accident of where a loop started.

Generalises well beyond this household. For a rescue or rehoming the
pre-adoption material — foster photos, shelter photos, the previous owner's
pictures — is often the entire origin story, and it all lands in exactly this
window. Worth remembering that the category is *invisible* until the anchor is
a fact rather than a guess.

Anchor persists to `pet.json`, so it is asked once and no import can move it
(D14, I1). Quarantine still keys off the derived anchor deliberately: outlier
detection and chapter-start are different jobs, and conflating them would let
a given date silently quarantine real moments.

## 2026-09-13 — Dropped pet recognition, and a useful negative result

Matt's call: don't invest in individual pet ID, leave it to the platforms and
to users, flag only what is obviously wrong. Recorded as D17.

Went looking for a cheap flag before closing it out, and found the opposite of
what was expected. The archive is a dog, so a detection labelled *sheep* ought
to be suspicious — free signal, no model needed. 294 files are labelled sheep,
horse, cat, cow, bird or bear. Cropped the twelve highest-confidence ones and
looked: **every single one is a dog.** A tan dog in profile scores 0.94 as
"sheep". So the heuristic would fire 294 times and be wrong 294 times, and
detector confidence gives no protection because it is confidently wrong.

Two things follow. The detector is a reliable *animal present* signal (90%
across three archives) and an unreliable *which animal* signal, so species
moved to a profile field the user sets rather than a majority vote over
detector labels. And the thing that actually caught both real stray dogs was
temporal — the pre-anchor quarantine (D16) — with no visual reasoning at all.

Worth keeping: the cheapest-looking signal was worthless and a much dumber one
worked. Checking cost about five minutes; building the clustering pipeline
would have cost a day and caught two photos.

Incidental: a second dog, dark and merle-patterned, appears throughout the
archive. Not an error — presumably a friend's or housemate's dog, and part of
Izzy's life. Nothing to fix, but a reminder that "other animals in frame" is
usually signal rather than noise.
