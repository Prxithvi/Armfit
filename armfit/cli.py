"""
ArmFit CLI.

  python -m armfit demo_model.pte
  python -m armfit my_model.pte --mode dev --serve
  python -m armfit my_model.pte --mode arm --output-dir out/

Runs entirely on stdlib. Works on Ryzen 7 / any x86 machine in --mode dev
(the default). --mode arm requires real Arm SME2 hardware.
"""
import argparse
import sys
from pathlib import Path

from armfit.runner import executorch_runner, arm_sme2_runner
from armfit.analysis import ranker, comparator, explainer
from armfit.report import export
from armfit.dashboard import serve


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="armfit", description="From profiler data to performance decisions.")
    p.add_argument("model", help="Path to an ExecuTorch .pte model file")
    p.add_argument("--mode", choices=["dev", "arm"], default="dev",
                    help="'dev' runs anywhere (projected SME2 numbers). 'arm' requires real Arm SME2 hardware (measured numbers). Default: dev")
    p.add_argument("--output-dir", default="armfit-out", help="Where to write armfit-report.json / .html (default: ./armfit-out)")
    p.add_argument("--serve", action="store_true", help="Launch the local dashboard after generating the report")
    p.add_argument("--port", type=int, default=8765, help="Dashboard port (default: 8765)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.output_dir)

    print(f"ArmFit — profiling {args.model} (mode={args.mode})\n")

    if args.mode == "dev":
        try:
            baseline = executorch_runner.run(args.model, args.mode)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        if not baseline.measured:
            print("[baseline] Using synthetic profile (ExecuTorch not installed / real run not wired up).")
            print("           This is expected on a dev machine — see README for real-hardware setup.\n")
        sme2 = arm_sme2_runner.run_dev(baseline)
    else:
        # --mode arm: both baseline AND sme2 come from Arm's real pipeline
        # output (mac_sme2_off/ + mac_sme2_on/), so they're measured=True
        # on both sides — not projected.
        try:
            baseline, sme2 = arm_sme2_runner.run_arm(args.model)
        except (RuntimeError, NotImplementedError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    ranked = ranker.rank_bottlenecks(baseline)
    comparison = comparator.compare(baseline, sme2)
    insights = explainer.generate(ranked, comparison)

    report_data = export.build_report_data(args.model, args.mode, baseline, sme2, ranked, comparison, insights)
    json_path = export.export_json(report_data, out_dir)
    html_path = export.export_html(report_data, out_dir)

    # Terminal summary
    print(f"MODEL PERFORMANCE")
    print(f"  Baseline latency : {baseline.total_time_ms} ms")
    print(f"  SME2 latency     : {sme2.total_time_ms} ms  ({sme2.label})")
    print(f"  Improvement      : {comparison['overall_speedup_pct']}%\n")
    print("TOP BOTTLENECKS")
    for b in ranked[:3]:
        print(f"  {b['rank']}. {b['category']:<14} {b['pct']:>5}%   impact: {b['impact']}")
    print()
    print("INSIGHTS")
    for line in insights:
        print(f"  - {line}")
    print()
    print(f"Report written to:\n  {json_path}\n  {html_path}")

    if args.serve:
        serve.launch(out_dir, port=args.port)

    return 0


if __name__ == "__main__":
    sys.exit(main())
