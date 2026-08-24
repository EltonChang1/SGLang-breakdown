# Reference Notes

Reference notes explain files and symbols after their conceptual subsystem has
been introduced. A reference note is not automatically proof that every linked
file is complete; consult the [coverage inventory](../coverage/README.md) for
its exact status.

- [Serving entry points](entrypoints.md): package import behavior, packaging
  entry points, `sglang serve`, backend discovery, startup dispatch, and the
  default request path into the runtime managers.
- [Configuration and startup](configuration-startup.md): CLI/YAML schema,
  one-time resolution and declarations, runtime publication, platform files,
  rank/port construction, readiness, warmup, and shutdown symbols.
- [Offline Engine](offline-engine.md): base contract, constructor and event-loop
  boundary, generation/embedding/scoring adapters, sessions, runtime controls,
  weight updates, LoRA, request schemas, and tokenizer-side fan-out.
- [Frontend language](frontend-language.md): public factories, sampling IR,
  interpreter state and concurrency, fork/join, choice policies, tracing and
  prefix caching, the backend contract, and the SRT HTTP runtime endpoint.
- [Provider clients and templates](provider-clients-and-templates.md): OpenAI,
  Anthropic, LiteLLM, Vertex AI, and Crusoe adapters; all frontend template
  records and matchers; and the focused examples and manual tests.
- [Diffusion generate CLI](diffusion-generate-cli.md): installed and secondary
  dispatchers, server/sampling precedence, `DiffGenerator`, worker topology,
  scheduler clients, output materialization/persistence, cleanup, and focused
  unit/GPU tests.
- [Native `/generate`](native-generate-protocol.md): request normalization,
  sampling, tokenization and media preparation, scheduler admission messages,
  incremental detokenization, output correlation, streaming, and abort paths.
- [OpenAI completions](openai-completions.md): completion/chat schemas, shared
  adapter lifecycle, message rendering, native handoff, reasoning/tools, usage,
  logprobs, streaming, extensions, documentation, examples, and focused tests.
- [Embedding and scoring adapters](openai-embeddings-and-scoring.md): embedding
  capability discovery; embedding/classification/score/rerank schemas and
  adapters; pooling and MIS; tokenization; documentation, examples, and tests.
