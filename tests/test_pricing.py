from smartllmcost.pricing import token_cost, amortized_gpu_hour, self_hosted_cost, DEFAULT_SNAPSHOT


def test_token_cost_uses_native_rates():
    # gpt-4o: 2.50 in / 10.00 out per 1M
    assert token_cost("openai:gpt-4o", 1_000_000, 0) == 2.50
    assert token_cost("openai:gpt-4o", 0, 1_000_000) == 10.00


def test_unknown_model_returns_none():
    assert token_cost("nope:model", 100, 100) is None


def test_amortized_gpu_hour_decomposes():
    gh = amortized_gpu_hour(20000, life_years=3, power_watts=700, pue=1.5, power_price_kwh=0.12)
    assert gh["gpu_hour_usd"] == round(gh["capex_component"] + gh["power_component"], 4)
    assert gh["assumptions"]["gpu_capex_usd"] == 20000


def test_self_hosted_cost_scales_with_time():
    gh = amortized_gpu_hour(20000)["gpu_hour_usd"]
    slow = self_hosted_cost(1000, 10, gh)   # 100s of gen
    fast = self_hosted_cost(1000, 100, gh)  # 10s of gen
    assert slow > fast > 0
