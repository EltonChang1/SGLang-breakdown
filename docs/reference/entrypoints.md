# Serving Entry Points: File and Symbol Reference

This note explains the files that turn an installed `sglang` command or Python
import into a running language-model server. The small dispatcher files are
covered completely. Large runtime files are covered only for the named startup
and one-request symbols; their other APIs remain `partial` in the ledger.

## `python/pyproject.toml`

**Purpose and placement.** This is the Python distribution manifest and the
source of the installed console commands. It declares Python 3.10+, the base and
optional dependency sets, package data, wheel exclusions, SCM versioning, and
the two scripts `sglang` and `killall_sglang`
([lines 1-18](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/pyproject.toml#L1-L18),
[lines 202-253](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/pyproject.toml#L202-L253)).

**Inputs and outputs.** Build tools consume this manifest and `setup.py`; the
output is a wheel/editable installation containing Python packages, selected
package data, and Rust extensions. Optional groups separate diffusion, Ray,
tracing, HTTP/2, checkpoint, and test dependencies, so importing a feature may
fail intentionally when its extra is absent.

**Non-obvious point.** Rust extension modules are not enumerated here. The
manifest states that `setup.py` discovers Cargo workspace crates whose metadata
declares a Python module
([lines 250-253](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/pyproject.toml#L250-L253)).
That keeps the workspace manifest authoritative but means a source distribution
without the sibling `rust/` tree needs the explicit no-Rust build path.

**Failure modes and check.** A missing optional extra produces an import error
at the feature boundary. A mismatched pinned dependency can fail much earlier
at installation. Verify that console-script targets remain import-light enough
to show help in the intended environment.

## `python/setup.py`

**Purpose.** This build hook asks `cargo metadata` for workspace packages,
selects crates carrying `[package.metadata.sglang] python-module`, and turns
them into `setuptools-rust` extensions
([`_cargo_workspace_metadata` and `_discovered_rust_extensions`, lines 50-131](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/setup.py#L50-L131)).

**Control flow.** The active pyproject can restrict extensions by substring;
the `SGLANG_BUILD_RUST_EXTS` environment variable applies a second build-time
filter. `none` short-circuits discovery, `all` or an empty value selects all,
and a comma-separated list must match at least one discovered module
([lines 121-190](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/setup.py#L121-L190)).
The custom `BuildRust` command replaces the distribution's extension list with
that selection before delegating
([lines 186-204](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/setup.py#L186-L204)).

**Invariant.** A filter token that matches nothing is an error, not a silent
extension omission. This protects platform builds from publishing a wheel that
looks successful but lacks the native module it intended to include.

## `python/sglang/__init__.py`

**Purpose.** This is the public Python API boundary.

**Control flow and side effects.** Before exporting frontend primitives it
redirects third-party cache locations, installs Apple Silicon stubs when
needed, and applies Hugging Face patches
([lines 1-23](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/__init__.py#L1-L23)).
It then imports the frontend language API, exposes client backends through
`LazyImport`, and exposes `ServerArgs` and `Engine` lazily as well
([lines 25-69](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/__init__.py#L25-L69)).

**Invariant.** Cache redirection and patches must run before imports that pull
in Torch, FlashInfer, or Transformers. Moving them below the public imports can
make the first importer permanently claim the wrong cache configuration.

**Study check.** Classify every name in `__all__` as frontend primitive, backend
client, runtime object, configuration, selection helper, or version metadata.

## `python/sglang/cli/main.py`

**Purpose.** This is the `sglang` console-script target and the complete
top-level subcommand dispatcher.

**Inputs and outputs.** It consumes `sys.argv` through `argparse`, recognizes
`serve`, `generate`, and `version`, and forwards all unparsed arguments to the
selected complex subcommand. `version` prints package and Git revision
information; the other commands own their argument grammars
([lines 7-46](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/main.py#L7-L46)).

**Non-obvious point.** `parse_known_args` and deferred imports are deliberate.
The top parser must not reject backend-specific flags or initialize a heavy
runtime before it knows which command will run.

**Failure mode.** A missing subcommand is rejected by `argparse`. Validation of
the remaining arguments belongs to the selected command, so adding a global
flag requires deciding whether it should be consumed here or forwarded.

## `python/sglang/cli/serve.py`

**Purpose.** This file normalizes the serving request, chooses a serving
backend, and owns common descendant cleanup.

**Inputs.** The file accepts either `--model-path model` or a first positional
model, plus an optional `--model-type`. `_extract_model_type_override` removes
the selector without validating it because out-of-tree entry points extend the
valid names; `_normalize_positional_model_path` rewrites a positional model to
the historical flag form
([lines 23-59](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/serve.py#L23-L59)).

**Control flow.** The built-in registry contains LLM and diffusion backends.
Diffusion has a lightweight model detector; LLM is the fallback. Backend help
is handled without launching a server. Real launches load SGLang plugins,
auto-detect or explicitly select the backend, enforce a model path when the
backend requires one, then run it
([lines 90-142](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/serve.py#L90-L142),
[lines 166-207](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/serve.py#L166-L207)).

**Outputs.** The selected backend blocks for the server lifetime. When it
returns or raises, `finally` kills descendants but not the CLI process itself.

**Failure modes.** Missing or empty selector values, unknown backends, ambiguous
detector matches, missing model paths, optional diffusion imports, and backend
startup errors all surface before or during `run`. Cleanup still runs after a
real launch attempt.

## `python/sglang/cli/serve_backends.py`

**Purpose.** This is the public extension contract for built-in and installed
serve backends. It intentionally avoids importing an inference runtime at
module import
([lines 1-11](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/serve_backends.py#L1-L11)).

**Key types.** `ServeRequest` is the normalized immutable input. `ServeBackend`
contains an API version, blocking runner, optional detector, and model-path
requirement. A detector returns `MATCH`, `NO_MATCH`, or `UNKNOWN`; it should be
lightweight and treat inconclusive metadata/I/O as unknown
([lines 28-68](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/serve_backends.py#L28-L68)).

**Discovery and validation.** The registry discovers the
`sglang.serve_backends` entry-point group without loading implementations.
Built-in and reserved names cannot be replaced. `get` lazily loads exactly one
provider and validates callable factory, return type, duplicate name, and API
version
([lines 79-171](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/serve_backends.py#L79-L171)).

**Fallback invariant.** Auto-detection never calls an LLM detector. It gathers
unique matches from other backends and falls back to `llm` only when none
matches. Broken optional detectors warn and do not break the historical LLM
path; multiple positive matches require an explicit choice
([lines 173-212](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/cli/serve_backends.py#L173-L212)).

**Study check.** Describe why a backend with no detector is still usable and
why an exception is strict under explicit selection but soft during automatic
detection.

## `python/sglang/launch_server.py`

**Purpose.** This is the LLM-mode launcher and the backward-compatible
`python -m sglang.launch_server` entry point.

**Control flow.** `run_server` first resolves configuration once, then selects:

- encoder-only HTTP or gRPC;
- legacy SMG gRPC;
- Ray-backed HTTP; or
- the default SRT HTTP server.

The native Rust gRPC port is not one of these exclusive branches; it starts
beside the default HTTP path later. The code calls this distinction out
explicitly
([lines 16-57](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/launch_server.py#L16-L57)).

When executed as a module, it warns that `sglang serve` is preferred, loads
plugins, parses arguments, runs the same dispatcher, and kills descendants in
`finally`
([lines 60-76](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/launch_server.py#L60-L76)).

**Failure mode.** `--use-ray` without the optional Ray dependency is converted
to an actionable installation error instead of a low-level missing-module
trace.

## `python/sglang/srt/server_args.py`

**Covered symbols:** `ServerArgs`, `resolve_once`, `check_server_args`,
`prepare_server_args`, and `PortArgs.init_new`.

`ServerArgs` is both the raw launcher record and the input to a resolution
pipeline. Annotated field metadata generates most CLI flags and maps resolved
values into runtime namespaces
([lines 476-516](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L476-L516)).
Construction stays raw; `resolve_once` is a separate, guarded transformation.
`check_server_args` enforces cross-field and topology invariants before child
startup. `prepare_server_args` optionally merges a config file with CLI values,
parses the result, configures basic logging, and constructs the raw record
([lines 10510-10544](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L10510-L10544)).

`PortArgs` is the concrete IPC/network wiring derived for an engine instance,
not user-facing configuration. It also carries a stable instance ID and
special endpoints for metrics, RPC, tokenizer workers, and speculative modes
([lines 10551-10635](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/server_args.py#L10551-L10635)).

The dedicated [configuration/startup reference](configuration-startup.md#pythonsglangsrtserver_argspy)
now covers argument metadata, YAML precedence, resolution/declaration
semantics, platform defaults, namespace projection, and launch validation.
Model- and backend-specific `_handle_*` policies remain with their owning
subsystem guides.

## `python/sglang/srt/entrypoints/http_server.py`

**Covered symbols:** `lifespan`, `generate_request`,
`_setup_and_run_http_server`, `_start_native_grpc_server_for_runtime`, and
`launch_server`.

`launch_server` reuses `Engine._launch_subprocesses`. The normal branch stores
the initialized tokenizer/template state and starts Uvicorn or Granian; the
Rust-server branch omits Python tokenization/detokenization, warms through the
bound native server, and waits on schedulers
([lines 2767-2828](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L2767-L2828)).

`lifespan` builds protocol-serving adapters around the live tokenizer manager,
configures optional metrics/tracing/tools/gRPC, starts warmup, and guarantees
cleanup for sidecars, gRPC, tool servers, and the warmup thread
([lines 269-430](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L269-L430)).
The native `/generate` endpoint is a thin transport adapter over the tokenizer
manager's async generator, including SSE framing and disconnect-aware errors
([lines 889-940](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/http_server.py#L889-L940)).

**Remaining work.** The OpenAI, Anthropic, Ollama, management, weight-update,
profiling, session, readiness, authentication, warmup, and error-contract
surfaces are not yet covered.

## `python/sglang/srt/entrypoints/engine.py`

**Status: covered.** The constructor, sync/async inference APIs, encoding,
reranking, scoring mixin, sessions, control/RPC methods, weight and LoRA
updates, process launch, environment setup, rank math, readiness, and shutdown
are now covered across this entry-point note, the
[configuration/startup reference](configuration-startup.md#startup-symbols-in-large-runtime-files),
and the dedicated [offline-engine reference](offline-engine.md#offline-engine-implementation).

The offline `Engine` and HTTP launcher share `_launch_subprocesses`, which is a
key anti-duplication boundary. The helper resolves and validates configuration,
allocates ports, publishes the tokenizer role, starts scheduler ranks or a data
parallel controller, conditionally starts detokenization/tokenization, waits
for model readiness, transfers scheduler limits back to the tokenizer manager,
and starts a child watchdog
([lines 1022-1237](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1022-L1237)).

**Invariants.** Nonzero distributed nodes do not construct tokenizer-side
state. Rust-server mode does not construct Python tokenizer/detokenizer state.
The published runtime context is restored if failure occurs before children are
spawned. Readiness must arrive before tokenizer limits are consumed.

**Failure and cleanup.** `Engine` registers `shutdown` with `atexit` before
launching children. Shutdown stops the watchdog, closes RPC, gracefully reaps
weight-cache daemons, kills descendants, and shuts down tokenizer-owned media
transport
([lines 265-296](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L265-L296),
[lines 1239-1269](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/entrypoints/engine.py#L1239-L1269)).

The important design boundary is now explicit: public methods construct shared
request/control records and delegate validation, locking, fan-out, and response
correlation to the tokenizer side. Ray-specific actor placement is implemented
in its own module and remains assigned to the distributed execution pass; it
does not make this file incomplete.

## `python/sglang/srt/managers/tokenizer_manager.py`

**Covered symbols:** single and batch `generate_request` flow, engine-facing
request state and response shapes, disk-update locking/readback, and GC
dispatch.

The manager owns request normalization, request-ID state, input tokenization and
multimodal preprocessing, request dispatch, client cancellation, and response
correlation. The covered path creates state before preprocessing, uses a
reader lock to prevent racing model updates, sends the tokenized request, and
yields from the response waiter
([lines 767-833](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L767-L833)).

**Invariant.** Every state entry created up front must either be removed by the
normal scheduler-response path or discarded on pre-dispatch failure. Input and
requested output length are validated against model context before scheduling
([lines 1159-1209](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/tokenizer_manager.py#L1159-L1209)).

The [offline-engine reference](offline-engine.md#tokenizer-side-boundaries)
adds batch aggregation/interleaving, pre-dispatch cleanup, embedding-override
validation, disk-update locking, config readback, and public response shapes.

**Remaining work.** Media/cache implementations, grammar and parser setup,
full output/logprob reconstruction, cancellation races, metrics,
multi-tokenizer and elastic routing, and protocol-only paths remain.

## `python/sglang/srt/managers/scheduler.py`

**Covered symbols:** `configure_scheduler_process`, `run_scheduler_process`,
and `dispatch_event_loop`.

The subprocess publishes its scheduler-role configuration before constructing
`Scheduler`, assigns a rank-aware process title and logging prefix, optionally
binds CPU/NUMA affinity, sends initialization data to its parent, and enters a
mode-specific event loop
([lines 5080-5142](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L5080-L5142),
[lines 5145-5212](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L5145-L5212)).

`dispatch_event_loop` makes the execution-mode branch explicit: ordinary,
overlap, MLX overlap, pipeline, prefill-disaggregated, and decode-disaggregated
loops are distinct
([lines 5050-5077](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/scheduler.py#L5050-L5077)).

**Failure mode.** An exception is reported with a traceback and propagated to
the parent failure path; a clean loop blocks until `ShutdownReq` requests
graceful exit.

**Remaining work.** Queue admission, batch construction, prefix-cache matching,
memory pressure/retraction, model-worker calls, overlap semantics, output
processing, and every advanced scheduling mode remain.

## `python/sglang/srt/managers/detokenizer_manager.py`

**Covered symbol:** `run_detokenizer_process` and its startup role.

The process arranges parent-death termination, assigns its process title,
publishes the detokenizer configuration role, constructs the manager, and
chooses the ordinary or multi-HTTP-worker loop. On failure it logs the full
trace, clears multi-worker socket mappings when possible, and signals the parent
with `SIGQUIT`
([lines 516-539](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/srt/managers/detokenizer_manager.py#L516-L539)).

**Remaining work.** Incremental decode state, stop-string handling, message
shapes, skip-detokenizer paths, cache limits, and multi-worker routing remain.

## End-to-end study check

Starting with `sglang serve model --model-type=auto`, name the function that:

1. preserves backend-owned CLI flags;
2. chooses the backend;
3. resolves `ServerArgs`;
4. allocates IPC addresses;
5. launches scheduler ranks;
6. exposes `/generate`;
7. tokenizes and dispatches one request; and
8. enters the scheduler event loop.

Then state which steps are replaced when the embedded Rust server is enabled
and which scheduler work remains.
