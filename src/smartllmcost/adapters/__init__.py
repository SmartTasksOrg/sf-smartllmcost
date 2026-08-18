from .base import ProviderAdapter, CallResult
from .openai_compat import OpenAICompatAdapter
from .anthropic import AnthropicAdapter

def build_adapter(preset, **kw):
    """Factory: preset -> adapter. openai-compatible covers OpenAI, LM Studio, vLLM,
    Ollama, llama.cpp (all expose /v1/chat/completions)."""
    p = (preset or "").lower()
    if p in ("openai", "lmstudio", "vllm", "ollama", "llamacpp", "openai-compatible", "custom"):
        return OpenAICompatAdapter(**kw)
    if p == "anthropic":
        return AnthropicAdapter(**kw)
    raise ValueError(f"unknown preset: {preset}")
