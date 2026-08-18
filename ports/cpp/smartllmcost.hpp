// SmartLLMCost measurement core — C++ port. Mirrors python smartllmcost/metrics.py.
#ifndef SMARTLLMCOST_HPP
#define SMARTLLMCOST_HPP
#include <vector>
#include <optional>
#include <algorithm>
#include <string>

namespace smartllmcost {

struct Attempt {
    double cost_usd = 0.0;
    bool success = false;
    bool timed_out = false;
    bool hit_token_cap = false;
    bool error = false;
};

struct CostResult {
    std::optional<double> cost_per_success;
    double total_cost = 0.0;
    int passed = 0;
    int attempts = 0;
};

inline std::optional<double> percentile(std::vector<double> xs, double p) {
    if (xs.empty()) return std::nullopt;
    std::sort(xs.begin(), xs.end());
    if (xs.size() == 1) return xs[0];
    double rank = (p / 100.0) * (xs.size() - 1);
    size_t lo = static_cast<size_t>(rank);
    size_t hi = std::min(lo + 1, xs.size() - 1);
    return xs[lo] + (xs[hi] - xs[lo]) * (rank - lo);
}

inline CostResult cost_per_successful_task(const std::vector<Attempt>& a) {
    CostResult r; r.attempts = static_cast<int>(a.size());
    double total = 0.0; int passed = 0;
    for (const auto& x : a) { total += x.cost_usd; if (x.success) passed++; }
    r.total_cost = total; r.passed = passed;
    if (passed > 0) r.cost_per_success = total / passed;
    return r;
}

inline std::string classify_failure(const Attempt& a) {
    if (a.success) return "success";
    if (a.timed_out || a.hit_token_cap) return "budget_exhaustion";
    if (a.error) return "harness_error";
    return "verifier_failure";
}

} // namespace smartllmcost
#endif
