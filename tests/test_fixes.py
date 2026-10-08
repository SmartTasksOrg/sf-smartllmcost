"""Regression tests for the devil's-advocate review fixes."""
import pytest
from sf_smartllmcost.config import resolve_adapter
from sf_smartllmcost.harness import run_taskpack
from sf_smartllmcost.harness.taskpack import validate_taskpack
from sf_smartllmcost.report import build_report
from sf_smartllmcost.pricing import amortized_gpu_hour


def _adapter(resp, model_id="openai:gpt-4o"):
    a = resolve_adapter("openai", "gpt-4o", transport=lambda p, b: resp)
    a.model_id = model_id
    return a


def test_W05_empty_choices_no_crash():
    r = _adapter({"choices": []}).complete("x")
    assert r.text == "" and not r.error


def test_D01_missing_usage_flagged_and_warned():
    a = _adapter({"choices": [{"message": {"content": "42"}}]})   # no usage
    rep = build_report(run_taskpack(
        {"name": "t", "version": "1", "tasks": [{"id": "a", "prompt": "6*7", "check": {"type": "contains", "value": "42"}}]}, a))
    assert rep["warnings"] and any("no token usage" in w for w in rep["warnings"])


def test_L02_gpu_hour_rejects_zero_life():
    with pytest.raises(ValueError):
        amortized_gpu_hour(20000, life_years=0)


def test_L04_malformed_task_becomes_error_record():
    a = _adapter({"choices": [{"message": {"content": "x"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    run = run_taskpack({"name": "t", "version": "1", "tasks": [{"id": "bad"}]}, a)
    assert run["attempts"][0]["error"].startswith("malformed task")
    assert run["attempts"][0]["success"] is False


def test_OP02_retries_then_succeeds():
    calls = {"n": 0}

    def flaky(path, body):
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("transient")
        return {"choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
    a = resolve_adapter("openai", "gpt-4o", transport=flaky)
    a.retries = 2
    a.backoff = 0
    r = a.complete("x")
    assert r.text == "ok" and calls["n"] == 2


def test_validate_catches_problems():
    probs = validate_taskpack({"name": "t", "version": "1",
                               "tasks": [{"id": "a"}, {"id": "a", "prompt": "x"}]})
    assert any("missing 'prompt'" in p for p in probs)
    assert any("duplicate task id" in p for p in probs)


def test_concurrency_runs_all_and_warns():
    a = _adapter({"choices": [{"message": {"content": "42"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    tp = {"name": "t", "version": "1",
          "tasks": [{"id": str(i), "prompt": "6*7", "check": {"type": "contains", "value": "42"}} for i in range(8)]}
    rep = build_report(run_taskpack(tp, a, concurrency=4))
    assert rep["n_tasks"] == 8 and rep["headline"]["success_rate"] == 1.0
    assert any("concurrency" in w for w in rep["warnings"])


def test_ttft_summary_present():
    a = _adapter({"choices": [{"message": {"content": "42"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    rep = build_report(run_taskpack({"name": "t", "version": "1", "tasks": [{"id": "a", "prompt": "x", "check": None}]}, a))
    assert "ttft_ms" in rep and "p95" in rep["ttft_ms"]
