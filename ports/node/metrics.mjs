// SmartLLMCost measurement core — Node port. Mirrors python smartllmcost/metrics.py exactly.
export function percentile(values, p) {
  const xs = values.filter(v => v != null).sort((a, b) => a - b);
  if (!xs.length) return null;
  if (xs.length === 1) return xs[0];
  const rank = (p / 100) * (xs.length - 1);
  const lo = Math.floor(rank), hi = Math.min(lo + 1, xs.length - 1);
  return xs[lo] + (xs[hi] - xs[lo]) * (rank - lo);
}
export function costPerSuccessfulTask(attempts) {
  const total = attempts.reduce((s, a) => s + (a.cost_usd || 0), 0);
  const passed = attempts.filter(a => a.success).length;
  if (passed === 0) return { cost_per_success: null, total_cost: +total.toFixed(6), passed: 0, attempts: attempts.length };
  return { cost_per_success: +(total / passed).toFixed(6),
           cost_per_1k_success: +(1000 * total / passed).toFixed(4),
           total_cost: +total.toFixed(6), passed, attempts: attempts.length,
           success_rate: +(passed / attempts.length).toFixed(4) };
}
export function classifyFailure(a) {
  if (a.success) return "success";
  if (a.timed_out || a.hit_token_cap) return "budget_exhaustion";
  if (a.error) return "harness_error";
  return "verifier_failure";
}
