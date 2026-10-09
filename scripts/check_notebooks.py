"""Validate and execute notebooks in memory, without replacing saved outputs."""

import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--save", action="store_true", help="Save executed outputs after success")
args = parser.parse_args()

for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    NotebookClient(
        notebook,
        timeout=300,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT / "notebooks")}},
    ).execute()
    if args.save:
        nbformat.write(notebook, path)
    print(f"Validated and executed: {path.name}")
