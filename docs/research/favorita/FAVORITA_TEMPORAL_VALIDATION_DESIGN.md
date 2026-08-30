# Favorita Temporal Validation Design

| Field | Value |
|---|---|
| Status | Approved canonical temporal-validation design |
| Canonical replacement date | 2026-08-29 |
| Target | `unit_sales` |
| Forecast strategy | Direct horizon-aware global forecasting |
| Maximum horizon | 16 calendar days |
| Modeling target scope | `2016-01-01` through `2017-07-30` |
| Validation method | Four-fold expanding-window backtesting |
| Final untouched holdout | `2017-07-31` through `2017-08-15` |

## 1. Purpose

This document records the canonical four-fold temporal validation design for Favorita forecasting. It defines the approved windows, the 2016 modeling-target boundary, expanding training histories, leakage prevention, and limitations that must accompany later model results. It replaces the earlier eight-fold paired-season design.

It is a research design, not evidence that a model was trained, a backtest ran, metrics were calculated, or the final holdout was scored.

Related authorities:

- [Favorita Dataset Source and Governance](../../governance/FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md);
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
- modeling target start: `2016-01-01`;
- approved main fold count: four;
- final holdout origin: `2017-07-30`;
- final untouched holdout: `2017-07-31` through `2017-08-15`;
- sparse observed-row semantics: absent source rows are not created and are not interpreted as zero sales; and
- historical 7-, 14-, and 28-day lags/windows remain historical features, not forecast-length definitions.

Sixteen is the maximum supported horizon, not a minimum forecasting requirement. A shorter operational horizon uses the first `N` predictions from the same ordered direct-horizon contract.

## 3. Preserved source and feature contracts

The full cleaned Favorita dataset remains unchanged. Its verified source contract is 125,497,040 rows, 21 columns, 502 Parquet row groups, 54 stores, 4,036 observed items, date coverage from `2013-01-01` through `2017-08-15`, grain `(date, store_nbr, item_nbr)`, and zero recorded duplicate grain keys.

The new modeling target boundary does not truncate or rewrite the cleaned source. Existing leakage-safe feature engineering is reused unchanged so pre-2016 observations can still supply historical context for features whose supervised target dates start on `2016-01-01`.

The new four-fold model-ready artifacts have not yet been materialized, so this design does not claim new fold row counts or executed scoring evidence.

## 4. Validation method

EDIP uses expanding-window backtesting. Training targets begin on `2016-01-01` and the eligible history grows through each fold origin, while each validation window remains 16 calendar days. This preserves temporal order and prevents future-label leakage.

All four folds are canonical. A single-fold runner executes exactly one selected fold per invocation so real-data runs can be controlled and accumulated safely without exposing the final holdout.

```text
Fold 1: 2016-01-01 through 2016-06-30 -> next 16 days validation
Fold 2: 2016-01-01 through 2016-12-31 -> next 16 days validation
Fold 3: 2016-01-01 through 2017-04-30 -> next 16 days validation
Fold 4: 2016-01-01 through 2017-07-14 -> next 16 days validation
```

## 5. Approved four folds

| Fold | Training target dates | Forecast origin | Validation dates |
|---:|---|---|---|
| 1 | `2016-01-01` through `2016-06-30` | `2016-06-30` | `2016-07-01` through `2016-07-16` |
| 2 | `2016-01-01` through `2016-12-31` | `2016-12-31` | `2017-01-01` through `2017-01-16` |
| 3 | `2016-01-01` through `2017-04-30` | `2017-04-30` | `2017-05-01` through `2017-05-16` |
| 4 | `2016-01-01` through `2017-07-14` | `2017-07-14` | `2017-07-15` through `2017-07-30` |

The origins are strictly increasing. Every validation window contains exactly 16 inclusive calendar dates, the windows do not overlap, and the final validation date precedes the protected holdout.

## 6. Expanding-window training rule

For fold origin `O`, every training example must satisfy:

```text
2016-01-01 <= forecast_date <= O
```

An earlier example origin alone is insufficient because its labelled target may still occur after `O`. Each fold is a separate fit. Preprocessing and model fitting use only that fold's eligible training partition, and validation actuals are consumed only for scoring after prediction.

Fold artifacts are materialized serially under `artifacts/features/favorita_four_fold/`. The existing eight-fold artifacts under `artifacts/features/favorita_folds/` remain untouched historical evidence and are incompatible with the new canonical experiment.

The materializer processes one store at a time and the LightGBM adapter avoids a full-fold pandas training frame, but LightGBM's native binned dataset remains in memory. Full real-data peak RAM, runtime, temporary-disk demand, and final artifact sizes remain unmeasured; real Fold 1 materialization and training therefore require separate execution approval and resource observation.

## 7. Leakage controls

Implementation and evaluation must enforce:

1. no random row splitting;
2. no training target before `2016-01-01` or after the fold origin;
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

The previous eight-fold schedule and the resource-constrained subset `(1, 3, 6, 8)` are no longer active methodology. Existing old artifacts must not be deleted, overwritten, rebuilt, or presented as evidence for this four-fold experiment.

The separate four-fold artifact root makes the methodology boundary explicit. Reuse within that root is allowed only when artifact manifests and Parquet metadata match the complete canonical four-fold contract.

## 10. Research rationale and limitations

The design provides 64 predeclared validation calendar days across four expanding folds. It supports a controlled medium-scale experiment within the active 2016-2017 modeling target scope. Fold-specific metrics and row counts must be reported; robustness beyond these four windows is not claimed.

Limitations include changing store/item populations, sparse target coverage, incomplete representation of months and business regimes, unmeasured full-data compute cost, and the fact that four folds do not prove exhaustive historical robustness.

## 11. Remaining decisions

The unresolved controls include:

- real-data fold materialization, training execution, and metric reporting by fold and horizon;
- uncertainty reporting and optional sensitivity designs;
- entity eligibility, cold-start handling, and fixed or dynamic population policy;
- full real-data resource sizing and execution approval;
- preprocessing, categorical, nullable-feature, and feature-availability policy;
- the model-input role of `forecast_horizon`;
- weighting or sampling for targets represented under multiple origins; and
- compute, temporary storage, durable artifact, and retention budgets.

Separate approval is still required for real-data fold materialization and training execution, model comparison or selection, uncertainty reporting, optional sensitivity designs, final holdout scoring, Kaggle submission, and deployment.

The four folds, the `2016-01-01` modeling target start, the 16-day horizon, expanding-window boundary, separate artifact location, and protected final holdout are canonical.
