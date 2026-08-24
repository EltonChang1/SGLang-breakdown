# SGLang Breakdown

The guide aims to explain every meaningful part of SGLang: architecture, runtime flows,
packages, source files, key symbols, configuration, APIs, tests, build tooling,
deployment, and examples.

## How to study this repository

1. Start with [`docs/00-study-path.md`](docs/00-study-path.md).
2. Read the numbered architecture and subsystem guides in order.
3. Use [`docs/reference/`](docs/reference/README.md) for file-by-file and
   symbol-level explanations.
4. Check [`PROGRESS.md`](PROGRESS.md) and the
   [coverage inventory](docs/coverage/README.md) before assuming a file is
   complete.

Generated, vendored, binary, cache, and build-output files are inventoried and
labeled, but are not expanded line by line.

## Available now

- [Architecture overview](docs/01-architecture-overview.md)
- [Configuration and startup](docs/02-configuration-and-startup.md)
- [Offline Engine API](docs/03-offline-engine.md)
- [Frontend Language Execution](docs/04-frontend-language.md)
- [Provider Clients and Prompt Templates](docs/05-provider-clients-and-templates.md)
- [Diffusion Generate CLI](docs/06-diffusion-generate-cli.md)
- [Native `/generate` Protocol](docs/07-native-generate-protocol.md)
- [OpenAI Completions and Chat Completions](docs/08-openai-completions.md)
- [Serving entry-point reference](docs/reference/entrypoints.md)
- [Configuration/startup file reference](docs/reference/configuration-startup.md)
- [Offline Engine file reference](docs/reference/offline-engine.md)
- [Frontend language file reference](docs/reference/frontend-language.md)
- [Provider client and template file reference](docs/reference/provider-clients-and-templates.md)
- [Diffusion generate CLI file reference](docs/reference/diffusion-generate-cli.md)
- [Native `/generate` file reference](docs/reference/native-generate-protocol.md)
- [OpenAI completions file reference](docs/reference/openai-completions.md)
- [Dependency map](docs/90-dependency-map.md)
- [Glossary](docs/99-glossary.md)
- [All 8,319 tracked paths in the coverage ledger](docs/coverage/inventory.csv)
