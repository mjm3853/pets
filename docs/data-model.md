# Core data model

Derived from a real archive, not from first principles: **4,547 files across
four pets and fourteen years**, from two people's exported albums
(`experiments/timeline/`). Every claim below is something the data actually
demonstrated; the numbers are current unless a line says otherwise.

The vision doc names four objects — `pet` / `moment` / `contributor` /
`milestone`. Running real data through them changed two of the four.

---

## The load-bearing insight: a file is not a moment

1,782 photos of Izzy are **723 moments**. People burst-shoot: three frames in
twenty-two seconds is one event, not three. Clustering media by a 20-minute
gap collapses the archive 2.5× and is the difference between a wall of
near-duplicates and a readable life. The ratio rises with excitement — the
puppy months burst harder than the adult years.

This is the unit the whole product narrates in. Getting it wrong means the
timeline shows the same dog in the same pose eight times and feels like a
file browser. Everything downstream — recaps, on-this-day, share cards —
selects moments, then picks a hero frame inside one.

```
media          one file. has a timestamp, maybe GPS, maybe a detection box
  └── moment   a burst. the narrative unit. has a hero frame
        └── era        a life year, anchored on the first photo
              └── pet
milestone      a derived fact pointing at a moment
contributor    a person. NOT a device (see below)
```

## `media`

One row per file. Cheap, immutable, never shown directly.

| field | notes |
|---|---|
| `taken_at` + `time_source` | `exif` \| `filename` \| `mtime`. Keep the provenance — it decides trust |
| `kind` | photo / motion / portrait / night / video. Pixel encodes this in the filename |
| `device` | EXIF make+model |
| `gps` | present on 97% of this archive |
| `pet`, `species`, `score`, `box` | detector output, normalized box |
| `species` | detector's guess, kept as evidence and **not trusted** — see below |
| `people` | count of `person` detections — the togetherness signal |

**`time_source` is not a debugging field.** 32 files (Snapchat saves) had no
EXIF and no date in the filename, so they fell back to file mtime and all
landed on the day the zip was unpacked — which corrupted "most recent photo"
and "longest burst" until they were quarantined. Undated media must be held
out of the spine and shown in its own bucket, never silently placed. Any
product ingesting from messaging apps will hit this constantly.

## `moment`

The narrative unit. Burst-clustered media.

Key fields: `started_at`/`ended_at`, `media_count`, `has_pet`, `with_people`,
`dated`, `gps`, `hero`, `hero_box`, `files[]`.

**Burst length is the best available proxy for importance.** Nobody rates
their photos, but they do keep shooting when something matters — 324 moments
in this archive are a single frame, while the top ones run to 31. That is
behavioural evidence, free of user effort, and it is strong enough to drive
visual hierarchy: sizing contact-sheet cells by frame count makes the
important moments findable at a glance without anyone marking a favourite.

**Hero selection matters more than it sounds.** Scoring by confidence alone
picks tight crops of a distant dog. `score × √(box area)` picks frames where
the animal is both confidently detected and actually fills the frame. Since
every thumbnail is then cropped to `hero_box`, the contact sheet comes out
auto-framed on the pet — that visual consistency is most of what makes the
output feel curated rather than dumped.

## `era` — life years, not gaps

First attempt segmented on silence (>45 days with no photos). It produced
**one era across five years**, because a well-loved pet has no long silences;
the longest gap in this archive is 36 days.

Life years anchored on the **first photo** produced six clean chapters, each
ending days before the next anniversary. No tuning, no thresholds, and it
matches how people already talk ("her first year").

**The anchor is a fact the user owns, not a derivation.** Izzy's adoption day
is 9 Apr 2021; the archive derives 7 Apr. A real anchor can be *later* than the
first photo, because people photograph an animal before bringing it home — and
those moments then sit before every chapter. They get a **prologue**, a
category that cannot exist while the anchor is derived, since a derived anchor
is the first photo by construction. For a rescue or rehoming that window holds
the whole origin story.

Anchor on first-seen, not January 1 — but hold the anchor loosely. A second
import of this same archive added 708 earlier photos and moved it 103 days,
taking all five anniversaries with it. See [D14](decisions.md) and
[I1](ideas.md): the past is never settled, and anything derived from the
earliest photo is provisional.

## `milestone`

Derived facts, never entered. What the archive yielded on its own: first
photo, most recent, longest burst, most photographed day, longest quiet
stretch, and each anniversary. The quiet-stretch one is the surprise — "in
five years the longest she went unphotographed was 36 days" is a sentence
no user would ever think to write down.

Milestones are **pointers** (`kind`, `date`, `label`, `moment`), not content.
They attach to the timeline rather than living in it — which makes the
identity of what they point at load-bearing. Positional moment IDs are
disqualified ([D13](decisions.md)); a re-ingest renumbered every moment and
each stale pointer resolved silently to a different, plausible photo.

Every milestone here is also a **maximum over the archive**, so any import
can dethrone one, and a "longest quiet stretch" can even shrink. Superlatives
already shown to a user must be treated as versioned observations, not
standing records.

## `contributor` — measured, not theorised

Two real rolls, merged: Matt 1,782 photos of Izzy, Renee 2,142, with only
**20 files in common** (the same photo texted between them at some point,
kept once). Each holds close to 290 days the other has nothing for. Merged
day coverage is 772 against 484 and 490 for each alone — **the merge adds
58% more days than the better single roll**, and 103 moments are built from
both cameras at the same event.

That is the D6 wedge, quantified, from two ordinary phone exports with no
shared album and no coordination.

**Contamination is real but small.** Renee's roll contained two photos of
other people's dogs from 2018 and 2019, years before Izzy. At 0.05% that is
harmless to the archive — but it was catastrophic to anything computed as an
extremum (see D15), which is the actual lesson. Individual pet ID becomes
necessary once a second roll joins; it does **not** need to land before the
merge is valuable.

## `contributor` — and why device is not one

This archive has three camera models. It is **one person upgrading phones**:
Pixel 5 → Pixel 8 (Oct 2023) → Pixel 10 Pro (Jan 2026), with zero date
overlap between them.

Tempting shortcut, wrong answer. Device succession and genuine
multi-contributor both look like "several EXIF models," and the only
reliable discriminator is **temporal overlap**. Contributor has to be
account identity, with device kept as metadata. Perfectly clean device
succession is also a decent heuristic for *stitching* one person's history
across upgrades.

Device succession still is not contribution: this archive now holds five
camera models across two people, and the model tells you which phone, never
which person. Contributor is carried explicitly through ingest from the roll
a file arrived in.

## What is not in the model yet

- **Individual pet ID.** Deliberately not built (D17). 0.05% contamination
  does not justify an embedding-and-clustering pipeline, the platforms already
  do it, and the cheap heuristic fails: 294 files in this dog archive are
  labelled sheep, horse, cat, cow, bird or bear and **every one is a dog**,
  including a "sheep" at 0.94. The detector is trustworthy for *an animal is
  present* and untrustworthy for *which animal*, so the pet's species is a
  profile field the user sets.
- **Place.** 97% GPS coverage, spanning roughly 41.7–45.0°N — the dog
  travels. Clustering coordinates into named places is unbuilt and looks
  cheap.
- **Video.** 12 files, currently carried but not analyzed.
- **Sub-moment structure.** A burst is currently a flat list. Expanding one
  reveals the sequence — the retries, the seconds between frames, the one
  that worked — which is a layer of story the platforms discard. Worth
  modelling explicitly if it earns its keep.
- **Ownership and custody.** The unresolved question flagged in D6: what
  happens to a contributor's moments when they leave.

---

## People, pets and the graph between them

*Proposed from a conversation, then **built** — issue #22 is closed and all
of this ships. `assigned_by` values in practice are `user`, `album`,
`caretaker`, `inferred`; `platform` was never used.*

### Why now

Two things surfaced that the current model cannot hold. A friend's
merle-patterned dog appears throughout the archive — visits, and dogsitting —
and there is nowhere to put it: the model has one pet, and every animal
detection is silently assumed to be her. And Matt and Renee are two people who
share one pet, while their friend is a person who shares a *different* pet
with them intermittently. The vision's §4 asked for "people with access to
this pet"; this is what that looks like once there are several of each.

### The model

```
person       an identity. contributes media. has a name and an account.
pet          the organising entity. name, species (user-set, D17), anchor, profile.
household    people and pets who live together. a default grouping, NOT a
             permission boundary.
access       person <-> pet, with a role and optional date range.
             THIS is the permission model (D5).
appearance   pet <-> moment. which pets are in a moment; a moment can hold
             several. carries assigned_by.
media, moment, era, milestone   as today, unchanged.
```

Roles on `access`: **owner** (full, including anchor and profile);
**caretaker** (contributes while they have the pet — a dogsitter, a foster;
usually date-boxed); **friend** (contributes photos they happen to take);
**viewer** (sees, does not add). Roles are per pet, not per household. The
friend is a `friend` of Izzy and an `owner` of the merle dog, and nothing
about either household changes that.

### The one structural change

`moment.pet` becomes `moment.appearances[]`. Today a moment has a pet by
assumption. Tomorrow it has zero or more, each with `assigned_by`: `user`,
`album`, `caretaker` or `inferred`. That field is the bridge between "multiple pets are
in scope" and "we do not build recognition" (D17). In a single-pet household
`inferred` is right almost always and nothing changes. With a second animal,
assignment comes from the person, or from the platform's own labels if the
export carries them — never from a model we own.

### What the graph makes possible

**Cross-household contribution.** The friend dogsits Izzy for a week and
takes forty photos. With a `caretaker` edge for that week, those photos flow
into Izzy's timeline. That is the D6 merge generalised past the household —
your friend's photos of your dog, from when you weren't there — and it is the
thing shared albums structurally cannot do. In reverse it is exactly what has
already happened: Matt and Renee hold photos of their friend's dog that the
friend has never seen.

**A pet with several homes.** Foster-then-adopted, shared custody, a dog that
summers with grandparents. Date-ranged `access` edges cover every one without
a special case.

**Multiple pets, multiple species, one household.** Each pet is its own
timeline, anchor and chapters. The household is a lens over them, not a
container — which is what keeps D5's warning against "family plan" intact.

### What it costs

Assignment. Without recognition, every moment in a multi-pet household needs
someone or something to say which pet. The realistic answers, in order: the
platform's labels via export; the contributor's roll as a prior (Renee's roll
is overwhelmingly Izzy); a time-boxed `caretaker` edge as a prior (photos
during the dogsitting week are probably the visiting dog); and **batched
correction, never per-photo prompting.** This cost is real, and it is the
reason to keep the single-pet path exactly as fast as it is today.

### What it deliberately does not include

People *in* moments as identities. The detector counts persons; it does not
say who. "With her people" stays a count. Face recognition is a different
product with a different privacy posture, and a decision for another day.

### Revised after Oakley: sparse pets, subject folders, guess fewer

A friend's dog arrived as a folder of 138 files before the model existed,
and settled three questions with data rather than argument.

**Sparse pets.** Oakley is 138 files across seven years, 88 of them in one
year and then a trickle. There is no sustained period to anchor on and no
"life" to chapter. Most pets in most people's archives look like this — a
friend's dog, a parent's cat, a dog that was dogsat twice. The model must
hold a pet that has **only appearances**: no anchor, no eras, no milestones,
just the moments it is in, in order. A timeline is earned by data, not
assumed by the schema. `find_anchor()` failing to find a run is the signal.

**Subject folders.** 53 of Oakley's 138 files are Matt's own photos, pulled
out by subject. The folder is *about* a pet, not *from* a person. That is
how most people will hand photos over — "here are pics of my dog" — and it
is a strong *hint*, not proof: every file in it is `assigned_by: album`
(D23) for that pet, with the contributor recovered from filename overlap with known rolls
or left `unknown`. Ingest takes `--about NAME=PATH` alongside `--roll`.

**Guess fewer times than needed (D21).** The single-pet inference that gets
Izzy right 99.95% of the time is wrong the moment a second dog exists: when
Oakley's album first landed, 27 of Izzy's 1,378 moments turned out to contain
him — 18 entirely, 9 both dogs. Two percent, forty times the stray rate, and
invisible until a human curated a folder. *(Point-in-time, before Ray and
Shadow; the fuller picture is D23 and the table above.)* So
inference is used for exactly one case, a contributor's single primary pet.
No secondary pet is ever inferred. Ambiguity resolves to **unassigned**, a
first-class state rendered in its own strip, never hidden, never defaulted.
Mixed bursts — some frames user-assigned to one pet, the rest inferred as
another — are the one automatic multi-pet case, and they are the playdate.

**Eras only for a contributor's own pet.** Ray has a real early period and
then a five-year hole; year-chapters would emit six empty ones. A friend's
pet never gets an anchor guessed for it — no owner is here to confirm one
(D21). Sparse view, `first_seen`, `last_seen`, and that is all.

**The input is an album, and that is now the design (D24).** Camera rolls
are out of scope. An album is ~90% animal photos and roughly two-thirds the
intended pet — high signal, imperfect. Hand-tagging 40 detections from
Oakley's album found **20 Izzy, 20 Oakley** (D23), because people build a
pet's album from the occasions that pet was around, and on those occasions
both animals are in frame.

So **multi-pet is the normal case, not the exception**, and the 32% is not
an error to eliminate — those photos really do contain both. The model's job
is to record both appearances and make the remainder cheap to correct, which
is what `appearances[]` and the correction tray exist for.

**Zero required metadata.** A pet needs a name. Species, anchor, adoption
date, dogsitting windows are all optional and all fillable later. People do
not look up dates, and a product that needs them to will not get them.
