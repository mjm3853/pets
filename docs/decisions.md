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
