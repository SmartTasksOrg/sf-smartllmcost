"""Versioned, timestamped pricing + cost computation.

Prices change constantly, so every number is pinned to a dated snapshot and reports
record which snapshot they used (auditable + re-computable later). Includes the
self-hosted amortized GPU-hour model so hosted vs local is finally comparable.
"""
from __future__ import annotations
import datetime
import json
import os

# A pinned snapshot. These are ILLUSTRATIVE defaults — real runs should load a current
# snapshot (see load_pricing) and record its date. Prices are USD per 1M tokens.
DEFAULT_SNAPSHOT = {
    "snapshot_date": "2026-01-01",
    "note": "ILLUSTRATIVE defaults — replace with a current dated snapshot before publishing numbers.",
    "models": {
        # model_id: {input, output}  (USD per 1M tokens)
        "openai:gpt-4o": {"input": 2.50, "output": 10.00},
        "anthropic:claude-sonnet": {"input": 3.00, "output": 15.00},
        "self-hosted": {"input": 0.0, "output": 0.0},  # computed via amortized model
    },
}


def load_pricing(path=""):
    if path and os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return DEFAULT_SNAPSHOT


def token_cost(model_id, input_tokens, output_tokens, snapshot=None):
    """Cost of one call from that model's native token counts. Never mixes tokenizers:
    each model is priced by ITS OWN token counts against ITS OWN rate."""
    snap = snapshot or DEFAULT_SNAPSHOT
    rate = snap["models"].get(model_id)
    if not rate:
        return None
    return round(input_tokens / 1e6 * rate["input"] + output_tokens / 1e6 * rate["output"], 8)


def self_hosted_cost(output_tokens, tokens_per_sec, gpu_hourly_usd, utilization=0.7):
    """Amortized self-hosted cost for a call: GPU-hour cost apportioned by the time this
    call actually used the GPU, adjusted for realistic utilization.

    gpu_hourly_usd should already amortize purchase + power + cooling + maintenance
    (see amortized_gpu_hour). utilization<1 means you rarely run the GPU flat-out.
    """
    if not tokens_per_sec or tokens_per_sec <= 0 or utilization <= 0:
        return None
    gen_seconds = output_tokens / tokens_per_sec
    effective_hourly = gpu_hourly_usd / utilization
    return round(gen_seconds / 3600.0 * effective_hourly, 8)


def amortized_gpu_hour(gpu_capex_usd, life_years=3, power_watts=700, pue=1.5,
                       power_price_kwh=0.12, maintenance_pct=0.10):
    """Build a defensible $/GPU-hour from purchase + power + cooling + maintenance.

    capex spread over life_years of 24/7 hours; power × PUE (cooling) at the grid price;
    maintenance as a % uplift on capex. Returns USD/hour. Every assumption is explicit so
    the number is auditable (the spec's core requirement for self-hosted fairness).
    """
    if life_years <= 0:
        raise ValueError("life_years must be > 0")
    hours = life_years * 365 * 24
    capex_hour = gpu_capex_usd * (1 + maintenance_pct) / hours
    power_hour = (power_watts * pue / 1000.0) * power_price_kwh
    return {"gpu_hour_usd": round(capex_hour + power_hour, 4),
            "capex_component": round(capex_hour, 4),
            "power_component": round(power_hour, 4),
            "assumptions": {"gpu_capex_usd": gpu_capex_usd, "life_years": life_years,
                            "power_watts": power_watts, "pue": pue,
                            "power_price_kwh": power_price_kwh, "maintenance_pct": maintenance_pct}}


def pricing_provenance(snapshot=None):
    snap = snapshot or DEFAULT_SNAPSHOT
    return {"snapshot_date": snap.get("snapshot_date"),
            "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
            "n_models": len(snap.get("models", {}))}
