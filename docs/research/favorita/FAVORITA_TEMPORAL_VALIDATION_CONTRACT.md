# Favorita Temporal Validation Contract

| Field | Value |
|---|---|
| Status | Active executable temporal-boundary contract |
| Target | `unit_sales` |
| Forecast origin | End of calendar day `t` |
| Supported horizon | Exact integers 1 through 16 |
| Strategy | Direct horizon-aware global forecasting |
| Validation design | Eight expanding-window folds |
| Final holdout origin | `2017-07-30` |
| Final holdout dates | `2017-07-31` through `2017-08-15` |

## 1. Purpose and boundary

This document is the current source of truth for Favorita forecast-horizon semantics, temporal validation boundaries, training-label eligibility, fold separation, leakage protection, bounded feature evidence, and final holdout protection.

It consolidates the completed 16-day horizon alignment and the executable temporal-validation definition. It does not claim that a forecasting model was trained, a model backtest ran, metrics were compared, a model was selected, or the final holdout was scored.

Related authorities:

- [Favorita Dataset Source and Governance](../../governance/FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md);
- [Favorita Temporal Validation Design](FAVORITA_TEMPORAL_VALIDATION_DESIGN.md);
- [Favorita Forecasting Evaluation Metric Contract](FAVORITA_FORECASTING_EVALUATION_METRICS.md); and
- [EDIP Architecture Plan](../../architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md).

## 2. Forecast contract

The active contract is:

- supervised target: `unit_sales`;
- prediction origin: end of calendar day `t`;
- `forecast_horizon`: the number of calendar days between the origin and target date;
- allowed horizons: exact integers 1 through 16;
- target-date equation: `forecast_date = forecast_origin + forecast_horizon days`;
- supported target dates: `t+1` through `t+16`;
- forecast strategy: direct horizon-aware global forecasting;
- recursive use of an earlier prediction as a later-horizon input: forbidden;
- historical features: information available at or before the example's forecast origin;
- future actual sales, transactions, and oil: forbidden inputs;
- sparse source semantics: absent store-item-date rows are not created or interpreted as zero demand.

Sixteen is the **maximum supported horizon**, not the minimum number of predictions every consumer must use. A shorter operational horizon of `N` days consumes the first `N` ordered predictions, for `1 <= N <= 16`, without redefining or retraining a recursive chain.

The official unlabelled competition inference dates are `2017-08-16` through `2017-08-31`, which motivates the maximum 16-day contract. Kaggle `test.csv` has no `unit_sales` and is not local metric evidence.

## 3. Feature-time and direct-strategy rules

For an example with origin `t` and horizon `h`:

- historical sales lags and rolling windows end at or before `t`;
- historical transaction and oil features use observations available at or before `t`;
- deterministic target-date calendar features may be derived for `t+h`;
- target-date promotion or holiday features require proof that the planned/published value was available at `t`;
- future actual outcomes are never model inputs;
- predictions for horizons 1 through `h-1` do not feed horizon `h`.

Historical values such as lag 14 and rolling mean 14 remain valid lookbacks. They do not define the maximum forecast horizon.

Generated examples include `forecast_origin`, `forecast_date`, and `forecast_horizon` as audit keys. The eventual estimator's precise encoding of horizon remains a modeling decision, but the end-to-end method must remain direct and horizon-aware.

## 4. Approved fold contract

| Fold | Forecast origin | Validation start | Validation end |
|---:|---|---|---|
| 1 | `2015-08-31` | `2015-09-01` | `2015-09-16` |
| 2 | `2015-12-08` | `2015-12-09` | `2015-12-24` |
| 3 | `2016-04-15` | `2016-04-16` | `2016-05-01` |
| 4 | `2016-06-30` | `2016-07-01` | `2016-07-16` |
| 5 | `2016-08-31` | `2016-09-01` | `2016-09-16` |
| 6 | `2016-12-08` | `2016-12-09` | `2016-12-24` |
| 7 | `2017-04-15` | `2017-04-16` | `2017-05-01` |
| 8 | `2017-06-30` | `2017-07-01` | `2017-07-16` |

The executable fold contract requires:

- exactly eight folds with identifiers 1 through 8;
- strictly increasing origins;
- `validation_start = origin + 1 day`;
- `validation_end = origin + 16 days`;
- exactly 16 inclusive calendar dates in each window;
- no overlap between validation windows; and
- every validation window ending before the final holdout.

Only canonical origins need to be stored; validation starts and ends should be derived through the shared 1-through-16 horizon function.

## 5. Expanding-window training-label eligibility

For fold origin `O`, a training example is eligible only when:

```text
forecast_date <= O
```

An earlier example origin alone is insufficient because its labelled target may still occur after `O`.

Each fold is a **separate fit**:

1. select eligible historical examples through `O`;
2. fit preprocessing and the estimator using that fold's training data only;
3. freeze learned state;
4. produce direct predictions for `O+1` through `O+16`;
5. join hidden validation outcomes only after prediction; and
6. score and preserve fold lineage separately.

A later fold may train on an earlier validation period only after that period is historical relative to the later origin.

## 6. Leakage protections

The contract blocks:

1. random row train/validation splitting;
2. training labels after the fold origin;
3. overlapping validation windows;
4. validation overlap with the final holdout;
5. future actual `unit_sales`, transactions, or oil as inputs;
6. reuse of features constructed at a later origin;
7. preprocessing, encoders, vocabularies, feature selection, or thresholds fitted on validation rows;
8. validation-informed entity selection;
9. duplicate examples at `(forecast_origin, forecast_date, store_nbr, item_nbr)`;
10. recursive prediction feedback;
11. densification or inferred zero demand for absent sparse rows; and
12. use of final holdout outcomes for design, tuning, or model selection.

Promotion and holiday target-date inputs remain governed by as-of-origin publication evidence. This contract does not expand their availability assumptions.

## 7. Final untouched holdout

The protected holdout is:

- origin: `2017-07-30`;
- target start: `2017-07-31`;
- target end: `2017-08-15`;
- duration: 16 calendar days.

The latest validation window ends on `2017-07-16`, leaving `2017-07-17` through `2017-07-30` outside approved validation windows.

The holdout remains unavailable for model selection, preprocessing decisions, metric policy, threshold selection, hyperparameter tuning, sensitivity-design selection, or workflow tuning. Scoring requires a separately approved later work item after all such decisions are frozen.

## 8. Bounded current smoke evidence

The executed model-ready feature smoke build records:

| Property | Verified value |
|---|---|
| Scope | `bounded_real_data_smoke_only` |
| Forecast origin | `2017-07-30` |
| Forecast-date minimum | `2017-07-31` |
| Forecast-date maximum | `2017-08-15` |
| Exact horizons | Integers 1 through 16 |
| Rows | 548 sparse observed target rows |
| Columns | 43 |
| Parquet row groups | 1 |
| Duplicate output keys | 0 |
| Smoke Parquet SHA-256 | `003aed5ef8120b0199aad3c61b953cc04c2b2174d702ce2b8ecbfe5f71f4550f` |
| Smoke manifest SHA-256 | `ae0995f8cfe691115b3ae36a4e3484063cbda7a1b9e88b7358b2a115e048d3d8` |

The 548 rows are observed sparse targets, not a dense 50-item by 16-day panel. Missing combinations were not created and were not interpreted as zero sales.

The manifest and Parquet evidence agree on ordered schema, row/column counts, origin, date range, exact horizon set, duplicate count, forbidden-column checks, and training/inference schema parity.

## 9. Source immutability evidence

Before smoke execution, the cleaned Parquet was 723,900,039 bytes with SHA-256:

`845b435622fc4fb31c5336fb1f6eda22195f64edba61a0de813e94f831c626e4`

The bounded build rechecked footer/schema, file size, modification time, and SHA-256 after execution. All comparisons passed, and the manifest recorded `mutated: false`.

The smoke build used the final holdout date boundary only to validate feature construction and contract coverage. It did not fit a model, select a method, calculate a metric, or score holdout outcomes.

## 10. Executable boundary

The current implementation provides deterministic structures and functions that:

- derive target windows from the canonical horizons;
- enforce the exact ordered horizon tuple 1 through 16;
- validate the forecast-date equation;
- validate fold identifiers, chronology, duration, and non-overlap;
- determine training-label eligibility;
- reject a post-origin training target;
- build the canonical eight fold datasets from the approved boundaries;
- require a fresh model-agnostic adapter and target-free prediction inputs for each fold;
- validate prediction counts, finiteness, audit-key alignment, and unique validation keys;
- provide a reusable fold-local global LightGBM adapter with training-only categorical state, native missing-value handling, and the approved direct-horizon feature contract;
- calculate SCRUM-17 metrics per fold, per horizon, and from pooled row-level evidence;
- validate the exact holdout dates and separation; and
- validate the canonical contract on demand.

The current executed temporal-definition notebook demonstrates these date and leakage boundaries without reading or rebuilding the full Favorita dataset.

## 11. Explicit later work

This contract does **not** complete:

- full-data LightGBM, naive, statistical, or alternative-model training runs;
- full-data expanding-window model fits or prediction runs;
- persisted full-data backtest evidence and metric reporting;
- full-data preprocessing and model-input materialization;
- entity eligibility and population policy;
- model comparison or selection;
- hyperparameter tuning;
- uncertainty evaluation;
- final holdout scoring;
- Kaggle prediction or submission; or
- model serving and Azure deployment.

Those activities require separate approved Jira/SCRUM work items and must consume this contract without weakening its training cutoff, fold isolation, direct 1-through-16 horizon semantics, sparse-row policy, or holdout protection.

## 12. Change discipline

If a future approved decision changes the horizon, folds, or holdout, update the canonical definitions, derived assertions, focused tests, research design, and this current contract together.

Do not globally replace numeric values. Preserve legitimate historical lag/window features and use Git history, rather than active documentation, for superseded intermediate alignment records.
