"""Run a task-pack against an adapter under controlled conditions → per-attempt records.

Same tasks/params for every model (apples-to-apples). Handles malformed tasks without
crashing the run, optionally runs tasks concurrently (honest throughput @ concurrency N),
and propagates token-accounting integrity so missing usage isn't silently $0.
"""
from __future__ import annotations
import concurrent.futures
import time

from .taskpack import load_taskpack, check_output
from ..pricing import token_cost, self_hosted_cost


def _run_one(task, i, adapter, snapshot, max_tokens, timeout, self_hosted):
    # [L-04] a malformed task (no prompt) becomes a recorded harness_error, not a crash
    prompt = task.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        return {"task_id": task.get("id", i), "success": False, "cost_usd": 0.0,
                "input_tokens": 0, "output_tokens": 0, "latency_ms": None, "ttft_ms": None,
                "gen_seconds": None, "timed_out": False, "hit_token_cap": False,
                "usage_missing": False, "error": "malformed task: missing 'prompt'"}
    r = adapter.complete(prompt, timeout=timeout, max_tokens=max_tokens)
    ok = (not r.timed_out and not r.error and check_output(r.text, task.get("check")))
    if self_hosted:
        tps = (r.output_tokens / r.gen_seconds) if (r.gen_seconds and r.output_tokens) else None
        cost = self_hosted_cost(r.output_tokens, tps, self_hosted["gpu_hour_usd"],
                                self_hosted.get("utilization", 0.7)) or 0.0
    else:
        cost = token_cost(adapter.model_id, r.input_tokens, r.output_tokens, snapshot) or 0.0
    return {"task_id": task.get("id", i), "success": ok, "cost_usd": cost,
            "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
            "latency_ms": r.latency_ms, "ttft_ms": r.ttft_ms, "gen_seconds": r.gen_seconds,
            "timed_out": r.timed_out, "hit_token_cap": r.hit_token_cap,
            "usage_missing": r.usage_missing, "error": r.error}


def run_taskpack(taskpack, adapter, snapshot=None, max_tokens=512, timeout=60,
                 self_hosted=None, concurrency=1, on_task=None):
    tp = load_taskpack(taskpack) if not hasattr(taskpack, "tasks") else taskpack
    concurrency = max(1, int(concurrency))
    attempts = [None] * len(tp.tasks)
    wall0 = time.perf_counter()
    if concurrency == 1:
        for i, task in enumerate(tp.tasks):
            attempts[i] = _run_one(task, i, adapter, snapshot, max_tokens, timeout, self_hosted)
            if on_task:
                on_task(i + 1, len(tp.tasks), attempts[i])
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            futs = {ex.submit(_run_one, t, i, adapter, snapshot, max_tokens, timeout, self_hosted): i
                    for i, t in enumerate(tp.tasks)}
            done = 0
            for fut in concurrent.futures.as_completed(futs):
                i = futs[fut]
                attempts[i] = fut.result()
                done += 1
                if on_task:
                    on_task(done, len(tp.tasks), attempts[i])
    wall = time.perf_counter() - wall0
    usage_missing_n = sum(1 for a in attempts if a.get("usage_missing"))
    return {"taskpack": tp.name, "taskpack_version": tp.version,
            "model_id": adapter.model_id, "n_tasks": len(tp.tasks),
            "concurrency": concurrency, "wall_seconds": round(wall, 3),
            "usage_missing_count": usage_missing_n, "attempts": attempts}
