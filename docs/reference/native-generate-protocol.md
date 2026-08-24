# Native `/generate`: File and Symbol Reference

This reference owns the Python native `/generate` handler, its header override
helper, complete text `SamplingParams`, request normalization and transport
schemas, tokenizer-side preparation/correlation, scheduler ingress/output
slices, the complete Python detokenizer, and focused tests. Large shared schema,
tokenizer, scheduler, and batch-state files remain partial outside the named
slices.

## `python/sglang/srt/entrypoints/http_server.py`

[`generate_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L889-L940)
registers both `POST` and `PUT`. It optionally applies header overrides before
branching on `stream`. The non-stream branch awaits the first result from the
manager iterator and returns it through SGLang's ORJSON response helper. The
stream branch frames each result as SSE, maps runtime `ValueError` to an in-band
native error, handles disconnect separately, appends `[DONE]` on ordinary
completion, and installs delayed abort cleanup.

[`abort_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1608-L1618)
is an administrative-optional control endpoint. Its HTTP 200 acknowledges
local dispatch only. [`_create_error_response`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2072-L2076)
is the smaller native error contract, distinct from OpenAI's typed error model.

The file remains **partial**: native generate/abort plus previously documented
startup, health, warmup, and lifecycle paths are covered; OpenAI, Anthropic,
Ollama, Vertex, tokenize/detokenize, sessions, and most management endpoints
retain their owning passes.

## `python/sglang/srt/entrypoints/request_headers.py`

[`_HEADER_OVERRIDES` and `apply_header_overrides`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/request_headers.py#L9-L33)
are the complete module. Eight case-insensitive HTTP headers can overwrite
request ID, prefill bootstrap coordinates, conversation ID, DP ranks, and
priority. String values are direct; integer values are cast and malformed
values become HTTP 400. There is no authentication or allowlist in this helper;
the endpoint/environment and deployment boundary must decide whether the
caller is trusted.

## `python/sglang/srt/managers/io_struct.py`

### Native request normalization

[`GenerateReqInput`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L162-L941)
is a mutable dataclass because normalization changes field shape in place. Its
method groups are:

| Methods | Responsibility |
| --- | --- |
| `regenerate_rid`, `_validate_rid_uniqueness` | New correlation IDs and within-batch uniqueness |
| `contains_mm_input` | Non-empty image/video/audio detection |
| `normalize_batch_and_arguments`, `_determine_batch_size` | Single/batch shape and compatibility checks |
| `_handle_parallel_sampling`, `_expand_inputs` | `n > 1` promotion/expansion |
| `_normalize_*` | IDs, LoRA, media/hashes, sampling, logprobs, hidden modes, processors, keys, disaggregation fields |
| `__getitem__` | Cached per-request projection from normalized batch state |

The three prompt fields are intended to be exclusive, but the implemented
boolean check permits exactly two. Cardinality normalization prefers text and
then IDs while clearing embeddings in either branch; later tokenization checks
embeddings, IDs, then text. The effective two-input outcomes are therefore IDs
over text and text-or-IDs over embeddings, with a potential text/ID cardinality
mismatch. Batch replication uses list multiplication; later code must copy
nested mutable transport objects before mutating them.

### Request and result transport schemas

[`TokenizedGenerateReqInput` and `BatchTokenizedGenerateReqInput`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L944-L1062)
are the tokenizer-to-scheduler records. They replace sampling dictionaries
with verified `SamplingParams`, use compact token arrays, attach processed
media/observability state, and preserve an HTTP-worker return route for
multi-tokenizer deployments.

[`BatchTokenIDOutput`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1397-L1494)
is the scheduler-to-detokenizer message. Its parallel arrays carry request IDs,
incremental decoding state, unsent output IDs, finish reasons, counts,
logprobs, optional sampling/hidden/expert data, cache/speculation metrics, DP
ranks, and time statistics.

[`BatchStrOutput`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1497-L1582)
is the detokenizer-to-tokenizer equivalent. It replaces incremental decode
inputs with text deltas and base64-encodes expert/indexer tensors, while most
other columns pass through unchanged. `BatchTokenIDOutput` also returns
directly when tokenizer initialization is skipped.

[`AbortReq`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1998-L2008)
serves both client-to-scheduler control and scheduler-to-tokenizer terminal
notification. Its compatibility hook converts missing `rid` to an empty
string, which makes the explicit empty-ID guard essential.

The file remains **partial**: native generation, major offline-control schemas,
and generation transport are covered; embedding, cache, disaggregation,
profiling, expert, weight, and other protocol records still need their owning
passes.

## `python/sglang/srt/sampling/sampling_params.py`

[`SamplingParams`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/sampling/sampling_params.py#L38-L254)
is a mutable array-like `msgspec.Struct`. Public fields describe length, stops,
temperature/top-k/top-p/min-p, penalties, `n`, grammar, detokenization, stream
interval, logit bias, seed, and JSON-safe custom parameters. Internal fields
hold normalized stop lists and their required decode-tail lengths.

`__post_init__` is deliberately idempotent after normalization. Before that it
implements null-as-default compatibility, stop alias copying, stop-token set
cleanup, empty-grammar removal, greedy conversion, and whole-vocabulary top-k
conversion. `verify` enforces finite ranges, length relations, vocabulary-safe
logit-bias keys, and at most one grammar constraint. It does not validate `n`.

[`normalize`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/sampling/sampling_params.py#L212-L254)
turns stop aliases into internal lists, computes tokenizer/regex buffer bounds,
rejects tokenizer-dependent features when no tokenizer exists, clears wire
aliases, and marks the record normalized.

[`get_max_seq_length` and `_max_length_from_subpattern`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/sampling/sampling_params.py#L227-L296)
walk Python's parsed regular-expression tree to find a conservative character
bound. Literals/classes/any add one, branches take their maximum, bounded
repeats multiply, unbounded or unknown tokens add a very large sentinel, and
zero-width assertions add nothing.

[`raise_if_tokenizer_required`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/sampling/sampling_params.py#L299-L332)
is the no-tokenizer compatibility gate for text/regex stops and minimum new
tokens. This completes the file.

## `python/sglang/srt/managers/tokenizer_manager.py`

### State and ingress

[`ReqState`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L216-L298)
owns one request's client-facing accumulation. Text chunks are joined lazily;
logprob and customized arrays grow incrementally; an event joins the shared
result loop to each request coroutine.

[`generate_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L767-L833)
is the shared native/offline ingress. Its exception cleanup is intentionally
broader than `Exception`: cancellation and other `BaseException` subclasses
must also remove precreated request states.

[`_init_req_state` and `_discard_pending_req_states`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L3358-L3415)
enforce in-flight ID uniqueness, initialize timing/tracing, and make partial
pre-dispatch failure cleanup idempotent.

### Preparation and dispatch

[`_tokenize_texts`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L835-L956)
distinguishes one string, a normal string batch, and embedding cross-encoder
pairs. Only one string can use the async dynamic-batching tokenizer.

[`_tokenize_one_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L958-L1126)
implements prompt precedence, skip-tokenizer errors, media deployment policy,
processor execution/transfer, external hash alignment, and final validation.
[`_validate_one_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1159-L1250)
owns raw context length, optional total budget, token-logprob, hidden-state, and
custom-processor gates.

[`_create_tokenized_object`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1333-L1447)
merges preferred sampling, injects strict-thinking budget, constructs and
validates `SamplingParams`, and maps the native object to scheduler transport.
[`_send_one_request` and `_send_batch_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1554-L1607)
prepare media transport, stamp timing and return routes, wrap pickle-only
fields, and cancel reservations if socket dispatch fails.

### Waiting, batches, streaming, and aborts

[`_wait_one_response`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1687-L1793)
periodically checks disconnect, atomically drains pending output, coalesces
incremental chunks, materializes cumulative text only when needed, logs final
results, translates abort status, and yields client-visible objects.

[`_handle_batch_request`, `_collect_batch_responses`, and
`_stream_batch_responses`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1795-L1943)
own optimized/sequential batch tokenization, the special prefix-warming `n > 1`
path, all-result collection, interleaved indexed streams, and sibling task
cleanup. The parallel-sampling ID/state mismatch described in the conceptual
guide remains a source-visible lifecycle gap.

[`abort_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1945-L1962)
guards the empty-prefix hazard and suppresses unknown IDs in single-tokenizer
mode. [`create_abort_task`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L2114-L2126)
builds the delayed streaming cleanup task.

[`handle_loop` and `_handle_batch_output`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L2153-L2461)
are the shared result pump and generation result shaper. They correlate by ID,
accumulate optional columns, choose text-versus-token output, implement
cumulative-versus-incremental stream semantics, update metrics, remove finished
state, and wake waiters. [`_handle_abort_req`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L3150-L3205)
is the direct abort-echo terminal path and tolerates completion races.

The file remains **partial**: native request preparation, correlation,
streaming, cancellation, output shaping, and previously documented offline
controls are covered; embedding-specific paths, parsers, session/control
details, multi-tokenizer internals, EPD encoding, elastic state, observability
export, and utility methods retain later passes.

## `python/sglang/srt/managers/scheduler.py`

[`process_input_requests`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L1910-L1943)
materializes media transport where required and dispatches typed requests.
[`handle_generate_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L2419-L2729)
is the native transport-to-scheduler-state boundary: it chooses ordinary or
session construction, validates disaggregation and optional-return modes,
expands media, initializes length/logprob state, and routes grammar or ordinary
queue admission. [`handle_batch_generate_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L2731-L2740)
deliberately loops through members rather than creating one inseparable
scheduler batch.

[`_add_request_to_queue`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L2788-L2810)
selects ordinary, prefill-disaggregated, or decode-disaggregated ownership.
[`abort_request`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L4572-L4729)
matches `rid` prefixes across chunked, waiting, grammar, disaggregation,
running, and transfer queues and releases the owning resources.

The file remains **partial**: this reference covers native request admission,
queue selection, and cancellation only. Scheduling policy, batch planning,
cache ownership, worker execution, result processing, distributed modes, and
the large control surface remain.

## `python/sglang/srt/managers/schedule_batch.py`

[`Req`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/schedule_batch.py#L816-L1034)
is the scheduler-owned mutable form of one generation. The native path relies
on its original input, sampling, optional returns, routing/cache/session
identity, token/output offsets, finish state, media data, and request timing.

[`output_ids_through_stop`, `finished`, and incremental-detokenize
state](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/schedule_batch.py#L1227-L1289)
bound emitted tokens and expose completion. [`init_incremental_detokenize`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/schedule_batch.py#L1428-L1446)
maintains a surrounding prefix so subword decoding can advance safely.

[`update_finish_state`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/schedule_batch.py#L1632-L1672)
prioritizes an explicit deferred finish, invalid-vocabulary defense, string or
regex stop, token/EOS stop, length, then grammar termination. This ordering
prevents speculative multi-token acceptance from leaking tokens past a stop or
the length cap.

The file is **partial**: native request identity, finish, stop, and
detokenization-offset slices are covered; the rest of request/batch cache,
memory-pool, model-input, overlap, speculative, and disaggregation state
remains for scheduling passes.

## `python/sglang/srt/managers/scheduler_components/output_sender.py`

[`SenderWrapper`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler_components/output_sender.py#L8-L29)
is the complete file. It no-ops when no output socket exists, otherwise stamps
a missing `BaseReq.http_worker_ipc` from the scheduler request before sending.
It never overwrites an explicit destination. Batch generation output already
carries per-item routes and bypasses this scalar stamping branch.

## `python/sglang/srt/managers/scheduler_components/output_streamer.py`

[`SchedulerOutputStreamer`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler_components/output_streamer.py#L45-L304)
selects generation versus embedding output, computes cache details, calls the
generation accumulator, validates optional subclass data alignment, and sends
to Python detokenization or Rust egress. Embedding output is final-only and
optimizes pooled hidden-state tensors by stacking compatible rows.

[`_GenerationStreamAccumulator`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler_components/output_streamer.py#L307-L729)
is a columnar payload builder. `accept` decides whether each request should
emit, advances all send offsets, slices tokens and optional metadata in lockstep,
marks finished output exactly once, and handles stop-limited/speculative result
lengths. `to_payload` creates `BatchTokenIDOutput`, keeping optional flat
logprob columns absent on the common path. Rust egress uses a smaller subset
and skips Python-only detokenization bookkeeping. This completes the file.

## `python/sglang/srt/managers/detokenizer_manager.py`

[`DecodeStatus`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L64-L89)
stores accumulated decode IDs, surrounding/read/sent offsets, and lazily joined
text. [`DetokenizerManager` initialization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L92-L175)
owns ZMQ endpoints, tokenizer construction, bounded state, watchdog/metrics,
typed dispatch, and ordinary event-loop forwarding.

[`trim_matched_stop`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L177-L207)
removes or retains the matched stop while always discarding speculative tokens
after it. The GPT-OSS tool-call token is retained even though it is also EOS.
[`_clamp_decode_ids` and `_grouped_batch_decode`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L213-L289)
make placeholder/hash IDs safe and group compatible fast-tokenizer rows while
preserving empty positions.

[`_decode_batch_token_id_output`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L291-L410)
does incremental surrounding/read decode, printable-text recovery, sent-offset
deduplication, final stop trim, bounded-state failure reporting, and state
deletion. [`handle_batch_token_id_out`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L431-L488)
builds the pass-through `BatchStrOutput` and base64-encodes tensor metadata.

[`run_detokenizer_process`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L516-L539)
publishes role-local configuration, selects ordinary versus multi-HTTP-worker
loop, reports fatal exceptions, clears dynamic sockets, and signals the parent.
Embedding batches bypass decoding unchanged. The local
`is_health_check_request` prefix helper has no call sites in the tracked Python
snapshot; similarly named encoder-disaggregation helpers are separate. The
small GC/logging handlers perform their named process-local controls, and
`LimitedCapacityDict` evicts the oldest state before inserting past its
configured capacity
([remaining handlers and helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L209-L213),
[process-local helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L488-L513)).
This completes the file.

## Focused tests

### Fully covered tests

- [`test/registered/cpu/test_request_headers.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/cpu/test_request_headers.py#L1-L109): every header, absence, partial override, body precedence, signed priority, and malformed integer case.
- [`test/registered/unit/sampling/test_sampling_params.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/sampling/test_sampling_params.py#L1-L539): all constructor conversions, verification boundaries, stop normalization, copy/msgpack behavior, and regex-bound cases.
- [`test/registered/unit/managers/test_tokenizer_manager_rid_cleanup.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/managers/test_tokenizer_manager_rid_cleanup.py#L1-L617): abort/completion/pre-dispatch cleanup, duplicate/resubmit behavior, sibling waiter cancellation/closure, and strict-thinking gating.
- [`test/registered/unit/managers/scheduler_components/test_output_sender.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/managers/scheduler_components/test_output_sender.py#L1-L63): explicit route preservation and scheduler abort routing to the originating tokenizer worker.
- [`test/registered/unit/managers/test_trim_matched_stop.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/managers/test_trim_matched_stop.py#L1-L68): no-match, string/token trim/retain, speculative tail, and GPT-OSS exception behavior.
- [`test/registered/unit/managers/test_customized_info_streaming.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/managers/test_customized_info_streaming.py#L1-L172): real Engine/scheduler alignment of custom token metadata for final results and incremental intervals.
- [`test/registered/scheduler/test_abort_with_metrics.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/scheduler/test_abort_with_metrics.py#L1-L79): the pure ASGI middleware preserves `receive`, allowing `Request.is_disconnected()` to observe both connected and disconnected messages. The filename is historical; it does not test metrics.
- [`test/manual/entrypoints/http_server/test_abort_request.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/entrypoints/http_server/test_abort_request.py#L1-L205): explicit non-stream abort and selective abort among three concurrent requests; this is manual GPU integration, not disconnect simulation.
- [`test/registered/npu/interface/test_npu_api_abort_request.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/npu/interface/test_npu_api_abort_request.py#L1-L78): Ascend-specific long-generation/abort concurrency. It has no assertions and only prints one response, so it is a smoke harness rather than a behavioral proof.

### Partial test files

- [`test/registered/unit/managers/test_io_struct.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/managers/test_io_struct.py#L43-L1112): generation message round trips and every `GenerateReqInput` normalization case are covered; embedding-only split behavior and generic tensor-extension details retain their broader IPC/embedding passes.
- [`test/registered/core/test_srt_endpoint.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/core/test_srt_endpoint.py#L40-L719): native generate logprob, custom processor, cache-count, logit-bias, and related Python/Rust reuse are covered. Server-info/startup, tokenize/detokenize routes, and the full Rust egress contract retain later passes. `test_logprob` itself prints without assertions; stronger neighboring tests carry the guarantees.
- [`test/registered/openai_server/validation/test_request_length_validation.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/validation/test_request_length_validation.py#L108-L170): native flat/nested/out-of-vocabulary token-logprob cases are covered; OpenAI prompt/maximum-token validation remains with that adapter.
- [`test/registered/scheduler/test_scheduler_control.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/scheduler/test_scheduler_control.py#L130-L208): sequential ID reuse, concurrent duplicate rejection, duplicate batch rejection, and post-error server health are covered; pause/continue and other scheduler controls remain.

### Missing combinations

There is no focused native HTTP test for cumulative versus incremental SSE,
in-band stream errors, client-close cancellation, or combined batch plus
parallel sampling. The `n > 1` parent/choice state and abort-ID relationship is
therefore source-audited here but not proven by a regression test.
