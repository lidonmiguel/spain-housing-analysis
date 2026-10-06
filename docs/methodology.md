# Methodology and interpretation

## Observation design

Begin with province × year wherever actual source coverage supports it. Retain
municipal and regional datasets separately before aggregation. Record official
geographic codes as strings (including leading zeros), geography level, year or
period, unit, source and observation status. Never join different geographic levels
by name or silently repeat a regional value across municipalities.

Housing stock, household tenure, advertisements and annual transactions describe
different quantities. Population aged 18+ is an indicator, not a count of households
needing an independent dwelling. Migration is a flow; nationality and residency
are distinct attributes. Household formation may also reflect changes in household size.

## Harmonisation and missingness

Audit source frequency, definitions, sample changes and geographic boundaries.
Do not invent yearly census observations. Keep missing values missing, distinguish
suppression from absence and document coverage. Any interpolation or imputation
must be flagged and excluded from the main empirical estimates unless justified.
Do not assume missing ownership categories have zero share. Preserve raw inputs.

## Prices and affordability

Keep advertised, contracted and appraised prices distinct. Report median and
quantiles where the source supports them; do not infer distributions from averages.
Separate euros per dwelling and euros per square metre. Convert nominal prices
using one documented CPI series and base period. Examine listing composition.

- Aggregate rent/income indicator: 12 × monthly rent / annual net household income.
  A ratio of territory-level averages is NOT the average household burden.
- Actual expenditure distributions require matched household-level expenditure and
  income, accounting for survey weights and the source's expenditure definition.
- Purchase-price/income ratio uses the total price and annual household income;
  label income as net or gross. It is not a mortgage-payment burden.
- Mortgage scenarios specify down payment, principal, rate and term; taxes,
  transaction costs, fees and insurance are separate assumptions.
- Households versus completions is a pressure indicator, not a complete housing
  deficit: existing stock, location, demolitions and changes of use also matter.

## Ownership

Separate legal personality, entity subtype, enterprise size and portfolio size.
A company is not automatically a fund; a non-resident is not automatically a foreign
national. Report shares of owners, dwellings and purchases with explicit denominators.
Adjust comparisons for location, size and condition where possible. Do not claim
national ownership shares from a non-representative local sample.

## Policy evaluation

Record the actual legal text, mechanism, affected territories, adoption date,
effective date, implementation, amendments and repeal. Classify each measure by
what it constrains or facilitates (rent, land, tax, supply or tenure security);
allow mixed effects and do not assign one ideology label to an entire law.

Pre/post charts are descriptive. Causal work requires a defensible counterfactual,
pre-treatment trends, sufficient observations and attention to anticipation,
spillovers and concurrent shocks. Consider difference-in-differences or event
studies only when assumptions are supportable; staggered policies require an
appropriate estimator rather than a naive pooled comparison. Report uncertainty,
placebo checks and sensitivity. Short post-policy coverage may only support monitoring.

Occupation without a contract, rent arrears, court cases and perceived risk are
separate measures. Changes in listings do not alone establish owners' motivations.

## Modelling

Start with interpretable baselines. Choose a documented target and observation unit.
For prediction, evaluate on future periods and/or held-out territories as appropriate;
fit preprocessing inside training folds, check leakage and compare to simple baselines.
Report MAE, residuals and errors by geography. Account for spatial and temporal
structure when estimating associations. Regression coefficients are not causal by default.
For clustering, scale features, assess stability and describe sensitivity to variables,
missingness and the number of clusters. Cluster labels are analytical descriptions.

## Reporting

Every figure includes geography, period, units, source and denominator where relevant.
Show uncertainty when estimated, publish comparable source definitions, and state
whether findings are descriptive, adjusted associations or causal estimates.
Hypothesis outcomes: supporting evidence, opposing evidence, mixed or insufficient.
Code licensing does not override external data or boundary reuse terms.
