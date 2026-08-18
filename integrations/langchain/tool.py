"""LangChain-style tool wrapper: run a SmartLLMCost task-pack and return the true-cost report."""
from __future__ import annotations
import json


def smartllmcost_run(taskpack_path, preset="openai", model="gpt-4o", host="", api_key=""):
    from smartllmcost.config import resolve_adapter
    from smartllmcost.harness import run_taskpack
    from smartllmcost.report import build_report
    adapter = resolve_adapter(preset, model, host=host, api_key=api_key)
    return build_report(run_taskpack(taskpack_path, adapter))


try:
    from langchain.tools import Tool
    smartllmcost_tool = Tool(
        name="smartllmcost_true_cost",
        description="Run a task-pack against a model; returns $/successful-task, latency, tokens/sec.",
        func=lambda p: json.dumps(smartllmcost_run(p)))
except Exception:
    smartllmcost_tool = None
