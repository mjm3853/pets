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

---

## I4 — Storage and media management

**Surfaced:** 2026-09-13, once the archive passed 4,000 files.

Still deliberately local and still proof-of-concept. This is not a call to
build a backend; it is the list of things that will hurt next, in the order
they will hurt, so the PoC can stay fast without a rewrite.

### What it costs today

| | |
|---|---|
| Originals | ~20 GB extracted across two rolls |
| Detection | full re-run over every file on every ingest |
| Thumbnails | re-cropped from originals on every render |
| Rendered page | 17.8 MB of base64, growing linearly with moments |

The two real problems are that **nothing is cached** and **the page embeds
its own images**. Detection results and crops are both pure functions of
(file bytes, parameters), so recomputing them is wasted work. Adding one
photo currently costs a full re-ingest of everything.

### Incremental plan, cheapest and highest-value first

1. **Content-hash cache for detection.** Key on a hash of the file bytes plus
   model and confidence. Re-ingest then only pays for genuinely new files,
   which turns a second roll arriving from a 15-minute job into a 2-minute
   one. This is the single biggest win and it is small.
2. **Content-hash cache for crops.** Same idea keyed on hash plus crop
   geometry and size. Makes render iteration cheap, which matters because
   render is where design gets tuned.
3. **Stable media identity.** Cache keys are content hashes, which is exactly
   what D13 asks for. Adopting them for caching gets the identity fix almost
   for free — do these together rather than inventing two schemes.
4. **Optional external thumbnails.** Emit a folder of JPEGs plus a small HTML
   instead of one fat base64 file, with the self-contained mode kept behind a
   flag for sharing. Faster to open, browser-cacheable, and lazy loading
   actually works. The single-file mode stops scaling somewhere around
   25–30 MB.
5. **SQLite instead of a JSON blob.** `moments.json` is fine at this size and
   will get awkward past roughly 10k media rows, particularly for the "which
   files changed" queries that caching wants. Not yet.
6. **Never keep the zip after extraction.** Already practice; worth stating.

### What this rehearses for the real product

The vision's §4 architecture is on-device index plus selective upload. The
PoC should mirror that shape rather than diverge from it: **index everything,
materialize only what is displayed.** A content-addressed local cache with a
derived-artifact layer on top is a small version of exactly that, so work
here is not throwaway. Resist anything that assumes all originals are
present and local forever, because on a phone they will not be.

---

## I5 — The two loops: onboarding and maintenance

**Surfaced:** 2026-09-13, from Matt.

There are at least two distinct user experiences, and they want opposite
things from the same machinery.

### Loop 1 — onboarding a life that already happened

Bulk import of an unorganized archive. High volume, one big push, user
present and motivated, tolerant of latency. The job is not "add photos", it
is **establish coverage**: get the beginning (the puppy and adoption
photos), and get a representative spread across the whole life.

Observed in this project, twice. The first export was missing the first
three months entirely. The second contributor's roll reaches back further
still. Both times the most emotionally valuable material was the part that
was missing, and neither absence was visible until something else arrived to
reveal it.

That suggests the product's job during onboarding is **showing the user
where the holes are**, not celebrating the volume it imported. Coverage is
measurable with what already exists: months with at least one moment, the
gap distribution, moments per life year. "You have 400 photos from 2021 and
12 from 2023" is a true, specific, actionable nudge. "Do you have anything
from before you brought her home?" is the highest-value question the product
can ask, and it should ask it explicitly, because those photos are usually in
someone else's roll or on a dead phone.

### Loop 2 — maintenance

Steady state. A few photos a week, arriving continuously, competing with
everything else for attention. Must be effectively zero-effort or it dies —
this is the effort/payoff asymmetry the vision doc opens with. The daily
value here is resurfacing, not capture, so nudges have to be earned rather
than nagging, and correction (wrong pet, wrong date, not-actually-a-moment)
has to be cheap and batched.

### Where the two collide with the architecture

**Onboarding never ends.** Renee's roll is an onboarding-shaped event
arriving in year five of steady state. A rescue, an old phone, a new
contributor, a Takeout export — every one of them is Loop 1 happening during
Loop 2. So onboarding is not a phase with an exit; it is a **mode the system
must support forever**. This is D14 restated more sharply, and it means the
bulk path cannot be a throwaway onboarding script.

**They need opposite notification behaviour.** Loop 2's trickle is genuinely
new and worth surfacing. Loop 1's flood is *old* content arriving now, and
firing four hundred "new moment" notifications would be catastrophic. The
system therefore has to separate **taken-at from ingested-at** everywhere,
and drive resurfacing off taken-at while driving "what changed" off
ingested-at. Neither field is optional and they are not interchangeable.

**Batch and stream want the same code.** Loop 1 is Loop 2 run four thousand
times — but only if ingest is idempotent and identity is stable, which is
exactly what D13 requires. Getting that right once means one ingest path
instead of two.

**The digest is the shared surface.** Both loops end in the same question:
what just arrived, and what does it change? I1 already proposes an import
digest for backfill. The same object serves maintenance at a smaller scale.
Build one, size it to the import.

### Open questions

1. What is the coverage metric, concretely, and is it legible to a user?
2. Does the product ever ask for specific missing periods, and how does that
   avoid feeling like homework?
3. What is the correction UI, given corrections arrive in batches after a
   bulk import but one at a time in steady state?
4. Where does a second contributor get invited — during onboarding, or when
   the system notices coverage gaps someone else could fill?
