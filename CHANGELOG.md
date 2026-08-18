# Changelog
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
