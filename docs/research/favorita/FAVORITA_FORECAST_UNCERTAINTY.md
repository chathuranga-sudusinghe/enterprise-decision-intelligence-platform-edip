# Favorita forecast uncertainty — GitHub Issue #128

## Status and engineering scope

The offline implementation is governed by [GitHub Issue #128](https://github.com/chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip/issues/128). GitHub Issues is the sole active execution-management system. The full selected-candidate backtesting run and real-data uncertainty evaluation each require separate owner approval; neither has been executed for this issue. No empirical coverage or width results are claimed. The implementation does not publish a model, modify serving, or implement stockout risk, overstock risk, or replenishment.

The engineering objective is to assess whether a deterministic empirical residual layer around the already-selected Time-Aware LightGBM forecasts provides useful 90% prediction intervals under sequential pre-holdout validation.

## Historical context

The local prototype originated under the legacy SCRUM-21 planning label. That label and the SCRUM-59 tuning and SCRUM-19 holdout identifiers are historical provenance only. This GitHub issue is the active work item.

## Frozen forecasting candidate

Reuse `FavoritaLightGBMAdapter` and the configuration already frozen in `pipelines/models/favorita_model_bundle.py`. No model comparison, parameter search, candidate replacement, or final-holdout evaluation is part of this work.

| Parameter | Value |
|---|---:|
| learning_rate | 0.02757359293934948 |
| num_leaves | 123 |
| min_data_in_leaf | 89 |
| feature_fraction | 0.8394633936788146 |
| num_boost_round | 150 |
| seed | 42 |
| deterministic | true |
| num_threads | 4 |
| force_col_wise | true |
| device_type | cpu |
| objective | regression |

The historical retained Time-Aware predictions use an earlier parameter configuration. They are not selected-candidate residual evidence. SCRUM-59 retains aggregate selected-trial metrics but discarded temporary row predictions. Before proposing four new fits, check whether matching prediction evidence can be recovered through a separately approved artifact inspection. Regeneration requires its own execution approval. The final-origin fitted bundle must not be used to regenerate predictions for earlier validation periods.

## Persisted fold reuse and temporal protection

The selected-candidate runner delegates to `run_favorita_lightgbm_evaluation.run_evaluation`. It reuses the existing Time-Aware fold artifacts under `artifacts/features/favorita_2017_four_fold_time_aware/`, including their manifests, ordered schemas, training/validation counts, and existing row-key/target digest evidence. It never calls the feature builder or rebuilds source data.

The existing evaluator checks canonical fold manifests and Parquet date bounds before fitting. Manifest artifact roots are compared as resolved locations using repository-relative path semantics, so equivalent relative/absolute representations are accepted without rewriting manifests. Different or malformed roots remain rejected; resolution does not depend on the caller's working directory. Each fold receives a separate model trained with targets at or before that fold's origin, exactly as specified by the established temporal contract. Training origins precede their targets; validation targets follow the fold origin. Validation rows are streamed and checked for date/horizon consistency and duplicate keys. The selected runner exposes no parameter override and refuses any existing output directory, including an empty directory left by an interrupted run.

| Fold | Origin | Validation targets | Interval calibration |
|---|---|---|---|
| 1 | 2017-02-28 | 2017-03-01–2017-03-16 | Warm-up only |
| 2 | 2017-04-14 | 2017-04-15–2017-04-30 | Fold 1 |
| 3 | 2017-05-31 | 2017-06-01–2017-06-16 | Folds 1–2 |
| 4 | 2017-07-14 | 2017-07-15–2017-07-30 | Folds 1–3 |

Every calibration target must precede the evaluated fold's origin. A fold's own outcomes and future folds cannot influence its bounds. Fold 1 has no scored interval rows because no earlier calibration set is available. Existing protections for the final holdout, 2017-07-31 through 2017-08-15, remain in force. The uncertainty reader rejects all target dates on or after 2017-07-31.

The protected Favorita holdout has already been evaluated. Its artifacts/results must remain unchanged and must not be rerun or regenerated under Issue #128. Observed holdout outcomes must not be used to retrospectively tune the original forecasting experiment or this interval method. The intended input is vetted pre-holdout prediction evidence; row-date rejection occurs after the prediction file is read and is not a no-read guarantee for a mislabeled file.

## Demand view and interval construction

Original source datasets and raw model predictions remain unchanged. Consistent with the established demand-oriented evaluation convention:

```text
actual_demand = max(actual_unit_sales, 0)
point_forecast = max(prediction, 0)
residual = actual_demand - point_forecast
q05, q95 = numpy.quantile(earlier_residuals, [0.05, 0.95], method="linear")
lower_bound = max(0, point_forecast + q05)
upper_bound = max(0, point_forecast + q95)
interval_width = upper_bound - lower_bound
uncertainty_level = 0.90
```

Residuals are pooled globally across stores, items, and horizons, with one vote per observed prediction row. Quantiles may be asymmetric around zero. Do not force the point prediction to fall inside the interval: doing so would change the predeclared empirical method. Fractional sales and bounds are preserved; no rounding is applied during calculation.

`uncertainty_level = 0.90` denotes nominal interval coverage. It is not achieved coverage, a categorical confidence rating, or a posterior probability for an individual forecast. Actual achieved coverage is reported separately as PICP.

Both raw columns (`actual_unit_sales`, `prediction`) are retained with the fold and forecast keys. Evaluated rows additionally contain `actual_demand`, `residual`, `point_forecast`, `lower_bound`, `upper_bound`, `interval_width`, and `uncertainty_level`. Residuals on evaluated rows are audit evidence; they are not used to calibrate that row's interval.

After sequential evaluation, a separately labelled final calibration entry pools folds 1–4. It has no independent performance score and is saved only for later approved development; this runner does not apply it to protected-holdout forecasts.

## Evaluation definitions

For N evaluated rows:

```text
PICP = sum(lower_bound <= actual_demand <= upper_bound) / N
MPIW = sum(upper_bound - lower_bound) / N
```

Prediction Interval Coverage Probability (PICP) uses inclusive bounds, is stored as a ratio, and is displayed as a percentage. Mean Prediction Interval Width (MPIW) is measured in sales units after clipping. Report both overall across folds 2–4, by evaluated fold, and by horizon 1–16. Overall results are calculated from pooled rows, not unweighted means of group metrics. Every metric record includes its row count and covered count. Width must be interpreted together with coverage; smaller width alone is not evidence of a better interval.

## Artifact lineage and safeguards

Selected-candidate outputs under `artifacts/evaluation/favorita_selected_candidate/`:

- `predictions.parquet`
- `overall_metrics.json`, `fold_metrics.json`, `horizon_metrics.json` (existing point-forecast metrics)
- `run_manifest.json`
- `evaluation_summary.md`

The selected-candidate acceptance record uses schema version 2, status `completed`, and `issue_number: 128`. It records the frozen configuration, candidate identifier, exact prediction-key columns, no-retuning/no-replacement flags, prediction SHA-256 checksum, producer source-code hashes, Git revision, a source-scoped working-tree dirty flag, and runtime versions. `historical_planning_label` retains the old planning label only as provenance. The generic evaluator labels any custom parameters as tuning; the wrapper corrects that flag to false in this run's manifest only. Existing fold lineage and model evidence remain intact. Required producer hashes cover the paths in `PROVENANCE_SOURCE_PATHS`: project dependencies, runtime paths, interval/evaluation logic, temporal/metric/backtesting contracts, feature construction/fold validation, and model/bundle modules. Python, NumPy, pandas, PyArrow, and LightGBM versions must be non-empty strings. Missing/malformed identities and hashes are rejected; saved producer hashes are not compared to the current consumer checkout or silently replaced. Hashes identify bytes but are not independent proof of execution or authenticity.

Uncertainty outputs under `artifacts/evaluation/favorita_uncertainty/`:

- `predictions.parquet`: evaluated rows from folds 2–4 with raw values and intervals.
- `calibration.json`: sequential quantiles, residual counts, date cutoffs, and separate final calibration.
- `overall_metrics.json`, `fold_metrics.json`, `horizon_metrics.json`: PICP and MPIW.
- `run_manifest.json`: input checksums, the saved producer code/runtime identity, separate current consumer code/runtime identity, frozen candidate, output checksums, active GitHub issue, and explicit holdout exclusion.
- `evaluation_summary.md`: all reporting views and research limitations.

The uncertainty runner refuses incomplete or mismatched candidate provenance, different global or per-fold parameters, incorrect feature contracts, holdout exposure, invalid dates/horizons, missing folds/horizons, duplicate prediction keys, non-finite numbers, invalid identifiers, row-count mismatches, and changed source artifacts. Prediction identity is `(forecast_origin, forecast_date, store_nbr, item_nbr)`; canonical checks establish its fold and horizon.

A generic `run.status: completed` is not selected-candidate acceptance: the consumer also requires the completed schema-2 selected-candidate record. The wrapper publishes that record only after source stability, checksumming, and enrichment succeed. On failure or interruption it removes completion claims and its temporary manifest from its exclusively reserved new directory, retaining partial predictions for inspection.

Existing output directories are never overwritten. The uncertainty artifacts are built in a temporary sibling directory; publication reserves the destination exclusively and writes the completion manifest last. A failed selected-candidate run may leave an incomplete directory; inspect it before choosing a new output namespace. There is deliberately no automatic destructive cleanup or overwrite option.

Heavy Parquet files remain ignored by Git under existing conventions. Reviewed lightweight JSON/Markdown engineering evidence is eligible for version control; official publication still requires owner approval. No ignore-rule changes are required.

## Reproducibility and resource requirements

Canonical sorting fixes evaluation row order. Quantile probabilities, interpolation, pooling, clipping, and fold order are fixed; uncertainty involves no random sampling. For the same source evidence, code revision, paths, and pinned environment, the uncertainty artifacts are repeatable, including numerical outputs. Selected backtesting manifests retain execution timestamps; byte-identical training manifests across runs are not expected. Cross-platform/library-version LightGBM results are not guaranteed bitwise identical.

Training uses the existing serial, four-thread CPU evaluator, including its native LightGBM memory needs. A historical four-fold run took approximately 68 minutes; the selected configuration may take longer. No runtime guarantee is made.

The initial uncertainty implementation reads the retained validation predictions into memory and sorts them, then holds approximately five million evaluated interval rows. It does not load training data. Plan for several GB of free memory and output storage; exact quantiles are not approximated or sampled. Resource use at full scale remains unmeasured until the approved run.

## Commands and approval boundary

Run from the repository root in WSL. The following expensive command is prepared for review only; do not execute until approved:

```bash
.venv/bin/python -m pipelines.evaluation.run_favorita_selected_candidate_backtesting \
  --source-path data/processed/favorita_cleaned/favorita_cleaned.parquet \
  --fold-root artifacts/features/favorita_2017_four_fold_time_aware \
  --output-dir artifacts/evaluation/favorita_selected_candidate
```

The following real-data uncertainty command also requires separate owner approval after backtesting succeeds:

```bash
.venv/bin/python -m pipelines.evaluation.run_favorita_uncertainty_evaluation \
  --input-dir artifacts/evaluation/favorita_selected_candidate \
  --output-dir artifacts/evaluation/favorita_uncertainty
```

No real-data results for Issue #128 should be claimed until these steps complete and the generated evidence is reviewed.

Focused verification:

```bash
.venv/bin/pytest -q \
  tests/unit/test_run_favorita_selected_candidate_backtesting.py \
  tests/unit/test_favorita_uncertainty.py \
  tests/unit/test_run_favorita_uncertainty_evaluation.py \
  tests/unit/test_run_favorita_lightgbm_evaluation.py \
  tests/unit/test_favorita_temporal_validation.py \
  tests/unit/test_favorita_backtesting.py
```

The tests use synthetic predictions and tiny synthetic Parquet fixtures. Integration regression coverage retains the real metadata validator and evaluator while replacing the model adapter with a fake, so no LightGBM fitting occurs. Equivalent relative/absolute paths, malformed/different roots, producer provenance, producer/consumer separation, and interrupted completion/publication are covered. They verify numerical examples, clipping, inclusive coverage, unequal-population aggregation, raw-value retention, temporal calibration isolation, order invariance, artifact checksums, exact repeated outputs, and failure safeguards. Existing evaluator/temporal tests cover the reused fold contract. These tests do not measure real-data coverage, validate full-scale memory usage, or complete a real four-fold fit.

## Engineering interpretation and limitations

1. Empirical residual quantiles target 90% coverage but provide no distribution-free finite-sample guarantee in this dependent time-series setting.
2. Global pooling hides differences in error scale across products, stores, sales volumes, and horizons. Per-horizon reporting is diagnostic, not horizon-specific calibration.
3. Residual transfer assumes earlier errors remain informative; seasonality, promotions, changing populations, and distribution shift can reduce coverage.
4. Trial 0 was selected using these validation folds. Sequential residual calibration avoids direct current/future-label leakage into intervals, but does not undo model-selection reuse. Report results as development evidence, not independent final generalization evidence.
5. Only three later windows receive interval evaluation. Many correlated rows do not imply many independent temporal replications. No significance claim or coverage confidence interval is implemented.
6. Observed sales are not latent demand: stockouts can censor sales and returns produce negative net sales. Mapping returns to zero is a deliberate demand-view convention, not recovery of unmet demand.
7. Coverage describes observed store/item/date rows, not unobserved combinations or total lead-time demand. Row intervals do not establish joint or aggregate coverage.
8. Zero clipping can create asymmetric or zero-width intervals near zero demand. Report achieved coverage and width together without modifying the predeclared method after inspecting results.
