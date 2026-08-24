# Offline Engine: File and Symbol Reference

This reference covers the public offline-engine contract and the adapter code
that carries it into tokenizer-side request and control paths. Scheduler policy,
session internals, cache implementations, model loading, and weight-update
workers are linked only at their boundary and keep their own later study passes.
Read the conceptual [Offline Engine API](../03-offline-engine.md) first.

## Engine base contract

### `python/sglang/srt/entrypoints/EngineBase.py`

**Status: covered.** `EngineBase` is the minimal nominal interface shared by
direct and transport-backed engines. Its abstract requirements are generation,
cache flush, tensor weight update, memory release/resume, and shutdown
([lines 7-79](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/EngineBase.py#L7-L79)).

The base is intentionally smaller than `Engine`: it does not promise async
generation, encoding, scoring, sessions, profiling, or every weight source.
Its `load_lora_adapter` and `unload_lora_adapter` methods are non-abstract
no-op stubs. A new subclass can therefore instantiate without implementing
LoRA and silently return `None`; capability-sensitive callers must check the
concrete engine rather than infer support from inheritance alone
([LoRA stubs](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/EngineBase.py#L49-L65)).

**Extension invariant.** Keep the base signature as the portability floor, not
as an exhaustive reflection of `Engine.generate`. Adding a required abstract
method would break every other engine implementation; adding a feature only to
`Engine` does not make it portable through `EngineBase`.

## Offline engine implementation

### `python/sglang/srt/entrypoints/engine.py`

**Status: covered across this note and the configuration/startup references.**
The file owns the concrete Python API, runtime launch, rank/port helpers,
weight-cache daemon bootstrap, environment/process setup, readiness polling,
and shutdown. Startup order, rank math, and readiness are explained in
[Configuration and startup](../02-configuration-and-startup.md#5-launch-converts-configuration-into-processes-ranks-and-channels).

### Construction and override hooks

`Engine` inherits `EngineScoreMixin` before `EngineBase`, then declares class
attributes for the `ServerArgs`, tokenizer-manager initializer, scheduler
runner, and detokenizer runner. Private forks and backend subclasses can
replace these without copying the launcher. `_placement_group` is a live
backend handle used by Ray placement, not resolved configuration
([class and hooks](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L209-L232)).

`__init__` loads plugins, chooses a supplied versus constructed `ServerArgs`,
rejects the Rust-server mode, preinitializes the tokenizer attribute for safe
early cleanup, registers `atexit`, calls the shared launcher, creates the
root-only direct RPC socket, optionally initializes tracing, and selects an
event loop
([lines 234-325](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L234-L325)).
If `server_args` is present, the other constructor keywords are not merged
into it; callers should pass one form or the other.

The `_launch_subprocesses` return annotation lists five tuple members, but its
docstring, every return statement, and `Engine.__init__` use six, with
engine-owned weight-cache daemon processes in the final slot
([annotation and docstring](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1022-L1047),
[constructor unpack](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L280-L300)).
Runtime behavior is unambiguous, but subclasses and static tooling should not
trust that stale annotation until it is corrected upstream.

`get_all_child_pids` returns the launch result's collected scheduler,
detokenizer, controller, and related child IDs. It is observability data, not a
resource-ownership transfer
([lines 327-329](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L327-L329)).

### Generation and embeddings

`_resolve_routed_dp_rank` translates the deprecated alias, ignores rank zero
for a single replica, and rejects ranks outside the configured DP space
([lines 331-360](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L331-L360)).

`generate` and `async_generate` have parallel argument-to-`GenerateReqInput`
mappings. The sync method drives the manager's async generator with the stored
loop; the async method either returns that generator for streaming or awaits
its first aggregate result
([sync, lines 362-470](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L362-L470),
[async, lines 472-573](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L472-L573)).
The duplicated construction is an API drift risk: a new field must be threaded
through both methods. At this snapshot their mappings agree.

`encode` and `async_encode` likewise build `EmbeddingReqInput`; `rerank` is the
sync-only specialization that sets `is_cross_encoder_request=True`
([lines 575-654](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L575-L654)).
Their `Dict` annotations understate batched runtime behavior: the shared
generator returns a list for batched inputs.

### Weight-cache daemon launch

`_launch_weight_cache_daemons` is active only for engine-owned daemon mode. It
requires a shared rendezvous address for multi-node launch, computes this
node's PP/TP rank range and GPU IDs, removes only stale readiness/socket files,
starts one daemon per local PP-by-TP rank, and waits for every readiness file
while checking that no daemon exited early
([lines 656-789](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L656-L789)).

The daemons are co-terminal with this engine and therefore do not make a later
engine restart faster by themselves. The persistent fast-recovery topology is
a separately launched daemon plus client mode. Timeout or partial launch
terminates already-started siblings. `_terminate_weight_cache_daemons` sends
SIGTERM first so handlers can remove IPC state, then SIGKILLs stragglers after
the join timeout
([lifecycle explanation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L656-L684),
[termination](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L791-L816)).
The daemon protocol and loader internals remain assigned to the model-loading
pass; the complete engine-side ownership boundary is covered here.

### Shared process launch and environment

`SchedulerInitResult` carries scheduler initialization dictionaries, all child
PIDs, deferred readiness/blocking callbacks, and an optional bootstrap server
([lines 147-154](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L147-L154)).
`init_tokenizer_manager` creates the manager and template manager, then turns
auto-detected reasoning/tool parser suggestions into runtime config updates or
explicitly disables unresolved auto choices
([lines 157-206](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L157-L206)).

The scheduler/detokenizer launch helpers and `_launch_subprocesses` implement
the process graph and failure gates
([lines 818-1237](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L818-L1237)).
`_set_startup_time` merges rank initialization timings rather than trusting a
single rank and publishes them to tokenizer-side metrics
([lines 993-1020](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L993-L1020)).

`_set_envs_and_config` is a process-wide setup boundary. It derives NCCL and
kernel environment defaults, assigns a run ID, initializes Prometheus
multiprocess storage, raises file limits, checks FlashInfer/SGL kernel versions,
installs the launch-phase `SIGQUIT` cleanup handler only on the main thread,
forces multiprocessing spawn, applies an optional GC threshold, and reports
legacy cache directories without deleting them
([lines 1632-1759](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1632-L1759)).
The main-thread restriction matters: constructing an engine elsewhere disables
the child-to-parent SIGQUIT process-tree cleanup path and emits a warning.

`_scheduler_died_error` joins briefly and turns an early process death into a
rank/exit-code error with an OOM diagnostic. `_wait_for_scheduler_ready` polls
all pipes, validates status, and checks every process after a timeout.
`_calculate_rank_ranges` and `_compute_parallelism_ranks` cover node/PP/TP and
attention/MoE rank decomposition
([lines 1762-1864](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1762-L1864)).

### Lifecycle, sessions, and controls

`shutdown` and the context methods own the public lifetime
([lines 1239-1276](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1239-L1276)).
The remaining methods fall into these adapter groups:

| Symbols | Responsibility | Source |
| --- | --- | --- |
| `flush_cache`, `open_session`, `close_session` | cache and conversation lifetime | [lines 1278-1318](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1278-L1318) |
| profile/expert controls | profiler and MoE-routing observations | [lines 1320-1340](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1320-L1340) |
| `get_server_info`, `get_model_info` | launch/live state readback | [lines 1342-1375](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1342-L1375) |
| update-group and weight-source methods | in-place model mutation | [lines 1377-1495](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1377-L1495) |
| tensor serialization and LoRA methods | per-rank payloads and adapter lifetime | [lines 1497-1583](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1497-L1583) |
| memory, GC, collective RPC, model save | operational controls | [lines 1585-1629](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1585-L1629) |

These wrappers should stay small. Validation, locking, fan-out, merging, and
config readback belong to `TokenizerManager`; direct scheduler RPC is reserved
for the two save wrappers and explicit `collective_rpc` calls.

## Engine score adapter

### `python/sglang/srt/entrypoints/engine_score_mixin.py`

**Status: covered.** `EngineScoreMixin` supplies sync `score` and async
`async_score`. Both forward the same query/items, label-token, ordering,
embedding-override, normalization, and pooled-state arguments to
`TokenizerManager.score_request`. The sync version drives the stored event
loop; the async version awaits the manager directly
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine_score_mixin.py#L1-L111)).

The mixin assumes its host has `loop` and `tokenizer_manager`; it is reusable by
shape, not a standalone class. It does not catch validation/model errors or
convert the `ScoreResult`, so sync and async semantics remain aligned.

## Score preparation and result contract

### `python/sglang/srt/managers/tokenizer_manager_score_mixin.py`

**Status: covered.** `ScoreResult` is an immutable, slotted record of per-item
scores, prompt-token count, and optional CPU pooled-state tensors. HTTP code
must convert tensors to lists; the in-process engine intentionally avoids that
round trip
([lines 13-23](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L13-L23)).

The mixin has four stages:

1. `score_prompts` converts already-composed text or token prompts into the
   general query/items API
   ([lines 26-66](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L26-L66)).
2. Input helpers tokenize text, concatenate ordinary query/item pairs or one
   delimiter-indexed multi-item sequence, and resolve embedding replacements
   to exact token positions
   ([lines 68-372](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L68-L372)).
3. `score_request` validates model/input combinations, builds either a
   zero-new-token `GenerateReqInput` or `EmbeddingReqInput`, runs the shared
   request path, and selects ordinary versus multi-item result processing
   ([lines 443-601](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L443-L601)).
4. Result helpers read label logprobs for generation models or head logits for
   classification models, validate delimiter counts, optionally softmax, and
   preserve pooled states when supported
   ([lines 111-238](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L111-L238),
   [lines 603-671](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L603-L671)).

**Invariants and failures.** CausalLM scoring requires label token IDs; items
are required; override embeddings require a placeholder token and exact list
lengths; `item_first` cannot combine with overrides; label IDs must be inside
the tokenizer vocabulary; pooled hidden states reject generation models and
cross-encoding poolers; multi-item output must contain exactly one delimiter
result per item plus the query boundary. Missing scoring fields or count drift
is a runtime error rather than a partial result.

**Non-obvious result rule.** With `apply_softmax=False`, CausalLM logprobs are
exponentiated individually. With `True`, only selected label logprobs are
softmaxed. Classification outputs apply softmax across the head vector when
requested. These three operations should not be conflated.

## Request and control schemas

### `python/sglang/srt/managers/io_struct.py`

**Status: partial.** The offline pass covers these structures:

- `GenerateReqInput`, `SessionParams`, and their single/batch normalization
  ([lines 120-905](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L120-L905));
- `EmbeddingReqInput` normalization and item extraction
  ([lines 1066-1299](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1066-L1299));
- disk/distributed/tensor/IPC weight, update-group, weight-readback, and memory
  request records
  ([lines 1736-1955](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1736-L1955)); and
- profile, open/close session, collective RPC, and LoRA request records
  ([lines 2060-2256](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L2060-L2256)).

`GenerateReqInput` is a Python dataclass because it performs rich normalization
and caches per-item subobjects. Most process-wire controls inherit the msgspec
base because compact typed IPC matters more than mutable preprocessing.
One pinned-snapshot caveat is that `_validate_inputs` rejects no main input or
all three of text, token IDs, and embeddings, but does not reject every
two-input combination despite its "either" error message
([validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L397-L415)).
The public contract is still to provide exactly one main input; callers should
not depend on the accidental precedence when both `prompt` and `input_ids` are
set.
Hundreds of scheduler, output, metrics, disaggregation, cache, and protocol
message types remain for their owning passes; the file is not fully covered.

## Tokenizer-side boundaries

### `python/sglang/srt/managers/tokenizer_manager.py`

**Status: partial.** This pass extends the existing single-request trace to
cover request normalization, batch aggregation/interleaving, request-state
cleanup, input/embedding override validation, disk weight update locking,
control-plane config readback, GC fan-out, and the public engine's response
shape
([request entry](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L767-L820),
[batch completion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1795-L1940),
[disk update and readback](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1985-L2112),
[state cleanup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L3358-L3420)).

Remaining work includes manager construction, media/cache implementations,
grammar/parser processing, cancellation races, full output/logprob assembly,
multi-tokenizer and elastic routing, observability, and protocol-only paths.

## Control-plane fan-out

### `python/sglang/srt/managers/tokenizer_control_mixin.py`

**Status: partial.** The engine-reachable methods covered here are cache flush;
profiling and expert records; update-group, distributed/tensor/IPC weight
updates; LoRA path/tensor load and unload; weight readback; memory release and
resume; internal-state readback; and session open/close
([cache/profile](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L301-L419),
[weights](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L421-L599),
[LoRA and memory](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L601-L812),
[state and sessions](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L844-L928)).

The common pattern is `auto_create_handle_loop`, typed communicator fan-out,
rank-result merge, and tokenizer-side reconciliation only after successful
runtime mutation. External corpora, HiCache attach/detach, remote-instance
weight sending, checksums, logging, pause/continue, load snapshots, elastic
scaling, dumper controls, and other HTTP-only management surfaces remain.

## Reference study check

Choose one generation method, one scoring method, and one weight mutation. For
each, identify:

1. the public adapter and return-shape bridge;
2. the request structure and normalization;
3. the tokenizer-side lock or request state;
4. the scheduler-facing dispatch channel;
5. the result merge or correlation point; and
6. the cleanup action if preprocessing, rank execution, or caller consumption
   fails.
