# Ordered Study Path

This guide follows the order in which SGLang turns a user request into model
work, then works downward into the machinery that makes that path fast. Read
the conceptual guide for a phase before using its file-by-file reference notes.

The source snapshot is fixed at
[`f464e77d17a3908ad0ea32547b1e8b039bcbd354`](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354).
Coverage labels describe this snapshot only.

## Phase 0: orient yourself

1. Read the [architecture overview](01-architecture-overview.md).
2. Keep the [dependency map](90-dependency-map.md) open while reading.
3. Use the [glossary](99-glossary.md) when an acronym first appears.
4. Check the [coverage inventory](coverage/README.md) before assuming a file
   has already received a full pass.

The orientation phase is available now. It distinguishes the Python runtime,
the diffusion runtime, native extensions, routers, tests, and operational
material so similarly named packages are not conflated.

## Phase 1: learn the public surfaces

Study the installed `sglang` package, the frontend language, the offline
`Engine`, and the command-line entry points. The first reference note,
[Serving entry points](reference/entrypoints.md), covers `sglang serve` and its
backend extension contract. The [Offline Engine API](03-offline-engine.md) and
its [file reference](reference/offline-engine.md) now cover the in-process
constructor, sync/async inference surfaces, request handoff, sessions, scoring,
control methods, weight updates, and shutdown. [Frontend Language Execution](04-frontend-language.md)
and its [file reference](reference/frontend-language.md) now trace decorated
functions through sampling IR, interpreter state, single/batch/stream modes,
fork/join, choice scoring, tracing and prefix caching, and the first SRT HTTP
handoff. Provider clients, the complete chat-template catalog, and the
diffusion `generate` command remain to be written.

Questions to answer before moving on:

- Which imports perform process-wide setup, and which public objects are lazy?
- When does `sglang serve` choose the LLM runtime, diffusion runtime, or an
  installed third-party backend?
- How does the offline `Engine` differ from the HTTP server without becoming a
  separate inference core?
- Which thread runs user Python, which thread evaluates expressions, and what
  event makes a generated variable safe to read?
- How do `RuntimeEndpoint`, local `Runtime`, and offline `Engine` differ in
  transport, process ownership, and return type?

## Phase 2: configuration and startup

Study `ServerArgs`, argument groups, config-file merging, runtime-context
publication, platform selection, process/rank construction, ports, readiness,
warmup, and shutdown. Treat resolved configuration as an input to later phases;
otherwise backend-selection code appears to make decisions from raw CLI values
that have already been transformed.

This phase is now available in [Configuration and startup](02-configuration-and-startup.md),
with a companion [file and symbol reference](reference/configuration-startup.md).
Before moving on, be able to distinguish raw, resolved, published, overridden,
configured-parallel, and live-parallel values, and distinguish scheduler/model
readiness from public HTTP readiness after warmup.

## Phase 3: protocols and request preparation

Follow native `/generate`, OpenAI, Anthropic, Ollama, gRPC, and embedding or
scoring requests into their shared request structures. Then cover chat
templates, tokenization, multimodal preprocessing, grammar/tool parsers,
sessions, request state, cancellation, and streaming response contracts.

## Phase 4: scheduling and cache ownership

Study the scheduler's queues and batch types before its individual policies.
Then cover continuous batching, prefill versus decode, chunked prefill,
RadixAttention, KV allocation, cache eviction, host/offloaded storage, and
session/prefix reuse. At this phase, trace both a cache hit and a cache miss.

## Phase 5: model execution

Move from `ModelRunner` and model loading into model registries, layers,
attention backends, sampling, logits processing, quantization, CUDA graphs,
Torch compilation, LoRA, and the JIT/AOT kernel layers. Model-specific files
should be grouped by reusable architecture family rather than read as thousands
of unrelated implementations.

## Phase 6: distributed and advanced execution

Cover tensor, pipeline, data, context, and expert parallelism; overlap modes;
prefill/decode and encoder disaggregation; weight transfer; elastic expert
parallelism; speculative decoding; and platform-specific backends. Each topic
needs a process/rank map and an explicit statement of which component owns each
piece of mutable state.

## Phase 7: multimodal and diffusion systems

Study SRT multimodal input processing separately from
`sglang.multimodal_gen`, which is the image/video/diffusion runtime. Then cover
its managers, pipelines, models, distributed execution, caches, post-training,
entry points, apps, and tests.

## Phase 8: routing and native services

Study the Rust extension workspace, the native Rust HTTP/gRPC surfaces, the
`sgl-model-gateway`, and the experimental KV-aware `sgl-router`. Compare their
responsibilities with SRT instead of treating every HTTP-facing component as a
replacement inference engine.

## Phase 9: validation and operations

Finish with tests, benchmarks, examples, documentation, build and packaging,
containers, deployment, CI, release automation, observability, incident
diagnostics, and security boundaries. The final audit must reconcile every row
in the coverage inventory, validate navigation and source links, and search for
important symbols mentioned nowhere else.

## How to use a file reference

A file is `covered` only when its meaningful contents have been explained at
the appropriate level. `partial` means named symbols or one flow through a
large file are explained, but other responsibilities remain. `inventory-only`
is reserved for a file that does not benefit from line-by-line notes and must
include a reason. See the [ledger policy](coverage/README.md) for the exact
definitions.
