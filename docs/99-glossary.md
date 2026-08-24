# Glossary

Definitions here describe usage in the pinned SGLang snapshot, not every use of
the term in the wider ML ecosystem.

**Backend.** Context-dependent term. A serve backend is an LLM, diffusion, or
installed external launcher implementing `ServeBackend`; an attention, kernel,
quantization, or communication backend is an implementation selected inside
the runtime. Always name the kind.

**Continuous batching.** Scheduling requests into changing batches as work
arrives and existing requests finish, rather than holding a static batch for
its whole lifetime. The detailed scheduler policy is not covered yet.

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

**IPC.** Inter-process communication. The default engine uses ZMQ endpoints
carried by `PortArgs`; local mode primarily uses `ipc://` files, while some
distributed modes derive TCP addresses
([`PortArgs`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L10551-L10635)).

**KV cache.** Accelerator or tiered storage for attention keys and values from
already processed tokens. It enables reuse and incremental decoding. Ownership,
allocation, and eviction receive a dedicated later guide.

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

**SRT.** SGLang Runtime, implemented primarily under `python/sglang/srt`. It is
the language-model serving runtime and includes much more than the scheduler:
protocols, configuration, tokenization, caches, model execution, distributed
modes, and operations.

**TokenizerManager.** The tokenizer-side coordinator in the main process for
the common HTTP/offline topology. It owns request normalization/state,
tokenization and media preparation, scheduler dispatch, cancellation, and
response correlation.

**TP / tensor parallelism.** Splitting tensor/model computation across ranks.
The launcher maps local GPU IDs and spawns scheduler processes for TP/PP rank
ranges when a data-parallel controller is not used
([`_launch_scheduler_processes`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L818-L933)).

**ZMQ.** ZeroMQ, the messaging library used for tokenizer, scheduler,
detokenizer, RPC, and metrics process channels in the default Python topology.
