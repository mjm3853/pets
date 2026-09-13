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

## 2026-09-13 — Ray, and the albums we mistook for rolls

Second friend's dog: Ray, 88 files, six camera models, 2012–2026. Matt
warned there would be Izzy in it.

The device survey answered a question nobody had asked. **51 of Ray's 84
photos and 125 of Oakley's 138 were taken on Matt's and Renee's own
Pixels** — yet only 8 and 53 of those appear in the Izzy exports. Photos of
other dogs, from the same phones, were never in the Izzy folders. Add ~400
files a year at a 90% dog rate, which no camera roll produces, and both
"rolls" were albums: Google Photos had already sorted by subject before we
saw anything.

That reframes the day. 90% detection, 0.05% contamination, single-pet
inference being right almost always — all measured on platform-curated
input. The vision's capture-inversion thesis is untested on a raw roll, and
D21's one automatic inference is exactly what a raw roll would break.
Filed #32 to measure it, and proposed D22: the input is the platform's pet
album, and the platform did the recognition we chose not to build. That is
a cleaner product story than the vision's, not a worse one — but it should
be a decision, not an accident.

Three smaller corrections from Ray, folded into #22. Friends' pets are
always the sparse view: Ray has a real 2015–2017 period on the owner's old
Motorola and Nexus, then a five-year hole, and year-chapters would emit six
empty ones. Eras only for a contributor's own primary pet. Device is a hint
and never a contributor — Matt and Renee may both own a Pixel 8. And
friends' folders are worse on metadata: 15% of Ray's files are undated
against 3.7% of Izzy's, and there is a `.gif` the scripts silently drop.

Ray's owner's own photos — the Samsung from 2012, the Motorola, the Nexus —
are 33 files Matt never had, and the 51 from Matt's phones are ones the
owner has never seen. Cross-household contribution, both directions,
already sitting in one folder.

Expected when Ray is ingested with `--about`: Izzy loses exactly 6
moments, all pure. Both zips are extracted; nothing ingested yet.

## 2026-09-13 — Confirmed: albums, all of them

Matt: every folder was a Google Photos album, exported and downloaded — the
two Izzy ones, Oakley, Ray. The friends' own phones hold more than reached
the albums. D22 moves from proposed to locked.

The confirmation adds something the device survey only hinted at. Ray's
album holds the owner's Samsung, Motorola and Nexus photos next to Matt's
Pixels, which means the album already accepted photos from more than one
person. Google Photos did the *gathering* as well as the recognition. The
vision imagined auto-pulling from everyone's camera roll; the cruder version
of that — a shared album people add to — already exists and people already
use it. So the ingest is "export your pet's album" via Takeout, and the
sidecars come with it.

What is left for us is the part the album cannot do: merge two people's
separate albums of the same pet (Matt's and Renee's were separate exports),
chapter it, resurface it, make it postable. That is the part that landed
over breakfast. Cleaner story than the vision's, and now a decision.

#32 stays at p1 but now measures dependence on the album rather than
choosing an input. #18 promoted to the ingest path.

## 2026-09-13 — Multi-pet, built

Built #22, #7, #30, #24 in one pass. Oakley and Ray are in.

**#22 worked, and the Izzy invariant held exactly** — same 1,487 moment
ids, same eras, same milestones when she is alone. With both albums added:
Izzy 1,353, Oakley 60, Ray 49, 24 moments holding two pets, **0
unassigned**.

Zero manual fixes is the number #28 wanted, and it is worth being suspicious
of. It is zero *because the albums are the assignment* — Google Photos
sorted by subject (D22), so Oakley's album contains Oakley. The
caretaker-window machinery was never exercised, and the contamination case I
predicted (a friend's photos of Izzy from a dogsitting week) never arose.
That case is still real; it just needs a raw roll, which is #32.

**My prediction was wrong and the reason is the interesting part.** I said
Izzy would lose exactly 18 to Oakley and 6 to Ray. She lost 25, and 24
moments went multi-pet rather than 9. The albums brought 164 files that were
in no roll; those landed inside existing bursts and re-clustered them. 26
moment ids changed and all 26 were absorbed into larger bursts — D13 working
as designed, D14 again. The prediction was computed on the old clustering
and could not have been right.

That is exactly what #7 now prints, in four lines, automatically.

**Sparse pets forced a copy rewrite.** Oakley's page opened with "Nothing
here was tagged, titled, sorted or chosen by a person", which for an
exported album is simply false — a person chose every file in it. It now
opens "Someone else's dog, in our photos" and the coda says plainly that a
person put these here and that no anchor is guessed because no owner is
present to confirm one. Worth remembering: the honest framing for a
fragment pet is the opposite of the framing for your own.

**#24 found nothing alarming, which is itself the finding.** Pages carry
thumbnails, device models and first names; no paths, no coordinates,
no originals. `moments.json` carries GPS on 2,944 rows and absolute paths on
all 4,547 — so the rule is that the page is the only thing that ever leaves.
Thumbnails being re-encoded crops strips EXIF as a side effect. `leakcheck.sh`
is the pre-send gate and passes on all three pages.

## 2026-09-13 — #29 prepared, awaiting reactions

Three pages are built, leak-checked and ready to send. Deliberately **not**
hosted — hand-delivered files, per security.md rule 5.

| file | size | |
|---|---|---|
| `oakley-portable.html` | 1.5 MB | 60 moments, 2019–2026, 22 shared with Izzy |
| `ray-portable.html` | 0.8 MB | 49 moments, 2012–2026, 2 shared with Izzy |
| `izzy-portable.html` | 22.4 MB | 1,353 moments, 7 chapters |

`leakcheck.sh` passes on all three: no absolute paths, no coordinates, no
originals.

### What to capture when each friend reacts

Write it here, verbatim where possible, one section per person. The wording
matters more than the summary — "huh, I forgot about that day" and "this is
nice" are different signals.

- **First reaction, unprompted.** Before any explanation. Do not describe the
  product first; send the file and wait.
- **What they opened first**, and whether they found the burst expansion on
  their own.
- **Anything wrong**: a dog that is not theirs, a date that is off, a photo
  they would not want in there.
- **Anything missing** they expected to see.
- **Did they ask for a copy of a photo** (#13) or to send it to someone (#15)?
- **Did they offer more photos without being asked?** That is the strongest
  positive signal available, and the one that would move D20.

### What is deliberately not being asked

No questions about features, pricing, or whether they would use an app.
Those answers are worthless this early. The only thing being measured is
whether the artifact produces a reaction.

### Known things they may notice

- Ray's page starts in **2012** — his owner's old Samsung. Fourteen years.
- Oakley's and Ray's pages have **no chapters and no anniversaries**, on
  purpose (D21). If a friend asks for them, that is a signal worth logging:
  it would mean the sparse view reads as incomplete rather than honest.
- Both pages say plainly that a person chose these photos. If that reads as
  a cop-out rather than as honesty, log that too.
- Matt's and Renee's photos are in their dogs' pages — 51 of Ray's files and
  125 of Oakley's came off Pixels in this household. The friends have not
  seen most of those.

## 2026-09-13 — The album is not ground truth

Ran `rawroll.py` as a demo against Oakley's album (no phone was connected
for the real raw-roll test), Matt tagged the 40-photo sample, and it
overturned the best result of the day.

**Of 40 detections sampled from Oakley's exported album: 20 are Izzy, 20 are
Oakley.** In 13 of 40 — **32%** — the model attributes a photo solely to
Oakley where a human says Izzy. Over the album's 129 detections that is
roughly 42 misattributed photos. Ray's 77 carry the same risk, unmeasured.

Resolving the tally took a minute of care: the page asked "is this Izzy?"
while showing Oakley's album, so "pet" was ambiguous. Cross-referencing
against album membership was inconclusive (40% vs 25%), so I built a contact
sheet of both groups and looked. Bottom row uniformly the dark merle dog,
top row the cream one. Unambiguous once seen, and another entry in the
column marked *look at the photos*.

**What it means.** D22 said the album is the assignment. Too strong, and now
corrected as D23: an album is a **subject hint**. People build a pet's album
from the occasions that pet was around, and on those occasions both dogs are
in the frame. An album about a visiting dog is really an album about the
visits. Google's own pet grouping has the same property — it groups photos
*containing* an animal, not photos *only* of it.

**It also invalidates the day's best number.** #22 and #28 reported "zero
manual fixes, zero unassigned" and I flagged that as suspicious at the time
because the albums were doing the work. It was worse than suspicious: the
assignment source was 32% wrong and was being taken at face value. The real
correction cost for multi-pet is still unknown. #33 measures it.

Worth naming the pattern, because it has now happened three times. The
strongest-looking result of a session — 90% detection, zero contamination,
zero manual fixes — has each time been an artifact of input that something
upstream had already cleaned. The fix each time was to look at the actual
photos rather than the summary statistic.

The 40 tags are saved as `experiments/timeline/fixtures/oakley-40-tagged.json`
so #33 can be scored against them rather than re-tagged.

## 2026-09-13 — Repositioned: curate a mostly-right pile

Matt set the direction after the tally: stop worrying about camera rolls and
full phone pulls. Assume the input is a **pet album**. Expect piles of pet
pictures with high signal for one pet, and many photos that are a different
pet or several at once. Explicitly *not* trying to get good at generalised
pet detection — "more on helping people manage good sets of photos that need
some cleanup."

Recorded as D24, and it is the clearest statement of what the product is
that the project has had. The engine was never the interesting part; the
platforms do recognition better and nobody asked us to compete there. What
is left is merging several people's albums of one animal, giving the result
structure, resurfacing it, and making the cleanup cheap.

**It reframes D23's 32% from a defect into the job.** Those Izzy photos in
Oakley's album are not mistakes — the two dogs were together. A photo should
belong to both timelines. Multi-pet is the normal case, which corrects how
D19 and D21 were being applied.

**It also dissolves two of the three biggest named risks**, rather than
mitigating them. The vision's §7 puts camera-roll permission friction near
the top, and it was the largest unvalidated risk in the project: an album
export needs no runtime permission at all, because it is a file someone
hands you. The "free up space" gap (D7) stops applying for the same reason.
Closed #17 and #32 on that basis.

One thing it opens: D7 chose Android-first because `MediaStore` plus ML Kit
was the ingest path. If ingest is a file, the client could be anything,
including a web app. Flagged in D24, not decided.

`rawroll.py` survives its own issue being closed — it is the **review tool**
now, and it is what #33 will use to score the cleanup loop.

## 2026-09-13 — The cleanup loop, scored

Built #33 and #34 together, since the review queue needed somewhere to live.

**#33 scored against Matt's 40 tags.** Izzy photos found 7/20 → 12/20,
misattributions 13 → 8, and **all 8 remaining are flagged for review**. The
second number is the one that matters: nothing is silently wrong any more,
which is the whole D21/D24 posture.

Two things worth keeping from the build.

**A plausible prior with zero signal.** The spec suggested using
co-occurrence, so I tested "was Izzy also photographed that day" before
writing anything. 10 of 13 for the *wrong* cases and 10 of 13 for the
*correct* ones — no discriminative power at all. It would have looked
clever, shipped, and added noise. Measuring first cost two minutes.

**The fix was removing code, not adding it.** One line —
`if row.get("assign"): continue` — was suppressing a contributor's own-pet
inference for album files. That single suppression was what hid Izzy inside
Oakley's album. Demoting the album tier and deleting that line did most of
the work.

The remaining 8 are album files with no roll overlap and an unknown
contributor. Nothing short of looking at them says Izzy is there, which is
D17 territory and exactly what the queue is for.

**#34, one navigable app.** index.html with pet cards, a **Together**
section (47 moments — Izzy+Oakley 39, Izzy+Ray 8) and the review queue. The
Together section is the bit Matt asked for and it is the most product-like
thing built so far: it shows a friend the overlap they have never seen,
which is the cross-person wedge made visible rather than argued.

Extracted the burst panel and picker into one shared function so a moment
opens and reassigns identically from any page.

## 2026-09-13 — First real correction

Matt used the review queue and marked one moment "not sure":
`{"mo1ea26aa04bbedf": []}`.

It was Ray's **oldest** moment — 2012-08-29, two frames on a
SAMSUNG-SGH-I747, assigned to Ray by his album and nothing else. Exactly the
class the queue exists for: contributor unknown, album-only, no corroborating
signal.

Applied: Ray 49 → 48 moments, review queue 63 → 62, unassigned 0 → 1. His
`first_seen` correctly did **not** move — there is another moment three hours
later the same evening, so the date span is still honest.

Two things this confirms, both cheaply.

**The round trip works end to end with a real human answer**, not a
synthetic test: page → localStorage → tray JSON → `pet.json` → rebuild →
counts move → re-render. Nothing overrode the user's answer on rebuild,
which is the D21 contract.

**"Not sure" is load-bearing.** Marking a 2012 photo unassigned is the
correct outcome for a photo nobody can vouch for, and it is better than
either alternative — silently keeping it on Ray, or discarding it. It stays
in the archive, visible, attached to nobody, and can be answered later.

One correction is not a measurement. The number that matters — corrections
per hundred photos — still needs a real pass through the 61.

## 2026-09-13 — A fourth dog, and what not to build

The moment Matt marked "not sure" turned out to be **Shadow**, another
friend's dog, sitting inside Ray's album. So the album contained two
different friends' dogs, neither of them declared.

He asked whether outlier heuristics would help. Measured before building,
and the answer was no — twice over.

**The existing flag already caught it.** That moment was in the review queue
before he opened it: album-only assignment, unknown contributor. The queue is
4% of assigned moments, so it is targeted, not noise. Nothing new was needed
to *find* it.

**A temporal-outlier rule would have been harmful.** Ray has three islands
separated by year-plus gaps — 2012–13 on a Samsung, 2015–17 on a Motorola and
Nexus, 2022–26 on Pixels. The first is Shadow. The other two are his owner's
old phones and genuinely Ray. No gap or device-novelty rule separates them,
and shipping one would have flagged a friend's real early history as suspect.
Isolation is not evidence of error; it is evidence of a forgotten era, which
is usually the good stuff.

So D25: flag provenance, not outliers — and spend the effort on making the
answer cheap instead. The queue now groups into islands with a one-click
"all of these are ___". Ray's 2012–13 Samsung island is six moments and
**one click**; verified, it wrote six corrections from one button.

Added Shadow as a pet with nothing but a name, which the model now supports
without complaint — no species, no date, no album. A pet with no moments
appears in every picker but gets no page until something is assigned to it.

## 2026-09-13 — Shadow gets a page, and Ray's history gets fixed

Matt used the batch button and sent back six assignments. Applied:

| | before | after |
|---|---|---|
| Ray | 49 moments, from **2012-08-29** | 42 moments, from **2015-05-01** |
| Shadow | — | **6 moments, 9 files**, 2012–2013 |
| review queue | 62 | **55** |

The important number is not the queue. **Ray's timeline was wrong** — it
claimed to start in 2012 on a Samsung, three years before his actual
earliest photo, because another friend's dog was sitting in his album. It is
now right, and it cost two clicks: one "not sure", one "all of these are
Shadow".

That is the cleanup loop doing exactly what D24 says the product is for.
Nothing was detected; a person answered one question about six photos.

**Found a real gap in the process.** A moment answered "not sure" leaves
every pet, which also removed it from the review queue — unreachable
forever, the one moment a human had already looked at and could not place.
Fixed: unassigned moments now appear as their own group at the top of the
queue. The loose 2012-08-29 17:57 moment is three hours before a confirmed
Shadow one, on the same phone, so it is almost certainly Shadow too — but
Matt's answer stands until he changes it (D21), and now he can.

Assignment sources are now 6 user / 104 album / 1,381 inferred.

## 2026-09-13 — The album named for one dog contained four

Matt worked the queue properly: **28 answers in one pass**. The result is
the most important measurement the project has produced.

**Only 1 of 28 confirmed what the model said.** 11 added a second pet the
model had missed, 14 changed the pet outright, 2 were "not sure". A 1-in-28
agreement rate is a *good* result for the queue — it surfaced almost
exclusively things that were actually wrong — and a bad one for the album.

**Where Ray's album photos actually belong, after review:**

| | photos |
|---|---|
| Shadow — a third friend's dog nobody had declared | 33 |
| Ray | 31 |
| Izzy **and** Ray together | 18 |
| Oakley | 3 |
| Izzy alone / unplaceable | 2 |

An album named for one dog contained **four**, and barely a third of it is
the dog on the label. The earlier Oakley estimate (~68% right) was
optimistic; for a friend's pet it is closer to a third.

The reason generalises and is worth holding onto: **an album you make of
someone else's pet is really "photos from the times that animal was
around"** — and on those occasions your dog, their dog and a third friend's
dog were all there. The label names the occasion, not the subject.

**The cost.** 34 standing corrections covering 58 photos, against 225
album-assigned photos: **15 corrections per 100 album photos**. That bought
disentangling four dogs. Queue is down from 62 to 28; Shadow went 0 → 19
moments, Ray 49 → 29, multi-pet moments 24 → 58.

Nothing about this is a failure of the product. It is the product: D24 says
the job is curating a mostly-right pile, and this is what "mostly right"
actually looks like when the pile is about a friend's dog.

## 2026-09-13 — The cleanup was fun, which changes the argument

Asked Matt whether 28 corrections felt like a chore. *"It felt like sorting
photos, not a chore. Pretty fun actually, similar mechanisms will help this
thing become real and useful."*

That qualifies the vision's opening argument. §2 treats user effort as the
thing that kills journaling products — cost at capture, value years later —
and the whole capture-inversion thesis follows from driving effort to zero.
Right about capture. Not a general law.

Sorting photos of your own dog is **retrieval with a decision attached**.
The photo is the payoff and it arrives in the same instant as the work. The
distinguishing property, stated precisely so it generalises: *the question
puts something you want to see in front of you, and answering takes one
glance.* Tagging from a filename is a chore; choosing between two dogs you
love while looking at them is an album scroll with a purpose.

Recorded as D26, and the vision doc now carries the qualification inline
rather than quietly contradicting itself. #35 files the other places the
same shape fits: which hero for this chapter, is this the gotcha day, where
is this place, which moments belong in the recap. Each is a real uncertainty
already sitting in the data.

One rule written into D26 and #35 because it would be easy to get wrong:
**never manufacture a question to create engagement.** The honesty of the
uncertainty is what makes this pleasant rather than manipulative.

Caveat recorded in the decision itself: one session, one person, and that
person built it. #29 — a friend with no investment — is the real test.

## 2026-09-13 — First question-shaped surface: pick the covers

Built the first of #35's candidates, chosen because it has the most visible
payoff: every chapter's cover image is currently picked by `hero_quality`, a
formula that knows which frame reads well and nothing about which one you
love.

The index now has a **Pick the covers** section: current cover large, five
candidates beside it, click to swap. Six chapters, five options each, one
click per answer. Picks persist in `pet.json` under `heroes`, and
`pick_hero()` prefers them over the formula forever after — verified: one
pick changed Year One's cover and flipped `hero_chosen` to true.

Two design notes worth keeping.

**Keyed by moment id, not by era.** Era ids and boundaries move when the
anchor moves or photos arrive (D13, D14), so a pick keyed to "chapter 2"
would drift onto a different chapter. A pick is a *moment id*, and the era
that contains it uses it. Survives re-clustering and anchor changes.

**The tray now carries two kinds of answer.** `assignments` and `heroes` in
one JSON, so a session of mixed work — some reassignments, some covers —
comes back as one paste. Keeping that shape stable matters: a phone UI would
write the same thing.

The remaining #35 candidates need other work first: places (#11) for "where
is this", recap selection (#15), and the gotcha-day question has no target
because Izzy's anchor is already given and the other three are sparse.
