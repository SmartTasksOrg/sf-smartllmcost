# Methodology — the apples-to-apples guarantees

1. **Same tasks/params** across every model; deviations recorded in the run manifest.
2. **Cost per task, not per token.** Each model is priced by ITS OWN native token counts
   against ITS OWN rate. Raw token counts are never compared across models (tokenizers differ).
3. **Quality-adjusted.** Headline = `$ per successful task` = total spend (incl. failed
   attempts) ÷ tasks that passed the acceptance check. No successes → reported as null
   (effectively infinite), never 0.
4. **Time measured consistently:** end-to-end latency p50/p95/p99, output tokens/sec,
   throughput at a disclosed concurrency. TTFT is captured for real when you pass --stream.
5. **Failure kinds separated:** budget_exhaustion (timeout / token cap) vs verifier_failure
   (wrong answer) vs harness_error — because they have different fixes.
6. **Pricing is versioned + timestamped.** Every report records the pricing snapshot date.
7. **Self-hosted fairness:** local models priced via an amortized $/GPU-hour (capex over
   life + power×PUE + maintenance), apportioned by the time each call used the GPU.

## Honest limits
- Token-cap vs timeout can only be told apart if the provider reports finish_reason /
  stop_reason; otherwise a wrong answer and a truncation may look alike.
- The self-hosted model is only as good as its assumptions — all are printed for audit.
- Default pricing in the repo is ILLUSTRATIVE; publish numbers only against a current snapshot.

## Dashboard
`smartllmcost dashboard *.json --max-cost 0.05 --min-success 0.9` renders a traffic-light
view: **green** within budget, **amber** over budget or low success, **red** failing/unreliable.
Runs are ranked cheapest-per-successful-task first, and per-run warnings surface on the card.
