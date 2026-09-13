# Pets

Hub repo for the pet memory product — an app that auto-builds a pet's life timeline from your camera roll instead of asking you to curate one.

**Status:** early ideation, pre-build. Nothing is being shipped yet; the work so far is de-risking against real data.

## Docs

- [docs/product-vision.md](docs/product-vision.md) — the working vision: premise, growth loops, risks, open questions.
- [docs/decisions.md](docs/decisions.md) — the decision log, with reasoning and what would overturn each one. Source of truth.
- [docs/data-model.md](docs/data-model.md) — the core object model. Every claim measured against a real archive.
- [docs/ideas.md](docs/ideas.md) — parking lot for problems worth solving later, deliberately unsolved.

## Tracking

Work lives in [GitHub issues](https://github.com/mjm3853/pets/issues), labelled
`now` / `next` / `later`. The `correctness` label marks silent-wrong-answer
risks, which outrank everything else — two of the three findings so far were
bugs that produced plausible wrong output rather than errors.

## Running it

Everything lives in [`experiments/timeline/`](experiments/timeline/) — see its
[README](experiments/timeline/README.md) for the full guide. The short version,
with [`uv`](https://docs.astral.sh/uv/) installed:

```bash
cd experiments/timeline
uv run ingest.py --pet Izzy --species dog --anchor 2021-04-09 --roll "Matt=/path/to/photos"
uv run render.py --out izzy.html
open izzy.html
```

No server, no database, no build step. Run against 4,403 files from two
people's camera rolls, it finds an animal in 90% of them and collapses them
into 1,378 moments across a prologue and six life-year chapters.

Experiments are throwaway scripts, each its own `uv` project. Photos and
generated output are never committed.

## Sharing it

The output is a 1 MB page plus a 22 MB folder of JPEGs, so hosting is
technically trivial — any static host serves it unchanged. The real constraint
is that it is a private photo archive and static hosting is unauthenticated by
default; an unguessable URL is not access control. For now it stays local:
send the single-file build, or serve it over Tailscale. Anything wider needs
real auth, which is a product decision rather than a hosting one.

## Where this stands

The single-roll timeline works — detection alone is sufficient for a single-pet household, and the chapters, gotcha day and anniversaries all fall out of the data with no user input. Two things it has **not** shown: that merging a second person's camera roll beats one person's (D6, the actual wedge), and that anyone will grant full camera-roll access to find out (D7).

Next real test is getting a photo export from a second person in the same pet's life.
