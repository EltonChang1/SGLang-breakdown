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
- Current statuses: 28 covered, 16 partial, 92 inventory-only, 8,183 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added [Frontend Language Execution](docs/04-frontend-language.md), tracing a
  decorated Python function through expression construction, program and
  executor threads, prompt/message/variable/media state, sampling-default
  overlay, sync/batch/stream modes, role/scoped output, fork/join, choice
  scoring, tracing, prefix caching, and the SRT HTTP handoff.
- Added the companion [file and symbol reference](docs/reference/frontend-language.md).
  It completes `api.py`, `global_config.py`, `ir.py`, `interpreter.py`,
  `choices.py`, `tracer.py`, `base_backend.py`, and `runtime_endpoint.py`; it
  gives `chat_template.py` an explicit partial boundary before a model-family
  catalog pass.
- Documented non-obvious safety rules: `.bind()` drops API-speculation size and
  bound values override same-named call keywords; sampling `clone()` drops
  dtype/regex;
  worker failures can remain stored on a returned state; batch generator style
  is chunked but input-ordered; fork position offsets and several nominal
  backend hooks are not wired by this interpreter; trace scope is not
  thread-local; and `Runtime`, `RuntimeEndpoint`, and `Engine` have different
  transport, ownership, and result contracts.
- Updated the architecture overview, study path, documentation/reference
  indexes, dependency map, glossary, coverage policy/counts, and every affected
  coverage row.

## Validation in the latest run

- Confirmed `.source/sglang` remained at the pinned commit with a clean worktree.
- Rebuilt and checked the 8,319-row inventory; status totals match this file.
- Validated local Markdown targets and anchors, coverage-note anchors, and
  pinned source paths and line ranges.
- Ran focused AST/source checks for frontend file ownership and documented
  `SglSamplingParams.clone`, `.bind()`, batch-result ordering, backend-hook, and
  fork-offset claims.
- `git diff --check` passed. No model/server runtime test was attempted because
  this run changes only study Markdown and ledger metadata.

## Next coherent study unit

Finish the frontend client layer by comparing `backend/openai.py`,
`anthropic.py`, `litellm.py`, `vertexai.py`, and `crusoe.py`; audit all concrete
records and matcher precedence in `chat_template.py`; and connect the relevant
frontend examples and tests. Trace message versus completion mode, media,
sampling-field loss, API speculative execution, usage accounting, streaming,
selection support, credentials, and error behavior before moving to the
diffusion CLI.

## Known gaps

- Provider client backends, the concrete chat-template catalog, diffusion CLI,
  and protocol-specific serving adapters are not yet covered. The common
  frontend IR/interpreter and SRT HTTP endpoint are complete.
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
