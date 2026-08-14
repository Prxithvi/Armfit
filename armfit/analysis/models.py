"""Core data structures shared across the ArmFit pipeline."""
from dataclasses import dataclass, field
from typing import List

# The operator categories ArmFit groups everything into. Kept small and
# developer-readable on purpose — this is the "human explanation" layer,
# not a raw op dump.
CATEGORIES = [
    "Conv2D",
    "GEMM/Linear",
    "Elementwise",
    "Normalization",
    "DataMovement",
    "Other",
]

# Maps category names produced by Arm's real sme-executorch-profiling
# analyze_results.py (see _categorize_op in that repo) onto ArmFit's own
# category names. Arm's tool never emits "Normalization" (batch/layer norm
# ops fall through to "Other" there) -- that's a real gap in their
# categorizer, not a bug in this mapping, so it's left legitimately at 0
# rather than guessed.
ARM_REAL_CATEGORY_MAP = {
    "Convolution": "Conv2D",
    "GEMM": "GEMM/Linear",
    "Data Movement": "DataMovement",
    "Elementwise": "Elementwise",
    "Other": "Other",
}


@dataclass
class OperatorStat:
    name: str          # e.g. "aten::convolution.default"
    category: str       # one of CATEGORIES
    time_ms: float


@dataclass
class CategoryTotal:
    category: str
    time_ms: float
    pct: float          # percentage of total runtime
    op_count: int


@dataclass
class Profile:
    """A single execution's full profile (either baseline or SME2)."""
    label: str                      # "SME2 OFF" or "SME2 ON"
    measured: bool                  # True only for real --mode arm runs
    total_time_ms: float
    operators: List[OperatorStat] = field(default_factory=list)
    categories: List[CategoryTotal] = field(default_factory=list)


def aggregate_categories(operators: List[OperatorStat], total_time_ms: float) -> List[CategoryTotal]:
    """Roll up individual operator timings into category totals."""
    buckets = {cat: {"time_ms": 0.0, "count": 0} for cat in CATEGORIES}
    for op in operators:
        cat = op.category if op.category in buckets else "Other"
        buckets[cat]["time_ms"] += op.time_ms
        buckets[cat]["count"] += 1

    totals = []
    for cat, agg in buckets.items():
        pct = (agg["time_ms"] / total_time_ms * 100.0) if total_time_ms else 0.0
        totals.append(CategoryTotal(category=cat, time_ms=round(agg["time_ms"], 2),
                                     pct=round(pct, 1), op_count=agg["count"]))
    totals.sort(key=lambda c: c.time_ms, reverse=True)
    return totals
