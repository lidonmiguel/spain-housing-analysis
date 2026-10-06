"""Reproduce demographic figures and tables without downloading data."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from spain_housing.demographics import run_analysis  # noqa: E402

if __name__ == "__main__":
    _, result = run_analysis(ROOT)
    print(result)
