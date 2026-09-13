# Ideas and open problems

Parking lot for problems worth solving later. Nothing here is decided — that
is what [decisions.md](decisions.md) is for. Each entry states the problem,
why it matters to real users, and the options seen so far, so a future
session can pick it up without rediscovering the shape of it.

---

## I1 — Backfill: photos that arrive late and land in the past

**Surfaced:** 2026-09-13, from a real event during testing.

### What happened

A second, larger export of the same dog's photos arrived after the first had
already been ingested and rendered. It was a clean superset: 1,274 files plus
708 new ones. Every new photo fell in **April–July 2021**, three months
*before* what had been the first photo — the actual puppyhood, missing from
the first export.

Re-running ingest produced this churn:

| | before | after |
|---|---|---|
| Anchor (first photo) | 2021-07-19 | **2021-04-07** (−103 days) |
| Anniversaries | mid-July ×5 | **early April ×5** |
| Chapter boundaries | 6 | **all 6 moved** |
| Busiest day | 2022-07-28, 5 moments | **2021-04-10, 9 moments** |
| Longest burst | 22 frames | **31 frames** |
| Milestones unchanged | — | **1 of 10** (longest gap) |
| Moment IDs preserved | — | **0 of 587 (100% churn)** |

### Why this matters beyond one test archive

Backfill is not an edge case, it is the **normal onboarding path**. Every one
of these is a person arriving with history:

- Photos still in Google Photos cloud but off the device (D7's "free up
  space" gap) — imported later, all dated in the past.
- A second contributor joining months in. Their roll is *entirely* backfill,
  and reaches back before the owner's first photo whenever they knew the pet
  first.
- A rescue or rehoming, where the previous owner or foster hands over photos
  predating everything.
- An old phone found in a drawer. A partner's Takeout export. A shared album
  from a breeder.
- Scanned prints for a pet that predates smartphones entirely.

So the system must assume **the past is not settled**. Anything derived from
"earliest photo" is provisional, possibly for years.

### The three distinct problems underneath

**1. Identity churn (the severe one).** Moment IDs are currently positional
(`m0000`, `m0001`, …), assigned by sort order at build time. Inserting 708
earlier photos renumbered every single one. The dangerous part is not that
pointers broke — it is that they *didn't*: each stale milestone pointer
resolved to a different, entirely plausible photo. A "first photo" link
silently became a random Tuesday. Any saved favorite, share link, print
order, notification deep link, or comment anchor would have drifted the same
way, with no error to catch it.

Options: content-addressed IDs (hash of member file identities); a stable
UUID minted once and carried in a persisted store; time-based IDs (ULID on
`started_at`) — but bursts can merge or split when new frames land between
them, so even time-based IDs need a merge/split lineage record.

**2. Anchor drift.** Life-year chapters (D10) anchor on the first photo, and
the anchor moved 103 days, taking every anniversary with it. If the product
had already told this user "Izzy's first year ended July 17," congratulated
them on it, or sold a Year One photo book, all of that is now retroactively
wrong.

Options: ask the user to **confirm the anchor date** once it is proposed, and
treat the confirmed value as sticky (auto-derive, human-ratify); keep
deriving but never celebrate an anniversary in its first cycle; distinguish
"birthday" (a real fact the user may know) from "first photo" (an artifact of
the archive) and stop conflating them — currently the same field does both.

**3. Superlative churn.** "Most photographed day," "longest burst," "longest
quiet stretch" are all maxima over the archive, so any import can dethrone
them. A quiet stretch can *shrink* when photos land inside it, meaning a fact
already shown to the user becomes false.

Options: version superlatives with the import that produced them; only
surface superlatives above a stability threshold; phrase them as
observations rather than records; recompute silently but never re-notify.

### The product question hiding in here

There is a genuinely nice experience on the other side of this. A backfill
that reaches into the past is **new old memories** — the most emotionally
loaded thing this product can deliver. "We found 708 photos from before we
thought her story started" is a better moment than any on-this-day.

So the handling shouldn't be a silent recompute. Options worth prototyping:
an **import digest** ("708 photos added, covering Apr–Jul 2021. Your timeline
now starts 103 days earlier."); a diffable timeline where newly-filled
stretches are marked as newly discovered for a while; treating a large
backfill as a **shareable event** in its own right, which feeds Loop B.

### What to decide before building ingest for real

1. Moment identity scheme, and how merge/split lineage is recorded.
2. Whether the anchor is derived, confirmed, or explicitly user-owned.
3. Whether milestones are stored facts or views recomputed on read.
4. What the user is told after an import, and what is never re-notified.
5. Whether an already-shared artifact pins its data or follows the live
   timeline.

---

## I2 — Places

97% of the test archive carries GPS, spanning roughly 41.7–45.0°N — the dog
travels. Clustering coordinates into named places ("the lake house," "the
vet," "home") is unbuilt and looks like cheap, high-delight surface area.
Reverse geocoding is the obvious approach; doing it on-device or from an
offline place file would keep the privacy story in D1/§4 intact.

---

## I3 — Video

12 files in the first export, carried through ingest but never analyzed. A
moment containing video should probably prefer it as the hero, since motion
is the most alive thing in an archive. Needs frame extraction before
detection.
