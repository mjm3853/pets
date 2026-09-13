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
- [docs/decisions.md](docs/decisions.md) is the source of truth for
  decisions and their reasoning; the vision doc describes the product. When
  a conversation makes or changes a decision, add or update an entry there
  (with status locked/proposed/superseded) rather than letting it live only
  in chat history. Don't edit the vision doc's §3 table to track decisions.
- **Before implementing any issue, read [docs/implementing.md](docs/implementing.md).**
  It has the orientation, the fast iteration loop, the eight rules that
  must survive any change, and the definition of done. Every open issue has
  an *Implementation* section with files, functions, steps and a *Verify*
  list; the closing comment must carry the measurements, not just "done".
- Work is tracked in **GitHub issues** on `mjm3853/pets` (`gh issue list`).
  Labels: `now` / `next` / `later` for scheduling, `correctness` / `ingest` /
  `experience` / `perf` for kind. `correctness` means a silent-wrong-answer
  risk and outranks everything else. Issues link back to the docs for
  reasoning; the docs stay the source of truth, issues are the queue.
- [docs/log.md](docs/log.md) is an append-only working log. Add a dated entry
  when something is learned or measured. **Never edit or delete past
  entries** — if one turns out to be wrong, write a new entry saying so.
- [docs/ideas.md](docs/ideas.md) is the parking lot for problems worth
  solving later but deliberately not solved yet. Put open problems there,
  not in decisions.md. [docs/data-model.md](docs/data-model.md) holds the
  object model, and every claim in it is grounded in measured data.
- Never identify anything by array position or sort order — see D13. A
  re-ingest renumbered 100% of moments and made stale pointers resolve
  silently to the wrong photo. This applies to experiment scripts too.
- The founding household is on Android phones plus a Mac; there are no
  iPhones to test with. Don't propose iOS-only tooling (Vision framework,
  osxphotos, Photos.app export) as the primary path.
