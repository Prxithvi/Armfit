"""
Produces the BASELINE (SME2-OFF-equivalent) operator profile for a .pte model.

Two paths:

1. REAL RUN  — if the `executorch` python package is importable, we attempt
   to actually load and profile the model via ExecuTorch's Inspector API.
   This works on x86 too (XNNPACK has no Arm dependency) — you just won't
   get SME2 acceleration on the "ON" side later.

   >>> THIS IS THE INTEGRATION POINT <<<
   Wire your real ExecuTorch Inspector / ETDump parsing code into
   `_try_real_run()`. It's stubbed out here because the exact API depends
   on your installed ExecuTorch version.

2. SYNTHETIC FALLBACK — if ExecuTorch isn't installed, or the real run
   fails/is not wired up yet, we generate a deterministic, realistic-looking
   operator profile so the rest of ArmFit (ranking, comparison, reporting,
   dashboard) is fully testable on ANY machine, including a Ryzen 7 laptop
   with nothing installed.

   The synthetic profile is seeded from the model file's contents, so the
   same .pte always produces the same numbers.
"""
import hashlib
import random
from pathlib import Path
from typing import List, Optional

from armfit.analysis.models import OperatorStat, Profile, aggregate_categories, CATEGORIES

# Representative operator names per category (based on typical ExecuTorch /
# aten op names you'd see in a real ETDump).
OP_POOL = {
    "Conv2D": ["aten::convolution.default", "aten::_convolution.default"],
    "GEMM/Linear": ["aten::addmm.default", "aten::mm.default", "aten::linear.default"],
    "Elementwise": ["aten::relu.default", "aten::add.Tensor", "aten::mul.Tensor", "aten::gelu.default"],
    "Normalization": ["aten::batch_norm.default", "aten::layer_norm.default", "aten::_native_batch_norm_legit.default"],
    "DataMovement": ["aten::view_copy.default", "aten::permute_copy.default", "aten::cat.default", "aten::to_copy.default"],
    "Other": ["aten::clone.default", "aten::dropout.default", "aten::empty.memory_format"],
}

# Rough default category share of total runtime for a CNN-ish mobile model,
# matching the shape of Arm's own published examples. Jittered per-model.
DEFAULT_SHARE = {
    "Conv2D": 0.417,
    "DataMovement": 0.234,
    "GEMM/Linear": 0.151,
    "Elementwise": 0.112,
    "Normalization": 0.06,
    "Other": 0.026,
}


def _seed_from_file(model_path: Path) -> int:
    h = hashlib.md5()
    try:
        h.update(model_path.read_bytes()[:65536])
    except Exception:
        h.update(str(model_path).encode())
    h.update(str(model_path.stat().st_size if model_path.exists() else 0).encode())
    return int(h.hexdigest()[:8], 16)


def _try_real_run(model_path: Path) -> Optional[List[OperatorStat]]:
    """Attempt a real ExecuTorch profiling run. Returns None if unavailable."""
    try:
        import executorch  # noqa: F401
    except ImportError:
        return None

    # TODO(team): wire real ExecuTorch Inspector API here, e.g.:
    #   from executorch.devtools import Inspector
    #   inspector = Inspector(etdump_path=..., etrecord_path=...)
    #   for event in inspector.event_blocks: ...
    # Left unimplemented on purpose — depends on your ExecuTorch version
    # and how you export the .pte. Falls back to synthetic until wired up.
    return None


def _synthetic_run(model_path: Path) -> List[OperatorStat]:
    seed = _seed_from_file(model_path)
    rng = random.Random(seed)

    total_time_ms = rng.uniform(180.0, 320.0)

    # Jitter the default category shares +/-15%, then renormalize to 100%.
    shares = {}
    for cat, base in DEFAULT_SHARE.items():
        shares[cat] = max(0.005, base * rng.uniform(0.85, 1.15))
    share_sum = sum(shares.values())
    shares = {cat: v / share_sum for cat, v in shares.items()}

    operators: List[OperatorStat] = []
    for cat in CATEGORIES:
        cat_time = total_time_ms * shares[cat]
        pool = OP_POOL[cat]
        n_ops = rng.randint(2, min(4, len(pool)))
        chosen = rng.sample(pool, n_ops)
        weights = [rng.uniform(0.4, 1.0) for _ in chosen]
        wsum = sum(weights)
        for name, w in zip(chosen, weights):
            operators.append(OperatorStat(name=name, category=cat, time_ms=round(cat_time * (w / wsum), 3)))

    return operators


def run(model_path_str: str, mode: str) -> Profile:
    model_path = Path(model_path_str)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            f"(Tip: for a quick test run, use the bundled demo_model.pte)"
        )

    operators = _try_real_run(model_path)
    measured = operators is not None
    if operators is None:
        operators = _synthetic_run(model_path)

    total_time_ms = round(sum(op.time_ms for op in operators), 2)
    categories = aggregate_categories(operators, total_time_ms)

    return Profile(
        label="SME2 OFF",
        measured=measured,
        total_time_ms=total_time_ms,
        operators=operators,
        categories=categories,
    )
