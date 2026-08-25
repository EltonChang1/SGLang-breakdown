# Glossary

Definitions here describe usage in the pinned SGLang snapshot, not every use of
the term in the wider ML ecosystem.

**Backend.** Context-dependent term. A *frontend backend* implements the
`BaseBackend` generation/stream/selection boundary for an SGL program; a serve
backend is an LLM, diffusion, or installed external launcher implementing
`ServeBackend`; an attention, kernel, quantization, or communication backend is
an implementation selected inside the runtime. Always name the kind.

**Anthropic content block.** The typed unit inside an Anthropic message or
stream, such as text, thinking, or tool use. In Python SRT the Messages adapter
translates input blocks to OpenAI chat parts and reconstructs output blocks from
OpenAI semantic chunks. A stream owns indexed start/delta/stop lifecycles per
block; a block is not a scheduler request or a Responses output item
([stream state](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L838-L939)).

**Anthropic serving adapter.** The tokenizer-process compatibility layer behind
`/v1/messages` and `/v1/messages/count_tokens`. It converts Anthropic records
to `ChatCompletionRequest`, delegates model-facing work to
`OpenAIServingChat`, and converts full or streamed output back to Anthropic
shape. It is distinct from the `sglang.lang` Anthropic provider client and does
not execute Anthropic built-in server tools. See
[Anthropic-Compatible Messages API](11-anthropic-messages.md).

**Choice policy.** A frontend callable that chooses among complete candidate
strings from their conditional token logprobs and, optionally, unconditional
logprobs. Built-ins use token-length normalization, greedy token comparison, or
unconditional-likelihood normalization
([policy interface](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/choices.py#L8-L29)).

**Chat template (frontend).** The lightweight `sglang.lang` record that maps
roles to prefix/suffix text and supplies default system text, stops, and media
markers. Model-path selection is ordered and first-match-wins. It is distinct
from SRT/tokenizer Jinja conversation templates
([record and registry](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L7-L78)).

**Continuous batching.** Scheduling requests into changing batches as work
arrives and existing requests finish, rather than holding a static batch for
its whole lifetime. The detailed scheduler policy is not covered yet.

**Control plane.** Operations that inspect or mutate the live runtime rather
than submit ordinary inference: cache/memory controls, profiling, sessions,
weight or LoRA updates, state readback, and collective RPC. Offline-engine
methods usually delegate these to tokenizer-side typed communicators so rank
fan-out and result merging have one owner
([engine controls](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1278-L1629)).

**Config bag.** A process-local, read-only namespace projected from resolved
`ServerArgs` fields at publication, such as `get_exec()` or `get_schedule()`.
It is the runtime source of truth; sanctioned post-publication overrides update
bags and provenance, not the startup record
([projection](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/runtime_context.py#L596-L730)).

**CP / context parallelism.** Splitting attention/context work across ranks.
The code distinguishes attention CP and additional derived rank concepts; do
not use `CP` as a generic synonym for tensor parallelism.

**Decode.** Autoregressive generation after prompt processing, commonly one or
a small number of new tokens per active request per step. In disaggregated mode,
decode can be hosted by different workers from prefill.

**DataType (diffusion).** The multimodal-generation request/output kind:
`IMAGE`, `VIDEO`, `MESH`, or `ACTION`. It selects default filename extension
and output materialization behavior; it is unrelated to a tensor's numeric
dtype
([enum](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/configs/sample/sampling_params.py#L81-L95)).

**DetokenizerManager.** The process-side component that turns scheduler token
outputs into text deltas and returns them to tokenizer-side request state. It
keeps bounded decoding context so subword boundaries remain correct while old
token history can be discarded; cumulative versus incremental client output
is decided later by `TokenizerManager`. See [Native `/generate`
Protocol](07-native-generate-protocol.md#correlation-batching-and-streaming-shapes).

**DiffGenerator.** The public synchronous Python client for the separate
`sglang.multimodal_gen` runtime. Local mode launches diffusion workers without
requiring HTTP; remote mode connects to scheduler endpoints. It prepares and
expands media requests, returns `GenerationResult`, exposes LoRA/action
controls, and owns client/worker cleanup
([class](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/diffusion_generator.py#L68-L145)).

**DP / data parallelism.** Multiple replicas or data-parallel ranks serving
work. In the default launcher, `dp_size > 1` introduces a data-parallel
controller that owns scheduler creation rather than directly starting all
schedulers from the tokenizer process.

**EP / expert parallelism.** Distributing mixture-of-experts experts and their
routing/communication across ranks. SGLang separately tracks expert, expert
data, and expert tensor ranks.

**Embedding path (SRT).** The prefill-only request/result transport built on
`EmbeddingReqInput`, `TokenizedEmbeddingReqInput`, and `BatchEmbeddingOutput`.
Despite the name, its output can be a dense embedding, task-head logits, a
reward, or a scalar cross-encoder score. The public adapter supplies the
semantic interpretation
([request record](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1066-L1128),
[pooler output](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L26-L44)).

**Frontend language.** The client-side `sglang.lang` programming layer. It runs
ordinary Python around typed SGL expressions and delegates model operations to
a frontend backend. It is an orchestrator above remote inference, not the SRT
scheduler or model loop. See [Frontend Language Execution](04-frontend-language.md).

**Provider client.** A frontend `BaseBackend` implementation that converts
executor text/messages/media and common sampling values into a remote provider
SDK call. These clients run synchronously on executor workers and expose
different capability subsets; they are not SRT's OpenAI/Anthropic server-side
protocol adapters. See
[Provider Clients and Prompt Templates](05-provider-clients-and-templates.md).

**Frontend IR.** The `SglExpr` hierarchy representing text, generation,
selection, roles, media, variables, scopes, forks, and optimization markers.
The interpreter consumes it incrementally; tracing links the same nodes into a
symbolic dependency graph
([IR definitions](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L327-L643)).

**IPC.** Inter-process communication. The default engine uses ZMQ endpoints
carried by `PortArgs`; local mode primarily uses `ipc://` files, while some
distributed modes derive TCP addresses
([`PortArgs`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L10551-L10635)).

**Harmony.** GPT-OSS's role/channel/recipient message and token protocol. The
Responses adapter uses it instead of an SRT chat template for GPT-OSS, parses
analysis/final/tool recipients from output token IDs, and can rerender the
conversation after server-executed browser or Python work. It is not a generic
synonym for reasoning or tool calling
([message conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/harmony_utils.py#L142-L245)).

**KV cache.** Accelerator or tiered storage for attention keys and values from
already processed tokens. It enables reuse and incremental decoding. Ownership,
allocation, and eviction receive a dedicated later guide.

**Matryoshka embedding.** An embedding trained so an allowed leading prefix of
the full vector remains useful. SGLang validates the requested dimension,
truncates before normalization, and can return different vector widths for
requests in one batch
([validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1267-L1293),
[pooler](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L184-L210)).

**MIS / multi-item scoring.** A scoring mode that packs one query and many
items into a delimiter-indexed sequence. It produces one boundary result plus
one result per item; the query-boundary result is discarded after strict count
validation. Delimiter indices, not a scan for the placeholder token, define
the scoring positions
([packing](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L68-L87),
[result processing](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L110-L190)).

**NDJSON.** Newline-delimited JSON: one complete JSON object per line. The
Ollama stream adapter uses `application/x-ndjson`, unlike native/OpenAI/
Anthropic server-sent events; it ends with a record whose `done` is true rather
than an SSE `[DONE]` sentinel
([chat stream](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L132-L171)).

**Ollama serving adapter.** The tokenizer-process compatibility layer behind
the configurable chat, generate, tags, and show routes. It directly builds
native generation requests, exposes only a subset of its declared request
fields, and advertises synthetic model metadata. It is distinct from both the
real Ollama server and SGLang's client-side `SmartRouter`; this snapshot has no
Ollama embedding route. See [Ollama-Compatible API and Smart
Router](12-ollama-api-and-smart-router.md).

**Offline Engine.** The in-process `sglang.Engine` Python API. It avoids an
HTTP/gRPC request boundary but still launches the shared tokenizer, scheduler,
detokenizer, IPC, and model-execution topology. "Offline" is a transport choice,
not a promise of single-process execution. See
[Offline Engine API](03-offline-engine.md).

**OpenAI serving adapter.** A tokenizer-side compatibility layer that validates
an OpenAI-shaped request, renders or maps it to `GenerateReqInput`,
`EmbeddingReqInput`, or tokenizer-only work, delegates when needed, and
reshapes native results as OpenAI JSON or SSE. It does not own scheduling or
model execution, and accepting an official field does not prove the field has
behavior. See [OpenAI Completions and Chat
Completions](08-openai-completions.md) and [Embeddings, Classification,
Scoring, Reranking, and Tokenization](09-openai-embeddings-and-scoring.md).

**Responses state (Python SRT).** The in-memory `msg_store`, `response_store`,
and background-task map owned by `OpenAIServingResponses`. They support
`previous_response_id`, retrieval, and background cancellation in one API
process but have no TTL, persistence, or cross-worker sharing. They are
distinct from scheduler sessions and the Rust gateway's storage
([stores](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L178-L192)).

**Responses output item.** The semantic unit returned by `/v1/responses`, such
as assistant `message`, `reasoning`, `function_call`, web-search, or
code-interpreter work. Regular streaming owns an added/delta/done lifecycle
per item and builds the final response from items closed in wire order; it is
not a chat-completion choice
([regular stream state](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L1997-L2215)).

**Smart Router (Ollama package).** A synchronous client utility that asks an
Ollama-served judge to classify a prompt, then calls local Ollama or a remote
SGLang Ollama-compatible endpoint. Full responses get one opposite-destination
fallback; streams do not. It is a heuristic demo, not an SRT request router,
scheduler policy, or security boundary
([class](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L23-L241)).

**Output-rank persistence (diffusion).** The default diffusion transport in
which the worker output rank writes generated media and clears tensor/audio
payloads before returning paths over ZMQ. It reduces serialization but means
the path is interpreted in the worker's filesystem namespace
([transport branch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/managers/gpu_worker.py#L610-L652)).

**ProgramState.** The imperative handle passed as `s` to a decorated SGL
function. It submits expressions, exposes named generated variables and
metadata, builds role/scope contexts, streams text, and creates fork groups. Its
`StreamExecutor` owns the mutable prompt and synchronization state
([class](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L852-L1042)).

**PP / pipeline parallelism.** Splitting model stages across ranks. The launcher
creates scheduler processes over PP and TP rank ranges; pipeline mode selects
special scheduler loops and imposes compatibility constraints.

**Pooler.** A model-side layer that reduces per-token hidden states to one or
more request-level vectors. SGLang's common pooler supports last-token, CLS,
and mean strategies, optional Matryoshka truncation, normalization, task heads,
cross-encoder scoring, and MIS delimiter positions
([implementation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L47-L263)).

**Prefill.** Processing prompt/input tokens to populate model state and KV
cache before decode. Chunked prefill divides large prefill work so it can be
scheduled with other requests.

**Public readiness.** For the Python HTTP path, the state reached after the
server is bound and a real generation/embedding warmup succeeds (or warmup is
explicitly skipped). This is later than scheduler readiness; `/health` returns
503 while the tokenizer manager is still starting.

**Resolved configuration.** The result of the one-time ordered `ServerArgs`
pipeline: defaults, compatibility choices, model/hardware policy, and
validations have been applied and the record is read-only. It is distinct from
raw CLI/YAML input and from later runtime bag overrides.

**SamplingParams (SRT).** The scheduler-facing generation policy created after
request values override server-preferred defaults. It owns token budget,
penalties, sampling filters, stops, grammar constraints, seed, stream interval,
and verification. Normalization converts near-zero temperature to greedy
`top_k=1` behavior and tokenizer-dependent normalization expands text stops
([implementation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/sampling/sampling_params.py#L38-L332)). It is unrelated to the
diffusion runtime's class of the same name.

**RID / request ID.** The correlation key joining tokenizer-side request
state, scheduler/detokenizer output, and the result's `meta_info.id`. Missing
IDs are generated during normalization; IDs within a batch and IDs already in
flight must be unique
([normalization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L345-L395),
[state guard](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L3358-L3395)).

**Runtime / RuntimeEndpoint.** `RuntimeEndpoint` is the frontend backend for an
already-running SRT HTTP server. `Runtime` owns a spawned local HTTP server and
exposes such an endpoint. Neither is the offline `Engine`, which bypasses HTTP
between its Python methods and tokenizer manager
([endpoint and wrapper](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L26-L555)).

**RadixAttention.** SGLang's prefix-sharing approach built around a radix-tree
view of reusable KV-backed token prefixes. This is an architectural term here;
the exact cache-node and allocator invariants remain pending.

**Scheduler.** The accelerator-owning runtime component that receives
tokenized work, admits and batches requests, invokes model execution, manages
cache/scheduling state, and emits results. There can be multiple scheduler
processes for parallel ranks.

**SchedulerClient (diffusion).** The sync/async ZMQ client used by
`sglang.multimodal_gen`. Ordinary requests select one DP ingress endpoint,
realtime sessions stay affinity-pinned, and stateful control requests fan out
to every replica. It is distinct from SRT tokenizer-to-scheduler transport
([routing](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/scheduler_client.py#L117-L197)).

**Scheduler readiness.** The parent-process handshake sent after a scheduler
has constructed the model runtime and can report token limits and startup
timings. It proves model-process initialization, but not yet a successful
request through the public HTTP path.

**Session parameters.** The scheduler conversation-history selector carried
as `session_params`: an opened session ID plus optional prior request ID,
replacement, token offset, or previous-output policy. It is distinct from the
separate `session_id` identity field, and request normalization rejects using
both at once
([schemas](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L120-L167),
[check](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L386-L395)).

**SglExt.** The response-level `sglext` object used by the OpenAI adapters for
requested SGLang-only routed-expert, cache-origin, and speculative-decoding
details. It is omitted when empty; speculative details become one object for
a single choice and a list for `n > 1`
([schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L432-L449)).

**SRT.** SGLang Runtime, implemented primarily under `python/sglang/srt`. It is
the language-model serving runtime and includes much more than the scheduler:
protocols, configuration, tokenization, caches, model execution, distributed
modes, and operations.

**SSE / server-sent events.** The native streaming response format: each
result is encoded as `data: <json>` followed by a blank line, and ordinary
completion ends with `data: [DONE]`. This snapshot can surface a streaming
`ValueError` as an in-band JSON error event; client disconnect ends the stream
without the sentinel. See [the native stream
contract](07-native-generate-protocol.md#correlation-batching-and-streaming-shapes).

**TokenizerManager.** The tokenizer-side coordinator in the main process for
the common HTTP/offline topology. It owns request normalization/state,
tokenization and media preparation, scheduler dispatch, cancellation, and
response correlation.
Default streaming accumulates detokenizer deltas into the full prefix; the
`--incremental-streaming-output` mode instead exposes new suffixes only.

**Token healing.** Re-evaluating a small suffix of an existing prompt so a
candidate can share or complete the prompt's final tokenization correctly. The
frontend runtime choice path starts logprobs up to two prompt tokens back and
removes an unchanged healed token before comparing candidates
([choice path](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L257-L293)).

**Tool-call constraint.** A structural-tag or JSON-schema generation
constraint derived from chat tools and tool choice. Required/named calls use
it to make parser input structurally reliable when a model-specific detector
does not own a native format. It cannot be combined with another required
output constraint because both cannot govern the same token stream
([sampling rule](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1142-L1173)).

**TP / tensor parallelism.** Splitting tensor/model computation across ranks.
The launcher maps local GPU IDs and spawns scheduler processes for TP/PP rank
ranges when a data-parallel controller is not used
([`_launch_scheduler_processes`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L818-L933)).

**ZMQ.** ZeroMQ, the messaging library used for tokenizer, scheduler,
detokenizer, RPC, and metrics process channels in the default Python topology.
