# Notebook workflow

Run notebooks in numerical order after environment setup. Notebook 00 audits
coverage before any analysis. The templates contain no results and do not download
data. Blank analysis sections are intentional. Reusable transformations belong in
`src/spain_housing/`; notebooks explain questions, choices, figures and findings.

Each notebook includes a root-discovery cell that works from either the project
root or this directory. Restart the kernel and Run All before committing completed
analysis; ensure every chart has units, source and territorial/temporal coverage.
Keep large intermediate tables in ignored data directories and commit selected
small outputs only after checking reuse terms.

Check notebook structure and execute the current templates with:

```bash
python scripts/check_notebooks.py
```

## Block 01: narrative workflow

`01_prices.ipynb` follows the eight sections in `docs/block_01_prices.md`.
It reads the price/CPI schemas and government/classification registers to show
readiness. Missing inputs are reported explicitly; no political values are invented.
Use `reports/block_01_prices.md` to write the Spanish narrative after analysis.
