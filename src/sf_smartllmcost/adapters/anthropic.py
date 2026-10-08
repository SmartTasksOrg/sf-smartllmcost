"""Anthropic Messages API adapter — blocking + streaming.

Anthropic's SSE format differs from OpenAI's: named events
(message_start / content_block_delta / message_delta / message_stop) with usage split
across message_start (input_tokens) and message_delta (output_tokens). We capture TTFT at
the first content_block_delta and generation-only time first→last delta.
"""
from __future__ import annotations
import json
import time
import urllib.request

from .base import ProviderAdapter, CallResult


class AnthropicAdapter(ProviderAdapter):
    provider = "anthropic"

    def __init__(self, endpoint="https://api.anthropic.com/v1", api_key="",
                 stream=False, stream_transport=None, **kw):
        super().__init__(**kw)
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.stream = stream
        self._stream_transport = stream_transport

    def _headers(self):
        return {"Content-Type": "application/json", "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"}

    def _post(self, path, body, timeout):
        if self._transport:
            return self._transport(path, body)
        req = urllib.request.Request(self.endpoint + path, data=json.dumps(body).encode(),
                                     headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

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

    def _complete(self, prompt, timeout=None, max_tokens=1024, temperature=0.0, **params):
        body = {"model": self.model, "max_tokens": max_tokens or 1024,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]}
        if self.stream:
            body["stream"] = True
            return self._complete_streaming(body, timeout)
        return self._complete_blocking(body, timeout)

    def _complete_blocking(self, body, timeout):
        t0 = time.perf_counter()
        data = self._post("/messages", body, timeout)
        elapsed = (time.perf_counter() - t0) * 1000
        usage = data.get("usage") or {}
        text = ""
        try:
            text = "".join(b.get("text", "") for b in (data.get("content") or []) if isinstance(b, dict))
        except Exception:
            text = ""
        return CallResult(text=text,
                          input_tokens=usage.get("input_tokens", 0),
                          output_tokens=usage.get("output_tokens", 0),
                          latency_ms=elapsed, gen_seconds=elapsed / 1000.0,
                          hit_token_cap=(data.get("stop_reason") == "max_tokens"),
                          usage_missing=(not usage), raw=data)

    def _complete_streaming(self, body, timeout):
        t0 = time.perf_counter()
        ttft_ms = None
        first_t = last_t = None
        parts = []
        in_tok = out_tok = 0
        stop_reason = ""
        for line in self._stream_lines("/messages", body, timeout):
            line = line.strip()
            if not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if not payload:
                continue
            try:
                ev = json.loads(payload)
            except Exception:
                continue
            etype = ev.get("type")
            if etype == "message_start":
                in_tok = (ev.get("message", {}).get("usage", {}) or {}).get("input_tokens", 0)
            elif etype == "content_block_delta":
                piece = (ev.get("delta") or {}).get("text")
                if piece:
                    now = time.perf_counter()
                    if first_t is None:
                        first_t = now
                        ttft_ms = (now - t0) * 1000
                    last_t = now
                    parts.append(piece)
            elif etype == "message_delta":
                out_tok = (ev.get("usage", {}) or {}).get("output_tokens", out_tok)
                stop_reason = (ev.get("delta", {}) or {}).get("stop_reason", stop_reason)
            elif etype == "message_stop":
                break
        elapsed = (time.perf_counter() - t0) * 1000
        gen_seconds = ((last_t - first_t) if (first_t and last_t) else None)
        usage_missing = (in_tok == 0 and out_tok == 0)
        return CallResult(text="".join(parts),
                          input_tokens=in_tok, output_tokens=out_tok,
                          ttft_ms=(round(ttft_ms, 2) if ttft_ms is not None else None),
                          latency_ms=elapsed, gen_seconds=gen_seconds,
                          hit_token_cap=(stop_reason == "max_tokens"),
                          usage_missing=usage_missing, raw={"streamed": True})
