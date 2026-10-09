from sf_smartllmcost.config import resolve_adapter
from sf_smartllmcost.harness import run_taskpack
from sf_smartllmcost.report import build_report, compare
from sf_smartllmcost.formats import to_csv, to_prometheus, to_json


def _adapter(answer, in_tok=10, out_tok=5, model_id="openai:gpt-4o"):
    fake = lambda path, body: {"choices": [{"message": {"content": answer}, "finish_reason": "stop"}],
                               "usage": {"prompt_tokens": in_tok, "completion_tokens": out_tok}}
    a = resolve_adapter("openai", "gpt-4o", transport=fake)
    a.model_id = model_id
    return a


_TP = {"name": "t", "version": "1", "tasks": [
    {"id": "a", "prompt": "6*7", "check": {"type": "contains", "value": "42"}},
    {"id": "b", "prompt": "cap", "check": {"type": "contains", "value": "Paris"}}]}


def test_run_and_report_headline():
    run = run_taskpack(_TP, _adapter("42 and Paris"))
    rep = build_report(run)
    assert rep["headline"]["success_rate"] == 1.0
    assert rep["headline"]["cost_per_successful_task"] is not None
    assert rep["n_tasks"] == 2


def test_partial_success_costs_more_per_success():
    good = build_report(run_taskpack(_TP, _adapter("42 Paris")))
    half = build_report(run_taskpack(_TP, _adapter("42 only")))   # misses Paris
    assert half["headline"]["success_rate"] == 0.5
    # same spend, fewer successes → higher cost per success
    assert half["headline"]["cost_per_successful_task"] > good["headline"]["cost_per_successful_task"]


def test_compare_ranks_cheapest_success_first():
    # both priced models; cheap = fewer output tokens on gpt-4o, pricey = many on claude
    r1 = build_report(run_taskpack(_TP, _adapter("42 Paris", out_tok=5, model_id="openai:gpt-4o")))
    r2 = build_report(run_taskpack(_TP, _adapter("42 Paris", out_tok=200, model_id="anthropic:claude-sonnet")))
    ranked = compare([r2, r1])["ranked"]
    assert ranked[0]["model_id"] == "openai:gpt-4o"


def test_exports_render():
    rep = build_report(run_taskpack(_TP, _adapter("42 Paris")))
    assert "smartllmcost_cost_per_successful_task_usd" in to_prometheus(rep)
    assert "cost_per_successful_task" in to_csv(rep)
    assert '"schema_version"' in to_json(rep)
