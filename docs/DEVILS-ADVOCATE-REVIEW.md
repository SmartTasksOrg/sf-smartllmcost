# Devil's-advocate review — findings & fixes

A hostile trace of the codebase against the Circuit-Breaker wiring/logic frameworks and the
security/UX/feature review prompt. Every finding below was a **real** bug in the code and is
now fixed with a regression test (`tests/test_fixes.py`).

## Wiring & interface integrity
| ID | Finding | Fix |
|----|---------|-----|
| **W-05** | `openai_compat._complete` did `data.get("choices",[{}])[0]` — an **empty** `choices: []` (not missing) → `IndexError`, crashing the call. | Guard: `choices = data.get("choices") or []; first = choices[0] if choices else {}`. |
| **W-02** | Adapter kwargs (`model`, `model_id`, `transport`) flowed through `**kw`; a typo'd preset would build the wrong adapter silently. | `build_adapter` validates the preset and raises on unknown; CLI restricts choices. |

## Logic execution & branch completeness
| ID | Finding | Fix |
|----|---------|-----|
| **L-02** | `amortized_gpu_hour(life_years=0)` → **ZeroDivisionError** (boundary failure). | Raise `ValueError` for `life_years <= 0`; other zero inputs already guarded. |
| **L-04** | A task missing `prompt` raised `KeyError` and **killed the whole run** (one bad row lost all results). | Malformed tasks become a recorded `harness_error` attempt; the run continues. |

## Data flow & transformation
| ID | Finding | Fix |
|----|---------|-----|
| **D-01** | If a provider omitted `usage`, token counts were `0` → cost silently `$0` → a run looked **free**. This is the most dangerous flaw: it corrupts the headline metric without any signal. | `usage_missing` flag on every call; runner counts them; report emits a **warning** that costs are unreliable, and warns if all attempts cost $0 (pricing snapshot miss). |

## Operational flow & resilience
| ID | Finding | Fix |
|----|---------|-----|
| **OP-01** | Report claimed "throughput @ concurrency N" but the runner was **serial** — the number was misleading. | Real optional concurrency (thread pool); report records `concurrency` and warns that latency reflects contention when >1. |
| **OP-02** | A single transient network error marked a task `harness_error` with **no retry** — noisy, unfair failures. | Retries with exponential backoff in `adapter.complete`. |
| **OP-04** | On Python 3.9 a socket timeout is `socket.timeout` (not `TimeoutError`), so it was mis-classified as a generic error, not `budget_exhaustion`. | Catch both `TimeoutError` and `socket.timeout`. |

## Feature completeness
| ID | Finding | Fix |
|----|---------|-----|
| **F-03** | No way to check a task-pack before a long run; no way to see providers. | `sf-smartllmcost validate <taskpack>` and `sf-smartllmcost presets`. |
| **F-04** | Spec promises TTFT but the report never summarized it. | `ttft_ms` percentile block added (populated when the transport streams; null otherwise, documented). |
| **CQ** | Task-pack structure was never validated (bad JSON shape → obscure crash). | `validate_taskpack` checks tasks list, prompts, check types, duplicate ids. |

## Honest residual limits (not "fixed" — acknowledged)
- **TTFT is measured with --stream (null otherwise).** The non-streaming path can't measure time-to-first-token; the field exists and is populated only when a streaming transport is used.
- **Token-cap vs timeout** can only be distinguished when the provider returns `finish_reason`/`stop_reason`.
- **Default pricing is illustrative** — publish numbers only against a current dated snapshot.
- **No live provider call has been exercised in CI** (offline); adapters are tested against mocked transports and must be validated against real endpoints.
