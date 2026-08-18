# SmartLLMCost measurement core — Ruby port. Mirrors python smartllmcost/metrics.py.
module SmartLLMCost
  def self.percentile(values, p)
    xs = values.compact.sort
    return nil if xs.empty?
    return xs[0] if xs.length == 1
    rank = (p / 100.0) * (xs.length - 1)
    lo = rank.to_i
    hi = [lo + 1, xs.length - 1].min
    xs[lo] + (xs[hi] - xs[lo]) * (rank - lo)
  end

  def self.cost_per_successful_task(attempts)
    total = attempts.sum { |a| a[:cost_usd] || 0.0 }
    passed = attempts.count { |a| a[:success] }
    return { cost_per_success: nil, total_cost: total, passed: 0, attempts: attempts.length } if passed.zero?
    { cost_per_success: total / passed, total_cost: total, passed: passed,
      attempts: attempts.length, success_rate: passed.to_f / attempts.length }
  end

  def self.classify_failure(a)
    return "success" if a[:success]
    return "budget_exhaustion" if a[:timed_out] || a[:hit_token_cap]
    return "harness_error" if a[:error]
    "verifier_failure"
  end
end
