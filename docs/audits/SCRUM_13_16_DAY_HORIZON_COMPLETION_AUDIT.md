# SCRUM-13 16-Day Forecast-Horizon Alignment Completion Audit

| Field | Value |
|---|---|
| Date | 2026-08-14 |
| Branch | `feature/scrum-13-temporal-validation-backtesting` |
| Work item | SCRUM-13 — complete 14-day-to-16-day contract alignment |
| Status | Alignment and bounded smoke evidence complete; temporal backtesting remains unimplemented |

## Purpose and scope

This audit records the completed repository alignment from the former 14-day forecast contract to the approved 16-day direct horizon-aware Favorita contract. The work covers the SCRUM-11 policy notebook, the SCRUM-12 executable notebook, the production feature pipeline, focused unit tests, bounded smoke evidence, and the associated audit trail.

This completion is limited to contract alignment and bounded feature-pipeline evidence. It does not implement SCRUM-13 folds or metrics, build the full model-ready dataset, train a model, calculate a metric from Kaggle `test.csv`, prepare a Kaggle submission, or perform SCRUM-14 or SCRUM-15.

## Approved 16-day contract

- The supervised target remains `unit_sales`.
- The previous active forecast contract was 14 calendar days; the approved active contract is 16 calendar days.
- Labelled Favorita history ends on `2017-08-15`.
- Official Kaggle `test.csv` covers `2017-08-16` through `2017-08-31`, an inclusive 16-day inference period.
- The 16-day horizon is approved to align the active contract with that official Kaggle inference period.
- `forecast_horizon` is exactly the integer set 1 through 16.
- For forecast origin `t`, `forecast_date = t + forecast_horizon days`, producing targets `t+1` through `t+16`.
- Forecasts use a direct horizon-aware global design; recursive prediction feedback is forbidden.
- Historical features use only information available at or before `t`; permitted future-known values are evaluated for `t+h` under their documented availability assumptions.
- Training and inference feature schemas remain identical and ordered apart from the training target.
- Historical evaluation must be chronological walk-forward or expanding-window evaluation, never a random split.
- Sparse observed-row semantics remain unchanged: no densification and no inferred zero-sales rows.
- Kaggle `test.csv` has no `unit_sales`; it is unlabelled final inference/submission input, not local metric evidence.

## Evidence inspected

- `notebooks/favorita/01_data_inventory_and_quality.ipynb` through `notebooks/favorita/08_build_model_ready_feature_dataset.ipynb`;
- `pipelines/features/favorita_model_ready.py`;
- `tests/unit/test_favorita_model_ready_features.py`;
- `data/processed/favorita_cleaned/favorita_cleaned.parquet` through file statistics, checksum, Parquet footer/schema APIs, and bounded feature reads only;
- `data/processed/favorita_cleaned/cleaning_manifest.json`;
- `data/processed/favorita_features/smoke/favorita_model_ready_features_smoke.parquet`;
- `data/processed/favorita_features/smoke/feature_manifest_smoke.json`;
- the readiness, notebook-alignment, and pipeline-alignment audits;
- repository-wide textual references to the former 14-day forecast contract.

## Files changed or created

Tracked or proposed tracked repository work:

- `notebooks/favorita/07_define_leakage_safe_feature_engineering_policy.ipynb`;
- `notebooks/favorita/08_build_model_ready_feature_dataset.ipynb`;
- `pipelines/features/favorita_model_ready.py`;
- `tests/unit/test_favorita_model_ready_features.py`;
- `docs/audits/SCRUM_13_TEMPORAL_VALIDATION_BACKTESTING_READINESS_AUDIT.md`;
- `docs/audits/SCRUM_13_16_DAY_HORIZON_NOTEBOOK_ALIGNMENT_AUDIT.md`;
- `docs/audits/SCRUM_13_16_DAY_HORIZON_PIPELINE_ALIGNMENT_AUDIT.md`;
- `docs/audits/SCRUM_13_16_DAY_HORIZON_COMPLETION_AUDIT.md`.

Regenerated bounded evidence, ignored by the repository's `data/processed/*` rule:

- `data/processed/favorita_features/smoke/favorita_model_ready_features_smoke.parquet`;
- `data/processed/favorita_features/smoke/feature_manifest_smoke.json`.

The readiness audit retains its pre-alignment findings and was changed only by the already-added historical/supersession notice. The two controlled-step alignment audits retain their original before-state evidence and now include prominent subsequent-completion notices rather than silently rewriting history.

## Repository-wide classification of remaining `14` references

| Classification | Remaining evidence | Disposition |
|---|---|---|
| Current forecast-contract reference requiring conversion | None found in the SCRUM-11 policy, SCRUM-12 notebook/pipeline/tests, or current SCRUM-13 alignment scope | No action remains for this alignment |
| Valid historical 14-day lookback | `sales_lag_14`, `sales_rolling_mean_14`, `transactions_lag_14`, `transactions_mean_14d`, offsets such as `t-14`, and their deterministic assertions | Preserved unchanged because these are origin-bounded history features, not forecast length |
| Superseded historical evidence | The readiness audit's 14-day contract, 478-row smoke evidence, fold candidates, and recommendations; before-state tables and literals in the two controlled-step audits | Retained and explicitly labelled historical or superseded |
| Unrelated occurrence | SCRUM-14 work-item references, section number 14, saved observed date `2017-08-14`, timestamps, and unrelated counts | Preserved unchanged |

The regenerated smoke output legitimately contains horizon value `14` as one member of the approved exact set 1 through 16. That value is not evidence of the former 14-day maximum.

## Notebook alignment evidence

Notebook 07 remains a 19-cell Markdown-only policy notebook. It now consistently states the 16-day, horizons-1-through-16, `t+1`-through-`t+16`, direct global contract; origin-bounded historical features; target-date future-known semantics; chronological 16-day evaluation; and Kaggle `test.csv` as unlabelled inference/submission input. Its tracked CRLF convention, cell IDs, ordering, structure, and metadata are preserved.

Notebook 08 remains a 26-cell nbformat-4 notebook with its tracked LF convention, original cell IDs/order/metadata, and bounded smoke design. It was executed from a fresh `python3` kernel, top to bottom. Its 12 code cells completed sequentially with execution counts 1 through 12 and no saved error output. Its saved outputs now report the executed 16-horizon contract and regenerated smoke evidence rather than the cleared transitional state.

The execution used smoke origin `2017-07-30`, Store 1, at most 50 observed item codes, and target dates `2017-07-31` through `2017-08-15`. It did not execute the planned full-output path.

## Pipeline and test alignment evidence

- `FORECAST_HORIZONS = tuple(range(1, 17))`.
- The semantic type states `bounded integer horizon 1..16`.
- Invalid horizons report the exact 1-through-16 restriction.
- Fixture and bounded-read future endpoints derive from `max(FORECAST_HORIZONS)`.
- Generated rows enforce `forecast_date = forecast_origin + forecast_horizon days`.
- The exact horizon set is validated, not merely bounded by minimum and maximum.
- Training/inference ordered-schema parity, target exclusion, forbidden-column exclusion, sparse observed-row semantics, and duplicate-key validation remain enforced.
- Historical lag-14 and rolling-14 features retain their original definitions.

The focused tests also prove deterministic equality across two identical builds, 32 fixture rows from 2 items × 16 observed target dates, exact origin-plus-1/origin-plus-16 bounds, schema parity, target exclusion, and preserved historical 14-period formulas.

## Executed smoke evidence

| Property | Executed value |
|---|---|
| Creation scope | `bounded_real_data_smoke_only` |
| Forecast origin | `2017-07-30` |
| Forecast-date minimum | `2017-07-31` |
| Forecast-date maximum | `2017-08-15` |
| Exact horizon set | Integers 1 through 16 |
| Rows | 548 observed target rows |
| Columns | 43 |
| Parquet row groups | 1 |
| Duplicate output keys | 0 |
| Smoke Parquet SHA-256 | `003aed5ef8120b0199aad3c61b953cc04c2b2174d702ce2b8ecbfe5f71f4550f` |
| Smoke manifest SHA-256 | `ae0995f8cfe691115b3ae36a4e3484063cbda7a1b9e88b7358b2a115e048d3d8` |

The 548 rows are sparse observed target rows, not a dense `50 × 16` panel. Missing store-item-date combinations were not created and no absent target was interpreted as zero.

## Manifest and Parquet agreement

Direct inspection of the regenerated Parquet footer/schema and bounded key columns agrees with the manifest on:

- 548 rows and 43 columns;
- exact ordered columns and Arrow type mapping;
- one forecast origin, `2017-07-30`;
- forecast-date range `2017-07-31` through `2017-08-15`;
- exact horizon set 1 through 16;
- zero duplicate grain keys;
- no forbidden model columns;
- ordered training/inference schema parity and target absence from inference;
- observed-row-only materialization.

Every Boolean recorded under the manifest's `validation` object is true, including the forecast-date equation, exact horizon restriction, output-grain uniqueness, source immutability, schema equality, forbidden-column checks, and deterministic fixture checks.

## Cleaned-source immutability evidence

Before execution, the cleaned source was 723,900,039 bytes with SHA-256:

`845b435622fc4fb31c5336fb1f6eda22195f64edba61a0de813e94f831c626e4`

Notebook 08 rechecked the footer/schema, file size, nanosecond modification time, and SHA-256 after the smoke build. All four comparisons passed. The manifest records the same source SHA-256 and `mutated: false`; an independent post-execution checksum also matched. The cleaned Parquet was not rewritten.

## Validation results

Production and focused-test Python sources compiled successfully.

Focused command:

    python -m pytest tests/unit/test_favorita_model_ready_features.py -q -p no:cacheprovider

Result:

    5 passed in 2.15s

Complete currently available suite:

    python -m pytest -q -p no:cacheprovider

Result:

    10 passed in 3.43s

Both pytest runs used the repository WSL `.venv`, `PYTHONDONTWRITEBYTECODE=1`, and disabled pytest cache. Repository-compatible `git -c core.whitespace=cr-at-eol diff --check` is required because Notebook 07 intentionally retains its tracked CRLF convention.

## Limitations and unresolved work

- SCRUM-13 temporal fold construction, metric implementation, preprocessing-fit boundaries, backtest orchestration, and backtest evidence are not implemented or executed by this alignment.
- The readiness audit's old fold candidates and horizon-dependent counts remain historical evidence and are not an approved 16-day design.
- The regenerated artifact is smoke-scale only and does not represent the complete training population.
- The full 125,497,040-row model-ready feature dataset was not built or loaded into memory.
- No forecasting baseline or model was trained; SCRUM-14 and SCRUM-15 were not performed.
- Kaggle `test.csv` was not assigned manufactured labels, scored locally, or submitted.
- Planned-at-origin publication evidence for promotions and holidays remains unavailable in the cleaned artifact, so the bounded smoke build keeps those future-known groups unknown under its safe configuration.

## Rollback approach

If a later approved decision returns the active contract to 14 days, perform a new controlled alignment rather than reverting historical evidence or globally replacing `16`. Change the active policy, `FORECAST_HORIZONS`, semantic and validation text, horizon-dependent fixture bounds and row-count expectations, Notebook 08 smoke origin/date coverage, and current completion evidence together. Re-execute Notebook 08 and regenerate only the bounded smoke artifact and manifest under explicit authorization, then rerun the focused and complete test suites plus the semantic scan. Preserve this audit and the earlier controlled-step audits as dated evidence of the 16-day state, and continue to leave legitimate 14-day historical lag and rolling features unchanged.

## Completion conclusion

The repository's SCRUM-11 policy, SCRUM-12 notebook, executable feature pipeline, focused tests, and bounded smoke evidence now agree on the approved direct 16-day contract. The alignment is ready for human review. This conclusion is limited to horizon-contract consistency and bounded execution evidence; it is not a claim that SCRUM-13 backtesting, research readiness, production readiness, SCRUM-14, or SCRUM-15 is complete.

No commit, push, merge, branch switch, model training, full feature build, or Kaggle submission was performed.
