"""Check project metadata and notebook syntax without downloading any data."""

import csv
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    with (ROOT / "pyproject.toml").open("rb") as stream:
        tomllib.load(stream)
    for path in [ROOT / "data/metadata", ROOT / "docs"]:
        for file in path.glob("*.csv"):
            with file.open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
                    raise ValueError(f"Invalid CSV header: {file}")
                for row in reader:
                    if None in row or any(value is None for value in row.values()):
                        raise ValueError(f"Invalid CSV row: {file}")
    for file in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = json.loads(file.read_text(encoding="utf-8"))
        if notebook["nbformat"] != 4:
            raise ValueError(f"Unsupported notebook format: {file}")
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), str(file), "exec")
    for catalogue in (ROOT / "docs").glob("block_*_chart_catalogue.csv"):
        block = catalogue.name.split("_")[1]
        with catalogue.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        title_column = "title" if "title" in rows[0] else "figure_id"
        titles = [row[title_column] for row in rows]
        if len(titles) != len(set(titles)):
            raise ValueError(f"Duplicate figure in {catalogue}")
        for row in rows:
            if row.get("status", "executed") == "executed":
                filename = f"{row[title_column]}.png"
                figure = ROOT / "reports/figures" / f"block{block}" / filename
                if not figure.is_file():
                    raise ValueError(f"Missing published figure: {figure}")
        findings = ROOT / "reports/tables" / f"block{block}" / "findings.json"
        counts = json.loads(findings.read_text(encoding="utf-8"))
        if "figure_count" in counts and counts["figure_count"] != len(rows):
            raise ValueError(f"Figure count does not match catalogue: {catalogue}")
    print("Project metadata and notebook code are valid.")


if __name__ == "__main__":
    main()
