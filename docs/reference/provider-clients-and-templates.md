# Provider Client and Template File Reference

This reference covers the provider-specific frontend backends, the complete
lightweight chat-template registry, the provider examples, and their focused
manual tests at commit
[`f464e77d17a3908ad0ea32547b1e8b039bcbd354`](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354).
Read [Provider Clients and Prompt Templates](../05-provider-clients-and-templates.md)
for the teaching path and [Frontend Language Execution](../04-frontend-language.md)
for the interpreter that calls these files.

## `python/sglang/lang/backend/openai.py`

**Status: covered.** The file implements OpenAI and OpenAI-compatible chat and
completion calls, constrained completion helpers, API speculation, streaming,
choice selection, retry behavior, and aggregate token usage
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L1-L475)).

### Import and initialization boundary

`openai` and `tiktoken` are one optional-dependency unit: failure to import
either stores the exception in both names, and construction re-raises it.
`create_logit_bias_int` scans private tiktoken tables, retains at most 299
digit/space tokens, and adds end-of-text to stay within the stated 300-entry
API limit
([lines 15-39](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L15-L39)).
This depends on private tokenizer attributes and on an `<|endoftext|>` special
token being present.

`TokenUsage.reset` zeroes both counters. `OpenAI.__init__` chooses the regular
or Azure SDK client, falls back to `cl100k_base` for unknown model names,
derives the chat template, and classifies only
`gpt-3.5-turbo-instruct` as completion-style by default
([lines 42-105](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L42-L105)).
The stored assistant prefix is later the chat-generation placement guard.

### Generation and constraints

`generate` selects message or text input. Chat input requires an open assistant
role unless API speculation is active. The ordinary branch converts sampling
arguments and chooses the model-name-dependent token-limit key
([lines 140-181](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L140-L181)).

String dtype is emulated by adding an opening quote to the prompt, stopping at
the next quote, and restoring both quotes. Integer dtype uses the digit/space
logit bias and a space stop. Both reject chat models; other dtypes raise
`ValueError`
([lines 182-222](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L182-L222)).
The return metadata is always empty.

`generate_stream` supports only unconstrained dtype. It performs the same
message-versus-text selection, but does not apply the ordinary branch's
`o1`/`o3` token-limit-key filtering before calling the stream helper
([lines 283-310](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L283-L310)).
Consequently the converted kwargs still contain both `max_tokens` and
`max_completion_tokens` on this path.

### Speculation and selection

`_prepare_spec_execution` fixes one shared speculative token limit, requires
all non-stop sampling fields to agree across placeholders, warns while
overriding each generation's max tokens, and records stop/name entries
([lines 109-138](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L109-L138)).
`spec_fill` records literal assistant segments. `spec_pattern_match` consumes
fixed text and discovers generated substrings using their stop values;
`role_end_generate` tries at most three provider completions, then publishes
whatever text remains in the format records even when no attempt matched
([lines 224-281](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L224-L281)).
The state is backend-instance-global and explicitly unsupported for
multithreaded batch use.

`select` rejects chat models, tokenizes choices, and performs a biased
one-token-at-a-time greedy walk. It ignores the `choices_method` argument and
returns match-count scores
([lines 312-380](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L312-L380)).
Empty choice lists fail at `max`; empty tokenized choices and a returned token
outside the active candidates violate later assumptions. Selection adds prompt
usage but assigns completion usage on each iteration instead of accumulating
it.

### SDK helpers

`openai_completion` removes unsupported `ebnf`, calls chat or completion
resources, preserves multiple outputs, adds usage, and retries API,
connection, or rate-limit errors three times with five-second sleeps
([lines 383-422](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L383-L422)).

`openai_completion_stream` requests an SDK-specific usage-bearing final chunk,
yields only the first choice's text deltas, and reads usage from the final
loop value after iteration
([lines 425-475](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/openai.py#L425-L475)).
An OpenAI-compatible endpoint that omits final usage, rejects
`stream_options`, or does not accept both token-limit fields can fail this
adapter even if its basic response shape is compatible.

## `python/sglang/lang/backend/anthropic.py`

**Status: covered.** The file is a synchronous Anthropic Messages adapter
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/anthropic.py#L1-L73)).

Construction re-raises a missing optional dependency, uses the `claude`
frontend template, and lets the SDK resolve credentials and other keyword
arguments
([lines 6-24](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/anthropic.py#L6-L24)).

Both generation methods use existing messages or wrap all accumulated text in
one user message. A leading system message is popped from the same list object
owned by the executor and sent separately. Non-streaming returns only the
first content block's `.text`; streaming yields `text_stream`. Neither path
converts media, records usage, or adds retry/error translation
([ordinary](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/anthropic.py#L26-L49),
[streaming](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/anthropic.py#L51-L73)).

## `python/sglang/lang/backend/litellm.py`

**Status: covered.** The file adapts SGL programs to LiteLLM's chat-completion
function
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/litellm.py#L1-L90)).

On import failure it stores the exception and attaches `num_retries=1`, which
allows the default parameter expression to be evaluated; construction then
re-raises the original exception. A successful constructor stores its model,
model-matched or explicit template, and client fields
([lines 8-48](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/litellm.py#L8-L48)).

Both paths prefer existing OpenAI-shaped messages and otherwise wrap `text_`
as one user message. Ordinary generation returns the first message choice;
streaming skips chunks whose first delta has `None` content. Client parameters
and the lossy LiteLLM sampling mapping are expanded into every call
([lines 50-90](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/litellm.py#L50-L90)).

## `python/sglang/lang/backend/vertexai.py`

**Status: covered.** The file initializes Vertex AI, converts frontend text,
messages, and images to generative-model inputs, and implements ordinary and
streaming calls
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/vertexai.py#L1-L148)).

Construction raises the stored import exception when the SDK is absent, reads
required `GCP_PROJECT_ID` and optional `GCP_LOCATION`, performs process-global
SDK initialization, and uses the `default` frontend template
([lines 9-36](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/vertexai.py#L9-L36)).

Generation chooses converted messages, text/image parts, or raw text. Each call
constructs `GenerativeModel` and `GenerationConfig`; streaming adds
`stream=True` and yields each response object's text
([lines 38-83](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/vertexai.py#L38-L83)).

`text_to_vertexai_input` splits on one image token per accumulated image and
interleaves text with `Image.from_bytes` values. Too few token segments raises
from `pop(0)`; extra markers leave unconsumed segments; the supplied value is a
base64 string rather than decoded bytes
([lines 85-97](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/vertexai.py#L85-L97)).

`messages_to_vertexai_input` maps `assistant` to `model`, emulates a system
message with a user/model pair, and assumes every non-string content list
starts with one text item followed by `image_url` items. Unknown roles leave
`vertexai_msg` undefined. Media data is copied from the data URL after the
first comma and labeled JPEG regardless of original encoding
([lines 99-148](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/vertexai.py#L99-L148)).

## `python/sglang/lang/backend/crusoe.py`

**Status: covered.** This is a complete thin configuration subclass of
`OpenAI`
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/crusoe.py#L1-L43)).

The explicit key wins over `CRUSOE_API_KEY`; absence raises before OpenAI client
construction. The explicit base URL wins over
`CRUSOE_BASE_URL`. All remaining keyword arguments and the optional template
flow to `OpenAI.__init__`, so every inherited capability and failure mode still
applies
([lines 23-43](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/crusoe.py#L23-L43)).

## `python/sglang/lang/chat_template.py`

**Status: covered.** The record/style behavior, mutable registries, all 27
concrete records, all 16 matching functions, selection precedence, fallback,
and standalone demonstration are explained here
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L1-L678)).

### Record and registry semantics

`ChatTemplateStyle` has plain and Llama-2 modes. `ChatTemplate` holds a name,
optional default system prompt, role wrapper map, stops, image/audio markers,
and style. Unknown roles receive empty wrappers. Llama-2 mode merges the first
system and user structure; `get_prompt` replaces an explicit system message
whose content is `None` with the default and otherwise concatenates messages in
order
([lines 7-54](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L7-L54)).

Template registration overwrites the name key without a duplicate check.
Matcher registration appends, and model lookup returns the first match before
falling back to `default`
([lines 57-78](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L57-L78)).
Custom backend constructor arguments can bypass model-name lookup altogether.

### Template catalog

“Generic media” means the dataclass defaults `<image>` and `<audio>` remain in
place. A dash in the stop column means the record adds no generation stop.

| Record | Source | Format/default | Stops | Media | Automatic selection |
| --- | --- | --- | --- | --- | --- |
| `default` | [81-91](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L81-L91) | `SYSTEM/USER/ASSISTANT:` labels; no default | — | Generic | Fallback only |
| `claude` | [93-103](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L93-L103) | Human/Assistant separators; no default | — | Generic | `orion`; Anthropic chooses explicitly |
| `chatml` | [105-117](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L105-L117) | ChatML; no default | `<|im_end|>` | Generic | TinyLlama |
| `chatml-llava` | [119-132](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L119-L132) | ChatML; helpful default | `<|im_end|>` | `<image>\n` | selected LLaVA 34B/Qwen2 names |
| `qwen` | [137-149](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L137-L149) | ChatML; helpful default | `<|im_end|>` | Generic | Qwen chat/instruct excluding LLaVA |
| `qwen2-vl` | [152-165](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L152-L165) | ChatML; helpful default | `<|im_end|>` | Qwen vision triplet | Qwen names containing VL |
| `vicuna_v1.1` | [168-182](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L168-L182) | Vicuna labels; long default | — | ` <image>\n` | Vicuna, LLaVA 1.5, LLaVA Next Video 7B |
| `llama-2-chat` | [184-195](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L184-L195) | `[INST]`/`<<SYS>>`; special style | — | Generic | Llama-2 Chat, CodeLlama Instruct |
| `mistral` | [198-210](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L198-L210) | `[SYSTEM_PROMPT]`/`[INST]` | `</s>` | `[IMG]` | Pixtral or Mistral/Mixtral Instruct |
| `llama-3-instruct` | [212-233](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L212-L233) | Llama-3 headers | `<|eot_id|>` | `<|image|>` | Llama-3 Instruct |
| `minicpmv` | [236-248](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L236-L248) | `user:`/`assistant:` | IM end, end-of-text | MiniCPM image wrapper | MiniCPM-V |
| `janus-pro` | [250-271](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L250-L271) | DeepSeek markers; capitalized `User` key | DeepSeek sentence end | `<image_placeholder>\n` | Every Janus name |
| `minicpmo` | [274-287](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L274-L287) | `user:`/`assistant:` | IM end, end-of-text | MiniCPM image and audio wrappers | MiniCPM-O |
| `janus` | [289-310](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L289-L310) | DeepSeek markers; lowercase `user` | DeepSeek sentence end | `<image_placeholder>\n` | Explicit only |
| `llama-3-instruct-llava` | [313-334](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L313-L334) | Llama-3 headers | `<|eot_id|>` | `<image>\n` | Explicit only |
| `llama-4` | [337-358](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L337-L358) | Llama-4 headers | `<|eot|>` | `<|image|>` | Explicit only |
| `yi-1.5` | [361-373](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L361-L373) | ChatML-like with user opening assistant | `<|im_end|>` | Generic | Yi 1.5 Chat |
| `yi-vl` | [376-390](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L376-L390) | Human/Assistant; bilingual default | — | Yi placeholder | Yi-VL excluding LLaVA |
| `gemma-it` | [392-405](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L392-L405) | Gemma turn tokens | — | start-of-image/audio | Gemma IT and Gemma-3 |
| `gemma-4-it` | [407-418](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L407-L418) | Gemma-4 turn tokens | — | Generic | Gemma-4 IT before generic Gemma |
| `dbrx-instruct` | [420-431](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L420-L431) | ChatML-like; long DBRX default | `<|im_end|>` | Generic | DBRX Instruct |
| `c4ai-command-r` | [433-450](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L433-L450) | Start/end-of-turn role tokens | — | Generic | C4AI Command-R |
| `internvl-2-5` | [453-464](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L453-L464) | ChatML; Chinese default | IM/action end | Generic | `internvl2_5` |
| `interns1` | [466-477](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L466-L477) | ChatML; reasoning-oriented default | IM/action end | Generic | Intern-S1 or InternS1 |
| `granite-3-instruct` | [479-499](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L479-L499) | Granite role tokens | `<|end_of_text|>` | Generic | Granite Instruct |
| `deepseek-v3` | [501-521](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L501-L521) | DeepSeek user/assistant markers | DeepSeek sentence end | Generic | DeepSeek V3/R1 excluding Base |
| `glm-4v` | [524-537](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L524-L537) | GLM role tokens | user/end-of-text/observation | `<|image|>` | GLM-4V spellings |

The `janus-pro` `User`/`user` mismatch is observable because unknown roles get
empty wrappers. `janus` has the lowercase key but is not returned by automatic
matching. The standalone `__main__` block only renders a Llama-2 example; it is
demonstration code, not registry validation
([lines 668-678](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L668-L678)).

### Matcher catalog and precedence

Matchers execute in the table's order. Conditions within one matcher also
execute top to bottom.

| Order | Matcher | Model-path condition | Result |
| ---: | --- | --- | --- |
| 1 | [`match_deepseek`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L540-L545) | DeepSeek V3 or R1, but not Base | `deepseek-v3` |
| 2 | [`match_orion`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L548-L551) | contains Orion | `claude` |
| 3 | [`match_deepseek_janus_pro`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L554-L557) | contains Janus | `janus-pro` |
| 4 | [`match_dbrx`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L560-L565) | contains DBRX and Instruct | `dbrx-instruct` |
| 5 | [`match_vicuna`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L568-L571) | Vicuna, LLaVA 1.5, or LLaVA Next Video 7B | `vicuna_v1.1` |
| 6 | [`match_llama2_chat`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L574-L581) | Llama-2 Chat or CodeLlama Instruct | `llama-2-chat` |
| 7 | [`match_mistral`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L584-L587) | Pixtral or Mistral/Mixtral Instruct | `mistral` |
| 8 | [`match_llama3_instruct`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L590-L593) | Llama-3 followed by Instruct | `llama-3-instruct` |
| 9 | [`match_chat_ml`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L596-L613) | TinyLlama; Qwen VL; GLM-4V; Qwen chat/instruct excluding LLaVA; selected LLaVA 34B/Qwen2 names | corresponding ChatML-family record |
| 10 | [`match_chat_yi`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L616-L623) | Yi-VL excluding LLaVA, then Yi-1.5 Chat | `yi-vl` or `yi-1.5` |
| 11 | [`match_gemma`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L626-L631) | Gemma-4 IT first; other Gemma IT or Gemma-3 second | `gemma-4-it` or `gemma-it` |
| 12 | [`match_openbmb_minicpm`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L634-L639) | MiniCPM-V, then MiniCPM-O | `minicpmv` or `minicpmo` |
| 13 | [`match_c4ai_command_r`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L642-L645) | C4AI Command-R | `c4ai-command-r` |
| 14 | [`match_granite_instruct`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L648-L651) | Granite followed by Instruct | `granite-3-instruct` |
| 15 | [`match_internvl_chat`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L654-L657) | `internvl2_5` | `internvl-2-5` |
| 16 | [`match_interns1_chat`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L660-L665) | Intern-S1 or InternS1 | `interns1` |

## Provider example files

**Status: covered for every file in this table.** These examples are concise
runnable clients, so proportional coverage means identifying the program shape,
backend configuration, and non-obvious behavior or execution requirement.

| File | What it demonstrates | Important reading note |
| --- | --- | --- |
| [`anthropic_example_chat.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/anthropic_example_chat.py#L1-L73) | Two-turn Anthropic single, stream, and batch | Requires live Anthropic credentials; system-pop mutation is absent because it starts with user |
| [`anthropic_example_complete.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/anthropic_example_complete.py#L1-L68) | Role-free few-shot prompt in all three modes | Still uses Anthropic Messages: backend wraps the whole text as one user message |
| [`azure_openai_example_chat.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/azure_openai_example_chat.py#L1-L83) | Azure client construction plus chat modes | Docstring names another script; endpoint is a hard-coded sample and key is indexed from environment |
| [`gemini_example_chat.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/gemini_example_chat.py#L1-L73) | Vertex role conversion in single, stream, batch | Requires Google project/application credentials beyond the named project variable as configured by SDK |
| [`gemini_example_complete.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/gemini_example_complete.py#L1-L68) | Vertex raw-text generation | Uses raw string input rather than a separate completion API |
| [`gemini_example_multimodal_chat.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/gemini_example_multimodal_chat.py#L1-L30) | Two inline images inside one user role | Exercises message-list media conversion and assumes paths relative to the quick-start directory |
| [`openai_example_chat.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/openai_example_chat.py#L1-L74) | Baseline chat single, stream, batch | Each generation is directly inside assistant, satisfying placement rule |
| [`openai_example_complete.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/openai_example_complete.py#L1-L68) | Recognized instruct completion model | Stop/temperature survive conversion; expected capitals make it a live-model assertion |
| [`openai_example_n.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/openai_example_n.py#L1-L71) | `n=2` variable followed by another turn | Variable is a list, but only choice zero continues in message text |
| [`openai_example_o1.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/openai_example_o1.py#L1-L57) | `o1` token-limit compatibility in non-streaming chat | Docstring names the generic chat example; no stream path is attempted |
| [`openrouter_example_chat.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/openrouter_example_chat.py#L1-L81) | OpenAI-compatible `base_url` and environment key | Docstring names Together's script; unknown model defaults to chat |
| [`orcarouter_example_chat.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/orcarouter_example_chat.py#L1-L83) | Routed OpenAI-compatible model name | Adapter does not know which downstream model is chosen and uses default template matching on router name |
| [`together_example_chat.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/together_example_chat.py#L1-L81) | Together chat through OpenAI client | Model name matches Mistral template and defaults to chat |
| [`together_example_complete.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/quick_start/together_example_complete.py#L1-L76) | Same model/endpoint forced to completion | Explicit `is_chat_model=False` is the decisive difference |
| [`openai_chat_speculative.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/usage/openai_chat_speculative.py#L1-L155) | Formatted multi-field chat speculation and normal comparison | Documents one assistant-region/stop-per-field invariant and intentionally exercises rejected streaming |
| [`openai_speculative.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/usage/openai_speculative.py#L1-L54) | Completion speculation with/without a few-shot format | Prints shared prompt-token usage rather than asserting deterministic savings |
| [`parallel_sample.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/usage/parallel_sample.py#L1-L40) | Five forks, OpenAI completion selection, gathered variables | Choice works because the backend is the recognized instruct model; default join gathers variables only |
| [`streaming.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/frontend_language/usage/streaming.py#L1-L49) | Synchronous and async consumption of one named streamed variable | `text_async_iter` adapts the same blocking executor events; provider client itself is synchronous |

## Provider-focused tests

### `test/manual/lang_frontend/test_openai_backend.py`

**Status: covered.** This manual, credentialed integration suite constructs one
instruct, one chat, and one vision backend, then delegates 14 tests to shared
frontend programs
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/lang_frontend/test_openai_backend.py#L1-L92)).

The instruct client owns few-shot completion, selection, integer/JSON dtype,
variable reuse, Python tool use, ReAct, fork decoding/encoding, streaming, and
completion speculation. Chat owns multi-turn roles and chat speculation;
vision owns image QA. It is not part of the registered deterministic unit suite
and requires live provider behavior. The wrapper itself does not isolate retry,
parameter-loss, message mutation, malformed stream, or concurrent usage cases.

### `test/manual/test_crusoe_backend.py`

**Status: covered.** The live half sets one default Crusoe backend and reuses
shared multi-turn, streaming, parallel-decoding, and parallel-encoding programs
([lines 24-48](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/test_crusoe_backend.py#L24-L48)).
The local half temporarily removes the environment key, checks the missing-key
error, and verifies explicit key and custom URL construction
([lines 51-75](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/test_crusoe_backend.py#L51-L75)).
Those construction tests instantiate the OpenAI SDK client and tokenizer but
do not make inference calls.

### `test/manual/test_deepseek_chat_templates.py`

**Status: covered.** This file loads three Jinja assets from
`examples/chat_template`, renders them with common token/context values, and
checks four tool-call cases: dict arguments, pre-serialized string arguments,
mixed multiple calls, and calls with ordinary assistant content
([loader](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/test_deepseek_chat_templates.py#L15-L54),
[test cases](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/manual/test_deepseek_chat_templates.py#L56-L314)).
Its invariant is that JSON keys/values appear without double escaping. It never
imports the frontend template registry, so it supplies no evidence for the
`deepseek-v3` prefix/suffix record or matcher.

### `python/sglang/test/test_programs.py` provider slice

**Status: partial.** Only the shared functions reached by the two provider
wrappers are covered here; the remaining frontend test-program catalog retains
its later test pass.

| Shared program | Source | Contract exercised by provider suites |
| --- | --- | --- |
| `test_few_shot_qa` | [17-42](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L17-L42) | deterministic completion and ordered batch outputs |
| `test_mt_bench` | [45-63](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L45-L63) | two turns and both role-construction syntaxes |
| `test_select` | [66-97](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L66-L97) | three-way completion selection |
| `test_decode_int` / `test_decode_json` | [100-160](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L100-L160) | integer/string dtype emulation and parseable scoped JSON |
| `test_expert_answer` | [163-183](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L163-L183) | generated variable reuse in a later prompt |
| `test_tool_use` | [186-205](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L186-L205) | generation-driven local Python evaluation and variable scope |
| `test_react` | [208-241](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L208-L241) | repeated selection controlling Python branches |
| `test_parallel_decoding` | [244-279](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L244-L279) | forked detailed generations, gather, and final summary |
| `test_parallel_encoding` | [282-311](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L282-L311) | concatenate-and-append request with text fallback on these clients |
| `test_image_qa` | [314-329](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L314-L329) | OpenAI vision data URL and output content |
| `test_stream` | [332-353](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L332-L353) | whole-program and named-variable delta iterators |
| `test_completion_speculative` | [440-479](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L440-L479) | shared usage counter reports fewer prompt tokens with speculation |
| `test_chat_completion_speculative` | [482-500](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/test/test_programs.py#L482-L500) | one formatted assistant region is resolved by chat speculation |

These are mostly outcome assertions against changing live models. They are
useful compatibility smoke tests, but they do not replace mocked unit tests for
exact request bodies, errors, or state transitions.
