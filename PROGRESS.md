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
- Current statuses: 5 covered, 13 partial, 92 inventory-only, 8,209 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Established the [ordered study path](docs/00-study-path.md), including
  configuration, protocols, scheduling/cache, model execution, distributed
  modes, diffusion, routing/native services, and operations/audit phases.
- Added an [architecture overview](docs/01-architecture-overview.md) that maps
  the Python frontend, SRT, kernels, diffusion runtime, Rust extensions,
  gateway, experimental router, and validation material.
- Traced `sglang serve` backend selection, default LLM startup, process/IPC
  topology, topology variants, readiness, cleanup, and one native `/generate`
  request.
- Added a file/symbol [entry-point reference](docs/reference/entrypoints.md).
  The small package/CLI launch files are complete; large server and manager
  files are explicitly partial.
- Seeded the [dependency map](docs/90-dependency-map.md) and
  [glossary](docs/99-glossary.md).

## Next coherent study unit

Document configuration and startup in depth: `ServerArgs` annotations and
argument groups, config-file precedence, resolution passes, runtime namespace
publication, platform selection, `PortArgs`, parallel rank construction,
readiness, warmup, and shutdown. This should turn the current partial entries
for `server_args.py` and `runtime_context.py` into reviewable subsystem notes
without jumping ahead to scheduler policy.

## Known gaps

- Frontend language, offline engine APIs, diffusion CLI, and protocol-specific
  serving adapters are not yet covered.
- Scheduler admission/batching, radix/KV caches, model execution, model/layer
  families, kernels, distributed/advanced modes, and diffusion internals remain.
- Rust crates, gateway, router, tests, benchmarks, examples, docs, packaging,
  deployment, CI, release, security, and operations need dedicated guides.
- The current architecture trace names only the entry symbols in several large
  runtime files; their ledger status remains partial by design.
