"""Streaming path: real TTFT capture + generation-only timing."""
import time
from sf_smartllmcost.config import resolve_adapter
from sf_smartllmcost.harness import run_taskpack
from sf_smartllmcost.report import build_report


def _fake_stream(delay_first=0.03):
    def gen(path, body):
        time.sleep(delay_first)
        yield 'data: {"choices":[{"delta":{"content":"4"}}]}'
        yield 'data: {"choices":[{"delta":{"content":"2"},"finish_reason":"stop"}]}'
        yield 'data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":2}}'
        yield 'data: [DONE]'
    return gen


def _adapter():
    a = resolve_adapter("openai", "gpt-4o", stream=True, stream_transport=_fake_stream())
    a.model_id = "openai:gpt-4o"
    return a


def test_streaming_captures_ttft():
    r = _adapter().complete("6*7")
    assert r.text == "42"
    assert r.ttft_ms is not None and r.ttft_ms >= 25   # ~30ms simulated think-time
    assert r.output_tokens == 2 and not r.usage_missing


def test_streaming_gen_seconds_excludes_first_token_latency():
    r = _adapter().complete("6*7")
    # generation-only (first->last token) is much smaller than end-to-end latency
    assert r.gen_seconds is not None
    assert r.gen_seconds * 1000 < r.latency_ms


def test_report_ttft_summary_populated_when_streaming():
    a = _adapter()
    tp = {"name": "t", "version": "1",
          "tasks": [{"id": str(i), "prompt": "6*7", "check": {"type": "contains", "value": "42"}} for i in range(3)]}
    rep = build_report(run_taskpack(tp, a))
    assert rep["ttft_ms"]["p50"] is not None
    assert rep["headline"]["success_rate"] == 1.0


def test_streaming_handles_missing_usage_chunk():
    def gen(path, body):
        yield 'data: {"choices":[{"delta":{"content":"hi"},"finish_reason":"stop"}]}'
        yield 'data: [DONE]'
    a = resolve_adapter("openai", "m", stream=True, stream_transport=gen)
    r = a.complete("x")
    assert r.text == "hi" and r.usage_missing is True
