# Pets

Hub repo for the pet memory product — an app that auto-builds a pet's life timeline from your camera roll instead of asking you to curate one.

**Status:** early ideation, pre-build. See [docs/product-vision.md](docs/product-vision.md) for the full working vision (premise, architecture principles, growth loops, risks, open questions) and [docs/decisions.md](docs/decisions.md) for the decision log with reasoning.

## Repo layout

- `docs/` — product thinking: vision doc, decisions, research notes.
- `experiments/` — throwaway scripts and notebooks for de-risking (e.g. running an animal detector over a sample camera roll — see vision doc §9). Not production code.

## Current focus

Validate the wedge (decisions D6/D7) before building any app: pull photos off each household member's Android phone, detect the pet, and render one merged, dated timeline as a plain static page. The question is whether the merged multi-person view feels meaningfully better than one person's roll alone. Start in [experiments/detection_pass/](experiments/detection_pass/).
