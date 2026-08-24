# Glossary

Definitions here describe usage in the pinned SGLang snapshot, not every use of
the term in the wider ML ecosystem.

**Backend.** Context-dependent term. A *frontend backend* implements the
`BaseBackend` generation/stream/selection boundary for an SGL program; a serve
backend is an LLM, diffusion, or installed external launcher implementing
`ServeBackend`; an attention, kernel, quantization, or communication backend is
an implementation selected inside the runtime. Always name the kind.

**Choice policy.** A frontend callable that chooses among complete candidate
strings from their conditional token logprobs and, optionally, unconditional
logprobs. Built-ins use token-length normalization, greedy token comparison, or
unconditional-likelihood normalization
([policy interface](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/choices.py#L8-L29)).

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

**DetokenizerManager.** The process-side component that turns scheduler token
outputs into incremental or final text and returns them to tokenizer-side
request state. Its process entry is
[`run_detokenizer_process`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L516-L539).

**DP / data parallelism.** Multiple replicas or data-parallel ranks serving
work. In the default launcher, `dp_size > 1` introduces a data-parallel
controller that owns scheduler creation rather than directly starting all
schedulers from the tokenizer process.

**EP / expert parallelism.** Distributing mixture-of-experts experts and their
routing/communication across ranks. SGLang separately tracks expert, expert
data, and expert tensor ranks.

**Frontend language.** The client-side `sglang.lang` programming layer. It runs
ordinary Python around typed SGL expressions and delegates model operations to
a frontend backend. It is an orchestrator above remote inference, not the SRT
scheduler or model loop. See [Frontend Language Execution](04-frontend-language.md).

**Frontend IR.** The `SglExpr` hierarchy representing text, generation,
selection, roles, media, variables, scopes, forks, and optimization markers.
The interpreter consumes it incrementally; tracing links the same nodes into a
symbolic dependency graph
([IR definitions](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L327-L643)).

**IPC.** Inter-process communication. The default engine uses ZMQ endpoints
carried by `PortArgs`; local mode primarily uses `ipc://` files, while some
distributed modes derive TCP addresses
([`PortArgs`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L10551-L10635)).

**KV cache.** Accelerator or tiered storage for attention keys and values from
already processed tokens. It enables reuse and incremental decoding. Ownership,
allocation, and eviction receive a dedicated later guide.

**Offline Engine.** The in-process `sglang.Engine` Python API. It avoids an
HTTP/gRPC request boundary but still launches the shared tokenizer, scheduler,
detokenizer, IPC, and model-execution topology. "Offline" is a transport choice,
not a promise of single-process execution. See
[Offline Engine API](03-offline-engine.md).

**ProgramState.** The imperative handle passed as `s` to a decorated SGL
function. It submits expressions, exposes named generated variables and
metadata, builds role/scope contexts, streams text, and creates fork groups. Its
`StreamExecutor` owns the mutable prompt and synchronization state
([class](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L852-L1042)).

**PP / pipeline parallelism.** Splitting model stages across ranks. The launcher
creates scheduler processes over PP and TP rank ranges; pipeline mode selects
special scheduler loops and imposes compatibility constraints.

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

**SRT.** SGLang Runtime, implemented primarily under `python/sglang/srt`. It is
the language-model serving runtime and includes much more than the scheduler:
protocols, configuration, tokenization, caches, model execution, distributed
modes, and operations.

**TokenizerManager.** The tokenizer-side coordinator in the main process for
the common HTTP/offline topology. It owns request normalization/state,
tokenization and media preparation, scheduler dispatch, cancellation, and
response correlation.

**Token healing.** Re-evaluating a small suffix of an existing prompt so a
candidate can share or complete the prompt's final tokenization correctly. The
frontend runtime choice path starts logprobs up to two prompt tokens back and
removes an unchanged healed token before comparing candidates
([choice path](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L257-L293)).

**TP / tensor parallelism.** Splitting tensor/model computation across ranks.
The launcher maps local GPU IDs and spawns scheduler processes for TP/PP rank
ranges when a data-parallel controller is not used
([`_launch_scheduler_processes`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L818-L933)).

**ZMQ.** ZeroMQ, the messaging library used for tokenizer, scheduler,
detokenizer, RPC, and metrics process channels in the default Python topology.
