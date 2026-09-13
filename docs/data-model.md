# Core data model

Derived from a real archive, not from first principles: 1,982 files covering
one dog across five and a half years and three phones (`experiments/timeline/`).
Every claim below is something the dump actually demonstrated.

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

Consequence for D6: this dump cannot test multi-contributor merging. That
still needs a second person's roll.

## What is not in the model yet

- **Individual pet ID.** Unnecessary here — 90% of a single-pet household's
  animal photos are that pet. Required the moment a second contributor's
  roll arrives, since theirs contains other people's dogs.
- **Place.** 97% GPS coverage, spanning roughly 41.7–45.0°N — the dog
  travels. Clustering coordinates into named places is unbuilt and looks
  cheap.
- **Video.** 12 files, currently carried but not analyzed.
- **Ownership and custody.** The unresolved question flagged in D6: what
  happens to a contributor's moments when they leave.
