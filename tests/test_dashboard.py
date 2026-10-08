"""Traffic-light dashboard: correct light per report + ranking."""
from sf_smartllmcost.config import resolve_adapter
from sf_smartllmcost.harness import run_taskpack
from sf_smartllmcost.report import build_report
from sf_smartllmcost.dashboard import build_dashboard, _light


_TP = {"name": "t", "version": "1",
       "tasks": [{"id": str(i), "prompt": "6*7", "check": {"type": "contains", "value": "42"}} for i in range(4)]}


def _report(answer, out_tok, mid):
    a = resolve_adapter("openai", "m", transport=lambda p, b: {
        "choices": [{"message": {"content": answer}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": out_tok}})
    a.model_id = mid
    return build_report(run_taskpack(_TP, a))


def test_all_fail_is_red():
    r = _report("nope", 5, "local:tiny")
    assert _light(r, 0.05, 0.9) == "red"


def test_over_budget_is_amber():
    r = _report("42", 300, "anthropic:claude-sonnet")   # passes but pricey
    assert _light(r, 0.0001, 0.9) == "amber"


def test_within_budget_is_green():
    r = _report("42", 5, "openai:gpt-4o")
    assert _light(r, 1.0, 0.9) == "green"


def test_dashboard_html_ranks_cheapest_first_and_has_states():
    good = _report("42", 5, "openai:gpt-4o")
    pricey = _report("42", 300, "anthropic:claude-sonnet")
    bad = _report("nope", 5, "local:tiny")
    html = build_dashboard([pricey, bad, good], max_cost=0.0005)
    assert "<!doctype html>" in html
    assert html.index("openai:gpt-4o") < html.index("anthropic:claude-sonnet")   # cheapest first
    assert all(c in html for c in ["#1a7f37", "#bf8700", "#cf222e"])              # all 3 lights
