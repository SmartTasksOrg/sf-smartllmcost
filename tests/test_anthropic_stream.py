"""Anthropic streaming: named-event SSE, TTFT, split usage."""
import time
from smartllmcost.config import resolve_adapter


def _fake(path, body):
    yield 'data: {"type":"message_start","message":{"usage":{"input_tokens":9}}}'
    time.sleep(0.03)
    yield 'data: {"type":"content_block_delta","delta":{"text":"4"}}'
    yield 'data: {"type":"content_block_delta","delta":{"text":"2"}}'
    yield 'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":2}}'
    yield 'data: {"type":"message_stop"}'


def test_anthropic_stream_ttft_and_usage():
    a = resolve_adapter("anthropic", "claude-sonnet", stream=True, stream_transport=_fake)
    r = a.complete("6*7")
    assert r.text == "42"
    assert r.ttft_ms is not None and r.ttft_ms >= 20
    assert r.input_tokens == 9 and r.output_tokens == 2
    assert not r.usage_missing


def test_anthropic_stream_max_tokens_flag():
    def gen(path, body):
        yield 'data: {"type":"message_start","message":{"usage":{"input_tokens":5}}}'
        yield 'data: {"type":"content_block_delta","delta":{"text":"x"}}'
        yield 'data: {"type":"message_delta","delta":{"stop_reason":"max_tokens"},"usage":{"output_tokens":1}}'
        yield 'data: {"type":"message_stop"}'
    a = resolve_adapter("anthropic", "claude-sonnet", stream=True, stream_transport=gen)
    r = a.complete("x")
    assert r.hit_token_cap is True
