"""Provider presets — mirrors SmartCVEScan's config. User gives host/port/token; the
preset fills endpoint + auth style. Same shape across the family."""
from __future__ import annotations

PRESETS = {
    "openai":    {"preset": "openai",    "endpoint": "https://api.openai.com/v1", "auth": "bearer"},
    "anthropic": {"preset": "anthropic", "endpoint": "https://api.anthropic.com/v1", "auth": "x-api-key"},
    "lmstudio":  {"preset": "lmstudio",  "endpoint": "http://localhost:1234/v1", "auth": "none"},
    "vllm":      {"preset": "vllm",      "endpoint": "http://localhost:8000/v1", "auth": "none"},
    "ollama":    {"preset": "ollama",    "endpoint": "http://localhost:11434/v1", "auth": "none"},
    "llamacpp":  {"preset": "llamacpp",  "endpoint": "http://localhost:8080/v1", "auth": "none"},
}


def build_endpoint(preset, host="", port=None, endpoint=""):
    if endpoint:
        return endpoint
    base = PRESETS.get(preset, {}).get("endpoint", "http://localhost:1234/v1")
    if host:
        scheme = "http://" if not host.startswith("http") else ""
        port_s = f":{port}" if port else ""
        return f"{scheme}{host}{port_s}/v1"
    return base


def resolve_adapter(preset, model, host="", port=None, endpoint="", api_key="", model_id="", transport=None, stream=False, stream_transport=None):
    from .adapters import build_adapter
    ep = build_endpoint(preset, host, port, endpoint)
    kw = dict(model=model, model_id=model_id or f"{preset}:{model}",
              endpoint=ep, api_key=api_key, transport=transport)
    if stream:
        kw["stream"] = True
    if stream_transport is not None:
        kw["stream_transport"] = stream_transport
    return build_adapter(preset, **kw)
