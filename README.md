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

## Experiments

[`experiments/timeline/`](experiments/timeline/) ingests a folder of photos into a moment graph and renders it as a self-contained page. Run against 1,982 files covering one dog over five and a half years, it found the pet in 90% of files and collapsed them into 723 moments across six auto-derived chapters.

Experiments are throwaway scripts, each its own `uv` project. Photos and generated output are never committed.

## Where this stands

The single-roll timeline works — detection alone is sufficient for a single-pet household, and the chapters, gotcha day and anniversaries all fall out of the data with no user input. Two things it has **not** shown: that merging a second person's camera roll beats one person's (D6, the actual wedge), and that anyone will grant full camera-roll access to find out (D7).

Next real test is getting a photo export from a second person in the same pet's life.
