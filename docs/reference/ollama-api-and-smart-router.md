# Ollama API and Smart Router File Reference

This reference supports
[Ollama-Compatible API and Smart Router](../12-ollama-api-and-smart-router.md).
It records every dedicated Ollama file in the pinned snapshot plus the shared
HTTP-server slice. The [coverage inventory](../coverage/README.md) remains
authoritative for broader files.

## Runtime package

<a id="pythonsglangsrtentrypointsollama__init__py"></a>

### `python/sglang/srt/entrypoints/ollama/__init__.py`

**Status: covered.** The file contains only a package comment. It imports no
records or handlers, re-exports no public names, and performs no registration;
route ownership remains in `http_server.py`
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/__init__.py#L1)).

<a id="pythonsglangsrtentrypointsollamaprotocolpy"></a>

### `python/sglang/srt/entrypoints/ollama/protocol.py`

**Status: covered.** The module defines all Ollama-specific Pydantic records
used by the Python HTTP server:

| Lines | Records | Contract |
| --- | --- | --- |
| [13-30](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/protocol.py#L13-L30) | `OllamaMessage`, `OllamaChatRequest` | Arbitrary role/content, optional image strings, default streaming, format/options/lifetime/thinking compatibility fields |
| [33-56](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/protocol.py#L33-L56) | chat full/stream responses | Assistant message plus terminal defaults, counts, and duration slots only on the full record |
| [59-74](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/protocol.py#L59-L74) | `OllamaGenerateRequest` | Prompt plus suffix/system/template/context/raw/format/options/lifetime/images/thinking shape |
| [77-101](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/protocol.py#L77-L101) | generate full/stream responses | Text response, terminal defaults, optional context/counts/durations only on the full record |
| [104-118](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/protocol.py#L104-L118) | model/tag records | One or more synthetic model records with optional detail dictionaries |
| [121-137](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/protocol.py#L121-L137) | show request/response | Requested model name plus metadata dictionaries and capability list |

The records provide wire shape but almost no semantic validation. Roles are
not literals, dictionaries and image strings are not inspected, requested
model names are not tied to the loaded server model, and no validator relates
`raw`, `template`, `format`, `think`, or `context`. The serving layer is
therefore the authoritative behavior boundary.

The two stream response records intentionally omit duration and token-count
fields. The empty generate stream is an implementation exception: it
serializes the full response record, including null optional fields.

<a id="pythonsglangsrtentrypointsollamaservingpy"></a>

### `python/sglang/srt/entrypoints/ollama/serving.py`

**Status: covered.** `OllamaServing` is the complete server-side adapter:

| Lines | Symbols | Responsibility |
| --- | --- | --- |
| [31-65](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L31-L65) | constructor, timestamp, option conversion | Bind `TokenizerManager`, format UTC milliseconds, map eight options, default to 2,048 output tokens |
| [68-103](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L68-L103) | `handle_chat` | Drop message images, render the raw tokenizer chat template to IDs, construct native generation |
| [105-132](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L105-L132) | `_generate_chat_response` | Consume the first full native result and shape text, nanosecond duration, and token counts |
| [134-170](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L134-L170) | `_stream_chat_response` | Convert assumed-cumulative native text to NDJSON deltas and an empty hard-coded terminal record |
| [173-220](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L173-L220) | `handle_generate` | Concatenate system/raw prompt, short-circuit blanks, construct native text generation |
| [222-249](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L222-L249) | `_generate_generate_response` | Shape the first full native result like full chat without a message wrapper |
| [251-287](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L251-L287) | `_stream_generate_response` | Apply the same prefix slicing and terminal behavior to generated text |
| [289-308](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L289-L308) | `get_tags` | Report one loaded model with zero size, unknown parameters, and a fixed digest |
| [310-349](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L310-L349) | `get_show` | Combine caller-derived family text with loaded context length and placeholder metadata |

The module never consults `request.model` for dispatch. Chat and generate use
the tokenizer manager's `served_model_name` in responses; show accepts any
name and does not compare it. `suffix`, template, context, raw, formats,
keep-alive, images, and thinking are schema-only in this snapshot.

The stream helpers require native text to be cumulative prefixes. Incremental
streaming mode violates the requirement. They compute the delta before the
terminal branch but emit an empty terminal payload, so a final text advance is
lost. All native finish reasons become `"stop"`, stream metrics are absent,
and generator exceptions are not translated into Ollama error records.

Input validation, scheduling, detokenization, cancellation, and pending-state
cleanup remain shared `GenerateReqInput`/`TokenizerManager` responsibilities.
Those broader modules remain partial in the inventory rather than being marked
complete through this adapter pass.

<a id="pythonsglangsrtentrypointsollamasmart_routerpy"></a>

### `python/sglang/srt/entrypoints/ollama/smart_router.py`

**Status: covered.** This module is an optional synchronous client utility,
not part of server assembly:

| Lines | Symbols | Responsibility |
| --- | --- | --- |
| [20-68](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L20-L68) | `SmartRouter`, constructor | Eagerly require `ollama`; build local, remote, and judge clients/models |
| [70-115](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L70-L115) | `_classify_with_llm`, `should_use_remote` | Judge the first 500 characters; substring-match `COMPLEX`; default local on failure |
| [117-195](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L117-L195) | `chat` | Select from force flags/judge, call once, then try the other endpoint once on failure |
| [197-241](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L197-L241) | `chat_stream` | Repeat selection and transparently yield one client's stream without fallback or reason metadata |
| [244-296](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L244-L296) | `main` | Maintain console history, print streamed content, and keep looping after visible errors |

If both force flags are true, remote wins. Supplied messages override prompt
for generation and the last user content becomes the judge prompt; no user
turn means an empty judge input. The ordinary fallback can duplicate a
side-effecting request at a second endpoint, while streaming has no fallback.
No explicit timeout, retry budget, concurrency control, sensitivity policy, or
route telemetry exists here.

The classifier is vulnerable to ordinary heuristic failure: truncation,
instruction influence from interpolated user text, and ambiguous output. Any
string containing `COMPLEX` selects remote; every other successful result and
all judge exceptions select local.

## Shared HTTP slice

<a id="pythonsglangsrtentrypointshttp_serverpy-ollama-slice"></a>

### `python/sglang/srt/entrypoints/http_server.py` — Ollama slice

**Status: partial.** Server initialization stores `OllamaServing` in app state.
The route definitions import the three request records, delegate chat/generate
asynchronously, and return tags/show synchronously
([imports](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L80-L85),
[assembly](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L333-L334),
[routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1954-L1997)).

Five environment variables choose route paths at module import. With no root
override, `/` returns `"SGLang is running"`; setting the override registers an
Ollama-specific root at the supplied path instead. Chat, generate, tags, and
show keep their defaults unless individually overridden. No embed route is
registered.

Earlier references cover startup, native generation, OpenAI completion/chat,
embedding/scoring, Responses, and Anthropic slices. Transcription/realtime,
Vertex, SageMaker, management, warmup, and remaining server responsibilities
keep the whole file partial.

## Documentation

<a id="docsdocsbasic_usageollama_apimdx"></a>

### `docs/docs/basic_usage/ollama_api.mdx`

**Status: covered.** The user guide lists root, tags, chat, generate, and show;
launches a small Qwen model; demonstrates the Ollama CLI and Python library;
adds an SSH tunnel example; and points to the smart router
([entire guide](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/ollama_api.mdx#L1-L157)).

It is a useful happy-path introduction but omits the adapter's accepted-but-
ignored fields, synthetic model metadata, missing embed routes, route
environment variables, cumulative-streaming assumption, terminal mapping, and
absence of focused tests. Its claim that the model name must exactly match the
launch value describes client intent, not handler enforcement: the handler
ignores the requested value. The `/` row calls the default root an Ollama
health check, while the default response text is `"SGLang is running"`.

<a id="pythonsglangsrtentrypointsollamareadmemd"></a>

### `python/sglang/srt/entrypoints/ollama/README.md`

**Status: covered.** This package guide links the API documentation and gives
the smart router's three-terminal setup, constructor, auto/forced/full/stream
usage, and simple-versus-complex diagram
([entire guide](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/README.md#L1-L112)).

The diagram correctly shows a local judge and two destinations. The prose does
not state that ordinary chat alone falls back, that a judge failure selects
local, that force-remote wins conflicting flags, that stream reason metadata
is discarded, or that fallback may replay the request. "Intelligent routing"
should therefore be read as an example heuristic rather than a production
policy or availability guarantee.

## Tests and validation boundary

No tracked test imports `OllamaServing`, the Ollama protocol records, or
`SmartRouter`, and no test exercises the four route families or five route
environment variables. The dedicated source and documentation rows are
covered through static source analysis; runtime compatibility with the
external Ollama client remains unverified.

AST parsing and symbol checks can validate the package without importing GPU
libraries. A meaningful runtime suite would need a fake tokenizer manager for
deterministic full/stream chunks, a small FastAPI route harness, and fake
Ollama clients for judge/fallback behavior. Live CLI interoperability and real
chat-template execution remain integration tests beyond that isolated unit
boundary.
