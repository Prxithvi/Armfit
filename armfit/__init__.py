"""
ArmFit — from profiler data to performance decisions.

This package is intentionally dependency-free (stdlib only) so it runs
on ANY machine, including non-Arm dev laptops (Ryzen, Intel, etc).

Two run modes:

  --mode dev   Works everywhere, including x86 (Ryzen 7). Runs the model
               through ExecuTorch/XNNPACK if available, otherwise falls
               back to a deterministic synthetic profile. The "SME2 ON"
               side is a clearly-labeled PROJECTION based on Arm's
               published category-level speedup ranges — not a real
               measurement. Use this to build/demo the tool end-to-end
               tonight without needing Arm hardware.

  --mode arm   Requires real Arm SME2-capable hardware (e.g. AWS
               Graviton4, a recent Cortex-X4/C1-class Android device).
               Produces genuinely measured SME2 ON/OFF numbers via
               Arm's sme-executorch-profiling workflow. This is what
               you run once, right before recording the demo.
"""

__version__ = "0.1.0"
