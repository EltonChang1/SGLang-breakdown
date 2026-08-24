# Embeddings, Classification, Scoring, Reranking, and Tokenization

This Phase 3 subunit covers the OpenAI-compatible non-generation adapters that
prepare or inspect model inputs: `/v1/embeddings`, `/v1/classify`, `/v1/score`,
`/v1/rerank`, `/v1/tokenize`, and `/v1/detokenize`. It also follows the native
`/encode` and `/classify` aliases far enough to show where they converge.

The central naming trap is that SGLang's internal **embedding path** carries
more than semantic vectors. The same `EmbeddingReqInput` and
`BatchEmbeddingOutput` transport can carry:

- a normalized dense embedding from an embedding model;
- class logits from a sequence-classification head;
- a scalar reward or cross-encoder relevance score; or
- optional pooled hidden states captured before a classification head.

The public adapter decides how to interpret that vector. Do not infer its
meaning from the internal field name `embedding` alone
([pooler output contract](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L26-L44),
[classification result interpretation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L192-L264)).

## Route and execution map

All OpenAI-compatible routes are thin FastAPI functions over handler objects
created during application lifespan. `/tokenize` and `/detokenize` are hidden
aliases for their `/v1/...` forms. `/encode` and `/classify` accept the native
`EmbeddingReqInput` directly rather than an OpenAI schema
([handler construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L302-L328),
[native routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L943-L964),
[OpenAI routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1733-L1790),
[score and rerank routes](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L1901-L1951)).

| Route | Public input | Internal work | Public result |
| --- | --- | --- | --- |
| `/v1/embeddings` | text, token IDs, or multimodal records | `EmbeddingReqInput` and a pooling forward pass | float-list or base64 dense vectors |
| `/v1/classify` | text or token IDs | `EmbeddingReqInput` and a classification head | label plus softmax probabilities |
| `/v1/score` | query and items | zero-token generation **or** `EmbeddingReqInput` | one score vector per item |
| `/v1/rerank` | query and documents | cross-encoder pooling, text-decoder scoring, or VL generation | descending relevance records |
| `/v1/tokenize` | prompt or chat messages | tokenizer/template work in the API process | token IDs, counts, model limit |
| `/v1/detokenize` | one or many token-ID lists | tokenizer decode in the API process | one string or string list |

Only the first four can enter accelerator scheduling. Tokenize and detokenize
return from the API/tokenizer process and never construct a scheduler request.

## Model capability before request handling

`ModelConfig` resolves a declarative `EmbeddingModelSpec` from the checkpoint's
architectures, explicit `--is-embedding` intent, and the special
EmbeddingGemma predicate. The spec separates task, execution style, attention,
pooling, normalization, multimodality, auto-enable policy, and safe cache/graph
adjustments. Known native encoder or pooling-only architectures can enable
embedding mode automatically; an ambiguous decoder checkpoint still needs
explicit user intent
([spec record and registries](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/embedding_model_spec.py#L13-L150),
[resolution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/embedding_model_spec.py#L268-L344),
[ModelConfig integration](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/model_config.py#L314-L340)).

This distinction is operational, not documentation metadata. Server-argument
resolution auto-enables the declared native embedding architectures. For
EmbeddingGemma it additionally disables radix reuse and split prefill, batches
tokenization atomically, disables decode graphs, selects full-prefill breakable
graphs on CUDA, and conditionally skips the KV pool on Hopper/Blackwell with
FA3/FA4. It deliberately does not apply those encoder assumptions to an
explicit decoder embedding
([capability adjustments](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L4043-L4159)).
`/model_info` exposes a resolved plan combining the static spec with live
Matryoshka, cache, and prefill-graph settings, so clients can inspect the
effective server rather than guess from a model name
([resolved plan](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/configs/embedding_model_spec.py#L223-L265),
[`/model_info`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L739-L774)).

## Shared adapter lifecycle

The handlers reuse `OpenAIServingBase`. Its lifecycle records receipt time,
runs endpoint validation, optionally logs the raw request, converts it to an
internal request, stamps timing on generation/embedding transports, and calls
the non-streaming implementation. `ValueError` becomes HTTP 400; unexpected
exceptions become HTTP 500. None of the adapters in this guide supports
streaming
([shared lifecycle](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_base.py#L73-L133),
[default streaming rejection](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_base.py#L160-L190)).

Unlike completion/chat serving, the base does not validate that a request's
`model` names the live checkpoint. Most model fields here are compatibility or
echo fields rather than dispatch keys. The embedding adapter is the exception
only in one narrow sense: it parses `base-model:adapter` to select a LoRA, with
that suffix taking precedence over explicit `lora_path`
([LoRA resolution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_base.py#L40-L71),
[embedding conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L150-L182)).

## `/v1/embeddings`: prepare, pool, and serialize

### Schema and validation

`EmbeddingRequest.input` accepts a string, string batch, flat token-ID list,
nested token-ID batch, or a batch of `{text, image, video}` records. It also
accepts output dimensions, request IDs, priority, LoRA selection, and
token-position embedding overrides. `user` is accepted but not consumed
([schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1274-L1304)).

Adapter validation rejects an empty top-level input, blank strings, blank
members of a string batch, negative token IDs in a **flat** ID input,
heterogeneous string or integer lists, and any `encoding_format` other than
`float` or `base64`. Pydantic handles shapes outside the declared union before
the adapter runs. A nested token-ID batch takes a different validation branch,
so its lower-bound gap is called out below
([validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L44-L83)).

### Text, tokens, and multimodal template precedence

Ordinary strings become `text`; token IDs become `input_ids`. Multimodal
records are split into aligned text, image, and video arrays, then prompt text
is selected in this order:

1. an SGLang-registered conversation template;
2. the tokenizer's Hugging Face Jinja chat template;
3. raw text, using the literal `"padding"` for a record without text.

The media payloads stay separate from rendered prompt strings. The Jinja path
normalizes OpenAI content-part names, renders one user message with a
generation prompt, and converts Jinja/type/key/attribute failures to
`ValueError` so malformed templates produce HTTP 400. An image-only Jinja
input does **not** inject the fallback `"padding"`; that literal belongs only
to the no-template branch
([multimodal conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L85-L149),
[Jinja rendering](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L186-L246)).

Embedding overrides must supply both the placeholder token ID and replacement
vectors. JSON floats become FP32 tensors, but positions are deliberately left
unresolved until text/media tokenization has produced the final input IDs. The
adapter also propagates priority, Matryoshka dimensions, LoRA, request ID, and
the `x-smg-routing-key` header
([override pairing and conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L150-L184),
[position resolution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1416-L1442)).

### Internal cardinality and validation

`EmbeddingReqInput.normalize_batch_and_arguments` makes a list of texts or a
nested ID list into a batch; a single string or flat ID list remains one
request. It generates unique IDs, sets `max_new_tokens=0`, expands sampling
and LoRA settings, and caches stable per-item objects. Cross-encoder pairs are
preserved as pairs during item extraction instead of being mistaken for an
ordinary text batch
([normalization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1066-L1228),
[item extraction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/io_struct.py#L1230-L1297)).

The tokenizer manager reuses the native request lifecycle: normalize, create
correlation state, take the model-update reader lock, tokenize or process
media, and dispatch a `TokenizedEmbeddingReqInput`. Cross-encoder text uses a
pair-aware tokenizer path. Multimodal processors may replace input IDs and add
token-type/media state before length validation
([request lifecycle](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L767-L833),
[token and media preparation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L958-L1126)).

Two semantic gates occur here:

- `EmbeddingReqInput` is rejected while the manager is in generation mode;
- `dimensions` is accepted only for a Matryoshka model, must be positive, must
  belong to a declared allowlist when present, and cannot exceed hidden size.

These are runtime capability checks, not merely schema validation
([embedding and dimension validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1211-L1220),
[Matryoshka rules](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1267-L1293)).

### Pooling and response shape

The scheduler converts the tokenized record into mutable `Req`, expands
multimodal IDs, repeats length validation after expansion, and queues a
prefill-only request. A model returns hidden states or its own pooler result;
the common `Pooler` selects LAST, CLS, or MEAN, applies per-request dimension
truncation, then optionally L2-normalizes. Mixed dimensions can therefore
produce a list of differently shaped tensors instead of one rectangular batch
([scheduler admission](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L2916-L2993),
[pooling](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L47-L74),
[truncation and normalization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L168-L210)).

Embedding work finishes after prefill: the result processor stores the vector,
uses a dummy output token only to drive the shared request finish state, and
releases or caches the request. The output streamer sends a final-only
`BatchEmbeddingOutput`; the tokenizer manager correlates it back into
`{"embedding": ..., "meta_info": ...}`. There is no detokenization step even
though the output channel retains its historical detokenizer-facing name
([result completion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler_components/batch_result_processor.py#L386-L425),
[embedding payload](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler_components/output_streamer.py#L245-L304),
[tokenizer-side reconstruction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L2388-L2403)).

The adapter preserves input order, sums prompt tokens, and reports the live
manager model path. Float output is ordinary JSON. Base64 output is explicitly
packed as contiguous little-endian FP32 before encoding, so it does not depend
on host endianness or Python float representation
([response construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L248-L308)).

## `/v1/classify`: logits become labels

Classification accepts one string, a string batch, or a flat token-ID list.
Like embeddings it rejects blank or heterogeneous inputs. It adapts only text
or IDs plus `rid` and `priority`; the accepted `model` and `user` fields do not
select a backend, a LoRA, or an output identity
([schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1313-L1341),
[conversion and validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_classify.py#L50-L109)).

Handler construction requires an `id2label` mapping. It reads the model config
mapping or synthesizes `LABEL_0`, `LABEL_1`, and so on from `num_labels`; if
neither is available, application lifespan fails while constructing the
handler. For each returned head vector, it computes softmax probabilities,
chooses the argmax of the original logits, and looks up the label. Empty or
malformed vectors silently degrade that item to `label="Default"` and
`probs=[1.0]`. Prompt usage is aggregated; accumulated latency is currently
unused
([mapping initialization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_classify.py#L28-L45),
[mapping fallback](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_classify.py#L111-L127),
[response shaping](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_classify.py#L129-L204)).

The response `model` is the served-model name when configured, otherwise the
manager's model path. It is not the request body's `model` value.

## `/v1/score`: one API, two model semantics

`ScoringRequest` accepts text or token IDs for a query, one or many items,
optional label token IDs, selected-label normalization, query/item order,
embedding overrides, and optional pre-head pooled-state return
([schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1351-L1384)).
The HTTP adapter converts replacement vectors to FP32 tensors, delegates to
`TokenizerManager.score_request`, converts pooled-state tensors back to JSON
lists, and reports usage. Only `ValueError` is handled locally; the base maps
other failures to HTTP 500
([HTTP adapter](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_score.py#L19-L102)).

The score mixin chooses its internal request from the live model:

- A **CausalLM** requires `label_token_ids`. It builds a non-streaming
  `GenerateReqInput` with `max_new_tokens=0`, logprob collection enabled, and
  selected token IDs. Ordinary mode reads the would-be next-token
  probabilities; it never performs decode.
- A **sequence-classification or reward model** builds `EmbeddingReqInput` and
  treats the task-head vector as the score vector. `label_token_ids`, if
  supplied, do not change that vector's width.

Both paths concatenate `query+item` by default or `item+query` when
`item_first=True`. Text and pre-tokenized pairs are supported. Embedding
overrides require an exact placeholder count and forbid `item_first`, because
the implemented position offsets assume query-first order
([input and model validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L443-L510),
[request construction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L511-L624)).

### Selected-label probability is not one operation

For CausalLMs, `apply_softmax=False` exponentiates each selected logprob. The
numbers are token probabilities under the model's full vocabulary and usually
do not sum to one across the selected labels. `apply_softmax=True` instead
renormalizes only the selected logprobs. For classification models, `False`
returns head logits and `True` softmaxes the whole head vector
([score conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L642-L671),
[ordinary result paths](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L192-L264)).

### Multi-item scoring

With `--enable-mis`, one request packs
`query<D>item1<D>item2<D>...<D>` and carries the delimiter indices explicitly.
The delimiter token exists for backend compatibility; correctness does not
depend on finding that token by scanning. CausalLM scoring reads selected
logprobs at delimiter positions. Classification scoring pools the hidden state
immediately before each delimiter and runs the task head only on those states.
The first result represents the query/item boundary and is deliberately
dropped; exactly one subsequent row must exist per item
([packed sequence](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L68-L108),
[result validation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L110-L190),
[pool-before-delimiter](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/layers/pooler.py#L77-L165)).

Pooled hidden states are available only for supported non-generation task-head
models. CausalLMs and `CrossEncodingPooler` reject the option. The in-process
API keeps tensors on CPU; the HTTP adapter is where they become nested lists
([pooled-state gates](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L583-L599),
[`ScoreResult`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager_score_mixin.py#L16-L25)).

## `/v1/rerank`: three backends behind one schema

The request contains a query, document list, optional instruction, positive
`top_n`, and `return_documents` (default `True`). Query/documents can be text or
OpenAI text/image/video content parts. There is no declared `model` field;
extra input such as the `model` shown in upstream examples is ignored by
Pydantic's default extra-field policy
([rerank content types](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L637-L664),
[request schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1387-L1426)).

Backend detection is shared by conversion and execution. A VL template, a
Qwen3-VL-looking model path, or a multimodal request paired with a text
yes/no template selects `vl_decoder`; a text yes/no template selects
`text_decoder`; everything else selects `cross_encoder`
([backend detection](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L52-L112)).

### Cross-encoder path

Each document becomes a `[query, document]` pair inside an
`EmbeddingReqInput(is_cross_encoder_request=True)`. If multimodal content
reaches this fallback, images and videos are discarded and only text parts are
joined; this is degradation, not multimodal cross-encoding. The model's scalar
score may arrive directly or as the first element of `embedding`; malformed or
empty vectors fail response construction
([pair adaptation](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L245-L279),
[cross-encoder execution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L281-L317),
[scalar extraction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L564-L600)).

### Text decoder path

Template detection looks for a yes/no-only instruction. The handler renders
one prompt per document in an immutable Jinja sandbox, passes the optional
instruction only when non-empty so the template's `default(...)` works, and
calls `score_prompts` for dynamically tokenized `yes` and `no` labels. If the
tokenizer cannot produce IDs, it falls back to Qwen3-specific IDs 9693/2152.
The relevance score is `p_yes / (p_yes + p_no)`, or zero when both are absent.
This path requires generation mode
([label IDs and sandbox](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L24-L49),
[text rendering](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L114-L165),
[text scoring](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L354-L396)).

### VL decoder path

The VL handler converts query and document parts to template records while
collecting media URLs in the same traversal order. It then renders the
query/document template and performs a **separate**, one-token,
temperature-zero generation request per document with the top 50 logprobs. It
finds yes/no
within the first token's candidate list and applies the same ratio. The loop is
serial, so document count multiplies tokenizer, media, and generation latency;
the handler does not batch these requests
([VL content conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L398-L533),
[generation and extraction](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L424-L462),
[logprob ratio](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L535-L562)).

All three paths retain original document indices, optionally omit document
content, and sort descending. `top_n` uses a bounded heap rather than sorting
the whole candidate set
([response ordering](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L564-L609)).

## Tokenize and detokenize without scheduling

`TokenizeRequest` requires exactly one of `prompt` or `messages`. It allows
extra fields because chat-specific options are revalidated through
`ChatCompletionRequest`. A string prompt returns one ID list and count; a
string batch returns parallel lists. `add_special_tokens` affects only prompt
encoding
([tokenize schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1444-L1478),
[prompt tokenization](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_tokenize.py#L20-L85)).

Chat tokenization deliberately reuses chat serving validation and
`_process_messages`, so tools, `tool_choice`, reasoning effort, continuation,
templates, and multimodal prompt rendering agree with `/v1/chat/completions`.
Already-rendered prompt IDs are returned directly; rendered text is encoded
with `add_special_tokens=False` to avoid double framing. This endpoint prepares
the chat prompt but does not run sampling, tool parsing, or model inference
([chat reuse](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_tokenize.py#L87-L115)).

`DetokenizeRequest` accepts one ID list or a list of ID lists and defaults to
skipping special tokens. Empty input returns `""`; a nested empty batch returns
an empty string list through the batch branch only when it has an outer item.
The handler checks integer homogeneity but not token range. A tokenizer error
whose message contains `decode` becomes HTTP 400; other decode failures become
HTTP 500. The focused test records negative IDs as the latter today
([detokenize schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1489-L1503),
[decode behavior](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_tokenize.py#L118-L189),
[negative-ID assertion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/core/test_srt_endpoint.py#L883-L891)).

## Failure modes and documentation drift

- Multimodal embedding alignment depends on parallel text/image/video arrays;
  template output changes prompt IDs but media is still processed separately.
- A multimodal rerank request can lose all media if backend detection falls
  through to the cross-encoder branch.
- Text/VL decoder rerank classification relies on template or model-name
  heuristics. A wrong template can select the wrong runtime mode; missing
  yes/no labels can silently produce score zero.
- Classification catches per-item output/mapping failures and emits `Default`
  instead of failing the request, which can hide a bad `id2label` mapping.
- Embedding validation rejects negative IDs only for a flat token list. A
  nested token batch bypasses that check, and the tokenizer manager's shared
  vocabulary check tests only the upper bound; negative batch IDs can
  therefore fail later than the equivalent single input
  ([adapter check](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_embedding.py#L44-L83),
  [manager check](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1315-L1331)).
- Embedding-override contracts do not line up for an HTTP single input. The
  schema requires an outer per-input list; conversion preserves it, but the
  unsplit single request later expects the inner tensor list. Unit tests cover
  both helpers separately but not this end-to-end shape
  ([schema shape](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1296-L1304),
  [conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/utils.py#L205-L240),
  [single-request resolution](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1416-L1442)).
- A rerank request may accept multimodal documents with
  `return_documents=true`, but `RerankResponse.document` is typed as a string
  while the response builder passes the original content-part list. Pydantic
  response construction then rejects that list; focused rerank tests cover
  returned text documents and omitted multimodal documents, not this
  combination
  ([response schema](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1429-L1441),
  [response builder](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/serving_rerank.py#L564-L600)).
- The classification guide claims a `Class_N` last fallback; this snapshot has
  only synthesized `LABEL_N` and per-item `Default` behavior
  ([upstream claim](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/supported-models/classify_models.mdx#L99-L104)).
- The rerank guide's multimodal parameter section says
  `return_documents` defaults to false, but the Pydantic schema defaults it to
  true
  ([guide text](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/supported-models/rerank_models.mdx#L321-L327),
  [schema default](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/openai/protocol.py#L1407-L1410)).
- Score test/doc comments sometimes call the non-softmax CausalLM values “raw
  log-probs” or “raw logits”; implementation exponentiates them. The behavioral
  test only proves that the selected probabilities do not sum to one
  ([HTTP test](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_score_api.py#L83-L99)).
- The native API guide describes `/v1/score` as decoder-only, but the same
  endpoint supports sequence-classification models; its “probability lists”
  wording is true only when normalization is requested or for CausalLM token
  probabilities
  ([upstream description](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/native_api.mdx#L247-L259)).
- The tokenization tutorial names its ordinary server variable
  `tokenizer_free_server_process`; it does not actually launch with
  `--skip-tokenizer-init`, and these endpoints require a tokenizer
  ([launch example](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/docs/docs/basic_usage/native_api.mdx#L376-L386)).

## What the focused tests prove

- Embedding unit tests cover text/token/multimodal conversion, explicit and HF
  template precedence, image/video-only behavior, template error mapping,
  little-endian FP32 base64, and encoding-format rejection
  ([unit suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/entrypoints/openai/test_serving_embedding.py#L102-L365)).
- Embedding integration tests cover one/batch text, flat/nested IDs, empty
  input, Matryoshka allow/deny behavior, and output dimensions
  ([integration suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_openai_embedding.py#L25-L201)).
- Rerank unit tests cover cross-encoder pair formation, text/VL backend
  selection, yes/no ratios, scalar extraction, original indices, document
  omission, and `top_n`
  ([rerank suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_serving_rerank.py#L49-L306)).
- Score HTTP tests cover response schema, normalization, malformed input, MIS
  cardinality, empty items, and determinism. Engine tests additionally compare
  CausalLM scoring with Hugging Face, prove zero decode tokens, exercise token
  inputs and errors, and cover ordinary/MIS classification heads
  ([HTTP suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_score_api.py#L40-L230),
  [engine suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_score_engine.py#L40-L487)).
- Pooled-hidden-state integration tests cover ordinary and MIS classification
  scoring, item cardinality and shape, CPU ownership, determinism, score
  invariance, CausalLM rejection, and HTTP tensor-to-list serialization
  ([suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/prefill_only/test_pooled_hidden_states.py#L1-L433)).
- CPU pooler tests prove packed-sequence boundaries, pre-delimiter selection,
  per-request MIS splitting, and empty-delimiter shapes. Override tests prove
  FP32 conversion, exact placeholder matching, absolute offsets, batch
  slicing, and the score validation gates
  ([pooler tests](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/layers/test_pooler_score_and_pool.py#L42-L187),
  [override tests](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/unit/managers/test_embed_overrides.py#L47-L598)).
- Tokenize/detokenize integration tests cover text/batch/special-token cases,
  chat and tool framing, round trips, invalid types, and the current
  negative-token error status. No focused `/v1/classify` suite exists in this
  snapshot
  ([endpoint suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/core/test_srt_endpoint.py#L742-L891)).

The broad OpenAI server suite adds live cross-encoder rerank and CausalLM score
shape, usage, token-input, and invalid-label checks. XPU and NPU files prove
backend-specific single/batch embedding and native text/token/multimodal
`/encode` transport, but not numerical quality
([OpenAI slices](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/basic/test_openai_server.py#L951-L1019),
[score slice](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/openai_server/basic/test_openai_server.py#L1110-L1294),
[XPU suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/xpu/test_xpu_embedding.py#L1-L70),
[NPU suite](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/test/registered/npu/interface/test_npu_api_encode.py#L1-L134)).

GPU integration suites require model downloads and accelerator resources. CPU
unit suites still provide useful guarantees at schema, conversion, and pooling
boundaries; they do not prove numerical quality for a production checkpoint.

## Study checks

1. Explain why the tokenizer-side result field `embedding` may mean a dense
   vector, logits, or a scalar score, and name the adapter that assigns its
   meaning.
2. Trace a multimodal embedding record through template rendering, separate
   media transport, tokenizer-manager processing, scheduler pooling, and
   base64 response serialization.
3. Compare CausalLM scoring with sequence-classification scoring when
   `apply_softmax` is both false and true.
4. Explain why MIS records one more delimiter result than there are items.
5. Given a rerank request, identify the three facts that can select the VL
   decoder path and describe what happens if all media reaches cross-encoder
   fallback instead.
6. Explain why chat tokenization reuses `OpenAIServingChat` but does not submit
   a `GenerateReqInput`.
7. Identify one failure that becomes HTTP 400, one that becomes HTTP 500, and
   one classification failure that silently becomes a `Default` result.
