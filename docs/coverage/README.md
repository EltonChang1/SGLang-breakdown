# Coverage Inventory

The inventory is the source of truth for file coverage at commit
[`f464e77d17a3908ad0ea32547b1e8b039bcbd354`](https://github.com/EltonChang1/sglang/tree/f464e77d17a3908ad0ea32547b1e8b039bcbd354).
[`inventory.csv`](inventory.csv) contains one row for every path returned by
`git -C .source/sglang ls-files`, including a pinned source URL, classification,
coverage status, note link when available, and a reason.

## Current ledger

The initial inventory contains 8,319 unique tracked paths:

| Category | Paths |
| --- | ---: |
| Source | 3,547 |
| Test or benchmark | 2,916 |
| Configuration | 868 |
| Documentation | 566 |
| Example | 147 |
| CI | 111 |
| Build or packaging | 72 |
| Binary | 67 |
| Vendored | 19 |
| Asset | 4 |
| Generated | 2 |

After the native gRPC Python bridge pass, 165 paths are `covered`, 41 are
`partial`, 92 are justified `inventory-only`, and 8,021 remain `pending`.
Small CLI, config-merging, argument-metadata, in-tree platform, offline-engine
adapter, scoring, frontend IR/interpreter, tracing, choice-policy, SRT frontend
HTTP adapter, provider backend/template/example, diffusion generate/launch/
client, output-helper, native sampling, request-header, output-streaming,
detokenization, OpenAI adapter base/completion/usage/logprob/SSE helpers,
embedding capability records, embedding/classify/score/rerank/token adapters,
pooling and embedding-override helpers, user-facing OpenAI material, and
Responses/Harmony state and streaming adapters, native Exa/MCP tool boundaries,
and their focused test files, plus Anthropic Messages records/conversion/SSE/
token counting, its user guide, focused unit test, live test mixin, tool suite,
and manual VLM suite, plus the complete Ollama package, direct adapter, public
tutorial, synthetic model metadata, and client-side Smart Router have complete
references. The shared native gRPC runtime protobuf, complete Python
`RuntimeHandle`, and its focused multi-choice unit test are also covered; the
Python-facing Rust extension, callback/channel, Tonic handler, and request-map
slices are partial pending a full crate pass. Large shared schema,
model-configuration, tokenizer, scheduler, result-processing, control, policy,
worker, pipeline-request, chat, runtime, native-API documentation, and
mixed-purpose test files remain partial; a link to one symbol must not be
mistaken for complete file coverage.

## Status meanings

- `pending`: classified and linked to pinned source, but still awaiting the
  appropriate study pass.
- `partial`: a linked note explains named responsibilities or symbols, while
  the row's reason states what remains.
- `covered`: a linked note explains all meaningful contents at a level
  proportionate to the file.
- `inventory-only`: detailed notes are unnecessary; the row includes a concise
  reason. This is used initially for generated, vendored, binary, and static
  asset material, not as a shortcut for difficult source.

## Classification policy

Classification is path-based and deliberately separates tests/benchmarks,
examples, documentation, CI, build/package inputs, and configuration from
runtime source. Generated and vendored paths take precedence over language;
binary fixtures take precedence over their containing test or documentation
directory. This makes the disposition explicit instead of pretending that a
PNG, font, generated binding, or upstream snapshot benefits from line-by-line
explanation.

The generated ledger is committed so readers can inspect it without running a
script. Human decisions live in [`overrides.csv`](overrides.csv). Rebuild or
validate it with:

```bash
python3 scripts/build_coverage_inventory.py
python3 scripts/build_coverage_inventory.py --check
```

The generator refuses to run if `.source/sglang` is not at the pinned commit,
rejects override paths absent from that snapshot, and rejects unknown statuses.

## Audit rules

A subsystem is not complete merely because every row has left `pending`.
Before final completion, audit for:

- conceptual guides for every meaningful subsystem;
- important public and internal symbols that lack explanation;
- cross-module flows that stop at a file boundary;
- files marked `covered` by a shallow directory summary;
- unjustified `inventory-only` source or test rows;
- broken navigation, note anchors, or unpinned source links; and
- inconsistent terminology between guides and reference notes.
