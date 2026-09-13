# Decision log

One entry per product or technical decision. Newest at the bottom. A decision
is **locked** (don't relitigate without new evidence), **proposed** (leaning
this way, not yet tested), or **superseded** (link to the replacement).
Reasoning lives here so the vision doc can stay a description of the product
rather than an argument for it.

Format: `D<n> — <title>` / status / date / decision / why / what would change it.

---

## D1 — Indie / side product, not venture-scale

**Status:** locked · **Date:** 2026-09-13

**Decision:** Build this as an indie product. Success is a small, profitable
tool with a loyal user base, not a category winner.

**Why:** Reframes every competitive concern. Churn at pet death, thin
willingness-to-pay, and Apple/Google platform overlap are fatal at venture
scale and survivable at indie scale. Also forces COGS discipline
(on-device processing, selective upload) from day one.

**What would change it:** Nothing planned. Revisit only if the
multi-contributor loop shows a k-factor well above 1 on real data.

---

## D2 — Everyday delight as the emotional anchor, not memorial

**Status:** locked · **Date:** 2026-09-13

**Decision:** Position and design around daily resurfacing and milestones.
End-of-life artifacts are a natural consequence of a complete archive, never
the pitch.

**Why:** Clinical/tracking-forward apps in the category underperform
memory-forward ones. Memorial-first monetization reads as predatory and is a
one-bad-headline brand risk.

**What would change it:** Nothing planned.

---

## D3 — Species-agnostic positioning, staged implementation

**Status:** locked · **Date:** 2026-09-13

**Decision:** The core object model is generic (name, type, birthdate or
estimate, personality tags, timeline, contributors). Species-specific fields
are optional templates layered on at profile creation. Detection support
ships for dogs and cats first.

**Why:** Broad positioning is honest and costs nothing at the schema level.
Off-the-shelf detectors cover dogs and cats well and most other species
poorly, so detection support has to be staged regardless.

**What would change it:** Nothing planned.

---

## D4 — Cut global feed and prize contests

**Status:** locked · **Date:** 2026-09-13

**Decision:** No public feed, no contests. Social is closed-group (household
and friends of the pet), outward shareable artifacts, and possibly
local/geographic later.

**Why:** A public engagement-optimized feed requires scale, a prize budget,
and a moderation function, and it degrades the private archive it would be
bolted onto. The pet-content audience already lives on TikTok and Instagram.

**What would change it:** Nothing planned.

---

## D5 — Monetization deferred, but the data model stays monetization-agnostic

**Status:** locked · **Date:** 2026-09-13

**Decision:** No pricing decisions until the core loop is validated. Access
is modeled as "people with access to this pet," never as a family plan or
clinic account. No storage caps in the schema.

**Why:** Either future path (consumer subscription, physical artifacts, B2B2C
via vets) should graft on without a rework.

**What would change it:** Validation of the core loop. Current leaning is
**physical artifacts at milestones** (first year, birthdays) rather than
subscriptions, because willingness-to-pay for journaling alone is weak across
the category and milestone artifacts avoid the memorial ethics problem in D2.

---

## D6 — The wedge is the pet as a cross-person entity, not detection

**Status:** proposed · **Date:** 2026-09-13

**Decision:** Treat auto-detection and on-this-day resurfacing as table
stakes. The differentiator is merging multiple people's camera rolls into one
pet timeline, with clear contributor ownership rules, and generating
narrative artifacts from that merged timeline.

**Why:** Apple Photos (People & Pets) and Google Photos already identify
individual pets and auto-generate pet memories, so "your pet's life, already
organized" is something many target users have for free. What neither
platform does, structurally, is organize across accounts: both are built
around one person's library. That gap survives platform risk.

**Consequence:** Multi-contributor merging requires individual pet
identification, not just animal detection, because a second contributor's
roll contains other animals. The de-risking plan must test the merge case,
not only the single-roll case.

**What would change it:** If merging a second household member's photos into
the timeline (see experiments) produces no stronger reaction than a single
roll, the product collapses to a marginally better Google Photos Memories
and should be stopped.

---

## D7 — Android first

**Status:** proposed · **Date:** 2026-09-13

**Decision:** The first client is a native Android app (Kotlin). iOS follows
only after the core loop is validated. Experiments ingest from the household's
Android phones via direct file export to the Mac.

**Why:** The founding household is on Android phones with a Mac laptop, so
Android is the only platform where the multi-contributor test (D6) can be run
on real data without borrowing devices. The Android ingest path is also
technically clean: `MediaStore` gives full camera roll access with
`READ_MEDIA_IMAGES`, and Google's **ML Kit** does on-device object detection
and image labeling (including dog and cat) for free, matching the COGS
constraint in D1. No dependence on the Google Photos Library API, which since
2025 only exposes app-created content.

**Known constraints:**
- Android 14+ offers "selected photos" partial access, analogous to iOS
  limited library. Full-access acceptance rate is an open question to
  measure, same as on iOS.
- Photos removed from the device by Google Photos "Free up space" are not in
  `MediaStore` and cannot be read by any API except the user-driven Google
  Photos Picker. Auto-ingest only sees photos that still exist locally. This
  needs measuring on the household's own phones before it's treated as a
  minor edge case.
- Any eventual cross-platform layer (Flutter, React Native, Kotlin
  Multiplatform) is a later decision; the detection and ingest code must be
  native on each platform regardless, so the shared-UI question can wait.

**What would change it:** A household member switching to iPhone, or the
"free up space" gap turning out to affect most of the library.

---

## D8 — North star is resurfacing engagement, not automated capture

**Status:** proposed · **Date:** 2026-09-13

**Decision:** Replace "Weekly Active Pets" (≥1 new moment or contributor
interaction in 7 days) with a metric that requires a human to open something:
a pet whose timeline, recap, or on-this-day was **viewed** by at least one
contributor in the trailing 7 days. Automated moment ingestion is tracked as a
supply diagnostic, not the north star.

**Why:** Once ingest is automatic, "new moment this week" fires whenever
someone photographs the pet, which measures whether background sync is
enabled rather than whether anyone values the product. The vision doc's own
thesis is that this is a consumption product; the metric should measure
consumption.

**What would change it:** Real usage data showing view events are too sparse
to be a stable weekly signal at early scale.

---

## D9 — A moment is a burst of media, not a file

**Status:** locked · **Date:** 2026-09-13

**Decision:** The narrative unit of the product is a **moment**: media
clustered by a ~20-minute gap, with one hero frame selected inside it.
Individual files are storage, never the thing shown.

**Why:** Measured on a real 1,274-file archive, 1,144 photos of one dog are
549 moments — 2.1× compression. People burst-shoot, so a file-per-row
timeline shows the same pose eight times and reads as a file browser.
Hero selection by `score × √(box area)`, with thumbnails cropped to the
detection box, is what makes the output look curated rather than dumped.

**What would change it:** Nothing planned. The gap constant may need tuning
per species or user.

---

## D10 — Eras are life years anchored on the first photo

**Status:** locked · **Date:** 2026-09-13

**Decision:** Chapter the timeline into life years counted from the pet's
first photo, not calendar years and not gaps in activity.

**Why:** Gap-based segmentation (>45 days silent) produced exactly one era
across five years, because a well-photographed pet has no long silences —
the longest gap in the test archive was 36 days. Life-year anchoring needs
no threshold, produced six clean chapters, and derived the gotcha day and
every anniversary with zero user input.

**What would change it:** An archive that starts long after the pet was
acquired, where first-photo is a poor proxy for the anniversary the owner
actually observes. Worth allowing a manual override of the anchor date.

---

## D11 — Undated media is quarantined, never guessed

**Status:** locked · **Date:** 2026-09-13

**Decision:** Every media row records `time_source` (`exif` / `filename` /
`mtime`). Anything resolved only by file mtime is held out of the timeline
spine and surfaced in its own bucket for the user to place.

**Why:** 32 files in the test archive (Snapchat saves) had no EXIF and no
date in the filename. Falling back to mtime dated them all to the day the
archive was unpacked, which corrupted "most recent photo" and "longest
burst" until they were quarantined. Any product ingesting from messaging
apps hits this constantly, and a wrong date in a memory product is worse
than a missing one.

**What would change it:** Nothing planned. Content-based placement (asking
the user, or matching against dated neighbours) could later promote these
out of quarantine.

---

## D12 — Contributor is account identity; device is metadata

**Status:** locked · **Date:** 2026-09-13 · **Refines:** D6

**Decision:** Never infer contributors from EXIF camera model. Contributor
is account identity; device is stored as metadata on media.

**Why:** The test archive contains three camera models (Pixel 5 → 8 → 10 Pro)
and is one person upgrading phones, with zero date overlap between devices.
Device succession and genuine multi-contributor are indistinguishable
without checking temporal overlap. Clean succession is, separately, a useful
heuristic for stitching one person's history across upgrades.

**Consequence:** The Izzy archive cannot test D6. Multi-contributor merging
still needs a second household member's roll.

**What would change it:** Nothing planned.

---

## D13 — Moment identity must be stable across re-ingest

**Status:** locked (constraint), mechanism open · **Date:** 2026-09-13
**See:** [ideas.md I1](ideas.md) for the options and the wider backfill problem

**Decision:** A moment's identifier must not depend on its position in the
archive. The current positional scheme (`m0000`, `m0001`, … assigned by sort
order at build time) is disqualified. Which scheme replaces it —
content-addressed, persisted UUID, or time-based with merge/split lineage —
is deliberately left open until ingest is built for real.

**Why:** Measured, not theorized. Adding 708 photos that predated the
archive renumbered **100% of 587 existing moments**. Every stale pointer then
resolved to a different but entirely plausible photo: the "first photo"
milestone silently pointed at an unrelated Tuesday. Silent wrong answers are
the worst failure mode available to a memory product — there is no error to
catch, and the user has no reason to doubt what they are shown. Favorites,
share links, print orders, notification deep links and comment anchors would
all drift identically.

**How to apply:** Treat any ID derived from ordering, indexing, or array
position as a bug in this codebase, including in throwaway experiment
scripts, because experiment output is what product decisions get read off.

**What would change it:** Nothing. The constraint is proven; only the
mechanism is open.

---

## D14 — The past is never settled

**Status:** locked (principle) · **Date:** 2026-09-13
**See:** [ideas.md I1](ideas.md)

**Decision:** Ingest is incremental and late-arriving media routinely lands
*before* everything already known. No derived fact may assume the earliest
photo is final.

**Why:** Backfill is the normal onboarding path, not an edge case: cloud-only
photos imported later, a second contributor whose roll reaches back further
than the owner's, rescues and rehomings, old phones, scanned prints. In the
test archive a single second import moved the anchor date 103 days earlier
and changed 9 of 10 milestones. Anything anchored on "first photo" — the
gotcha day, every anniversary, every chapter boundary in D10 — is provisional
and may stay provisional for years.

**How to apply:** Derived superlatives and anchors are recomputed, versioned,
and never re-notified as if new. Anniversaries in particular should be
human-ratified rather than silently celebrated off a derived date. Design
import as a visible event with a digest, not a silent recompute — a backfill
reaching into the past is *new old memories*, the most emotionally valuable
thing this product can deliver, and hiding it wastes that.

**What would change it:** Nothing planned.

---

## D15 — Derived anchors must be robust to outliers, never extrema

**Status:** locked · **Date:** 2026-09-13
**See:** [log.md](log.md) 2026-09-13, [I1](ideas.md)

**Decision:** No user-visible fact may be computed as a raw minimum or
maximum over the archive. The timeline anchor is the first date photography
*sustains* (≥5 moments within 30 days), not the earliest photo.

**Why:** Measured. Two misdetected photos out of 3,924 — someone else's
chihuahua in 2018 and beagle in 2019, sitting in a second contributor's roll
— moved the anchor back two and a half years, invented two single-moment
chapters, shifted every chapter boundary by seven months and relabelled the
pet's actual first year as "Year 3". An extremum gives a single outlier
unbounded leverage over the entire narrative spine, and detection will never
be clean enough to rely on one.

**How to apply:** Anything anchored, dated or superlative needs an outlier
story before it is shown. Extend to the other derived maxima (longest burst,
busiest day, longest gap), which are currently still raw extrema and carry
the same fragility at smaller blast radius.

**What would change it:** Nothing. The thresholds may need tuning per
archive; the principle does not.

---

## D16 — Media that predates the anchor is quarantined, not deleted

**Status:** locked · **Date:** 2026-09-13 · **Extends:** D11

**Decision:** Moments before the anchor are flagged, held out of the
timeline, and reported with filename and contributor — the same treatment
undated media gets (D11). Never silently dropped.

**Why:** They are usually another animal, but not always. For a rescue or a
rehoming, photos predating the owner's first are exactly the origin story the
product most wants, and they arrive through the same door. The system cannot
tell these apart without individual pet ID, so it must surface the ambiguity
to the person who can.

**What would change it:** Individual pet ID landing, which would let most of
these be resolved automatically — though a human confirmation step is still
the right default for anything that moves the anchor.

---

## D17 — No pet recognition; the detector answers "an animal", not "which animal"

**Status:** locked · **Date:** 2026-09-13 · **Refines:** D6

**Decision:** Do not build individual pet identification. Detection stays at
"is there an animal in this frame". Species is a **profile field the user
sets**, not a detector output. Contamination is handled by cheap temporal
heuristics (D16) and, eventually, user correction — not by a model.

**Why:** Three reasons, in order of weight.

1. **The investment is disproportionate.** Contamination in the real
   two-contributor archive is two files out of 3,924 — 0.05%. Embedding and
   clustering 3,924 crops to catch two photos is not a good trade for an
   indie product (D1), and the platforms are already doing this work: Apple's
   People & Pets and Google Photos both identify individual animals. Let them,
   and let users correct what they care about.
2. **The cheap heuristic provably does not work.** Species mismatch looked
   like free signal — the archive is a dog, so a "sheep" detection should be
   suspicious. In practice 294 files are labelled sheep, horse, cat, cow, bird
   or bear, and inspection shows **every one is a dog**, including a sheep at
   0.94 confidence. Flagging on species would produce 294 false positives and
   zero true positives. Detector confidence is no help either: it is
   confidently wrong.
3. **What does work is temporal, and already built.** Both genuine stray dogs
   were caught by the pre-anchor quarantine (D16) without any visual
   reasoning at all.

**Consequence:** `pet.species` now comes from `pet.json`, not from a majority
vote over detector labels. Per-file detector labels are kept as evidence but
are not treated as truth anywhere.

**What would change it:** A household with two pets that genuinely need
separating, or contamination rising far enough that temporal heuristics stop
coping. Neither is true today.

---

## D18 — The primary surface is a feed, not the timeline

**Status:** locked · **Date:** 2026-09-13 · **See:** issue #16

**Decision:** The thing a person opens daily is a **feed**: the fewest, most
meaningful moments for right now, or bite-sized scrolling by timeframe. The
full timeline stays as the archive view — everything, in order — but it is
not the front door.

**Why:** The vision's own thesis (§2) is that this is a consumption product
and retention lives on resurfacing. Matt, after the timeline landed: it
needs "a Feed feature which surfaces the fewest most meaningful pictures at a
given time … in a more bite sized and limited attention way." The contact
sheet is the opposite of that — it is everything at once, and it rewards
sitting down with it over breakfast, not opening it on a Tuesday. The ranking
signals already exist and cost the user nothing: burst length, co-attendance,
a person in frame, on-this-day, milestone proximity, and recently-ingested-
but-old.

**How to apply:** "Fewest" is the discipline. One to three moments per open.
Anything that turns the feed into an infinite scroll has recreated the thing
D4 cut.

**What would change it:** Two weeks of the feed not being opened (#16).

---

## D19 — Multiple pets, multiple people, cross-household contribution are in scope

**Status:** locked · **Date:** 2026-09-13 · **Refines:** D3, D5, D6, D17 · **See:** issue #22

**Decision:** The model supports several pets per household, several
households per pet, and people whose relationship to a pet is owner,
caretaker, friend or viewer. Assignment of *which pet is in this moment* is
done by the person or by the platform's labels — never by a model of ours.

**Why:** A friend's dog appears throughout the archive, through visits and
dogsitting, and the current model silently assumes every animal is Izzy.
Matt: "I'd assume people can have multiple pets." The generalisation is also
the strongest version of the wedge — a friend's photos of your dog from the
week they had her flow into her timeline, which no shared album can do.

**How to apply:** `moment.pet` becomes `moment.appearances[]` with
`assigned_by`. The single-pet path must stay exactly as fast and as
automatic as today; the cost of assignment is paid only where a second
animal actually exists. The household is a grouping, not a permission
boundary — `access` edges are.

**What would change it:** Nothing planned. This is the shape D5 was
protecting room for.

---

## D20 — What "done with the proof of concept" means

**Status:** proposed · **Date:** 2026-09-13 · **See:** issue #21, milestones 1–3

**Decision (proposed):** Work runs in three milestones, and the third does
not start until the first two say go.

**Milestone 1, Learn** — answer the three questions the vision hangs on, all
cheap and local: will they keep opening a feed after two weeks (#16); would
either of them send a generated recap to someone outside the house (#15);
will strangers grant full photo access (#17).

**Milestone 2, Household #2** — get other people's pets and other people's
reactions in, without anyone installing anything. Matt collects friends'
dog photos and ingests them himself (#28), which stress-tests the multi-pet
model (#22) on real contaminated data; each friend then gets their own
dog's timeline and their reaction goes in the log (#29). A threat model
comes first, before any output leaves the laptop (#24). Takeout import (#18)
is the realistic way friends hand over photos. This is what breaks n=1.

**Milestone 3, Product** — identity (#25), where data lives (#26),
deployment (#27), the multi-pet model (#22), ownership (#20). Every one is
gated on the first two.

**Go** means all three of: the feed is still being opened at two weeks; at
least one recap was actually sent; at least three friends have seen their
own dog's timeline and reacted the way Matt and Renee did — with the
strongest signal being a friend who sends more photos unasked. **Stay personal** is the outcome if any fail — a tool
two people keep using is a success by the vision's own definition of indie
(D1). Either way, the answer gets written here.

**Why:** Nineteen commits and a working timeline in a day is exactly the
pace at which a demo drifts into a build without anyone deciding to. The
infrastructure questions — auth, database, deployment — are real and are
now written up, and every one of them is premature until someone outside the
house has used the thing.

**What would change it:** Matt's version of the criterion. This is his call;
the proposal is a starting point.

---

## D21 — Guess fewer times than needed: unassigned beats wrong

**Status:** locked · **Date:** 2026-09-13 · **Refines:** D11, D16, D17, D19 · **See:** issues #22, #30, #31

**Decision:** Automatic assignment of a moment to a pet happens in exactly
one case — a contributor's single primary pet, the one they have `owner`
access to and nothing else. No secondary pet is ever inferred. Every other
assignment comes from a person: a subject folder (`--about`), a manual
choice (#30), or a dated `caretaker` window. Ambiguity resolves to
**unassigned**, which is a first-class, visible state. A pet needs only a
name; no date or species is ever required to ingest.

**Why:** Matt, verbatim: "most people don't want to remember certain things
off the top of their heads or look up dates and times … educated guesses
could be made but better to guess fewer times than needed." And the data
agreed the same afternoon: a curated folder of a friend's dog showed that
27 of Izzy's moments were that dog, 18 entirely, with no signal anywhere
that they were wrong. A wrong assignment in a memory product is silent; an
unassigned one is a strip someone can clear in a minute.

**How to apply:** If you find yourself writing a heuristic that assigns a
second pet, stop and make it a *suggestion* in the unassigned strip instead
(#31). If you find yourself adding a required field to onboarding, stop.

**What would change it:** Manual-fix counts from #28 being so high that
multi-pet is unusable — which would argue for recognition (revisiting D17),
not for more inference.

---

## D22 — The input is the platform's pet album, not the raw camera roll

**Status:** locked · **Date:** 2026-09-13 · **Refines:** D7, D17, D21 · **See:** issues #32, #18

**Confirmed by Matt:** every folder so far — Izzy (both), Oakley, Ray — was
a Google Photos album, exported and downloaded. The friends' own phones
hold more photos of their dogs than reached the albums.

**Decision (proposed):** What a person hands the product is the pet album
their phone already made — Google Photos' or Apple's own pet grouping — not
their entire camera roll. The platform does the first cut, which is the
recognition we decided not to build (D17). We do what the platform does not:
merge across people, and tell the story.

**Why:** Every input so far was already an album. 51 of Ray's 84 photos and
125 of Oakley's 138 were taken on Matt's and Renee's phones, yet only 8 and
53 appear in the "Izzy" exports — the platform had already sorted by
subject. So the numbers the project rests on (90% detection, 0.05%
contamination, single-pet inference being right almost always) describe
album input, and the vision's "connect the camera roll" thesis is untested
on a roll. On a raw roll, D21's one automatic inference is the assumption
most likely to break.

**What this changes:** The ask at onboarding becomes "share your pet's
album" rather than "give us full library access" — a smaller, more
comprehensible permission, and one the platforms already expose as an
export or a shared album. It weakens the vision's §7 platform-risk worry in
one direction (we are downstream of the platform, not competing with its
recognition) and sharpens it in another (we depend on that grouping
existing and being exportable). The cross-person merge, the narrative, the
feed and the artifacts are unaffected: none of them needed a raw roll.

**What the confirmation adds:** the platform did the *gathering* too, not
only the recognition. Ray's album holds photos from the owner's Samsung,
Motorola and Nexus alongside Matt's Pixels — Google Photos albums already
accept contributions from several people, and that is how a friend's old
phone ended up in Matt's export. So the multi-contributor mechanism the
vision imagined (auto-pull from everyone's camera roll) already exists in a
cruder form that people use today: a shared album. The product's ingest is
**"export your pet's album"**, via Takeout (#18) so the sidecars come with
it. What the album cannot do — merge two people's *separate* albums of the
same pet, chapter it, resurface it, make it postable — is exactly what is
left for us, and it is the part that landed.

**What would change it:** #32 showing the album is a poor input after all —
too curated, too lossy, or unexportable at fidelity. Until then, "connect
the camera roll" in the vision (§2) should be read as "connect the album".

---

## D23 — An album is a subject *hint*, not ground truth

**Status:** locked · **Date:** 2026-09-13 · **Corrects:** D22 · **Refines:** D21 · **See:** issue #33

**Decision:** A photo's presence in a pet's exported album is **strong
evidence** that the pet is in it, not proof, and not proof that *only* that
pet is in it. `--about` must record `assigned_by: "album"`, a tier below
`user`, and album assignments are reviewable rather than final.

**Why:** Measured, twice, and the second time was worse. Forty detections
sampled from Oakley's album and tagged by hand: **20 Izzy, 20 Oakley**.
Then a full review pass over Ray's album found where its photos actually
belong:

| | photos |
|---|---|
| Shadow — a **third friend's dog** nobody had declared | 33 |
| Ray | 31 |
| Izzy **and** Ray together | 18 |
| Oakley | 3 |
| Izzy alone / unplaceable | 2 |

**An album named for one dog contained four.** Barely a third of it is the
dog on the label, alone.

The cause is obvious in hindsight and general: people build a pet's album
from the occasions that pet was around, and on those occasions **both dogs
are in the frame**. An album about a visiting dog is really an album about
the visits. Google's pet grouping has the same property — it groups photos
*containing* an animal, not photos *only* of it.

**What this corrects in D22:** the platform did the gathering and a first
cut at recognition, but its output is not a clean single-pet classification.
"The album is the assignment" was too strong. The album is the best cheap
prior available, and it still needs a human pass.

**What it invalidates:** the "zero manual fixes, zero unassigned" result
from #22 and #28. That was not inference succeeding; it was a noisy
assignment source being taken at face value. The real correction cost for
multi-pet is **not yet known**, and #33 measures it.

**How to apply:** Never treat an album as final. Multi-pet households need
the correction pass (#30) as a normal step, not an exception. Where two
known pets plausibly co-occur, prefer recording **both** appearances over
picking one.

**Why it happens, generalised.** An album you make of *someone else's* pet
is really "photos from the times that animal was around" — and on those
occasions your dog, their dog, and a third friend's dog were all there. The
label names the occasion, not the subject. Expect this to be worse for
friends' pets than for your own.

**What would change it:** A source that really is single-pet ground truth —
a user tapping "this is Oakley" per photo. That is #30, and it stays the
only `user` tier.

---

## D24 — The product curates a mostly-right pile; it does not find pets in chaos

**Status:** locked · **Date:** 2026-09-13 · **Supersedes the ambition in:** D22 · **Refines:** D6, D17, D19, D21, D23 · **See:** issues #32, #33

**Decision:** The input is **a pet album** — an export the user hands over,
already about one pet. Camera-roll ingestion is out of scope. The product's
job is to take a pile of photos that is already high-signal for one pet and
make it a good, browsable, shareable set: merging several people's albums of
the same animal, giving it structure, resurfacing it, and **making the
cleanup cheap**. It is not a general pet-detection system and will not try
to become one.

**Why:** Matt, deciding the direction: expect "piles of pet pictures, with
high signal that it is a specific pet, but with many examples where it is a
different pet or multiple pets that could assign to multiple areas … I don't
think we want to get super good at generalized pet detection. More on
helping people manage good sets of photos that need some cleanup."

The measurements support it. An album is 90%+ animal photos and roughly
two-thirds the intended pet (D23) — high signal, imperfect. A raw camera
roll is a different and much harder problem that nobody asked us to solve,
and the platforms are already better at the recognition half of it (D17).

**What this reframes.** The 32% of Oakley's album that is actually Izzy is
**not an error to eliminate** — those photos genuinely contain Izzy, usually
both dogs at once, because the two were together. The product's job is to
let a photo belong to both timelines and to make the remainder a minute of
clicking. **Multi-pet is the normal case, not the exception**, which is a
correction to how D19 and D21 were being applied.

**What it dissolves.** The vision's §7 names camera-roll permission friction
as a top risk, and it was the largest unvalidated one in the project. An
album export needs **no runtime permission at all** — it is a file. The "free
up space" gap (D7) stops mattering for the same reason. Two of the three
biggest named risks are gone, not mitigated.

**What it opens, unresolved.** D7 chose Android-first because `MediaStore`
plus ML Kit was the ingest path. If ingest is a file the user exports,
that reasoning weakens and the client could be anything, including a web
app. Not decided here; flagged.

**How to apply:** Anything that improves detection on unconstrained photos
is out of scope. Anything that makes a roughly-right set easier to correct,
merge, structure or share is the product. When a photo plausibly contains
two known pets, record both rather than choosing.

**What would change it:** Users arriving without albums — no pet grouping on
their platform, or unwilling to export. Then onboarding needs a different
front door, not a different engine.

---

## D25 — Flag uncertainty, batch the answer; do not detect outliers

**Status:** locked · **Date:** 2026-09-13 · **Refines:** D17, D21, D24 · **See:** issue #33

**Decision:** The product does not try to detect "wrong pet" photos. It
flags **provenance uncertainty** — a moment vouched for by nothing but an
album — says why, and groups the flagged moments into **islands** of
contiguous activity so a person can answer a whole run in one click.

**Why:** A fourth dog (Shadow, a different friend's) was found sitting in
Ray's album. Two things were measured in response.

The existing provenance flag **already caught it** before anyone looked:
album-only assignment, unknown contributor. The review queue is 4% of
assigned moments, so it is well targeted rather than noisy.

A temporal-outlier heuristic would have been actively harmful. Ray's
archive has three islands separated by year-plus gaps: 2012–13 on a Samsung,
2015–17 on a Motorola and Nexus, 2022–26 on Pixels. The first is the wrong
dog; the other two are his owner's old phones and genuinely him. A gap or
device-novelty rule cannot separate them, and would flag a friend's real
early history as suspect. **Isolation is not evidence of error** — it is
evidence of a forgotten era, which is often the most valuable material
(compare the prologue in D14's wake).

**How to apply:** Islands are a *review aid*, never an assignment signal.
Show the reason a moment is flagged. Prefer one question over twenty: a run
of photos from one fortnight on one old phone is usually one answer.

**What would change it:** Nothing available without recognition, which D17
declines and D24 puts out of scope.

---

## D26 — Cleanup is a consumption surface, not a tax

**Status:** locked · **Date:** 2026-09-13 · **Qualifies:** the effort/payoff argument in vision §2 · **See:** issues #16, #35

**Decision:** The correction loop is treated as **a reason to open the app**,
not as friction to be minimised toward zero. Design questions whose answer
is *looking at a photo you would enjoy looking at anyway*. Effort spent that
way is retention, not cost.

**Why:** Matt, after answering 28 queue items in one sitting: *"it felt like
sorting photos, not a chore. Pretty fun actually."*

The vision's §2 treats user effort as the thing that kills journaling
products — cost paid at capture, value realised years later — and the whole
capture-inversion thesis follows from minimising it. That argument is right
about *capture* and wrong as a general law. Sorting photos of your own dog
is not capture; it is **retrieval with a decision attached**, and the photo
is the payoff, delivered in the same instant as the work.

The distinguishing property is worth stating precisely, because it is what
makes this generalisable and not just a nice anecdote: **the question puts
something you want to see in front of you, and answering it takes one
glance.** Tagging from a filename is a chore. Choosing between two dogs you
love while looking at them is a scroll through an album with a purpose.

**How to apply.** Prefer question-shaped surfaces wherever a fact is
genuinely uncertain: which pet, which of these is the better hero for this
chapter, is this the right gotcha day, where is this place. Batch them, make
every answer one click, and never ask anything that does not show a photo.
Never manufacture questions to create engagement — the honesty of the
uncertainty is what keeps this from being a dark pattern.

**Caveat, recorded deliberately:** this is one session, one person, and that
person built the thing. It should be checked against a friend who has no
investment in it (#29) before it carries much weight. It is promising, not
proven.

**What would change it:** A friend finding the same loop tedious, or the
queue staying enjoyable only while it is novel.

---

## D27 — A review queue must accept "yes" as easily as "no"

**Status:** locked · **Date:** 2026-09-13 · **Refines:** D21, D26 · **See:** issue #33

**Decision:** Every review surface offers an explicit affirmative — *Yes,
correct* — alongside the corrections, individually and in batch. Confirming
promotes the existing guess to `assigned_by: user` and clears the item.

**Why:** Matt, working the queue: *"is there a way to confirm that a dog is
the correct one when reviewing? I was clicking on and off."*

Toggling a pet off and on did produce a confirmation, but only by accident
of the data model, and the intermediate state looked like deletion. The
deeper problem is a bias: **if the only way to clear an item is to change
it, people change things that were right.** A queue that can only shrink
through correction manufactures corrections, and every one of those is a
silent wrong answer of exactly the kind D13 and D23 exist to prevent.

Confirmation is also *information*. "The album was right here" is as useful
a signal as "the album was wrong", and without it the measured error rate is
biased upward — the 1-in-28 agreement rate from the first pass was measured
on a queue where agreeing was awkward.

**How to apply:** Anywhere a person is asked to check a derived fact, the
affirmative must be a first-class control with its own key, not the absence
of action. Silence is not consent and must never clear a queue item.

**What would change it:** Nothing planned.
