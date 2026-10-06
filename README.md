# Spain Housing Analysis

A reproducible Data Science project investigating housing prices, affordability,
demographics, ownership concentration and housing policy in Spain.

**Status: project foundation. No datasets have been ingested and no empirical
results or policy effects have been established yet.**

## Research question

How has access to housing changed in Spain, and how do demographic change,
housing supply, ownership and regulation relate to differences between territories?

## Scope

| Block | Focus |
| --- | --- |
| 1. Prices | Purchase and rent prices, inflation, distributions and housing characteristics |
| 2. Demographics | Total population, population aged 18+, households, migration and emancipation |
| 3. Supply and tenure | Ownership/renting, construction, vacancy, tourism and social housing |
| 4. Ownership | Owner categories, concentration and buyer composition |
| 5. Affordability | Income groups, housing expenditure, mortgage costs and entry savings |
| 6. Policy | Measure-level timelines and comparisons of prices, supply and access |

Start with province-level annual descriptive analysis. Add regional series and
municipal or neighbourhood case studies only where definitions and coverage match.
The historical window will be chosen after auditing the sources; annual, quarterly
and census observations will retain their original frequency.

## Quick start

Requires Python 3.11 or newer. Run from the repository root.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python scripts/check_project.py
python -m unittest discover -s tests -v
jupyter lab
```

Open `notebooks/00_data_audit.ipynb` first. Select the Python interpreter from
`.venv` in VS Code, or choose that environment's kernel in JupyterLab.

## Repository layout

| Path | Purpose |
| --- | --- |
| `notebooks/` | Ordered analysis notebooks with questions, inputs and figure plans |
| `src/spain_housing/` | Reusable Python code and explicit indicator formulas |
| `data/raw/` | Unmodified downloaded inputs; ignored by Git |
| `data/interim/` | Cleaning and harmonisation outputs; ignored by Git |
| `data/processed/` | Analysis-ready datasets; ignored by Git |
| `data/metadata/` | Source register, dataset manifest, variables and policy records |
| `docs/` | Research plan, methodology, hypothesis register and chart catalogue |
| `reports/figures/` | Selected figures for publication |
| `reports/tables/` | Selected summary tables |
| `scripts/` | Repository validation and notebook checks |
| `tests/` | Checks for indicator calculations |

## First working milestone

1. Audit price, rent, income, population, household and housing-completion sources.
2. Verify download access, definitions, territorial coverage, years and reuse terms.
3. Register each downloaded file with its source, retrieval date and SHA-256.
4. Harmonise geography and time while retaining original units and provenance.
5. Produce coverage, price/income evolution and households-versus-construction figures.

The complete scope and staged backlog are in [the research plan](docs/research_plan.md).
See also [methodology](docs/methodology.md), [sources](docs/sources.md),
[the chart catalogue](docs/chart_catalogue.csv) and [hypotheses](docs/hypotheses.csv).

## Interpretation

Distinguish advertised, contracted and appraised prices; housing stock, listings and
transactions; households and inhabitants; foreign nationality and non-residence.
Policy measures will be classified by mechanism, not only by political labels.
Correlation will not be presented as a causal policy effect. Missing ownership data
will remain explicitly unknown rather than being filled with unsupported estimates.

## License

Code is covered by the existing [MIT License](LICENSE). External data, geographic
boundaries and published figures derived from restricted inputs remain subject to
their own terms. Record those terms before redistributing any dataset.
