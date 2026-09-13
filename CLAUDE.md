# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this repo is

The hub for the pet memory product: an app that auto-builds a pet's life
timeline from the camera roll instead of asking the user to curate one.
Currently pre-build — ideation and de-risking, not production code.

Read [docs/product-vision.md](docs/product-vision.md) before proposing
features or architecture. It contains locked decisions (§3), architecture
principles (§4), and named risks (§7) — don't relitigate those without the
user raising it first.

## Repo layout

- `docs/` — product thinking: vision doc, decisions, research notes.
- `experiments/` — throwaway scripts for de-risking specific open questions
  (§8 of the vision doc). Each experiment is its own `uv` project
  (`experiments/<name>/pyproject.toml` + `.venv`), not a shared dependency
  tree — these are one-off scripts, not a growing codebase.

## Conventions

- Python experiments: `uv init` per experiment, `uv add` for deps, `uv run`
  to execute. Don't add a top-level dependency manager until there's an
  actual app to build.
- Camera-roll photos and model weights are never committed — each
  experiment's `.gitignore` should exclude sample media and downloaded
  weights. Treat any real pet photos as the user's private data.
- Keep the vision doc as the single source of truth for product decisions.
  If a conversation changes a "locked" decision, update the doc's §3 table
  rather than letting the decision live only in chat history.
