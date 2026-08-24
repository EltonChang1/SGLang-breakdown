# Repository Instructions

This repository contains study notes about the SGLang source checkout at
`.source/sglang`.

- Treat `.source/sglang` as read-only except for fetching and checking out the
  fork's current default branch.
- Write all study material in this repository, primarily under `docs/`.
- Resume from `PROGRESS.md` and the coverage inventory; do not redo finished
  sections unless the source changed or an audit finds a gap.
- Explain behavior from source evidence. Include links pinned to the analyzed
  Git commit and name the relevant paths and symbols.
- Prefer teaching-oriented explanations: purpose, placement in the system,
  inputs and outputs, control flow, dependencies, invariants, failure modes,
  and a short study checklist.
- Cover every tracked file. Inventory generated, vendored, binary, cache, and
  build artifacts and explain why they do not need line-by-line notes.
- Keep navigation indexes and `PROGRESS.md` accurate after every run.
- Before finishing a run, validate Markdown links, commit the useful changes,
  and push them to the public GitHub repository.

