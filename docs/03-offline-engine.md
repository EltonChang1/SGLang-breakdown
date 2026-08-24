# Offline Engine API

`sglang.Engine` is SGLang's in-process Python API for language-model inference.
"Offline" means that the caller does not cross an HTTP or gRPC boundary. It
does **not** mean that inference runs in one process: the Python object still
launches the same tokenizer-side coordinator, scheduler process or processes,
detokenizer path, runtime configuration, and ZMQ channels used by the default
HTTP server
([`Engine`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L209-L232),
[`_launch_subprocesses`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1022-L1237)).

Read [Configuration and startup](02-configuration-and-startup.md) first if
raw, resolved, and published configuration or scheduler readiness are new
terms. The companion [file reference](reference/offline-engine.md) maps this
guide to the implementation symbols.

## 1. The API is a transport adapter, not a second inference core

The public object has four responsibilities:

1. normalize Python constructor arguments into `ServerArgs` and launch the
   shared runtime;
2. convert method arguments into the same request structures used by serving
   adapters;
3. bridge synchronous callers to tokenizer-manager coroutines, or expose those
   coroutines directly through async methods; and
4. expose selected runtime control operations without HTTP serialization.

For generation, the ordered path is:

```text
Python caller
  -> Engine.generate / async_generate
  -> GenerateReqInput
  -> TokenizerManager.normalize + tokenize + correlate request ID
  -> ZMQ dispatch to scheduler process(es)
  -> model work and optional detokenization
  -> TokenizerManager response state
  -> dict, iterator, or async iterator returned to caller
```

`Engine.generate` creates a `GenerateReqInput` and immediately delegates to
`TokenizerManager.generate_request`; it does not implement sampling,
tokenization, batching, cache lookup, or model execution itself
([sync adapter](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L362-L470),
[tokenizer-manager entry](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L767-L820)).
That boundary is why an offline result should match the HTTP runtime for the
same resolved configuration and deterministic sampling inputs; the transport
front end changed, not the accelerator path.

The offline API is rank-zero-facing. Nonzero multi-node launchers do not build
tokenizer-side state, and node zero alone creates the direct scheduler RPC
socket
([nonzero-node branch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1111-L1137),
[RPC socket](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L297-L307)).

## 2. Construction fixes the runtime and event-loop boundary

`Engine.__init__` loads plugins before constructing `ServerArgs`, so plugin
hooks participate in configuration resolution. Callers may either pass
`server_args=<ServerArgs>` or pass `ServerArgs` fields as keyword arguments.
When it constructs the record itself, the offline API defaults `log_level` to
`error`; an explicitly supplied `ServerArgs` keeps its own logging choice
([constructor normalization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L234-L262)).

The constructor rejects `SGLANG_RUST_SERVER`. That option replaces the Python
HTTP/tokenizer path, so it is incompatible with an object whose methods require
a live Python `TokenizerManager`
([guard](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L264-L272)).
It registers `shutdown` with `atexit` before starting children, launches the
shared runtime, stores the tokenizer/template/port/watchdog handles, and only
then creates the root-only RPC socket
([lifecycle setup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L274-L307)).

Finally, the engine captures the running asyncio loop or creates and installs a
new loop when construction occurs in ordinary synchronous code
([loop selection](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L321-L325)).
This is part of the API contract, not an implementation curiosity:

- synchronous methods call `self.loop.run_until_complete(...)`;
- async methods await tokenizer-manager coroutines in the caller's loop; and
- calling a synchronous method while that same loop is already running raises
  the usual asyncio "event loop is already running" error.

Use `async_generate`, `async_encode`, `async_score`, and async LoRA operations
inside an async service. Notebook environments with a nested loop need an
explicit loop strategy; the pinned upstream usage note recommends
`nest_asyncio`
([offline API note](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/offline_engine_api.mdx#L18-L27)).
Because launch forces Python multiprocessing's `spawn` method, executable
scripts should also construct the engine behind `if __name__ == "__main__"`
([environment setup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1632-L1733),
[guarded example](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/runtime/engine/offline_batch_inference.py#L33-L40)).

## 3. Generation has four observable modes

`generate` and `async_generate` accept text or token IDs, scalar or batched
sampling/logprob options, multimodal data, LoRA selection, request IDs,
priority, tracing metadata, disaggregation bootstrap values, explicit DP
routing, sessions, cache namespaces, and optional hidden/expert outputs. The
method signatures deliberately mirror the subset of `GenerateReqInput` useful
to direct Python callers
([sync signature](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L362-L419),
[request schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L162-L363)).

The runtime result shape follows both batching and streaming:

| Input and mode | Synchronous return | Asynchronous return |
| --- | --- | --- |
| Single, non-streaming | one result `dict` | awaited result `dict` |
| Batch, non-streaming | `list[dict]` | awaited `list[dict]` |
| Single, streaming | `Iterator[dict]` | `AsyncIterator[dict]` |
| Batch, streaming | iterator of interleaved result chunks | async iterator of interleaved result chunks |

For a streaming batch, each chunk receives an `index` that maps it back to the
normalized batch position; completion order is not input order
([batch collection and streaming](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1887-L1940)).
For non-streaming calls, the engine consumes the single aggregate item yielded
by the tokenizer manager. For streaming calls, the synchronous wrapper drives
the async generator one item at a time, whereas `async_generate` returns the
generator itself
([sync bridge](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L457-L470),
[async bridge](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L472-L573)).

### Input normalization and correlation

The intended main-input contract is one of `prompt` or `input_ids`. The request
normalizer derives single versus batch shape, generates missing request IDs,
expands scalar options, validates list lengths and within-batch ID uniqueness,
and expands `sampling_params["n"]` into parallel samples
([normalization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L366-L483)).
After normalization, `TokenizerManager` creates one request-state entry per
request ID before preprocessing. Normal completion removes it through the
response path; pre-dispatch failure removes any still-pending entries in the
exception handler, preventing failed validation from leaking correlation state
([state creation and cleanup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L783-L820),
[`_init_req_state`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L3358-L3414)).

Text requires an initialized tokenizer. A `skip_tokenizer_init=True` engine
must receive token IDs. Tokenization and media processing run before context
length checks and scheduler dispatch; invalid length, unsupported embedding or
hidden-state modes, mismatched embedding overrides, and unavailable
multimodal encoders therefore fail on the caller side before model scheduling
([tokenization branch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L978-L1088),
[request validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1159-L1239)).

### Routing is a constraint, not a second batch axis

`routed_dp_rank` selects a data-parallel destination. The deprecated
`data_parallel_rank` alias warns and fills it only when the new spelling is
absent. Rank zero is normalized back to `None` for `dp_size == 1`; negative or
out-of-range ranks fail before request construction
([`_resolve_routed_dp_rank`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L331-L360)).
The tokenizer manager checks again against its elastic worker count, which can
differ from the originally configured DP size after scaling
([runtime check](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L779-L794)).

### Outputs are runtime records

Generation results contain `text` and `output_ids` when detokenization is
active plus `meta_info`. The tokenizer-side response builder adds the request
ID, finish reason, prompt/completion/cache counts, active weight version,
retractions, optional DP rank, and only the optional logprob, hidden-state,
expert, modality, or tracing fields requested and available
([response construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L2168-L2319)).
Do not assume an intermediate streaming chunk has the same completeness as the
final record. Depending on the configured streaming style, text/token fields
can be deltas or accumulated values; use the pinned runtime's merge helpers or
the final chunk when an accumulated answer is required.

## 4. Encoding, reranking, and scoring are different contracts

These methods all reach the same request pipeline, but they ask the model for
different products:

| API | Request type | Model expectation | Result |
| --- | --- | --- | --- |
| `encode` / `async_encode` | `EmbeddingReqInput` | embedding/pooling mode | dict for one input, list for a batch |
| `rerank` | cross-encoder `EmbeddingReqInput` | cross-encoder model | pooled ranking output through the embedding response shape |
| `score` / `async_score` | generation or embedding request built by score mixin | CausalLM or classification/reward model | `ScoreResult` |

`encode` sets `max_new_tokens=0` during request normalization. It supports
Matryoshka output dimensions, LoRA, multimodal input, and replacing placeholder
tokens with caller-supplied embedding tensors. Placeholder count must equal
the number of replacement tensors after tokenization
([engine methods](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L575-L640),
[`EmbeddingReqInput` normalization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1066-L1217),
[override resolution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1493-L1523)).
`rerank` is intentionally thinner: it marks a list of text pairs as a
cross-encoder request and offers neither an async twin nor the wider embedding
argument set
([`rerank`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L642-L654)).

Scoring has a more semantic adapter. For a CausalLM, `label_token_ids` is
required and the result is derived from label-token log probabilities. Without
`apply_softmax`, each value is exponentiated independently and remains a
probability under the full vocabulary; with it, only the selected labels are
renormalized to sum to one. Classification/reward models instead return pooled
head logits, optionally normalized with softmax. The immutable result records
`scores`, total prompt tokens, and optional pre-head pooled hidden states
([`ScoreResult`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L13-L23),
[result conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L603-L638)).

With multi-item scoring enabled, the tokenizer side combines the query and all
items into one delimiter-indexed sequence and extracts one result per item. Its
fixed `query, delimiter, item...` layout ignores `item_first`; the ordinary
mode builds one query/item request per item
([input construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L284-L372),
[main scoring branch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L443-L601)).

## 5. Sessions have two identities

`open_session(capacity_of_str_len, ...)` sends an `OpenSessionReqInput` and
returns the scheduler-approved ID. A streaming session must be enabled at
launch; duplicate IDs return `None` from the tokenizer-side guard, despite the
engine method's `str` annotation. `close_session` dispatches release and can
defer final cleanup while a streaming request still owns KV state
([engine session methods](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1281-L1318),
[tokenizer-side open/close](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L898-L928),
[scheduler close safety](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/session/session_controller.py#L390-L435)).

The generation arguments `session_id` and `session_params` are not aliases:

- `session_params={"id": opened_id, ...}` selects scheduler-managed
  multi-turn context and can select a prior request ID, replace a branch,
  splice at a token offset, or drop previous output; and
- `session_id` is stable request identity for other serving/session consumers
  and does not reconstruct the prompt.

Request normalization rejects supplying both
([schema distinction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L120-L141),
[mutual exclusion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L386-L395)).
Streaming sessions allow only one in-flight request and append-only history;
replace, output dropping, and nonzero offsets abort that turn
([streaming invariants](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/session/session_controller.py#L210-L286)).

## 6. Control methods fan out through the tokenizer side

Most management methods are synchronous adapters: construct a typed request,
run the corresponding tokenizer-manager coroutine, and return its typed output
or merged `(success, message)` tuple. This keeps rank fan-out, locking, and
state reconciliation on the tokenizer side rather than duplicating them in the
public object.

### Cache, memory, profiling, and introspection

- `flush_cache` succeeds only when schedulers are fully idle; on success the
  tokenizer manager also clears its multimodal preprocess cache
  ([tokenizer control](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L301-L310),
  [scheduler invariant](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L4381-L4410)).
- `release_memory_occupation(tags)` and `resume_memory_occupation(tags)` fan
  out memory controls; the schema currently names `weights` and `kv_cache` as
  supported tags
  ([engine adapters](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1585-L1595),
  [schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1937-L1955)).
- `freeze_gc` first asks the scheduler/detokenizer path to freeze long-lived
  objects, then freezes tokenizer-side objects. Call it only after realistic
  warmup has created the long-lived graph of objects
  ([engine guidance](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1597-L1613),
  [manager dispatch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L2108-L2112)).
- profile and expert-distribution controls broadcast typed actions. Profile
  failures raise `RuntimeError`; expert record calls do not return per-rank
  results
  ([engine methods](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1320-L1340),
  [profile execution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L377-L419)).

`get_server_info` combines the resolved startup record, the first scheduler's
initialization facts, startup timings, live internal state from every
scheduler, and the package version. `get_model_info` is deliberately smaller
and reflects control-plane changes such as a new model path, load format,
weight version, or resolved parser
([server/model info](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1342-L1375)).

### Weight updates are serialized model mutations

The public weight paths cover disk, an external distributed group, in-memory
tensors, and checkpoint-engine IPC handles. Distributed group initialization
and destruction require either one DP replica or DP attention. The tokenizer
manager takes its model-update writer lock unless generation is already paused,
so a mutation cannot race ordinary request readers
([group and distributed methods](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1377-L1431),
[locking](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L421-L505)).

`update_weights_from_tensor` emits one serialized payload per TP rank. Ordinary
input tensors are serialized once for each rank; `load_format="flattened_bucket"`
expects caller-provided per-rank payloads and normalizes them instead. The
per-rank ownership prevents each receiver from deserializing and retaining all
other ranks' CUDA-IPC references
([serialization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1433-L1454),
[`_serialize_tensors_per_rank`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1497-L1513)).

Cache invalidation is the caller-visible invariant. `flush_cache=True` is the
safe default because KV and multimodal preprocess entries were produced by the
old weights. When deliberately batching multiple tensor/distributed/IPC
updates with flushing disabled, the caller must arrange one final successful
flush before trusting inference. Update results must also be inspected: these
methods return success information rather than uniformly raising on every
rank-side failure
([weight request schemas](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1736-L1854),
[tensor merge and cache clear](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L507-L540)).

Dynamic LoRA load/unload has both sync and async path-based methods; tensor
loading is synchronous at the engine surface. LoRA must be enabled at launch.
The tokenizer side serializes registry changes, registers only after all ranks
load successfully, waits for active users before unload, and may evict the
least-recently-used unpinned adapter at the configured capacity. Validation
failures are returned in typed outputs with `success=False`, so callers must
inspect the result instead of assuming lack of an exception means success
([engine LoRA methods](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1515-L1583),
[registry update path](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_control_mixin.py#L601-L783)).

### Raw collective RPC is deliberately sharp

`collective_rpc` bypasses the tokenizer-manager communicators. It sends a
method name and scalar keyword parameters on the rank-zero DEALER socket,
blocks without a method-level timeout, asserts the response type, and asserts
success. `save_remote_model` and `save_sharded_model` are only named wrappers
over that surface
([implementation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1616-L1629),
[wire schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L2196-L2204)).
Use typed control methods when one exists; this RPC requires rank-zero
tokenizer-side state and trusts that the target scheduler method agrees with
the flat parameter schema.

## 7. Shutdown is part of correctness

The engine is a context manager. `__enter__` returns the same object;
`__exit__` calls `shutdown` and returns `False`, so an exception from the body
is not swallowed
([context methods](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1271-L1276)).
Prefer:

```python
with sgl.Engine(model_path=model_path) as engine:
    output = engine.generate("Explain prefix caching briefly.")
```

Shutdown stops the child watchdog, closes the direct RPC socket with zero
linger, gracefully terminates engine-owned weight-cache daemons so they can
unlink their IPC files, kills and waits for remaining descendants, and closes
tokenizer-owned multimedia/CUDA-VMM transports in `finally`. It blocks until
the scheduler releases its device context so the caller can reallocate on the
same accelerator
([`shutdown`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1239-L1269)).

## Failure and invariant checklist

- Construct and use the public API on rank zero; nonzero nodes are runtime
  participants, not independent Python front ends.
- Use async methods inside a running event loop. Do not call a synchronous
  `run_until_complete` adapter from that loop without an explicit nesting
  strategy.
- Give executable scripts a `__main__` guard because child launch uses spawn.
- Treat request IDs as unique correlation keys. A duplicate batch ID or an ID
  already in flight is rejected.
- Treat `stream=True` as a different return type and merge deltas according to
  the configured streaming style.
- Keep `session_id` distinct from scheduler `session_params`; only the latter
  selects multi-turn history opened by `open_session`.
- Do not run cache flush or destructive control operations as if they were
  ordinary inference. Check typed success results and respect the idle/update
  locks.
- Flush inference caches after the final weight mutation unless the mutation
  workflow proves no stale cache entry can be reused.
- Inspect LoRA result objects for `success`; validation can be reported without
  raising.
- Close the engine explicitly or use the context manager. `atexit` is a final
  safety net, not a resource-lifetime plan.

## Study checks

1. Explain why eliminating HTTP does not eliminate ZMQ or subprocesses.
2. For a batched streaming request, identify where `index` is added and why
   chunks cannot be assumed to arrive in input order.
3. Trace one invalid over-context prompt and show where its request-state entry
   is removed.
4. Compare `encode`, `rerank`, and CausalLM `score` by request type and output
   semantics.
5. Explain why `apply_softmax=False` label scores need not sum to one.
6. Open a session on paper, then write the `session_params` needed to append a
   turn; explain why passing the returned ID as `session_id` is different.
7. Describe the lock and cache steps required for a safe multi-part tensor
   weight update.
8. List the resources released by `shutdown` and the reason the call blocks.
