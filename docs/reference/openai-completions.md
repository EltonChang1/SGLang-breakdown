# OpenAI Completions File Reference

This reference accompanies [OpenAI Completions and Chat
Completions](../08-openai-completions.md). Coverage labels below are
file-level decisions for commit
[f464e77d17a3908ad0ea32547b1e8b039bcbd354](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354).
A partial label names the exact boundary that remains.

## Runtime files

### python/sglang/srt/entrypoints/http_server.py

[Handler construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L302-L339)
stores completion and chat adapters in FastAPI application state after the
tokenizer and template managers exist. Chat is instantiated through
TokenizerManager.serving_chat_class, while completion uses the concrete
OpenAIServingCompletion directly. The same chat instance is injected into the
Anthropic adapter, making OpenAI chat preparation a reusable internal
compatibility layer.

[openai_v1_completions and openai_v1_chat_completions](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1712-L1730)
attach JSON-content validation through the route dependency, let FastAPI parse
the Pydantic request, and delegate to the stored adapter's handle_request.

The file remains **partial**. Startup, readiness, native generation/abort, and
the OpenAI completion/chat route and construction slices are covered.
Embedding, scoring, reranking, Responses, transcription, Realtime, Anthropic,
Ollama, gRPC, management, batch, file, tool-server, and remaining service
routes retain their owning passes.

### python/sglang/srt/entrypoints/openai/__init__.py

[The package marker](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/__init__.py)
is empty. Import behavior comes from explicitly imported sibling modules; the
package performs no registration or aggregate export. The file is
**covered**.

### python/sglang/srt/entrypoints/openai/protocol.py

The completion/chat slice contains these symbol groups:

| Lines | Symbols | Responsibility |
| --- | --- | --- |
| [77-257](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L77-L257) | ModelCard, ErrorResponse, parser protocols, logprob/usage/format records | Shared compatibility vocabulary and optional structured constraints |
| [314-415](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L314-L415) | deprecated DP migration, CompletionRequest | Text-completion wire schema and positive max-token validation |
| [418-528](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L418-L528) | SpecTokensDetails, SglExt, completion response records | Non-stream and stream completion output with omission serializers |
| [531-820](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L531-L820) | content parts, messages, tools, tool choice, reasoning types | Chat inputs, role/media/tool normalization, and extensions |
| [823-1173](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L823-L1173) | ChatCompletionRequest | Request defaults, migrations, reasoning normalization, and sampling conversion |
| [1176-1271](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1176-L1271) | chat response and delta records | Visible content, reasoning, tool calls, logprobs, usage, and extensions |
| [2009-2037](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L2009-L2037) | request metadata and processing results | Internal renderer/tool-parser return types |

Omission serializers are protocol behavior: absent hidden states, token IDs,
meta_info, and sglext do not appear as explicit nulls. Usage preserves the
OpenAI-compatible top-level counters while adding cache and multimodal prompt
detail. JsonSchemaResponseFormat uses StrictBool so strings and integers are
not silently coerced to strict flags.

The file is **partial**. Completion/chat requests, responses, content parts,
tools, usage, formats, and internal processing records are covered. Files and
batches, embeddings, classify, score, rerank, tokenize/detokenize, Responses
API, and transcription schemas remain for their protocol guides.

### python/sglang/srt/entrypoints/openai/serving_base.py

[OpenAIServingBase](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_base.py#L26-L293)
is the complete endpoint adapter template:

- the constructor caches the allowed custom-label set;
- _parse_model_parameter and _resolve_lora_path implement adapter selection;
- handle_request fixes validation, logging, conversion, timing, stream
  selection, and exception translation order;
- the abstract request prefix, conversion, validation, streaming, and
  non-streaming hooks define the subclass surface;
- create_error_response and create_streaming_error_response produce the two
  transport-specific error shapes; and
- the header helpers filter labels, carry a routing key, and give the DP-rank
  header priority over the body.

[_generate_request_id_base](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_base.py#L140-L149)
returns None before its legacy RID code, so the advertised cmpl- and chatcmpl-
prefix hooks do not assign native request IDs in this path. GenerateReqInput
normalization owns missing IDs instead. The file is **covered**.

### python/sglang/srt/entrypoints/openai/serving_completions.py

[OpenAIServingCompletion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_completions.py#L46-L688)
is the entire text-completion adapter:

| Methods | Role |
| --- | --- |
| [constructor, prefix, validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_completions.py#L49-L66) | Bind TemplateManager and reject empty prompt families |
| [_convert_to_internal_request](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_completions.py#L68-L142) | Template optional prompts and map OpenAI plus SGLang fields to GenerateReqInput |
| [_build_sampling_params](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_completions.py#L144-L190) | Rename sampling fields and translate response formats |
| [stream setup and generator](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_completions.py#L192-L499) | Prime validation; track per-choice offsets, logprobs, IDs, usage, aborts, and terminal extension chunks |
| [non-stream path and response builder](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_completions.py#L501-L639) | Flatten results to choices and aggregate usage and extensions |
| [echo helpers](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_completions.py#L641-L688) | Recover and decode each prompt for stream and non-stream response prefixing |

The adapter accepts best_of, suffix, user, session_params, and body
custom_labels through the request model but never reads them. It reads
session_id and header-derived custom labels. This distinction is part of the
file's compatibility contract. The file is **covered**.

### python/sglang/srt/entrypoints/openai/serving_chat.py

The file is organized into six layers:

| Lines | Layer | Key behavior |
| --- | --- | --- |
| [14-240](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L14-L240) | Module helpers | Thinking mode, tool-content/argument normalization, media patch aggregation, Kimi placeholder safety, video metadata |
| [249-717](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L249-L717) | Construction and custom encoders | Parser/config overlays, encoder selection, assistant-prefill rules, Kimi/Inkling paths, usage adjustments |
| [719-1097](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L719-L1097) | Semantic stream chunks and request conversion | Parser-aware chunking, validation, prompt/media choice, native field mapping, header overrides |
| [1099-1512](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L1099-L1512) | Message processing | Tool constraints, input-ID bypass, Jinja/custom/conversation rendering, media extraction, stops |
| [1514-2232](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L1514-L2232) | Response adapters | Stream lifecycle, usage/extensions, non-stream response, logprobs, tool IDs and calls |
| [2234-2724](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_chat.py#L2234-L2724) | Reasoning and tool stream state | Reasoning parser lifecycle, model toggles/history, incremental tool parsing and argument drain |

The central invariant is ownership: one renderer owns message framing; the
reasoning parser owns reasoning/content separation; the function-call parser
owns model-native tool syntax; and GenerateReqInput owns runtime execution.
Mixing those layers, such as stripping special tokens before a parser sees its
markers, loses structure.

The file remains **partial** despite the end-to-end adapter trace. Generic
request validation, mapping, rendering, response shaping, usage, logprobs, and
tool/reasoning handoff are covered. DeepSeek-3.2/4, Kimi K3, Inkling, every
reasoning-mode family, and every model-specific tool-parser branch need their
own parser/template passes before the file can be called complete.

### python/sglang/srt/entrypoints/openai/chat_encoding.py

The module is the single dispatch home for custom chat encoders:

- [_detect_dsv4_reasoning_effort_profile](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/chat_encoding.py#L24-L78)
  reads a local or pinned-revision checkpoint encoder, rejects files above one
  MiB, parses only literal top-level assignments, and distinguishes official
  from preview effort profiles without executing checkpoint code.
- [profile validation and resolution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/chat_encoding.py#L81-L105)
  give an explicit model-config override priority and otherwise fall back to
  preview when inspection fails.
- [resolve_chat_encoding_spec](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/chat_encoding.py#L108-L143)
  resolves parser override before architecture and template availability.
- [spec_owns_reasoning_history](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/chat_encoding.py#L146-L157)
  gives every non-default encoder the safe ownership rule.
- [encode_simple_chat](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/chat_encoding.py#L160-L211)
  provides offline plain-text encoding and deliberately excludes tools, media,
  and assistant continuation.

Remote checkpoint inspection can fail because of missing files, network,
revision, size, syntax, or non-literal definitions; all degrade to the preview
profile rather than executing arbitrary code. The file is **covered**.

### python/sglang/srt/entrypoints/openai/usage_processor.py

[UsageProcessor](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/usage_processor.py#L9-L126)
is a stateless aggregation layer. _details_if_cached suppresses empty cache
detail. calculate_response_usage strides results by n for prompt/cache input
counts but sums every completion/reasoning count. calculate_streaming_usage
does the equivalent using choice indexes. calculate_token_usage attaches
cache and multimodal prompt details and computes total_tokens as prompt plus
completion; reasoning tokens are reported separately rather than added a
second time. The file is **covered**.

### python/sglang/srt/entrypoints/openai/utils.py

The complete helper catalog is:

| Lines | Helpers | Contract |
| --- | --- | --- |
| [18-52](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/utils.py#L18-L52) | to_openai_style_logprobs | Native tuples to legacy parallel arrays; text offsets remain unsupported at -1 |
| [55-90](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/utils.py#L55-L90) | hidden-state helpers | Gate optional output and distinguish the last-mode payload from ordinary last-layer selection |
| [92-106](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/utils.py#L92-L106) | should_include_usage | Combine request final-usage option with the server default; continuous stats remain request-only |
| [109-202](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/utils.py#L109-L202) | routed/cache/speculative helpers | Gate extensions, normalize optional storage fields, and accept canonical or legacy speculative metrics |
| [205-240](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/utils.py#L205-L240) | convert_embeds_to_tensors | Preserve None, distinguish single/batch nesting, and create float32 replacement tensors |

For return_hidden_states=True, process_hidden_states_for_response returns the
last outer element when more than one exists but returns an empty list when
there is only one; return_hidden_states='last' returns the original object.
That non-obvious shape distinction belongs to callers. The file is
**covered**.

### python/sglang/srt/entrypoints/openai/sse_utils.py

[StreamDelta, StreamChoice, StreamChunk, and build_sse_content](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/sse_utils.py#L13-L99)
use msgspec and one reusable JSON encoder for chat content/reasoning/finish
chunks. reasoning_content is required at construction so it serializes even
when null; other default-null fields can be omitted. The builder emits exactly
one choice and frames bytes as data, JSON, and a blank line. Tool-call and
hidden-state chunks use the richer Pydantic response models elsewhere. The
file is **covered**.

### Deferred encoder implementations

[encoding_dsv32.py](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/encoding_dsv32.py)
and
[encoding_dsv4.py](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/encoding_dsv4.py)
are reached by this adapter and remain **pending**. This pass establishes why
they are selected and what prompt IDs they return; their DSML grammar, role
rendering, reasoning history, task tokens, tool-call parsing, and error
recovery need dedicated model-format notes.

## Documentation and example files

### docs/docs/basic_usage/openai_api.mdx

[The nine-line page](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/openai_api.mdx)
is an OpenAI-compatible API navigation hub. It links completions, vision,
embeddings, and the separate Anthropic page; it defines no runtime contract.
The file is **covered**.

### docs/docs/basic_usage/openai_api_completions.mdx

[The tutorial](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/openai_api_completions.mdx#L1-L456)
launches a small server, demonstrates chat and text completions, documents
reasoning/template flags for selected model families, logit bias, sampling,
streaming, routed experts, structured-output navigation, and both LoRA
selection forms. Its executable examples are user orientation, not exhaustive
schema tests.

Two claims drift from this snapshot's code. 'Fully implements' is too broad
because accepted fields can be inert, and the completion routed-expert
paragraph says per-choice sgl_ext while both adapters build response-level
sglext. The LoRA precedence statement does match OpenAIServingBase. The file
is **covered**, including these accuracy caveats.

### docs/docs/basic_usage/openai_api_vision.mdx

[The vision tutorial](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/openai_api_vision.mdx#L1-L176)
shows the same chat route with ordered text/image_url parts through curl,
requests, and the OpenAI SDK, then shows multiple interleaved images. Actual
support remains model-dependent and flows through content-part validation,
template-format media extraction, and multimodal processing. The curl command
is executed twice consecutively in the page, an example duplication with no
protocol meaning. The file is **covered**.

### examples/runtime/openai_chat_with_response_prefill.py

[The example](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/runtime/openai_chat_with_response_prefill.py#L1-L53)
sends the same system/user/trailing-assistant history twice. With
continue_final_message the open '{' prefix is continued; without it the
adapter's generic rule treats the assistant text as user input before a fresh
assistant turn. It requires a live Llama server, performs no assertion, and
contains a display typo, continue_final_messagem. The file is **covered**.

## Test files

### test/registered/unit/entrypoints/openai/test_serving_completions.py

[ServingCompletionTestCase](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/test_serving_completions.py#L63-L591)
contains nineteen tests covering prompt/token-ID mapping; cache_salt versus
extra_key; normalization
rejection of batch-only cache salt; all echo shapes; response-format mapping
and missing schema; non-stream token IDs; abort error SSE; exact token-ID/text
delta coverage in cumulative and incremental modes; cache-detail sglext; and
single/parallel speculative details in stream and non-stream ordering.

It does not exercise the FastAPI route, base-class exception mapping, live
disconnect cancellation, completion templates, logprob values, usage options,
or accepted-but-inert schema fields. Those are meaningful missing integration
cases, not missing contents of this focused unit file. The file is
**covered**.

### test/registered/unit/entrypoints/openai/test_protocol.py

The completion/chat slice verifies defaults and extensions, strict JSON
booleans, content hashes, sampling precedence, tool-choice defaults,
reasoning normalization/ranges, ordered thinking roles, response-format
migration and renderer gating, inline audio conversion, optional-field
serialization, defer_loading propagation, tool references, invalid tool
choice, and negative completion token caps
([completion/chat classes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/test_protocol.py#L74-L775)).

The file remains **partial**: these completion/chat and shared model cases are
covered; later protocol classes in protocol.py and their tests retain the
embedding, score, rerank, tokenize, Responses, and transcription passes.

### test/registered/unit/entrypoints/openai/test_serving_chat.py

The large unit suite uses mock tokenizer/template managers to cover:

- control-plane parser overlays, media validation, native field/header
  conversion, stream-only extension rejections, and input-ID bypass;
- default/Jinja/custom encoder selection, reasoning settings, Kimi,
  DeepSeek-3.2/4, Inkling, assistant continuation, and tool schema fallbacks;
- tool-schema validation, constraint conflicts, required/auto/native/JSON
  parsing, tool IDs, streaming argument drain, and malformed-call fallback;
- abort streams, cumulative/incremental deltas, parser-aware logprobs, usage,
  cache/speculative/routed extension placement, and token/meta_info returns;
  and
- reasoning-mode dispatch, parser toggles, history ownership, and response
  whitespace.

The suite is **partial** in this pass. All test names and the adapter-facing
behavior groups above are indexed, but exact model-specific encoder/parser
fixtures and reasoning-family assertions remain with the deferred model-format
passes. This prevents a broad test file from making those source modules look
complete prematurely.

### test/registered/lora/test_lora_openai_api.py

[The full unit suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/lora/test_lora_openai_api.py#L1-L253)
uses a minimal concrete OpenAIServingBase to cover no-adapter, explicit,
model-embedded, path, whitespace, multiple-colon, empty, list, precedence,
Unicode, and special-character cases. It validates string resolution only;
actual adapter existence, loading, batching, and inference remain LoRA
integration concerns. Every test and fixture in this file is explained, so it
is **covered**.

### test/registered/openai_server/validation/test_request_length_validation.py

[The four OpenAI cases](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/validation/test_request_length_validation.py#L39-L106)
launch a 1,000-token server and verify over-context input for non-stream and
stream, the smaller generation-aware allowable length, and an oversized
max_tokens adapter error. The remaining native token-logprob cases were
covered in the native protocol pass. Together the two notes explain every
test, fixture, launch argument, and cleanup path. The file is **covered**.

### test/registered/openai_server/validation/test_large_max_new_tokens.py

[The integration case](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/validation/test_large_max_new_tokens.py#L34-L108)
starts a server whose context is larger than its token pool, submits four
chat requests with no explicit output cap, and scans stderr until all four are
simultaneously running. It tests admission estimation under
SGLANG_CLIP_MAX_NEW_TOKENS_ESTIMATION, not response text. The local
all_requests_running variable is assigned only after a matching log line, so
failure may surface as an unbound variable after the futures finish rather
than a purpose-built assertion message. The file is **covered**.

### Additional test boundaries

The inherited matched-stop integration shell, basic OpenAI server suite,
manual continuous-usage tests, function-calling suites, vision suites, LoRA
end-to-end tests, Rust-server tests, and gateway/router compatibility tests
remain pending. They exercise broader runtime and deployment matrices rather
than the adapter core isolated here.
