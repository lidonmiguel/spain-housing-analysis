"""Generate the extended histories, figures, tables and report from snapshots."""

from pathlib import Path

from spain_housing.price_history import run_history

if __name__ == "__main__":
    figures, findings = run_history(Path(__file__).resolve().parents[1])
    print(f"Generated {len(figures)} historical figures.")
    print(findings)
