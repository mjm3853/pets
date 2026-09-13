# Pets

Hub repo for the pet memory product — an app that auto-builds a pet's life timeline from your camera roll instead of asking you to curate one.

**Status:** early ideation, pre-build. See [docs/product-vision.md](docs/product-vision.md) for the full working vision (premise, architecture principles, growth loops, risks, open questions).

## Repo layout

- `docs/` — product thinking: vision doc, decisions, research notes.
- `experiments/` — throwaway scripts and notebooks for de-risking (e.g. running an animal detector over a sample camera roll — see vision doc §9). Not production code.

## Current focus

Per the vision doc's next step (§9): validate that an auto-built timeline from raw camera roll photos actually feels like something, before building any app around it. That's a detection pass over a sample of photos, rendered as a plain static page, no app required.
