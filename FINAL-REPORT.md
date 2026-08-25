# Final SGLang Breakdown Report

Generated for the 2026-08-25 10:11 AM America/Los_Angeles run. The scheduled
reporting window requires this file for every run beginning at or after 10:00
AM and ends at 12:00 PM.

## Executive assessment

The study guide is **not complete** under its own completion rules. The
inventory is exhaustive—all 8,319 tracked source-snapshot paths have a category,
status, source URL, and reason—but 8,021 rows remain pending and 41 are only
partial. The public entry/configuration/offline/frontend/diffusion surfaces and
the main Python protocol adapters now have deep teaching guides. Scheduler and
cache internals, model execution, most distributed and multimodal systems,
Rust/gateway/router subsystems, and project-wide operations still require
subsystem and file-level coverage.

This run made a defensible Phase 3 advance: it completed the shared native gRPC
schema, Python runtime bridge, and focused unit test while explicitly leaving
the larger Rust crate and four other gRPC systems incomplete.

## Pinned source and repository state

- Source repository: `EltonChang1/sglang`
- Analyzed commit:
  [`f464e77d17a3908ad0ea32547b1e8b039bcbd354`](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354)
- Local source checkout: `.source/sglang`, treated as read-only
- Study repository: [`EltonChang1/SGLang-breakdown`](https://github.com/EltonChang1/SGLang-breakdown)
- Branch and destination: `main` -> public `origin/main`

The source checkout was clean and at the pinned commit before analysis. The
final pre-commit audit must repeat both checks; its result is recorded below.

## Runs and commits

The repository had 18 commits at this run's start. They record initialization,
source pinning, architecture/inventory, configuration/startup, offline engine,
frontend execution, provider clients/templates, diffusion CLI, native generate,
OpenAI completion/chat, embedding/scoring, Responses, Anthropic Messages, and
Ollama. The current native-gRPC and final-report deliverables are intended as
the nineteenth commit; because this file is part of that commit, its own SHA
cannot be embedded without changing it.

Substantive study sequence:

| Stage | Published commit(s) before this run |
| --- | --- |
| Initialization and pinned snapshot | `d31fbd7`, `9ea85da` |
| Architecture and exhaustive inventory | `a470d7d` |
| Configuration and startup | `c73124e` |
| Offline Engine | `5fc589a` |
| Frontend language | `a082d79` |
| Provider clients and templates | `23c8bcb` |
| Diffusion generate CLI | `6cd468c` |
| Native generate protocol | `03d0fe3` |
| OpenAI completions/chat | `2e0d536` |
| README editorial pass | `7e66f05` |
| Embedding/scoring plus audit corrections | `df53771`, `7eda429`, `9c056b5` |
| OpenAI Responses | `22de6a6` |
| Anthropic and Ollama plus validation corrections | `e8ac56f`, `70ed366`, `18ff9ea` |
| Native gRPC Python bridge and this report | containing commit |

## Coverage inventory

The committed ledger contains one row for every path returned by
`git -C .source/sglang ls-files`.

### Overall status

| Status | Paths |
| --- | ---: |
| Covered | 165 |
| Partial | 41 |
| Inventory-only | 92 |
| Pending | 8,021 |
| **Total** | **8,319** |

### Category by status

| Category | Covered | Partial | Inventory-only | Pending | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Source | 83 | 20 | 0 | 3,444 | 3,547 |
| Test or benchmark | 47 | 11 | 0 | 2,858 | 2,916 |
| Configuration | 1 | 2 | 0 | 865 | 868 |
| Documentation | 10 | 3 | 0 | 553 | 566 |
| Example | 24 | 0 | 0 | 123 | 147 |
| CI | 0 | 0 | 0 | 111 | 111 |
| Build or packaging | 0 | 5 | 0 | 67 | 72 |
| Binary | 0 | 0 | 67 | 0 | 67 |
| Vendored | 0 | 0 | 19 | 0 | 19 |
| Asset | 0 | 0 | 4 | 0 | 4 |
| Generated | 0 | 0 | 2 | 0 | 2 |

`inventory-only` is limited to generated, vendored, binary, and static asset
material with explicit reasons. It is not used to avoid difficult source.

## Major guides and flows produced

The ordered entry point is [the study path](docs/00-study-path.md). Available
conceptual guides now cover:

- [architecture and process ownership](docs/01-architecture-overview.md);
- [configuration resolution, publication, launch, readiness, and
  cleanup](docs/02-configuration-and-startup.md);
- [offline Engine API and runtime controls](docs/03-offline-engine.md);
- [frontend language IR, interpreter, concurrency, choice, and
  backend flow](docs/04-frontend-language.md);
- [provider clients and prompt templates](docs/05-provider-clients-and-templates.md);
- [diffusion generate CLI and client/worker output flow](docs/06-diffusion-generate-cli.md);
- [native generation request, scheduler admission, detokenization, response,
  and abort flow](docs/07-native-generate-protocol.md);
- [OpenAI completion/chat preparation and response flow](docs/08-openai-completions.md);
- [embedding, classification, score, rerank, pooler, and tokenizer-only
  paths](docs/09-openai-embeddings-and-scoring.md);
- [OpenAI Responses regular/Harmony state, tools, streaming, and
  replay](docs/10-openai-responses.md);
- [Anthropic request conversion and indexed content-block SSE](docs/11-anthropic-messages.md);
- [Ollama direct native conversion, NDJSON, metadata, and Smart
  Router](docs/12-ollama-api-and-smart-router.md); and
- [native gRPC schema, Rust/Python event-loop bridge, backpressure,
  cancellation, OpenAI pass-through, and controls](docs/13-native-grpc-python-bridge.md).

Each has a companion under [the file reference index](docs/reference/README.md).
Cross-cutting navigation also includes the [dependency
map](docs/90-dependency-map.md), [glossary](docs/99-glossary.md), [coverage
policy and counts](docs/coverage/README.md), and [progress
ledger](PROGRESS.md).

## Native gRPC deliverable from this run

Covered rows:

- `proto/sglang/runtime/v1/sglang.proto`;
- `python/sglang/srt/entrypoints/grpc_bridge.py`; and
- `test/registered/unit/entrypoints/test_grpc_bridge.py`.

Partial rows, limited to their Python-facing boundary:

- `rust/sglang-grpc/src/lib.rs`;
- `rust/sglang-grpc/src/bridge.rs`;
- `rust/sglang-grpc/src/server.rs`; and
- `rust/sglang-grpc/src/utils/request_utils.rs`.

The guide distinguishes five gRPC meanings: native in-process runtime gRPC,
legacy external SMG serving, model-gateway worker gRPC, image-only EPD encoder
gRPC, and the experimental KV indexer. Only the shared native schema and Python
bridge are complete in this pass.

## Validation

Final pre-commit results:

| Check | Result |
| --- | --- |
| Source commit and cleanliness before analysis | Passed: exact pinned SHA and clean checkout. |
| Inventory regeneration | Passed: 8,319 rows. |
| Inventory `--check` | Passed: generator reports the 8,319-path inventory current. |
| Markdown local links and image targets | Passed: 208 targets across 36 Markdown files. |
| Pinned source paths and line ranges | Passed: 1,429 links resolve against the pinned checkout. |
| Covered/partial ledger note targets and anchors | Passed: all 206 resolve. |
| Python AST and named gRPC symbols | Passed: 41 `RuntimeHandle` methods, exact two focused tests, and 25 RPCs. |
| `git diff --check` | Passed before staging; staged whitespace check is repeated before commit. |
| Focused Python test | Did not run: retry stopped at missing `orjson` during package import. |
| Rust crate tests / live Tonic / model server | Not run in this environment. |
| Final source SHA/cleanliness and repository diff review | Passed: exact SHA, clean source, useful study-repository changes only. |
| Push to public `origin/main` | Pending. |

The first test attempt used `python -m unittest` with a non-package path and
failed to locate `test.registered`. The direct-file retry was the valid
invocation, but source-package import failed at missing `orjson` before test
discovery. No result is represented as a passing runtime test.

## Broken or unresolved items

The final validator found no broken navigation, note anchors, source paths, or
line ranges. Known *source/test gaps*, rather than documentation-link failures,
include:

- native gRPC has no HTTP API-key/admin-key middleware and exposes control RPCs;
- unary embedding lacks explicit generator closure/backpressure status handling;
- OpenAI SSE deframing has no partial-line carry buffer;
- invalid UTF-8 takes the unexpected-server-error path;
- structured control failure bodies are lost when the Rust callback receives
  an `error` argument;
- current Rust calls do not wire the Python request-shim disconnect hook;
- callback exceptions can defer Rust-channel cleanup until response timeout;
- the focused Python test covers only multi-choice terminal ordering; and
- no live protobuf/Tonic/model parity test was run.

## Precise remaining gaps

Immediate continuation:

1. Complete the native Rust gRPC crate: build/package integration, tokenizer,
   every Tonic handler, request/response utilities, embedded Rust tests, Python
   extension tests, and live compatibility/client coverage.
2. Cover `entrypoints/grpc_server.py` and its external SMG contract separately
   from the locally managed sidecar process.
3. Give the model gateway's gRPC regular/PD/Harmony pipelines their own router
   guide rather than attributing them to `RuntimeHandle`.
4. Cover the EPD encoder gRPC service with its image-only input, transfer
   backends, health/reflection, worker lifecycle, and disaggregation tests.
5. Resume Phase 3 parser and session subunits.

Broader completion gaps remain the scheduler/queues and KV caches; model
loading/execution, attention, quantization, kernels, and model families;
parallel/disaggregated/speculative/platform paths; SRT multimodal and most
diffusion internals; Rust workspaces, gateway, and experimental router; and
tests, benchmarks, examples, docs, build/package, CI, containers, deployment,
release, security, observability, and operations.

## Completion-rule audit

| Rule | Assessment |
| --- | --- |
| Every tracked path represented | **Met.** 8,319 of 8,319 paths are in the inventory. |
| Every path has final coverage or justified no-detail reason | **Not met.** 8,021 are pending and 41 partial. |
| Every meaningful subsystem has a conceptual guide | **Not met.** Major runtime, model, distributed, native, routing, and operations subsystems remain. |
| Important cross-module flows traced | **Partially met.** Public Python surfaces are strong; deep scheduler/model/distributed/gateway flows remain. |
| Navigation and terminology audited | **Partially met.** Current material is indexed; final whole-project audit cannot pass while coverage remains open. |
| Final audit finds no unexplained areas | **Not met.** Remaining gaps are explicit and substantial. |

The honest project state is an exhaustive inventory plus a high-quality first
slice of conceptual/file coverage, not a complete source study. Do not use the
word “complete” for overall coverage until the pending/partial ledger and final
subsystem audit are resolved.
