# ArmFit

**From profiler data to performance decisions.**

ArmFit takes an ExecuTorch `.pte` model, profiles it, ranks bottlenecks by
operator category, compares SME2 OFF vs ON execution, and explains — in
plain English — what to optimize next.

## Why this runs on your Ryzen 7

SME2 (Scalable Matrix Extension 2) is Arm-only silicon — it doesn't exist
on x86/AMD chips, so real SME2 numbers can only ever come from Arm SME2
hardware. To keep development unblocked, ArmFit ships with **two modes**:

- **`--mode dev`** (default) — runs entirely on stdlib Python, works on
  any machine including a Ryzen 7 laptop. If ExecuTorch is installed, it
  profiles your model for real on x86 (XNNPACK has no Arm dependency).
  The "SME2 ON" side is a clearly-labeled **projection**, built from Arm's
  published category-level speedup ranges — not a real measurement. This
  is what you use to build and demo the whole tool tonight.

- **`--mode arm`** — calls Arm's real `sme-executorch-profiling` workflow
  and produces genuinely **measured** SME2 ON/OFF numbers. Requires actual
  Arm SME2-capable hardware — see below.

Every report (terminal, JSON, HTML) is explicitly labeled `MEASURED` or
`PROJECTED` so you never accidentally present synthetic numbers as real
ones to judges.

## Quick start (works right now, zero install)

```bash
cd armfit-repo
python3 -m armfit demo_model.pte --serve
```

This runs the full pipeline against a placeholder model, generates
`armfit-out/armfit-report.json` and `.html`, and opens the dashboard in
your browser at `http://127.0.0.1:8765/armfit-report.html`.

Or without the dashboard:

```bash
python3 -m armfit demo_model.pte
# or
python3 armfit_cli.py demo_model.pte
```

## Using a real model

```bash
python3 -m armfit /path/to/my_model.pte --mode dev --serve
```

If `executorch` is installed (`pip install executorch torch`), ArmFit will
attempt a real profiling run on your baseline (see
`armfit/runner/executorch_runner.py::_try_real_run` — this is a stub you
need to wire to your ExecuTorch version's Inspector API). Otherwise it
falls back to a deterministic synthetic profile seeded from the model file,
so the rest of the pipeline is fully testable either way.

## Getting REAL SME2 numbers

You need actual Arm SME2-capable hardware. Options, cheapest first:

1. **AWS Graviton4 EC2 instance** — Arm's own ExecuTorch 1.0 benchmarks
   were run on Graviton4 with SME2 via KleidiAI, so this is a known-good,
   judge-defensible environment. Spin one up, `git clone` this repo there.
2. A recent flagship Android phone (Cortex-X4 / Arm C1-class chip).

Then:

```bash
git clone https://github.com/ArmDeveloperEcosystem/sme-executorch-profiling
export ARMFIT_SME_REPO=/path/to/sme-executorch-profiling
python3 -m armfit my_model.pte --mode arm --serve
```

`armfit/runner/arm_sme2_runner.py::run_arm` has a `TODO` where you wire in
the actual calls to that repo's scripts and parse its ETDump/CSV output —
this is intentionally left as your Hour 0–2 "kill switch" task from the
project plan: prove `.pte → Arm profiling repo → SME2 ON/OFF → ETDump →
CSV/JSON` works manually first, then port the parsing logic in.

## Project layout

```
armfit/
  cli.py                        # argument parsing, orchestrates the pipeline
  runner/
    executorch_runner.py        # baseline (SME2 OFF) profiling — real + synthetic fallback
    arm_sme2_runner.py          # SME2 ON side — dev-mode projection + real arm-mode hook
  analysis/
    models.py                   # OperatorStat / CategoryTotal / Profile dataclasses
    ranker.py                   # bottleneck ranking + impact labels
    comparator.py                # OFF vs ON diffing
    explainer.py                 # rule-based plain-English insights
  report/
    export.py                    # JSON + self-contained HTML report writer
    template.py                   # HTML/CSS template (no external assets/CDN)
  dashboard/
    serve.py                      # tiny local HTTP server for the HTML report
demo_model.pte                    # placeholder model so the CLI runs out of the box
armfit_cli.py                     # convenience root-level entry point
```

No React, no FastAPI, no npm install, no CDN calls — matches the project
plan's rule: "don't waste time on a huge frontend, a polished local
dashboard is enough." Swap in the FastAPI+React stack later only if you
have time to spare.

## MVP checklist (from the project plan)

- [x] Accept an ExecuTorch `.pte` model
- [x] Run the profiling workflow (real on real HW, synthetic fallback elsewhere)
- [x] Parse runtime/operator statistics
- [x] Rank the largest bottlenecks
- [x] Compare SME2 OFF vs ON
- [x] Generate a clear, developer-friendly performance report (JSON + HTML)
