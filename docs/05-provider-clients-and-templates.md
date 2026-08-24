# Provider Clients and Prompt Templates

The frontend language is useful even when SGLang does not execute the model.
Its interpreter can send the accumulated program state to OpenAI, Anthropic,
LiteLLM, Vertex AI, Crusoe, or an OpenAI-compatible service. These adapters are
small, synchronous clients beneath `StreamExecutor`; they are not SRT protocol
servers, schedulers, or model runners.

This guide completes the provider-client and lightweight chat-template layer
at source commit
[`f464e77d17a3908ad0ea32547b1e8b039bcbd354`](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354).
Read [Frontend Language Execution](04-frontend-language.md) first for the IR,
executor, role, media, sampling, and synchronization machinery that calls these
backends. The companion [file reference](reference/provider-clients-and-templates.md)
catalogs every provider file, all 27 template records, all 16 matchers, and the
relevant examples and manual tests.

## 1. Three template systems must not be conflated

This snapshot contains several things called a chat template:

| System | Location | Job |
| --- | --- | --- |
| Frontend `ChatTemplate` | [`python/sglang/lang/chat_template.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L7-L78) | Incrementally wraps `system`, `user`, and `assistant` regions while an SGL program builds `text_` and OpenAI-shaped `messages_` |
| SRT conversation/Jinja rendering | `python/sglang/srt/...` plus tokenizer templates | Prepares requests received by the SGLang server; it has a much richer protocol, tool, and model-specific surface |
| Example Jinja files | [`examples/chat_template`](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/chat_template) | User-selectable or demonstrative templates for server APIs and tooling |

The frontend record has only prefixes, suffixes, default system text, stop
strings, media markers, and one Llama-2-specific style. It does not interpret
Jinja, tools, reasoning fields, or arbitrary tokenizer template logic. A test of
the example DeepSeek Jinja files therefore does not test the frontend registry.

## 2. End-to-end provider request flow

For one generation expression, data moves through these steps:

1. `SglRoleBegin`, text/media expressions, and `SglRoleEnd` update the
   executor's serialized `text_`, OpenAI-shaped `messages_`, and media lists.
   A template with a default system prompt injects it before the first
   non-system role
   ([role execution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L665-L717)).
2. `_resolve_sampling_params` overlays expression fields on call defaults and
   appends the template's stop strings. The adapter then converts that common
   record to its provider's smaller parameter vocabulary
   ([resolution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L788-L812),
   [provider mappings](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L64-L119)).
3. The backend chooses message or completion input, calls its SDK, and returns
   `(text, metadata)` or yields `(delta, metadata)` pairs. These provider
   adapters return empty metadata; only the OpenAI adapter separately records
   aggregate token counts.
4. `StreamExecutor` appends the returned text, stores a named variable, and
   releases its synchronization events. If a non-streaming provider returns
   multiple completions, the variable keeps the list while only the first item
   advances `text_`
   ([generation result handling](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L593-L645)).

The adapter methods are synchronous. Even a streaming iterator performs
blocking SDK iteration on the executor worker thread. `run_batch` gains
concurrency from its outer pool of program workers, not from asynchronous
provider clients.

## 3. Capability matrix

| Backend | Request shape | Streaming | Selection | API speculation | Media path | Usage accounting |
| --- | --- | --- | --- | --- | --- | --- |
| `OpenAI` | Chat messages by default; raw completion text for the one recognized instruct model or explicit override | Yes | Completion models only; custom greedy token walk | Chat and completion paths | OpenAI message blocks in chat mode | Mutable aggregate `TokenUsage` |
| `Crusoe` | Inherits `OpenAI`; defaults to Crusoe's compatible `/v1/` endpoint | Yes | Inherited | Inherited | Inherited | Inherited |
| `Anthropic` | Messages API; bare text is wrapped as one user message | Yes | No | No | OpenAI-shaped blocks are not translated | None |
| `LiteLLM` | Always LiteLLM chat completion; bare text is wrapped as one user message | Yes | No | No | Passes OpenAI-shaped blocks for LiteLLM to adapt | None |
| `VertexAI` | Converted message list, raw string, or string/image parts | Yes | No | No | Has custom image conversion | None |

None of these five clients enables the frontend KV concatenate/append
capability. Unsupported `BaseBackend.select` and optimization methods therefore
raise only if a program actually reaches them; inheritance does not make every
SGL feature portable.

## 4. Sampling is a lossy portability boundary

`SglSamplingParams` is wider than every provider request. The important rule is
to reason from the conversion method, not from the public `sgl.gen` signature.

| Field group | OpenAI / Crusoe | Anthropic | LiteLLM | Vertex AI |
| --- | --- | --- | --- | --- |
| Length | `max_tokens` or `max_completion_tokens` | `max_tokens` | `max_tokens` | `max_output_tokens` |
| Multiplicity | `n` | Dropped | Dropped | Forced `candidate_count=1` |
| Stops | `stop` | `stop_sequences` | `stop` | `stop_sequences` |
| Core sampling | temperature, `top_p` | temperature, `top_p`, `top_k` | temperature, `top_p` | temperature, `top_p`, positive `top_k` |
| Penalties | frequency and presence | Dropped | frequency and presence | Dropped |
| Regex | Warning, then dropped | Warning, then dropped | Warning, then dropped | Warning, then dropped |
| Other frontend/SRT fields | Dropped | Dropped | Dropped | Dropped |

The last row includes minimum tokens, stop token IDs/regex, `min_p`, EOS policy,
logprob controls, JSON schema, and most constraint metadata. OpenAI implements
`str` and `int` dtypes itself, but only for completion models: strings are
generated between quotes, while integers use a tokenizer-derived positive
logit bias and stop at a space
([dtype branches](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L182-L220)).

OpenAI initially creates both token-limit keys, then drops
`max_tokens` for names containing or starting with `o1`/`o3`; other names drop
`max_completion_tokens`
([selection](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L163-L179)).
This is string-based compatibility policy, not server capability discovery.

## 5. OpenAI is both a native and compatibility client

Construction selects `openai.OpenAI` or `openai.AzureOpenAI`, asks `tiktoken`
for the named tokenizer with a `cl100k_base` fallback, selects a frontend chat
template from the model name, and initializes mutable usage and speculative
state
([constructor](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L56-L105)).
Only `gpt-3.5-turbo-instruct` is automatically classified as a completion
model. Every other name—including third-party names used with `base_url`—is a
chat model unless the caller supplies `is_chat_model=False`.

That default explains the OpenRouter, OrcaRouter, Together, Azure, and Crusoe
examples: they reuse the OpenAI SDK transport and frontend behavior by changing
client construction, not by adding provider-specific protocol code. A
compatible endpoint must accept the particular parameters and streaming usage
extension this adapter sends.

### Chat placement invariant

Without API speculation, a chat-model `sgl.gen` must occur immediately after
the assistant prefix. The backend checks `s.text_.endswith(chat_prefix)` and
otherwise raises
([check](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L140-L160)).
This prevents a partial assistant message from being represented inconsistently
between `text_` and the still-open `messages_` list. Completion models simply
send the whole accumulated text.

For `n > 1`, `openai_completion` preserves all returned strings. The executor
stores that list in the named variable but appends only its first element to
the continuing prompt. Later turns therefore continue from candidate zero,
not from all alternatives.

### API speculative execution

Completion speculation asks once for a longer suffix and slices later named
fields locally in the interpreter. Chat speculation is backend-specific: each
generation records a stop/name placeholder, literal assistant text records a
fixed segment, and the assistant-role end performs up to three full completions
until the format matches
([preparation and matching](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L109-L138),
[`role_end_generate`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L224-L281)).

The speculative dictionaries and format list belong to the backend instance,
not a program state. The source explicitly notes that batch/multithreaded use
is unsupported. Streaming with any API speculation is rejected by the
interpreter before the provider call.

### Choice selection is not the common choice-policy protocol

`OpenAI.select` works only for completion models. It tokenizes every choice,
then repeatedly requests one token with a strong bias toward the current
candidate tokens, prunes candidates that do not match, and returns the choice
with the most matched positions
([implementation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L312-L380)).
It ignores the supplied `ChoicesSamplingMethod`, does not compute full-choice
logprobs, and fails naturally on empty choices or an API token outside the
biased candidates. Its `scores` metadata is therefore match counts, not the
normalized likelihood metadata produced by `RuntimeEndpoint`.

### Retry and usage behavior

Ordinary and streaming helpers retry three categories of OpenAI SDK failure up
to three times with a blocking five-second delay. Other exceptions fail
immediately
([ordinary helper](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L383-L422),
[stream helper](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L425-L475)).
The shared `TokenUsage` record has no lock. Ordinary calls add both counts;
selection adds prompt tokens but replaces, rather than adds, completion tokens
on each step. Treat its values as approximate process diagnostics under
concurrency, not request-scoped billing records.

## 6. Other provider adapters

### Anthropic

`Anthropic` always uses the Messages API and the `claude` frontend template. A
plain-text SGL program becomes one user message; a role-based program reuses
`s.messages_`. If the first message is a system message, the adapter removes it
with `pop(0)` and sends its content through the separate `system` argument
([generation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/anthropic.py#L26-L49)).

Because `messages = s.messages_` is not a copy, that pop mutates executor
history. The adapter also takes only `ret.content[0].text`, does not translate
OpenAI image blocks to Anthropic blocks, and relies entirely on SDK error and
retry behavior. Streaming repeats the same message transformation and yields
the SDK's `text_stream` deltas
([streaming](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/anthropic.py#L51-L73)).

### LiteLLM

`LiteLLM` stores model/client arguments and always calls
`litellm.completion` with messages. Role-free text is one user message; role
history and media blocks pass through unchanged for LiteLLM to adapt. The
adapter extracts the first message choice, yields non-`None` delta content, and
adds no local retry or usage layer
([entire adapter](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/litellm.py#L15-L90)).
Its `max_retries` default is captured from `litellm.num_retries` at import time;
the constructor passes all client fields, including `None`, to each call.

### Vertex AI

Construction requires `GCP_PROJECT_ID`, accepts optional `GCP_LOCATION`, calls
the process-global `vertexai.init`, and fixes the frontend template to
`default`
([constructor](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/vertexai.py#L20-L36)).
Every generation constructs a new `GenerativeModel`. Message conversion maps
assistant to Vertex's `model` role and emulates an unsupported system prompt as
a user/model exchange. Content lists assume text first and image blocks after
it; image MIME type is always `image/jpeg`
([conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/vertexai.py#L99-L148)).

The role-free multimodal path splits `text_` on the template image marker and
interleaves `Image.from_bytes(image_base64_data)`. The interpreter supplies a
base64 string, so this path passes encoded text rather than decoded image bytes
([single-turn conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/vertexai.py#L85-L97),
[encoder result](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/utils.py#L235-L257)).
The message path instead places the base64 string in `inline_data`. These are
important integration checks for non-JPEG data and SDK-version changes.

### Crusoe

`Crusoe` resolves an explicit key before `CRUSOE_API_KEY`, rejects a missing
key, supplies the managed-inference base URL unless overridden, and delegates
everything else to `OpenAI`
([entire adapter](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/crusoe.py#L1-L43)).
It does not change chat-model detection, tokenization fallback, selection,
speculation, retry, streaming, or parameter behavior. Compatibility with a
specific hosted model is therefore an OpenAI-adapter concern.

## 7. Template selection and execution invariants

`register_chat_template` overwrites by name, while matcher registration appends
to a list. `get_chat_template_by_model_path` calls matchers in import order and
returns the first non-`None` result; unmatched names receive `default`
([registries and lookup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L57-L78)).
Thus registration order is behavior, not just organization.

The 27 records fall into familiar groups: labeled default/Claude/Vicuna
prompts; ChatML and Qwen variants; Llama, Mistral, and Gemma turn formats;
DeepSeek/Janus records; and multimodal variants with model-specific image or
audio markers. The full [template catalog](reference/provider-clients-and-templates.md#template-catalog)
records each name, match trigger, default system behavior, stops, and media
tokens.

Four names are never returned by a matcher: `default`, `janus`,
`llama-3-instruct-llava`, and `llama-4`. The first is the fallback; the others
require explicit selection. In particular, a Llama-3 Instruct model path is
matched to `llama-3-instruct`, so the LLaVA-specific image marker is not chosen
automatically.

`ChatTemplate.get_prefix_and_suffix` silently returns empty strings for an
unknown role. That makes the `janus-pro` record's capitalized `User` key
significant: normal `sgl.user(...)` emits lowercase `user`, so automatically
matched Janus-Pro user turns receive no registered user prefix
([record](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L250-L271),
[fallback lookup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L22-L41)).
The separately registered `janus` record uses lowercase `user`, but the Janus
matcher returns `janus-pro`.

The only style-specific behavior is Llama 2. Its initial system prefix is
combined with the first user prefix, and the next user role suppresses its own
prefix so the system and first instruction occupy one `[INST]` block
([special case](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L22-L41)).

## 8. Examples and validation evidence

The provider quick starts are mostly a controlled comparison: the same
single/stream/batch chat or few-shot completion program is run against different
backends. This makes request-shape differences visible, but they are executable
samples with live credentials, network access, model drift, and cost—not
deterministic unit tests. The OpenRouter and Azure usage docstrings also name a
different script than the file containing them; invoke the actual checked-out
path.

Focused usage examples demonstrate multiple OpenAI choices, sync/async
streaming, completion speculation, chat speculation, and selection on an
instruct model. The chat-speculation example deliberately invokes an unsupported
streaming case and says an executor error is expected
([example](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/usage/openai_chat_speculative.py#L122-L155)).

The manual OpenAI suite maps chat, completion, and vision clients onto shared
frontend programs covering roles, selection, dtypes, Python tool use, forks,
media, streaming, and both speculation modes
([suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/lang_frontend/test_openai_backend.py#L23-L92)).
The Crusoe suite adds live chat/stream/fork smoke tests and local credential/base
URL construction checks
([suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/test_crusoe_backend.py#L28-L79)).

No focused Anthropic, LiteLLM, or Vertex AI backend test file is present in the
pinned snapshot. The DeepSeek chat-template test renders three example Jinja
files and checks tool-argument escaping; it does not import or validate
`sglang.lang.chat_template`
([test boundary](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/test_deepseek_chat_templates.py#L1-L54)).

## 9. Operational and failure checklist

- Treat provider SDK versions and endpoint compatibility as runtime inputs;
  these adapters perform little capability negotiation.
- Supply `is_chat_model` and, when needed, `chat_template` explicitly for
  OpenAI-compatible model names whose naming does not match the built-in rules.
- Do not share one OpenAI backend across concurrent API-speculative programs;
  speculative state and usage counters are instance-global and unlocked.
- Expect a large part of `SglSamplingParams` to disappear at a provider
  boundary. Verify constraints at the actual endpoint.
- Keep `sgl.gen` directly inside an assistant role for OpenAI chat without
  speculation. Use completion mode for `select` and dtype helpers.
- Treat Anthropic system extraction as destructive to `state.messages()` in
  this snapshot.
- Validate Vertex media bytes and MIME type with the installed SDK and actual
  input type.
- Remember that a successful example is not proof of retry, rate-limit,
  malformed-stream, multi-content, or concurrent-accounting behavior.

## Study checks

1. For one role-based program, identify the exact values of `text_`,
   `messages_`, template stops, and provider kwargs immediately before a call.
2. Explain why an unknown OpenAI-compatible model defaults to chat mode and how
   to force completion semantics.
3. Predict which generation fields survive through each of the four sampling
   conversion methods.
4. Explain what is stored in a variable and what advances the prompt when
   OpenAI returns `n=2`.
5. Trace chat API speculation from placeholders to the one provider response
   and list the conditions that make pattern matching fail.
6. Compare OpenAI's selection score with `RuntimeEndpoint` choice-policy
   metadata and explain why they are not interchangeable.
7. Given a model path, walk the matcher registry in order and identify whether
   the selected template was automatic, explicit-only, or the default fallback.
8. Explain why the DeepSeek Jinja regression test does not cover the frontend
   `deepseek-v3` record.
