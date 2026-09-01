# Favorita Temporal Validation Design

| Field | Value |
|---|---|
| Status | Approved canonical temporal-validation design |
| Canonical replacement date | 2026-08-31 |
| Target | `unit_sales` |
| Forecast strategy | Direct horizon-aware global forecasting |
| Maximum horizon | 16 calendar days |
| Modeling/evaluation scope | `2017-01-01` through `2017-07-30` |
| Validation method | Four-fold expanding-window backtesting |
| Final untouched holdout | `2017-07-31` through `2017-08-15` |

## 1. Purpose

This document records the redesigned canonical four-fold temporal validation design for Favorita forecasting. It defines the approved windows, the `2017-01-01` modeling-target boundary, expanding training histories, leakage prevention, and limitations that must accompany later model results. It replaces both the earlier eight-fold paired-season design and the superseded four-fold schedule that began on `2016-01-01`.

The fold boundaries remain a research design contract. All four canonical Proposed Time-Aware LightGBM folds have completed successfully, while the final holdout remains unscored.

Related authorities:

- [Favorita Dataset Source and Governance](../../governance/FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md);
- [Favorita Research Hypothesis and Experiment Design](FAVORITA_RESEARCH_HYPOTHESIS_AND_EXPERIMENT_DESIGN.md);
- [Favorita Temporal Validation Contract](FAVORITA_TEMPORAL_VALIDATION_CONTRACT.md);
- [Favorita Forecasting Evaluation Metric Contract](FAVORITA_FORECASTING_EVALUATION_METRICS.md); and
- [EDIP Architecture Plan](../../architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md).

## 2. Fixed forecast and data decisions

- supervised target: `unit_sales`;
- forecast origin: end of calendar day `t`;
- `forecast_horizon`: number of calendar days ahead;
- allowed horizons: exact integers 1 through 16;
- forecast target dates: `t+1` through `t+16`;
- strategy: direct horizon-aware global forecasting;
- recursive prediction feedback: forbidden;
- validation duration: 16 calendar days;
- validation method: four-fold expanding-window backtesting; random splitting is forbidden;
- modeling target start: `2017-01-01`;
- modeling/evaluation end: `2017-07-30`;
- approved main fold count: four;
- final holdout origin: `2017-07-30`;
- final untouched holdout: `2017-07-31` through `2017-08-15`;
- sparse observed-row semantics: absent source rows are not created and are not interpreted as zero sales; and
- historical 7-, 14-, and 28-day lags/windows remain historical features, not forecast-length definitions.

Sixteen is the maximum supported horizon, not a minimum forecasting requirement. A shorter operational horizon uses the first `N` predictions from the same ordered direct-horizon contract.

## 3. Preserved source and feature contracts

The full cleaned Favorita dataset remains unchanged. Its verified source contract is 125,497,040 rows, 21 columns, 502 Parquet row groups, 54 stores, 4,036 observed items, date coverage from `2013-01-01` through `2017-08-15`, grain `(date, store_nbr, item_nbr)`, and zero recorded duplicate grain keys.

The new modeling target boundary does not truncate or rewrite the cleaned source. Existing leakage-safe feature engineering is reused unchanged so observations before `2017-01-01` can still supply origin-available historical context for features whose supervised target dates start on `2017-01-01`.

All four canonical Proposed Time-Aware LightGBM folds have been materialized and trained/evaluated successfully (`completed_folds = [1, 2, 3, 4]`). Earlier feasibility artifacts remain historical evidence, not canonical fold artifacts.

## 4. Validation method

EDIP uses expanding-window backtesting. Training targets begin on `2017-01-01` and the eligible history grows through each fold origin, while each validation window remains 16 calendar days. This preserves temporal order and prevents future-label leakage.

All four folds are canonical and complete for the Proposed Time-Aware LightGBM. This four-fold design is the common experimental framework for the SCRUM-18 Contextual LightGBM versus Proposed Time-Aware LightGBM comparison; each comparator must use the same fold boundaries, training scope per fold, horizons, and holdout separation.

```text
Fold 1: 2017-01-01 through 2017-02-28 -> 2017-03-01 through 2017-03-16 validation
Fold 2: 2017-01-01 through 2017-04-14 -> 2017-04-15 through 2017-04-30 validation
Fold 3: 2017-01-01 through 2017-05-31 -> 2017-06-01 through 2017-06-16 validation
Fold 4: 2017-01-01 through 2017-07-14 -> 2017-07-15 through 2017-07-30 validation
```

## 5. Approved four folds

| Fold | Training target dates | Forecast origin | Validation dates |
|---:|---|---|---|
| 1 | `2017-01-01` through `2017-02-28` | `2017-02-28` | `2017-03-01` through `2017-03-16` |
| 2 | `2017-01-01` through `2017-04-14` | `2017-04-14` | `2017-04-15` through `2017-04-30` |
| 3 | `2017-01-01` through `2017-05-31` | `2017-05-31` | `2017-06-01` through `2017-06-16` |
| 4 | `2017-01-01` through `2017-07-14` | `2017-07-14` | `2017-07-15` through `2017-07-30` |

The origins are strictly increasing. Every validation window contains exactly 16 inclusive calendar dates, the windows do not overlap, and the final validation date precedes the protected holdout.

## 6. Expanding-window training rule

For fold origin `O`, every training example must satisfy:

```text
2017-01-01 <= forecast_date <= O
```

An earlier example origin alone is insufficient because its labelled target may still occur after `O`. Each fold is a separate fit. Preprocessing and model fitting use only that fold's eligible training partition, and validation actuals are consumed only for scoring after prediction.

The redesigned canonical fold artifact root is `artifacts/features/favorita_2017_four_fold/`, with manifest metadata bound to that root and the 2017 execution scope. Existing four-fold artifacts under `artifacts/features/favorita_four_fold/`, older eight-fold artifacts under `artifacts/features/favorita_folds/`, and feasibility artifacts remain historical or experimental evidence. They must not be overwritten or silently reused for the redesigned schedule.

The materializer processes one store at a time and the LightGBM adapter avoids a full-fold pandas training frame, but LightGBM's native binned dataset remains in memory. A training-only feasibility run for targets `2017-01-01` through `2017-06-30` succeeded with 277,275,971 model-ready rows, an approximately 2.23 GiB Parquet, approximately 30.70 GiB peak process RAM, and exit status 0 on a 64 GB RAM machine. It used the existing adapter and unchanged parameters.

Fold 4 training through `2017-07-14` succeeded with 313,475,735 training rows, 1,672,872 validation rows, an approximately 2.6 GiB training Parquet, approximately 26 minutes elapsed time, approximately 34.7 GiB peak process RAM, zero swap use, and exit status 0. The current 64 GB CPU LightGBM architecture is therefore approved unchanged.

## 7. Leakage controls

Implementation and evaluation must enforce:

1. no random row splitting;
2. no training target before `2017-01-01` or after the fold origin;
3. no overlapping validation windows;
4. no overlap with the final holdout;
5. no future actual `unit_sales`, transactions, or oil inputs;
6. no reuse of features constructed at a later origin;
7. no preprocessing or vocabulary fit on validation rows;
8. no entity selection based on hidden validation outcomes;
9. no duplicate `(forecast_origin, forecast_date, store_nbr, item_nbr)` examples;
10. no earlier-horizon prediction as a later-horizon input;
11. no densification or inferred zero target for missing sparse rows; and
12. target-date promotion or holiday features only when as-of-origin availability is proven.

Cold-start and insufficient-history handling, weighting or sampling for realized targets represented under multiple earlier origins, and the operational cutoff for same-day transactions and oil remain explicit unresolved controls; the fold dates do not decide them.

## 8. Final untouched holdout

The protected holdout remains:

- origin: `2017-07-30`;
- target dates: `2017-07-31` through `2017-08-15`.

The latest approved validation date is `2017-07-30`, immediately before the holdout starts. Holdout outcomes must not influence fold selection, preprocessing, metrics, model selection, hyperparameter tuning, threshold setting, or workflow tuning.

## 9. Superseded design and artifact separation

The previous eight-fold schedule, its resource-constrained subset `(1, 3, 6, 8)`, and the superseded four-fold schedule beginning on `2016-01-01` are historical methodology only. Existing artifacts must not be deleted, overwritten, rebuilt, or presented as evidence for the redesigned four-fold evaluation.

The active root is `artifacts/features/favorita_2017_four_fold/`; manifests bind artifacts to the redesigned execution scope, and incompatible historical roots remain rejected.

## 10. Research rationale and limitations

The design provides 64 predeclared validation calendar days across four expanding folds within the `2017-01-01` through `2017-07-30` modeling/evaluation scope. Fold-specific metrics and row counts must be reported; robustness beyond these four windows is not claimed.

Limitations include changing store/item populations, sparse target coverage, incomplete representation of months and business regimes, and the fact that four folds do not prove exhaustive historical robustness.

## 11. Remaining decisions

The unresolved controls include:

- the Contextual LightGBM feature schema and the leakage-safe temporal/time-series feature group added by the Proposed Time-Aware LightGBM;
- controlled model configuration and other experimental conditions for a fair feature-information comparison;
- the predeclared comparison and consistency interpretation;
- candidate selection from complete four-fold evidence;
- optional sensitivity or uncertainty analysis;
- later final-holdout evaluation after promotion criteria and selection decisions are frozen; and
- compute, temporary storage, durable artifact, and retention budgets.

Separate approval is still required for SCRUM-18 comparator execution and model selection, uncertainty reporting, optional sensitivity designs, final holdout scoring, Kaggle submission, and deployment.

The four approved folds, the `2017-01-01` modeling target start, the `2017-07-30` evaluation end, the 16-day horizon, expanding-window boundary, and protected final holdout are canonical. The canonical artifact and result roots are implemented and protected from historical reuse.
