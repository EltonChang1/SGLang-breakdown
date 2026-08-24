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
- Current statuses: 137 covered, 35 partial, 92 inventory-only, 8,055 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added [Embeddings, Classification, Scoring, Reranking, and
  Tokenization](docs/09-openai-embeddings-and-scoring.md) and its [file
  reference](docs/reference/openai-embeddings-and-scoring.md). They trace six
  public API families from FastAPI schemas through template/token/media
  preparation, accelerator or tokenizer-only execution, and response shaping.
- Explained why the shared internal embedding transport can mean dense
  vectors, class logits, reward/cross-encoder scores, or pooled states. Covered
  capability resolution, Matryoshka dimension checks, embedding overrides,
  cross-encoder pair handling, pooling, result correlation, and little-endian
  base64 serialization.
- Distinguished CausalLM score semantics from classification-head semantics,
  including selected-token probability normalization, zero-decode requests,
  multi-item scoring delimiter invariants, and optional pooled-state return.
- Documented rerank's cross-encoder, text-decoder, and VL-decoder backends,
  including heuristic backend selection, media fallback, yes/no score
  extraction, the serial VL loop, stable source indices, document omission,
  and bounded `top_n` selection.
- Covered tokenize/detokenize's tokenizer-process-only path and chat-serving
  reuse. Recorded source-visible documentation drift around classify fallback
  labels, rerank defaults, score terminology and supported model families, and
  the nominally tokenizer-free example. Also recorded untested contract gaps
  for nested negative embedding IDs, single-input HTTP embedding overrides,
  and returned multimodal rerank documents.
- Completed 28 source, documentation, example, and focused-test ledger rows and
  added four explicit partial boundaries for model configuration, batch-result
  processing, the native API guide, and the broad OpenAI server suite. Updated
  architecture/study navigation, dependency and terminology maps, indexes,
  coverage policy/counts, inventory, and shared-file rows.

## Validation in the latest run

- Confirmed `.source/sglang` remained at the pinned commit with a clean
  worktree.
- Rebuilt and checked the 8,319-row inventory; status totals match this file.
- Checked 133 Markdown local links, all 172 ledger note targets, and 1,108 pinned
  source links, including local anchors, tracked source paths, and source line
  ranges.
- AST-parsed all 37 Python source/test files linked by the new guides and
  structurally checked 14 central capability/adapter/pooler symbols plus all
  eight documented route strings against the pinned source.
- Attempted collection of six CPU-oriented capability, embedding/rerank
  adapter, pooler, override, and request-structure suites with the source
  package on `PYTHONPATH`, but no tests collected because the environment
  lacks `orjson`; `msgspec` is also absent.
- No GPU/model end-to-end suite was attempted because those tests require
  accelerator resources and model downloads; this run changes only study
  Markdown and ledger metadata.

## Next coherent study unit

Continue Phase 3 with the OpenAI Responses API. Trace request normalization,
state and previous-response handling, item/tool/reasoning conversion, streaming
events, usage and error semantics, tests, and user documentation. Then cover
Anthropic, Ollama, gRPC, parser, and session subunits.

## Known gaps

- Phase 1 public surfaces plus native generation and OpenAI completion/chat/
  embedding/classify/score/rerank/tokenize Phase 3 subunits are complete at
  their generic adapter boundaries. Responses and the remaining protocol
  adapters are the next gaps.
- The shared frontend test-program file is partial outside the provider-reached
  functions, and no focused Anthropic, LiteLLM, or Vertex AI backend tests are
  present in the pinned snapshot.
- Model- and backend-specific configuration handlers, declarative override
  providers, and runtime-context derived helpers remain assigned to their
  owning subsystem passes rather than being treated as complete here.
- OpenAI protocol.py and serving_chat.py remain partial: Responses,
  transcription, file/batch schemas plus DeepSeek-3.2/4, Kimi K3, Inkling,
  reasoning-family, and model-specific tool-parser implementations retain
  dedicated passes. The broad chat unit suite remains partial on the same
  boundary.
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
