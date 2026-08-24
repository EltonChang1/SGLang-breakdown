# OpenAI Responses File Reference

This reference supports [OpenAI Responses API](../10-openai-responses.md) at
commit
[`f464e77d17a3908ad0ea32547b1e8b039bcbd354`](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354).
`covered` means the whole meaningful file is explained here; shared files stay
`partial` outside the exact Responses slices named below.

## Runtime and protocol files

### `python/sglang/srt/entrypoints/context.py`

**Status: covered.** `ConversationContext` is the four-operation boundary used
by the Responses generation loop: append model/tool output, decide whether a
built-in tool is needed, call it, and rerender the next prompt. `SimpleContext`
stores only the last native result and deliberately rejects tool operations
([base and simple contexts](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/context.py#L20-L61)).

`HarmonyContext` owns the mutable Harmony message transcript, parser, tool
sessions, initial-message boundary, usage counters, and last non-null finish
reason. Dictionary output IDs are parsed into messages; tool output messages
are appended directly. Browser/Python recipients select either a native `Tool`
or MCP `ClientSession`, with JSON arguments and tool results converted back to
Harmony tool messages. Other recipients fail
([Harmony context](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/context.py#L63-L181)).

`StreamingHarmonyContext` distinguishes cumulative from incremental token-ID
chunks using `completion_tokens`, feeds only new IDs into its parser, renders
direct tool messages into tokens, detects assistant-action stop tokens, and
advances parser state through the suffix added by rerendering. It records a
finish reason but does not update inherited token counters; that is why the
Responses Harmony stream reports zero usage
([streaming context](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/context.py#L184-L231)).

### `python/sglang/srt/entrypoints/harmony_utils.py`

**Status: covered.** The lazy encoding getter loads the GPT-OSS Harmony
encoding once. System/developer builders map reasoning tiers, date, built-in
namespace descriptions, instructions, and function schemas into Harmony
content; unsupported tool types are intentionally omitted. `get_user_message`,
`render_for_completion`, stop-token lookup, and parser construction are thin
typed boundaries
([encoding and input builders](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/harmony_utils.py#L44-L140),
[render helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/harmony_utils.py#L219-L245)).

`parse_response_input` converts message, function output, reasoning, and
function-call input items. System becomes developer, non-text parts are
filtered, function output resolves a prior call ID, and function calls become
commentary-channel recipients. `parse_response_output` performs the smaller
reverse conversion for message and function-call items
([input conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/harmony_utils.py#L142-L217)).

`parse_output_message` maps assistant browser actions, analysis, function
calls, Python/browser commentary, and final text into Responses item types;
tool-authored messages are intentionally hidden. `parse_remaining_state`
salvages partial analysis/final text but drops partial browser or commentary
state. `parse_output_into_messages` is the whole-token convenience parser
([output conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/harmony_utils.py#L247-L397)).

### `python/sglang/srt/entrypoints/http_server.py`

**Status: partial.** Earlier references cover startup, native generation,
completion/chat, embedding/scoring, and their routes. The Responses slice
chooses demo, MCP, or Exa-backed native tool service; initializes the optional
Responses adapter without making its failure fatal to server startup; closes
the tool service on lifespan exit; provides Responses-specific HTTP and
validation error envelopes; and exposes create/retrieve/cancel routes
([tool and handler assembly](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L342-L379),
[tool cleanup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L421-L431),
[error adaptation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L529-L630),
[routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1909-L1942)).

Transcription/realtime, model catalog, Anthropic, Ollama, Vertex, SageMaker,
management endpoints, warmup details, and remaining assembly retain their
owning passes. See the [embedding reference](openai-embeddings-and-scoring.md#pythonsglangsrtentrypointshttp_serverpy)
for the other explicitly covered slices.

### `python/sglang/srt/entrypoints/openai/protocol.py`

**Status: partial.** Earlier references cover completion/chat and
embedding/scoring schemas. The Responses slice defines reasoning tiers,
function and accepted extended tool records, the request field set, request ID
generation, input/image/thinking validators, effective tool choice, structured
output conversion, sampling precedence, grammar conflict checks, response
status/echo fields, Responses-shaped usage serialization, and the
`ResponsesResponse.from_request` factory
([request records and normalization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1519-L1763),
[sampling conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1765-L1842),
[response records](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1846-L2006)).

`RequestResponseMetadata` and `MessageProcessingResult` are also used by the
adapter, but were already explained with chat serving. File/batch and
transcription protocol families remain pending; this shared 2,116-line file is
not complete. See the [completion reference](openai-completions.md) and
[embedding reference](openai-embeddings-and-scoring.md#pythonsglangsrtentrypointsopenaiprotocolpy)
for the earlier slices.

### `python/sglang/srt/entrypoints/openai/serving_responses.py`

**Status: covered.** Module helpers convert native per-token logprobs into
Responses SDK records and suppress qwen3-coder whitespace separators only
while a function call is open. Initialization inherits chat template/parser
state, detects GPT-OSS, adds Harmony action stop IDs, resolves tool
capabilities, and creates unbounded response/message/task stores
([helpers and initialization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L85-L197)).

`create_responses` validates function-tool requirements, logprobs, Harmony
structured output and browser availability, resolves previous state, chooses
regular or Harmony preparation, owns MCP session lifetime, derives sampling,
constructs the native request, and selects background/stream/full delivery.
Its preprocessing and delivery errors use the Responses-specific nested
envelope
([create dispatcher](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L199-L558)).

`_make_request` creates a temporary chat request and reuses `_process_messages`
for templates, media, stops, tool grammar, special tokens, and reasoning;
`_make_request_with_harmony` renders raw Harmony IDs. The full generator drains
native work, separates regular/Harmony output construction, calculates usage,
maps only length to incomplete, protects cancellation from a racing store
overwrite, and returns one response
([request builders](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L560-L617),
[full generator](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L619-L759)).

Reasoning/tool output helpers decide thinking state, parse non-stream output,
fall back to required-call JSON, build response items, translate tool choice,
and normalize every supported Responses input item into chat shape. History
helpers extract only message text, merge assistant fragments, coalesce system
text, replay stored messages, and build or continue Harmony transcripts
([output helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L761-L989),
[normalization and history](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L991-L1354)).

Background helpers implement queued/in-progress/final/failed transitions;
retrieve and cancel validate IDs, synchronize store access, dispatch native
abort, cancel local tasks, and make terminal cancellation idempotent
([state helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L1356-L1461)).

`responses_stream_generator` is the Harmony token/channel event adapter. It
emits text, reasoning, web-search, code-interpreter, and completion events but
has documented disconnect, item-ID, usage, and typed-error gaps
([Harmony stream](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L1463-L1892)).

`responses_stream_generator_non_harmony` is the decoded-text state machine. It
handles cumulative/incremental chunks, reasoning and function parsers,
added/delta/done item ordering, parser flush, usage, store updates, failed
events, and final completion snapshots
([regular stream](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L1894-L2529)).

`_generate_with_builtin_tools` drives one or more native turns, appends each
result into the conversation context, executes recognized Harmony built-ins,
rerenders the transcript, and reduces the remaining output budget. Its
`priority` mutations are not copied into either native request
([tool loop](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_responses.py#L2531-L2604)).

### `python/sglang/srt/entrypoints/openai/tool_server.py`

**Status: covered.** `list_server_and_tools` opens and initializes one MCP SSE
session for discovery. `trim_schema` mutates title/default/anyOf/properties into
Harmony's smaller JSON Schema dialect; `post_process_tools_description`
applies it and removes tools marked out of prompt
([discovery and schema adaptation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/tool_server.py#L20-L72)).

`ToolServer` defines capability, description, and session lookup.
`MCPToolServer` discovers comma-separated host/ports as `/sse`, builds Harmony
namespace configs, maps namespace names to URLs, and initializes a fresh
session on use. Duplicate names log a warning and keep the first URL, although
the later description assignment has already overwritten the description;
missing names make the async context manager fail to yield
([MCP implementation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/tool_server.py#L74-L142)).

`DemoToolServer` conditionally owns native browser/Python `Tool` objects,
returns canonical Harmony namespace descriptions, yields the object directly,
and closes the browser's Exa session. `NativeToolServer` disables Python and is
the `EXA_API_KEY`-only production web-search branch
([demo and native implementations](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/tool_server.py#L145-L191)).

### `python/sglang/srt/entrypoints/search/exa_client.py`

**Status: covered.** Constants define the API endpoint, integration header,
defaults, and allowed search modes. Immutable `ExaSearchConfig` reads typed
environment values, enforces result/search-mode semantic bounds, warns and
falls back on invalid settings, and preserves the highlight toggle
([configuration](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/search/exa_client.py#L1-L61)).

`ExaClient` normalizes base URL, builds auth/integration headers and search or
contents payloads, lazily creates one locked `aiohttp.ClientSession`, exposes
search/contents/close operations, and includes response text in bounded-domain
HTTP or decode errors
([client](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/search/exa_client.py#L64-L138)).

### `python/sglang/srt/entrypoints/tool.py`

**Status: covered.** `Tool` is the async result boundary. `HarmonyBrowserTool`
enables itself from an injected client or `EXA_API_KEY`, validates the last
Harmony recipient, dispatches search/open/find, turns failures into tool text,
and returns one tool-authored Harmony message
([base and browser entry](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/tool.py#L22-L87)).

Browser helpers keep cursor and loaded text state on the conversation context,
reset it on search, format bounded search/page results, lazily fetch pages for
find, resolve direct URLs or 1-based cursors, map model-emitted cursor zero to
the first result, choose highlight/summary/text snippets, cap matches, and
truncate prompt material
([browser state and formatting](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/tool.py#L89-L257)).

`HarmonyPythonTool` is disabled if optional `gpt_oss` support is absent;
otherwise it owns `PythonTool`, streams all produced messages into a list, and
exposes the backend tool config. It requires a `HarmonyContext`
([Python tool](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/tool.py#L259-L286)).

## Documentation

### `docs/cookbook/autoregressive/OpenAI/GPT-OSS.mdx`

**Status: partial.** The Responses slice describes native Exa versus demo
Python versus external MCP startup and gives reasoning, search, and Python SDK
examples. Its trust implication is important: the documented
`PYTHON_EXECUTION_BACKEND=UV` option runs model-authored code on the host
([Responses section](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/cookbook/autoregressive/OpenAI/GPT-OSS.mdx#L437-L504)).

The rest of the GPT-OSS model guide covers installation, quantization,
parallelism, chat, reasoning, tool parsing, speculative decoding, benchmark
results, and deployment; those sections retain their model/operations passes.
There is no general Python SRT Responses API guide elsewhere in the pinned
documentation. The gateway guide describes a separate Rust implementation and
remains assigned to Phase 8.

## Tests

### `test/registered/unit/entrypoints/openai/test_exa_search.py`

**Status: covered.** Five client tests cover headers, default search and
contents payloads, environment configuration, and mocked request transport.
The Responses test proves missing Harmony web-search backend rejection. The
mocked native integration drives `NativeToolServer` through search and open
with environment credentials; the browser-tool test covers request-scoped
search/open/find state. No live Exa call occurs
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/test_exa_search.py#L1-L303)).

The suite does not cover error HTTP/JSON responses, invalid environment bounds,
session close, cursor failures, result truncation, or concurrent session
creation.

### `test/registered/unit/entrypoints/openai/test_responses_protocol.py`

**Status: covered.** Request tests cover named function validation and accepted
extended/namespace tool shapes. Sampling tests cover processed stops,
structural/JSON constraints, structured output, conflicts, preferred values,
logprob include detection, and thinking control. Response tests cover requested
text format, parallel-call echo, incomplete details, Responses usage shape,
SDK-safe reasoning tiers, replayed output IDs, and effective tool-choice echo
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/test_responses_protocol.py#L1-L410)).

It does not cover missing model, tiny/near-limit output budgets, service tier,
maximum tool calls, invalid top-logprob ranges, or most loose input-item forms.

### `test/registered/unit/entrypoints/openai/test_serving_responses.py`

**Status: covered.** Input tests cover previous text replay, replayed call
lists, text/image normalization, function/tool/reasoning/developer conversion,
assistant merging, and unknown types. Chat handoff tests cover function tools,
required choice validation, Kimi K3 fields, processed reasoning, and
marker-preserving special-token behavior. Output tests cover usage, multimodal
rejection/forwarding, native and JSON tool parsing, prose, tool-choice none,
Harmony unsupported-tool filtering, finish status, logprobs, chat tool choice,
separator whitespace, engine flags, cancellation idempotency, and streaming
logprob rejection
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/test_serving_responses.py#L1-L993)).

It does not drive background lifecycle/retrieval, non-Harmony function-call
continuation, Harmony tool loops/streams, missing model, or priority.

### `test/registered/unit/entrypoints/openai/test_serving_responses_stream.py`

**Status: covered.** `NonHarmonyStreamTestCase` verifies processed reasoning
state, typed lifecycle and consecutive sequence numbers, required JSON tool
events, final text/tool/text ordering, and reasoning-parser end flush.
`MultiToolCallStreamingOrderTestCase` drives the real qwen3-coder detector to
prove prior-call close order, prose-before-call order, and one-delta
call-tail/prose/next-call behavior
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/test_serving_responses_stream.py#L1-L313)).

It does not exercise incremental-output mode, exception-to-failed events,
stored streams, reasoning summaries, abort finish reasons, or Harmony
streaming.

### `test/registered/unit/entrypoints/openai/utils.py`

**Status: covered.** This helper temporarily neutralizes `torch.compile`,
stubs the CUDA-only kernel package before importing serving modules, restores
Torch, and exports minimal tokenizer/template managers. Stream helpers collect
SSE, extract event types/payloads, find completion, create cumulative native
chunks, and drive the non-Harmony stream generator. CI registration explicitly
disables the helper as a test file
([entire helper](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/utils.py#L1-L160)).

The mocks intentionally do not prove scheduler, detokenizer, network,
background-task, Harmony, or real model behavior.

<a id="testregisteredopenai_serverbasictest_openai_serverpy-responses-slice"></a>

### `test/registered/openai_server/basic/test_openai_server.py` — Responses slice

**Status: partial.** `TestOpenAIServerv1Responses` launches a small model and
uses the OpenAI SDK to check ordinary and streamed response envelopes, status,
usage keys, output text aggregation, nested invalid-ID errors, and frequency
penalty acceptance. Stream usage is not actually enforced because both checks
use `assert final_usage_ok or True`
([Responses class](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/basic/test_openai_server.py#L600-L950)).

The earlier [embedding/scoring reference](openai-embeddings-and-scoring.md#testregisteredopenai_serverbasictest_openai_serverpy-rerank-and-score-slices)
covers rerank and score slices. Completion/chat, model-list, grammar,
custom-processor, and remaining broad server responsibilities retain later
passes; the whole file is not complete.

## Validation boundary

The focused suites are CPU-registered and mock accelerator/model work, but
importing them still requires the SGLang Python dependency surface, including
`orjson`, `msgspec`, `openai_harmony`, and optional kernel stubs. The live broad
suite launches a model server. This pass attempted collection through an
isolated temporary dependency overlay; collection still stopped in the common
test bootstrap at the absent `compressed_tensors` quantization package, before
any case ran. Static source, link, symbol, and AST checks validate the guide's
references, but they are not substitutes for running either test level in the
project's full runtime environment.
