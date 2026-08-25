# Dependency Map

This is the initial package-level map for the pinned snapshot. Arrows mean
"calls, embeds, or builds on" rather than a promise that every import points in
only one direction. Symbol-level dependency maps will be added with each
subsystem guide.

## Serving layers

| Layer | Depends on | Supplies |
| --- | --- | --- |
| Frontend language and clients (`sglang.lang`) | IR, interpreter state, chat templates, choice policies, HTTP/provider adapters | User-facing model programs and backend requests |
| CLI (`sglang.cli`) | Packaging entry points, model metadata, plugin/serve-backend registries | A selected LLM, diffusion, or external serving launch |
| Protocol entry points (`srt.entrypoints`) | FastAPI/ASGI, protocol schemas, templates, `TokenizerManager` | Native, OpenAI, Anthropic, Ollama, gRPC, and management surfaces |
| Tokenizer side (`srt.managers.tokenizer_manager`) | Tokenizers, parsers, multimodal processors, request schemas, ZMQ | Validated tokenized requests and correlated client responses |
| Scheduler (`srt.managers.scheduler`) | Runtime context, queues/batches, cache managers, model execution, distributed groups | Ordered accelerator work and token/embedding results |
| Model executor and models | Model loaders/configs, layers, attention/sampling/quantization backends | Forward-pass outputs for scheduled batches |
| Kernel layers | Torch/custom-op interfaces, JIT/AOT/native or external kernel packages | Device operations used by layers and caches |
| Detokenizer | Tokenizer, output message schemas, ZMQ | Incremental/final text returned to the tokenizer side |

The default startup path linking these layers is source-visible in
[`launch_server`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2767-L2828)
and [`Engine._launch_subprocesses`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1022-L1237).

## Frontend language dependency boundary

The frontend is an imperative client orchestrator. Its main dependencies form
this order:

```text
public factories -> SglFunction + expression IR -> ProgramState
                 -> StreamExecutor -> BaseBackend implementation
                 -> provider API or RuntimeEndpoint -> SRT HTTP /generate
```

| Frontend component | Depends on | Supplies |
| --- | --- | --- |
| `api.py` | IR factories and global config | decorators, generation/selection/role/media helpers |
| `ir.py` | sampling schema, choice-policy protocol | decorated wrapper and typed expressions |
| `interpreter.py` | IR, templates through backend, media encoders | ordered prompt/message/variable state and backend calls |
| `tracer.py` | IR plus interpreter state interface | symbolic dependencies and leading static prefix |
| `choices.py` | aligned conditional/unconditional logprobs | selected string and diagnostic metadata |
| `BaseBackend` | chat template | minimum generation/stream/selection/optimization boundary |
| `RuntimeEndpoint` | SRT HTTP endpoints | concrete frontend backend for a running SGLang server |
| `Runtime` | resolved `ServerArgs`, spawned HTTP server, endpoint | owning local convenience wrapper for frontend programs |
| Provider clients | provider SDK, common sampling conversions, executor text/messages/media | synchronous provider requests and streamed deltas |
| Frontend chat-template registry | ordered model-name matchers and prefix/suffix records | default system text, serialized role markers, stops, and media tokens |

The Python program thread enqueues expressions; the executor worker mutates
prompt state and calls the backend. Named variable events join those lanes when
user Python reads a model result. Batch execution adds a thread pool outside
that per-program pair. See [Frontend Language Execution](04-frontend-language.md)
for the ordered single, batch, stream, choice, fork, and trace flows.

Provider adapters do not share one feature-complete request schema. OpenAI can
choose chat or completion and uniquely supplies frontend selection,
speculation, and usage counters; Anthropic and LiteLLM always send messages;
Vertex AI converts messages and media; Crusoe inherits the OpenAI path. Every
conversion drops common sampling fields. Model-path template matching happens
before these calls and is first-match-wins. See
[Provider Clients and Prompt Templates](05-provider-clients-and-templates.md)
for the capability and data-loss matrices.

`RuntimeEndpoint` is where this frontend first meets SRT: it serializes the
accumulated prompt and sampling record to `/generate`. The offline `Engine`
instead calls tokenizer-manager coroutines directly and is not a frontend
backend
([runtime endpoint generation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L159-L246),
[offline generation adapter](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L362-L573)).

## Diffusion offline dependency boundary

The diffusion `generate` surface is a separate synchronous client over the
`multimodal_gen` scheduler, not an SRT offline-engine mode:

```text
sglang CLI -> diffusion classification -> ServerArgs + sampling kwargs
           -> DiffGenerator -> launch_server(no HTTP) -> GPU workers
           -> SamplingParams -> expanded Req group -> SchedulerClient/ZMQ
           -> output-rank persistence or returned payload -> GenerationResult
```

| Component | Depends on | Supplies |
| --- | --- | --- |
| root `cli.generate` | model path extraction, overlay/native/Diffusers detection | selected diffusion-only command |
| diffusion CLI `generate_cmd` | server and sampling parsers, config loader, model registry | resolved launch record plus request kwargs |
| `DiffGenerator` | launch/warmup, request helpers, synchronous scheduler client | single/list/none results and control methods |
| `runtime.launch_server` | worker process entry, rank/node configuration, readiness pipes | local worker handles or a blocking server/role lifecycle |
| `SchedulerClient` | DP endpoints, per-call ZMQ sockets, request/control types | routed ordinary response or all-replica control response |
| `SamplingParams` + `Req` | model defaults, explicit user fields, pipeline validation | one validated request per prompt/output |
| output-rank worker | pipeline output, request output settings, persistence helpers | saved paths with tensor/audio payload removed by default |
| output helpers | Torch/NumPy, Pillow, imageio/FFmpeg, optional postprocessors | frames, images, video/audio, action JSON, and paths |

Within-replica model/tensor/sequence parallelism belongs to worker execution;
DP routing chooses an ingress replica above it. Control requests fan out to all
DP replicas because weights, LoRA, memory, and shutdown state must agree. See
[Diffusion Generate CLI](06-diffusion-generate-cli.md) for the ordered trace.

## Offline Engine dependency boundary

The offline API removes the network protocol adapter but preserves the shared
runtime below it. Its method groups have distinct immediate dependencies:

| Public operation | Immediate dependency | Supplies |
| --- | --- | --- |
| `generate` / `async_generate` | `GenerateReqInput`, tokenizer-manager request state, stored/current asyncio loop | One or batched result records, optionally streamed |
| `encode` / `rerank` | `EmbeddingReqInput`, tokenizer/media preprocessing | Embeddings or cross-encoder pooled outputs |
| `score` / `async_score` | engine score mixin, tokenizer score mixin, generation or embedding request | `ScoreResult` with label/class scores |
| sessions | open/close schemas, tokenizer control mixin, scheduler session controller | Multi-turn context identity and lifetime |
| weight/LoRA controls | typed schemas, model-update/LoRA locks, rank communicators | Merged mutation results and live model metadata |
| cache/memory/profile controls | tokenizer control mixin and scheduler fan-out | Runtime state transitions and typed status |
| `collective_rpc` | root-only ZMQ DEALER socket and scheduler RPC dispatcher | Blocking all-rank method execution |
| shutdown | watchdog, RPC socket, daemon/process tree, tokenizer transports | Released process and accelerator ownership |

Request data flows down through typed request objects; results flow up through
request-ID-correlated tokenizer state. Model mutations take the writer side of
the same lock whose reader side protects preprocessing/dispatch. Direct
collective RPC is the exception: it bypasses tokenizer-manager communicators
and is therefore a sharper root-only interface. See
[Offline Engine API](03-offline-engine.md) for the ordered traces and failure
boundaries.

## Native and external boundaries

- The Python build reads the [`rust` Cargo workspace](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/Cargo.toml#L1-L31)
  and builds crates that declare a Python module. Native gRPC can then bridge
  back into live tokenizer/runtime state.
- `python/sglang/kernels` wraps SGLang-owned compiled/JIT operations, while the
  Python dependency manifest also brings in specialized packages such as
  FlashInfer, SGL Kernel, DeepGEMM, and hardware-specific backends
  ([base dependencies](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/pyproject.toml#L18-L100)).
- `sgl-model-gateway` and `experimental/sgl-router` sit in front of workers.
  They depend on HTTP/gRPC, tokenization, discovery, and routing state, but they
  do not replace scheduler-owned model execution.
- `sglang.multimodal_gen` has its own runtime managers, pipelines, models,
  distributed execution, and optional dependency group. Its reuse of shared
  package utilities does not make it a mode inside the SRT scheduler.

## Native generate dependency boundary

The native protocol crosses process-ownership boundaries and three typed
message changes before client-visible text returns:

```text
GenerateReqInput -> TokenizerManager -> TokenizedGenerateReqInput
                 -> Scheduler/Req -> BatchTokenIDOutput
                 -> DetokenizerManager -> BatchStrOutput
                 -> ReqState -> JSON or SSE
```

| Boundary | Depends on | Supplies |
| --- | --- | --- |
| HTTP handler | FastAPI body conversion, trusted request headers | native request object and JSON/SSE response policy |
| `GenerateReqInput.normalize_batch_and_arguments` | prompt/media cardinality, sampling dictionaries, IDs | normalized single/batch objects with request IDs and cardinality |
| tokenizer preparation | tokenizer or supplied IDs/embeddings, media processor, server sampling defaults | verified `SamplingParams` and tokenized transport request |
| scheduler admission | mutable `Req`, grammar manager, session/cache state, model limits | queued execution work or correlated error output |
| scheduler output streamer | request finish state, stream interval, unsent offsets | token/logprob/custom-data suffix batches |
| detokenizer | tokenizer, bounded decode state, stop trimming | printable text deltas preserving request IDs |
| tokenizer result loop | `ReqState`, request ID, output-mode configuration | cumulative or incremental client result records |

Abort messages travel tokenizer-to-scheduler and use request-ID prefix
matching; successful dispatch is not an acknowledgement that active work was
found or stopped. Parallel sampling creates fresh choice IDs above the
scheduler, which makes its cancellation relationship distinct from ordinary
`n == 1` requests. See [Native `/generate`
Protocol](07-native-generate-protocol.md) for the full trace.

## OpenAI completion dependency boundary

The completion adapters wrap the native path with schema and response
compatibility:

```text
CompletionRequest -> OpenAIServingCompletion -> GenerateReqInput
ChatCompletionRequest -> message/template/tool preparation -> GenerateReqInput
GenerateReqInput -> shared native runtime -> result records
result records -> usage/logprob/reasoning/tool adapters -> OpenAI JSON or SSE
```

| Component | Depends on | Supplies |
| --- | --- | --- |
| FastAPI routes | Pydantic protocol records, JSON-content dependency, app-state handlers | typed completion/chat ingress |
| `OpenAIServingBase` | raw Request, TokenizerManager, common error models | fixed validation/conversion/stream/error lifecycle |
| completion adapter | prompt shape, completion template, sampling/format request | direct native generation request and text-completion choices |
| chat message preparation | TemplateManager, tokenizer/Jinja or custom encoder, media formatter, tool schemas | prompt text/IDs, media, stops, grammar constraint, reasoning bit |
| chat response preparation | reasoning and function-call parsers, native result metadata | content/reasoning/tool choices and semantic SSE deltas |
| `UsageProcessor` | prompt-major flattened results and n | input counts once per prompt; output counts across choices |
| OpenAI utilities | native logprob/extension/hidden-state records | wire-compatible optional response fields |

Parser ownership is intentionally layered: rendering frames model input;
reasoning parsing separates hidden and visible channels; function-call parsing
extracts tools; the native runtime only executes the resulting generation
request. See [OpenAI Completions and Chat
Completions](08-openai-completions.md) for the complete flow.

## Anthropic Messages dependency boundary

The Anthropic adapter is stacked on the chat adapter rather than beside the
native runtime:

```text
Anthropic request -> content/system/tool/reasoning conversion
                  -> ChatCompletionRequest -> OpenAIServingChat
                  -> GenerateReqInput -> shared native runtime
OpenAI full response/chunks -> Anthropic blocks -> JSON or Anthropic SSE
```

| Component | Depends on | Supplies |
| --- | --- | --- |
| Anthropic protocol records | Pydantic discriminators and SDK-compatible field shapes | typed messages, content/tool/thinking blocks, responses, and stream events |
| request converter | active chat template, OpenAI chat records, reasoning-history helpers | ordered chat messages, sampling, custom tools, reasoning intent |
| inline-system probe | sandboxed Jinja render and tokenizer chat template | cached merge-versus-preserve decision for system turns |
| `OpenAIServingChat` | templates/encoders, media formatter, reasoning and tool parsers, tokenizer manager | native request plus OpenAI full or streamed semantic output |
| full response adapter | OpenAI choice, reasoning, parsed tool calls, usage | Anthropic thinking/text/tool blocks, stop reason, partitioned usage |
| Anthropic stream state machine | OpenAI SSE chunks and continuous usage | balanced indexed thinking/tool/text block events and terminal message events |
| token-count route | request converter and chat `_process_messages` | rendered-token length without scheduler or model execution |

Custom function tools remain client-executed protocol. Anthropic built-in tool
families are validated then skipped, so they do not reach either the Responses
server-tool loop or an Anthropic-specific executor. The adapter accepts more
fields than it implements and does not populate signatures, pings,
cache-creation usage, or matched stop sequences. See
[Anthropic-Compatible Messages API](11-anthropic-messages.md) for the ordered
flow and failure boundaries.

## Ollama API and Smart Router dependency boundary

The Ollama server adapter bypasses the OpenAI semantic chat layer and reaches
the native runtime directly:

```text
chat messages -> tokenizer chat template -> input IDs --\
                                                      +-> GenerateReqInput
generate prompt -> optional plain system prefix -> text-/        |
                                                               v
                                      shared native runtime -> result dict
                                                               |
                                                     JSON or NDJSON

SmartRouter -> local judge -> local Ollama or remote SGLang Ollama endpoint
```

| Component | Depends on | Supplies |
| --- | --- | --- |
| Ollama protocol records | Pydantic and permissive option dictionaries | chat/generate/tags/show request and response shapes, but no embed/tool/error records |
| route block | import-time environment variables and FastAPI app state | optional Ollama root plus configurable chat/generate/tags/show ingress |
| chat converter | active tokenizer default chat template and text-only role/content messages | prompt IDs and one native generation request |
| generate converter | prompt, optional literal system prefix, mapped options | text and one native generation request, or scheduler-free empty response |
| NDJSON shaper | default cumulative native text and finish metadata | newline-framed deltas plus empty terminal record |
| tags/show helpers | served name, request label, active context length | synthetic discovery/detail placeholders |
| Smart Router | synchronous Ollama clients and model judge output | chosen local/remote call; one full-response fallback but no stream fallback |

Only eight sampling options cross the boundary. Format, thinking, images,
template, suffix, context, lifetime, raw mode, and request-side model selection
do not. The stream shaper assumes cumulative output, discards terminal text,
and has no Ollama error/cancellation layer. The adjacent Smart Router reports
configured labels even though remote SGLang executes its one loaded model. See
[Ollama-Compatible API and Smart
Router](12-ollama-api-and-smart-router.md) for the full flow and test gaps.

## Native gRPC Python bridge dependency boundary

Native gRPC adds a Rust transport beside HTTP while preserving Python SRT
runtime ownership:

```text
runtime protobuf -> Tonic handler -> Rust request map -> PyBridge channel
                 -> synchronous RuntimeHandle call
                 -> TokenizerManager asyncio loop -> shared SRT runtime
native result dict -> PyO3 callback -> bounded Rust channel -> protobuf stream
```

| Component | Depends on | Supplies |
| --- | --- | --- |
| runtime protobuf | proto3 optional fields and oneof grammar constraints | 25 typed native, OpenAI JSON, and admin RPC contracts |
| Rust/Tonic server | compiled protobuf, Tokio, optional Rust tokenizer | listener, per-RPC validation, response timeout, stream-drop abort, typed wire output |
| `PyBridge` | PyO3 `RuntimeHandle`, bounded per-RID channels | short synchronous submissions, callbacks, ready edges, terminal errors |
| `RuntimeHandle` | TokenizerManager event loop, template manager, OpenAI adapters | native request construction, async scheduling, result/control callbacks, JSON/SSE conversion |
| typed native path | Rust protobuf-to-dict mapper and ordinary SRT request records | text/token generation, embedding/classification, routing/tracing/session/disaggregation controls |
| OpenAI pass-through | raw JSON bytes and existing Python serving classes | validated full JSON or SSE-deframed payload chunks |
| control path | tokenizer-manager local state and communicators | model/server information, health, cache/load/pause/profile/weight operations |

`Ready` permits the producer to continue; `Pending` parks one Rust send and
requires Python to wait for a cross-thread ready edge; `Closed` stops
production. Rust owns response-stream drop cancellation and Python forwards it
to the normal tokenizer-manager abort path. The native listener does not pass
through HTTP authentication, so network reachability also exposes control
RPCs. Legacy SMG serving, model-gateway worker gRPC, EPD encoder gRPC, and the
experimental KV indexer use distinct owners or schemas. See [Native gRPC and
the Python Runtime Bridge](13-native-grpc-python-bridge.md).

## OpenAI Responses dependency boundary

Responses adds item normalization, local state, and two output protocols above
the ordinary native generation path:

```text
ResponsesRequest -> regular item-to-chat conversion -> chat preparation
                 \-> GPT-OSS Harmony messages/IDs -> Harmony context
both -> GenerateReqInput -> shared native runtime -> context/output parsers
     -> JSON, typed SSE, or background response store
Harmony browser/python recipient -> tool session -> rerender -> another turn
```

| Component | Depends on | Supplies |
| --- | --- | --- |
| request/response protocol | OpenAI SDK item types, shared usage and grammar helpers | normalized request, native sampling, item-shaped response and usage serialization |
| regular request branch | Responses item conversion, chat message/template/media preparation | prompt IDs/text, media arrays, stops, reasoning and tool grammar |
| Harmony request branch | `openai_harmony`, model type, tool namespace descriptions | role/channel/recipient transcript and rendered token IDs |
| conversation contexts | native result chunks, Harmony parser, optional tool sessions | accumulated messages, finish/usage state, rerendered continuation prompt |
| state store | response ID, normalized messages, asyncio background task | local continuation, retrieval, status mutation, cancellation lookup |
| regular stream state machine | decoded deltas, reasoning/function parsers, output mode | ordered item added/delta/done events and final snapshot |
| Harmony stream state machine | output token IDs and Harmony parser state | analysis/final/built-in tool event families with weaker usage/error guarantees |
| native/MCP tool layer | Exa or GPT-OSS tool object, external MCP SSE session | browser/Python tool message and another generation turn |

Function tools are prompt/output protocol: the client executes them. Harmony
browser and Python tools are server execution: their result re-enters the model
loop. Accepted extended tools without either branch are validation-only. The
local stores have no TTL, persistence, or cross-worker coordination. See
[OpenAI Responses API](10-openai-responses.md) for the ordered flow and
operational boundaries.

## Embedding and scoring dependency boundary

The non-generation adapters share transport but not result semantics:

```text
embedding/classify/cross-encoder -> EmbeddingReqInput -> prefill + pool/head
CausalLM score/text rerank       -> GenerateReqInput  -> selected logprobs
VL rerank                         -> GenerateReqInput  -> one generated token
tokenize/detokenize               -> tokenizer only   -> no scheduler request
```

| Component | Depends on | Supplies |
| --- | --- | --- |
| embedding capability spec | checkpoint architectures, explicit user intent, EmbeddingGemma predicate | task/execution/pooling/cache/graph contract and `/model_info` plan |
| embedding adapter | OpenAI input union, template manager, tokenizer Jinja, media arrays, LoRA/routing/override controls | one or batched `EmbeddingReqInput` plus float/base64 vectors |
| classification adapter | task-head output and config `id2label`/`num_labels` | softmax probabilities and a selected label |
| score mixin | query/item composition, model generation mode, optional MIS and overrides | zero-decode selected-token probabilities or task-head score vectors |
| rerank adapter | template/model/input backend detection | cross-encoder, text-decoder, or VL-decoder relevance records |
| tokenizer manager | tokenizer/media processor, dimension/length/override validation | `TokenizedEmbeddingReqInput` and correlated final vectors |
| pooler/task head | packed hidden states, pooling type, dimensions, normalization, MIS indices | dense embeddings, logits, scalar scores, optional pre-head states |
| tokenization adapters | prompt/chat schema and tokenizer/template state | token IDs or decoded text without accelerator work |

`EmbeddingReqInput` is a transport name, not a semantic guarantee. Dense
embedding models usually truncate then normalize pooled hidden states;
sequence-classification models apply a task head; cross encoders activate and
squeeze a scalar. `BatchEmbeddingOutput` returns all three through the same
request-ID-correlated channel. CausalLM score and decoder rerank deliberately
bypass that branch because their labels come from next-token logprobs. See
[Embeddings, Classification, Scoring, Reranking, and
Tokenization](09-openai-embeddings-and-scoring.md) for the ordered flow and
normalization rules.

## Configuration dependency

Raw CLI/config values become `ServerArgs`; resolution derives a consistent
record; `runtime_context.publish` projects process-local, read-only namespace
bags; runtime modules read those bags and live distributed topology. This order
is important:

```text
CLI/config file -> raw ServerArgs -> resolve/check -> publish(role)
                -> config namespaces + live parallel state -> runtime behavior
```

See [`prepare_server_args`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L10510-L10544),
[`resolve_once`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L3667-L3698),
and [`publish`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/runtime_context.py#L1308-L1355).
The full dependency order and mutation boundaries are explained in
[Configuration and startup](02-configuration-and-startup.md).

| Configuration component | Depends on | Supplies |
| --- | --- | --- |
| CLI annotation layer | Dataclass types/defaults, `Arg` metadata | One argparse grammar and raw `ServerArgs` |
| YAML merger | The constructed argparse actions | Lower-precedence CLI tokens, not a second schema |
| Resolution pipeline | Raw values, model metadata, hardware/platform probes, ordered declarations | A materialized read-only startup record |
| Runtime publication | Resolved record and `NS` metadata | Process-role provenance and nested config bags |
| Parallel context | Published topology config and initialized process groups | Configured launch sizes before init; live ranks/groups after init |
| Launch/warmup | Published config, ports, ranks, scheduler pipes, HTTP lifecycle | Scheduler readiness followed by public service readiness |

## Questions for later passes

- Which cache owns token slots, KV tensors, radix nodes, host storage, and
  external/disaggregated copies?
- Which model/layer abstractions are stable extension points versus
  hardware/model-specific implementations?
- Which Rust server and gateway protocols are generated from shared schemas,
  and where are compatibility versions enforced?
