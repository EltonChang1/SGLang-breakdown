# Diffusion Generate CLI: File and Symbol Reference

This reference owns the installed `sglang generate` wrapper, the secondary
diffusion CLI package, the complete `DiffGenerator` public class, its active
launch/client/output helpers, and focused tests. Large model configuration,
request, and worker files are `partial` only for the named CLI-reached symbols;
their pipeline and execution internals remain in Phase 7.

## Public wrapper and model classification

### `python/sglang/cli/generate.py`

**Status: covered.** `generate` special-cases help, extracts the model path,
calls the shared diffusion classifier, lazily imports diffusion-only parser
code, and delegates parsed/unknown arguments to `generate_cmd`. A non-diffusion
classification raises because this public command has no LLM implementation
([lines 1-33](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/generate.py#L1-L33)).

The help branch must precede model extraction: help is useful without a model
and importing diffusion code is deferred until the user selects this surface.
The wrapper uses ordinary `ArgumentParser`, so underscore/dash normalization
from the diffusion `FlexibleArgumentParser` is not part of the installed path.

### `python/sglang/cli/utils.py`

**Status: covered.** The overlay registry is loaded once. Model classification
then checks overlay and native registries, local Diffusers metadata, and a
remote model-index download, returning false on optional-dependency or remote
failures. `_is_gated_diffusion_repo` exists but is not called by
`get_is_diffusion_model` in this snapshot
([lines 18-96](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/utils.py#L18-L96)).

`try_get_model_path` accepts separate or equals forms of `--model-path` and
`--model`; `get_model_path` turns absence into usage/error text. The help text
still says `sglang serve`, even when the caller is `generate`
([lines 99-132](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/utils.py#L99-L132)).
`get_git_commit_hash` prefers `SGLANG_GIT_COMMIT`, then Git, then `N/A`, and is
cached for the process
([lines 135-151](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/utils.py#L135-L151)).

## Diffusion CLI package

### `python/sglang/multimodal_gen/runtime/entrypoints/__init__.py`

**Status: covered.** This is an intentionally behavior-free package marker
containing only the SPDX license declaration
([file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/__init__.py#L1)).

### `python/sglang/multimodal_gen/runtime/entrypoints/cli/__init__.py`

**Status: covered.** This is an intentionally behavior-free package marker; it
contains only provenance text. Imports must target the concrete command files
([file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/cli/__init__.py#L1)).

### `cli_types.py`

**Status: covered.** `CLISubcommand` is a structural base, not an abstract base
class. Subclasses supply `name`, `cmd`, and `subparser_init`; validation is a
no-op by default. Missing command/subparser implementations fail only when
called
([lines 8-30](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/cli/cli_types.py#L8-L30)).

### `main.py`

**Status: covered.** The secondary `sglang-diffusion CLI` parser registers
`GenerateSubcommand` and `ServeSubcommand`, parses known arguments, validates
only a recognized subcommand, passes unknown arguments to the command, and
prints help if none was selected. Its version is a literal `0.1.0`
([lines 12-44](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/cli/main.py#L12-L44)).

This module is not the installed `sglang` console target. It is a runnable
secondary dispatcher and should not be inserted into the installed flow trace.

### `generate.py`

**Status: covered.** Its responsibilities are:

- register config, performance, output alias, server, base sampling, and
  intentionally unsupported text-encoder flags;
- select the model/pipeline sampling subclass for config-field filtering;
- merge config and explicit sampling values, apply the output alias, assign a
  UUID, and parse `diffusers_kwargs` JSON;
- enable server-side diffusion-decoder loading when the request asks for it;
- construct a local `DiffGenerator`, call `generate`, and optionally dump the
  first result's metrics; and
- validate positive `num_gpus` and config-file existence through
  `GenerateSubcommand`
  ([argument layer, lines 34-105](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/cli/generate.py#L34-L105),
  [execution, lines 108-206](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/cli/generate.py#L108-L206),
  [subcommand, lines 209-250](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/cli/generate.py#L209-L250)).

`init_arg_names` and `generation_arg_names` are populated but not read elsewhere
in the tracked snapshot. `args.request_id` is assigned a mock value, but the
sampling record receives a separately generated real UUID. Failure to produce
results is not converted to a nonzero process status.

### `serve.py`

**Status: covered.** The sibling command registers config plus the complete
`ServerArgs` grammar. It creates server args with serving-specific defaults,
routes through `dispatch_launch`, and starts the Web UI after that function
returns when requested. `ServeSubcommand` checks config existence and owns the
subparser
([lines 18-77](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/cli/serve.py#L18-L77)).

For the usual blocking HTTP branch, `dispatch_launch` does not return until
server shutdown. Web UI mode starts HTTP in a child and can return process
handles, which is why the follow-on Web UI branch is meaningful.

### `utils.py`

**Status: covered.** `RaiseNotImplementedAction` makes reserved flags fail at
parse time. `launch_distributed` builds a `torch.distributed.run` subprocess,
streams combined output, and returns its exit code
([lines 16-75](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/cli/utils.py#L16-L75)).

No tracked caller uses `launch_distributed`, and its computed target
`python/sglang/sgl_diffusion/sample/v1_sgl_diffusion_inference.py` is absent.
It is completely explained here as dead/unintegrated compatibility code; the
active multiprocess path is `runtime/launch_server.py`.

## Public Python export and configuration boundary

### `python/sglang/multimodal_gen/__init__.py`

**Status: covered.** The package exports `DiffGenerator`, `PipelineConfig`, and
`SamplingParams` eagerly. Unlike the root `sglang` package's lazy heavy runtime
objects, importing this surface loads the diffusion generator module and
therefore applies its multiprocessing start-method side effect
([lines 1-6](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/__init__.py#L1-L6)).

### `runtime/server_args/__init__.py`

**Status: covered.** This façade re-exports server-configuration constants,
enums, constructors, `ServerArgs`, and `PortArgs`. Its module-level
`__getattr__` dynamically forwards `_global_server_args` so readers see the
current value rather than a stale import-time copy
([lines 1-42](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/server_args/__init__.py#L1-L42)).

### `runtime/server_args/server_args.py`

**Status: partial. Covered symbols:** CLI/config construction, configuration
adjustment/validation boundary, `scheduler_endpoint(s)`, parallel validation,
`PortArgs`, and global argument publication.

`ServerArgs` separates total world size from node count/rank, describes DP and
within-replica parallel degrees, and defaults persistent output to `outputs/`
([fields, lines 215-310](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/server_args/server_args.py#L215-L310),
[runtime/output fields, lines 430-452](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/server_args/server_args.py#L430-L452)).
`__post_init__` normalizes component weights and roles, adjusts the full record,
validates it, and logs a sanitized view
([lines 1697-1744](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/server_args/server_args.py#L1697-L1744)).

The parser merge uses only explicitly supplied values, config sits below CLI,
and unknown arguments are limited to dynamic component paths, weight paths,
and attention backends
([lines 2874-2927](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/server_args/server_args.py#L2874-L2927)).
DP endpoints are consecutive ports unless settled ports were recorded;
multi-node and parallel-degree checks reject inconsistent world layouts
([lines 2707-2727](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/server_args/server_args.py#L2707-L2727),
[lines 3239-3312](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/server_args/server_args.py#L3239-L3312)).

`PortArgs.from_server_args` creates local IPC filenames and a free NCCL port.
`DiffGenerator` stores this record, but the active synchronous request path
uses TCP scheduler endpoints from `ServerArgs`; worker processes create their
own `PortArgs`
([lines 3356-3396](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/server_args/server_args.py#L3356-L3396)).

**Remaining work.** Model selection, performance-mode adjustment, residency,
offload, quantization, attention, warmup, batching, disaggregation, and every
pipeline-specific policy remain with Phase 7.

### `configs/sample/sampling_params.py`

**Status: partial. Covered symbols:** request ID, filename/type helpers, output
fields, CLI registration/extraction, model-specific construction/merge,
adjustment boundary, and output-path generation.

`SamplingParams` is both a request schema and a dynamic-batching signature;
fields marked `batch_sig_exclude` do not determine compatibility
([lines 97-166](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/configs/sample/sampling_params.py#L97-L166)).
Filename construction is deterministic for all fields except its embedded
timestamp, sanitizes user/prompt text, and appends a type extension
([lines 306-345](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/configs/sample/sampling_params.py#L306-L345)).

`from_user_sampling_params_args` chooses the pipeline/model subclass, builds a
default instance and a user instance, merges explicit fields, preserves raw
Diffusers kwargs, adjusts against server configuration, and runs pipeline
validation
([lines 816-897](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/configs/sample/sampling_params.py#L816-L897)).
CLI actions suppress defaults so absence cannot overwrite config/model values;
`get_cli_args` intersects only present namespace attributes, expands resolution
shortcuts, normalizes a one-item seed list, and collects Spectrum overrides
([lines 905-913](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/configs/sample/sampling_params.py#L905-L913),
[lines 1427-1486](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/configs/sample/sampling_params.py#L1427-L1486)).

**Remaining work.** The full field catalog, validation matrix, video model
hooks, action/mesh adjustments, cache/quality/rollout controls, and model
subclasses remain for the diffusion configuration guide.

## Offline generator implementation

### `runtime/entrypoints/diffusion_generator.py`

**Status: covered.** Import forces multiprocessing `spawn`, protecting CUDA
from fork inheritance. Construction supports an existing `ServerArgs`, a dict,
or keyword construction; local mode starts workers and warmup, while remote
mode initializes the same client and pings every endpoint
([lines 58-175](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/diffusion_generator.py#L58-L175)).

`generate` owns the complete public image/video/mesh request lifecycle:

- prompt-file resolution and per-prompt image pairing;
- model-specific sampling creation and preservation of explicit-field
  provenance across `dataclasses.replace`;
- per-output seed, ID, trace, and filename expansion;
- model-owned video queue preparation and idempotent cleanup;
- one synchronous scheduler call per prompt's output group;
- file-path, mesh, or payload result branches with exact output-count checks;
- per-group error logging/continuation, aggregate summary, and single/list/none
  return shaping
  ([lines 177-274](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/diffusion_generator.py#L177-L274),
  [lines 276-419](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/diffusion_generator.py#L276-L419)).

`generate_action` is deliberately separate: it requires an action pipeline,
sends one request, and returns the first policy output or raises on error/empty
output. `_result_common` maps media/action dimensions and picks per-output
metrics when a grouped batch supplied them
([lines 421-447](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/diffusion_generator.py#L421-L447),
[lines 489-531](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/diffusion_generator.py#L489-L531)).

LoRA controls construct typed requests, share one error-checking helper, and
offer a convenience `generate_with_lora`. The generator keeps no client-side
LoRA cache; server operations own idempotence
([lines 533-673](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/diffusion_generator.py#L533-L673)).

Graceful shutdown is bounded and escalates. Context-manager exit calls it;
finalization uses a shorter force-only path resilient to missing module globals
during interpreter teardown
([lines 675-758](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/diffusion_generator.py#L675-L758)).

**Invariants and failures.** Multi-prompt fixed names and ambiguous image
pairing are rejected. Returned output count must equal expanded request count.
Video queue cleanup occurs on preparation failure and after every attempted
group. Scheduler/persistence errors are swallowed per group; all failure yields
`None`. Despite the optional annotation, `sampling_params_kwargs` must not be
`None` because the first operation is `.get`.

## Request, output, and transport helpers

### `runtime/entrypoints/utils.py`

**Status: covered.** This file defines all small control request records,
`GenerationResult`, `MaterializedOutput`, LoRA logging format, request/output
expansion, frame/audio materialization, and persistence.

`normalize_output_seeds` accepts an integer, one prompt's exact seed list, or a
flattened all-prompt list. `expand_request_outputs` uses shallow copies so large
tensors are not duplicated, but copies mutable sampling/extra/condition maps,
creates independent tracing for outputs after zero, and refreshes model-owned
request extras before validation
([lines 259-379](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/utils.py#L259-L379)).

`prepare_request` wraps sampling parameters in `Req`, applies request extras,
gives explicit Diffusers max-sequence-length precedence, validates prompt and
positive dimensions, and attaches tracing when enabled
([lines 882-923](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/utils.py#L882-L923)).

The output layer has three levels:

1. normalize tensor/NumPy frames and optional audio, then lazily interpolate or
   upscale;
2. save one materialized image/video/action, preferring single-pass audio and
   falling back to compatible encoding/mux paths; and
3. coordinate a sequence of outputs, including two-at-a-time parallel CUDA
   direct video saves and serial fallback
   ([audio/direct-video helpers, lines 382-879](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/utils.py#L382-L879),
   [materialization, lines 926-1123](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/utils.py#L926-L1123),
   [sequence save, lines 1126-1289](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/utils.py#L1126-L1289)).

The direct path uses a CUDA-registered memfd with locked single-buffer reuse,
bounded cache/chunk sizes, explicit file-descriptor/mmap unregister cleanup,
FFmpeg discovery, bounded thread selection, and `sendfile` transfer. Any
unsupported platform/shape/tool condition returns false so the portable path
can take over
([lines 51-159](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/utils.py#L51-L159),
[lines 436-737](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/entrypoints/utils.py#L436-L737)).

### `runtime/pipelines_core/schedule_batch.py`

**Status: partial. Covered symbols:** `Req` sampling delegation and
`output_file_path`, plus `OutputBatch`'s CLI-visible payload/error/metrics/path
contract.

`Req` delegates unknown reads and sampling-field writes to its owned
`SamplingParams`. `output_file_path` adds an index only when asked to name
multiple outputs and returns `None` when path or name is absent
([lines 236-323](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/pipelines_core/schedule_batch.py#L236-L323)).
`OutputBatch` can carry tensor/NumPy output, raw frames, audio, actions,
trajectories, an error, saved paths, single/per-output metrics, peak memory, and
usage
([lines 440-480](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/pipelines_core/schedule_batch.py#L440-L480)).

**Remaining work.** Full request state, batching signature, latent/prompt
fields, validation, logging, warmup mutation, and pipeline-stage consumers.

### `runtime/managers/gpu_worker.py`

**Status: partial. Covered symbols:** output transport/materialization/saving
and `run_scheduler_process`.

The transport branch selects raw frames, saved paths, or returned frames. Only
the output rank materializes; saved-path mode clears tensor/audio payloads
before ZMQ return
([lines 610-720](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/managers/gpu_worker.py#L610-L720)).
Single and grouped save helpers preserve request-specific names and validate
shared output settings
([lines 762-870](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/managers/gpu_worker.py#L762-L870)).

`run_scheduler_process` applies parent-death handling, logging/platform setup,
tracing, local ports, constructs the deeper `Scheduler`, sends readiness only
after construction, enters its event loop, and tears down cache/process-group
state in `finally`
([lines 1167-1232](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/managers/gpu_worker.py#L1167-L1232)).

**Remaining work.** Model/pipeline loading, execution, grouping, metrics,
post-training, memory, and LoRA worker implementation remain in Phase 7.

## Worker launch and scheduler clients

### `runtime/launch_server.py`

**Status: covered.** `_find_available_port` searches a bounded wrapping port
range; `kill_process_tree` resets the main-thread child handler and kills
descendants with an optional parent/skip boundary
([lines 38-93](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/launch_server.py#L38-L93)).
The remaining cleanup helpers implement graceful monolithic
scheduler shutdown followed by one shared ten-second join deadline, terminate,
and kill. Disaggregated roles skip the monolithic control request
([lines 95-169](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/launch_server.py#L95-L169)).

`launch_server` is the active monolithic/offline launcher. It derives local and
global ranks from `num_gpus`, `nnodes`, and `node_rank`; wires local driver/slave
pipes; starts every worker; closes unused parent ends; waits for every ready
record; keeps nonzero nodes worker-only; and either starts HTTP or returns the
workers for offline mode
([lines 171-330](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/launch_server.py#L171-L330)).

The remainder of the file owns diffusion serving launch variants:

- pool disaggregation allocates work/result endpoints, derives per-role
  `ServerArgs`, starts all ranks before NCCL readiness waits, starts a
  `DiffusionServer`, and optionally HTTP
  ([lines 333-539](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/launch_server.py#L333-L539));
- `launch_http_server_only` publishes args and runs Uvicorn, while URL parsing
  splits semicolon-separated role endpoints
  ([lines 542-594](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/launch_server.py#L542-L594));
- server-role disaggregation connects one orchestrator to remote role pools and
  owns its stop lifecycle
  ([lines 596-671](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/launch_server.py#L596-L671));
- standalone encoder/denoiser/decoder roles derive nonconflicting internal
  endpoints, build role-specific parallelism, spawn all ranks before readiness,
  block, and force cleanup
  ([lines 673-793](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/launch_server.py#L673-L793)); and
- `dispatch_launch` sets NCCL NVLS policy and selects monolithic, server, or
  worker-role launch. Module execution guarantees descendant cleanup
  ([lines 796-818](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/launch_server.py#L796-L818)).

The file is covered at its launch/control level. The orchestrator, role
transfer protocol, and scheduler internals it calls remain separate pending
files.

### `runtime/scheduler_client.py`

**Status: covered.** Both clients create one `REQ` socket per call, apply an
optional bounded receive timeout, close with zero linger, materialize spilled
IPC-array references after receive, and translate ZMQ timeout into
`TimeoutError`. The synchronous form sends Python objects; the async form
serializes with pickle
([sync client, lines 145-225](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/scheduler_client.py#L145-L225),
[async client, lines 228-326](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/scheduler_client.py#L228-L326)).

Ordinary requests round-robin across DP endpoints; realtime session CRC32 pins
state; control types fan out; and the first error wins the merged response
([lines 39-53](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/scheduler_client.py#L39-L53),
[lines 117-142](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/scheduler_client.py#L117-L142)).
`run_zeromq_broker` bridges offline pickle requests in an HTTP process to the
shared async client and always attempts an error reply so REQ clients do not
hang
([lines 78-115](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/runtime/scheduler_client.py#L78-L115)).

## Focused test files

### Fully covered tests

| File | What it proves |
| --- | --- |
| [`test_resolve_prompts.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_resolve_prompts.py#L1-L100) | Inline/list/blank prompt behavior, request/server path priority, missing/empty file errors |
| [`test_output_saving.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_output_saving.py#L1-L245) | PNG fidelity/compression path, audio one-pass/fallback, x264 threads, direct and parallel video saves |
| [`test_diffusion_generator_shutdown.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_diffusion_generator_shutdown.py#L1-L99) | bounded graceful shutdown, terminate/kill escalation, forceful finalization during module teardown |
| [`test_launch_server_shutdown.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_launch_server_shutdown.py#L1-L83) | monolithic shutdown request, client closure on errors, disaggregated skip behavior |
| [`test_scheduler_client.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_scheduler_client.py#L1-L160) | configured/explicit deadlines, delayed response, invalid timeout, cancellation and broker cleanup |
| [`test_dp_routing.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_dp_routing.py#L1-L68) | round robin, session affinity, control classification, first-error merge, DP endpoint list |
| [`cli_generate_common.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/single_test_file/cli_generate_common.py#L1-L119) | isolated output directory, exact installed command shape, status/file/dimension verification |
| [`test_cli_generate_common.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_cli_generate_common.py#L1-L69) | harness quoting/token construction and positive/missing image verification |
| [`test_generate_i2i.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/single_test_file/test_generate_i2i.py#L1-L135) | Qwen edit single/multiple prompt-image pairing, file count, output dimensions |
| [`test_generate_zimage_turbo_cli.py`](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/single_test_file/test_generate_zimage_turbo_cli.py#L1-L45) | inherited installed-command smoke test and output-file-path alias precedence |

### Partial test files

- `test_multi_output_grouping.py`: the seed/ID/filename tests through line 133
  are covered; latent splitting and stage-deduplication cases belong to the
  pipeline-stage pass
  ([covered slice](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_multi_output_grouping.py#L76-L133)).
- `test_sampling_params.py`: the CLI Diffusers-kwargs and explicit-field
  preservation cases are covered; the broader model adjustment and validation
  matrix remains with sampling configuration
  ([covered slice](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_sampling_params.py#L435-L503)).
- `test_cfg_parallel_warmup.py`: only the explicit
  `DiffGenerator`-to-scheduler warmup case is reached here; worker warmup and
  model-stage cases remain later
  ([covered slice](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/test_cfg_parallel_warmup.py#L253-L300)).
- `realtime/test_output_materialization.py`: tensor-to-frame conversion,
  materialization without persistence, and payload clearing through line 78
  are covered; raw realtime RGB batching/upscaling belongs to the realtime
  serving pass
  ([covered slice](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/multimodal_gen/test/unit/realtime/test_output_materialization.py#L18-L78)).

GPU tests were not run for this documentation pass because they require model
downloads and accelerator resources. The isolated unit files are the practical
local regression boundary for the public flow.

## Study check

Starting from `sglang generate --model-path ...`, name the symbol that owns:

1. diffusion classification;
2. server/config precedence;
3. model-specific sampling defaults;
4. global/local worker rank mapping;
5. DP replica selection;
6. per-output seed and name expansion;
7. worker-side output persistence;
8. `GenerationResult` construction; and
9. graceful then forceful cleanup.
