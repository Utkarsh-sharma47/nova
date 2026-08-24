#!/usr/bin/env python3
"""Alias for scripts/run-extractor-eval.py (underscore form)."""

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    target = Path(__file__).with_name("run-extractor-eval.py")
    runpy.run_path(str(target), run_name="__main__")
