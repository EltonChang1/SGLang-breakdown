# Anthropic-Compatible Messages API

SGLang's `/v1/messages` surface is a translation layer, not a second inference
engine. It accepts Anthropic-shaped messages, converts them into the existing
OpenAI chat request model, reuses `OpenAIServingChat` for chat-template,
reasoning, tool-parser, native-generation, and cancellation behavior, then
translates the result back into Anthropic JSON or typed SSE events
([adapter overview](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1-L59)).

This boundary matters. The adapter owns protocol compatibility and content
mapping. `OpenAIServingChat` owns model-facing preparation and parsing.
`TokenizerManager`, schedulers, and the detokenizer still own the execution
path described in [Native `/generate` Protocol](07-native-generate-protocol.md).

## Read this after the OpenAI chat guide

The fastest study order is:

1. Read the [OpenAI chat request flow](08-openai-completions.md#chat-completions)
   through `_process_messages` and `GenerateReqInput`.
2. Study Anthropic request and content-block conversion below.
3. Compare the non-streaming response adapter with the Anthropic-specific SSE
   state machine.
4. Finish with token counting, compatibility gaps, and the test boundary.

The companion [file and symbol reference](reference/anthropic-messages.md)
records exact file coverage.

## End-to-end ownership

```text
Anthropic JSON
  -> FastAPI + Anthropic Pydantic records
  -> AnthropicServing._convert_to_chat_completion_request
  -> ChatCompletionRequest
  -> OpenAIServingChat validation, template/media/tool/reasoning preparation
  -> GenerateReqInput -> shared tokenizer/scheduler/detokenizer runtime
  -> OpenAI chat response or SSE chunks
  -> Anthropic message JSON or Anthropic content-block SSE
```

The server constructs one `AnthropicServing` instance around the already
initialized OpenAI chat handler, then registers `/v1/messages` and
`/v1/messages/count_tokens` unconditionally
([assembly](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L333-L339),
[routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2000-L2020)).
There is no Anthropic-specific model process, cache, scheduler queue, or tool
executor.

Request validation happens in two stages. FastAPI/Pydantic checks the
Anthropic wire shape; the adapter then builds a `ChatCompletionRequest`, whose
normalizers and `OpenAIServingChat._validate_request` apply the shared chat
rules. Conversion failures are client errors. Failures after native preparation
starts are either translated OpenAI errors or generic Anthropic 5xx errors
([dispatch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L206-L227),
[delivery branches](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L735-L836)).

## Protocol records: shape is not behavior

`AnthropicMessagesRequest` requires a nonempty `model`, a positive
`max_tokens`, and a message list. It accepts sampling fields, top-level system
content, custom metadata, thinking, tools, tool choice, and Claude 4.7
`output_config`/`betas` records. The count request uses the same message,
system, thinking, and tool families without generation sampling
([request models](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L341-L398)).

Content and event families are discriminated on `type`. This prevents, for
example, an `input_json_delta` from validating as text or a `tool_result` from
being confused with a tool definition. The accepted input blocks are text,
image, tool use, tool result, deferred-tool reference, search result, thinking,
and redacted thinking
([content records](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L51-L131)).

The schema is deliberately broader than the execution behavior:

| Accepted field or variant | Actual behavior in this snapshot |
| --- | --- |
| `metadata` | Parsed and then ignored; it is not copied to the chat request or response. |
| `thinking.enabled.budget_tokens` | Required and validated at `>= 1024`, but only logged; it does not cap reasoning tokens. |
| `thinking.adaptive` | Treated exactly like enabled reasoning; there is no adaptive throttle. |
| `thinking.display="omitted"` | Accepted and logged, but reasoning is still returned to the client. |
| `output_config.effort` | Mapped to OpenAI `reasoning_effort`; Anthropic `xhigh` collapses to `max`. |
| `output_config.task_budget` | Validated and logged, but not assigned to `custom_params` or any other execution field. |
| `betas` | Accepted and logged as a local no-op. |
| built-in web-search/computer/bash/editor tools | Validated, then skipped because the OpenAI chat backend has no matching server execution. |
| `cache_creation_input_tokens` | Present in the response schema but never populated. |
| ping and signature event records | Modeled for wire compatibility, but the stream generator emits no pings and never captures a thinking signature. |

These distinctions follow the conversion and usage code, not merely the
record definitions
([thinking/output configuration](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L590-L652),
[tool filtering](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L654-L731),
[usage fields](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L88-L133)).

## Message conversion

### System placement is template-dependent

Anthropic normally carries system instructions in the top-level `system`
field, but the request model also tolerates `role: "system"` inside
`messages` for clients such as Claude Code. At adapter construction,
`detect_inline_system_support` renders a four-message sentinel probe in a
sandboxed Jinja environment. A template counts as inline-capable only when the
second system sentinel survives rendering; raising or silently dropping it
both count as unsupported
([probe](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/parser/template_detection.py#L599-L627)).

If inline systems are unsupported, the converter extracts text from every
in-message system turn and appends it after top-level system text in one leading
system message. If supported, the top-level system stays leading and in-message
system turns retain their original positions
([initialization and extraction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L184-L204),
[merge decision](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L412-L433)).

The invariant is renderability, not exact conversational equivalence: moving a
mid-conversation system instruction to the prefix changes prompt ordering, but
is preferable to a template error or silent loss.

### Content-block mapping

| Anthropic input | OpenAI chat representation | Important boundary |
| --- | --- | --- |
| text | string when alone; otherwise a text part | Empty assistant text is preserved so strict role alternation does not collapse. |
| base64 image | `image_url` data URI | Missing/invalid data is silently omitted. |
| URL image source | `image_url` with the URL | The source record is loosely typed; the adapter checks for a `url` key. |
| assistant `thinking` | native `reasoning_content` for encoders that own reasoning history; otherwise detector-specific wrapped text | The raw thinking block is skipped afterward to prevent duplication. |
| `redacted_thinking` | rejected | Local parsers cannot interpret or verify the opaque data. |
| assistant `tool_use` | OpenAI function tool call with JSON-string arguments | The call ID and function name survive. |
| user `tool_result` | one or more `role: tool` messages | `tool_use_id`, falling back to legacy `id`, becomes `tool_call_id`; `is_error` is not forwarded. |
| `tool_reference` inside a result | GLM-specific `tool_reference` content with `name` | Consecutive reference and non-reference runs are split because templates expand references only at a tool-message boundary. |
| `search_result` | formatted title/source/content text | Structured citation semantics are lost. |

The image, search, tool-result, and reasoning helpers live inside the request
converter because they are protocol-bound normalization rather than reusable
runtime behavior
([media/search/result helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L235-L367),
[reasoning history](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L369-L410)).

Ordering around tool results is an explicit invariant. For a user block list
`[text-before, tool_result, text-after]`, the converter flushes the first text
as a user message, emits the tool message, then emits the trailing user text.
Without that flush, collecting all user parts until the end would reorder the
tool result ahead of preceding text
([ordered emission](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L435-L562)).

Thinking-history replay has a second invariant: prior reasoning must remain in
the model's reasoning channel. Encoders such as channel-framed models receive
`reasoning_content` directly. Other reasoning models use the active detector's
own start/end markers. If no detector exists, the adapter warns and drops the
opaque prior thinking rather than exposing it as ordinary assistant prose
([chat ownership helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L2311-L2337)).

## Sampling, reasoning, and tools

The direct sampling mapping is small and lossless for the fields it handles:
`temperature`, `top_p`, `top_k`, `stop_sequences`, `max_tokens`, and `stream`
become their chat equivalents. Streaming also forces continuous usage chunks
so the Anthropic adapter can produce input usage at `message_start` and output
usage at `message_delta`
([request construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L564-L588)).

`thinking` is not passed as a raw template keyword. The adapter calls
`OpenAIServingChat.apply_reasoning_enabled`, which knows whether the active
model uses a template toggle, effort value, or always-on parser. Enabling
without a compatible parser, or disabling an always-on parser, becomes a
client error rather than silently doing the opposite
([reasoning toggle contract](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L2357-L2427)).

Only custom tools enter the OpenAI chat pipeline. Their `input_schema` is
required and normalized to an object schema; `defer_loading` survives so
supporting templates can hide the definition until a later `tool_reference`
names it
([tool schemas](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/protocol.py#L134-L248)).
Tool choice maps as follows:

| Anthropic | OpenAI chat |
| --- | --- |
| `none` | `none` |
| `auto` | `auto` when at least one custom tool survives |
| `any` | `required` |
| named `tool` | an OpenAI named function choice after membership validation |

If `any` or named selection refers only to skipped server-side tools, the
adapter rejects the request. An automatic choice over only skipped tools
becomes the chat schema's default `none`; it cannot execute a built-in
([choice conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L691-L731)).

## Non-streaming response conversion

The non-streaming branch records a monotonic receive time, invokes the shared
chat validation and internal-request builder, then awaits the existing OpenAI
non-streaming handler. This means prompt rendering, media preparation,
tool/reasoning parsing, scheduler admission, abort behavior, and usage are not
reimplemented in the Anthropic package
([non-streaming handoff](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L735-L787)).

The result adapter emits content in this order: a `thinking` block when
`reasoning_content` exists, a text block when visible content exists, then one
`tool_use` block per parsed OpenAI tool call. Invalid tool-argument JSON logs a
warning and becomes `{}`; an entirely empty result gets an empty text block so
strict clients still receive nonempty `content`
([response conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1259-L1335)).

Finish reasons map `stop -> end_turn`, `length -> max_tokens`, and
`tool_calls -> tool_use`. `content_filter`, `abort`, and `function_call` fall
back to `end_turn` with a warning because the Anthropic response literal has no
exact target. Although the intermediate OpenAI choice exposes `matched_stop`,
the adapter never reads it, so `stop_sequence` is never populated and a matched
user stop is reported as `end_turn`
([mapping](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L63-L85),
[available OpenAI field](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1183-L1193)).

## Streaming is a block-state machine

The shared OpenAI stream emits chat-completion chunks. Anthropic requires an
outer message lifecycle plus separately indexed content-block lifecycles, so a
simple field rename is insufficient.

The adapter tracks whether the message and one content block are open, the
current block type/index, finish reason, final usage, and whether meaningful
content has appeared. A change among thinking, tool use, and text closes the
old block before opening the new one. Every new tool call forces a fresh block
even after another tool call; otherwise argument fragments for adjacent calls
would corrupt one JSON stream
([state and block helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L838-L939)).

For a successful text-and-tool stream, the wire ordering is:

```text
message_start
content_block_start(text)
content_block_delta(text_delta)*
content_block_stop
content_block_start(tool_use)
content_block_delta(input_json_delta)*
content_block_stop
message_delta(stop_reason, output usage)
message_stop
```

`message_start` is delayed past role-only chunks so prompt usage is more likely
to be available. The first payload or finish-reason chunk starts it. Usage-only
chunks update final usage but create no content. A finish-reason chunk is still
processed for content because some backends attach the last token or final
argument fragment to that same chunk
([chunk processing](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1118-L1170)).

Reasoning becomes `thinking_delta`, tool arguments remain partial JSON strings,
and visible text becomes `text_delta`. The state machine never combines or
validates the final streamed tool JSON itself; the client concatenates the
fragments
([delta conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1172-L1257)).

`[DONE]` closes an open block, maps the finish reason, emits final output usage,
and stops the message. A stream with a finish reason but no content is treated
as a valid empty completion. A stream with neither content nor finish reason is
an in-band `api_error`, because calling it a successful empty answer would hide
a dropped backend stream
([completion handling](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1042-L1085)).

On parse or generator failure, `_flush_on_error` starts the message if needed,
closes any open content block, emits an Anthropic error event, and emits
`message_stop`. `CancelledError` is deliberately re-raised; the
`StreamingResponse` background task delegates client-disconnect abortion to
the tokenizer manager
([error balancing](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L941-L1035),
[abort attachment](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L825-L836)).

## Usage conversion

Anthropic usage partitions cached prompt tokens from ordinary input tokens:

```text
input_tokens = max(OpenAI prompt_tokens - cached_tokens, 0)
cache_read_input_tokens = cached_tokens, when nonzero
output_tokens = OpenAI completion_tokens
```

Cached tokens larger than total prompt tokens trigger a warning and clamp
ordinary input to zero. Non-streaming responses include input and output.
Streaming `message_start` includes input and forces output to zero;
`message_delta` includes output and omits input, matching the intended split
between the two event types
([usage conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L88-L133),
[stream placement](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L861-L874)).

This depends on continuous OpenAI usage being present when the first meaningful
chunk starts the Anthropic message. If it is absent, the adapter emits zero
input usage and has no later event that repairs that field. Cache-creation
usage is never derived.

## Token counting is preparation-only

`/v1/messages/count_tokens` constructs a dummy one-token Messages request,
reuses the same Anthropic-to-chat conversion, and calls
`OpenAIServingChat._process_messages`. It returns the length of prepared token
IDs, or encodes the prepared prompt string when the multimodal branch leaves
`prompt_ids` as text. It never creates `GenerateReqInput` and never enters the
scheduler
([count handler](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1416-L1477),
[shared preparation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L1099-L1203)).

This is exact for the rendered textual token sequence. For multimodal requests,
it does not run scheduler-side media expansion and therefore should not be read
as a guarantee of the final model-visible image/video token count. The count
request accepts `output_config` and `betas`, but the dummy request does not copy
either. `betas` is a no-op everywhere. Dropping `output_config.effort` is more
consequential: models whose chat template uses reasoning effort can receive a
count for different framing than generation.

## Error and security boundary

FastAPI's global handlers special-case every `/v1/messages...` path. Validation
errors become status 400 with a short `field: message` digest. HTTP exceptions
map status codes to Anthropic error types. The handler never exposes 5xx detail
([HTTP error adaptation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L497-L604)).

Adapter-generated errors follow the same policy. Four-hundred-level upstream
messages are bounded, and obvious traceback/file lines are removed so callers
retain useful validation context. Five-hundred-level messages are always
`Internal server error`; exception class names are logged server-side only
([scrubbing](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L161-L181),
[error conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/anthropic/serving.py#L1337-L1414)).

The adapter does not execute Anthropic built-in tools, verify thinking
signatures, enforce `metadata`, or provide Anthropic-side prompt caching. It
does accept remote image URLs, which are handed to the shared multimodal
pipeline; operators should apply the same outbound-fetch and untrusted-media
controls as for OpenAI vision requests.

## Validation and test boundary

The focused CPU unit suite drives conversion, usage, reasoning history, custom
and deferred tools, tool-result ordering, stop fallback, balanced SSE
lifecycles, adjacent tool calls, final-payload chunks, and error scrubbing with
fake OpenAI handlers. It also tests the inline-system template probe
([unit suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/anthropic/test_serving.py#L1-L1638)).

Three broader layers require model or network resources:

- `AnthropicMessagesMixin` adds live basic, multi-turn, system, sampling,
  streaming, raw HTTP, validation, content-block, and token-count cases to the
  broad OpenAI server suite
  ([mixin](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/kits/anthropic_messages_kit.py#L1-L546)).
- the registered tool-use suite launches a small model with the Llama 3 parser
  and checks ordinary/required/named/multi-turn/streamed tool behavior
  ([tool suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/function_call/test_anthropic_tool_use.py#L1-L560)).
- the manual VLM suite downloads image fixtures and launches a multimodal
  server for base64, mixed-part, stream, multi-image, and multi-turn checks
  ([vision suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/vlm/test_anthropic_vision.py#L1-L433)).

No focused test asserts `stop_sequence`, `metadata`, `is_error`, true URL image
input, thinking signatures, pings, cache-creation usage, actual built-in tool
execution, multimodal token-count parity, or the global FastAPI Anthropic error
handlers. The live mixin's empty-message case expects an error, but the request
schema itself does not declare a minimum list length; any rejection therefore
depends on later shared chat preparation.

## Study checks

- Explain why this adapter delegates through OpenAI chat instead of creating a
  native request directly.
- Convert `[text, tool_result, text]` by hand and verify the three output roles
  stay in order.
- Explain when prior thinking becomes `reasoning_content`, wrapped content, or
  is dropped.
- Trace a two-tool stream and identify why both tools need distinct block
  indices.
- Distinguish custom function tools, deferred tool references, and accepted but
  skipped Anthropic server tools.
- Identify which usage fields appear at `message_start` versus
  `message_delta` and what happens if initial usage is unavailable.
- Explain why token counting does not prove the scheduler-visible multimodal
  token total.
- Find every accepted compatibility field that does not currently affect
  execution before promising full Anthropic API parity.
