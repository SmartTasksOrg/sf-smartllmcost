# Changelog
## Unreleased

### Security
- Install instructions no longer name packages the maintainers have not
  published. Until the first release, install from a clone (README, "Install").
- New `SECURITY.md` (private vulnerability reporting), `names.json` (the only
  official package names) and a CI check that fails when a document names any
  other package.
- Releases are built and published only by `.github/workflows/release.yml`
  through PyPI trusted publishing, with provenance attestations.

### Changed
- **Renamed (breaking), `sf-` = Smart Family:** repository `SmartTasksOrg/sf-smartllmcost`, PyPI package `sf-smartllmcost`, command `sf-smartllmcost`, import package `sf_smartllmcost`, MCP server `io.github.smarttasksorg/sf-smartllmcost`. The unprefixed names are not used any more, so nobody can be sent to a look-alike.
- README: "Install" and "Status" sections.
- `pyproject.toml`: SPDX licence, `NOTICE` in the wheel, "3 - Alpha" classifier (the "License ::" classifier is replaced by the SPDX field), Source/Issues/Security/Changelog URLs.
- Example cost-gate workflow pins `actions/checkout` and `actions/setup-python` by commit.
- Go port module path `github.com/SmartTasksOrg/sf-smartllmcost/ports/go`.

## 0.1.0
- Streaming mode (--stream): real TTFT + generation-only timing via SSE (OpenAI-compat + Anthropic).
- Traffic-light HTML dashboard (`smartllmcost dashboard`): green/amber/red by cost-per-successful-task + success rate.
- Measurement core: cost-per-successful-task, latency p50/p95/p99, throughput, tokens/sec,
  failure classification (budget-exhaustion vs wrong-answer vs harness-error).
- Versioned pricing snapshots + amortized self-hosted $/GPU-hour model.
- Provider adapters: OpenAI-compatible (OpenAI/LM Studio/vLLM/Ollama/llama.cpp) + Anthropic.
- Native task-pack format + runner + transparent acceptance checks.
- Report + JSON/CSV/Prometheus export. CLI: run / compare / gpu-hour.
- Ports: Node (tested) + Go. Integrations: GitHub Action gate, langchain/n8n/flowise.
