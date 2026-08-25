# Ollama-Compatible API and Smart Router

SGLang's Ollama surface is a thin tokenizer-process adapter over native
generation. It does **not** translate through `OpenAIServingChat`: chat calls
render the loaded tokenizer's chat template directly, both chat and generate
construct `GenerateReqInput`, and `OllamaServing` reshapes native output as JSON
or newline-delimited JSON (NDJSON)
([handler](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L31-L287)).

The package also contains `SmartRouter`, an optional client-side example that
uses a local Ollama model as a binary judge and then calls either local Ollama
or remote SGLang through the same Ollama Python client. It is not HTTP
middleware and is never installed into the SGLang server request path
([router module](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L1-L23)).

## Recommended study order

1. Revisit the native request and output contract in
   [Native `/generate` Protocol](07-native-generate-protocol.md).
2. Compare the Ollama protocol records with the fields the handler actually
   consumes.
3. Trace chat and raw-prompt generation separately; only chat calls a chat
   template.
4. Study the NDJSON delta assumption and terminal behavior.
5. Finish with synthetic model metadata, route customization, and the separate
   smart-router client.

The [file and symbol reference](reference/ollama-api-and-smart-router.md)
records the exact coverage boundary.

## Placement and end-to-end ownership

At server initialization, `http_server.py` constructs one `OllamaServing`
around the already initialized `TokenizerManager`. The four main routes are
registered regardless of launch flags; only their paths can change through
environment variables
([assembly](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L333-L334),
[routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1954-L1997)).

```text
Ollama client JSON
  -> FastAPI + Ollama Pydantic record
  -> OllamaServing
       chat: tokenizer.apply_chat_template(...) -> input_ids
       generate: system + prompt -> text
  -> GenerateReqInput
  -> TokenizerManager -> scheduler -> detokenizer
  -> native result dictionaries
  -> Ollama JSON or application/x-ndjson
```

This path reuses request normalization, tokenization for raw text, scheduler
admission, model execution, detokenization, request-state cleanup, and
disconnect detection from `TokenizerManager`. The adapter owns the earlier
chat-template call and the later wire shape. It does not own a model registry,
model lifecycle, cache lifetime, Ollama template store, or a second scheduler.

The distinction from other compatibility layers is important:

| Surface | Model-facing preparation |
| --- | --- |
| OpenAI chat | `OpenAIServingChat` plus `TemplateManager`, media, reasoning, tool, grammar, and parser logic |
| Anthropic Messages | Anthropic conversion, then `OpenAIServingChat` |
| Ollama chat | `tokenizer.apply_chat_template` directly with role/content dictionaries |
| Ollama generate | plain `system + "\n\n" + prompt` text concatenation |

Consequently, an Ollama chat request does not inherit OpenAI reasoning/tool
parsers, multimodal preparation, chat-template override machinery, or usage
shaping merely because those features exist elsewhere in the server.

## Routes and path customization

The route paths are read from the environment when `http_server.py` is
imported:

| Environment variable | Default path | Method |
| --- | --- | --- |
| `SGLANG_OLLAMA_CHAT_ROUTE` | `/api/chat` | `POST` |
| `SGLANG_OLLAMA_GENERATE_ROUTE` | `/api/generate` | `POST` |
| `SGLANG_OLLAMA_TAGS_ROUTE` | `/api/tags` | `GET` |
| `SGLANG_OLLAMA_SHOW_ROUTE` | `/api/show` | `POST` |
| `SGLANG_OLLAMA_ROOT_ROUTE` | no Ollama-specific default | `GET`, `HEAD` |

The root behavior is easy to misread. If `SGLANG_OLLAMA_ROOT_ROUTE` is set,
that exact path returns `"Ollama is running"`. If it is absent, `/` instead
returns `"SGLang is running"`; the user guide's table describes `/` as an
Ollama health check, but the literal body is not Ollama's default body in this
snapshot
([root branch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1956-L1971),
[guide table](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/ollama_api.mdx#L19-L60)).

There is no `/api/embed` or legacy `/api/embeddings` route, record, or handler
in this package. "Ollama-compatible" here means the listed chat, generate,
tags, and show subset rather than complete coverage of every Ollama API family.

## Protocol records: accepted is not implemented

The records are intentionally permissive. Roles are arbitrary strings,
`options` is an untyped dictionary, message images are base64-looking strings
without validation, and most optional compatibility fields have no cross-field
checks
([records](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/protocol.py#L13-L137)).

The serving code consumes only this subset:

| Request field | Chat | Generate | Snapshot behavior |
| --- | --- | --- | --- |
| `model` | accepted | accepted | Ignored for execution; the loaded `served_model_name` is returned instead. |
| `messages[].role`, `messages[].content` | used | n/a | Passed directly to the tokenizer chat template. |
| `messages[].images` | accepted | n/a | Ignored; no `image_data` is constructed. |
| `prompt` | n/a | used | Sent as native text after optional system concatenation. |
| `system` | n/a | used | Prepended as plain text with two newlines. |
| `stream` | used | used | Selects full JSON versus NDJSON. Defaults to `true`. |
| `options` | partially used | partially used | Only eight mapped sampling keys survive. |
| `suffix`, `template`, `context`, `raw` | n/a | accepted | Ignored. `raw=true` does not change construction. |
| `format` | accepted | accepted | Ignored; no JSON grammar is created. |
| `keep_alive` | accepted | accepted | Ignored; SGLang owns one already loaded model. |
| `images` | n/a | accepted | Ignored; raw generation is text-only here. |
| `think` | accepted | accepted | Ignored; no reasoning toggle or effort mapping occurs. |

This also means a request naming an unavailable model is not rejected at this
adapter boundary. Both generation handlers read the model name from the live
tokenizer manager and never compare it with `request.model`
([chat](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L68-L103),
[generate](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L173-L220)).

## Sampling conversion

`_convert_options_to_sampling_params` copies exactly eight keys:

| Ollama option | SGLang sampling key |
| --- | --- |
| `temperature` | `temperature` |
| `top_p` | `top_p` |
| `top_k` | `top_k` |
| `num_predict` | `max_new_tokens` |
| `stop` | `stop` |
| `presence_penalty` | `presence_penalty` |
| `frequency_penalty` | `frequency_penalty` |
| `seed` | `seed` |

All other option keys are silently omitted. If `num_predict` is absent, the
adapter sets `max_new_tokens=2048` rather than accepting the native request
default of 128
([mapping](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L41-L65)).

The resulting dictionary still goes through SGLang's normal `SamplingParams`
normalization and verification later. The adapter therefore performs mapping,
not final validation: invalid types, bounds, stop shapes, or unsupported
values can fail after the Ollama handler has constructed `GenerateReqInput`.

## Chat flow

`handle_chat` discards message image arrays and builds one dictionary per
message containing only `role` and `content`. It calls the loaded tokenizer's
`apply_chat_template` synchronously with `tokenize=True` and
`add_generation_prompt=True`, then sends the resulting IDs as the sole input
to native generation
([conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L68-L103)).

Important consequences follow:

- the tokenizer must exist and expose a usable chat template;
- roles unsupported by that template fail or render according to the
  tokenizer, not an Ollama-specific role validator;
- server chat-template overrides and model-specific OpenAI encoders are not
  consulted here; and
- tools, structured output, reasoning content, and media do not receive the
  preparation available in `OpenAIServingChat`.

The prompt IDs prevent native tokenization from repeating the template work.
After that point, ordinary `GenerateReqInput` normalization creates a request
ID, validates the one-input invariant, and dispatches to the shared runtime.

### Non-streaming chat

The non-streaming helper measures wall-clock duration around the first result
from `generate_request`, copies `text`, `prompt_tokens`, and
`completion_tokens`, and returns one assistant message. `done` and
`done_reason` are hard-coded to `true` and `"stop"`; the native finish reason
is not translated
([full response](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L105-L132)).

`total_duration` is nanoseconds, matching Ollama's duration unit. Load,
prompt-evaluation, and evaluation durations remain `null`. The adapter trusts
that a non-streaming native request yields exactly one final record and takes
only `.__anext__()`; a premature empty iterator propagates as an error.

### Streaming chat

Each native item is serialized as one JSON object followed by `\n`, with
`application/x-ndjson` media type. The adapter keeps `previous_text` and emits
`text[len(previous_text):]`, so its central invariant is that every native
`text` value is the cumulative prefix of the next
([stream](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L134-L170)).

That invariant holds for the default tokenizer-manager output mode. It does
not hold when SGLang is launched with incremental streaming output, where
native `text` values are already suffixes. In that mode, slicing later chunks
by the length of the previous suffix can remove valid text.

A chunk is terminal whenever native `finish_reason` is non-null. The adapter
then emits an empty assistant message with `done=true` and
`done_reason="stop"`. If a terminal native chunk also advances the cumulative
text, that last delta is discarded. Stop, length, abort, and error reasons are
not distinguished, and the stream record schema has no token-count or duration
fields. Exceptions during iteration are not converted into an Ollama NDJSON
error object; they terminate the response body after headers may already have
been sent.

## Generate flow

`handle_generate` uses raw text instead of the tokenizer chat template. When
`system` is truthy it constructs `system + "\n\n" + prompt`; it does not use
`template`, `raw`, prior `context` token IDs, a suffix, or multimodal images
([prompt construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L173-L220)).

The concatenated value is tested for emptiness. A blank prompt plus a nonblank
system instruction therefore generates from the system text, while a fully
blank value returns immediately without scheduler work. The empty streaming
branch serializes the full `OllamaGenerateResponse` model as its single NDJSON
record, so its optional `context` and duration/count fields appear as `null`;
ordinary stream chunks use the smaller stream record.

Non-streaming generation mirrors non-streaming chat: first native result,
nanosecond total duration, token counts when present, hard-coded stop reason,
and no returned context IDs
([full response](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L222-L249)).
The ordinary generate stream has the same cumulative-prefix assumption,
terminal-delta loss, hard-coded finish reason, missing metrics, and unframed
error behavior as chat
([stream](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L251-L287)).

Passing `raw_request` into `TokenizerManager.generate_request` preserves the
shared disconnect check and scheduler abort path. There is no separate Ollama
request ID in the wire records, so clients cannot issue a protocol-level abort
or resume a returned `context` through this adapter.

That shared path is weaker than an adapter-owned streaming cleanup guarantee.
The Ollama generator creates neither the delayed abort task used by the native
HTTP path nor a `finally` that aborts its native request when ASGI cancels body
iteration. `TokenizerManager` can detect a disconnect while its iterator stays
alive and reaches a wait timeout, but this snapshot has no focused test proving
prompt scheduler cancellation when the streaming generator itself is closed
([manager wait and disconnect checks](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1687-L1793)).

## Tags and show are synthetic metadata

`get_tags` always returns exactly the one loaded `served_model_name`. Size is
zero, parameter size is `"unknown"`, format is `"sglang"`, and the digest is a
fixed placeholder rather than a hash of weights or configuration
([tags](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L289-L308)).

`get_show` does not validate the requested name against that loaded model. It
derives a family string from the caller's value, strips one of `-Instruct`,
`-Chat`, or `-Base`, and combines it with the loaded model configuration's
context length. License, template, quantization, block count, embedding size,
head count, and parameter count are empty, unknown, or zero; only
`"completion"` is advertised as a capability
([show](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/serving.py#L310-L349)).

These endpoints are compatibility shims for discovery clients. Their values
must not be used as an inventory of downloaded models, an integrity check, or
a reliable model-card description.

## Smart Router: a separate client-side policy

`SmartRouter` constructs three synchronous Ollama clients: local generation,
remote generation, and a judge. The judge defaults to the local host/model but
can be independently configured. The `ollama` package is imported eagerly and
is not part of this snapshot's core Python dependency declaration, so users
must install it as the accompanying documentation says
([construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L20-L68),
[prerequisite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/README.md#L14-L22)).

### Classification

The judge sees only the first 500 characters of the selected prompt inside a
plain-text classification instruction. It runs with temperature zero and a
ten-token output budget. Any uppercase result containing the substring
`COMPLEX` routes remote; every other result routes local. A judge exception is
caught and also routes local
([classifier](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L70-L115)).

This is a heuristic, not a trustworthy policy boundary:

- prompt truncation can hide complexity after character 500;
- user content is interpolated without escaping, so it can influence the
  classifier instruction;
- `NOT COMPLEX` still contains `COMPLEX` and routes remote;
- judge failure defaults to the local model even when the request is complex;
  and
- neither sensitivity, cost, tenant, capacity, nor data-residency policy is
  considered.

### Non-streaming routing and fallback

When `messages` is supplied, it replaces the prompt for generation and the
last user message becomes the judge input. If the history has no user turn,
the judge receives an empty string. `force_remote` wins if both force flags are
true; otherwise force-local, or finally the judge, selects the client
([selection](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L117-L168)).

The chosen client receives only `model` and `messages`. If that call raises,
the other client is attempted once with the same messages. A second failure
propagates. The returned dictionary reports content, the model actually tried,
the local/remote label, and either the classification/force reason or
`"Fallback from ..."`
([call and fallback](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L170-L195)).

Here “model tried” is the configured label sent in the Ollama request, not
verified execution identity. On the remote SGLang destination, `/api/chat`
ignores that label and executes the checkpoint already bound to
`TokenizerManager`, while `SmartRouter` still reports `remote_model`. A
mismatched router/server configuration can therefore attribute an answer to a
model that did not execute it.

### Streaming is deliberately weaker

`chat_stream` repeats routing, then yields the selected client's chunks
unchanged. It has no fallback block, and its computed `reason` is not returned
to the caller. Connection failure before the first chunk and failure after a
partial stream both propagate
([streaming](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L197-L241)).

The interactive `main` function retains full user/assistant history and prints
content from the raw stream. It catches errors at the outer loop and keeps the
session alive, but does not remove the user message that failed or retry it
automatically
([demo](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/ollama/smart_router.py#L244-L296)).

## Failure and test boundary

There are no dedicated Ollama handler, route, schema, or smart-router tests in
the pinned snapshot. Source inspection can establish conversion behavior, but
not compatibility with a particular version of the external Ollama CLI or
Python package.

The highest-value missing regressions are:

- requested-model mismatch and synthetic `/api/tags`/`/api/show` metadata;
- all accepted-but-ignored fields, especially images, format, thinking,
  template/raw/context, and keep-alive;
- direct chat-template errors and unsupported roles;
- cumulative versus incremental native streaming and a final chunk that adds
  text while setting `finish_reason`;
- stop/length/abort/error finish mapping and in-band NDJSON errors;
- route environment overrides and default root response;
- non-streaming fallback versus streaming failure in `SmartRouter`; and
- adversarial, truncated, malformed, or failed judge output.

Operationally, the smart router is synchronous, configures no explicit
timeouts or retries of its own, and can send the same message history to the
other endpoint after a failure. Treat that fallback as a possible data and
side-effect boundary, not merely a latency optimization.

## Study checks

- Explain why Ollama chat does not inherit OpenAI tool, reasoning, media, or
  grammar behavior.
- List the eight option keys that reach `SamplingParams` and state the default
  token budget when `num_predict` is absent.
- Predict the returned model name when a request names a different model from
  the one SGLang loaded.
- Explain how incremental streaming output violates the adapter's prefix
  invariant and when the final delta can disappear.
- Distinguish `/api/tags` and `/api/show` compatibility metadata from actual
  model discovery and inspection.
- Explain why `SmartRouter` is not a server-side load balancer and why only its
  non-streaming call has fallback.
- Identify which missing test would catch the largest user-visible streaming
  bug first.
