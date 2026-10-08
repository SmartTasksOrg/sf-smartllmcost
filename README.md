# SmartLLMCost

**The live true-cost calculator for LLMs — apples-to-apples cost & performance.**

What does a model *actually* cost to do your job? SmartLLMCost runs identical task-packs across any model and reports **dollars per _successful_ task** (counting failed attempts), with consistent latency, throughput, and token accounting. Runs identical task-packs across
any model and reports the number that actually matters: **dollars per _successful_ task**,
alongside latency percentiles, throughput, and tokens/sec — reproducibly.

## Why
Per-token price doesn't predict the bill (tokenizers differ per model), latency is
reported inconsistently, and a cheap model that fails a task isn't cheap. SmartLLMCost
measures time and tokens the same way for every model and pairs cost with success.

## Quickstart
SmartLLMCost is not published on PyPI yet; a package of that name on any registry is not ours.

```bash
git clone https://github.com/SmartTasksOrg/smartllmcost
cd smartllmcost
python -m venv .venv && . .venv/bin/activate   # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install .
# run your own task-pack against a model
smartllmcost run examples/example-taskpack.json --preset openai --model gpt-4o --stream -o report.json  # --stream measures real TTFT
# self-hosted (LM Studio / vLLM / Ollama / llama.cpp)
smartllmcost run taskpack.json --preset lmstudio --model gpt-oss --host 192.168.1.10 --port 1234 \
  --self-hosted-gpu-hour 0.96 -o local.json
# check a task-pack before a long run; list providers
smartllmcost validate taskpack.json
smartllmcost presets
# compare several runs, cheapest-$/success first
smartllmcost compare report.json local.json --format table
# build a traffic-light dashboard from run reports
smartllmcost dashboard report.json local.json --max-cost 0.05 -o dashboard.html
# build a defensible $/GPU-hour for self-hosted cost
smartllmcost gpu-hour --capex 20000 --watts 700 --pue 1.5 --kwh-price 0.12
```

## What it measures
`$ per successful task` · `$ per 1k successful` · success rate · latency p50/p95/p99 ·
output tokens/sec · throughput · native input/output tokens · failure breakdown
(budget-exhaustion vs wrong-answer vs harness-error).

## Structure
- `src/smartllmcost/` — measurement core, pricing, provider adapters, harness runner, CLI.
- `ports/` — Node + Go reimplementations of the core (identical results).
- `integrations/` — an example GitHub Actions workflow (`integrations/github-action/cost-gate.example.yml`), langchain/n8n/flowise, Prometheus export.
- `examples/` — a runnable task-pack.
- Docs: `docs/METHODOLOGY.md`.

## Providers
OpenAI-compatible (OpenAI, LM Studio, vLLM, Ollama, llama.cpp) + Anthropic, via presets. Both support `--stream` for real TTFT.

## Harnesses
Native task-pack format (your own jobs) today; adapters for lm-evaluation-harness / HELM /
SWE-bench convert their tasks into the same shape so the cost/timing math is identical.

Apache-2.0.
