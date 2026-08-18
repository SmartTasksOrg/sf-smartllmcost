// SmartLLMCost measurement core — C# port. Mirrors python smartllmcost/metrics.py.
using System;
using System.Collections.Generic;
using System.Linq;

namespace SmartLLMCost {
    public record Attempt(double CostUsd, bool Success, bool TimedOut = false, bool HitTokenCap = false, bool Error = false);
    public record CostResult(double? CostPerSuccess, double TotalCost, int Passed, int Attempts);

    public static class Metrics {
        public static double? Percentile(IEnumerable<double> values, double p) {
            var xs = values.OrderBy(x => x).ToList();
            if (xs.Count == 0) return null;
            if (xs.Count == 1) return xs[0];
            double rank = (p / 100.0) * (xs.Count - 1);
            int lo = (int)rank, hi = Math.Min(lo + 1, xs.Count - 1);
            return xs[lo] + (xs[hi] - xs[lo]) * (rank - lo);
        }
        public static CostResult CostPerSuccessfulTask(IReadOnlyList<Attempt> a) {
            double total = a.Sum(x => x.CostUsd);
            int passed = a.Count(x => x.Success);
            return new CostResult(passed > 0 ? total / passed : (double?)null, total, passed, a.Count);
        }
        public static string ClassifyFailure(Attempt a) =>
            a.Success ? "success" :
            (a.TimedOut || a.HitTokenCap) ? "budget_exhaustion" :
            a.Error ? "harness_error" : "verifier_failure";
    }
}
