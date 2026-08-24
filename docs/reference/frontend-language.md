# Frontend Language: File and Symbol Reference

This reference maps the public SGL language, its IR and interpreter, tracing,
choice scoring, and the SRT HTTP backend to the pinned source. Read
[Frontend Language Execution](../04-frontend-language.md) first. The provider
clients (`openai.py`, `anthropic.py`, `litellm.py`, `vertexai.py`, and
`crusoe.py`) remain a separate pass so their vendor contracts can be compared
without blurring the common interpreter boundary.

## `python/sglang/lang/api.py`

**Status: covered.** This file is the public factory layer; it creates IR nodes,
sets process-wide frontend state, or lazily constructs a heavier runtime. It
does not execute a model itself
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/api.py#L1-L292)).

### Decorator and backend helpers

`function` supports both `@sgl.function` and
`@sgl.function(num_api_spec_tokens=...)`, returning `SglFunction` in either
form. `Runtime` and `Engine` delay their imports until construction; this keeps
ordinary frontend client import from eagerly requiring their server-side
dependencies
([lines 23-47](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/api.py#L23-L47)).

`set_default_backend` mutates the singleton `global_config`. `flush_cache` and
`get_server_info` choose an explicit or default backend, unwrap a local
`Runtime` to its `.endpoint`, and delegate. Their absent-backend sentinels are
different: cache flush returns `False`, while server info returns `None`
([lines 49-72](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/api.py#L49-L72)).

### Generation, selection, roles, and media

`gen` switches completely to `SglSelect` when `choices` is truthy. In that
branch it retains the name, choices, temperature, and decision method; ordinary
generation controls such as stops, regex, and token limits do not participate.
Without choices it validates Python regex syntax and constructs `SglGen`
([lines 75-139](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/api.py#L75-L139)).
An empty choice list is therefore treated as ordinary generation rather than a
selection request.

`gen_int` and `gen_string` are constrained-generation conveniences. They build
`SglGen` with `dtype=int` or `str`; they intentionally expose a smaller
signature than `gen`
([lines 142-225](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/api.py#L142-L225)).
`image` and `video` wrap a path for deferred client-side encoding. `select`
requires a non-`None` list but does not reject an empty list or nonzero
temperature; concrete backends own those checks
([lines 228-243](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/api.py#L228-L243)).

The role helpers either return begin/end nodes around an expression or expose
individual markers. `separate_reasoning` returns `[expr, marker]`, so execution
first generates or selects and then post-processes the named value. Passing no
expression leaves `None` in that list and cannot be interpreted successfully
([lines 246-292](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/api.py#L246-L292)).

## `python/sglang/lang/global_config.py`

**Status: covered.** `GlobalConfig` is one mutable process-wide record
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/global_config.py#L1-L27)).

| Field | Consumer | Meaning |
| --- | --- | --- |
| `verbosity` | `run_internal` | print final program text at level 2 or higher |
| `default_backend` | `SglFunction` and API helpers | fallback backend for calls without an explicit one |
| output special-token flags | `RuntimeEndpoint.generate*` | controls forwarded to SRT sampling parameters |
| `enable_precache_with_tracing` | `run_program_batch` | trace/cache a common prefix for batches larger than one |
| `enable_parallel_encoding` | `StreamExecutor` | permit backend KV concatenate/append when capability agrees |

There is no lock, context-local override, or reset helper. These settings are
best treated as application startup configuration rather than per-request
options.

## `python/sglang/lang/ir.py`

**Status: covered.** The file defines sampling records, decorated program
wrappers, and every expression type interpreted or traced by the frontend
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L1-L643)).

### Sampling record and conversions

`REGEX_INT`, `REGEX_FLOAT`, `REGEX_BOOL`, and `REGEX_STR` are built-in patterns
used by `RuntimeEndpoint` for dtype generation. The string pattern is
deliberately restricted because the underlying `interegular` path has trouble
with a greedy quoted-string pattern
([lines 11-14](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L11-L14)).

`SglSamplingParams` contains common sampling, stopping, logprob, JSON-schema,
dtype, and regex controls. `to_srt_kwargs` preserves the SRT-supported sampling
and constraint fields; provider conversions rename or omit unsupported values
and warn about regex
([record and mappings](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L17-L138)).
`clone()` constructs positionally and stops after `json_schema`; `dtype` and
`regex` reset to `None`. This is a lossy helper in the pinned snapshot.

### `SglFunction`

Construction enforces a first positional parameter named `s`, records later
positional arguments/defaults, and stores bindings and optional API
speculation size
([lines 141-153](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L141-L153)).
Keyword-only parameters can still reach the wrapped Python function through
call keywords or batch dictionaries, but they are absent from `arg_names` and
therefore cannot be accepted by `bind` or positional batch normalization.
`bind` validates names and returns a new wrapper, but does not forward
`num_api_spec_tokens`
([lines 154-158](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L154-L158)).

`run` normalizes mutable stop defaults, builds call-level sampling defaults,
chooses a backend, and calls `run_program`. `run_batch` accepts dictionaries or
positional sequences, validates arity for the latter, constructs the same
default record, and delegates to batch execution
([single run](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L160-L221),
[batch run](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L223-L302)).
Positional batch arity is calculated from the original signature and does not
subtract bound arguments; use batch dictionaries when bindings should supply
otherwise-required parameters.
`trace` and `cache` load tracer/interpreter paths lazily. `__call__` selects
ordinary execution unless a `TracingScope` is active
([lines 304-324](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L304-L324)).
The tracing branch forwards `*args` into keyword-only `trace`; nested decorated
calls under tracing must therefore pass program arguments by keyword.

### Expression hierarchy

`SglExpr` assigns a process-global monotonically increasing node ID, supports
string/expression concatenation, and renders dependency-first trace graphs
([lines 327-394](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L327-L394)).
The counter is not synchronized, and IDs are diagnostic rather than request
identities.

`SglExprList` preserves flattenable execution order. `SglArgument` represents
a symbolic tracing input and proxies limited length/index/conversion behavior;
f-string formatting is rejected because it would collapse symbolic structure
([lines 397-431](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L397-L431)).
`SglImage` and `SglVideo` store media inputs but do not call `SglExpr.__init__`,
so they do not receive a node ID, although tracing can add `pid` and
`prev_node` dynamically. Ordinary interpretation uses their type and fields,
while generic graph printing should not assume complete node metadata
([lines 434-448](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L434-L448)).

`SglGen` packages per-expression overrides. Text and role nodes carry literal
content or delimiters; `SglSelect` carries choices and a callable decision
policy
([lines 451-549](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L451-L549)).
Fork/get-item and variable nodes exist mainly for traced dependency graphs;
runtime forking is performed directly by `ProgramState`
([lines 552-581](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L552-L581)).
Scope, concatenate, and commit nodes control interpreter state or backend
optimization. `SglSeparateReasoning` recursively discovers named generation or
selection nodes and derives the reasoning variable name, rejecting an unnamed
leaf. The one `name` attribute is overwritten for every discovered leaf, so an
expression list retains only the final reasoning-event name
([lines 584-643](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/ir.py#L584-L643)).

## `python/sglang/lang/interpreter.py`

**Status: covered.** This is the execution engine for SGL programs: it owns
single/batch launch, queue/stream coordination, prompt and variable state,
expression dispatch, fork/join, and backend calls
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L1-L1098)).

### Program launch and batch orchestration

`run_internal` calls the original function, always ends the stream executor,
optionally synchronizes, and prints at high verbosity. It does not inspect the
worker's stored error after synchronization
([lines 42-55](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L42-L55)).
`run_program` unwraps local `Runtime`, requires a backend, applies bindings,
creates executor/state, and runs inline or starts the program thread for
streaming
([lines 57-90](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L57-L90)).
Ordinary `.run()` leaves `sync=False`, so its default worker may finish after
the state is returned; state accessors and variable reads provide the join.
Batch calls pass `sync=True`, and `use_thread=False` evaluates submissions
inline.

`run_program_batch` optionally traces a common prefix, selects a thread count,
and returns independent states in input order. The non-generator pool submits
all calls at once. `_run_program_batch_generator` limits submissions to chunks
of 200, but iterates each chunk's future list in input order
([lines 93-239](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L93-L239)).
`cache_program` caches only a traced prefix longer than 64 characters
([lines 242-247](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L242-L247)).
`_merge_stream_meta_info` concatenates only the three incremental output
logprob arrays; all other keys use the newest metadata object
([lines 250-271](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L250-L271)).

### `StreamExecutor`

The constructor establishes client state and optionally starts a worker under
a copied `contextvars` context. It gets the chat template from the backend
unless a fork supplies one explicitly
([lines 274-340](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L274-L340)).
`submit` initializes variable/streaming events before queueing or synchronous
execution. Accessors synchronize through queue completion or variable events;
metadata supports a timeout
([lines 342-368](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L342-L368)).

`fork` commits lazy work for a multi-branch nonempty prompt, synchronizes, then
copies selected state into child executors. It does not call the declared
`BaseBackend.fork_program` hook and does not apply `position_ids_offset`
([lines 370-402](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L370-L402)).
`end` queues a sentinel when the worker is alive and calls
`backend.end_program`; destructor paths can repeat this call
([lines 404-420](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L404-L420)).

The worker serially executes expressions. On failure it warns, drains queued
tasks, releases all known variable and stream events, stores the exception,
and marks the executor finished
([lines 422-459](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L422-L459)).
Because it stores rather than re-raises, a program that never reads the failed
result can return a state whose `error()` must be checked.

`_execute` is the exhaustive runtime type dispatcher. Concatenate/append uses
the KV-capable path only when both global policy and backend capability allow
it
([lines 461-503](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L461-L503)).
Fill maintains speculative text matching before appending. Media execution
encodes files and appends the template token
([lines 505-541](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L505-L541)).

`_spec_gen` reuses a longer speculative completion for completion-style
backends. `_execute_gen` selects normal, API-speculative, or streaming backend
calls; publishes completion and metadata; and signals readiness
([lines 543-645](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L543-L645)).
The speculative chat branch relies on `is_chat_model`, `spec_fill`, and
`role_end_generate`, which are not part of `BaseBackend`.

Selection publishes a `ChoicesDecision`; variables wait on a source executor;
role begin/end enforce non-nesting, apply template strings, and build message
history
([lines 647-717](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L647-L717)).
Variable scopes capture a prompt substring. Concatenate/append either copies
branch suffix text or commits child requests before a backend KV operation
([lines 719-752](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L719-L752)).
Reasoning separation is non-streaming only and imports the SRT parser lazily
([lines 754-786](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L754-L786)).
`_resolve_sampling_params` performs deep-copy overlay plus template stop
extension; `_init_var_event` recursively prepares synchronization nodes
([lines 788-849](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L788-L849)).

### `ProgramState` and `ProgramStateGroup`

`ProgramState` exposes role and variable-scope context managers, fork/copy,
text/message/error access, synchronous and asynchronous delta iterators,
variable and metadata access, and the `+=`/index syntax
([lines 852-1042](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L852-L1042)).
The role/scope context managers enqueue their end marker only when the context
continues to normal exit. Variable streaming waits for the variable's event to
be registered; a worker failure before value creation can release the event
without creating a readable value.

`ProgramStateGroup.join("gather_variable")` collects child-only variables as
lists; `join("concate_and_append")` asks the parent executor to append branch
suffixes. Both modes end every child. Group `+=` broadcasts one expression,
maps a callable by child index, or applies a same-length list
([lines 1045-1098](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/interpreter.py#L1045-L1098)).

## `python/sglang/lang/choices.py`

**Status: covered.** The file defines the choice-policy protocol, immutable
decision shape, and all three built-in methods
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/choices.py#L1-L164)).

`ChoicesSamplingMethod` declares the required logprob inputs and a capability
property for unconditional scores. `TokenLengthNormalized` chooses the maximum
backend-computed normalized prompt logprob and preserves diagnostic arrays in
metadata
([lines 8-53](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/choices.py#L8-L53)).

`GreedyTokenSelection` builds a candidate-by-token matrix, padding shorter
options with their own mean logprob, then filters tied survivors column by
column. A full tie resolves to the earliest choice
([lines 56-107](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/choices.py#L56-L107)).
It assumes every candidate has at least one input token; an empty sequence
produces undefined mean/padding behavior.

`UnconditionalLikelihoodNormalized` advertises its extra request, validates
the supplied arrays, substitutes zero for the expected missing first
unconditional logprob, and maximizes mean conditional-minus-unconditional
logprob
([lines 110-164](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/choices.py#L110-L164)).
`zip` truncates mismatched outer arrays rather than diagnosing them, so the
backend is responsible for maintaining choice/logprob alignment.

## `python/sglang/lang/tracer.py`

**Status: covered.** This file symbolically executes SGL programs for graph
inspection and common-prefix extraction
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/tracer.py#L1-L279)).

`extract_prefix_by_tracing` creates dummy arguments, overlays bindings, traces
until a `StopTracing` or selected Python error, and concatenates leading
constant nodes only
([lines 25-51](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/tracer.py#L25-L51)).
Its exception handling intentionally favors a conservative cache prefix over a
failed batch, but can also hide a programming error during this optimization.
`trace_program` fills missing arguments symbolically, uses a dummy base backend
when needed, and returns the trace state
([lines 54-72](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/tracer.py#L54-L72)).

`TracerProgramState` records a trace ID, nodes, symbolic variables, chat state,
and child traces. Forking builds explicit `SglFork`/`SglGetForkItem`
dependencies; prefix-only tracing stops at a fork
([construction and fork](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/tracer.py#L75-L133)).
Its dispatcher mimics constant, generation, selection, role, and scope
semantics without backend calls. A generation/selection creates a symbolic
`SglVariable`; `get_var` returns a bound/dummy argument or a new reference to a
generated source
([lines 139-239](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/tracer.py#L139-L239)).
`flatten_nodes` preserves recorded order while flattening expression lists
([lines 240-251](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/tracer.py#L240-L251)).

`TracingScope` is a manually restored class-global scope stack. Child trace
states register with every enclosing scope, enabling nested decorated calls,
but the scope is not thread-local
([lines 257-279](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/tracer.py#L257-L279)).

## `python/sglang/lang/chat_template.py`

**Status: covered.** The core record, selection algorithm, role semantics, and
relationship to frontend execution are summarized here. The complete audit of
all 27 records and 16 model-path matchers is in the
[provider/template file reference](provider-clients-and-templates.md#pythonsglanglangchat_templatepy).

`ChatTemplate` stores default system text, role prefix/suffix pairs, stop
strings, media tokens, and a style. `get_prefix_and_suffix` handles the special
Llama 2 system/user interaction; `get_prompt` renders message history in order
([lines 7-54](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L7-L54)).
The interpreter uses this same operation incrementally, so template history
and active-role state must stay aligned.

Template and matcher registries are import-time mutable collections. Lookup by
model path returns the first matcher result and otherwise the `default`
template
([lines 57-78](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L57-L78)).
Order is therefore part of matching precedence. Concrete records occupy
[lines 81-537](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L81-L537),
and model-path matchers occupy
[lines 540-665](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/chat_template.py#L540-L665).
The catalog identifies four automatic-selection gaps and the `janus-pro`
capitalized-`User` mismatch with the interpreter's lowercase role.

## `python/sglang/lang/backend/base_backend.py`

**Status: covered.** `BaseBackend` is the nominal adapter floor for the
frontend interpreter
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/base_backend.py#L1-L82)).

Construction disables KV concatenate/append and installs the default chat
template. Model-name lookup, `generate`, `generate_stream`, `select`, and
`concatenate_and_append` raise when absent. Chat template lookup returns the
stored template. Cache/request/program/fork/media/shutdown/flush/info methods
are permissive no-ops
([lines 9-82](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/base_backend.py#L9-L82)).

The nominal interface and the observed interpreter protocol differ:

- ordinary programs require generation or streaming plus template lookup;
- selections require `select`;
- optimized concatenate/join requires both capability flag and method;
- API speculative chat execution also expects `is_chat_model`, `spec_fill`,
  and `role_end_generate`, none declared here; and
- `begin_program`, `fork_program`, `fill_image`, `end_request`, and
  `uncache_prefix` have no caller in the interpreter/tracer snapshot.

New backends should implement the observed feature set explicitly and make
cleanup idempotent, because end hooks can be reached from normal and destructor
paths.

## `python/sglang/lang/backend/runtime_endpoint.py`

**Status: covered.** The file contains the SRT HTTP implementation of the
frontend backend and the legacy local HTTP-server wrapper
([entire file](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L1-L555)).

### `RuntimeEndpoint`

Construction enables concatenate/append, stores connection options, requires
a successful `/get_model_info`, and selects an explicit or model-path-matched
chat template
([lines 26-55](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L26-L55)).
It does not define the speculative-chat attributes missing from `BaseBackend`,
so `num_api_spec_tokens` is not a supported endpoint capability in this
snapshot.
Model name, cache flush, server info, template lookup, prefix cache, and profile
controls map directly to HTTP endpoints. Prefix cache, lazy commit, and image
fill use `/generate` with zero new tokens
([lines 56-125](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L56-L125)).

`_handle_dtype_to_regex` mutates the execution-local sampling record, converts
four supported dtypes, adds numeric stops, and lets dtype override regex
([lines 127-157](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L127-L157)).
It converts only the empty tuple to a list before calling `.extend`; a caller
that directly supplies a nonempty stop tuple with numeric dtype violates this
implicit mutability expectation.

`generate` sends prompt text, SRT sampling values, output-token flags, optional
top-level logprob controls, and one optional media payload; it returns response
text and metadata
([lines 159-196](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L159-L196)).
`generate_stream` sends the same data with `stream=True`, parses `data:` lines,
stops at `[DONE]`, and converts cumulative response text to deltas by character
position
([lines 198-246](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L198-L246)).

`select` requires near-zero temperature. It primes the prefix, derives a
token-healing logprob start, scores all completed choices as one batch, removes
an unchanged healed token, optionally scores the choice tokens without
context, then invokes the decision policy
([lines 248-315](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L248-L315)).
`compute_normalized_prompt_logprobs` averages truthy logprobs, excluding both
`None` and exact zero; an empty remainder divides by zero
([lines 351-353](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L351-L353)).

`concatenate_and_append` maps executor IDs to the dedicated management
endpoint. Request generation in this class does not itself send `StreamExecutor.sid`
as an explicit request ID, and the interpreter does not call the base
begin/fork hooks; optimized join behavior should be integration-tested rather
than inferred only from the capability flag
([lines 317-335](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L317-L335)).
`_add_images` enforces one accumulated item. `_assert_success` accepts exactly
status 200 and raises JSON or text error content
([lines 337-348](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L337-L348)).

### `Runtime`

`Runtime` is an owning wrapper around a spawned SRT HTTP server. It lazily
imports SRT, finds an available port below 40000, builds and resolves
`ServerArgs`, launches `launch_server` with multiprocessing `spawn`, registers
shutdown, and polls `/health_generate` until ready, child exit, or timeout
([lines 356-440](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L356-L440)).
The search is `range(requested_port, 40000)`: a starting port at or above 40000
leaves `port` unbound, while an all-busy nonempty range falls through with its
last busy value and leaves binding failure to server startup.

`shutdown` kills the process tree once and clears the PID. Profile and prefix
helpers delegate to the endpoint. `get_tokenizer` uses the resolved tokenizer
or model path and resolution-sensitive tokenizer settings
([lines 442-466](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L442-L466)).

`async_generate` always streams and switches between `text` and `input_ids`
according to `skip_tokenizer_init`; it yields cumulative-text deltas or decoded
non-text event objects. `add_request` is an alias
([lines 468-507](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L468-L507)).
It does not call `raise_for_status`, so non-SSE HTTP failure behavior depends on
the response body/chunk loop.

The synchronous `generate` and `encode` helpers post directly with `requests`
and return `json.dumps(response.json())`. `generate` always uses `text`, and a
list `lora_path` is checked against `len(prompt)`, which means a scalar string
is measured in characters rather than batch items
([lines 509-541](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L509-L541)).
The async server-info helper decodes success and expects an OpenAI-shaped error
message on failure. `__del__` repeats idempotent shutdown
([lines 543-555](https://github.com/EltonChang1/sglang/blob/f464e77d17a3908ad0ea32547b1e8b039bcbd354/python/sglang/lang/backend/runtime_endpoint.py#L543-L555)).

## Continue with provider clients

The concrete provider adapters and full template registry are now covered in
[Provider Clients and Prompt Templates](../05-provider-clients-and-templates.md)
and its [file reference](provider-clients-and-templates.md). Continue there for
message versus completion modes, image conversion, sampling-parameter loss,
API speculative execution, token usage, selection, streaming/errors,
credentials, examples, and tests.
