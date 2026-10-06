"""Generate actual figures, numerical tables and the Spanish narrative report."""

from pathlib import Path

from spain_housing.prices_analysis import run_analysis

if __name__ == "__main__":
    figures, findings = run_analysis(Path(__file__).resolve().parents[1])
    print(f"Generated {len(figures)} figures from committed real-data snapshots.")
    print(findings)
