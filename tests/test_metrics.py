from sf_smartllmcost.metrics import (percentile, latency_summary, cost_per_successful_task,
                                throughput, tokens_per_sec, failure_breakdown, classify_failure)


def test_percentile_interpolates():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([10], 99) == 10
    assert percentile([], 50) is None


def test_cost_per_successful_task_counts_failed_spend():
    a = [{"cost_usd": 0.10, "success": True}, {"cost_usd": 0.05, "success": False},
         {"cost_usd": 0.10, "success": True}]
    r = cost_per_successful_task(a)
    assert r["cost_per_success"] == 0.125          # 0.25 total / 2 passed
    assert r["success_rate"] == round(2 / 3, 4)


def test_no_success_is_not_zero_cost():
    r = cost_per_successful_task([{"cost_usd": 0.2, "success": False}])
    assert r["cost_per_success"] is None and r["total_cost"] == 0.2


def test_failure_classification():
    assert classify_failure({"timed_out": True}) == "budget_exhaustion"
    assert classify_failure({"hit_token_cap": True}) == "budget_exhaustion"
    assert classify_failure({"error": "boom"}) == "harness_error"
    assert classify_failure({"success": False}) == "verifier_failure"
    b = failure_breakdown([{"success": True}, {"timed_out": True}, {"success": False}])
    assert b["success"] == 1 and b["budget_exhaustion"] == 1 and b["verifier_failure"] == 1


def test_throughput_and_tps():
    assert throughput(10, 5) == 2.0
    assert tokens_per_sec(100, 2) == 50.0
    assert tokens_per_sec(100, 0) is None
