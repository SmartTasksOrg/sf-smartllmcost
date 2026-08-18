"""Adapter interface + timed call wrapper with retries, timeout classification, and
token-accounting integrity (flags when a provider omits usage so cost isn't silently $0)."""
from __future__ import annotations
import socket
import time
from dataclasses import dataclass, field


@dataclass
class CallResult:
    text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    ttft_ms: float = None
    latency_ms: float = None
    gen_seconds: float = None
    timed_out: bool = False
    hit_token_cap: bool = False
    usage_missing: bool = False       # [D-01] provider returned no token usage
    error: str = ""
    raw: dict = field(default_factory=dict)


class ProviderAdapter:
    provider = "base"

    def __init__(self, model="", model_id="", transport=None, retries=2, backoff=0.5, **kw):
        self.model = model
        self.model_id = model_id or f"{self.provider}:{model}"
        self._transport = transport
        self.retries = max(0, retries)
        self.backoff = backoff
        self.opts = kw

    def complete(self, prompt, timeout=None, max_tokens=None, **params):
        """Times the call, retries transient failures, and classifies timeouts vs errors."""
        last_err = ""
        for attempt in range(self.retries + 1):
            t0 = time.perf_counter()
            try:
                r = self._complete(prompt, timeout=timeout, max_tokens=max_tokens, **params)
                if r.latency_ms is None:
                    r.latency_ms = (time.perf_counter() - t0) * 1000
                return r
            except (TimeoutError, socket.timeout):                 # [OP-04] both, for 3.9+
                return CallResult(timed_out=True, latency_ms=(time.perf_counter() - t0) * 1000)
            except Exception as e:                                  # [OP-02] retry transient
                last_err = str(e)
                if attempt < self.retries:
                    time.sleep(self.backoff * (2 ** attempt))
                    continue
                return CallResult(error=last_err, latency_ms=(time.perf_counter() - t0) * 1000)
        return CallResult(error=last_err)

    def _complete(self, prompt, **params):
        raise NotImplementedError
