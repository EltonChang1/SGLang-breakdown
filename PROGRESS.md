# Coverage Progress

## Source snapshot

- Repository: `EltonChang1/sglang`
- Analyzed commit: `f464e77d17a3908ad0ea32547b1e8b039bcbd354`
- Last completed run: 2026-08-24

## Completion rules

- Every tracked source file must appear in the coverage inventory.
- Every meaningful package or subsystem needs a conceptual overview.
- Important classes, functions, configuration objects, protocols, and entry
  points need source-linked explanations.
- Cross-module runtime flows need ordered traces.
- Tests, examples, build tooling, CI, packaging, and deployment need dedicated
  notes.
- Generated, vendored, binary, cache, and build artifacts must be labeled with
  a reason when detailed explanation is skipped.
- The final study path must order the material from prerequisites through
  internals and advanced topics.

## Current work

- [x] Inventory all 8,319 tracked paths and record the source commit.
- [x] Create the initial architecture map and ordered study sequence.
- [ ] Work through each subsystem and file in the recorded order.
- [ ] Audit coverage and resolve missing or shallow areas.

## Coverage ledger

- Inventory: [`docs/coverage/inventory.csv`](docs/coverage/inventory.csv)
- Policy and counts: [`docs/coverage/README.md`](docs/coverage/README.md)
- Generator: [`scripts/build_coverage_inventory.py`](scripts/build_coverage_inventory.py)
- Current statuses: 16 covered, 14 partial, 92 inventory-only, 8,197 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added a teaching-oriented [configuration and startup guide](docs/02-configuration-and-startup.md)
  covering the CLI/YAML schema, precedence, the raw-to-resolved declaration
  pipeline, platform selection, runtime namespace publication and overrides,
  configured versus live parallel state, rank/port construction, readiness,
  warmup, health gating, and shutdown.
- Added the companion [file and symbol reference](docs/reference/configuration-startup.md).
  It completes the config merger, argument metadata/actions, empty package
  marker, and all in-tree platform files; `server_args.py`, `overrides.py`, and
  `runtime_context.py` remain explicitly partial where later model/cache/kernel
  guides own the details.
- Deepened the startup trace in `engine.py`, `http_server.py`, and
  `scheduler.py`: scheduler pipe readiness is now clearly separated from
  public readiness after a real warmup request, with failure and cleanup owners
  named.
- Updated the study path, documentation/reference indexes, dependency map,
  glossary, and all affected coverage rows.

## Validation in the latest run

- Confirmed `.source/sglang` remained at the pinned commit with a clean worktree.
- Rebuilt and checked the 8,319-row inventory; status totals match this file.
- Validated local Markdown targets and note anchors, and verified pinned source
  paths and line ranges for every guide.
- A dependency-light `ConfigArgumentMerger` smoke test passed for CLI
  precedence and YAML boolean/list/dict conversion.
- `git diff --check` passed.
- Targeted upstream config/platform/runtime-context tests could not collect in
  this lightweight environment because `orjson` is not installed; no source
  assertion ran. Interpreter/pytest caches from the attempt were removed so
  the source checkout remained unchanged.

## Next coherent study unit

Finish the remaining Phase 1 public surface with the offline `Engine`:
constructor normalization, sync/async generation and embedding APIs, sessions,
control/RPC methods, weight updates, and shutdown/context-manager semantics.
Relate each public method to the shared tokenizer/scheduler runtime without
entering scheduler policy, then update the `engine.py` ledger boundary before
moving to frontend language execution and protocol adapters.

## Known gaps

- Frontend language, offline engine APIs, diffusion CLI, and protocol-specific
  serving adapters are not yet covered.
- Model- and backend-specific configuration handlers, declarative override
  providers, and runtime-context derived helpers remain assigned to their
  owning subsystem passes rather than being treated as complete here.
- Scheduler admission/batching, radix/KV caches, model execution, model/layer
  families, kernels, distributed/advanced modes, and diffusion internals remain.
- Rust crates, gateway, router, tests, benchmarks, examples, docs, packaging,
  deployment, CI, release, security, and operations need dedicated guides.
- The current architecture trace names only the entry symbols in several large
  runtime files; their ledger status remains partial by design.
