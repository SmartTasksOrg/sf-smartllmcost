# Integrations
- **github-action/** — gate PRs on cost-per-successful-task or p95 latency regression.
- **langchain/** — `smartllmcost_true_cost` tool.
- **n8n/**, **flowise/** — Function-node wrappers around the CLI.
- **Traffic-light dashboard:** `sf-smartllmcost dashboard *.json -o dashboard.html` (self-contained HTML).
- Prometheus: `sf-smartllmcost run ... --format prometheus` exposes gauges
  (`smartllmcost_cost_per_successful_task_usd`, `smartllmcost_latency_p95_ms`, …) to scrape.
