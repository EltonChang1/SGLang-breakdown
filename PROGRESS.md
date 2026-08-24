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
- Current statuses: 148 covered, 36 partial, 92 inventory-only, 8,043 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added [OpenAI Responses API](docs/10-openai-responses.md) and its [file
  reference](docs/reference/openai-responses.md). They trace create/retrieve/
  cancel routes through regular item-to-chat normalization or GPT-OSS Harmony
  messages, native generation, ordinary/background/stream delivery, and final
  item and usage shaping.
- Explained previous-response replay and its in-process state boundary,
  background queued/in-progress/final/cancelled transitions, native RID
  matching, cancellation races, unbounded local stores, and the difference
  from scheduler sessions or durable gateway state.
- Covered reasoning, structured output, logprobs, function tools, required-call
  JSON fallback, non-Harmony typed SSE item ordering, Harmony raw-token/channel
  streaming, and server-executed browser/Python continuation turns.
- Completed the conversation-context, Harmony conversion, Responses adapter,
  MCP tool-server, native Exa client/browser/Python tool, and five focused CPU
  test/helper files. Added an explicit partial boundary for the GPT-OSS
  cookbook and refreshed the shared HTTP server, protocol, and broad live
  OpenAI suite rows.
- Recorded schema-versus-behavior gaps for accepted tool/include fields,
  `service_tier`, `max_tool_calls`, and Responses `priority`; regular
  function-call continuation gaps; missing-model and token-budget edges; and
  weaker Harmony streaming IDs, usage, errors, disconnect, and test coverage.
- Updated architecture/study navigation, the dependency and terminology maps,
  indexes, coverage policy/counts, inventory, and shared-file references.

## Validation in the latest run

- Verified `.source/sglang` is clean and exactly at
  `f464e77d17a3908ad0ea32547b1e8b039bcbd354` before and after analysis.
- Regenerated the 8,319-row inventory and passed the generator's `--check`;
  status counts are 148 covered, 36 partial, 92 inventory-only, and 8,043
  pending.
- Audited all 29 study Markdown files: 146 local links/images, 1,211 pinned
  source links and line ranges, and all 184 covered/partial ledger note targets
  resolve with no errors.
- AST-parsed all 14 Python files linked from the new guides and checked 33
  central symbols in seven implementation files plus all three Responses route
  definitions.
- Attempted collection of the four focused CPU Responses/Exa suites through an
  isolated temporary dependency overlay. Collection reached the shared
  quantization imports but stopped at missing `compressed_tensors`; no test
  cases ran. The broad live suite was not run because it launches a model
  server.
- `git diff --check` passed. No GPU/model server, MCP server, Exa service, or
  Python sandbox was available for live integration validation.

## Next coherent study unit

Continue Phase 3 with the Anthropic Messages adapter. Trace schema conversion,
message/media/tool/reasoning mapping onto chat serving, ordinary and streaming
event conversion, errors and usage, documentation, and focused tests. Then
cover Ollama, gRPC, parser, and session subunits.

## Known gaps

- Phase 1 public surfaces plus native generation and OpenAI completion/chat/
  embedding/classify/score/rerank/tokenize/Responses Phase 3 subunits are
  complete at their generic adapter boundaries. Anthropic and the remaining
  protocol adapters are the next gaps.
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
