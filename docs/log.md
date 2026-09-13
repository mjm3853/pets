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

## 2026-09-13 — Review: where this stands against the vision

Nineteen commits, one day, a working two-contributor timeline. Stopped to
review before building more. The critique lives in the conversation; the
next steps are issues #14–#21. The short version of the critique:

**Validated:** the capture inversion (90% detection across three archives,
zero human input); the pet as the organising entity; the multi-contributor
merge (58% more days than either roll alone, 81 moments from both cameras).
Two of the four core objects changed under real data — a moment is a burst,
a contributor is not a device — and both changes are load-bearing.

**Not validated, and the vision says these are the point:** the consumption
loop (resurfacing exists only as a static section; nothing tests whether it
earns a daily open); the outward artifact (Loop B, the stated growth engine,
has zero investment); permission friction (adb pull proves the pipeline,
not that anyone taps "Allow all"). The chills test was never closed
explicitly, and Renee — the second contributor — has not seen it.

**Overstated in the vision:** multi-contributor is "a genuine 10x". Measured,
it is 1.58× on coverage. Real and valuable; not 10×.

**Where the day over-invested:** UI polish. The heatmap and bento sizing are
delightful and answer no product question. The burst expansion earned its
place by surfacing the retries. The correctness pass and the caching were the
best hours of the day — cheap, and each caught something that would have
shipped wrong.

**Where it is still a demo:** it lives on one laptop, as a static page. The
gap between that and "someone else uses it" is the entire product, and #21
exists to stop that gap from being crossed by drift.

## 2026-09-13 — It landed

Matt and Renee looked at the merged timeline together over breakfast. "Lots
of great memories." That closes the vision's step 3 — the chills test — and
closes it with the second contributor, which is the version that mattered.
Issue #14.

What they wanted next reshaped two things.

**The front door is a feed.** Matt asked for something that surfaces the
fewest, most meaningful photos at a given time, bite-sized, for limited
attention. That is the consumption thesis stated as a product surface, and
it is the opposite of the contact sheet. Recorded as D18; issue #16 became
the feed. The ranking signals are all already in the data.

**There are more pets and more people than the model holds.** The merle dog
is a friend's — visits, dogsitting. Matt: people can have multiple pets;
model people, households, multiple pets, friends, family. Wrote the proposed
graph into data-model.md (person, pet, household, access, appearance) with
the one structural change — `moment.pet` → `moment.appearances[]` with
`assigned_by` — that lets multi-pet be in scope while recognition stays out.
Recorded as D19; issue #22.

The dogsitting case is the one to remember. A friend has your dog for a week
and takes forty photos; with a date-boxed caretaker edge they flow into her
timeline. That is the D6 merge generalised past the household, and it is the
thing shared albums cannot do. It has also already happened in reverse: Matt
and Renee hold photos of their friend's dog the friend has never seen.

**Postable means a movie, not a card.** Pause on a moment, dig in, package
it as an AI-assisted animation. Bursts are already stop-motion clips.
Neither of them is a social-media person, so the artifact should work in a
text thread as well as a feed — which broadens who the product is for.
Issue #15 rewritten.

Nothing built today after the review, deliberately.

## 2026-09-13 — Made the issues implementable

Matt asked whether the issues were detailed enough for a less capable model
to implement, and whether they set the implementer up to think big picture.
Honest answer was no: strong on why, weak on how. A fresh session would know
what the feed is for but not which function to open, what shape the data
has, what must not break, or how to prove it works.

Fixed in two layers. `docs/implementing.md` is written once and linked from
everywhere: orientation to the three files and the `moments.json` shapes, the
two-second iteration loop, the eight rules most likely to be broken by
accident (each one a real bug from today), how to think about an issue as a
question rather than a feature, and a definition of done that requires
measurements in the closing comment and a log entry. Then every open issue
got an *Implementation* section: big picture, exact files and functions,
data fields, ordered steps, a *Verify* list with the numbers to report, what
the issue sets up, and a *Don't* list. The two `validate` issues got a
protocol instead of code.

The guide is the more important half. The rules section exists because
every one of those rules was violated today by reasonable-looking code, and
a capable model working fresh would violate several of them again.

## 2026-09-13 — Prioritised, and drew the line on infrastructure

Matt asked whether the issues were prioritised, whether it was time to turn
this into a reusable product with auth, a database and deployment, or
whether more local learning loops came first.

The `next`/`later` labels were a tier, not an order. Replaced with three
milestones by intent — **Learn**, **Household #2**, **Product** — with
p1/p2/p3 inside each. The milestones are the argument: the three questions
the vision hangs on (feed, recap, permission) are cheap and unanswered; the
thing that breaks n=1 is a second household, which needs Takeout and a
one-command setup and no server at all; and everything infrastructural is
gated behind those.

Wrote the auth, data-location, deployment and threat-model stories anyway
(#23–#27), because the thinking is cheap and it stops someone building them
early. The honest content of each: authorisation is already solved by the
`access` model, so auth is just proving you are a person and a magic link
is enough; SQLite until it hurts; try a shared folder between two
households before writing a server; nothing on a server ever holds an
original. The threat model is the one that is *not* premature — 97% of
files carry home coordinates, and it should be written before the first byte
leaves the laptop.

Proposed D20 as the go/stop criterion. Matt's version wins.

## 2026-09-13 — The plan for outside feedback

Matt's plan, better than the one I proposed: collect friends' dog photos,
ingest them himself, stress-test the multi-pet model on real contaminated
data, then send each friend their own dog's timeline and write down what
they say. Nobody installs anything; Matt is the operator. Issues #28, #29.

Two things this changes. The multi-pet model (#22) moves from "product,
later" to the gate for the next data arriving — it has to be built and
proven byte-identical on Izzy before the first friend's folder lands.
And one-command setup (#23) drops to milestone 3, because the operator is
Matt and the friends only need to receive a file.

The contamination case is now the whole test, and it is worth stating
plainly so nobody is surprised. With no recognition (D17), a friend's
photos of Izzy from the week they dogsat her will be assigned to the
friend's own dog unless there is a caretaker edge for that week. That is
the case the model exists for, and the number to watch is **manual fixes
per hundred photos**. If it is small, multi-pet works without recognition.
If it is large, D17 gets revisited with evidence rather than guesswork.

D20's go criterion changed to match: three friends see their dog's timeline
and react; the strongest signal is one who sends more photos unasked.

## 2026-09-13 — Oakley

Matt added a folder of the merle dog, Oakley: 138 files, 2019–2026, 88 of
them in 2022. Fragments, not a life — exactly what he said most pets will
look like in most people's archives.

Two things fell out before any code. **53 of the 138 are Matt's own photos**,
so the folder is *about* Oakley rather than *from* a contributor, and that
is how people will actually hand photos over. And against the current
single-pet timeline, **27 of Izzy's 1,378 moments contain Oakley-folder
files: 18 are entirely Oakley, 9 are both dogs.** A 2% misassignment rate,
forty times the stray rate, and nothing in the data could have shown it
without a human curating a folder. Checked the two 2019 strays against the
folder: neither is Oakley, so D16 stands.

Matt's rule — guess fewer times than needed — became D21, and it overrode
my first design for #22, which had "the contributor's own pet" as a default
prior. That prior is now used for exactly one case (a single primary pet)
and nothing else is ever inferred. Ambiguity goes to an unassigned strip.
No date or species is required to ingest anything. #22 rewritten; #30
(quick reassign) and #31 (playdate suggestions, never assignments) filed.

The number that matters next is manual fixes per hundred photos once
Oakley is ingested with `--about`. Baseline expectation: Izzy loses exactly
18 moments, 9 become both, Oakley gets no eras.

Housekeeping: Renee's 12 GB zip is still in `pics/` and is fully extracted;
Oakley's zip is not yet extracted.
