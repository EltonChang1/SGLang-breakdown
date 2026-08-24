# Dependency Map

This is the initial package-level map for the pinned snapshot. Arrows mean
"calls, embeds, or builds on" rather than a promise that every import points in
only one direction. Symbol-level dependency maps will be added with each
subsystem guide.

## Serving layers

| Layer | Depends on | Supplies |
| --- | --- | --- |
| Frontend language and clients (`sglang.lang`) | Template/program state, HTTP-provider clients | User-facing generation primitives and backend requests |
| CLI (`sglang.cli`) | Packaging entry points, model metadata, plugin/serve-backend registries | A selected LLM, diffusion, or external serving launch |
| Protocol entry points (`srt.entrypoints`) | FastAPI/ASGI, protocol schemas, templates, `TokenizerManager` | Native, OpenAI, Anthropic, Ollama, gRPC, and management surfaces |
| Tokenizer side (`srt.managers.tokenizer_manager`) | Tokenizers, parsers, multimodal processors, request schemas, ZMQ | Validated tokenized requests and correlated client responses |
| Scheduler (`srt.managers.scheduler`) | Runtime context, queues/batches, cache managers, model execution, distributed groups | Ordered accelerator work and token/embedding results |
| Model executor and models | Model loaders/configs, layers, attention/sampling/quantization backends | Forward-pass outputs for scheduled batches |
| Kernel layers | Torch/custom-op interfaces, JIT/AOT/native or external kernel packages | Device operations used by layers and caches |
| Detokenizer | Tokenizer, output message schemas, ZMQ | Incremental/final text returned to the tokenizer side |

The default startup path linking these layers is source-visible in
[`launch_server`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2767-L2828)
and [`Engine._launch_subprocesses`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1022-L1237).

## Native and external boundaries

- The Python build reads the [`rust` Cargo workspace](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/rust/Cargo.toml#L1-L31)
  and builds crates that declare a Python module. Native gRPC can then bridge
  back into live tokenizer/runtime state.
- `python/sglang/kernels` wraps SGLang-owned compiled/JIT operations, while the
  Python dependency manifest also brings in specialized packages such as
  FlashInfer, SGL Kernel, DeepGEMM, and hardware-specific backends
  ([base dependencies](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/pyproject.toml#L18-L100)).
- `sgl-model-gateway` and `experimental/sgl-router` sit in front of workers.
  They depend on HTTP/gRPC, tokenization, discovery, and routing state, but they
  do not replace scheduler-owned model execution.
- `sglang.multimodal_gen` has its own runtime managers, pipelines, models,
  distributed execution, and optional dependency group. Its reuse of shared
  package utilities does not make it a mode inside the SRT scheduler.

## Configuration dependency

Raw CLI/config values become `ServerArgs`; resolution derives a consistent
record; `runtime_context.publish` projects process-local, read-only namespace
bags; runtime modules read those bags and live distributed topology. This order
is important:

```text
CLI/config file -> raw ServerArgs -> resolve/check -> publish(role)
                -> config namespaces + live parallel state -> runtime behavior
```

See [`prepare_server_args`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L10510-L10544),
[`resolve_once`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L3667-L3698),
and [`publish`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/runtime_context.py#L1308-L1355).
The full dependency order and mutation boundaries are explained in
[Configuration and startup](02-configuration-and-startup.md).

| Configuration component | Depends on | Supplies |
| --- | --- | --- |
| CLI annotation layer | Dataclass types/defaults, `Arg` metadata | One argparse grammar and raw `ServerArgs` |
| YAML merger | The constructed argparse actions | Lower-precedence CLI tokens, not a second schema |
| Resolution pipeline | Raw values, model metadata, hardware/platform probes, ordered declarations | A materialized read-only startup record |
| Runtime publication | Resolved record and `NS` metadata | Process-role provenance and nested config bags |
| Parallel context | Published topology config and initialized process groups | Configured launch sizes before init; live ranks/groups after init |
| Launch/warmup | Published config, ports, ranks, scheduler pipes, HTTP lifecycle | Scheduler readiness followed by public service readiness |

## Questions for later passes

- Which request/output message types cross each ZMQ channel?
- Which cache owns token slots, KV tensors, radix nodes, host storage, and
  external/disaggregated copies?
- Which model/layer abstractions are stable extension points versus
  hardware/model-specific implementations?
- Which Rust server and gateway protocols are generated from shared schemas,
  and where are compatibility versions enforced?
