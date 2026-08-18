"""Export: JSON (native), CSV, and Prometheus metrics text."""
from __future__ import annotations
import csv
import io
import json


def to_json(report):
    return json.dumps(report, indent=2)


def to_csv(reports):
    if isinstance(reports, dict):
        reports = [reports]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["model_id", "taskpack", "cost_per_successful_task", "cost_per_1k_successful",
                "success_rate", "p50_ms", "p95_ms", "p99_ms", "tokens_per_sec", "total_cost_usd"])
    for r in reports:
        h = r["headline"]
        lat = r["latency_ms"]
        w.writerow([r["model_id"], r["taskpack"], h["cost_per_successful_task"],
                    h["cost_per_1k_successful"], h["success_rate"], lat["p50"], lat["p95"],
                    lat["p99"], r["output_tokens_per_sec"], h["total_cost_usd"]])
    return buf.getvalue()


def to_prometheus(report):
    m = report["model_id"].replace(":", "_").replace("-", "_").replace(".", "_")
    h = report["headline"]
    lat = report["latency_ms"]
    lines = []

    def g(name, val, help_):
        if val is None:
            return
        lines.append(f"# HELP smartllmcost_{name} {help_}")
        lines.append(f"# TYPE smartllmcost_{name} gauge")
        lines.append(f'smartllmcost_{name}{{model="{report["model_id"]}"}} {val}')
    g("cost_per_successful_task_usd", h["cost_per_successful_task"], "USD per successful task")
    g("success_rate", h["success_rate"], "fraction of tasks passing")
    g("latency_p95_ms", lat["p95"], "p95 end-to-end latency (ms)")
    g("output_tokens_per_sec", report["output_tokens_per_sec"], "output tokens/sec")
    return "\n".join(lines) + "\n"
