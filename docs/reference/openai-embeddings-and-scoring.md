# Embedding and Scoring File Reference

This reference supports [Embeddings, Classification, Scoring, Reranking, and
Tokenization](../09-openai-embeddings-and-scoring.md). Status statements apply
only to commit
[`f464e77d17a3908ad0ea32547b1e8b039bcbd354`](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354).
The shared manager and protocol files remain partial outside the named slices.

## Runtime and configuration files

### `python/sglang/srt/configs/embedding_model_spec.py`

**Status: covered.** Six enums separate public task, pooling, execution,
attention, static breakable-CUDA-graph prefill policy, and derived BCG
eligibility. `EmbeddingModelSpec` is immutable capability metadata;
`bcg_eligibility` derives the compatibility summary and `as_dict` creates the
stable external form
([types and record](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/embedding_model_spec.py#L13-L115)).

`_EMBEDDING_ARCHITECTURES` and `_CLASSIFICATION_ARCHITECTURES` are deliberately
conservative architecture registries. `embedding_support_matrix` derives
documentation/tool rows from the same embedding registry and adds the
predicate-based EmbeddingGemma row. `_embedding_gemma_spec` declares its
bidirectional mean-pooling, full-encoder BCG, and safe cache-disable policy;
`_native_embedding_spec` supplies the common native architecture defaults
([registries and matrix](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/embedding_model_spec.py#L118-L171),
[spec factories](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/embedding_model_spec.py#L174-L220)).

`resolved_embedding_plan` overlays live enablement, Matryoshka dimensions,
prefill graph capture, and cache policy without importing `ServerArgs` or
`ModelConfig`. `resolve_embedding_model_spec` prioritizes EmbeddingGemma,
classification heads, registered embedding architectures, explicit decoder
intent, then a no-capability record. Unknown decoder architectures are never
auto-promoted
([resolved plan](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/embedding_model_spec.py#L223-L265),
[resolver](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/embedding_model_spec.py#L268-L344)).

### `python/sglang/srt/configs/model_config.py`

**Status: partial.** After loading an isolated Hugging Face config,
`ModelConfig.__init__` recognizes EmbeddingGemma and resolves the declarative
embedding specification from checkpoint architectures plus explicit
`is_embedding` intent. That record becomes the stable input to later
server-argument capability adjustments
([embedding integration](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/model_config.py#L314-L340)).
Model loading, quantization, attention/head geometry, multimodal and backend
normalization, and the remaining derived properties retain their owning model
configuration passes.

### `python/sglang/srt/server_args.py`

**Status: partial.** The embedding slice of
`_handle_model_capability_adjustments` auto-enables unambiguous native
embedding architectures. EmbeddingGemma additionally disables radix reuse and
chunked prefill, enables tokenizer batch encode, disables decode graphs,
selects full-prefill breakable graphs on CUDA, raises unlocked capture sizing,
uses eager prefill off CUDA, and conditionally enables the Hopper/Blackwell
FA3/FA4 no-KV-pool path
([capability adjustment](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L4043-L4159)).
The general argument lifecycle is covered in the configuration reference;
other model/backend capability handlers retain later subsystem passes.

### `python/sglang/srt/entrypoints/http_server.py`

**Status: partial.** This pass covers construction of embedding, classify,
score, rerank, tokenize, and detokenize handlers; `/model_info` embedding-plan
readback; native `/encode` and `/classify`; OpenAI `/v1/embeddings`,
`/v1/classify`, `/v1/score`, `/v1/rerank`; and both tokenization aliases
([construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L269-L328),
[`/model_info`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L730-L774),
[native routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L943-L964),
[OpenAI embedding/token routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1733-L1790),
[score/rerank routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1901-L1951)).

Startup/native generation/OpenAI completion-chat slices were covered earlier.
Responses, transcription/realtime, model catalog, Anthropic, Ollama, Vertex,
SageMaker, remaining management endpoints, warmup details, and full server
assembly retain their owning passes.

### `python/sglang/srt/entrypoints/openai/protocol.py`

**Status: partial.** The newly covered schema slice is:

- `MultimodalEmbeddingInput`, `EmbeddingRequest`, `EmbeddingObject`, and
  `EmbeddingResponse` for dense vectors, output format, dimensions, LoRA, and
  embedding replacement inputs
  ([lines 1274-1309](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1274-L1309),
  [lines 1344-1348](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1344-L1348));
- `ClassifyRequest`, `ClassifyData`, and `ClassifyResponse` for label/probability
  output
  ([lines 1313-1341](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1313-L1341));
- `ScoringRequest` and `ScoringResponse`, including override and pooled-state
  shapes
  ([lines 1351-1384](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1351-L1384));
- rerank content unions, request validation/multimodal detection, and response
  document omission
  ([content types](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L637-L664),
  [request/response](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1387-L1441)); and
- tokenize/detokenize input exclusivity, chat conversion, and
  cardinality-preserving response records
  ([lines 1444-1503](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1444-L1503)).

Completion/chat schemas are covered in the earlier OpenAI reference. Responses,
transcription, file/batch operations, and their later serializers remain; the
2,116-line shared file is not complete.

### `python/sglang/srt/entrypoints/openai/serving_embedding.py`

**Status: covered.** `OpenAIServingEmbedding` validates output format and
nonempty homogeneous text/token inputs; converts single, batched, tokenized,
and multimodal input; applies registered-conversation, tokenizer-Jinja, then
raw-text template precedence; and keeps media parallel to rendered prompts
([validation and conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L30-L149)).

The converter resolves LoRA precedence and routing headers, enforces paired
embedding-override fields, and converts replacement vectors without resolving
positions. `_apply_jinja_template_to_embedding_inputs` normalizes content
parts, avoids padding in image-only Jinja input, and maps template failures to
bad requests
([remaining conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L150-L184),
[Jinja helper](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L186-L246)).

The public override schema has an outer per-input dimension. For a single HTTP
input, conversion preserves that dimension but the unsplit internal request
later expects its inner tensor list. The separate conversion and resolution
unit tests therefore do not prove the single-input HTTP integration.

The handler consumes the one final native result, normalizes single/batch
shape, serializes little-endian FP32 base64 when requested, preserves input
order, aggregates prompt usage, and reports the live model path
([execution and response](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L248-L308)).

### `python/sglang/srt/entrypoints/openai/serving_classify.py`

**Status: covered.** Initialization resolves the served output model name and
requires either config `id2label` or `num_labels` from which it synthesizes
`LABEL_N`. Conversion/validation handles string, string-batch, and flat-ID
input but propagates only request ID and priority
([initialization and conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_classify.py#L28-L77),
[validation and mapping](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_classify.py#L79-L127)).

Response shaping softmaxes each head vector, chooses the logit argmax, maps its
label, aggregates prompt usage, and creates a new public classification ID.
Empty or exception-raising items become `Default/[1.0]`; `total_latency` is
accumulated but not emitted
([execution and shaping](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_classify.py#L129-L204)).

### `python/sglang/srt/entrypoints/openai/serving_score.py`

**Status: covered.** The adapter intentionally passes the Pydantic request
through conversion because the tokenizer manager owns scoring preparation. It
converts query/item overrides to FP32 tensors, forwards every scoring control,
converts optional CPU pooled states to JSON lists, constructs usage, and maps
`ValueError` through the shared error form
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_score.py#L1-L102)).

### `python/sglang/srt/entrypoints/openai/serving_rerank.py`

**Status: covered.** The module-level helpers resolve yes/no token IDs,
recognize text/VL rerank templates and Qwen3-VL model names, make one shared
backend decision, normalize yes/no probability, build a sandboxed Jinja
environment, render text/VL templates, and extract text-only fallback content
([helper catalog](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L24-L202)).

`OpenAIServingRerank` validates query/documents and converts only cross-encoder
work to pair-shaped `EmbeddingReqInput`; decoder requests retain their schema
object. `_handle_rerank_paths` keeps conversion and execution detection
aligned. The text path renders per-document prompts and delegates to
`score_prompts`; the VL path builds ordered media/template content and runs one
one-token generation per document
([initialization through cross-encoder](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L205-L317),
[decoder dispatch and text path](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L319-L396),
[VL path](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L398-L562)).

`_build_rerank_response` accepts scalar or legacy vector-shaped score output,
keeps original indices, conditionally omits documents, and applies descending
full sort or heap-based `top_n`
([response builder](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L564-L609)).

Because `RerankResponse.document` accepts only strings, returning an original
multimodal content-part list fails response validation. Tests cover returned
text documents and multimodal requests with document omission separately.

### `python/sglang/srt/entrypoints/openai/serving_tokenize.py`

**Status: covered.** `OpenAIServingTokenize` optionally builds a chat-serving
adapter, directly encodes one/batched prompts with caller-controlled special
tokens, reports tokenizer `model_max_length`, and maps ordinary versus
unexpected failures to 400/500. `_tokenize_chat_request` converts to and
validates `ChatCompletionRequest`, reuses multimodal/template message
processing, prefers ready IDs, and avoids adding special tokens twice
([tokenize handler](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_tokenize.py#L20-L115)).

`OpenAIServingDetokenize` decodes a flat ID list, each row of a nested list, or
empty input; enforces integer homogeneity; propagates the special-token flag;
and distinguishes message-text `decode` errors from other internal failures
([detokenize handler](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_tokenize.py#L118-L189)).

### `python/sglang/srt/managers/embed_types.py`

**Status: covered.** `PositionalEmbeds` is isolated to break the
`io_struct`/`schedule_batch` import cycle. Its post-init accepts a pre-stacked
tensor, stacks one-dimensional vectors, or concatenates already row-shaped
vectors, then requires exactly one destination position per row. An empty
Python list is intentionally invalid because `torch.cat([])` raises; a
pre-stacked zero-row tensor with no positions is valid
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/embed_types.py#L1-L58)).

### `python/sglang/srt/managers/io_struct.py`

**Status: partial.** `EmbeddingReqInput` defines text/token/media, LoRA,
routing, dimensions, embedding injection, pooled-state, trace, and MIS input.
Normalization establishes single/batch cardinality, zero decode tokens, unique
IDs, and LoRA expansion; cached `__getitem__` preserves cross-encoder pair
shape and slices parallel fields
([input and normalization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1066-L1228),
[item extraction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1230-L1297)).

`TokenizedEmbeddingReqInput` is the tokenizer-to-scheduler record, including
compact IDs/media, resolved positional embeddings, dimensions, optional pooled
state, and MIS indices. `BatchTokenizedEmbeddingReqInput` is an iterable batch
wrapper. `BatchEmbeddingOutput` carries correlated vectors, usage/cache/timing,
and optionally packed pooled-state tensors back to the tokenizer side
([tokenized records](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1300-L1348),
[output record](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1585-L1611)).

Generation and several offline control slices are covered elsewhere. Cache,
metrics, disaggregation, remaining control, and generic IPC types keep this
large file partial.

### `python/sglang/srt/managers/tokenizer_manager.py`

**Status: partial.** The embedding slice covers pair-aware tokenization,
multimodal processing, generation-mode rejection, dimension validation,
post-tokenization override resolution, and construction of
`TokenizedEmbeddingReqInput`
([preparation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L958-L1126),
[validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1211-L1293),
[tokenized conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1333-L1460)).

The result-loop slice covers embedding metadata, vector reconstruction,
stacked/non-stacked pooled-state unpacking, metrics, final state deletion, and
waiter notification
([embedding result path](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L2153-L2445)).
Previously named generation, offline controls, and cleanup slices remain valid;
parser/cache internals, multi-tokenizer/elastic modes, and remaining management
paths still prevent full coverage.

### `python/sglang/srt/managers/tokenizer_manager_score_mixin.py`

**Status: covered in the [offline-engine reference](offline-engine.md#score-preparation-and-result-contract).**
This protocol pass reuses its complete explanation of composed-prompt scoring,
text/token preparation, MIS packing, embedding override resolution, CausalLM
versus task-head request construction, result validation, normalization, and
pooled-state behavior.

### `python/sglang/srt/managers/scheduler.py`

**Status: partial.** `handle_embedding_request` converts the wire record to
`Req`, propagates dimensions/pooling/MIS state, expands multimodal IDs, checks
post-expansion and ordinary input lengths, then queues prefill-only work.
`handle_batch_embedding_request` deliberately calls the same scalar handler
for each row
([embedding admission](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L2916-L2993)).
The forward slice wraps model pooler output in `EmbeddingBatchResult` and
preserves optional pooled hidden states
([embedding forward output](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L3890-L3935)).
Queue policy, cache ownership, batching, model execution, distributed modes,
and controls retain later scheduling passes.

### `python/sglang/srt/managers/scheduler_components/batch_result_processor.py`

**Status: partial.** The covered non-generation branch waits for any async
copy, converts embeddings, moves pooled states to detached CPU tensors, stores
per-request output, uses a dummy token to enter shared completion state, and
releases or retains cache state according to completion/chunking
([embedding result branch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler_components/batch_result_processor.py#L386-L425)).
Generation/speculative/chunked-prefill logprob processing, auxiliary output,
and other batch state remain for the scheduler pass.

### `python/sglang/srt/managers/scheduler_components/output_streamer.py`

**Status: covered in the [native-protocol reference](native-generate-protocol.md#pythonsglangsrtmanagersscheduler_componentsoutput_streamerpy).**
The embedding-relevant first half selects final-only output and stacks
compatible pooled-state tensors to reduce IPC serialization calls
([embedding payload](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler_components/output_streamer.py#L245-L304)).

### `python/sglang/srt/layers/pooler.py`

**Status: covered.** `EmbeddingPoolerOutput` permits tensor/list output and
optional pre-head states. `pool_hidden_states` implements LAST, CLS, and
packed-sequence-safe MEAN pooling
([output and basic pooling](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L20-L74)).

`pool_at_delimiter_positions` translates per-request MIS indices into packed
batch indices immediately before delimiters. `score_and_pool` uses that path
only for prefill-only MIS, applies a classification head once to the flattened
selected states, then splits results; the ordinary path pools each request and
applies the head
([MIS pooling](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L77-L165)).

`Pooler` adds per-request Matryoshka truncation and optional L2 normalization.
`CrossEncodingPooler` processes each packed pair slice, applies an optional
pooler/classifier arrangement, activates the score, and squeezes the scalar
dimension
([embedding pooler](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L168-L210),
[cross-encoder pooler](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L213-L263)).

## Documentation and examples

### `docs/docs/basic_usage/openai_api_embeddings.mdx`

**Status: covered.** The tutorial demonstrates explicit decoder embedding
mode, cURL/requests/OpenAI clients, text and token-ID input, base64 output, and
cleanup. It accurately notes that native encoder architectures and
EmbeddingGemma can be detected automatically
([entire tutorial](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/openai_api_embeddings.mdx#L1-L120)).

### `docs/docs/basic_usage/native_api.mdx`

**Status: partial.** Encode, rerank, score, native reward classification, and
tokenize/detokenize examples are covered here
([encode through rerank](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/native_api.mdx#L183-L245),
[score and classify](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/native_api.mdx#L247-L339),
[token round trip](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/native_api.mdx#L376-L450)).
Generation, server/model info, cache/weight operations, and expert recording
retain their protocol/operations passes. The score section understates
classification support; the tokenization example's variable is “tokenizer
free” in name only.

### `docs/docs/supported-models/embedding_models.mdx`

**Status: covered.** The guide distinguishes auto-detected native encoders from
explicit decoder embeddings, shows Qwen3 and EmbeddingGemma launch policy,
documents text/multimodal/Matryoshka requests, and inventories supported
families with their template/backend constraints
([entire guide](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/supported-models/embedding_models.mdx#L1-L189)).

### `docs/docs/supported-models/rerank_models.mdx`

**Status: covered.** The guide separates cross-encoder, text decoder, and VL
decoder launch modes; documents request/response controls and templates; and
provides text/image/multimodal examples plus operational pitfalls
([entire guide](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/supported-models/rerank_models.mdx#L1-L340)).
Its final `return_documents=false` default conflicts with the schema's true
default, and example `model` fields are ignored because the rerank schema has
no such field.

### `docs/docs/supported-models/classify_models.mdx`

**Status: covered.** The guide describes `/v1/classify` schema/result, example
clients, model/reward families, label mapping, error intent, and claimed
gateway/Python implementation layers
([entire guide](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/supported-models/classify_models.mdx#L1-L150)).
The request model actually has a default, the Python path does not synthesize a
`Class_N` label, and no referenced `test_classify_api.py` exists in this
snapshot.

### Example files

- [`examples/runtime/engine/embedding.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/runtime/engine/embedding.py#L1-L27): constructs an explicit decoder embedding `Engine`, encodes a batch, prints vectors, and correctly protects spawn-based construction with `__main__`.
- [`examples/runtime/multimodal_embedding.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/runtime/multimodal_embedding.py#L1-L18): posts separate text-only and image-only records to one batch; it omits the `gme-qwen2-vl` chat-template flag recommended by the supported-model guide and performs no HTTP/error validation.
- [`examples/runtime/qwen3_vl_reranker.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/runtime/qwen3_vl_reranker.py#L1-L185): gives matching launch instructions, text/image/multimodal-query payloads, output handling, a health preflight, and connection guidance. It checks selected response error shapes but does not call `raise_for_status`.
- [`examples/chat_template/qwen3_reranker.jinja`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/chat_template/qwen3_reranker.jinja#L1-L7): formats two message contents and an optional instruction into a yes/no assistant prefill.
- [`examples/chat_template/qwen3_vl_reranker.jinja`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/examples/chat_template/qwen3_vl_reranker.jinja#L1-L32): iterates query/document content, emits model vision/video placeholders in traversal order, and ends at the same yes/no assistant prefill.

All five example/template files are **covered**. They demonstrate adapter
shape, not numerical quality, throughput, or production retry policy.

## Test files

### `test/registered/unit/configs/test_embedding_model_spec.py`

**Status: covered.** Six CPU tests prove EmbeddingGemma's full-encoder policy,
native encoder auto-enable behavior, registry-derived support rows, live plan
readback, conservative explicit decoder policy, and no auto-capability for an
unknown generation architecture
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/configs/test_embedding_model_spec.py#L1-L122)).

### `test/registered/unit/entrypoints/openai/test_serving_embedding.py`

**Status: covered.** The CPU/mock suite isolates adapter conversion for single,
batch, IDs, image/video and template precedence; checks image-only fallback and
Jinja error detail; and byte-checks little-endian FP32 base64 plus format
validation
([fixture and conversion tests](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/test_serving_embedding.py#L1-L305),
[error/encoding tests](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/test_serving_embedding.py#L306-L369)).

### `test/registered/prefill_only/test_openai_embedding.py`

**Status: covered.** The server/OpenAI-client suite covers single and batched
text, flat and nested token IDs, blank-input 400, non-Matryoshka dimension
rejection, allowed/omitted Matryoshka dimensions, and invalid values
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_openai_embedding.py#L1-L205)).
It requires model launch and accelerator-capable CI despite also registering a
CPU suite.

### `test/registered/prefill_only/test_serving_rerank.py`

**Status: covered.** Mocked unit cases prove cross-encoder pairing, decoder
template routing, scalar/vector score extraction, template defaults, text
`score_prompts` integration, VL logprob extraction, sorting, original indices,
document omission, and `top_n`
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_serving_rerank.py#L1-L310)).

### `test/registered/prefill_only/test_score_api.py`

**Status: covered.** Two live-server classes cover ordinary CausalLM response
shape/default normalization/schema rejection and FlashInfer MIS item
cardinality, empty input, varied counts, normalization, and determinism
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_score_api.py#L1-L234)).
The non-softmax comments say raw logprobs, while the implementation returns
their exponentiated probabilities; the assertion only checks they do not sum
to one.

### `test/registered/prefill_only/test_score_engine.py`

**Status: covered.** CausalLM tests compare against Hugging Face selected-token
softmax, inspect the zero-decode internal request, and cover batch sizes, empty
items, label widths, Unicode, determinism, and bad inputs.
Sequence-classification tests cover normalized/raw head vectors, token/text parity,
ignored label IDs, MIS cardinality, and a 12-label shape stress case
([CausalLM cases](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_score_engine.py#L40-L250),
[classification cases](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_score_engine.py#L258-L487)).
The CausalLM non-softmax docstring says raw logits, but the test asserts only
numeric shape and does not establish that description.

### `test/registered/prefill_only/test_pooled_hidden_states.py`

**Status: covered.** Twenty GPU/model-dependent tests exercise ordinary and
MIS sequence-classification scoring with and without pooled hidden states;
vector count and hidden-width consistency; CPU ownership; determinism;
tokenized input; score invariance; and the CausalLM rejection boundary. The
three HTTP cases among them verify nested-float-list serialization, null
omission, and item cardinality
([Engine and MIS cases](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_pooled_hidden_states.py#L1-L291),
[CausalLM and HTTP cases](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_pooled_hidden_states.py#L294-L433)).
The classification head is intentionally random, so these tests prove shape
and plumbing rather than semantic score quality.

### `test/registered/unit/layers/test_pooler_score_and_pool.py`

**Status: covered.** CPU tensor tests cover ordinary task-head output, MIS
list/split shapes, exact positions before delimiters, manual score parity,
packed MEAN boundaries, and empty delimiter tensors
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/layers/test_pooler_score_and_pool.py#L1-L191)).

### `test/registered/unit/managers/test_embed_overrides.py`

**Status: covered.** This focused CPU suite covers `PositionalEmbeds` shape and
count normalization, JSON-to-FP32 conversion, tokenizer-manager placeholder
matching, generation/embedding batch slicing, score offset resolution,
ordinary/MIS combined inputs, and validation for labels/items/override pairing
([types and direct resolution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/managers/test_embed_overrides.py#L1-L199),
[score preparation and validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/managers/test_embed_overrides.py#L200-L602)).

### `test/registered/unit/managers/test_io_struct.py`

**Status: partial.** The embedding slice checks that ordinary and
cross-encoder batch splitting preserve priority, that both adapter path and
resolved LoRA identity survive item extraction, and that a short LoRA list is
rejected
([embedding item tests](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/managers/test_io_struct.py#L1115-L1166)).
Generation normalization and message round trips were covered earlier; generic
msgpack/tensor-extension, CUDA-device, and remaining multimodal transport cases
keep this mixed test file partial.

### `test/registered/core/test_srt_endpoint.py` token slice

**Status: partial.** `TestTokenizeDetokenize` covers prompt/batch/special-token
encoding, invalid prompt type, chat/tool framing including `tool_choice=none`,
multilingual round trips, empty IDs, invalid string IDs, and the current 500
for a negative token ID
([slice](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/core/test_srt_endpoint.py#L742-L891)).
Native generation/logprob slices were covered earlier. Server-info/startup and
the complete embedded Rust endpoint matrix still keep the mixed suite partial.

### `test/registered/openai_server/basic/test_openai_server.py` rerank and score slices

**Status: partial.** Two live cross-encoder cases verify single/batch rerank
result shape and original indices. Three live CausalLM score cases verify
text/token input, selected-label normalization, prompt-only usage, and a 400
for an out-of-vocabulary label token
([rerank slice](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/basic/test_openai_server.py#L951-L1019),
[score slice](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/basic/test_openai_server.py#L1110-L1294)).
Completion/chat, Responses API, model catalog, grammar, custom-processor, and
remaining mixed OpenAI cases keep this 1,298-line suite partial.

### `test/registered/xpu/test_xpu_embedding.py`

**Status: covered.** Two live Intel-XPU tests launch an explicit embedding
model and use the OpenAI client to verify nonempty single and two-item batch
vectors. They prove XPU route availability and cardinality, not dimensions,
base64, numerical parity, or quality
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/xpu/test_xpu_embedding.py#L1-L70)).

### `test/registered/npu/interface/test_npu_api_encode.py`

**Status: covered.** Four Ascend integration cases exercise native `/encode`
with text, token IDs, remote-image multimodal input, and a batch of explicit
request IDs, asserting HTTP success and ID correlation. They do not inspect
the embedding vector. The docstring names a GME-Qwen2-VL checkpoint while the
fixture actually imports the Qwen3-VL-4B path
([entire suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/npu/interface/test_npu_api_encode.py#L1-L134)).

No focused test names `OpenAIServingClassify` or `/v1/classify` in this
snapshot. Pooler/score tests exercise its underlying head-vector shape but not
label mapping, per-item `Default` fallback, output identity, or HTTP contract.

## Reference study check

For each public route, identify:

1. the Pydantic or native request type;
2. whether it constructs `GenerateReqInput`, `EmbeddingReqInput`, or neither;
3. how single versus batch cardinality is represented;
4. where token/media/template preparation happens;
5. whether the returned vector means an embedding, logits, probability, or
   scalar score; and
6. the exact boundary that converts internal errors or tensors into HTTP JSON.
