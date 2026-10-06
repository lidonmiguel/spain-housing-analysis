# Research plan

## Objective and boundaries

Study housing in Spain through six connected empirical blocks. The full scope is a
research backlog, not a claim that every dataset is obtainable. Begin with a
province-level annual panel where possible and targeted local cases where needed.

## Prices and political context — first narrative block

Follow [the eight-part block specification](block_01_prices.md):

1. National purchase/rent evolution and base-100 comparison.
2. National government mandates over the same time series.
3. Nominal and inflation-adjusted prices.
4. Large-city/periphery and coastal/inland profiles.
5. Autonomous-community price and growth maps.
6. Regional mandate panels and comparable annualised changes.
7. Provincial and municipal maps and predefined local cases.
8. Evidence-led political reading, explicitly separated from policy causality.

The specification includes formulas, coalition handling, transition-year rules,
data contracts and a chart catalogue. New/used segments, source differences and
composition diagnostics remain supporting checks when data permits.

## Population and households

- Total and age-18+ population; age structure, emancipation and cohabitation.
- Household count and size; internal/external migration; employment geography.
- Dwellings per 1,000 inhabitants/adults/households with explicit denominators.
- Net household formation versus housing completions; geographic mismatch.

## Supply and tenure

- Main, secondary and vacant dwellings; location and habitability of vacant stock.
- Households in ownership, rent and free use; counts and shares over time.
- Sales and rental listings versus actual transactions; listing duration and turnover.
- Long-term, seasonal, room and tourist rental; public/social housing coverage.
- Permits, starts, completions, completion lags, licensing delays, land and building costs.

## Ownership and concentration

- Natural/legal persons; identified corporate subtypes; enterprise and portfolio size.
- Shares of owners, dwellings and annual purchases; national versus local concentration.
- Resident/non-resident buyers separately from nationality.
- Adjusted rents by owner category where property characteristics are available.
- Explicit coverage gaps; no invented fund/SME ownership shares.

## Affordability

- Rent/income and purchase-price/income with consistent households, years and units.
- Actual burden distributions and differences by income group, age and tenure.
- Mortgage scenarios at constant property characteristics; down payment and saving scenarios.
- Associations with employment, population, households, income and housing availability.

## Policy evaluation

- Measure-level legal timeline; effective dates, territories, implementation and repeal.
- Classify rent, land, tax, supply and tenure mechanisms; mixed measures allowed.
- Prior trends and comparable untreated territories; post-policy observation window.
- Price, contracts, supply, construction and displacement between rental modalities.
- Separate arrears, occupation, court duration and perceived risk.
- Causal design only if feasible; uncertainty, placebo and robustness checks.

## Modelling and synthesis

Use notebook 07 for clustering and regression only after the core audit and EDA.
Use notebook 08 for the final hypothesis review. Policy evaluation has its own
identification requirements and is not equivalent to predictive modelling.

## Milestones

- [ ] M0: source feasibility audit, coverage matrix and confirmed definitions.
- [ ] M1: reproducible ingestion for prices, rent, income, population, households and completions.
- [x] M2: block 01 completed with 16 figures, numerical tables and an executed notebook (2026-10-06).
- [ ] M2b: demographics and households-versus-construction figures (C02, C04).
- [ ] M3: tenure, affordability and selected local tourism/vacancy cases.
- [ ] M4: ownership feasibility decision; analyse only supported categories and scales.
- [ ] M5: verified policy timeline and feasibility assessment for comparative evaluation.
- [ ] M6: modelling, robustness, hypothesis synthesis and selected portfolio figures.

## Completion criteria

Each empirical notebook runs from documented inputs with no hidden manual state.
Every finding identifies geography, years, definitions and limitations. Every
published figure has a source and units. Missing-data and source sensitivity are
reported. Unsupported questions are marked insufficient evidence. The README is
updated with actual findings only when results exist.

Block 01 ingestion and coverage are complete for the documented series. Full M0/M1
remain open because income, demography and completions belong to subsequent blocks.
