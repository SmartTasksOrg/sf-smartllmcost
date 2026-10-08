"""Measurement core — the apples-to-apples math.

Pure functions, no I/O, so they're identical across ports and fully testable. Everything
the spec promises lives here: latency percentiles, throughput, token accounting, and the
headline QUALITY-ADJUSTED metric: dollars per SUCCESSFUL task (counting failed attempts).
"""
from __future__ import annotations


def percentile(values, p):
    """Linear-interpolation percentile (p in 0..100). Matches the ports' implementation."""
    xs = sorted(v for v in values if v is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    rank = (p / 100.0) * (len(xs) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(xs) - 1)
    frac = rank - lo
    return xs[lo] + (xs[hi] - xs[lo]) * frac


def latency_summary(latencies_ms):
    """p50/p95/p99 + min/max/mean over a list of end-to-end latencies (ms)."""
    xs = [x for x in latencies_ms if x is not None]
    if not xs:
        return {"n": 0, "p50": None, "p95": None, "p99": None, "min": None, "max": None, "mean": None}
    return {"n": len(xs),
            "p50": round(percentile(xs, 50), 2),
            "p95": round(percentile(xs, 95), 2),
            "p99": round(percentile(xs, 99), 2),
            "min": round(min(xs), 2), "max": round(max(xs), 2),
            "mean": round(sum(xs) / len(xs), 2)}


def tokens_per_sec(output_tokens, generation_seconds):
    if not generation_seconds or generation_seconds <= 0:
        return None
    return round(output_tokens / generation_seconds, 2)


def throughput(n_tasks, wall_seconds):
    """Completed tasks per second at the run's concurrency (wall-clock)."""
    if not wall_seconds or wall_seconds <= 0:
        return None
    return round(n_tasks / wall_seconds, 4)


def cost_per_successful_task(attempts):
    """THE headline metric. attempts: list of {cost_usd, success: bool}.

    Divides TOTAL spend (including failed attempts) by the number of SUCCESSFUL tasks.
    A cheap model that fails a lot is correctly shown as expensive. Returns None if no
    task succeeded (infinite cost — surfaced honestly, not as 0).
    """
    total = sum(a.get("cost_usd", 0.0) or 0.0 for a in attempts)
    passed = sum(1 for a in attempts if a.get("success"))
    if passed == 0:
        return {"cost_per_success": None, "total_cost": round(total, 6),
                "passed": 0, "attempts": len(attempts), "note": "no successes — cost is effectively infinite"}
    return {"cost_per_success": round(total / passed, 6),
            "cost_per_1k_success": round(1000 * total / passed, 4),
            "total_cost": round(total, 6), "passed": passed, "attempts": len(attempts),
            "success_rate": round(passed / len(attempts), 4)}


def classify_failure(attempt):
    """Distinguish the two failure kinds the article/spec insist on separating:
    budget-exhaustion (timeout / token-cap) vs verifier-failure (wrong answer)."""
    if attempt.get("success"):
        return "success"
    if attempt.get("timed_out") or attempt.get("hit_token_cap"):
        return "budget_exhaustion"
    if attempt.get("error"):
        return "harness_error"
    return "verifier_failure"


def failure_breakdown(attempts):
    out = {"success": 0, "budget_exhaustion": 0, "verifier_failure": 0, "harness_error": 0}
    for a in attempts:
        out[classify_failure(a)] += 1
    return out
