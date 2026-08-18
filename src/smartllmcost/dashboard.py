"""Traffic-light dashboard — self-contained HTML from one or more run reports.

Green/amber/red is by cost-per-successful-task and success rate against budgets you set
(or sensible defaults). No dependencies; writes a single .html you can open or host.
"""
from __future__ import annotations
import html
import json


def _light(report, max_cost, min_success):
    h = report.get("headline", {})
    cps = h.get("cost_per_successful_task")
    sr = h.get("success_rate", 0) or 0
    if cps is None or sr < 0.5:
        return "red"
    if (max_cost and cps > max_cost) or sr < min_success:
        return "amber"
    return "green"


_COLORS = {"green": "#1a7f37", "amber": "#bf8700", "red": "#cf222e"}
_BG = {"green": "#e6f4ea", "amber": "#fff8e1", "red": "#ffebe9"}


def build_dashboard(reports, max_cost=0.05, min_success=0.9, title="SmartLLMCost — true cost"):
    if isinstance(reports, dict):
        reports = [reports]
    rows = []
    ranked = sorted(reports, key=lambda r: (r["headline"].get("cost_per_successful_task") is None,
                                            r["headline"].get("cost_per_successful_task") or 0))
    for r in ranked:
        light = _light(r, max_cost, min_success)
        h = r["headline"]
        lat = r.get("latency_ms", {})
        ttft = r.get("ttft_ms", {})
        cps = h.get("cost_per_successful_task")
        cps_s = "n/a" if cps is None else f"${cps:.6f}"
        warns = r.get("warnings", [])
        warn_html = ("<div class='warn'>⚠ " + "<br>⚠ ".join(html.escape(w) for w in warns) + "</div>") if warns else ""
        rows.append(f"""
        <div class="card" style="border-left:8px solid {_COLORS[light]};background:{_BG[light]}">
          <div class="dot" style="background:{_COLORS[light]}"></div>
          <div class="body">
            <div class="model">{html.escape(r.get('model_id','?'))}</div>
            <div class="metrics">
              <span><b>{cps_s}</b> / successful task</span>
              <span>success <b>{round((h.get('success_rate') or 0)*100)}%</b></span>
              <span>p95 <b>{lat.get('p95','–')} ms</b></span>
              <span>TTFT p50 <b>{ttft.get('p50','–')} ms</b></span>
              <span>tok/s <b>{r.get('output_tokens_per_sec','–')}</b></span>
              <span>tasks <b>{r.get('n_tasks','–')}</b></span>
            </div>
            {warn_html}
          </div>
        </div>""")
    overall = "green"
    lights = [_light(r, max_cost, min_success) for r in reports]
    if "red" in lights:
        overall = "red"
    elif "amber" in lights:
        overall = "amber"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f8fa;color:#1f2328}}
 header{{padding:20px 28px;background:#fff;border-bottom:1px solid #d0d7de;display:flex;align-items:center;gap:14px}}
 header .big{{width:20px;height:20px;border-radius:50%;background:{_COLORS[overall]}}}
 h1{{font-size:18px;margin:0}} .sub{{color:#656d76;font-size:13px;margin-left:auto}}
 .wrap{{padding:22px 28px;max-width:1000px;margin:0 auto}}
 .card{{display:flex;gap:14px;align-items:flex-start;background:#fff;border:1px solid #d0d7de;
        border-radius:10px;padding:14px 16px;margin-bottom:12px}}
 .dot{{width:14px;height:14px;border-radius:50%;margin-top:5px;flex:none}}
 .model{{font-weight:600;font-size:15px;margin-bottom:6px}}
 .metrics{{display:flex;flex-wrap:wrap;gap:16px;font-size:13px;color:#3b4148}}
 .metrics b{{color:#1f2328}}
 .warn{{margin-top:8px;font-size:12px;color:#9a6700}}
 footer{{padding:16px 28px;color:#8b949e;font-size:12px;text-align:center}}
</style></head><body>
<header><div class="big"></div><h1>{html.escape(title)}</h1>
 <span class="sub">budget: ≤ ${max_cost}/task · ≥ {round(min_success*100)}% success · ranked cheapest-per-success first</span>
</header>
<div class="wrap">{''.join(rows)}</div>
<footer>Green = within budget · Amber = over budget or low success · Red = failing / unreliable.
 Estimates only — see the run warnings and methodology.</footer>
</body></html>"""
