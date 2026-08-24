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
