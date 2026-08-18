"""smartllmcost CLI — run a task-pack against one or more models and emit a true-cost report."""
from __future__ import annotations
import argparse
import json
import os
import sys

from .config import resolve_adapter
from .harness import run_taskpack
from .report import build_report, compare
from .formats import to_json, to_csv, to_prometheus
from .pricing import load_pricing, amortized_gpu_hour
from .versioning import __version__


def _add_model_args(p):
    p.add_argument("--preset", default="openai",
                   choices=["openai", "anthropic", "lmstudio", "vllm", "ollama", "llamacpp", "custom"])
    p.add_argument("--model", required=True)
    p.add_argument("--host", default="")
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--endpoint", default="")
    p.add_argument("--api-key", default=os.environ.get("SMARTBENCH_API_KEY", ""))
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--timeout", type=int, default=60)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="smartllmcost")
    ap.add_argument("--version", action="version", version=f"smartllmcost {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run a task-pack against a model")
    r.add_argument("taskpack")
    _add_model_args(r)
    r.add_argument("--pricing", default="", help="path to a dated pricing snapshot JSON")
    r.add_argument("--self-hosted-gpu-hour", type=float, default=None,
                   help="price local model via this amortized $/GPU-hour")
    r.add_argument("--concurrency", type=int, default=1, help="run N tasks in parallel (throughput @ N)")
    r.add_argument("--stream", action="store_true", help="stream responses to measure real TTFT")
    r.add_argument("--format", default="json", choices=["json", "csv", "prometheus"])
    r.add_argument("--output", "-o", default="")

    c = sub.add_parser("compare", help="rank several run reports by cost-per-successful-task")
    c.add_argument("reports", nargs="+")
    c.add_argument("--format", default="table", choices=["table", "csv", "json"])

    v = sub.add_parser("validate", help="check a task-pack for problems before running")
    v.add_argument("taskpack")

    sub.add_parser("presets", help="list provider presets and their default endpoints")

    dsh = sub.add_parser("dashboard", help="build a traffic-light HTML dashboard from run reports")
    dsh.add_argument("reports", nargs="+")
    dsh.add_argument("--max-cost", type=float, default=0.05, help="budget: max $/successful task (green threshold)")
    dsh.add_argument("--min-success", type=float, default=0.9, help="min success rate for green")
    dsh.add_argument("--output", "-o", default="smartllmcost-dashboard.html")

    g = sub.add_parser("gpu-hour", help="compute an amortized $/GPU-hour for self-hosted cost")
    g.add_argument("--capex", type=float, required=True)
    g.add_argument("--life-years", type=float, default=3)
    g.add_argument("--watts", type=float, default=700)
    g.add_argument("--pue", type=float, default=1.5)
    g.add_argument("--kwh-price", type=float, default=0.12)

    args = ap.parse_args(argv)

    if args.cmd == "run":
        snapshot = load_pricing(args.pricing)
        adapter = resolve_adapter(args.preset, args.model, args.host, args.port,
                                  args.endpoint, args.api_key, stream=args.stream)
        sh = {"gpu_hour_usd": args.self_hosted_gpu_hour} if args.self_hosted_gpu_hour else None

        def prog(done, total, rec):
            sys.stderr.write(f"\r  task {done}/{total} {'✓' if rec['success'] else '·'}   ")
            sys.stderr.flush()
        run = run_taskpack(args.taskpack, adapter, snapshot=snapshot,
                           max_tokens=args.max_tokens, timeout=args.timeout,
                           self_hosted=sh, concurrency=args.concurrency, on_task=prog)
        sys.stderr.write("\n")
        report = build_report(run, snapshot=snapshot)
        for w in report.get("warnings", []):
            print(f"  ! {w}", file=sys.stderr)
        out = {"json": to_json(report), "csv": to_csv(report),
               "prometheus": to_prometheus(report)}[args.format]
        if args.output:
            open(args.output, "w", encoding="utf-8").write(out)
            h = report["headline"]
            print(f"{report['model_id']}: ${h['cost_per_successful_task']}/successful task "
                  f"(success {h['success_rate']}) → {os.path.abspath(args.output)}", file=sys.stderr)
        else:
            print(out)
        return 0

    if args.cmd == "compare":
        reports = [json.load(open(p, encoding="utf-8")) for p in args.reports]
        cmp = compare(reports)
        if args.format == "json":
            print(json.dumps(cmp, indent=2))
        elif args.format == "csv":
            print(to_csv(reports))
        else:
            print(f"{'model':30s} {'$/success':>12s} {'success':>8s} {'p95 ms':>10s} {'tok/s':>8s}")
            for r in cmp["ranked"]:
                cps = "n/a" if r["cost_per_successful_task"] is None else f"{r['cost_per_successful_task']:.6f}"
                print(f"{r['model_id']:30s} {cps:>12s} {r['success_rate']:>8} "
                      f"{str(r['p95_latency_ms']):>10s} {str(r['tokens_per_sec']):>8s}")
        return 0

    if args.cmd == "validate":
        from .harness.taskpack import validate_taskpack
        problems = validate_taskpack(args.taskpack)
        if not problems:
            print("task-pack OK")
            return 0
        print("task-pack has problems:")
        for pr in problems:
            print(f"  - {pr}")
        return 1

    if args.cmd == "presets":
        from .config import PRESETS
        for name, cfg in PRESETS.items():
            print(f"{name:12s} {cfg['endpoint']:40s} auth={cfg['auth']}")
        return 0

    if args.cmd == "dashboard":
        from .dashboard import build_dashboard
        reports = [json.load(open(p, encoding="utf-8")) for p in args.reports]
        html_out = build_dashboard(reports, max_cost=args.max_cost, min_success=args.min_success)
        open(args.output, "w", encoding="utf-8").write(html_out)
        print(f"dashboard → {os.path.abspath(args.output)}", file=sys.stderr)
        return 0

    if args.cmd == "gpu-hour":
        gh = amortized_gpu_hour(args.capex, args.life_years, args.watts, args.pue, args.kwh_price)
        print(json.dumps(gh, indent=2))
        return 0

    return 1


def _entry():
    sys.exit(main())
