"""Turns category totals into a ranked, human-labeled bottleneck list."""
from typing import List, Dict
from armfit.analysis.models import Profile


def _impact_label(pct: float) -> str:
    if pct >= 35:
        return "Very High"
    if pct >= 20:
        return "High"
    if pct >= 10:
        return "Medium"
    return "Low"


def rank_bottlenecks(profile: Profile) -> List[Dict]:
    """Returns categories sorted by share of runtime, richest first."""
    ranked = []
    for i, cat in enumerate(profile.categories, start=1):
        if cat.time_ms <= 0:
            continue
        ranked.append({
            "rank": i,
            "category": cat.category,
            "time_ms": cat.time_ms,
            "pct": cat.pct,
            "impact": _impact_label(cat.pct),
            "op_count": cat.op_count,
        })
    return ranked
