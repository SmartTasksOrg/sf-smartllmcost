"""OpenAI-compatible adapter (OpenAI, LM Studio, vLLM, Ollama, llama.cpp).

Two modes:
  * non-streaming (default): one POST, usage comes back in the body.
  * streaming (stream=True): SSE chunks — captures real TTFT (time to first content
    token) and generation-only time (first token → last token), which makes
    tokens/sec accurate instead of network-inflated.

Testable offline: inject `transport` (non-streaming) or `stream_transport` (an iterable
of SSE `data:` lines) so no network is needed.
"""
from __future__ import annotations
import json
import time
import urllib.request

from .base import ProviderAdapter, CallResult


class OpenAICompatAdapter(ProviderAdapter):
    provider = "openai"

    def __init__(self, endpoint="https://api.openai.com/v1", api_key="", stream=False,
                 stream_transport=None, **kw):
        super().__init__(**kw)
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.stream = stream
        self._stream_transport = stream_transport   # callable(path, body) -> iterable of raw SSE lines

    # ---- non-streaming ----
    def _post(self, path, body, timeout):
        if self._transport:
            return self._transport(path, body)
        req = urllib.request.Request(self.endpoint + path, data=json.dumps(body).encode(),
                                     headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    # ---- streaming (SSE line iterator) ----
    def _stream_lines(self, path, body, timeout):
        if self._stream_transport:
            for ln in self._stream_transport(path, body):
                yield ln
            return
        req = urllib.request.Request(self.endpoint + path, data=json.dumps(body).encode(),
                                     headers=self._headers(), method="POST")
        resp = urllib.request.urlopen(req, timeout=timeout)
        for raw in resp:
            yield raw.decode("utf-8", "replace")

    def _complete(self, prompt, timeout=None, max_tokens=None, temperature=0.0, **params):
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature}
        if max_tokens:
            body["max_tokens"] = max_tokens
        if self.stream:
            body["stream"] = True
            # ask providers that support it to include usage in the final SSE chunk
            body["stream_options"] = {"include_usage": True}
            return self._complete_streaming(body, timeout)
        return self._complete_blocking(body, timeout)

    def _complete_blocking(self, body, timeout):
        t0 = time.perf_counter()
        data = self._post("/chat/completions", body, timeout)
        elapsed = (time.perf_counter() - t0) * 1000
        choices = data.get("choices") or []
        first = choices[0] if choices else {}
        text = ((first.get("message") or {}).get("content", "") or "")
        finish = first.get("finish_reason", "")
        usage = data.get("usage") or {}
        return CallResult(text=text,
                          input_tokens=usage.get("prompt_tokens", 0),
                          output_tokens=usage.get("completion_tokens", 0),
                          latency_ms=elapsed, gen_seconds=elapsed / 1000.0,
                          hit_token_cap=(finish == "length"),
                          usage_missing=(not usage), raw=data)

    def _complete_streaming(self, body, timeout):
        t0 = time.perf_counter()
        ttft_ms = None
        first_tok_t = None
        last_tok_t = None
        parts = []
        finish = ""
        usage = {}
        for line in self._stream_lines("/chat/completions", body, timeout):
            line = line.strip()
            if not line or not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if payload == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
            except Exception:
                continue
            if chunk.get("usage"):
                usage = chunk["usage"]                       # final usage chunk
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = (choices[0].get("delta") or {})
            piece = delta.get("content")
            if piece:
                now = time.perf_counter()
                if first_tok_t is None:
                    first_tok_t = now
                    ttft_ms = (now - t0) * 1000
                last_tok_t = now
                parts.append(piece)
            if choices[0].get("finish_reason"):
                finish = choices[0]["finish_reason"]
        elapsed = (time.perf_counter() - t0) * 1000
        # generation-only time = first token → last token (excludes prompt/network to first byte)
        gen_seconds = ((last_tok_t - first_tok_t) if (first_tok_t and last_tok_t) else None)
        text = "".join(parts)
        # if provider didn't stream usage, estimate output tokens roughly (flag it)
        usage_missing = not usage
        out_tokens = usage.get("completion_tokens", 0)
        return CallResult(text=text,
                          input_tokens=usage.get("prompt_tokens", 0),
                          output_tokens=out_tokens,
                          ttft_ms=(round(ttft_ms, 2) if ttft_ms is not None else None),
                          latency_ms=elapsed,
                          gen_seconds=gen_seconds,
                          hit_token_cap=(finish == "length"),
                          usage_missing=usage_missing, raw={"streamed": True})
