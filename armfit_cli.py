#!/usr/bin/env python3
"""Convenience wrapper so you can run `python armfit_cli.py demo_model.pte`
instead of `python -m armfit demo_model.pte`. Identical behavior."""
from armfit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
