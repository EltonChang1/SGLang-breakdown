# Native gRPC and the Python Runtime Bridge

SGLang's native gRPC endpoint is an **additional transport around the existing
Python SRT runtime**, not a second inference engine. A Rust/Tonic server accepts
the wire protocol on its own thread, converts requests to ordinary SRT request
dictionaries, and calls `RuntimeHandle`. That Python handle schedules all
asynchronous work onto the already running `TokenizerManager` event loop and
pushes result chunks back through bounded Rust channels
([Python bridge](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L1-L84),
[Rust startup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/lib.rs#L141-L257)).

This guide completes the Python request bridge and its focused unit test. It
also maps the surrounding gRPC systems so readers do not combine incompatible
schemas, launch modes, or ownership boundaries. The Rust extension, standalone
SMG server, model gateway, and encoder transport still retain dedicated later
passes; their Python-facing edges are explained here only where the bridge
depends on them. The [file and symbol
reference](reference/native-grpc-python-bridge.md) records that coverage line.

## Recommended study order

1. Revisit [Configuration and Startup](02-configuration-and-startup.md) and
   the [Native `/generate` Protocol](07-native-generate-protocol.md).
2. Separate the five gRPC meanings in the source tree before following any
   call named `grpc`.
3. Read the shared runtime protobuf as the wire contract.
4. Trace one typed `Generate` request through Rust, `RuntimeHandle`, and the
   ordinary tokenizer manager.
5. Study callback status and backpressure before cancellation and errors.
6. Compare typed native RPCs with JSON pass-through OpenAI RPCs.
7. Finish with info/control operations and the focused multi-choice tests.

## Five distinct gRPC boundaries

| Boundary | Launch or owner | Protocol and purpose | Relationship to this guide |
| --- | --- | --- | --- |
| Native in-process gRPC | `--grpc-port` or `SGLANG_GRPC_PORT`; Rust extension beside Python HTTP | `proto/sglang/runtime/v1/sglang.proto`; native inference, OpenAI JSON pass-through, and controls | Primary subject; `RuntimeHandle` is fully covered here. |
| Legacy SMG server | `--smg-grpc-mode`, or deprecated `--grpc-mode`; replaces default HTTP | External `smg-grpc-servicer`, with a small in-tree aiohttp metrics/profile sidecar | Different server and external schema; only its dispatch boundary is mapped. |
| Model gateway gRPC client/router | `sgl-model-gateway` | External `smg-grpc-client` worker protocol, regular/PD routing, Harmony and response shaping | A router in front of workers, not the in-process runtime bridge. |
| EPD encoder gRPC | `--encoder-only --grpc-mode` | External `smg_grpc_proto` encoder service; image encode/send/rendezvous transport | Separate multimodal encoder runtime; not text generation and not this protobuf. |
| Experimental KV indexer | `experimental/sgl-router/sgl-kv-indexer` | `kv_indexer.proto`; KV index updates and lookup contract | Separate experimental routing/index service for a later Phase 8 pass. |

The top-level dispatcher makes the first two differences explicit. Encoder-only
legacy gRPC selects the encoder server; ordinary `smg_grpc_mode` selects the
standalone external server; otherwise the default HTTP launch continues. The
native server is started *inside* that default HTTP lifecycle when `grpc_port`
is set
([dispatch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/launch_server.py#L16-L57),
[HTTP lifecycle](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L389-L426)).

Do not infer compatibility from the transport name alone. The model gateway
imports its worker records from `smg_grpc_client`, while the native extension
compiles the in-tree runtime protobuf. The encoder imports another external
encoder protobuf and restricts its encode path to image modality
([gateway imports](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/sgl-model-gateway/src/routers/grpc/mod.rs#L1-L23),
[encoder imports and service](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/disaggregation/encoder/grpc_server.py#L17-L87)).

## Native launch topology

`--grpc-port` means “bind native gRPC beside HTTP.” It does not redirect the
HTTP port and does not construct another `TokenizerManager`. Resolution rejects
Ray, encoder-only mode, multiple tokenizer workers, and HTTP/API admin keys;
the last constraint exists because the gRPC listener does not run through HTTP
authentication middleware. The gRPC and HTTP ports must differ
([resolution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L4412-L4484),
[port validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L9982-L9991)).

```text
process hosting FastAPI and TokenizerManager
  |
  +-- HTTP/ASGI event loop --------> TokenizerManager event loop
  |
  +-- Rust extension
        +-- OS thread "sglang-grpc"
        +-- Tokio worker runtime
        +-- Tonic SglangService
        +-- per-RID bounded response channel
                  |
                  | short PyO3/GIL calls
                  v
              RuntimeHandle
                  |
                  | run_coroutine_threadsafe(...)
                  v
              same TokenizerManager event loop
                  |
                  v
        scheduler -> detokenizer -> result dictionary
```

The HTTP lifecycle loads `sglang.srt.rust_extensions._grpc`, constructs one
`RuntimeHandle`, and passes it to `start_server`. Shutdown calls the returned
Rust handle before the HTTP application finishes cleanup
([assembly](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2729-L2764)).
The Rust extension binds the listener before spawning its thread, optionally
loads a Rust tokenizer, builds a multithreaded Tokio runtime, and retains the
Python object in `PyBridge`
([extension startup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/lib.rs#L152-L257)).

An optional `--sidecar` is yet another process. SGLang spawns an importable
module with a `main(argv)` function and gives it a loopback native endpoint in
`SGLANG_GRPC_ENDPOINT`. It is a managed client of native gRPC, not the legacy
SMG server's aiohttp metrics sidecar
([sidecar lifecycle](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/sidecar.py#L30-L132)).

## Wire contract

The `SglangService` protobuf declares 25 RPCs in three families
([service](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L1-L35)):

| Family | RPCs | Wire strategy |
| --- | --- | --- |
| Typed native inference and controls | `TextGenerate`, `Generate`, `TextEmbed`, `Embed`, `Classify`, `Tokenize`, `Detokenize`, `HealthCheck`, `GetModelInfo`, `GetServerInfo`, `ListModels`, `GetLoad`, `Abort`, `FlushCache`, `PauseGeneration`, `ContinueGeneration` | Protobuf fields become native SRT requests or local/control calls. Generate responses are server streams even when the request's `stream` flag is false. |
| OpenAI-compatible | `ChatComplete`, `Complete`, `OpenAIEmbed`, `OpenAIClassify`, `Score`, `Rerank` | The protobuf carries raw JSON bytes plus trace headers. Chat/completion return a stream of deframed JSON payloads; the four others return JSON bytes and an HTTP-like status integer. |
| Admin | `StartProfile`, `StopProfile`, `UpdateWeightsFromDisk` | Typed protobuf inputs reach tokenizer-manager communicators; small JSON bridge results are parsed back into typed responses. |

`TextGenerate` supplies prompt text and returns text; `Generate` supplies token
IDs and returns token IDs. They share sampling, routing, session,
prefill/decode-rendezvous, priority, and reasoning controls
([text request](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L37-L112),
[token request](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L114-L139)).
Sampling exposes the common scalar filters, stops, `n`, seed, and one guided
constraint. The older top-level `json_schema` and `regex` fields are deprecated
in favor of the `GuidedDecoding` oneof
([sampling schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/proto/sglang/runtime/v1/sglang.proto#L51-L84)).

The Rust request mapper performs the protobuf-to-SRT name conversion. For
example, protobuf `seed` becomes `sampling_seed`; guided choices become an
escaped noncapturing regex; trace headers become `external_trace_header`; and
the three disaggregation fields become the flat bootstrap fields expected by
`GenerateReqInput`. It also stamps `received_time` at the Rust ingress
([sampling conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/utils/request_utils.rs#L19-L128),
[text mapping](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/utils/request_utils.rs#L202-L258),
[token mapping](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/utils/request_utils.rs#L260-L312)).

The response `meta_info` fields are `map<string,string>`. Rust therefore JSON
encodes every Python metadata value into the string value; callers must parse a
value again to recover numbers, booleans, arrays, or nested objects
([metadata extraction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L788-L804)).

## Crossing from Rust into the tokenizer loop

`RuntimeHandle.__init__` stores the tokenizer/template managers and effective
server information, asks the tokenizer manager to create its handle loop if
needed, and captures that loop. Its public submission methods are synchronous
because Rust calls them while briefly holding the GIL. They never run model
work in the Tonic worker: `_submit_on_tm_loop` uses
`asyncio.run_coroutine_threadsafe` and attaches a done callback so an otherwise
lost coroutine exception is logged
([construction and scheduling](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L60-L89),
[submission helper](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L187-L229)).

The native request dispatcher accepts only `req_type="generate"` and
`req_type="embed"`. It constructs `GenerateReqInput` or `EmbeddingReqInput`
from the Rust-built dictionary on the calling thread, then schedules the
corresponding coroutine. Classification deliberately arrives as `embed`
because the internal classification path uses `EmbeddingReqInput`
([Python dispatch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L267-L296),
[Rust classify handoff](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L431-L470)).

The constructor is outside the scheduled coroutine, so request-record type
errors can propagate immediately through PyO3 and become `INVALID_ARGUMENT` or
`INTERNAL` according to the Rust exception mapper. Errors after scheduling are
instead sent through the response callback
([Rust error mapping](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L60-L76)).

## Typed generation flow

For a native generation request:

1. Tonic chooses or creates an RID and Rust maps protobuf fields into an SRT
   dictionary.
2. `PyBridge` creates a bounded channel keyed by RID. Duplicate active RIDs
   fail before Python work starts.
3. Rust converts the dictionary to a Python dict and calls
   `RuntimeHandle.submit_request` with a PyO3 `ChunkCallback`.
4. Python constructs the SRT request and schedules `_run_generate` on the
   tokenizer-manager loop.
5. The ordinary `TokenizerManager.generate_request` path normalizes,
   tokenizes/prepares media, dispatches to schedulers, correlates output, and
   yields native result dictionaries.
6. Python invokes the callback with each result and a transport-level
   `finished` flag. Rust extracts only `text`, `output_ids`, `embedding`, and
   `meta_info` into its response-channel record.
7. Tonic turns channel records into streamed protobuf responses. Its abort
   guard remains armed until a terminal record is observed.

The channel creation and PyO3 call are in `PyBridge.submit_request`
([submission](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L133-L209));
the Python generation loop is `_run_generate`
([loop](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L298-L351));
and the typed callback extracts the result subset
([callback](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L612-L697)).

### Non-streaming still uses a streamed RPC

When the request's SRT `stream` value is false, Python asks the native
generator for its first final result. That result may be a list—batch or
parallel-choice output—so the bridge emits every element and marks only the
last callback terminal. It does not collapse choices into one protobuf message
([non-stream branch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L330-L344)).

This is why a nominally non-streaming `Generate` RPC can yield more than one
`GenerateResponse`: protobuf server streaming represents transport
cardinality, while the request flag controls native incremental output.

### Streaming completion is choice-aware

For native streaming, one choice finishing must not close an `n > 1` request.
The bridge reads `n` from the request sampling dictionary, tracks terminal
choice identifiers from `chunk.index` or `meta_info.id`, and marks the callback
finished only after all expected choices have reported a non-null native
finish reason. If the generator exits without such a terminal chunk, it emits
an empty defensive terminal record
([choice tracking](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L304-L329)).

The invariant assumes a stable, distinct `index` or metadata ID for every
choice. A malformed producer that repeats an identifier can leave the count
short and fall into the empty defensive terminal path instead of identifying
which choice was missing.

## Backpressure and channel ownership

Each Rust response channel defaults to capacity 64. Callback invocation
returns one of three statuses:

| Status | Meaning for Python |
| --- | --- |
| `Ready` | The chunk entered the channel; production may continue. |
| `Pending` | The channel was full; Rust parked exactly one chunk in an async send. Python must await the ready edge before invoking the callback again. |
| `Closed` | The receiver/client is gone or the channel contract has failed; stop producing. |

Rust permits only one parked send per RID. A second callback while that parked
send is pending closes the channel as `RESOURCE_EXHAUSTED`, which is why the
Python wait is a correctness requirement rather than an optimization
([bounded send](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L527-L610)).

Before producing a stream, Python registers an `on_ready` callback. Rust can
invoke it from a Tokio thread, so the callback uses
`loop.call_soon_threadsafe(ready_event.set)` rather than touching the asyncio
event directly. Rust also remembers an early ready edge so registration cannot
miss a parked chunk that drained first
([Python registration](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L160-L185),
[Rust edge handoff](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L479-L525)).

`_send_with_backpressure` invokes the callback first. `None`—including a
callback exception caught by `_safe_callback`—and `Closed` stop the caller.
`Pending` waits up to 300 seconds unless the chunk is already terminal. A
native timeout aborts the request RID or every RID in a normalized batch; an
OpenAI pass-through timeout merely closes that stream because the helper is not
given an SRT RID
([send helper](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L91-L158)).

Terminal parked chunks need no later ready signal: the producer contract is
over and Rust removes the channel after the send drains. Python always clears
the installed callback in `finally`, and native generation explicitly closes
its async generator
([Python cleanup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L343-L351),
[terminal send](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L565-L579)).

Embedding is unary and does not install this protocol. `_run_embed` takes the
first native item, invokes one terminal callback, and translates an empty
iterator or exception into a terminal record. It neither checks the callback
status nor explicitly closes the async generator; the contract relies on one
embedding result and Rust's receiver cleanup
([embedding bridge](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L353-L362)).

## Cancellation and timeouts

The Rust Tonic stream owns client-lifetime cancellation. Its
`RequestAbortGuard` calls `PyBridge.abort` when a response stream is dropped,
times out, or closes before a terminal response. The bridge removes the RID's
channel first and calls Python `RuntimeHandle.abort`, which enqueues the normal
tokenizer-manager abort
([abort guard](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L78-L140),
[channel abort](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L212-L264)).

`RuntimeHandle.abort` must work from two contexts. If already on the tokenizer
loop, it calls `abort_request` directly. Otherwise it schedules `_abort_async`
thread-safely and blocks the calling Rust worker for at most five seconds. A
timeout is logged and dropped rather than deadlocking the handler thread
([Python abort](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L364-L400)).

This gives two distinct limits: the Rust response wait and Python backpressure
wait default to 300 seconds, while the cross-thread abort acknowledgement is
bounded at five seconds. An `AbortResponse.success=true` means the bridge
accepted and invoked the abort path; as with the HTTP abort API, it is not proof
that every scheduler rank has already stopped work.

The optional `is_disconnected_fn` hook in `_GrpcRequest` can make existing
OpenAI/tokenizer code observe a non-ASGI client. The current Rust
`submit_request` and `submit_openai` calls do not pass that hook, so live native
gRPC cancellation is supplied by the Rust abort guard instead
([request shim](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L32-L57),
[current OpenAI call](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L414-L437)).

## OpenAI JSON pass-through

The six OpenAI RPCs deliberately reuse the existing Python serving adapters.
On first use, `RuntimeHandle` constructs and caches chat, completion,
embedding, classify, score, and rerank serving objects around the same managers
([lazy serving map](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L231-L265)).

For every call, the bridge:

1. decodes the protobuf `json_body` as a JSON object;
2. validates it with the endpoint's ordinary Pydantic request class;
3. builds a minimal request shim with case-insensitive trace headers, mutable
   `state`, and optional disconnect polling;
4. invokes the existing adapter's `handle_request`; and
5. converts the returned model/response or deframes its SSE body.

Malformed JSON, a non-object top level, and Pydantic validation failures become
BadRequest JSON. Unary RPCs retain that body with status 400; streaming
chat/completion send an error callback, which Rust converts to a gRPC error
instead of an `OpenAIStreamChunk`
([validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L695-L734),
[JSON callback error precedence](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/bridge.rs#L721-L768)).

### SSE becomes payload chunks, not SSE

If the serving result has `body_iterator`, the bridge parses SSE lines. It
ignores comments and non-`data:` fields, joins consecutive data values with a
newline, skips `[DONE]`, and sends each blank-line-delimited event's payload as
one protobuf `json_chunk`. After iteration it sends an empty terminal chunk
([deframing loop](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L736-L781)).

Clients must therefore not expect `data:`, blank-line framing, comments, event
names, or the `[DONE]` sentinel inside `json_chunk`; `finished` is the transport
terminator.

The parser assumes each iterator chunk is line-aligned. It retains complete
`data:` values across lines but has no partial-line carry buffer. A body
iterator that splits one `data:` line across two chunks can produce truncated
JSON or drop the second fragment. Existing SGLang streaming helpers generally
yield complete events, but the bridge itself does not enforce that invariant.

For non-stream results, Pydantic models are dumped to JSON, response objects
reuse their body, dictionaries/lists are encoded, and other values become
text. `status_code` or `code` is forwarded when available, otherwise 200 is
used. Unexpected failures become gRPC stream errors for chat/completion and
HTTP-like status payloads for unary OpenAI RPCs
([full response and errors](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L782-L816)).

Invalid UTF-8 in `json_body` is not among the inner BadRequest exceptions; it
falls to the outer unexpected-error path and is reported as a server failure
rather than a 400-equivalent validation error.

## Information and control plane

The small synchronous methods return JSON strings for Rust to parse:

| Python method | Source of truth and important boundary |
| --- | --- |
| `get_model_info` | Live tokenizer-manager identity/config values, runtime tokenizer path, model architecture, and resolved embedding plan. |
| `get_server_info` | `server_args` dataclass plus scheduler initialization fields and KV-event publisher description; scheduler keys overwrite same-named server-arg keys. |
| `health_check` | Process-local tokenizer-manager status: false for graceful exit, `Starting`, or `UnHealthy`; it does not issue a scheduler probe. |
| `tokenize` / `detokenize` | Python tokenizer fallback. Rust attempts its locally loaded tokenizer first and uses these only when unavailable. |
| `list_models` | One served base model plus live LoRA registry entries; it is not a checkpoint discovery service. |

These methods occupy
[`get_model_info` through `list_models`, lines 402-478](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L402-L478).
Rust's tokenizer-first fallback is explicit in the tokenization handlers
([tokenize/detokenize](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L473-L556)).

Load, cache flush, pause/continue, profiling, and weight update are asynchronous
tokenizer-manager operations. `_submit_json_unary` schedules a coroutine,
encodes one terminal JSON result, and turns an exception into an error callback
([unary helper](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L202-L229),
[operations](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/grpc_bridge.py#L480-L561)).
Because the Rust JSON callback gives `error` precedence, the structured Python
failure body is discarded and the RPC receives a gRPC error. Successful weight
updates include `num_paused_requests` in the intermediate JSON, but the public
protobuf response exposes only `success` and `message`.

Native gRPC is currently unauthenticated. Resolution prevents combining it
with the HTTP API-key options, but a listener bound to a reachable interface
still exposes inference, `abort_all`, cache flush, pause, profiling, weight
replacement, and server configuration to network clients. Treat bind address
and network policy as the security boundary
([listener warning](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L974-L1007),
[abort-all warning](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/sglang-grpc/src/server.rs#L655-L675)).

## Focused test and missing regressions

`test_grpc_bridge.py` is a CPU unit file with fake callbacks and a fake
tokenizer manager. Its two tests establish only the multi-choice terminal
contract:

- a non-streaming list emits every choice and marks only the last terminal;
- a streaming `n=2` request does not terminate when choice 0 finishes and does
  terminate when choice 1 finishes.

The tests call `_run_generate` directly on a partially constructed handle, so
they do not exercise constructor loop capture, thread-safe scheduling, PyO3,
protobuf mapping, the Rust channel, or Tonic
([entire test](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/test_grpc_bridge.py#L1-L115)).

Highest-value missing cases are:

- `Ready`/`Pending`/`Closed`, early ready edges, one parked chunk, timeout, and
  callback exceptions;
- stream drop, explicit RID abort, `abort_all`, stuck-loop timeout, and batch
  RID abort;
- embedding empty/error/callback-closed behavior and generator closure;
- malformed native dictionaries and immediate versus scheduled exceptions;
- all info/control methods, Rust-tokenizer fallback, and structured-error loss;
- OpenAI valid/invalid JSON, invalid UTF-8, trace headers, status propagation,
  multi-line SSE, fragmented SSE lines, `[DONE]`, backpressure, and disconnect;
- duplicate active RID, response timeout, message-size cap, and unauthenticated
  admin exposure; and
- an end-to-end test that launches the extension and compares HTTP and native
  gRPC results against the same runtime.

The focused test could not run in this documentation environment because the
source package import stops at the optional environment's missing `orjson`
dependency before test discovery. Static AST and symbol validation still cover
the bridge and test structure; no live Tonic server or model process was
started.

## Study checks

- Explain why `--grpc-port` does not select `grpc_server.py`.
- Name which loop owns Tonic I/O, which loop owns `TokenizerManager`, and where
  the GIL is acquired.
- Trace a tokenized `Generate` request to `GenerateReqInput` and back to
  `GenerateResponse` without crossing through HTTP or OpenAI serving.
- Explain why `stream=false` can still return multiple protobuf messages.
- Show why one finished choice cannot close an `n > 1` stream.
- Describe the lost-wakeup defense between `ready_signals` and `set_on_ready`.
- Compare the 300-second response/backpressure limits with the five-second
  abort acknowledgement limit.
- Explain why OpenAI `json_chunk` is not an SSE frame and identify the
  fragmented-line failure mode.
- Distinguish process-local `HealthCheck` from a scheduler execution probe.
- List the native gRPC control operations that make network exposure
  security-sensitive.
- Explain why the model gateway and EPD encoder cannot be treated as clients of
  this exact in-tree protobuf merely because they also use gRPC.
