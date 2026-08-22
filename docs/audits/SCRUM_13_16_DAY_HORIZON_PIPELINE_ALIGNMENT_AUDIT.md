# SCRUM-13 16-Day Horizon Production Pipeline Alignment Audit

> **Subsequent completion notice (2026-08-14):** This document remains the historical record of the pipeline-and-test alignment step before notebook execution. Notebook 08 was subsequently executed top to bottom from a fresh kernel and regenerated the bounded 16-horizon smoke Parquet and manifest. Statements below that execution or regeneration was pending or not performed describe this audit's original controlled-step boundary; current executed evidence is recorded in `SCRUM_13_16_DAY_HORIZON_COMPLETION_AUDIT.md`.


| Field | Value |
|---|---|
| Date | 2026-08-14 |
| Branch | feature/scrum-13-temporal-validation-backtesting |
| Controlled step | Production pipeline and focused unit-test alignment |
| Status | Pipeline and tests aligned; Notebook 08 execution and smoke regeneration pending |

## Reason for the production change

The official Kaggle Corporación Favorita test period is 2017-08-16 through 2017-08-31, an inclusive 16-day inference period. The preceding controlled step aligned the Favorita notebook contract from 14 to 16 daily horizons. This step aligns the executable production feature pipeline and its focused unit tests to the same direct horizon-aware contract.

The target remains unit_sales; forecast origin remains end-of-day t; forecast dates remain forecast_origin plus forecast_horizon calendar days; and valid horizons are now exactly integers 1 through 16.

## Required evidence inspected

- pipelines/features/favorita_model_ready.py
- tests/unit/test_favorita_model_ready_features.py
- notebooks/favorita/07_define_leakage_safe_feature_engineering_policy.ipynb
- notebooks/favorita/08_build_model_ready_feature_dataset.ipynb
- docs/audits/SCRUM_13_16_DAY_HORIZON_NOTEBOOK_ALIGNMENT_AUDIT.md

The earlier notebook-alignment audit remains the historical record of the first controlled step. It was not rewritten to imply that pipeline alignment had already occurred when that audit was produced.

## Classified occurrences reviewed

### Production horizon occurrences changed

| Pre-alignment occurrence | Classification | Aligned behavior |
|---|---|---|
| tuple(range(1, 15)) | Forecast-horizon contract | tuple(range(1, 17)) |
| bounded integer horizon 1..14 | Forecast-horizon semantic type | bounded integer horizon 1..16 |
| validation error restricted to 1..14 | Forecast-horizon validation | Reports restricted to 1..16 |
| fixture source ending at origin plus 14 days | Horizon-dependent fixture bound | Derives from max(FORECAST_HORIZONS) |
| row-group reload ending at origin plus 14 days | Horizon-dependent fixture bound | Derives from max(FORECAST_HORIZONS) |
| fixture assertion between(1, 14) | Horizon validation | Requires the exact FORECAST_HORIZONS set |

Existing production forecast-end calculations in source slicing, target-row selection, materialization, and manifest evidence already derive from max(FORECAST_HORIZONS) or FORECAST_HORIZONS. They were intentionally left structurally unchanged; the updated constant expands their behavior to 16 days.

### Production occurrences intentionally preserved

- sales_lag_14 and its offset 14;
- sales_rolling_mean_14 and complete interval [t-14,t-1];
- transactions_lag_14 at t-14;
- transactions_mean_14d over [t-13,t];
- SALES_MEAN_WINDOWS = (7, 14, 28);
- deterministic fixture assertions for lag-14 and rolling-14 behavior;
- unrelated dates, sequence values, section numbers, and counts containing 14.

These are origin-bounded historical lookbacks, not forecast-horizon definitions.

### Focused test occurrences

- Changed the old contract assertion from tuple(range(1, 15)) to tuple(range(1, 17)).
- Preserved every lag-14 and rolling-14 definition assertion.
- Added explicit minimum-horizon 1 and maximum-horizon 16 assertions.
- Added deterministic twice-built feature-frame equality.
- Added exact 16-day horizon-set and forecast-date-equation assertions.
- Added an exact 1-through-16 assertion for every complete deterministic fixture entity group and an explicit zero-duplicate-key assertion.
- Added explicit origin+1 and origin+16 date bounds.
- Preserved ordered training/inference schema parity, target exclusion, Arrow schema order, and forbidden-column assertions.

### Notebook and prior-audit occurrences

- Notebook 07 contains only valid historical feature references to 14 and section number 14; no change was required.
- Notebook 08's remaining 14 references are historical lag/window definitions, preserved historical outputs, fixture checks, or section number 14.
- The previous notebook-alignment audit retains its pre-change occurrence inventory, observed 2017-08-14 dates, historical features, and then-pending pipeline status as historical controlled-step evidence.

## Exact production code changes

- FORECAST_HORIZONS now equals tuple(range(1, 17)).
- SEMANTIC_TYPES["forecast_horizon"] now states bounded integer horizon 1..16.
- Invalid feature frames now report that horizons must be restricted to 1..16.
- Deterministic fixture construction and row-group reload both use max(FORECAST_HORIZONS) for their future boundary.
- Deterministic fixture validation requires the generated horizon set to equal FORECAST_HORIZONS.
- Forecast-date equality remains forecast_date = forecast_origin + forecast_horizon days.
- Manifest evidence continues to serialize list(FORECAST_HORIZONS), which now records 1 through 16.

No approved feature column, target rule, sparse-row policy, availability rule, categorical/static semantic, inference schema, or forbidden-column policy changed.

## Exact unit-test changes

The focused test module now contains five tests. The new or strengthened assertions verify:

- exact horizon tuple 1 through 16;
- minimum horizon 1 and maximum horizon 16;
- deterministic equality across two builds from the same fixture;
- exact generated horizon set;
- forecast dates from origin+1 through origin+16;
- row-level forecast-date equation;
- 32 generated fixture rows;
- unchanged training/inference ordered-schema parity;
- unit_sales absent from inference output;
- forbidden raw columns absent from model features;
- unchanged lag-14 and rolling-14 definitions.

## Fixture expectation changes and mathematical reasons

The deterministic fixture contains two item series and one observed row per future date for each item. Expanding from 14 to 16 horizons changes the expected supervised-row count:

    2 items x 16 observed future dates = 32 rows

The previous 14-horizon equivalent was 28 rows. The new target-date bounds are forecast_origin + 1 day through forecast_origin + 16 days.

The fixture source and bounded row-group reload therefore extend by two future dates. Historical input requirements remain unchanged: sales still require at most t-28, and all lag-14 and 14-day rolling calculations retain their original formulas.

## Notebook 08 transitional correction

Notebook 08 now states that its source, the production pipeline, and focused tests share the 16-horizon expectation. Its fail-fast assertion message no longer says production alignment is pending.

This step changes Notebook 08 source only in cells 1 and 3. Cumulatively against HEAD, Notebook 08 source changes remain limited to cells 1, 3, 7, 12, 13, 17, and 19. Previously cleared outputs remain limited to cells 7, 13, 15, 17, 19, 23, and 25; cleared execution counts remain limited to cells 3, 7, 13, 15, 17, 19, 23, and 25.

Notebook 08 was not executed. Unrelated saved evidence remains preserved. Its tracked LF line-ending convention, cell IDs, cell order, and notebook metadata remain unchanged.

## Validation results

### Focused tests

Command:

    python -m pytest tests/unit/test_favorita_model_ready_features.py -q -p no:cacheprovider

Result:

    5 passed in 2.07s

### Complete currently available suite

Command:

    python -m pytest -q -p no:cacheprovider

Result:

    10 passed in 3.44s

Both commands were executed with the repository's WSL .venv, PYTHONDONTWRITEBYTECODE=1, and pytest cache disabled.

Additional validation:

- production and focused-test Python sources compile;
- Notebook 08 parses as nbformat 4 and all code-cell sources compile;
- no stale production/test range(1, 15), 1..14, or between(1, 14) horizon contract remains;
- valid lag-14 and rolling-14 occurrences remain;
- git -c core.whitespace=cr-at-eol diff --check passes;
- no unexpected encoding or control characters are present;
- no data, Parquet, manifest, model, or smoke artifact was written or modified.

## Changed-file list for this controlled step

- pipelines/features/favorita_model_ready.py
- tests/unit/test_favorita_model_ready_features.py
- notebooks/favorita/08_build_model_ready_feature_dataset.ipynb
- docs/audits/SCRUM_13_16_DAY_HORIZON_PIPELINE_ALIGNMENT_AUDIT.md

Notebook 07 and the two earlier audit documents remain in the cumulative uncommitted branch work from the preceding controlled step but were not modified by this pipeline-alignment step.

## Limitations and remaining work

- Notebook 08 has not been executed against the aligned pipeline.
- The existing smoke Parquet and smoke manifest remain 14-horizon historical evidence.
- No 16-day smoke artifact, manifest, checksum, row count, date range, or null profile is claimed.
- Controlled Notebook 08 execution and smoke-artifact regeneration require a later explicitly approved step.
- SCRUM-13 temporal folds, metrics, backtesting code, full-scale feature materialization, baselines, and models remain outside this task.
- No full 125,497,040-row dataset scan occurred and no model was trained.

No commit, push, merge, branch switch, dataset modification, or artifact regeneration was performed.
