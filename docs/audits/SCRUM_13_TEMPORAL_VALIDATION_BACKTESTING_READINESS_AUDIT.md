# SCRUM-13 Temporal Validation and Backtesting Readiness Audit

> **Historical pre-alignment evidence - not the current 16-day design**
>
> This document records the repository's pre-alignment 14-day state. Its 14-day horizon, fold candidates, counts, and recommendations are retained as historical evidence and must not be silently reinterpreted as current decisions. All horizon-dependent recommendations in this document are superseded by the approved 16-day contract first recorded in `docs/audits/SCRUM_13_16_DAY_HORIZON_NOTEBOOK_ALIGNMENT_AUDIT.md` and completed in `docs/audits/SCRUM_13_16_DAY_HORIZON_COMPLETION_AUDIT.md`. This readiness audit must not be interpreted as the current approved 16-day SCRUM-13 design.

| Field | Value |
|---|---|
| Audit date | 2026-08-14 |
| Branch | `feature/scrum-13-temporal-validation-backtesting` |
| Work item | SCRUM-13 — Define temporal validation and backtesting |
| Audit status | Readiness audit complete; implementation not started |

## Executive summary

The repository contains enough confirmed policy, schema, lineage, and bounded real-data evidence to design SCRUM-13, but it does not yet contain an implemented or executed temporal backtesting system. The implemented Favorita feature contract is a direct, horizon-aware 14-day forecasting contract: an end-of-day forecast origin predicts observed target rows from the following 14 calendar days, with `unit_sales` as the training target and with inference schema parity apart from that target.

Only the bounded smoke-scale model-ready feature artifact is currently available. It contains 478 rows for store 1, 50 items, one forecast origin (`2017-07-31`), and horizons 1–14. The planned full-scale model-ready feature Parquet and full feature manifest are absent. The cleaned source-derived Parquet is available and its manifest records 125,497,040 rows from `2013-01-01` through `2017-08-15`, but that cleaned dataset is not itself a model-ready backtesting artifact.

SCRUM-13 is ready for a design approval step, not for a claim of backtesting, production readiness, or research readiness. Decisions about fold origins, holdout policy, negative-target evaluation, entity eligibility, preprocessing, feature availability at the operational cutoff, output evidence, and compute budgets must be approved before implementation.

## Audit objective, scope, and non-scope

### Objective

Establish repository-backed evidence needed to design leakage-safe temporal validation and rolling-origin backtesting for the real Kaggle Corporación Favorita forecasting workflow.

### Scope

The audit reviewed the current project and architecture direction, the SCRUM-11 feature policy, the SCRUM-12 model-ready feature implementation, unit tests, manifests, saved notebook evidence, and bounded Parquet metadata or column reads. It assessed:

- the currently implemented forecast contract;
- available feature artifacts and their scale;
- temporal boundaries, feature availability rules, and schema parity;
- leakage risks that a future backtester must prevent;
- candidate temporal folds and metric choices;
- staged validation and proposed implementation deliverables.

### Explicit non-scope

This audit did not:

- implement temporal folds, metric functions, preprocessing, training, prediction, or backtesting;
- execute a model baseline or global forecasting model;
- generate a Notebook 09, reusable backtesting module, tests, or evidence artifact;
- rebuild the cleaned or model-ready feature datasets;
- load the complete 125,497,040-row cleaned dataset into memory;
- approve fold dates, metrics, target transformations, holdouts, or resource budgets;
- establish production readiness or research readiness;
- perform SCRUM-14 forecasting-baseline work or SCRUM-15 model-training work.

## Evidence reviewed

### Project, governance, and architecture

- `README.md`
- `docs/governance/EDIP_RESEARCH_ENGINEERING_DELIVERY_WORKFLOW.md`
- `docs/architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md`

### Favorita policy and executable workflow

- `notebooks/favorita/07_define_leakage_safe_feature_engineering_policy.ipynb`
- `notebooks/favorita/08_build_model_ready_feature_dataset.ipynb`
- `pipelines/features/favorita_model_ready.py`
- `tests/unit/test_favorita_model_ready_features.py`
- existing Favorita notebook names and saved notebook structure for Notebooks 01–08

Notebook 07 is policy-oriented and Markdown-only. Notebook 08 follows the existing numbered-section execution convention and contains saved assertions and outputs for a bounded smoke build. That convention is relevant to a proposed SCRUM-13 policy/design notebook, but it does not prove that a backtester exists.

### Manifests and artifacts

- `data/processed/favorita_cleaned/cleaning_manifest.json`
- `data/processed/favorita_cleaned/favorita_cleaned.parquet`
- `data/processed/favorita_features/smoke/feature_manifest_smoke.json`
- `data/processed/favorita_features/smoke/favorita_model_ready_features_smoke.parquet`
- planned but absent full outputs:
  - `data/processed/favorita_features/feature_manifest.json`
  - `data/processed/favorita_features/favorita_model_ready_features.parquet`

The Parquet evidence was inspected through file metadata, schemas, footer statistics, or bounded row-group/column reads. The complete cleaned table was not materialized.

### Validation evidence

The focused existing feature test was run without pytest cache or Python bytecode creation:

```text
tests/unit/test_favorita_model_ready_features.py: 4 passed in 2.00s
```

Those tests protect feature-contract behavior; they do not implement or validate temporal backtesting.

## Confirmed forecasting-contract evidence

The following statements are confirmed by the current policy notebook, feature implementation, tests, saved Notebook 08 evidence, and smoke manifest.

### Target, origin, dates, horizons, and grain

- Training target: `unit_sales`.
- Forecast origin: the end of calendar day `t`.
- Forecast dates: `t + 1` through `t + 14`.
- Direct horizon values: integers 1 through 14.
- Forecast-example grain: `(forecast_origin, forecast_date, store_nbr, item_nbr)`.
- Examples are generated only for observed target rows. The current contract does not densify the panel or infer zero sales from absent source rows.
- Negative and fractional `unit_sales` values are preserved by cleaning. The target is excluded from inference output.
- The contract is direct and horizon-aware. It does not recursively feed predictions back into later horizons.

### Historical features

Historical feature calculations are bounded by the fold/example forecast origin:

- sales lags at 1, 7, 14, and 28 days;
- sales rolling means over complete 7-, 14-, and 28-day windows ending at `t - 1`;
- sales rolling standard deviations over complete 7- and 28-day windows ending at `t - 1`, using sample standard deviation semantics (`ddof=1`);
- transactions at the origin, lags at 7 and 14 days, and complete 7- and 14-day means ending at the origin;
- oil movement features using observations through the origin; raw `dcoilwtico` is not passed through as a model feature;
- store and item attributes selected from records whose dates do not exceed the origin.

Incomplete required windows remain null rather than being filled with invented history.

### Future-known features

- Calendar fields are deterministic functions of the target date.
- Target-date promotion and holiday fields are permitted only when their planned or published values are demonstrably available at the forecast origin.
- The current cleaned artifact does not contain publication-time evidence for those fields.
- The smoke build records both future-promotion and future-holiday assumptions as disabled; corresponding target-date fields are therefore null in that artifact.
- Future actual sales, transactions, and oil observations are not valid model inputs for a fold originating earlier in time.

### Training and inference schema parity

The training schema contains 43 ordered columns. The inference schema contains the same ordered schema with only `unit_sales` removed, for 42 columns. `forecast_horizon` is present in the output/audit schema, but it is not currently included in `MODEL_FEATURE_COLUMNS`; whether the eventual estimator consumes it directly remains unresolved.

## Available model-ready feature artifacts

| Artifact | Confirmed evidence | Scale classification |
|---|---|---|
| `data/processed/favorita_cleaned/favorita_cleaned.parquet` | 125,497,040 rows; 21 columns; 502 row groups; `2013-01-01` through `2017-08-15`; 54 stores; 4,036 items; no duplicate cleaned grain recorded by the cleaning manifest | Full cleaned source-derived dataset, not a model-ready feature artifact |
| `data/processed/favorita_features/smoke/favorita_model_ready_features_smoke.parquet` | 478 rows; 43 columns; 1 row group; one origin (`2017-07-31`); target dates `2017-08-01` through `2017-08-14`; all horizons 1–14; store 1; 50 items; zero duplicate forecast-example keys recorded | Smoke-scale only |
| `data/processed/favorita_features/smoke/feature_manifest_smoke.json` | Declares `bounded_real_data_smoke_only` and records the smoke artifact's configuration, schema, counts, ranges, and validation checks | Smoke evidence only |
| `data/processed/favorita_features/favorita_model_ready_features.parquet` | File was absent at audit time | Planned full-scale artifact; unavailable |
| `data/processed/favorita_features/feature_manifest.json` | File was absent at audit time | Planned full-scale manifest; unavailable |

The cleaned Parquet size observed during the audit was 723,900,039 bytes. The smoke Parquet size was 16,859 bytes and its manifest size was 17,112 bytes. File size is recorded only as descriptive evidence and is not used to classify correctness.

## Confirmed date, schema, forecast-origin, and horizon evidence

### Cleaned source schema and bounds

The cleaned Parquet footer exposes 21 ordered Arrow fields:

| Position | Column | Arrow type |
|---:|---|---|
| 1 | `id` | `int64` |
| 2 | `date` | `timestamp[us]` |
| 3 | `store_nbr` | `int16` |
| 4 | `item_nbr` | `int32` |
| 5 | `unit_sales` | `double` |
| 6 | `onpromotion` | `bool` |
| 7 | `family` | `large_string` |
| 8 | `class` | `int16` |
| 9 | `perishable` | `int8` |
| 10 | `city` | `large_string` |
| 11 | `state` | `large_string` |
| 12 | `store_type` | `large_string` |
| 13 | `cluster` | `int8` |
| 14 | `transactions` | `int32` |
| 15 | `dcoilwtico` | `double` |
| 16 | `is_holiday` | `bool` |
| 17 | `holiday_type` | `large_string` |
| 18 | `holiday_locale` | `large_string` |
| 19 | `holiday_description` | `large_string` |
| 20 | `holiday_transferred` | `bool` |
| 21 | `holiday_event_count` | `int16` |

Arrow reports these cleaned fields as nullable. Footer statistics also confirmed: no nulls in `unit_sales` or `perishable`; `unit_sales` range `-15372.0` to `89440.0`; `perishable` range 0 to 1; 21,657,651 null `onpromotion` values; 214,625 null `transactions` values; and 40,522,930 null `dcoilwtico` values.

### Model-ready training schema

The 43 model-ready training columns are grouped as follows:

- audit keys: `forecast_origin`, `forecast_date`, `forecast_horizon`;
- entity/static fields: `store_nbr`, `item_nbr`, `family`, `class`, `perishable`, `city`, `state`, `store_type`, `cluster`;
- target: `unit_sales`;
- sales history: `sales_lag_1`, `sales_lag_7`, `sales_lag_14`, `sales_lag_28`, `sales_rolling_mean_7`, `sales_rolling_mean_14`, `sales_rolling_mean_28`, `sales_rolling_std_7`, `sales_rolling_std_28`;
- target-date calendar: `day_of_week`, `day_of_month`, `week_of_year`, `month`, `quarter`, `is_weekend`;
- promotion: `onpromotion`;
- transactions: `transactions_at_origin`, `transactions_rolling_mean_7`, `transactions_rolling_mean_14`, `transactions_lag_7`, `transactions_lag_14`;
- oil movement: `oil_pct_change_1d`, `oil_pct_change_7d`, `oil_rolling_change_7d`, `oil_rolling_volatility_7d`;
- holiday: `is_holiday`, `holiday_type`, `holiday_locale`, `holiday_transferred`, `holiday_event_count`.

Audit keys, entity/static fields, the target, and calendar fields are non-nullable in the saved smoke schema. Sales, promotion, transactions, oil, and holiday feature fields are nullable. The inference schema removes only `unit_sales`.

### Smoke temporal evidence

- Forecast-origin minimum and maximum: `2017-07-31`.
- Forecast-date minimum and maximum: `2017-08-01` and `2017-08-14`.
- Horizon set: every integer from 1 through 14.
- Recorded duplicate count at the four-column forecast-example grain: 0.

This proves bounded smoke execution for one origin. It does not demonstrate multi-fold backtesting or full-scale feature availability.

## Leakage risks SCRUM-13 must prevent

SCRUM-13 must explicitly encode and test the following controls:

1. **Random-row splitting:** never use random train/validation splits for these temporal forecast examples.
2. **Training-target overlap:** for validation origin `O`, training examples must satisfy `forecast_date <= O`. Checking only that a training example's own origin is earlier than `O` is insufficient because its target date could still fall in the validation future.
3. **Validation-window overlap:** folds should use non-overlapping target windows unless repeated scoring of the same realized target is intentionally approved and reported.
4. **Feature availability:** every historical feature must use information available no later than the example's forecast origin. Features produced for a later origin must not be reused for an earlier fold.
5. **Future actuals:** future sales, transactions, and oil values must not enter fold features.
6. **Promotions and holidays:** target-date values may be model features only with valid as-of-origin publication evidence. Post-hoc actual values may be diagnostic labels only if clearly separated.
7. **Preprocessing fit leakage:** encoders, scalers, imputers, category vocabularies, feature selectors, thresholds, and similar learned state must be fit on the fold's training data only and frozen before validation.
8. **Unknown categories:** unseen-category behavior must be specified without refitting on validation data.
9. **Entity-selection leakage:** store/item eligibility must be fixed independently or derived only from pre-origin history. The current smoke `max_items` selection uses the bounded future target window and is not a valid full evaluation sampling rule.
10. **Cold starts:** exclusion or inclusion rules for entities without sufficient pre-origin history must be predeclared and their coverage reported.
11. **Duplicate examples:** `(forecast_origin, forecast_date, store_nbr, item_nbr)` must remain unique within each fold artifact.
12. **Repeated realized targets:** expanding-origin training data can represent one realized row under multiple earlier origins/horizons; the weighting and sampling effect must be explicitly approved.
13. **Target transformations:** clipping or transforming negative targets for a metric or estimator is modeling/evaluation behavior, not cleaning, and must be explicit.
14. **Operational cutoff:** whether end-of-day transactions and oil observations are actually available at prediction time may require an additional lag even though current feature code allows values through the origin.
15. **Horizon handling:** the estimator's use of `forecast_horizon` must be settled before training-schema assertions are treated as final model-input assertions.

## Recommended rolling-origin expanding-window design

> **Recommendation only — not an approved SCRUM-13 decision.**

Use expanding training windows and fixed 14-day validation windows. For a fold with origin `O`:

1. build or select features using only information available through each example's origin;
2. allow training examples only when their target `forecast_date <= O`;
3. fit all learned preprocessing on that training subset;
4. freeze preprocessing and predict observed rows for `O + 1` through `O + 14`;
5. join hidden targets only after prediction;
6. score the fold and retain its lineage separately;
7. allow a later fold to train on an earlier validation period only after that period is historical relative to the later origin.

The recommendation uses direct horizon-aware global examples and preserves source-observed target rows. It does not approve panel densification or synthetic zero-demand rows.

## Candidate fold origins and derivation

> **Candidate dates — not approved fold dates.**

The cleaned source ends on `2017-08-15`, so `2017-08-01` is the latest origin with a complete following 14-day observed target window. Moving backward in 14-day increments yields six recent, non-overlapping candidates:

| Candidate origin | Candidate validation dates | Observed cleaned target rows in window |
|---|---|---:|
| `2017-05-23` | `2017-05-24`–`2017-06-06` | 1,505,137 |
| `2017-06-06` | `2017-06-07`–`2017-06-20` | 1,470,791 |
| `2017-06-20` | `2017-06-21`–`2017-07-04` | 1,488,708 |
| `2017-07-04` | `2017-07-05`–`2017-07-18` | 1,472,146 |
| `2017-07-18` | `2017-07-19`–`2017-08-01` | 1,469,025 |
| `2017-08-01` | `2017-08-02`–`2017-08-15` | 1,461,581 |
| **Total** | 84 non-overlapping calendar days | **8,867,388** |

These counts were derived without reading the full dataset: Parquet footer statistics identified 36 row groups intersecting `2017-05-24` through `2017-08-15`, after which only the `date` column was read one selected row group at a time. The bounded read examined 8,997,040 date values across those row groups; filtering produced the counts above. All 84 candidate target dates had observed rows, with daily counts from 97,436 to 118,194.

The counts are counts of cleaned source target rows, not guaranteed model-ready feature-row counts. Entity eligibility, history requirements, and null-feature rules can reduce the eventual evaluation population.

A defensible option is to use the first five candidates as rolling folds and reserve `2017-08-01` as a final untouched holdout. This is a recommendation requiring approval. If that option is adopted, the existing smoke origin (`2017-07-31`) and its `2017-08-01`–`2017-08-14` targets must not be used to select a model, preprocessing rule, or threshold for the holdout.

These six candidates cover only the final 12 weeks of cleaned observations. They do not establish seasonal robustness. Earlier folds or a different cadence may be required, subject to evidence and compute approval.

## Recommended evaluation metrics

> **Metric proposal — not approved.**

### Proposed primary metric

Use competition-style normalized weighted RMSLE if the evaluation-target treatment is explicitly approved:

```text
sqrt(sum(weight * (log1p(prediction) - log1p(actual))^2) / sum(weight))
```

Use weight 1.25 for `perishable == 1` and 1.0 otherwise, matching the Favorita competition convention. Negative predictions are invalid for this metric. More importantly, the cleaned dataset intentionally preserves negative `unit_sales`; `log1p` is undefined for sufficiently negative actuals. The metric therefore cannot be applied to every raw target without a declared evaluation transformation or exclusion.

The recommended competition-comparable option is to derive `evaluation_target = max(unit_sales, 0)` only inside evaluation/modeling and retain the original target for lineage and signed diagnostics. This would not change cleaning, but it requires user approval. Alternatives are to exclude negative targets with explicit coverage reporting or choose a signed-error primary metric.

### Proposed supporting metrics

- MAE on raw signed `unit_sales`;
- RMSE on raw signed `unit_sales`;
- WAPE with a documented zero-denominator guard;
- sMAPE with an explicit both-zero convention;
- signed mean error (bias);
- prediction and target coverage/counts by fold.

### Proposed diagnostic breakdowns

Report pooled and per-fold results, plus breakdowns by:

- forecast horizon;
- store;
- item family;
- promotion status, separating known/unknown as-of-origin status from any post-hoc actual diagnostic;
- perishability;
- cold-start or insufficient-history status;
- sparse-history status;
- negative-target status.

Thresholds for reporting or suppressing small groups must be approved before results are interpreted.

## Proposed validation and backtesting stages

### Unit-test stage

Use small deterministic synthetic fixtures to test logic, not business performance:

- fold-boundary construction and the 14-day horizon equation;
- `forecast_date <= fold_origin` training-target cutoff;
- non-overlapping validation windows;
- preprocessing fit/freeze scope and unseen categories;
- grain uniqueness and duplicate detection;
- metric formulas, perishable weighting, negative targets, and zero denominators;
- rejection of future feature values.

### Smoke-backtest stage

Use bounded real-data reads for two or three approved origins, a fixed entity population selected from pre-origin history, all 14 horizons, and a simple deterministic prediction callback or harness. The stage should validate orchestration, fold evidence, metrics, and manifests. It must remain labelled smoke-scale and must not silently implement or claim SCRUM-14 forecasting baselines.

### Full-backtest stage

After approvals, use all approved origins and the intended global population across 54 stores. Preserve observed-row-only semantics unless a separately approved panel policy changes the modeling population. Process origin/store batches, partition fold outputs, stream metric accumulators, and retain exact lineage. The current validator's in-memory Python set of all keys should be replaced or supplemented by partition-aware or disk-backed uniqueness validation for global scale.

Any baseline comparison belongs to SCRUM-14. Training the first global forecasting model belongs to SCRUM-15.

## Proposed SCRUM-13 implementation deliverables

> **Proposed only; paths and contents require approval.**

- Policy/design notebook: `notebooks/favorita/09_define_temporal_validation_and_backtesting.ipynb`.
- Reusable fold and metric module: `pipelines/evaluation/favorita_temporal_backtesting.py`.
- Focused tests: `tests/unit/test_favorita_temporal_backtesting.py`.
- A generated backtest manifest or evidence artifact recording fold definitions, inputs, schemas, counts, metric policy, validations, and checksums; its exact path and retention policy remain unresolved.
- An optional reviewed Markdown summary after execution, if required by governance.

A Notebook 09 should follow the established numbered-section convention, state its execution boundary, use repository-relative paths, distinguish smoke and full evidence, contain explicit assertions, and save no failed cells or errors. It should call reusable code rather than contain an independent second implementation.

## Unresolved decisions requiring user approval

1. Approve, replace, or extend the six candidate origins.
2. Decide whether `2017-08-01` is an untouched final holdout.
3. Choose fold count, spacing, and whether earlier seasonal folds are required.
4. Choose the cadence of training forecast origins and control repeated realized targets.
5. Choose the earliest usable training origin and minimum history requirements.
6. Approve the explicit `forecast_date <= fold_origin` training-label cutoff.
7. Choose weighting or sampling for targets represented at multiple training origins/horizons.
8. Confirm observed-row-only evaluation or separately authorize a panel definition.
9. Define cold-start and insufficient-history inclusion, exclusion, and reporting.
10. Approve negative-target treatment for the primary metric and estimator.
11. Approve primary/supporting metrics, fold aggregation, and diagnostic suppression thresholds.
12. Confirm perishable weighting and its source of truth.
13. Decide whether actual promotion status may be used only as a post-hoc diagnostic.
14. Decide whether and how publication-time promotion/holiday data can become as-of-origin features.
15. Confirm the operational end-of-day availability cutoff for transactions and oil.
16. Approve preprocessing, unseen-category, and nullable-feature behavior.
17. Decide whether `forecast_horizon` is a model input, stratification field, or audit-only field.
18. Define a leakage-safe smoke entity-selection rule.
19. Approve backtest output partitioning, manifest location, retention, and checksums.
20. Approve time, memory, disk, and parallelism budgets for global execution.
21. Approve the proposed deliverable paths before implementation.

## Limitations and unavailable evidence

- No full-scale model-ready Favorita feature Parquet or full feature manifest was available.
- No temporal fold builder, metric module, backtest runner, baseline, trained model, or backtest evidence artifact exists yet.
- The only model-ready artifact is a one-origin, one-store, 50-item smoke artifact.
- Candidate target counts come from cleaned observed rows and may not equal eventual feature or scored-example counts.
- The candidate folds cover only the last 12 weeks and do not prove robustness across seasons or earlier operational regimes.
- Footer metadata and bounded date-column reads establish structure and candidate counts, not end-to-end leakage safety.
- The focused feature tests validate current feature behavior; they do not validate fold orchestration, preprocessing isolation, metrics, or model evaluation.
- Promotion and holiday publication-time evidence is unavailable in the current cleaned artifact.
- Operational availability timing for same-day transactions and oil has not been established.
- Compute and storage costs for full global multi-origin feature construction and scoring have not been measured in this audit.
- The audit makes no claim of backtesting completion, model quality, production readiness, or research readiness.

## Final readiness conclusion

SCRUM-13 has sufficient confirmed repository evidence to proceed to approval of a detailed temporal-validation design. The current origin/date/horizon contract, leakage-safe feature boundaries, schema parity, cleaned lineage, and bounded real-data evidence provide a credible foundation.

Implementation should not begin until the unresolved temporal, metric, target-treatment, entity, operational-cutoff, evidence-retention, and resource decisions are approved. Backtesting has not been implemented or executed, and the absence of a full-scale model-ready feature artifact remains a material limitation.

## Changed-file statement

This audit task creates only:

- `docs/audits/SCRUM_13_TEMPORAL_VALIDATION_BACKTESTING_READINESS_AUDIT.md`

No application code, pipeline code, tests, notebooks, datasets, manifests, generated artifacts, dependency files, or other documentation were modified. No complete dataset was loaded or rebuilt, and no commit, push, merge, or branch change was performed.
