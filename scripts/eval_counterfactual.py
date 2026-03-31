#!/usr/bin/env python
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("analyze_counterfactual_gap.py")), run_name="__main__")

