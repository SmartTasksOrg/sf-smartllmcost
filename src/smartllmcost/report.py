"""Assemble a run into the standardized true-cost report (schema-versioned)."""
from __future__ import annotations
import datetime

from .versioning import SCHEMA_VERSION
from .metrics import (latency_summary, tokens_per_sec, throughput,
                      cost_per_successful_task, failure_breakdown)
from .pricing import pricing_provenance


def _warnings(run, attempts):
    w = []
    um = run.get("usage_missing_count", 0)
    if um:
        w.append(f"{um}/{len(attempts)} calls returned no token usage — their cost is "
                 f"understated (counted as $0). Costs are NOT reliable for this run.")
    if all((a.get("cost_usd", 0) == 0) for a in attempts) and attempts:
        w.append("all attempts cost $0 — check pricing snapshot covers this model_id.")
    if run.get("concurrency", 1) > 1:
        w.append(f"run used concurrency={run['concurrency']}; latency reflects contention, "
                 f"not isolated per-call timing.")
    return w


def build_report(run, snapshot=None):
    attempts = run["attempts"]
    lat = latency_summary([a["latency_ms"] for a in attempts])
    ttft = latency_summary([a.get("ttft_ms") for a in attempts])
    out_tok = sum(a["output_tokens"] for a in attempts)
    gen_s = sum((a["gen_seconds"] or 0) for a in attempts)
    cps = cost_per_successful_task(attempts)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "model_id": run["model_id"],
        "taskpack": run["taskpack"], "taskpack_version": run["taskpack_version"],
        "n_tasks": run["n_tasks"],
        "headline": {
            "cost_per_successful_task": cps.get("cost_per_success"),
            "cost_per_1k_successful": cps.get("cost_per_1k_success"),
            "success_rate": cps.get("success_rate", 0.0),
            "total_cost_usd": cps.get("total_cost"),
        },
        "latency_ms": lat,
        "ttft_ms": ttft,
        "throughput_tasks_per_sec": throughput(run["n_tasks"], run["wall_seconds"]),
        "output_tokens_per_sec": tokens_per_sec(out_tok, gen_s),
        "tokens": {"output_total": out_tok,
                   "input_total": sum(a["input_tokens"] for a in attempts)},
        "failures": failure_breakdown(attempts),
        "pricing": pricing_provenance(snapshot),
        "warnings": _warnings(run, attempts),
        "wall_seconds": run["wall_seconds"],
        "attempts": attempts,
    }


def compare(reports):
    """Rank models by cost-per-successful-task (None = no successes → worst)."""
    def key(r):
        c = r["headline"]["cost_per_successful_task"]
        return (c is None, c if c is not None else 0)
    ranked = sorted(reports, key=key)
    return {"ranked": [{"model_id": r["model_id"],
                        "cost_per_successful_task": r["headline"]["cost_per_successful_task"],
                        "success_rate": r["headline"]["success_rate"],
                        "p95_latency_ms": r["latency_ms"]["p95"],
                        "tokens_per_sec": r["output_tokens_per_sec"]} for r in ranked]}
