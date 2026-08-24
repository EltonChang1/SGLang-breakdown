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
- Current statuses: 55 covered, 16 partial, 92 inventory-only, 8,156 pending.

Every row includes a pinned source URL and category. Covered and partial rows
link to their note. Inventory-only rows explain why line-by-line notes are not
useful. Pending rows state which future pass owns them.

## Completed in the latest run

- Added [Provider Clients and Prompt Templates](docs/05-provider-clients-and-templates.md)
  and its [file reference](docs/reference/provider-clients-and-templates.md).
  They trace executor state into OpenAI, Anthropic, LiteLLM, Vertex AI, and
  Crusoe; compare request shapes and lossy sampling conversions; and explain
  credentials, retries, token usage, streaming, selection, API speculation,
  media conversion, and failure behavior.
- Completed `openai.py`, `anthropic.py`, `litellm.py`, `vertexai.py`,
  `crusoe.py`, and `chat_template.py`. The template audit represents all 27
  records and all 16 ordered model-path matchers, including four
  explicit-only/fallback records and the automatically selected `janus-pro`
  capitalized-`User` mismatch.
- Covered 18 provider quick-start/usage examples and three manual test files.
  Added an explicit partial boundary for the 14 shared functions in
  `python/sglang/test/test_programs.py` reached by provider suites, and recorded
  the absence of focused Anthropic, LiteLLM, and Vertex AI backend tests.
- Documented non-obvious portability rules: OpenAI streaming forwards both
  token-limit fields while ordinary generation selects one; `n > 1` stores a
  list but advances the prompt with candidate zero; OpenAI selection ignores
  the common choice policy; chat speculative state and usage counters are
  unlocked backend-instance state; Anthropic removes the leading system
  message from executor history; and Vertex's role-free image path passes a
  base64 string to `Image.from_bytes` while message media is always labeled
  JPEG.
- Updated the architecture/study navigation, dependency map, glossary,
  frontend cross-links, coverage policy/counts, inventory, and affected ledger
  rows.

## Validation in the latest run

- Confirmed `.source/sglang` remained at the pinned commit with a clean worktree.
- Rebuilt and checked the 8,319-row inventory; status totals match this file.
- Validated local Markdown targets and anchors, coverage-note anchors, and 354
  pinned source links and line ranges across the affected navigation and notes.
- Ran focused AST/source checks proving the 27-record/16-matcher catalog is
  exact, the four non-matcher records are identified, all 18 covered provider
  examples match the ledger, the Janus role mismatch is source-backed, and the
  documented provider sampling/state branches are present.
- Parsed the five provider files, template registry, and three manual tests
  without writing bytecode.
- `git diff --check` passed. No model/server runtime test was attempted because
  provider suites require live credentials, network access, and changing
  external models; this run changes only study Markdown and ledger metadata.

## Next coherent study unit

Finish Phase 1 with the diffusion `generate` public surface. Start at
`python/sglang/multimodal_gen/runtime/entrypoints/cli/main.py`, `generate.py`,
`cli_types.py`, and `utils.py`; trace argument/config construction into
`DiffusionGenerator`, output persistence, distributed launch behavior, and the
focused CLI-generate tests. Keep the deeper diffusion managers, pipelines,
models, and caches assigned to Phase 7.

## Known gaps

- The frontend provider clients and concrete lightweight chat-template catalog
  are complete. The diffusion CLI and protocol-specific serving adapters are
  not yet covered.
- The shared frontend test-program file is partial outside the provider-reached
  functions, and no focused Anthropic, LiteLLM, or Vertex AI backend tests are
  present in the pinned snapshot.
- Model- and backend-specific configuration handlers, declarative override
  providers, and runtime-context derived helpers remain assigned to their
  owning subsystem passes rather than being treated as complete here.
- Request/control schemas and tokenizer/control manager files remain partial
  outside the methods exercised by the offline API; session-controller and
  weight/cache/model-worker internals retain their later subsystem passes.
- Scheduler admission/batching, radix/KV caches, model execution, model/layer
  families, kernels, distributed/advanced modes, and diffusion internals remain.
- Rust crates, gateway, router, tests, benchmarks, examples, docs, packaging,
  deployment, CI, release, security, and operations need dedicated guides.
- The current architecture trace names only the entry symbols in several large
  runtime files; their ledger status remains partial by design.
