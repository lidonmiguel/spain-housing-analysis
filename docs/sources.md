# Source discovery and audit

The register contains **candidate providers**, not verified downloadable datasets.
Dataset IDs, exact downloads, coverage and licenses must be audited before ingestion.
No data has been downloaded. Use primary documentation for statistical definitions;
use party statements to attribute arguments, not to establish empirical findings.

| Candidate provider | Proposed use | Access point |
| --- | --- | --- |
| INE | Population, ages, migration, households, census housing, income, CPI and price indices | https://www.ine.es/ |
| Ministry responsible for housing | Appraised values, rental statistics, stock, construction and social housing | https://www.mivau.gob.es/ |
| Banco de España | Financing series and housing research | https://www.bde.es/ |
| Eurostat | Harmonised affordability and tenure comparisons | https://ec.europa.eu/eurostat/ |
| Registradores | Buyer categories, transactions and geographic indicators if accessible | https://www.registradores.org/ |
| Consejo General del Notariado | Transactions and buyer indicators if accessible | https://www.notariado.org/ |
| BOE and regional official gazettes | Legal texts, effective dates and amendments | https://www.boe.es/ |
| Regional/municipal open-data portals | Local rental, tourism, supply and boundary case studies | Verify each portal |
| Property portals | Advertised prices, listings and duration only with suitable access and reuse terms | Verify provider |

For ownership by funds, financial entities, SMEs and portfolio size, investigate
feasibility before promising nationwide coverage. Transaction categories are not
ownership-stock categories. Some information may only be local, aggregated,
restricted or unavailable. Do not scrape or redistribute inputs by default.

## Register workflow

1. Update `source_register.csv` with the exact dataset URL and audited coverage.
2. Record definitions, geography, years/frequency, license URL and access method.
3. Save approved downloads unchanged under `data/raw/<source_id>/`.
4. Add each download to `dataset_manifest.csv` with retrieval UTC time, relative
   path, SHA-256, release/vintage, coverage and license.
5. Document variables in `variable_dictionary.csv`; build a coverage matrix in notebook 00.
6. Keep a timestamped source snapshot so later provider updates are distinguishable.
