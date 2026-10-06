"""Reproduce the 1950 horizon with the longest verified histories and declared gaps."""

from pathlib import Path

from spain_housing.long_history import run_long_history

if __name__ == "__main__":
    figures, results = run_long_history(Path(__file__).resolve().parents[1])
    print(f"Generated {len(figures)} figures.")
    print(results.to_string(index=False))
