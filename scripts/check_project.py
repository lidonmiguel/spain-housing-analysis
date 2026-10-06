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
    print("Project metadata and notebook code are valid.")


if __name__ == "__main__":
    main()
