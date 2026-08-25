# Native gRPC Python Bridge File Reference

This reference supports [Native gRPC and the Python Runtime
Bridge](../13-native-grpc-python-bridge.md). It fully covers the in-tree runtime
protobuf, Python `RuntimeHandle`, and focused Python unit test. Rust and other
gRPC files are linked only to define the Python-facing boundary; their complete
implementation, build, and test passes remain later work. The [coverage
inventory](../coverage/README.md) is authoritative.

## Shared runtime schema

<a id="protosglangruntimev1sglangproto"></a>

### `proto/sglang/runtime/v1/sglang.proto`

**Status: covered.** This is the full wire contract compiled by the native
Rust extension. `SglangService` declares 25 operations: 16 typed native
inference/control RPCs, six OpenAI JSON pass-through RPCs, and three admin RPCs
([service](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L1-L35)).

| Lines | Messages | Contract |
| --- | --- | --- |
| [37-49](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L37-L49) | `DisaggregatedParams` | Prefill/decode KV rendezvous host, port, and 64-bit room ID. |
| [51-84](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L51-L84) | `SamplingParams`, `GuidedDecoding`, `ChoiceConstraint` | Optional filters, penalties, budget, stops, `n`, seed, deprecated direct JSON/regex, and exactly one modern grammar constraint. |
| [86-139](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L86-L139) | text/token generate requests and responses | Text or token input; shared routing/session/tracing/disaggregation/priority/reasoning controls; streamed text or token output plus string metadata and terminal bit. |
| [141-167](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L141-L167) | text/token embedding | Text or token input, RID/routing/tracing, dense float output, and metadata. |
| [169-203](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L169-L203) | health, model info, server info, abort | Empty probes, JSON information envelopes, and single/all request cancellation. |
| [205-218](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L205-L218) | classification | Text and/or token IDs mapped to the shared embedding path; float result retains the historical `embedding` field name. |
| [220-265](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L220-L265) | tokenize, detokenize, models, load | Local tokenizer shapes, one base/LoRA model-card list, and opaque JSON load information. |
| [267-290](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L267-L290) | cache flush, pause, continue | Small success/message control responses. |
| [292-307](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L292-L307) | OpenAI pass-through | Raw JSON request bytes and trace headers; streamed payload bytes or unary bytes plus HTTP-like integer status. |
| [309-335](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L309-L335) | profile and weight update | Optional profile output directory, model/load-format update, and message/success responses. |

The schema alone does not validate semantic combinations. Rust rejects empty
classification input, invalid guided constraints, negative detokenize IDs,
and empty single-request aborts; Python SRT performs the remaining native
request validation. `meta_info` is a string map whose values contain
JSON-encoded representations, not necessarily human-readable strings.

## Python runtime bridge

<a id="pythonsglangsrtentrypointsgrpc_bridgepy"></a>

### `python/sglang/srt/entrypoints/grpc_bridge.py`

**Status: covered.** The entire module is the synchronous-PyO3 to
async-tokenizer-manager adapter.

| Lines | Symbols | Responsibility |
| --- | --- | --- |
| [28-57](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L28-L57) | `_BadOpenAIRequest`, `_CaseInsensitiveHeaders`, `_GrpcRequest` | Distinguish non-object JSON, provide case-insensitive trace headers, mutable request state, and optional non-ASGI disconnect polling. |
| [60-89](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L60-L89) | `RuntimeHandle.__init__`, `_tm_loop` | Retain managers/config, ensure the tokenizer handle loop exists, and capture its event loop. |
| [91-158](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L91-L158) | callback/status helpers, `_send_with_backpressure` | Contain callback exceptions; detect Rust enum statuses; abort batch/single native RIDs on a 300-second pending-send timeout. |
| [160-200](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L160-L200) | ready registration, `_submit_on_tm_loop`, future logger | Bridge a Rust-thread ready edge into asyncio, clear it, schedule coroutines thread-safely, and surface otherwise unobserved failures. |
| [202-229](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L202-L229) | `_submit_json_unary` | Run one async control operation, JSON-encode its terminal result, and signal errors. |
| [231-265](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L231-L265) | `_get_openai_serving` | Lazily instantiate/cache the six existing OpenAI serving adapters. |
| [267-296](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L267-L296) | `submit_request` | Materialize `GenerateReqInput` or `EmbeddingReqInput`; reject unknown request families; schedule the correct native coroutine. |
| [298-351](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L298-L351) | `_run_generate` | Stream choice-aware native results with backpressure, emit every full-result item, synthesize missing terminal output, close the generator, and clear readiness. |
| [353-362](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L353-L362) | `_run_embed` | Consume one embedding/classification result and issue a terminal callback or error. |
| [364-400](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L364-L400) | `abort`, `_abort_async` | Abort directly on the tokenizer loop or bridge synchronously from Rust with a five-second bound. |
| [402-478](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L402-L478) | info, health, tokenizer, model methods | Serialize effective model/server state, expose status, provide Python tokenizer fallback, and list base plus LoRA models. |
| [480-561](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L480-L561) | load/cache/pause/profile/weight controls | Convert each RPC to its tokenizer-manager method and one JSON terminal result. |
| [563-693](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L563-L693) | OpenAI submitters and request-class map | Select streaming versus unary callback convention and pair six RPCs with ordinary Pydantic request classes. |
| [695-816](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L695-L816) | `_run_openai_request` | Decode/validate JSON, construct the request shim, reuse serving handlers, deframe SSE with backpressure, serialize unary results, and distinguish stream from unary errors. |

The essential invariant is that no async inference/control work runs on the
Tonic thread. Synchronous methods either return small local data or enqueue a
coroutine on the tokenizer-manager loop. Stream producers must honor the Rust
callback's `Pending` status; one extra callback while Rust has a parked send is
a channel-contract failure.

Non-streaming generation consumes one native final result but expands a list
into separate callbacks, marking only the last terminal. Streaming completion
tracks distinct finished choices against `sampling_params.n`. The module uses
`meta_info.finish_reason` as the per-choice terminal signal, not iterator
exhaustion alone.

The native generation path closes its generator in `finally`. The unary embed
path takes only the first item, does not install readiness, ignores callback
status, and has no explicit `aclose`. OpenAI deframing clears readiness in
`finally` but assumes iterator chunks do not split inside an SSE line.

The current Rust caller does not supply the optional disconnect function.
Native transport cancellation instead comes from the Rust response-stream
abort guard. Callback exceptions return `None`; native/OpenAI producers stop,
but an exception that did not also close the Rust channel can leave final
cleanup to the Rust response timeout.

Validation asymmetry is deliberate but worth testing: malformed JSON objects
and Pydantic errors are 400-equivalent for unary OpenAI RPCs, while stream RPCs
become gRPC errors. Invalid UTF-8 is handled by the outer unexpected-error path.
Structured JSON from failed unary controls is discarded because Rust gives the
callback's `error` argument precedence.

## Focused unit test

<a id="testregisteredunitentrypointstest_grpc_bridgepy"></a>

### `test/registered/unit/entrypoints/test_grpc_bridge.py`

**Status: covered.** The file registers a one-second CPU test, defines a
three-state callback enum, a recording callback that always returns `Ready`, a
fake tokenizer manager yielding fixed responses, and a helper that bypasses
the real `RuntimeHandle` constructor
([fixtures](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/test_grpc_bridge.py#L1-L43)).

`test_non_streaming_returns_every_choice_before_finishing` supplies one final
two-choice list and asserts both output-ID arrays are emitted with terminal
flags `[False, True]`
([test](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/test_grpc_bridge.py#L46-L68)).
`test_streaming_first_finished_choice_is_not_batch_terminal` emits an open
choice 0, terminal choice 0, then terminal choice 1 for `n=2`; it asserts all
three outputs survive and only the last callback is terminal
([test](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/test_grpc_bridge.py#L70-L111)).

No test in this file covers the constructor, thread-safe submission, request
record construction, embedding, callback failure, `Pending`/`Closed`, ready
edges, timeout/abort, info/control methods, OpenAI JSON/SSE, PyO3 channels,
protobuf mapping, or live Tonic transport. Direct execution in the study
environment stops during package import because `orjson` is absent, before
either registered test runs.

## Shared and Rust boundary files

<a id="pythonsglangsrtentrypointshttp_serverpy-native-grpc-slice"></a>

### `python/sglang/srt/entrypoints/http_server.py` — native gRPC slice

**Status: partial.** The lifecycle starts native gRPC only for a single
tokenizer when `grpc_port` is set and legacy mode is not selected. It starts an
optional managed sidecar after gRPC, then shuts the sidecar and native server
down in `finally`
([lifecycle](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L389-L426)).
The helper loads the extension, constructs `RuntimeHandle`, passes host, port,
and effective worker count, and returns the shutdown handle
([helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2729-L2764)).
All previously listed HTTP responsibilities and remaining adapters keep the
whole file partial.

<a id="rustsglang-grpcsrclibrs-python-boundary"></a>

### `rust/sglang-grpc/src/lib.rs` — Python startup boundary

**Status: partial.** Lines
[141-265](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/lib.rs#L141-L265)
explain the Python-callable startup/shutdown contract: validate/bind, normalize
workers/channel/timeout, optionally load a Rust tokenizer, create Tokio and
`PyBridge`, spawn the server thread, and export `start_server`, handle, and
callback-status types. Tokenizer-info extraction and the complete Rust
extension test/build audit remain assigned to the Rust pass.

<a id="rustsglang-grpcsrcbridgers-python-boundary"></a>

### `rust/sglang-grpc/src/bridge.rs` — Python callback boundary

**Status: partial.** This guide covers the response record/status types and
bounded per-RID state
([types](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L13-L95)),
native submission and abort
([submission](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L133-L264)),
OpenAI/control callback invocation
([control and OpenAI](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L318-L450)),
and the ready/backpressure/callback mechanics
([backpressure](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L452-L804)).
The Rust-internal audit and tests remain later work.

<a id="rustsglang-grpcsrcserverrs-python-boundary"></a>

### `rust/sglang-grpc/src/server.rs` — Python bridge boundary

**Status: partial.** The covered slice explains Python exception status
mapping, response timeout, drop-triggered abort, terminal-channel errors
([common lifecycle](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L60-L215)),
native generation/embed/classify calls
([inference](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L218-L470)),
Python tokenizer and control results
([local/control](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L473-L735)),
and OpenAI JSON plus listener boundaries
([OpenAI and listener](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L736-L1008)).
The full Rust per-RPC review and unit test audit remain pending.

<a id="rustsglang-grpcsrcutilsrequest_utilsrs-python-boundary"></a>

### `rust/sglang-grpc/src/utils/request_utils.rs` — request-map boundary

**Status: partial.** The Python-facing conversion is covered: sampling and
guided constraints, generation controls, tracing/disaggregation flattening,
received timestamp, and text/token generation plus embed/classify dictionaries
([mapping](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/utils/request_utils.rs#L1-L371)).
Its embedded Rust unit module and integration with the rest of the crate retain
the dedicated Rust pass.

`grpc_server.py`, `entrypoints/sidecar.py`, the EPD encoder server, the model
gateway gRPC router, and the experimental KV indexer are mapped conceptually in
the main guide but remain `pending`; a boundary mention is not complete file
coverage.
