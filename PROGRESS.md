# Coverage Progress

## Source snapshot

- Repository: `EltonChang1/sglang`
- Analyzed commit: `f464e77d17a3908ad0ea32547b1e8b039bcbd354`
- Last completed run: 2026-08-25

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
- Current statuses: 165 covered, 41 partial, 92 inventory-only, 8,021 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added [Native gRPC and the Python Runtime
  Bridge](docs/13-native-grpc-python-bridge.md) and its [file
  reference](docs/reference/native-grpc-python-bridge.md).
- Separated native in-process gRPC, legacy external SMG serving, the Rust model
  gateway worker client/router, image-only EPD encoder gRPC, and the
  experimental KV indexer so their launch modes and schemas are not conflated.
- Completed the 25-RPC shared runtime protobuf and all 816 lines of Python
  `RuntimeHandle`: synchronous PyO3 entry, tokenizer-loop scheduling, native
  generate/embed handoff, choice-aware terminal detection, bounded-channel
  ready/pending/closed behavior, backpressure timeout, abort, information and
  control operations, OpenAI request validation, response serialization, and
  SSE deframing.
- Explained the Rust-facing contract without claiming the crate complete:
  listener/thread/Tokio startup, per-RID channels, one parked send, lost-wakeup
  defense, stream-drop abort guard, exception/status mapping, protobuf-to-SRT
  dictionaries, metadata JSON strings, and unauthenticated admin exposure.
- Completed the focused Python test file and recorded its narrow guarantee:
  every non-streaming choice is emitted and the first finished streaming
  choice does not terminate `n > 1`. Backpressure, cancellation, OpenAI,
  embedding, controls, PyO3, Tonic, and live runtime behavior remain untested.
- Recorded source-visible gaps: unary embedding does not explicitly close its
  generator or honor callback status; SSE parsing has no partial-line carry;
  invalid UTF-8 is a server error instead of BadRequest; structured unary
  control errors are discarded by Rust error precedence; current Rust callers
  do not use the request-shim disconnect hook; callback exceptions can defer
  cleanup to the response timeout; and bind/network policy is the security
  boundary.
- Refreshed the architecture overview, ordered study path, README, reference
  index, dependency map, glossary, coverage policy/counts, inventory, progress
  ledger, and required [final report](FINAL-REPORT.md).

## Validation in the latest run

- Verified `.source/sglang` was clean and exactly at
  `f464e77d17a3908ad0ea32547b1e8b039bcbd354` before analysis; the final audit
  repeats this check before commit.
- Regenerated the 8,319-row inventory. Status counts are 165 covered, 41
  partial, 92 inventory-only, and 8,021 pending.
- AST/symbol, Markdown link/range, ledger-note, inventory `--check`, whitespace,
  and final source/repository-state results are recorded in `FINAL-REPORT.md`.
- The first test invocation used a non-package unittest module name and failed
  before import. Retrying the file directly reached the source package but
  stopped at missing `orjson`; neither focused test ran. No Rust build, Tonic
  client, live model server, or GPU test was available.

## Next coherent study unit

Continue Phase 3 with the complete native Rust gRPC crate: build/package
integration, tokenizer fallback, all Tonic RPC handlers, response and request
utilities, embedded Rust tests, Python extension tests, and a live client
matrix. Then treat the legacy SMG server, model gateway gRPC router, and EPD
encoder transport as separate guides before moving to parser and session
subunits.

## Known gaps

- Phase 1 public surfaces plus native generation, OpenAI completion/chat/
  embedding/classify/score/rerank/tokenize/Responses, Anthropic Messages, and
  Ollama and Python native-gRPC Phase 3 subunits are complete at their recorded
  adapter boundaries. The native Rust crate, legacy SMG, model gateway, EPD
  encoder, and remaining protocol adapters are the next gaps.
- Native gRPC's Rust crate remains partial outside its Python-facing slices.
  Legacy `grpc_server.py`, managed sidecar, model-gateway gRPC tree, encoder
  gRPC, experimental KV-indexer protocol, build/packaging, and Rust/Python/live
  integration tests remain pending. The current listener is unauthenticated;
  Python embedding cleanup/status, fragmented SSE, invalid UTF-8, structured
  control errors, disconnect-hook plumbing, and callback-failure cleanup need
  regression tests or fixes.
- Ollama does not enforce request model selection; prepare message/generate
  images; implement format/thinking/template/suffix/context/keep-alive/raw
  semantics; expose embedding; translate native finish/error/usage details;
  or support incremental native streaming correctly. A terminal native chunk
  can lose text, explicit stream-abort cleanup is absent, tags/show metadata
  are synthetic, and there are no focused tests. `SmartRouter` has heuristic
  prompt classification, synchronous calls, one full-response fallback, no
  stream fallback, possible configured-versus-served model misattribution, and
  no policy guard against replaying sensitive or side-effecting requests to
  the other endpoint.
- The shared frontend test-program file is partial outside the provider-reached
  functions, and no focused Anthropic, LiteLLM, or Vertex AI backend tests are
  present in the pinned snapshot.
- Model- and backend-specific configuration handlers, declarative override
  providers, and runtime-context derived helpers remain assigned to their
  owning subsystem passes rather than being treated as complete here.
- OpenAI protocol.py and serving_chat.py remain partial: transcription and
  file/batch schemas plus DeepSeek-3.2/4, Kimi K3, Inkling, reasoning-family,
  and model-specific tool-parser implementations retain dedicated passes. The
  broad chat unit suite remains partial on the same boundary.
- Anthropic Messages does not execute dated web-search/computer/bash/editor
  built-ins; preserve metadata or tool-result `is_error`; enforce thinking or
  task budgets; suppress omitted thinking; implement adaptive throttling or
  betas; or emit thinking signatures, pings, cache-creation usage, matched stop
  sequences, or effort-aware/scheduler-expanded multimodal token counts.
  Focused HTTP error, count-token, disconnect, and actual URL-image tests are
  also absent.
- Responses stores are process-local and unbounded. Accepted extended tools,
  include values, `service_tier`, `max_tool_calls`, and `priority` do not all
  have execution behavior. Regular previous-response replay omits non-message
  output items; missing-model and tiny/near-context output budgets are
  untested.
- Harmony streaming retains source-visible gaps around unique item identity,
  usage counters, typed failures, disconnects, and multiple built-in turns.
  MCP schema/session failures and the optional Python tool lack focused tests;
  the live Responses usage assertion is non-binding.
- No focused `/v1/classify` test exists in the pinned snapshot; classification
  behavior is currently supported by shared embedding/pooling coverage and
  source inspection rather than a route-specific regression suite.
- No focused integration case covers a single-input HTTP embedding override or
  a multimodal rerank response with `return_documents=true`; nested embedding
  token batches also bypass the flat-input negative-ID check.
- Request/control schemas and tokenizer/control manager files remain partial
  outside the native/offline paths now explained; parser caches, observability,
  multi-tokenizer, elastic, session-controller, weight/cache, and model-worker
  internals retain their later subsystem passes.
- Diffusion CLI, launch, client, and output helpers are complete; sampling
  details, request/worker files outside the public slices, managers,
  disaggregation protocols, pipelines, models, caches, and kernels remain for
  Phase 7.
- Native scheduler admission and output boundaries are explained; batching
  policy, radix/KV caches, model execution, model/layer families, kernels, and
  distributed/advanced SRT modes remain.
- Rust crates, gateway, router, tests, benchmarks, examples, docs, packaging,
  deployment, CI, release, security, and operations need dedicated guides.
- The current architecture trace names only the entry symbols in several large
  runtime files; their ledger status remains partial by design.
