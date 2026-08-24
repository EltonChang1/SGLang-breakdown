# Coverage Progress

## Source snapshot

- Repository: `EltonChang1/sglang`
- Analyzed commit: `f464e77d17a3908ad0ea32547b1e8b039bcbd354`
- Last completed run: 2026-08-24

## Completion rules

- Every tracked source file must appear in the coverage inventory.
- Every meaningful package or subsystem needs a conceptual overview.
- Important classes, functions, configuration objects, protocols, and entry
  points need source-linked explanations.
- Cross-module runtime flows need ordered traces.
- Tests, examples, build tooling, CI, packaging, and deployment need dedicated
  notes.
- Generated, vendored, binary, cache, and build artifacts must be labeled with
  a reason when detailed explanation is skipped.
- The final study path must order the material from prerequisites through
  internals and advanced topics.

## Current work

- [x] Inventory all 8,319 tracked paths and record the source commit.
- [x] Create the initial architecture map and ordered study sequence.
- [ ] Work through each subsystem and file in the recorded order.
- [ ] Audit coverage and resolve missing or shallow areas.

## Coverage ledger

- Inventory: [`docs/coverage/inventory.csv`](docs/coverage/inventory.csv)
- Policy and counts: [`docs/coverage/README.md`](docs/coverage/README.md)
- Generator: [`scripts/build_coverage_inventory.py`](scripts/build_coverage_inventory.py)
- Current statuses: 94 covered, 28 partial, 92 inventory-only, 8,105 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added [Native `/generate` Protocol](docs/07-native-generate-protocol.md) and
  its [file reference](docs/reference/native-generate-protocol.md). They trace
  `GenerateReqInput` normalization through sampling preparation,
  tokenization/media processing, scheduler admission, token-ID output,
  incremental detokenization, request-ID correlation, JSON/SSE shaping, and
  cancellation.
- Completed the request-header mapper, SRT `SamplingParams`, scheduler output
  sender/streamer, and detokenizer files. Expanded explicit partial boundaries
  for native HTTP, generation schemas, tokenizer manager, scheduler admission,
  and `Req` state without claiming their unrelated management, cache, parser,
  or execution responsibilities.
- Documented request/result cardinality for batch and `n > 1`, cumulative
  versus incremental streaming ownership, trusted-header precedence,
  multimodal post-expansion length checks, prefix-matched explicit abort, and
  the difference between dispatch success and abort acknowledgement.
- Recorded two source-visible edge cases: prompt validation permits exactly
  two of text/token IDs/embeddings and can mix text-derived cardinality with
  token-ID execution despite its one-input error message; and
  parallel sampling's normalized parent IDs do not have a clear one-to-one
  relationship with generated choice IDs for state cleanup and HTTP abort.
- Covered nine focused test files and partial slices of four mixed-purpose
  suites. Recorded missing native HTTP coverage for both streaming modes,
  in-band stream errors, actual client-close cancellation, and combined batch
  plus parallel sampling.
- Updated architecture/study navigation, dependency map, glossary, reference
  indexes, coverage policy/counts, inventory, and ledger rows for the first
  Phase 3 protocol subunit.

## Validation in the latest run

- Confirmed `.source/sglang` remained at the pinned commit with a clean worktree.
- Rebuilt and checked the 8,319-row inventory; status totals match this file.
- Checked 110 Markdown local links, all 122 ledger note targets, and 823 pinned
  source links, including local anchors, tracked source paths, and source line
  ranges.
- Parsed 23 native-guide Python files and structurally checked five complete
  runtime-file catalogs, native POST/PUT and abort routes, six transport
  schemas, tokenizer/scheduler boundary methods, prompt-selection and
  parallel-sampling/abort edge conditions, and focused-test assertion caveats.
- Attempted five focused CPU/unit test files with the source package on
  `PYTHONPATH`, but collection stopped before any test ran because the available
  Python environment lacks `orjson` and `msgspec`.
- No GPU/model end-to-end suite was attempted because those tests require
  accelerator resources and model downloads; this run changes only study
  Markdown and ledger metadata.

## Next coherent study unit

Continue Phase 3 with the OpenAI completions and chat-completions adapters.
Trace their schemas, validation, chat-template/tool-parser preparation, usage
and logprob conversion, streaming chunks, error/status compatibility, and
convergence on `GenerateReqInput`. Then cover embeddings/scoring before the
Anthropic, Ollama, gRPC, grammar/tool, and session protocol subunits.

## Known gaps

- Phase 1 public surfaces and the native `/generate` Phase 3 subunit are
  complete. OpenAI and other protocol adapters remain the next gap.
- The shared frontend test-program file is partial outside the provider-reached
  functions, and no focused Anthropic, LiteLLM, or Vertex AI backend tests are
  present in the pinned snapshot.
- Model- and backend-specific configuration handlers, declarative override
  providers, and runtime-context derived helpers remain assigned to their
  owning subsystem passes rather than being treated as complete here.
- Request/control schemas and tokenizer/control manager files remain partial
  outside the native/offline paths now explained; parser caches observability
  multi-tokenizer elastic session-controller weight/cache and model-worker
  internals retain their later subsystem passes.
- Diffusion CLI, launch, client, and output helpers are complete; sampling
  details, request/worker files outside the public slices, managers,
  disaggregation protocols, pipelines, models, caches, and kernels remain for
  Phase 7.
- Native scheduler admission and output boundaries are explained; batching
  policy, radix/KV caches, model execution, model/layer families, kernels, and
  distributed/advanced SRT modes remain.
- Rust crates, gateway, router, tests, benchmarks, examples, docs, packaging,
  deployment, CI, release, security, and operations need dedicated guides.
- The current architecture trace names only the entry symbols in several large
  runtime files; their ledger status remains partial by design.
