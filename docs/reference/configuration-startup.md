# Configuration and Startup: File and Symbol Reference

Read the [conceptual guide](../02-configuration-and-startup.md) first. This
reference records what each configuration/platform file contributes and where
coverage deliberately stops. All links target the pinned source snapshot.

## `python/sglang/srt/server_args.py`

**Status: partial.** The configuration lifecycle, field-group map, resolution
dispatcher, validation entry, read-only boundary, legacy global shims, CLI
preparation, and `PortArgs` endpoint construction are covered. The thousands of
model/backend-specific decisions inside individual `_handle_*` methods remain
owned by their later model, kernel, cache, and distributed guides.

`ServerArgs` is the typed raw/resolved launch record. `Arg` metadata generates
most of its CLI and `NS` metadata maps fields to runtime bags
([class and authoring contract](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L476-L516)).
The fields are grouped by operator concern from model/tokenizer through
parallelism, APIs, kernels, speculation, caches, disaggregation, loading, and
operations
([fields](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L518-L3655)).

Construction remains raw. `resolve_once` guards the non-idempotent pipeline and
poisons a partially transformed object after failure. `replace_resolved`
preserves raw/declaration provenance when a resolved copy must cross a process
boundary
([lines 3657-3747](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L3657-L3747)).
`_run_resolution_pipeline` is the ordered normalization/policy dispatcher; it
must keep consumers after their prerequisites and materializes declarations at
the end
([lines 3759-3977](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L3759-L3977)).
The post-resolution `__setattr__` guard rejects ordinary writes so live changes
cannot silently desynchronize the namespace bags
([lines 9651-9685](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L9651-L9685)).

`check_server_args` is the launch-stage cross-field gate. It validates topology,
graph/compile compatibility, PP and DP restrictions, LoRA, speculation,
chunk/page geometry, worker counts, scheduling, metrics, communication, and
port conflicts; specialized helpers extend that matrix
([lines 9802-10439](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L9802-L10439)).
Some checks perform declared late resolution, so this call must happen before
publication.

`prepare_server_args` creates the parser, optionally merges YAML, parses, sets
basic logging, and constructs the raw dataclass
([lines 10510-10544](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L10510-L10544)).
`PortArgs.init_new` allocates local IPC or deterministic DP-attention TCP
endpoints and validates required speculative/port inputs
([lines 10552-10722](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L10552-L10722)).

**Failure modes.** Re-resolution corrupts transformed values; late writes after
publish are refused; platform/model probes can reject unavailable kernels or
unsafe combinations; TCP derived ports can collide; and a user-facing option
can pass argparse yet fail only when its dependent model/hardware facts exist.

## `python/sglang/srt/server_args_config_parser.py`

**Status: covered.** `ConfigArgumentMerger` validates one YAML path, requires a
mapping root, serializes scalar/list/dict values into CLI tokens, and prepends
them so later explicit CLI tokens win
([class and merge](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args_config_parser.py#L17-L83),
[conversion](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args_config_parser.py#L85-L187)).

The merger inspects the actual parser to distinguish `store_true` actions and
reject unsupported custom actions. YAML false omits a store-true flag; empty
lists emit nothing; dicts are JSON-encoded. File I/O/YAML exceptions propagate
after logging, while malformed shape, suffix, missing path, and multiple config
flags produce explicit value errors.

## `python/sglang/srt/arg_groups/__init__.py`

**Status: covered.** The file is intentionally empty. It marks the directory as
a package but exports no aggregate API or import-time registration. Callers
import metadata, actions, declarations, and feature hooks from their defining
modules directly
([empty source file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/arg_groups/__init__.py)).

## `python/sglang/srt/arg_groups/arg_utils.py`

**Status: covered.** `Arg` is frozen CLI metadata; `NS` is an independent
dotted namespace marker. Cached introspection functions extract namespace,
field, and resolvable-field sets from dataclass annotations
([lines 62-145](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/arg_groups/arg_utils.py#L62-L145)).

The private unwrappers normalize `Annotated`, `Optional`, `Literal`, Python
defaults/default factories, and field-to-flag naming. The public
`add_cli_args_from_dataclass` then generates custom actions, literal choices,
lists, booleans, or scalars and preserves the dataclass field as argparse's
destination
([lines 155-345](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/arg_groups/arg_utils.py#L155-L345)).

**Invariant.** Fields without supported annotation metadata or marked `no_cli`
are skipped; they are not accidentally exposed. Requiredness is inferred only
when a flag-like argument has no default, and an explicit type parser takes
ownership of list-shaped input instead of the generic `nargs` branch.

## `python/sglang/srt/arg_groups/argparse_actions.py`

**Status: covered.** `LoRAPathAction` accepts a list of plain paths or JSON
objects and requires JSON entries to contain both `lora_name` and `lora_path`
([lines 8-25](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/arg_groups/argparse_actions.py#L8-L25)).
The remaining action classes implement four deprecation behaviors: warn-only
or hard error, store `True`, store a fixed replacement value, and store an
alias's parsed value. Each warning names the replacement when available
([lines 28-113](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/arg_groups/argparse_actions.py#L28-L113)).

These are CLI translation adapters, not resolution rules. The YAML merger
rejects them because it only knows how to reproduce ordinary store/store-true
semantics safely.

## `python/sglang/srt/arg_groups/overrides.py`

**Status: partial.** The declaration engine, registries, read-only resolving
view, late/direct-write bridges, materialization, shared derived predicates,
and validation contract are covered. Individual architecture providers and
backend post-process policies remain for model/kernel guides.

Constant, architecture-keyed, and predicate-keyed registries return field
declarations rather than mutating `ServerArgs`
([registry](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/arg_groups/overrides.py#L66-L124)).
`ResolvedView` overlays accumulated declarations, ordered post-process passes
append new declarations, and `declare_resolution` validates field names before
writing during the pipeline
([lines 126-261](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/arg_groups/overrides.py#L126-L261)).
Late resolution refuses an already published record; direct-write capture
bridges out-of-tree callbacks; materialization and `resolution_result` make the
same last-writer result visible both on the record and in projected bags
([lines 263-389](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/arg_groups/overrides.py#L263-L389)).

**Failure modes.** A provider returning a non-dict, declaring an unknown or
non-resolvable field, mutating a read-only view, or attempting late resolution
after publish fails loudly. Ordering is semantically significant because later
declarations win.

## `python/sglang/srt/runtime_context.py`

**Status: partial.** Publication, config bags, live parallel delegation,
runtime flag/resource tiers, forward-scoped state, runtime overrides,
role-namespace policy, lifecycle snapshot/restore, and configured-size/derived
accessor intent are covered. Individual derived helpers will be revisited with
their owning cache/speculation/MoE subsystems.

`ParallelContext` delegates size/rank/group properties live and serves
config-only topology leaves from the published parallel bag
([lines 116-310](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/runtime_context.py#L116-L310)).
Typed flag groups reject mistyped fields and support transactional test
overrides; `Resources` owns process handles; `ForwardFlags` separates
context-local values from graph-visible plain slots
([lines 312-594](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/runtime_context.py#L312-L594)).

`_ConfigBag` and `_build_config_bags` create the read-only, Dynamo-traceable
resolved tree
([lines 596-730](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/runtime_context.py#L596-L730)).
`RuntimeContext` owns the startup record, bags, overrides, role, flags,
resources, and forward state. Permanent runtime overrides validate all routes
before writing and preserve provenance; readback overlays those changes without
altering the startup record
([lines 732-994](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/runtime_context.py#L732-L994)).

`publish` is process-local and last-publish-wins. `ensure_published` avoids an
unnecessary reprojection for the exact record/role
([lines 1308-1380](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/runtime_context.py#L1308-L1380)).
`snapshot_context`, `restore_context`, and `reset_context` cover all owned slots
and copy mutable flag leaves so a failed launch can restore the prior lifecycle
instead of retaining values seeded by the failed publish
([lines 1412-1501](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/runtime_context.py#L1412-L1501)).

## `python/sglang/srt/platforms/__init__.py`

**Status: covered.** The module lazily exposes `current_platform`. Explicit
selection imports only one named entry point; automatic discovery activates all
plugins and requires zero or one match. Built-in fallback prioritizes explicit
CPU mode, then CUDA, ROCm, XPU, and the base platform
([lines 26-172](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/__init__.py#L26-L172)).
`_load_platform_class` rejects non-classes and classes outside the
`SRTPlatform` hierarchy. Plugin activation exceptions are logged; they are
strict under explicit selection but an auto-discovery failure can be bypassed
by another valid activation or built-in fallback.

## `python/sglang/srt/platforms/device_mixin.py`

**Status: covered.** `PlatformEnum`, `CpuArchEnum`, and `DeviceCapability`
normalize identity and comparable compute versions
([lines 38-81](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/device_mixin.py#L38-L81)).
`DeviceMixin` supplies identity predicates, active memory/pinning contracts,
device/distributed operations, deterministic seeding, CPU-architecture
detection, profiler hooks, and conservative/default behavior
([lines 94-267](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/device_mixin.py#L94-L267)).

The source labels methods active or planned. A planned method can be correctly
implemented by a plugin yet remain unused until core call sites adopt it. The
distributed backend map defaults unknown devices to Gloo; new platforms should
override that when the fallback is inappropriate.

## `python/sglang/srt/platforms/interface.py`

**Status: covered.** `SRTPlatform` extends device behavior with startup-default,
attention/graph/KV-pool/allocator/compiler/quantization factories, conservative
capability flags, worker initialization, and fused-op dispatch identity
([lines 26-140](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/interface.py#L26-L140)).
The base default hook is a no-op, compile backend is `inductor`, dispatch key is
`native`, capabilities are false, and factories without a safe generic
implementation raise. This makes unsupported use fail at the factory boundary
instead of silently choosing a device-specific implementation.

## `python/sglang/srt/platforms/cuda.py`

**Status: covered.** `CudaDeviceMixin` maps memory, device identity,
synchronization, cache, availability, pinned memory, NCCL, and seeding to
`torch.cuda`; `CudaSRTPlatform` declares FP8 and both decode/piecewise graph
support
([lines 15-80](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/cuda.py#L15-L80)).
Pinned memory is deliberately false when the requested target is CPU even on a
CUDA host.

## `python/sglang/srt/platforms/rocm.py`

**Status: covered.** PyTorch exposes HIP devices through `torch.cuda`, so
`RocmDeviceMixin` inherits CUDA operations but changes platform identity while
retaining `device_type="cuda"`. `RocmSRTPlatform` keeps conservative base
capabilities because detailed in-tree AMD gates still use legacy HIP checks
([lines 1-31](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/rocm.py#L1-L31)).

## `python/sglang/srt/platforms/cpu.py`

**Status: covered.** `CpuDeviceMixin` treats system available RAM as free
capacity, returns one unindexed CPU device for all ranks, uses Gloo, performs GC
on cache-empty requests, and exposes a cached host-architecture identity
([lines 20-121](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/cpu.py#L20-L121)).
It intentionally reports whole-machine rather than process RSS; per-rank NUMA
isolation belongs to thread/NUMA binding, not the device object. GC may free
cycles into the allocator without reducing RSS. `CpuSRTPlatform` keeps graph
and FP8 capabilities false and pinned memory unavailable
([lines 123-133](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/cpu.py#L123-L133)).

## `python/sglang/srt/platforms/xpu.py`

**Status: covered.** `XpuDeviceMixin` maps device/memory/cache/sync operations
to `torch.xpu`, obtains capability through the SGL kernel op, validates device
IDs for memory queries, uses inherited XCCL mapping, and seeds every XPU
([lines 18-92](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/xpu.py#L18-L92)).
Its free-memory calculation uses total minus allocated memory and warns if the
queried device is not current. `XpuSRTPlatform` supports graph capture but not
FP8
([lines 94-104](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/platforms/xpu.py#L94-L104)).

## Startup symbols in large runtime files

These files remain partial because later guides own their main APIs:

- `entrypoints/engine.py`: `SchedulerInitResult`, scheduler/detokenizer launch,
  `_launch_subprocesses`, rank math, readiness polling, and `shutdown` are
  covered
  ([launch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L818-L1269),
  [readiness and rank math](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1773-L1864)).
- `entrypoints/http_server.py`: health gating, ASGI lifespan cleanup, general
  warmup, Python/Rust readiness, HTTP worker startup, and native gRPC lifecycle
  are covered
  ([lifespan](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L269-L430),
  [warmup](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2187-L2434),
  [launch](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2514-L2828)).
- `managers/scheduler.py`: initialization handshake, graceful shutdown flag,
  process error signaling, and host-resource release are covered; admission,
  batches, caches, and model execution remain pending
  ([handshake](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L1675-L1702),
  [process entry](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L5145-L5233)).

## Reference study check

For one option, identify its dataclass field, generated or manual CLI action,
YAML representation, resolution writer, `NS` path, published accessor, and
first runtime consumer. Then repeat for one topology field whose live
`get_parallel()` value can only exist after distributed initialization.
