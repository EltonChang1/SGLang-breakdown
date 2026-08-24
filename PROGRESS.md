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
- Current statuses: 20 covered, 15 partial, 92 inventory-only, 8,192 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added a teaching-oriented [Offline Engine API](docs/03-offline-engine.md)
  covering the in-process-versus-single-process distinction, constructor and
  event-loop lifecycle, sync/async and single/batch/streaming return shapes,
  request normalization/correlation, DP routing, output records, encoding,
  reranking, scoring, sessions, controls, weights, LoRA, RPC, and shutdown.
- Added the companion [file and symbol reference](docs/reference/offline-engine.md).
  It completes `EngineBase.py`, `engine.py`, `engine_score_mixin.py`, and
  `tokenizer_manager_score_mixin.py`; it adds explicit partial boundaries for
  engine-used `io_struct.py` and `tokenizer_control_mixin.py` responsibilities
  and deepens the existing `tokenizer_manager.py` trace.
- Documented non-obvious safety rules: sync methods cannot drive an already
  running loop, spawned scripts need a main guard, batch streams are
  completion-interleaved and indexed, scheduler session history uses
  `session_params` rather than the distinct `session_id`, weight mutations use
  the model writer lock and require cache invalidation, and LoRA result objects
  must be checked for success.
- Updated the architecture overview, study path, documentation/reference
  indexes, dependency map, glossary, coverage policy/counts, and every affected
  coverage row.

## Validation in the latest run

- Confirmed `.source/sglang` remained at the pinned commit with a clean worktree.
- Rebuilt and checked the 8,319-row inventory; status totals match this file.
- Validated all local Markdown targets and note anchors, every coverage-note
  anchor, and pinned source paths and line ranges across all guides.
- An AST-based adapter parity check confirmed sync and async generation map the
  same 30 request fields and sync/async embedding map the same 10 fields.
- `git diff --check` passed. No model/device runtime test was attempted because
  this run changes only study Markdown and ledger metadata.

## Next coherent study unit

Continue Phase 1 with the frontend language execution core: trace `@function`
and `SglFunction` construction through IR expressions, `ProgramState` and
`StreamExecutor`, sync/batch/stream execution, choice evaluation, the
`BaseBackend` contract, and the first handoff through `RuntimeEndpoint`. Cover
`lang/api.py`, `ir.py`, `interpreter.py`, `global_config.py`, `choices.py`,
`backend/base_backend.py`, and the relevant `backend/runtime_endpoint.py`
boundary before surveying provider-specific client adapters.

## Known gaps

- Frontend language, provider client backends, diffusion CLI, and
  protocol-specific serving adapters are not yet covered.
- Model- and backend-specific configuration handlers, declarative override
  providers, and runtime-context derived helpers remain assigned to their
  owning subsystem passes rather than being treated as complete here.
- Request/control schemas and tokenizer/control manager files remain partial
  outside the methods exercised by the offline API; session-controller and
  weight/cache/model-worker internals retain their later subsystem passes.
- Scheduler admission/batching, radix/KV caches, model execution, model/layer
  families, kernels, distributed/advanced modes, and diffusion internals remain.
- Rust crates, gateway, router, tests, benchmarks, examples, docs, packaging,
  deployment, CI, release, security, and operations need dedicated guides.
- The current architecture trace names only the entry symbols in several large
  runtime files; their ledger status remains partial by design.
