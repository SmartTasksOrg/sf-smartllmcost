"""Adapter pattern for external harnesses → native task-pack.

External suites (lm-evaluation-harness, HELM, SWE-bench) describe tasks differently. Each
adapter converts their task list into SmartBench's {id, prompt, check} shape so the SAME
cost/timing/quality math applies. Below is the interface + a worked converter example.
"""
from __future__ import annotations
from ..harness.taskpack import TaskPack


def from_records(name, version, records, prompt_key="prompt", answer_key="answer"):
    """Generic converter: list of {prompt, answer} → TaskPack with equality checks."""
    tasks = [{"id": r.get("id", i), "prompt": r[prompt_key],
              "check": {"type": "contains", "value": str(r[answer_key])}}
             for i, r in enumerate(records)]
    return TaskPack(name, version, tasks)


# Stubs to be fleshed out against each harness's real API:
def from_lm_eval_harness(task_name, docs):        # EleutherAI lm-evaluation-harness
    return from_records(f"lm-eval:{task_name}", "0", docs)


def from_helm(scenario, instances):               # Stanford HELM
    return from_records(f"helm:{scenario}", "0", instances)


def from_swebench(instances):                     # SWE-bench (coding/agentic)
    # SWE-bench success is "patch applies + tests pass"; the check would call the harness's
    # own evaluator rather than a text match. Placeholder keeps the shape.
    return from_records("swe-bench", "0", instances, prompt_key="problem_statement",
                        answer_key="expected")
