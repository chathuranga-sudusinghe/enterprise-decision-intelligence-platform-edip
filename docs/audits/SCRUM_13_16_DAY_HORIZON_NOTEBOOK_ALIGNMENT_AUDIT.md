# SCRUM-13 16-Day Horizon Notebook Alignment Audit

> **Subsequent completion notice (2026-08-14):** This document remains the historical record of the notebook-only alignment step. The production pipeline and focused tests were subsequently aligned, Notebook 08 was executed top to bottom from a fresh kernel, and the bounded smoke Parquet and manifest were regenerated for horizons 1 through 16. Statements below that those activities were pending or not performed describe this audit's original controlled-step boundary; current executed evidence is recorded in `SCRUM_13_16_DAY_HORIZON_COMPLETION_AUDIT.md`.


| Field | Value |
|---|---|
| Date | 2026-08-14 |
| Branch | `feature/scrum-13-temporal-validation-backtesting` |
| Work item | SCRUM-13 — first controlled 16-day horizon alignment |
| Scope | Favorita notebooks only, plus this audit |
| Status | Notebook contract aligned; pipeline, tests, artifacts, and backtesting remain pending |

## Reason for the alignment

The official Kaggle Corporación Favorita test period covers `2017-08-16` through `2017-08-31`, an inclusive 16-day inference period. Notebook 01 already records that test-date range and `inclusive_days: 16`. The prior Notebook 07 policy and Notebook 08 executable narrative used a 14-day direct horizon-aware contract. This task aligns the notebook-level forecast, inference, and chronological-evaluation contract to daily horizons 1 through 16.

This is the first controlled alignment step. It does not change the production feature pipeline, tests, manifests, Parquet artifacts, general documentation, or SCRUM-13 backtesting implementation.

## Notebooks inspected

Every notebook under `notebooks/favorita/` was inspected at source-cell and saved-output level:

1. `01_data_inventory_and_quality.ipynb`
2. `02_temporal_sales_and_coverage_eda.ipynb`
3. `03_build_favorita_merged_base.ipynb`
4. `04_review_merged_dataset_quality.ipynb`
5. `05_define_data_cleaning_rules.ipynb`
6. `06_create_cleaned_favorita_dataset.ipynb`
7. `07_define_leakage_safe_feature_engineering_policy.ipynb`
8. `08_build_model_ready_feature_dataset.ipynb`

Notebooks 01, 03, 04, and 06 contained no stale 14-day forecast-contract reference. Notebook 02 and Notebook 05 contain saved rows dated `2017-08-14`; these are observed dates, not horizon definitions, and were preserved. Notebook 01's existing `2017-08-16` to `2017-08-31` test-period evidence was also preserved.

## Classified pre-edit occurrences

| Notebook | Cell index | Classification | Pre-edit reference | Action |
|---|---:|---|---|---|
| Notebook 07 | 2 | Forecast contract | `t+1` through `t+14`; combined 14-day total; horizon values 1–14 | Changed to 16-day semantics |
| Notebook 07 | 13 | Chronological evaluation | 14-day forecast windows; following 14 hidden days; 14 daily horizons | Changed to 16-day semantics |
| Notebook 07 | 17 | Deferred SCRUM-13 evaluation | 14-day hidden-outcome procedure | Changed to 16-day semantics |
| Notebook 07 | 18 | Policy completion checklist | 14 daily horizons | Changed to 16 daily horizons |
| Notebook 08 | 1 | Forecast contract | `t+1` through `t+14` | Changed to `t+1` through `t+16` |
| Notebook 08 | 7 output | Saved schema evidence | bounded horizon 1–14 | Cleared; not relabelled as unexecuted evidence |
| Notebook 08 | 8 | Historical features | `sales_lag_14`, 14-day sales windows, transaction lag/mean 14 | Preserved |
| Notebook 08 | 12 | Forecast-bound source interval | read through `t+14` | Changed to `t+16` |
| Notebook 08 | 13 source/output | Smoke horizon configuration | imported 14 horizons and displayed 1–14 | Source now expects 1–16; stale output cleared |
| Notebook 08 | 17 output | Saved smoke coverage | horizons 1–14 and maximum date `2017-08-14` | Cleared; artifact was not regenerated |
| Notebook 08 | 19 source/output | Horizon validation | `horizon_restricted_to_1_14` | Changed to `horizon_restricted_to_1_16`; stale result cleared |
| Notebook 08 | 25 output | Saved smoke summary | coverage ending `2017-08-14` | Cleared; not rewritten as a 16-day result |
| Notebook 02 | 28 output | Observed date | `2017-08-14` rows | Preserved |
| Notebook 05 | 88 output | Observed date | `2017-08-14` oil/calendar rows | Preserved |

Cell indexes in this audit are zero-based JSON notebook cell indexes. Notebook section numbering was not changed.

## Notebook 07 changes

Notebook 07 remains the authoritative policy statement and remains Markdown-only.

- Cell 2 now defines daily targets from `t+1` through `t+16`.
- Cell 2 now rejects a combined 16-day total and requires `forecast_horizon` values 1 through 16.
- Cell 13 now requires 16-day expanding-window or walk-forward forecast windows, 16 hidden outcome days, and 16 daily predictions.
- Cell 17 now delegates enforcement of the 16-day hidden-outcome procedure to SCRUM-13.
- Cell 18 now records 16 daily horizons in the policy checklist.

Forecast-origin semantics, direct horizon-aware design, no recursive feedback, leakage controls, feature-availability rules, train/inference parity, sparse-row policy, and chronological evaluation rules were otherwise preserved.

## Notebook 08 changes

Notebook 08 is aligned at notebook source-contract level without changing the production pipeline:

- Cell 1 documents `t+1` through `t+16` and records the controlled-alignment limitation.
- Cell 3 defines `EXPECTED_FORECAST_HORIZONS = tuple(range(1, 17))`.
- Cell 3 fails fast until the imported production `FORECAST_HORIZONS` matches the expected 16-day contract.
- Cell 7 requires the imported semantic description to be `bounded integer horizon 1..16`.
- Cell 12 changes the planned bounded read from `t-28 ... t+14` to `t-28 ... t+16`.
- Cells 12 and 13 move the planned smoke origin from `2017-07-31` to `2017-07-30`, allowing 16 observed target dates through the cleaned-data maximum of `2017-08-15`.
- Cell 13 displays `EXPECTED_FORECAST_HORIZONS` after the production pipeline is aligned.
- Cell 17 validates artifact horizons against `EXPECTED_FORECAST_HORIZONS`.
- Cell 19 renames the notebook validation to `horizon_restricted_to_1_16` and compares against the expected horizons.

The horizon-dependent execution state was invalidated rather than fabricated. Execution counts and outputs were cleared for cells 3, 7, 13, 15, 17, 19, 23, and 25. These cells import/assert the pipeline contract, display it, configure or build the smoke artifact, validate it, write its manifest, or summarize its coverage. Unrelated saved source-metadata, historical-feature-definition, deterministic-fixture, and cleaned-source immutability evidence was retained.

Notebook 08 was not executed because the intentionally unchanged production pipeline still exposes 14 horizons. Its new fail-fast assertion makes that pending dependency explicit.

## Intentionally preserved 14-period historical features

The alignment did not replace valid historical lookbacks. Preserved examples include:

- `sales_lag_14 = t-14`;
- `sales_rolling_mean_14` over `[t-14, t-1]`;
- transaction lag 14 at `t-14`;
- `transactions_mean_14d` over `[t-13, t]`;
- deterministic fixture checks such as `sales_lag_14_is_t_minus_14` and `transactions_lag_14_is_t_minus_14`.

The existing 14-day historical definitions are independent of the 16-day forecast horizon and remain valid origin-bounded features.

## Remaining controlled alignment work

The following non-notebook items still encode or evidence the prior 14-day contract and were intentionally not changed:

### Production pipeline

- `pipelines/features/favorita_model_ready.py:19` — `FORECAST_HORIZONS = tuple(range(1, 15))`.
- `pipelines/features/favorita_model_ready.py:190` — semantic description `1..14`.
- `pipelines/features/favorita_model_ready.py:661` — 1–14 assertion message.
- Pipeline calculations that derive forecast-end dates or manifest values from `FORECAST_HORIZONS` will change behavior after the constant is aligned and require focused validation.

### Unit tests

- `tests/unit/test_favorita_model_ready_features.py:70` asserts `tuple(range(1, 15))`.
- Existing fixture, schema, row-generation, and artifact-validation expectations require review for the 16-day contract.

### Existing data and generated evidence

- `data/processed/favorita_features/smoke/favorita_model_ready_features_smoke.parquet` remains the previously executed 14-horizon smoke artifact.
- `data/processed/favorita_features/smoke/feature_manifest_smoke.json` remains its matching manifest.
- No smoke or full feature artifact was regenerated in this task.

### Documentation and SCRUM-13

- `docs/audits/SCRUM_13_TEMPORAL_VALIDATION_BACKTESTING_READINESS_AUDIT.md` remains an accurate record of the pre-alignment 14-day repository state. Its candidate folds, counts, validation windows, holdout recommendation, and horizon statements require a separately controlled 16-day redesign; they were not silently rewritten.
- General project, governance, and architecture documentation requires a targeted horizon review in the next alignment step.
- SCRUM-13 fold construction, metrics, tests, backtesting code, manifests, and execution remain unimplemented.

## Validation performed

- Parsed all eight Favorita notebooks as JSON notebooks.
- Confirmed every notebook retains `nbformat == 4`.
- Confirmed Notebook 07 has 19 cells, all Markdown, with no execution counts or outputs.
- Confirmed Notebook 07 and Notebook 08 retain their original cell order, cell IDs, and notebook metadata.
- Compiled every Notebook 08 code-cell source to confirm Python syntax.
- Confirmed no saved notebook error output remains.
- Re-ran the semantic occurrence scan across all Favorita notebook sources and saved outputs.
- Confirmed the only remaining `t+14` match is Notebook 08's explicitly preserved historical `sales_lag_14 = t-14` and 14-day lookback text.
- Confirmed `range(1, 17)`, `t+16`, 16-day evaluation language, and the 1–16 validation name are present where expected.
- Confirmed valid historical `sales_lag_14`, `sales_rolling_mean_14`, `transactions_mean_14d`, and lag-14 fixture references remain.
- Confirmed Notebook 07 preserves its tracked CRLF line-ending convention.
- Confirmed Notebook 08 preserves its tracked LF line-ending convention.
- Because Notebook 07 is a tracked CRLF notebook, ran `git -c core.whitespace=cr-at-eol diff --check`; no whitespace errors remain under this repository-compatible check.

No full dataset scan, notebook execution, model training, feature-dataset build, artifact generation, data modification, commit, push, merge, or branch change was performed.

## Limitations and unresolved decisions

- Notebook 08 cannot execute successfully until the production pipeline and tests are aligned to 16 horizons; the fail-fast assertion is intentional.
- No new 16-day smoke row count, date range, null profile, checksum, or manifest result is claimed.
- The prior smoke artifact and manifest remain internally 14-day evidence.
- Exact 16-day rolling-origin fold dates, fold counts, holdout policy, and validation-row counts require a revised SCRUM-13 design and user approval.
- The 16-day primary metric, negative-target treatment, preprocessing policy, entity eligibility, and operational feature cutoffs remain unresolved.
- The eventual 16-day smoke origin and bounded entity-selection policy must be revalidated after the pipeline changes.

## Changed-file statement

This alignment changes only:

- `notebooks/favorita/07_define_leakage_safe_feature_engineering_policy.ipynb`;
- `notebooks/favorita/08_build_model_ready_feature_dataset.ipynb`;
- `docs/audits/SCRUM_13_16_DAY_HORIZON_NOTEBOOK_ALIGNMENT_AUDIT.md`;
- `docs/audits/SCRUM_13_TEMPORAL_VALIDATION_BACKTESTING_READINESS_AUDIT.md`.

The readiness audit changed only by adding the historical pre-alignment and supersession notice immediately after its title; its 14-day evidence and candidate counts remain unchanged. No pipeline, test, other documentation, data, manifest, Parquet, model, or other artifact was modified.
