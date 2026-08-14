"""Diffs the baseline (SME2 OFF) profile against the SME2 ON profile."""
from typing import Dict, List
from armfit.analysis.models import Profile, CATEGORIES


def compare(baseline: Profile, sme2: Profile) -> Dict:
    baseline_by_cat = {c.category: c for c in baseline.categories}
    sme2_by_cat = {c.category: c for c in sme2.categories}

    rows: List[Dict] = []
    for cat in CATEGORIES:
        b = baseline_by_cat.get(cat)
        a = sme2_by_cat.get(cat)
        b_ms = b.time_ms if b else 0.0
        a_ms = a.time_ms if a else 0.0
        delta_ms = round(a_ms - b_ms, 2)
        delta_pct = round(((a_ms - b_ms) / b_ms * 100.0), 1) if b_ms else 0.0
        rows.append({
            "category": cat,
            "off_ms": b_ms,
            "on_ms": a_ms,
            "delta_ms": delta_ms,
            "delta_pct": delta_pct,
        })
    rows.sort(key=lambda r: r["off_ms"], reverse=True)

    overall_speedup_pct = 0.0
    if baseline.total_time_ms:
        overall_speedup_pct = round(
            (baseline.total_time_ms - sme2.total_time_ms) / baseline.total_time_ms * 100.0, 1
        )

    top_before = max(baseline.categories, key=lambda c: c.time_ms) if baseline.categories else None
    top_after = max(sme2.categories, key=lambda c: c.time_ms) if sme2.categories else None

    return {
        "rows": rows,
        "baseline_total_ms": baseline.total_time_ms,
        "sme2_total_ms": sme2.total_time_ms,
        "overall_speedup_pct": overall_speedup_pct,
        "top_bottleneck_before": top_before.category if top_before else None,
        "top_bottleneck_after": top_after.category if top_after else None,
        "measured": baseline.measured and sme2.measured,
    }
