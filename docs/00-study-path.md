# Ordered Study Path

This guide follows the order in which SGLang turns a user request into model
work, then works downward into the machinery that makes that path fast. Read
the conceptual guide for a phase before using its file-by-file reference notes.

The source snapshot is fixed at
[`f464e77d17a3908ad0ea32547b1e8b039bcbd354`](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354).
Coverage labels describe this snapshot only.

## Phase 0: orient yourself

1. Read the [architecture overview](01-architecture-overview.md).
2. Keep the [dependency map](90-dependency-map.md) open while reading.
3. Use the [glossary](99-glossary.md) when an acronym first appears.
4. Check the [coverage inventory](coverage/README.md) before assuming a file
   has already received a full pass.

The orientation phase is available now. It distinguishes the Python runtime,
the diffusion runtime, native extensions, routers, tests, and operational
material so similarly named packages are not conflated.

## Phase 1: learn the public surfaces

Study the installed `sglang` package, the frontend language, the offline
`Engine`, and the command-line entry points. The first reference note,
[Serving entry points](reference/entrypoints.md), covers `sglang serve` and its
backend extension contract. The [Offline Engine API](03-offline-engine.md) and
its [file reference](reference/offline-engine.md) now cover the in-process
constructor, sync/async inference surfaces, request handoff, sessions, scoring,
control methods, weight updates, and shutdown. [Frontend Language Execution](04-frontend-language.md)
and its [file reference](reference/frontend-language.md) now trace decorated
functions through sampling IR, interpreter state, single/batch/stream modes,
fork/join, choice scoring, tracing and prefix caching, and the first SRT HTTP
handoff. [Provider Clients and Prompt Templates](05-provider-clients-and-templates.md)
and its [file reference](reference/provider-clients-and-templates.md) compare
OpenAI, Anthropic, LiteLLM, Vertex AI, and Crusoe, then audit every frontend
template record, matcher, provider example, and focused manual test. Finally,
[Diffusion Generate CLI](06-diffusion-generate-cli.md) and its
[file reference](reference/diffusion-generate-cli.md) trace the separate
multimodal-generation surface through model detection, configuration,
`DiffGenerator`, worker launch, request/output expansion, ZMQ routing,
persistence, metrics, controls, and cleanup. Phase 1 is complete at the public
boundary; deeper diffusion pipelines and models remain in Phase 7.

Questions to answer before moving on:

- Which imports perform process-wide setup, and which public objects are lazy?
- When does `sglang serve` choose the LLM runtime, diffusion runtime, or an
  installed third-party backend?
- How does the offline `Engine` differ from the HTTP server without becoming a
  separate inference core?
- Which thread runs user Python, which thread evaluates expressions, and what
  event makes a generated variable safe to read?
- Which sampling fields survive each provider adapter, and which backends
  support choices, media, usage accounting, or API speculation?
- Why can a model-path matcher, a frontend prefix/suffix template, and an SRT
  Jinja template make different decisions for the same model?
- How do `RuntimeEndpoint`, local `Runtime`, and offline `Engine` differ in
  transport, process ownership, and return type?
- Why is the active diffusion symbol `DiffGenerator`, and why is
  `cli.utils.launch_distributed` not the installed command's launch path?
- When does diffusion output persistence happen in the worker instead of the
  offline client, and what crosses ZMQ in each branch?
- How do within-replica model parallelism and data-parallel request routing
  divide responsibility in the diffusion runtime?

## Phase 2: configuration and startup

Study `ServerArgs`, argument groups, config-file merging, runtime-context
publication, platform selection, process/rank construction, ports, readiness,
warmup, and shutdown. Treat resolved configuration as an input to later phases;
otherwise backend-selection code appears to make decisions from raw CLI values
that have already been transformed.

This phase is now available in [Configuration and startup](02-configuration-and-startup.md),
with a companion [file and symbol reference](reference/configuration-startup.md).
Before moving on, be able to distinguish raw, resolved, published, overridden,
configured-parallel, and live-parallel values, and distinguish scheduler/model
readiness from public HTTP readiness after warmup.

## Phase 3: protocols and request preparation

Follow native `/generate`, OpenAI, Anthropic, Ollama, gRPC, and embedding or
scoring requests into their shared request structures. Then cover chat
templates, tokenization, multimodal preprocessing, grammar/tool parsers,
sessions, request state, cancellation, and streaming response contracts.

The first protocol subunit is available in [Native `/generate`
Protocol](07-native-generate-protocol.md), with a companion [file and symbol
reference](reference/native-generate-protocol.md). It traces request shape and
normalization through sampling preparation, tokenizer/media work, scheduler
admission messages, incremental detokenization, correlation, SSE/non-streaming
shaping, disconnect detection, and explicit abort. Read it before the adapters:
they eventually converge on much of this same runtime machinery but add their
own schemas and compatibility behavior.

The next subunit, [OpenAI Completions and Chat
Completions](08-openai-completions.md), and its [file
reference](reference/openai-completions.md), follows both OpenAI-compatible
generation routes through shared error/timing policy, completion prompt
mapping, chat message/template/media preparation, tool and reasoning
constraints, native generation, logprobs, usage, extensions, and JSON/SSE
response shaping.

[Embeddings, Classification, Scoring, Reranking, and
Tokenization](09-openai-embeddings-and-scoring.md), with its [file
reference](reference/openai-embeddings-and-scoring.md), then covers the
non-generation OpenAI-compatible surfaces. It distinguishes dense pooling,
classification heads, CausalLM label scoring, multi-item scoring, three rerank
backends, and tokenizer-only routes; traces multimodal/template/override input
preparation and final embedding transport; and records compatibility drift in
the pinned docs and tests.

[OpenAI Responses API](10-openai-responses.md), with its [file
reference](reference/openai-responses.md), completes the item-oriented OpenAI
generation surface. It follows ordinary and GPT-OSS/Harmony prompt protocols,
previous-response replay, background and in-memory state, structured output,
reasoning and function items, server-executed browser/Python loops, regular and
Harmony SSE state machines, usage/errors, operational trust boundaries, and
focused test gaps.

[Anthropic-Compatible Messages API](11-anthropic-messages.md), with its [file
reference](reference/anthropic-messages.md), then traces the Messages adapter
onto the shared OpenAI chat path. It covers discriminated wire records,
template-dependent system placement, media and reasoning history, custom and
deferred tools, non-streaming output, indexed content-block SSE, usage and
errors, preparation-only token counting, Claude Code documentation, and exact
schema-versus-behavior gaps.

[Ollama-Compatible API and Smart Router](12-ollama-api-and-smart-router.md),
with its [file reference](reference/ollama-api-and-smart-router.md), covers the
smaller direct-to-native adapter and the separate client utility. It traces
chat-template IDs and generate text into `GenerateReqInput`, the eight-option
sampling map, empty initialization response, full and NDJSON output, synthetic
tags/show metadata, import-time route overrides, missing embedding surface,
streaming correctness gaps, and the Smart Router's judge, force, fallback, and
interactive-demo behavior.

[Native gRPC and the Python Runtime
Bridge](13-native-grpc-python-bridge.md), with its [file
reference](reference/native-grpc-python-bridge.md), next separates the native
in-process endpoint from legacy SMG serving, the model gateway, encoder EPD,
and experimental KV-indexer protocols. It completes the shared runtime schema,
Python `RuntimeHandle`, and focused multi-choice test; traces PyO3 into the
tokenizer-manager event loop; and explains channel backpressure, choice-aware
completion, abort ownership, OpenAI SSE deframing, controls, unauthenticated
operations, and exact remaining Rust/integration gaps.

Questions to answer before continuing:

- Why does `n > 1` become multiple independent request IDs rather than one
  scheduler request with multiple choices?
- Where do token deltas become cumulative text in the default streaming mode?
- Which process owns client disconnect detection, scheduler abort matching,
  and detokenization state?
- Why can prompt length pass tokenizer-side validation and fail at scheduler
  admission for multimodal input?
- What guarantees does an HTTP 200 from `/abort_request` provide—and what does
  it not prove?
- Why can a field accepted by CompletionRequest still be behaviorally inert?
- Which component owns chat framing, reasoning separation, tool-call parsing,
  native request execution, and final OpenAI response shaping?
- Why are prompt/cache/multimodal token counts strided by n while completion
  and reasoning counts include every choice?
- Why can the internal `embedding` field mean a dense vector, class logits, or
  one scalar cross-encoder score?
- When does `/v1/score` construct a zero-token generation request instead of
  an embedding request, and what does `apply_softmax=False` mean in each case?
- Which template/model/input signals choose each rerank backend, and which
  fallback discards image and video content?
- Why does chat tokenization reuse chat serving without entering scheduling or
  detokenization?
- Why is `previous_response_id` an in-process replay mechanism rather than a
  scheduler session or durable conversation record?
- Which Responses tool definitions merely validate, which return control to
  the client, and which can execute another model turn inside SGLang?
- Why do regular and Harmony Responses streams have different item, usage,
  error, and logprob guarantees?
- Why does the Anthropic endpoint translate through `OpenAIServingChat` rather
  than create a native generation request directly?
- Which templates preserve an inline system turn, and when must the adapter
  merge it into the leading system prompt?
- How do thinking, text, and consecutive tool calls become balanced indexed
  Anthropic content blocks over an OpenAI chunk stream?
- Which Anthropic fields and built-in tools validate but do not affect local
  execution, usage, or response shaping?
- Why can `/v1/messages/count_tokens` be exact for rendered text yet fail to
  prove the scheduler-visible multimodal token count?
- Why does Ollama chat pre-tokenize to `input_ids` while Ollama generate sends
  `text`, and which richer OpenAI chat behaviors does that direct path bypass?
- Which Ollama request fields validate but never affect execution, and why is
  `/api/embed` an absent route rather than an untraced adapter branch?
- Why does Ollama NDJSON work with default cumulative native output but break
  with incremental output, and when can its terminal record lose final text?
- How can `/api/show` combine an unserved requested name with the active
  checkpoint's context length, and why is `/api/tags` not a model store?
- Why does Smart Router full-response fallback not imply streaming fallback,
  and why must its judge not be treated as a policy enforcement boundary?
- Why does `--grpc-port` start a Rust endpoint beside HTTP while
  `--smg-grpc-mode` selects a different standalone server?
- Which thread/loop owns Tonic I/O, callback backpressure, and tokenizer-manager
  work, and how does a Rust ready edge safely wake Python asyncio?
- Why can a native request with `stream=false` still produce multiple protobuf
  response messages, and which identifiers close an `n > 1` stream?
- Which SSE fields and sentinels disappear in OpenAI gRPC `json_chunk`, and
  what happens if the body iterator splits one `data:` line across chunks?
- Why is the native gRPC listener's bind/network policy the security boundary
  for inference and admin RPCs?

## Phase 4: scheduling and cache ownership

Study the scheduler's queues and batch types before its individual policies.
Then cover continuous batching, prefill versus decode, chunked prefill,
RadixAttention, KV allocation, cache eviction, host/offloaded storage, and
session/prefix reuse. At this phase, trace both a cache hit and a cache miss.

## Phase 5: model execution

Move from `ModelRunner` and model loading into model registries, layers,
attention backends, sampling, logits processing, quantization, CUDA graphs,
Torch compilation, LoRA, and the JIT/AOT kernel layers. Model-specific files
should be grouped by reusable architecture family rather than read as thousands
of unrelated implementations.

## Phase 6: distributed and advanced execution

Cover tensor, pipeline, data, context, and expert parallelism; overlap modes;
prefill/decode and encoder disaggregation; weight transfer; elastic expert
parallelism; speculative decoding; and platform-specific backends. Each topic
needs a process/rank map and an explicit statement of which component owns each
piece of mutable state.

## Phase 7: multimodal and diffusion systems

Study SRT multimodal input processing separately from
`sglang.multimodal_gen`, which is the image/video/diffusion runtime. Then cover
its managers, pipelines, models, distributed execution, caches, post-training,
entry points, apps, and tests.

## Phase 8: routing and native services

Study the Rust extension workspace, the native Rust HTTP/gRPC surfaces, the
`sgl-model-gateway`, and the experimental KV-aware `sgl-router`. Compare their
responsibilities with SRT instead of treating every HTTP-facing component as a
replacement inference engine.

## Phase 9: validation and operations

Finish with tests, benchmarks, examples, documentation, build and packaging,
containers, deployment, CI, release automation, observability, incident
diagnostics, and security boundaries. The final audit must reconcile every row
in the coverage inventory, validate navigation and source links, and search for
important symbols mentioned nowhere else.

## How to use a file reference

A file is `covered` only when its meaningful contents have been explained at
the appropriate level. `partial` means named symbols or one flow through a
large file are explained, but other responsibilities remain. `inventory-only`
is reserved for a file that does not benefit from line-by-line notes and must
include a reason. See the [ledger policy](coverage/README.md) for the exact
definitions.
