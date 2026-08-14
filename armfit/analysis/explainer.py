"""
Converts ranked bottlenecks + comparison data into plain-English insights.

Deliberately rule-based (no LLM) — fast, offline, deterministic, and easy
to defend to judges: every sentence traces directly back to a measured or
clearly-labeled-projected number.
"""
from typing import Dict, List


def generate(ranked_before: List[Dict], comparison: Dict) -> List[str]:
    insights: List[str] = []
    label = "measured" if comparison["measured"] else "projected (dev-mode estimate)"

    if ranked_before:
        top = ranked_before[0]
        insights.append(
            f"{top['category']} consumes {top['pct']}% of baseline runtime and is your "
            f"largest bottleneck before optimization."
        )

    before = comparison["top_bottleneck_before"]
    after = comparison["top_bottleneck_after"]
    if before and after and before != after:
        insights.append(
            f"SME2 reduced the cost of {before}, which shifted the largest remaining "
            f"bottleneck to {after}. This is a {label} comparison — investigate {after} next."
        )
    elif before and after == before:
        insights.append(
            f"{after} remains the largest bottleneck even after SME2 ({label}). "
            f"Further Arm-specific or algorithmic optimization targeting this category "
            f"would have the biggest impact."
        )

    speedup = comparison["overall_speedup_pct"]
    if speedup:
        direction = "faster" if speedup > 0 else "slower"
        insights.append(
            f"Overall latency changed by {abs(speedup)}% ({direction}) with SME2 enabled "
            f"({label}): {comparison['baseline_total_ms']} ms -> {comparison['sme2_total_ms']} ms."
        )

    # Row-level call-outs for any category that got relatively worse (a real
    # phenomenon Arm documents: shrinking compute time can expose data
    # movement as the new bottleneck).
    for row in comparison["rows"]:
        if row["delta_pct"] > 15:
            insights.append(
                f"{row['category']} grew from {row['off_ms']} ms to {row['on_ms']} ms "
                f"after SME2 ({label}) — its relative share of runtime increased and it's "
                f"now a bigger optimization target than before."
            )

    if not comparison["measured"]:
        insights.append(
            "Note: these SME2 numbers are a dev-mode projection based on Arm's published "
            "category-level speedup ranges, not a real hardware measurement. Run with "
            "--mode arm on Arm SME2-capable hardware for real numbers before the final demo."
        )

    return insights
