"""
Produces the SME2-ON side of the comparison (and, in --mode arm, the
measured baseline too, since Arm's real pipeline produces both experimentsv
together).

--mode dev  (works on Ryzen 7 / any x86 machine)
    SME2 physically does not exist on non-Arm silicon, so we can't measure
    it. Instead we apply Arm's *published* category-level speedup ranges
    (roughly 3x-15x on CONV/GEMM, per Arm's SME2 profiling docs) to the
    baseline profile. The result is clearly labeled `measured=False` /
    "projected" everywhere it surfaces (CLI, JSON, HTML).

--mode arm  (requires real Arm SME2 hardware)
    Wired to Arm's actual `sme-executorch-profiling` repo. That repo only
    ships build presets for macOS (Apple Silicon) and Android -- there is
    no Linux/Graviton4 preset out of the box, despite what you may have
    read elsewhere. Get access to an M-series Mac or a recent Android
    phone; see README for the one-time setup commands.
"""
import json
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from armfit.analysis.models import (
    ARM_REAL_CATEGORY_MAP,
    CATEGORIES,
    OperatorStat,
    Profile,
    aggregate_categories,
)

DEV_MODE_MULTIPLIERS = {
    "Conv2D": 0.29,
    "GEMM/Linear": 0.25,
    "Elementwise": 0.88,
    "Normalization": 0.90,
    "DataMovement": 1.30,
    "Other": 0.85,
}


def run_dev(baseline: Profile) -> Profile:
    """Build a clearly-labeled PROJECTED SME2-ON profile from a baseline."""
    rng = random.Random(hash(baseline.total_time_ms) & 0xFFFFFFFF)
    operators: List[OperatorStat] = []
    for op in baseline.operators:
        mult = DEV_MODE_MULTIPLIERS.get(op.category, 1.0)
        jitter = rng.uniform(0.95, 1.05)
        operators.append(OperatorStat(name=op.name, category=op.category,
                                       time_ms=round(op.time_ms * mult * jitter, 3)))

    total_time_ms = round(sum(op.time_ms for op in operators), 2)
    categories = aggregate_categories(operators, total_time_ms)

    return Profile(
        label="SME2 ON (projected)",
        measured=False,
        total_time_ms=total_time_ms,
        operators=operators,
        categories=categories,
    )


def _kit_root() -> Path:
    return Path(os.environ.get("ARMFIT_SME_KIT", "./executorch_sme2_kit"))


def _platform() -> str:
    """'mac' or 'android'. Override with ARMFIT_SME_PLATFORM if needed."""
    override = os.environ.get("ARMFIT_SME_PLATFORM")
    if override:
        return override
    return "mac" if sys.platform == "darwin" else "android"


def _run_analyze_if_needed(analyze_script: Path, run_subdir: Path) -> Dict:
    """Call Arm's analyze_results.py for one experiment dir (mac_sme2_on/
    or mac_sme2_off/) if analysis_summary.json isn't already there, then
    load and return it."""
    summary_path = run_subdir / "analysis_summary.json"
    if not summary_path.exists():
        if not run_subdir.exists():
            raise RuntimeError(
                f"Expected experiment output directory not found: {run_subdir}\n"
                "Did the pipeline (mac_pipeline.py / android_pipeline.py) run "
                "and complete successfully?"
            )
        subprocess.run(
            [sys.executable, str(analyze_script), "--run-dir", str(run_subdir), "--quiet"],
            check=True,
        )
    return json.loads(summary_path.read_text(encoding="utf-8"))


def _profile_from_category_totals(label: str, category_totals_ms: Dict[str, float]) -> Profile:
    """Build a Profile from Arm's real category_totals_ms dict.

    NOTE: analysis_summary.json only gives category-level totals, not a
    true per-operator breakdown, so each category is represented here as
    one aggregate OperatorStat. This is enough to drive ArmFit's ranking,
    comparison, and report -- if you want real per-operator granularity,
    parse the *_exec_ops_stats.csv file next to each .etdump instead (also
    produced automatically by analyze_results.py).
    """
    operators: List[OperatorStat] = []
    for arm_cat, ms in category_totals_ms.items():
        armfit_cat = ARM_REAL_CATEGORY_MAP.get(arm_cat, "Other")
        operators.append(OperatorStat(name=f"{arm_cat} (aggregate)", category=armfit_cat, time_ms=round(ms, 3)))

    total_time_ms = round(sum(op.time_ms for op in operators), 2)
    categories = aggregate_categories(operators, total_time_ms)

    return Profile(
        label=label,
        measured=True,
        total_time_ms=total_time_ms,
        operators=operators,
        categories=categories,
    )


def run_arm(model_path_str: str) -> Tuple[Profile, Profile]:
    """
    Run (or reuse the results of) the REAL Arm SME2 profiling pipeline.
    Returns (baseline_profile, sme2_profile), both measured=True.

    Requires:
      1. Real Arm SME2-capable hardware (Apple Silicon Mac or a recent
         Cortex-X4/C1-class Android phone -- NOT arbitrary Linux/x86; the
         repo has no Linux preset).
      2. The sme-executorch-profiling kit already set up per its README
         (setup_repo.sh + build_runners.sh run once), with a completed
         pipeline run for this model (mac_pipeline.py / android_pipeline.py).

    Env vars:
      ARMFIT_SME_KIT       path to the cloned kit (default ./executorch_sme2_kit)
      ARMFIT_SME_PLATFORM  'mac' or 'android' (default: 'mac' on macOS, else 'android')
      ARMFIT_SME_RUN_ROOT  path to out_<model>/runs/<platform> for this model
                            (default: <kit>/model_profiling/out_<model_stem>/runs/<platform>)
    """
    kit = _kit_root()
    if not kit.exists():
        raise RuntimeError(
            "Real SME2 profiling requested (--mode arm) but the Arm "
            f"sme-executorch-profiling kit was not found at '{kit}'.\n\n"
            "Setup (one time, on an Apple Silicon Mac or with an Android phone):\n"
            "  git clone https://github.com/ArmDeveloperEcosystem/sme-executorch-profiling.git executorch_sme2_kit\n"
            "  cd executorch_sme2_kit\n"
            "  bash model_profiling/scripts/setup_repo.sh\n"
            "  bash model_profiling/scripts/build_runners.sh\n\n"
            "Then export your model and run the pipeline (mac_pipeline.py or\n"
            "android_pipeline.py) before re-running: armfit <model.pte> --mode arm\n\n"
            "Until then, use --mode dev (default) to build/test on this machine."
        )

    analyze_script = kit / "model_profiling" / "scripts" / "analyze_results.py"
    if not analyze_script.exists():
        raise RuntimeError(f"Could not find analyze_results.py under {kit}. Is ARMFIT_SME_KIT correct?")

    platform = _platform()
    model_stem = Path(model_path_str).stem
    default_run_root = kit / "model_profiling" / f"out_{model_stem}" / "runs" / platform
    run_root = Path(os.environ.get("ARMFIT_SME_RUN_ROOT", str(default_run_root)))

    off_dir = run_root / f"{platform}_sme2_off"
    on_dir = run_root / f"{platform}_sme2_on"

    off_summary = _run_analyze_if_needed(analyze_script, off_dir)
    on_summary = _run_analyze_if_needed(analyze_script, on_dir)

    baseline = _profile_from_category_totals("SME2 OFF", off_summary["category_totals_ms"])
    sme2 = _profile_from_category_totals("SME2 ON", on_summary["category_totals_ms"])
    return baseline, sme2
