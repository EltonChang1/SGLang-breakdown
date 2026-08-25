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
- Current statuses: 162 covered, 37 partial, 92 inventory-only, 8,028 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added [Anthropic-Compatible Messages API](docs/11-anthropic-messages.md) and
  its [file reference](docs/reference/anthropic-messages.md). They trace both
  routes through discriminated Anthropic records, ordered message conversion,
  shared OpenAI chat preparation/native execution, full response shaping,
  indexed content-block SSE, errors, usage, and preparation-only token count.
- Explained template-probed inline system placement; base64/URL media;
  structured search and tool-result flattening; deferred tool references;
  user/tool/user ordering; native versus marker-wrapped thinking history; and
  empty assistant-turn preservation.
- Covered sampling and stop inputs, reasoning toggles and effort, custom tool
  schemas and auto/required/named selection, built-in-tool filtering,
  non-stream thinking/text/tool output, adjacent tool block separation,
  last-payload finish chunks, balanced stream failures, and disconnect abort
  ownership.
- Completed all three Anthropic runtime-package rows, the user guide, focused
  unit suite, reusable live test mixin, registered tool-use suite, and manual
  VLM suite. Added a partial boundary for the inline-system template detector
  and refreshed shared HTTP server, OpenAI chat, and broad server-test rows.
- Recorded exact compatibility gaps: metadata and tool-result `is_error` are
  lost; built-in Anthropic tools are accepted but skipped; thinking budget,
  display omission, adaptive mode, task budget, and betas are only partially
  honored; signatures, pings, cache-creation usage, and matched stop sequences
  are not emitted; token count omits `output_config` and does not run
  multimodal media expansion.
- Added [Ollama-Compatible API and Smart
  Router](docs/12-ollama-api-and-smart-router.md) and its [file
  reference](docs/reference/ollama-api-and-smart-router.md). They trace direct
  chat-template-ID and prompt-text conversion into native generation, the
  eight-option sampling map, full responses, NDJSON streams, synthetic model
  metadata, route environment variables, and the separate client utility.
- Covered every dedicated Ollama runtime and documentation file. Explained
  that request-side model names, images, format, thinking, template, suffix,
  context, keep-alive, and raw mode are accepted but do not affect execution,
  and confirmed that the snapshot exposes no Ollama embedding route.
- Recorded the cumulative-stream invariant, incremental-output corruption,
  possible terminal-delta loss, hard-coded finish reasons, absent stream
  metrics/errors, permissive `/api/show`, fixed `/api/tags` metadata, and the
  difference between the default SGLang root and an overridden Ollama root.
- Traced `SmartRouter` classification, prompt truncation and trust boundary,
  force precedence, last-user-message selection, one-shot non-stream fallback,
  no streaming fallback, and the interactive history/error loop.
- Updated architecture/study navigation, the dependency and terminology maps,
  indexes, coverage policy/counts, inventory, and shared-file references.

## Validation in the latest run

- Verified `.source/sglang` is clean and exactly at
  `f464e77d17a3908ad0ea32547b1e8b039bcbd354` before analysis; the final audit
  repeats this check before commit.
- Regenerated the 8,319-row inventory and passed the generator's `--check`;
  status counts are 162 covered, 37 partial, 92 inventory-only, and 8,028
  pending.
- Audited all 32 study Markdown files: 177 local links/images, 1,349 pinned
  source links and line ranges, and all 199 covered/partial ledger note targets
  resolve with no errors.
- AST-parsed all four dedicated Ollama modules plus the shared HTTP server and
  checked 34 central records, classes, methods, functions, routes, and all five
  route environment keys. An isolated import/default assertion pass for the
  protocol records also succeeded.
- Attempted the focused CPU Anthropic unit suite directly. Import stopped at
  missing `orjson` before test discovery, so no test cases ran. The broad,
  tool-use, and manual VLM suites were not run because they launch model
  servers; VLM also downloads external fixtures.
- The snapshot has no dedicated Ollama schema, handler, route, or smart-router
  tests. The current environment also lacks `orjson`, so runtime handler import
  and live Ollama-client/model validation were not available; source, AST,
  protocol-model, link, and ledger checks define this pass's validation floor.
- The inventory check and `git diff --check` passed. No GPU/model server was
  available for live integration validation.

## Next coherent study unit

Continue Phase 3 with Python and native gRPC entry points and their protocol
boundary. Trace bridge/server startup, runtime handoff, streaming, generated
records, cancellation/errors, configuration, tests, and deployment behavior.
Then cover parser and session subunits.

## Known gaps

- Phase 1 public surfaces plus native generation, OpenAI completion/chat/
  embedding/classify/score/rerank/tokenize/Responses, Anthropic Messages, and
  Ollama Phase 3 subunits are complete at their generic adapter boundaries.
  gRPC and the remaining protocol adapters are the next gaps.
- Ollama does not enforce request model selection; prepare message/generate
  images; implement format/thinking/template/suffix/context/keep-alive/raw
  semantics; expose embedding; translate native finish/error/usage details;
  or support incremental native streaming correctly. A terminal native chunk
  can lose text, tags/show metadata are synthetic, and there are no focused
  tests. `SmartRouter` has heuristic prompt classification, synchronous calls,
  one full-response fallback, no stream fallback, and no policy guard against
  replaying sensitive or side-effecting requests to the other endpoint.
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
