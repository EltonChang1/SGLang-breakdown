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
- Current statuses: 80 covered, 24 partial, 92 inventory-only, 8,123 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added [Diffusion Generate CLI](docs/06-diffusion-generate-cli.md) and its
  [file reference](docs/reference/diffusion-generate-cli.md). They trace the
  installed and secondary dispatchers through diffusion model detection,
  `ServerArgs`/model-specific `SamplingParams` precedence, `DiffGenerator`,
  local/remote scheduler clients, worker launch, prompt/output expansion,
  persistence, metrics, LoRA/action controls, and cleanup.
- Completed the root generate wrapper/classifier, six-file diffusion CLI
  package, package/server-args façades, `DiffGenerator`, entry-point output
  helpers, launch dispatcher, and sync/async scheduler client. Added explicit
  partial boundaries for CLI-reached sampling configuration, `Req`/`OutputBatch`,
  GPU-worker output/entry symbols, and diffusion `ServerArgs`.
- Explained that the active public symbol is `DiffGenerator`; the installed
  command bypasses the secondary diffusion CLI `main`; worker-side saved-path
  transport is the default; DP routing is separate from within-replica model
  parallelism; and the unreferenced `launch_distributed` torchrun helper targets
  a path absent from the pinned snapshot.
- Covered ten focused test/harness files and partial slices of four
  mixed-purpose tests. Recorded the absence of isolated tests for root
  generate dispatch, config/CLI sampling precedence, malformed Diffusers JSON,
  performance-report selection, all-groups-failed exit status, and the dead
  torchrun helper.
- Marked Phase 1's public-surface study complete while preserving deeper
  diffusion sampling, managers, orchestrator, pipelines, models, caches, and
  kernels for Phase 7. Updated architecture/study navigation, dependency map,
  glossary, reference indexes, coverage policy/counts, inventory, and ledger
  rows.

## Validation in the latest run

- Confirmed `.source/sglang` remained at the pinned commit with a clean worktree.
- Rebuilt and checked the 8,319-row inventory; status totals match this file.
- Checked 204 local/coverage links and 217 pinned source links, including local
  anchors, ledger note targets, tracked source paths, and source line ranges.
- Parsed the 19 reached Python source files and checked the active dispatcher,
  argument-precedence, output-transport, data-parallel control, dead-helper,
  and exact 26-method `DiffGenerator` catalog claims against the pinned tree.
- Attempted the focused diffusion unit tests, but collection stopped before any
  test ran because the available Python environment lacks `orjson`.
- No GPU/model end-to-end suite was attempted because those tests require
  accelerator resources and model downloads; this run changes only study
  Markdown and ledger metadata.

## Next coherent study unit

Begin Phase 3 with SRT's native `/generate` protocol. Trace
`http_server.generate_request` through `GenerateReqInput` normalization,
`srt/sampling/sampling_params.py`, tokenizer/media preparation, request-state
correlation, scheduler messages, detokenizer output, SSE/non-streaming response
shapes, disconnect/cancellation behavior, and focused native-API tests. Keep
OpenAI, Anthropic, Ollama, gRPC, grammar/tool, and session adapters as the next
ordered protocol subunits.

## Known gaps

- Phase 1 public surfaces are complete. Protocol-specific serving adapters and
  their shared request-preparation machinery are the next gap.
- The shared frontend test-program file is partial outside the provider-reached
  functions, and no focused Anthropic, LiteLLM, or Vertex AI backend tests are
  present in the pinned snapshot.
- Model- and backend-specific configuration handlers, declarative override
  providers, and runtime-context derived helpers remain assigned to their
  owning subsystem passes rather than being treated as complete here.
- Request/control schemas and tokenizer/control manager files remain partial
  outside the methods exercised by the offline API; session-controller and
  weight/cache/model-worker internals retain their later subsystem passes.
- Diffusion CLI, launch, client, and output helpers are complete; sampling
  details, request/worker files outside the public slices, managers,
  disaggregation protocols, pipelines, models, caches, and kernels remain for
  Phase 7.
- Scheduler admission/batching, radix/KV caches, model execution, model/layer
  families, kernels, and distributed/advanced SRT modes remain.
- Rust crates, gateway, router, tests, benchmarks, examples, docs, packaging,
  deployment, CI, release, security, and operations need dedicated guides.
- The current architecture trace names only the entry symbols in several large
  runtime files; their ledger status remains partial by design.
