# Anthropic Messages File Reference

This reference supports [Anthropic-Compatible Messages API](../11-anthropic-messages.md).
It records the exact files and symbols covered in the Anthropic protocol pass.
The [coverage inventory](../coverage/README.md) remains authoritative for
shared files whose other responsibilities are still pending.

## Runtime source

<a id="pythonsglangsrtentrypointsanthropic__init__py"></a>

### `python/sglang/srt/entrypoints/anthropic/__init__.py`

**Status: covered.** This is a zero-byte package marker. It performs no route
registration, imports no schemas or handlers, and defines no aggregate public
surface. Registration lives in `http_server.py`, so importing the package
alone has no application-state side effect
([empty source](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/__init__.py)).

<a id="pythonsglangsrtentrypointsanthropicprotocolpy"></a>

### `python/sglang/srt/entrypoints/anthropic/protocol.py`

**Status: covered.** The module defines the complete Python SRT Anthropic wire
model:

| Lines | Records and helpers | Contract |
| --- | --- | --- |
| [23-48](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L23-L48) | `AnthropicError`, `AnthropicErrorResponse`, `AnthropicUsage` | Typed error envelope and optional stream/non-stream/cache usage fields |
| [51-131](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L51-L131) | content blocks and `AnthropicMessage` | Discriminated text/image/tool/reference/search/thinking history plus user/assistant/system roles |
| [134-248](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L134-L248) | tool variants, discriminator, `is_server_tool` | Missing type selects a custom tool; dated prefixes select built-in families; custom schemas gain `type: object` when absent |
| [248-339](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L248-L339) | tool choice, thinking, task budget, output config | Cross-field SDK-shape validation and Claude 4.7 compatibility records |
| [341-398](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L341-L398) | count/messages requests and count response | Required model/messages/max-tokens shape, sampling fields, and positive-token validation |
| [405-498](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L405-L498) | content deltas and stream events | Separate message-end delta plus discriminated message/content/ping/error event families |
| [501-518](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L501-L518) | `AnthropicMessagesResponse`, forward-model rebuilds | Generated `msg_` ID, assistant response contract, four stop literals, and nested-type resolution |

The tool discriminator defaults every unknown type to the custom variant. Such
a value then fails the custom variant's `Literal["custom"]` when the explicit
type is neither absent nor `custom`; this produces validation failure rather
than accepting an arbitrary built-in family. `input_schema` validation mutates
the supplied dictionary by adding the object type.

`AnthropicThinkingParam` faithfully checks the SDK-level distinction among
enabled, disabled, and adaptive records, but its docstring also states the
important execution limitation: the local adapter cannot enforce the budget
or omit displayed reasoning. `AnthropicOutputConfig` says task budget is
propagated as a custom hint, while the serving implementation only logs it;
the implementation is the behavior in this snapshot.

The response and event unions are broader than the generator. `PingEvent`,
`SignatureDelta`, `cache_creation_input_tokens`, and `stop_sequence` are valid
serialized records, but their mere presence here does not prove the serving
layer populates them.

<a id="pythonsglangsrtentrypointsanthropicservingpy"></a>

### `python/sglang/srt/entrypoints/anthropic/serving.py`

**Status: covered.** The module is the full adapter, organized into these
responsibilities:

| Lines | Symbols | Behavior |
| --- | --- | --- |
| [63-181](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L63-L181) | maps and module helpers | Stop/error mapping, cache-aware usage partitioning, system text extraction, SSE framing, bounded error scrubbing |
| [184-227](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L184-L227) | constructor, `_chat_template`, `handle_messages` | Bind one OpenAI chat adapter, cache the inline-system decision, convert once, select stream/full delivery |
| [229-410](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L229-L410) | nested media/search/tool-result/thinking helpers | Convert sources and structured results; preserve deferred references; choose native or marker-wrapped reasoning history |
| [412-562](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L412-L562) | system and message conversion | Merge or preserve system turns, maintain user/tool/user order, preserve empty assistant turns, build prior tool calls |
| [564-733](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L564-L733) | chat request, reasoning, compatibility, tools | Map sampling; apply reasoning; map effort; log budget/betas; forward custom tools and validated choice; skip built-ins |
| [735-836](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L735-L836) | non-stream/stream setup | Shared validation/internal conversion, monotonic receive time, OpenAI handler delegation, disconnect abort task |
| [838-1085](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L838-L1085) | stream state and terminal/error helpers | One message, one open block, monotonically increasing indices, balanced failure closure, finish/empty-stream policy |
| [1087-1257](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1087-L1257) | OpenAI chunk conversion | Usage-only handling, last-payload preservation, thinking/tool/text block transitions and deltas |
| [1259-1414](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1259-L1414) | full response and error conversion | Thinking/text/tool block order, invalid-JSON fallback, empty block, status/type preservation, 5xx secrecy |
| [1416-1477](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1416-L1477) | `handle_count_tokens` | Dummy generation request, shared chat rendering/tokenization, no scheduler work, generic 5xx on preparation failure |

Several non-obvious invariants deserve source study:

- tool-result text/reference groups are split only when their reference-ness
  changes, preserving part order while satisfying GLM's boundary-sensitive
  expansion;
- assistant thinking is inserted through exactly one channel, then skipped in
  ordinary content iteration;
- two consecutive streamed tools force a block close/open even though both
  share type `tool_use`;
- role-only chunks do not start the Anthropic message, while a finish-reason
  chunk does, allowing a valid empty completion; and
- all failure paths either re-raise cancellation or leave every opened
  Anthropic block balanced before `message_stop`.

Source-visible compatibility gaps are `metadata` and tool-result `is_error`
loss; built-in tool skipping; budget, task-budget, and beta no-ops; omission of
`output_config` from token-count conversion; omitted signatures/pings/
cache-creation usage; and failure to copy `matched_stop` into
`stop_reason="stop_sequence"` plus `stop_sequence`. The manual and registered
tests do not close these gaps.

<a id="pythonsglangsrttemplatedetectionpy-anthropic-slice"></a>

### `python/sglang/srt/parser/template_detection.py` — Anthropic slice

**Status: partial.** `detect_inline_system_support` returns false for an absent
template, a render exception, or a render that silently drops the mid-dialogue
sentinel. It uses `ImmutableSandboxedEnvironment`, but the probe omits the
custom `raise_exception` callable; templates invoking it fail closed, which is
the desired merge decision
([function](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/parser/template_detection.py#L599-L627)).

The Anthropic unit suite checks guarded, inline-capable, silent-drop, empty,
and absent templates. The module's reasoning-mode and parser rule catalogs,
architecture detection, late config resolution, and CLI orchestration remain
for the parser subsystem pass; this one helper does not make the 781-line file
complete.

<a id="pythonsglangsrtentrypointsopenaiserving_chatpy-anthropic-slice"></a>

### `python/sglang/srt/entrypoints/openai/serving_chat.py` — Anthropic slice

**Status: partial.** The earlier [OpenAI chat reference](openai-completions.md#pythonsglangsrtentrypointsopenaiserving_chatpy)
covers generic preparation and response behavior. The Anthropic pass adds the
adapter-facing reasoning contract:

- `supports_native_reasoning_history` delegates history ownership to the
  selected chat encoder;
- `wrap_reasoning_history` uses the active detector's exact opening label and
  closing token and rejects the no-detector case; and
- `apply_reasoning_enabled` maps Anthropic on/off intent through Hunyuan,
  Inkling, Mistral, always-on, or template-toggle behavior while mirroring the
  read-side support test
  ([history and toggle helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L2311-L2427)).

Anthropic also calls `_validate_request`, `_convert_to_internal_request`,
`_handle_non_streaming_request`, `_generate_chat_stream`, and
`_process_messages`; those shared methods retain the ownership already
explained in the OpenAI guide. DeepSeek-3.2/4, Kimi K3, Inkling, remaining
reasoning families, and every model-specific tool parser keep this file
partial.

<a id="pythonsglangsrtentrypointshttp_serverpy-anthropic-slice"></a>

### `python/sglang/srt/entrypoints/http_server.py` — Anthropic slice

**Status: partial.** Server assembly wraps `openai_serving_chat` in
`AnthropicServing`. Global HTTP and Pydantic exception handlers special-case
the `/v1/messages` prefix, use Anthropic error types, turn validation 422s into
400s, truncate the digest, and hide all 5xx detail
([assembly](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L333-L339),
[error handlers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L497-L604)).
The two JSON-only routes delegate typed requests from app state
([routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2000-L2020)).

Earlier references cover startup, native generation, OpenAI completion/chat,
embedding/scoring, and Responses slices. Ollama, transcription/realtime,
Vertex, SageMaker, management endpoints, warmup details, and remaining
assembly still prevent whole-file coverage.

## Documentation

<a id="docsdocsbasic_usageanthropic_apimdx"></a>

### `docs/docs/basic_usage/anthropic_api.mdx`

**Status: covered.** The tutorial documents automatic route availability, a
GLM-5.2 launch, Anthropic SDK base-URL semantics, ordinary/streamed/system/tool
requests, count tokens, Claude Code environment setup, prefix-cache effects,
troubleshooting, and parameter navigation
([entire guide](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/anthropic_api.mdx#L1-L287)).

The `CLAUDE_CODE_ATTRIBUTION_HEADER=0` discussion explains why a changing
prefix defeats radix-cache reuse; it is operational advice, not adapter code.
The guide correctly says tools need a matching parser for structured output and
that count tokens reuses chat conversion.

Three claims need qualification against this snapshot:

- “standard Anthropic Messages API parameters” overstates parity: metadata is
  ignored, built-in tools are skipped, several Claude 4.7 controls are no-ops,
  and stop-sequence/signature/cache-creation outputs are incomplete;
- “any model works” means the route exists for any loaded model, not that every
  model can honor reasoning, tools, media, or Anthropic protocol semantics; and
- the final paragraph suggests passing model-specific `thinking` or
  `enable_thinking` kwargs through the request, while this request schema
  exposes the typed Anthropic `thinking` object and the serving layer chooses
  the model-facing toggle itself.

## Tests

<a id="pythonsglangtestkitsanthropic_messages_kitpy"></a>

### `python/sglang/test/kits/anthropic_messages_kit.py`

**Status: covered.** `AnthropicMessagesMixin` normalizes a host class's base
URL, provides raw request/default-payload helpers, and contributes live tests
for ordinary/multi-turn/system messages, sampling and stops, basic and
multi-turn streams, HTTP content types, explicit text blocks, error status,
and token counting. It also directly unit-checks base64 image conversion inside
a tool result
([entire mixin](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/kits/anthropic_messages_kit.py#L1-L546)).

`TestOpenAIServer` is its only consumer. Most inherited cases therefore launch
a real small model through the broad GPU/AMD server fixture. The tool-result
image conversion is the exception: it constructs the adapter with an inert
object and never starts generation. SSE parsing ignores invalid JSON rather
than failing. Error tests accept multiple status codes, and the stop-sequence
test checks only acceptance, not `stop_reason` or `stop_sequence` correctness.

<a id="testregisteredunitentrypointsanthropictest_servingpy"></a>

### `test/registered/unit/entrypoints/anthropic/test_serving.py`

**Status: covered.** The CPU-registered suite stubs kernel import and uses fake
OpenAI handlers/chunks. Its cases cover:

- text/thinking/tool block transitions, adjacent tools, zero-argument tools,
  last-token finish chunks, empty completions, upstream error envelopes, parse
  failures, and balanced terminal events;
- cache-aware ordinary and stream usage, missing cache details, and invalid
  cached-greater-than-prompt telemetry;
- search-result flattening, deferred reference grouping/rendering, built-in
  filtering, schema validation, all custom/named/required choice branches, and
  mixed user/tool ordering;
- thinking SDK validation, toggle application, effort mapping, logged
  budget/task-budget/display/beta limitations, history channel ownership,
  redacted-history rejection, and no-detector fallback;
- non-streaming thinking/empty responses, finish fallback, safe 4xx/5xx errors,
  empty assistant turns, and system-template probe/merge behavior
  ([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/anthropic/test_serving.py#L1-L1638)).

It does not exercise the FastAPI routes, content-type dependency, global error
handlers, `handle_count_tokens`, client-disconnect abort, scheduler/media
processing, real parser output, signatures, pings, cache creation, metadata,
tool-result `is_error`, stop-sequence identity, or server-built-in execution.

<a id="testregisteredopenai_serverfunction_calltest_anthropic_tool_usepy"></a>

### `test/registered/openai_server/function_call/test_anthropic_tool_use.py`

**Status: covered.** The CUDA/AMD/CPU-registered integration class launches the
default small model with the Llama 3 tool parser. Non-streaming tests cover tool
shape, automatic/required/named choice, multi-turn result replay, mixed text
and tools, and the no-tool control. Streaming tests require a tool block,
concatenable argument JSON, `tool_use` stop reason, and balanced event ordering
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/function_call/test_anthropic_tool_use.py#L1-L560)).

The tests are model-output-sensitive and the helper silently drops malformed
SSE JSON. `test_tool_use_streaming_args_parsing` only checks JSON when a tool
name appears, although the request itself leaves tool choice at the default;
the primary streamed-tool case uses `any` and is binding. No case covers
parallel tool calls, invalid emitted JSON, deferred definitions, built-in
tools, `is_error`, or reasoning plus tools.

<a id="testmanualvlmtest_anthropic_visionpy"></a>

### `test/manual/vlm/test_anthropic_vision.py`

**Status: covered.** The manual suite downloads two public image fixtures,
launches the small VLM with multimodal mode, and checks base64 single image,
interleaved text/image blocks, streaming, multiple images, and replayed
multi-turn image context. Its semantic helper accepts several keywords for the
person, vehicle, and ironing action
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/vlm/test_anthropic_vision.py#L1-L433)).

Despite its name, `test_single_image_url` sends the same base64 source as the
first case; no case exercises the adapter's actual `source.url` branch. The
suite requires outbound network, a model server, and accelerator-capable VLM
execution, is not registered in CI here, silently skips malformed SSE data,
and uses output semantics rather than deterministic token assertions.

<a id="testregisteredopenai_serverbasictest_openai_serverpy-anthropic-slice"></a>

### `test/registered/openai_server/basic/test_openai_server.py` — Anthropic slice

**Status: partial.** `TestOpenAIServer` mixes in `AnthropicMessagesMixin`,
provides its live small-model server/base URL/API key, and therefore executes
the mixin's HTTP tests in the broad registered suite
([mixin wiring](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/basic/test_openai_server.py#L15-L55)).

Linked references now cover its Responses, embedding/scoring, and Anthropic
slices. Direct completion/chat, native generation, model catalog, grammar,
custom-processor, concurrency, and remaining server responsibilities keep the
file partial.

## Validation boundary

Static AST and symbol checks can validate these references without importing
accelerator libraries. The focused unit file is registered for CPU, but its
shared SGLang imports still require the project dependency surface. The broad,
tool, and vision suites launch model servers; vision additionally downloads
fixtures. A successful focused unit run does not prove FastAPI routing,
disconnect handling, real tool/reasoning parsers, scheduler admission, or
multimodal behavior.
