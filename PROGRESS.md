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
- Current statuses: 109 covered, 31 partial, 92 inventory-only, 8,087 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added [OpenAI Completions and Chat
  Completions](docs/08-openai-completions.md) and its [file
  reference](docs/reference/openai-completions.md). They trace both FastAPI
  routes through shared validation/error policy, request mapping or message
  rendering, native generation, reasoning/tool parsing, usage/logprobs,
  extensions, and JSON/SSE shaping.
- Completed the empty OpenAI package marker, shared serving base, text
  completion adapter, chat-encoding dispatcher, usage processor, response
  utilities, and compact chat SSE builder. Added explicit partial boundaries
  for the shared protocol schema and the model-specific branches of the large
  chat adapter.
- Documented completion prompt and response cardinality, echo, structured
  output constraints, chat schema normalization, Jinja/conversation/custom
  encoder selection, media extraction, assistant prefill, tool constraints,
  reasoning ownership, semantic stream chunk order, and extension placement.
- Recorded compatibility gaps that are visible in source: accepted completion
  fields such as `best_of`, `suffix`, `user`, and `session_params` are not
  consumed; body `custom_labels` is ignored in favor of the configured header;
  and the upstream tutorial's per-choice `sgl_ext` claim conflicts with the
  response-level `sglext` implementation.
- Covered the three directly relevant user documentation/example files, the
  complete completion unit suite, the LoRA parsing suite, two validation
  suites, and the remaining OpenAI slice of request-length validation. Kept
  broad protocol and chat unit files partial where later API or model-format
  assertions remain.
- Updated architecture/study navigation, dependency and terminology maps,
  reference indexes, coverage policy/counts, inventory, and ledger rows for
  the second Phase 3 protocol subunit.

## Validation in the latest run

- Confirmed `.source/sglang` remained at the pinned commit with a clean worktree.
- Rebuilt and checked the 8,319-row inventory; status totals match this file.
- Checked 121 Markdown local links, all 140 ledger note targets, and 917 pinned
  source links, including local anchors, tracked source paths, and source line
  ranges.
- Parsed 15 OpenAI-guide Python files and structurally checked the complete
  base, completion, encoding-dispatch, usage, utility, and SSE catalogs;
  request routes; accepted-but-inert versus forwarded fields; tool-constraint
  and usage-stride claims; documentation drift; and focused test counts.
- Attempted collection of the protocol, completion, chat, and LoRA unit suites
  with the source package on `PYTHONPATH`, but no tests collected because the
  environment lacks `orjson`; `msgspec` is also absent.
- No GPU/model end-to-end suite was attempted because those tests require
  accelerator resources and model downloads; this run changes only study
  Markdown and ledger metadata.

## Next coherent study unit

Continue Phase 3 with OpenAI embeddings, classification, score, rerank, and
tokenize/detokenize adapters. Trace their schemas, template/token/media
preparation, `EmbeddingReqInput` or generation fallback, pooled-result
shaping, error/status behavior, tests, and user documentation. Then cover the
Responses API before Anthropic, Ollama, gRPC, parser, and session subunits.

## Known gaps

- Phase 1 public surfaces plus native generation and OpenAI completion/chat
  Phase 3 subunits are complete at their generic adapter boundaries. Embedding,
  Responses, and the remaining protocol adapters are the next gaps.
- The shared frontend test-program file is partial outside the provider-reached
  functions, and no focused Anthropic, LiteLLM, or Vertex AI backend tests are
  present in the pinned snapshot.
- Model- and backend-specific configuration handlers, declarative override
  providers, and runtime-context derived helpers remain assigned to their
  owning subsystem passes rather than being treated as complete here.
- OpenAI protocol.py and serving_chat.py remain partial: non-completion schemas
  plus DeepSeek-3.2/4, Kimi K3, Inkling, reasoning-family, and model-specific
  tool-parser implementations retain dedicated passes. The broad chat unit
  suite remains partial on the same boundary.
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
