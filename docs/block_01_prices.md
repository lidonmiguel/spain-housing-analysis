# Block 01 — Housing prices in Spain: territory and political context

## Purpose

Tell a chronological, territorial narrative that helps examine competing political
accounts of housing prices. Start with national purchase/rent evolution, add the
political timeline, adjust for inflation, then examine territorial differences and
regional governments. This block is descriptive; policy effects belong to block 06.

**Status:** executed with primary-source snapshots retrieved on 2026-10-06.
[Read the numerical findings and 16 figures](../reports/block_01_prices.md) or
[open the executed notebook](../notebooks/01_prices.ipynb).
Regional bands identify the party of the presidency, not complete cabinets.
The municipal profile is a disclosed 30-municipality sample. Rental coverage starts
in 2021 for Navarra and 2024 for País Vasco. These series have no 2011–2024 rental growth.

## Reading order

| Part | Subject | Main figures |
| --- | --- | --- |
| 1.1 | National price evolution | Separate purchase and rent panels in EUR/m² and EUR/dwelling where supported. Base-100 comparison over a shared window. |
| 1.2 | National governments | The national series with dated mandate bands; annual-change bars with transition years identified. |
| 1.3 | Inflation and real growth | Purchase and rent panels comparing nominal and constant-euro prices, retaining government bands. |
| 1.4 | Territorial profiles | Price-level panels and base-100 trends by explicitly defined territorial groups. |
| 1.5 | Autonomous communities | Separate maps of levels and percentage changes for purchase and rent; annual-change heatmap. |
| 1.6 | Regional governments | Small multiples with mandate bands; descriptive mandate table and annualised-growth comparison. |
| 1.7 | Provinces and municipalities | Provincial/municipal price and growth maps plus preselected local time-series cases. |
| 1.8 | Political reading of the evidence | Evidence table by geography and mandate: nominal/real changes, annualised rates, coverage and sources. |

## 1.1 — National price evolution

**Question:** How have purchase prices and rents changed in Spain?

**Figures:** Separate purchase and rent panels in EUR/m² and EUR/dwelling where supported. Base-100 comparison over a shared window.

**Inputs:** National price/rent series with exact definitions and units.

**Narrative:** Lead with measured changes, dates and units before introducing party labels.

## 1.2 — National governments

**Question:** How did prices evolve during each national government?

**Figures:** The national series with dated mandate bands; annual-change bars with transition years identified.

**Inputs:** Verified national mandates and the same national price/rent series.

**Narrative:** Describe evolution during mandates. Include governing coalition and changes within a year.

## 1.3 — Inflation and real growth

**Question:** How much of the increase remains after adjusting for inflation?

**Figures:** Purchase and rent panels comparing nominal and constant-euro prices, retaining government bands.

**Inputs:** Documented annual CPI series and common base year.

**Narrative:** Separate nominal from real changes. Never interpret a deflated price as a household burden.

## 1.4 — Territorial profiles

**Question:** Do large cities, peripheries, coastal and inland places evolve differently?

**Figures:** Price-level panels and base-100 trends by explicitly defined territorial groups.

**Inputs:** Municipal observations and verified geography classification/aggregation weights.

**Narrative:** Urban/peripheral and coastal/inland are separate dimensions. Show composition and coverage.

## 1.5 — Autonomous communities

**Question:** Which communities are most expensive and where have prices changed most?

**Figures:** Separate maps of levels and percentage changes for purchase and rent; annual-change heatmap.

**Inputs:** Comparable community series, harmonised geography codes and licensed boundaries.

**Narrative:** Distinguish expensive places from fast-growing places. Use shared map periods and scales.

## 1.6 — Regional governments

**Question:** How did prices evolve during each regional mandate and across government changes?

**Figures:** Small multiples with mandate bands; descriptive mandate table and annualised-growth comparison.

**Inputs:** Verified regional mandates, coalition composition and comparable price observations.

**Narrative:** Compare durations and observed windows. No causal party ranking or mixed-coalition simplification.

## 1.7 — Provinces and municipalities

**Question:** What do regional averages conceal?

**Figures:** Provincial/municipal price and growth maps plus preselected local time-series cases.

**Inputs:** Local prices, coverage thresholds and boundaries compatible with observation vintages.

**Narrative:** Use all qualifying territories or declare the selection rule before inspecting results.

## 1.8 — Political reading of the evidence

**Question:** Which descriptive claims are supported and what remains unexplained?

**Figures:** Evidence table by geography and mandate: nominal/real changes, annualised rates, coverage and sources.

**Inputs:** Completed previous sections and traceable calculations.

**Narrative:** Present increases and decreases symmetrically. Causes and laws belong to later blocks.

## Comparison rules

- Keep market (purchase/rent), price concept (advertised/contracted/appraised),
  dwelling segment, unit and provider explicit. An index is not a euro price.
- A dwelling total cannot be obtained by multiplying an average EUR/m² by an
  unrelated average area. Publish only supported measures; show gaps honestly.
- Annual change: 100 × (value[t] / value[t−1] − 1), only for consecutive years.
- Cumulative change: 100 × (last / first − 1), using the same dates across territories.
- Annualised change: 100 × ((last / first) ** (1 / elapsed_years) − 1).
  Use observation elapsed time, not full mandate duration when coverage is partial.
- Constant-euro value: nominal × CPI[base] / CPI[year]. State CPI coverage/base and
  aggregation. Do not compare CPI series with incompatible rebasing.
- Base-100 comparisons require a shared observed baseline. Missing years remain
  missing; do not invent observations or let annual lines bridge gaps silently.
- Keep each presidency's exact appointment dates and party. Cabinet composition remains unverified; do not infer a complete coalition. Use half-open
  intervals [start, end). An ongoing term has an empty end, not an invented date.
- Annual averages cover a whole year: do not assign a transition year entirely to
  one party. Show the transition on the timeline; mark such years in summaries.
- Use complete within-mandate years for a conservative annual comparison; compare
  observed endpoints, expose exclusions and mark incomplete mandate coverage.
  Quarterly data may support finer windows; do not mix frequencies silently.
- Government colours must be consistent. Treat coalitions as their own labels and
  keep externally supporting parties separate from cabinet members. No forced
  left/right classification for territorial parties or mixed coalitions.
- Use one set of inclusion rules and a common observed window for party comparisons.
  Avoid pooled party averages that conflate places, periods and repeated mandates.
- Maps must include missing-data shading, year/window, units, boundary vintage and
  source; never compare unmatched years as if they were simultaneous.
- Urbanity (large city/periphery/other) and coast (coastal/inland) are separate
  attributes. Publish population/metropolitan/coast criteria and classification date.
  If pooling places, document weights and use a stable sample or report sample change.

## Deliverables

- `notebooks/01_prices.ipynb`: eight ordered sections with input and figure checklists.
- `docs/block_01_chart_catalogue.csv`: block-specific figure IDs and data dependencies.
- `data/metadata/government_register.csv`: verified mandate metadata, separate from laws.
- `data/metadata/territory_classification.csv`: urban/coastal classification provenance.
- `data/metadata/price_panel_template.csv`: long-form price observation contract.
- `data/metadata/cpi_panel_template.csv`: deflator observation contract.
- `reports/block_01_prices.md`: Executed Spanish narrative, numerical findings and figures.

## Implementation sequence

1. Audit and register national purchase/rent sources and CPI; determine shared windows.
2. Ingest original releases and build source-separated annual price/CPI panels.
3. Verify national and regional mandate dates and coalition labels from primary sources.
4. Complete parts 1.1–1.3 with audited national data before geographic extensions.
5. Build common-window regional maps and mandate panels, retaining transition flags.
6. Extend to provinces/municipalities and territorial profiles where data permits.
7. Execute the notebook from documented inputs and write the evidence-led narrative.

Do not substitute the CPI rent component for a market rent-level series without
identifying it as a distinct measure. Do not present plans or missing inputs as results.


## Ampliación histórica (6 de octubre de 2026)

El análisis histórico principal está en `notebooks/01b_price_history.ipynb` y
`reports/block_01_price_history.md`. Mantiene el informe inicial como ventana reciente.

| Medida | Serie histórica | Ventana comparable |
| --- | --- | --- |
| Tasación libre nacional, CCAA y provincias | 1995–2025 | Mismos extremos en mapas |
| Importe de transacciones, segunda mano libre | 2004–2025 | No mezclar con tasación |
| IPV de compraventa | 2007–2025 | 2011–2024 al comparar con IPVA |
| IPVA general (INE 59056) | 2011–2024 | Misma definición en toda la serie |
| Tasación de 30 municipios | 2005–2025 | Panel fijo en perfiles |
| Alquiler fiscal, m² y vivienda | 2011–2024 según territorio | Cobertura explícita |
| IPC nacional | 2002–2025 | No deflactar antes de 2002 |

Máximo precrisis: máximo observado en 1995–2008; mínimo postcrisis: mínimo en
2009–2015. No se calcula un máximo precrisis para alquileres que empiezan en 2011.
Las tablas conservan años inicial/final nominales y reales separados, años observados
y huecos. Los cambios por presidencia usan años completos dentro del intervalo,
excluyen años de transición y ofrecen variación acumulada y anualizada.


## Horizonte solicitado desde 1950

El punto de entrada nacional de largo plazo pasa a `notebooks/01c_prices_since_1950.ipynb`
y `reports/block_01_since_1950.md`. Cobertura recuperada: alquiler IPC 1961–2001 y
2002–2025; compra BIS 1971–2025. El proxy de Madrid 1975–1986 se distingue de los datos
nacionales. Se publican huecos desde 1950 y se rechazan acumulados que cruzan 2001/2002.
Las comparaciones nacionales coherentes usan ventanas 1987–2001 y 2002–2025, con base,
periodo y deflactor comunes dentro de cada ventana y escalas nominal/real idénticas.
