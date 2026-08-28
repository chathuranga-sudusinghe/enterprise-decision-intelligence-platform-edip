# Favorita Temporal Validation Design

| Field | Value |
|---|---|
| Status | Approved main temporal-validation design |
| Approval date | 2026-08-22 |
| Target | `unit_sales` |
| Forecast strategy | Direct horizon-aware global forecasting |
| Maximum horizon | 16 calendar days |
| Validation method | Eight-fold expanding-window backtesting |
| Final untouched holdout | `2017-07-31` through `2017-08-15` |

## 1. Purpose

This document records the approved evidence-based temporal validation design for Favorita forecasting. It defines why the eight validation windows were selected, how expanding training histories are bounded, how leakage is prevented, and which limitations must accompany later model results.

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
- validation method: eight-fold expanding-window backtesting; random splitting is forbidden;
- approved main fold count: eight;
- final holdout origin: `2017-07-30`;
- final untouched holdout: `2017-07-31` through `2017-08-15`;
- sparse observed-row semantics: absent source rows are not created and are not interpreted as zero sales;
- historical 7-, 14-, and 28-day lags/windows remain historical features, not forecast-length definitions.

Sixteen is the maximum supported horizon, not a minimum forecasting requirement. A shorter operational horizon uses the first `N` predictions from the same ordered direct-horizon contract.

## 3. Temporal data evidence

The cleaned source-derived dataset records:

| Property | Verified value |
|---|---:|
| Date minimum | `2013-01-01` |
| Date maximum | `2017-08-15` |
| Rows | 125,497,040 |
| Columns | 21 |
| Row groups | 502 |
| Stores | 54 |
| Observed items | 4,036 |
| Grain | `(date, store_nbr, item_nbr)` |
| Recorded duplicate grain keys | 0 |

Parquet row group: **a physical block of rows stored together inside a Parquet file, allowing selective reading of relevant blocks instead of scanning the full dataset.**

The cleaned-data contract preserves source rows without densification, inferred zero sales, or feature engineering.

Fold coverage was measured through a bounded read: row-group date statistics identified relevant groups, then only the date and holiday/event lineage fields required for the design were projected. The scan read 59 of 502 row groups and 14,750,000 rows rather than materializing the complete dataset.

All eight approved validation windows contain observed targets on every one of their 16 calendar dates. Together they contain 12,678,867 cleaned source target rows. These are source-row counts, not guaranteed final scoring counts; entity eligibility, history completeness, and feature-null rules may reduce the evaluated population.

## 4. Common time-series validation methods

| Method | How it works | EDIP decision |
|---|---|---|
| Single holdout / temporal split | Trains on past data and validates on one future period. | Not selected: one validation period gives limited evidence about stability across seasons and business regimes. |
| Rolling-window backtesting | Moves a fixed-size training window forward; older observations leave as newer observations enter. | Not selected: EDIP needs to retain the full available historical sales history. |
| Expanding-window backtesting | Keeps the same historical starting point, adds more history at each fold, and evaluates the next fixed future window. | **SELECTED.** |
| Blocked time-series cross-validation | Uses separate chronological training and validation blocks while preserving time order. | Not selected as the main method: the approved design requires an expanding training history. |
| Random cross-validation | Randomly distributes rows between training and validation sets. | Rejected: future information can influence training and create temporal leakage. |

EDIP's validation method is **eight-fold expanding-window backtesting**. The training history grows at each fold while each validation window remains 16 calendar days. This preserves temporal order, prevents future-data leakage, retains all available historical information, and evaluates performance across multiple seasonal and business regimes.

The approved validation design contains eight expanding-window folds. The initial full-scale LightGBM experiment executes folds 1, 3, 6, and 8 as a representative resource-constrained subset because the full eight-fold feature-materialization and model-training workload exceeds the current local compute/time budget. This subset preserves chronological separation and multiple seasonal regimes but provides less robustness evidence than the complete eight-fold protocol.

```text
Fold 1: shorter historical training period -> next 16 days validation
Fold 2: larger historical training period  -> next 16 days validation
...
Fold 8: largest approved training period   -> next 16 days validation
```

## 5. Fold-selection methodology

The approved strategy is **paired-season, recent-two-cycle stratification**:

1. represent four interpretable calendar regimes: September, the December holiday lead-in, mid-April through 1 May, and early July;
2. repeat each regime across two annual cycles where supported;
3. keep every target window non-overlapping and strictly before the final holdout;
4. require observed targets on all 16 calendar dates;
5. retain substantial source history before the earliest origin; and
6. use holiday/event lineage only to characterize evaluation regimes, not as proof that post-origin actuals were available as model features.

The design favors relevance to the 2017 forecasting setting while retaining two annual cycles and at least 973 days of source history before the earliest origin.

## 6. Alternatives considered

| Strategy | Strength | Main weakness | Decision |
|---|---|---|---|
| Eight adjacent recent windows | Strong latest-regime emphasis | Highly correlated and seasonally narrow | Rejected for the main design |
| Even spacing across 2013-2017 | Broad chronology | Early population differs; equal spacing lacks a business rationale | Optional sensitivity design only |
| Fixed quarterly origins | Simple and reproducible | Can miss the supported holiday lead-in and earthquake stress period | Not selected |
| Paired-season, recent-two-cycle | Comparable seasonal windows, recency, normal and exceptional regimes | Not equally spaced; does not cover every month/year | Approved main design |

A December 16-31 window was rejected because the cleaned source contains no observed target rows on December 25. Filling that date would violate sparse-row governance. December 9-24 retains a complete 16-date window and the recorded pre-Christmas regime.

## 7. Approved eight folds

| Fold | Available source history through origin | Forecast origin | Validation start | Validation end | Observed target rows | Research rationale |
|---:|---|---|---|---|---:|---|
| 1 | `2013-01-01` to `2015-08-31` (973 days) | `2015-08-31` | `2015-09-01` | `2015-09-16` | 1,387,388 | First September shoulder-season reference |
| 2 | `2013-01-01` to `2015-12-08` (1,072 days) | `2015-12-08` | `2015-12-09` | `2015-12-24` | 1,525,492 | Pre-Christmas regime with recorded `Navidad-4` through `Navidad-1` lineage |
| 3 | `2013-01-01` to `2016-04-15` (1,201 days) | `2016-04-15` | `2016-04-16` | `2016-05-01` | 1,546,383 | `Terremoto Manabi` day and recorded aftermath stress period |
| 4 | `2013-01-01` to `2016-06-30` (1,277 days) | `2016-06-30` | `2016-07-01` | `2016-07-16` | 1,561,914 | Early-July mid-year comparison |
| 5 | `2013-01-01` to `2016-08-31` (1,339 days) | `2016-08-31` | `2016-09-01` | `2016-09-16` | 1,539,969 | Calendar-matched September comparison for Fold 1 |
| 6 | `2013-01-01` to `2016-12-08` (1,438 days) | `2016-12-08` | `2016-12-09` | `2016-12-24` | 1,694,286 | Repeated pre-Christmas lead-in |
| 7 | `2013-01-01` to `2017-04-15` (1,566 days) | `2017-04-15` | `2017-04-16` | `2017-05-01` | 1,705,829 | Calendar-matched comparison for Fold 3 without the 2016 earthquake sequence |
| 8 | `2013-01-01` to `2017-06-30` (1,642 days) | `2017-06-30` | `2017-07-01` | `2017-07-16` | 1,717,606 | Most recent approved pre-holdout window and July comparison |

The origin sequence is strictly increasing. All windows are exactly 16 inclusive calendar days, no approved validation windows overlap, and every validation window ends before the final holdout.

## 8. Expanding-window training rule

Each fold uses all eligible historical model-ready training records whose labels are available on or before that fold's forecast origin. No additional historical-origin sampling cadence is approved. SCRUM-15 now provides serial fold-wise Parquet materialization and evaluation orchestration that preserves full eligible history and entity coverage without changing these temporal boundaries. The production adapter scans training Parquet in bounded batches, retains training-only categorical/null metadata, stores labels in a temporary disk memory map, and supplies feature ranges to LightGBM through Sequence; it does not create full-fold BacktestExample tuples or a full-fold training pandas frame. Validation is also consumed in bounded Parquet batches. Each batch is contract-checked, predicted, written directly to staged row-level evidence Parquet, and discarded after updating fold, horizon, and pooled metric accumulators; no full-fold validation pandas frame or EvaluationEvidence tuple is retained. Runtime duplicate checks use the feature artifact's contiguous single-store block and strict within-store key ordering guarantees, so cross-batch state is bounded by the 54 stores. LightGBM's native binned training dataset remains in memory, so this removes Python-object/DataFrame amplification but is not true out-of-core training. The implementation is validated with bounded fixtures only; full real-data peak RAM remains unmeasured, and no full real-data backtest, reported metrics, model selection, or final-holdout scoring is claimed.

For fold origin `O`:

- training begins at the earliest eligible historical data and expands through `O`;
- every training example must satisfy `forecast_date <= O`;
- checking only `training_example.forecast_origin < O` is insufficient because its label may still occur after `O`;
- validation labels belong only to `O+1` through `O+16`;
- each fold is a separate fit;
- preprocessing, encoding, imputation, feature selection, thresholds, vocabularies, and model fitting use only the fold's eligible training subset;
- validation actuals are joined only after predictions are produced;
- an earlier validation period may enter a later fold's training history only after it is in that later fold's simulated past.

## 9. Leakage controls

Later implementation and evaluation must enforce:

1. no random row splitting;
2. no training label after the fold origin;
3. no overlapping validation windows;
4. no overlap with the final holdout;
5. no future actual `unit_sales`, transactions, or oil inputs;
6. no reuse of features constructed at a later origin;
7. no preprocessing or vocabulary fit on validation rows;
8. no entity selection based on hidden validation outcomes;
9. no duplicate `(forecast_origin, forecast_date, store_nbr, item_nbr)` examples;
10. no earlier-horizon prediction as a later-horizon input;
11. no densification or inferred zero target for missing sparse rows;
12. explicit cold-start and insufficient-history policy;
13. explicit weighting/sampling policy for realized targets represented under multiple earlier origins;
14. explicit operational cutoff for same-day transactions and oil; and
15. target-date promotion or holiday features only when as-of-origin availability is proven.

Holiday and earthquake lineage in this design is descriptive. It does not authorize post-origin actual event fields as model inputs or establish causal effects.

## 10. Final untouched holdout

The protected holdout is:

- origin: `2017-07-30`;
- target dates: `2017-07-31` through `2017-08-15`.

The latest approved validation date is `2017-07-16`. The intervening dates `2017-07-17` through `2017-07-30` are outside all approved validation windows.

Holdout outcomes must not influence fold selection, preprocessing, metric selection, model selection, hyperparameter tuning, threshold setting, or sensitivity design. They remain unavailable until the validation protocol and modeling decisions are frozen.

## 11. Research rationale

The design provides:

- 128 validation calendar days;
- 12,678,867 observed source target rows;
- four paired calendar regimes;
- two annual cycles;
- one documented exceptional shock window;
- two holiday lead-in windows; and
- a recent pre-holdout comparison.

The paired structure supports transparent descriptive comparison of September 2015/2016, December 2015/2016, April-May 2016/2017, and July 2016/2017 while retaining expanding history.

These are descriptive evaluation strata, not causal matched pairs. Store/item availability, promotions, macroeconomic conditions, assortment, and operations differ between years. Fold-specific results and dispersion must be reported rather than relying only on one pooled score.

## 12. Threats and limitations

- Source row counts precede entity, history, and null-feature eligibility.
- Store/item population changes across folds.
- Validation intentionally excludes observations before September 2015.
- Several months are not directly represented.
- The earthquake fold may materially affect aggregate results and requires separate reporting and predeclared sensitivity analysis.
- Holiday metadata is retrospective unless publication-time availability is proven.
- The sparse source does not provide an identical dense entity panel across dates or horizons.
- Compute cost for full fold construction and fitting remains unmeasured.
- Fold dates do not define uncertainty, preprocessing, or model choice. Metric and negative-target policies are defined by the separate SCRUM-17 contract.
- Eight folds do not prove exhaustive robustness across all historical regimes.

Optional sensitivity designs may examine evenly spaced history, earthquake-excluded aggregates, or a more recent-heavy schedule. They must be pre-specified before viewing final holdout performance.

## 13. Remaining decisions

Human approval is still required for:

- backtest execution and metric reporting by fold and horizon;
- uncertainty reporting;
- entity eligibility and fixed/dynamic population;
- full real-data resource sizing and execution approval;
- preprocessing, categorical, nullable-feature, and feature-availability policy;
- the model-input role of `forecast_horizon`;
- earthquake sensitivity and optional folds;
- compute, storage, and artifact budgets.

The eight folds, their windows, the 16-day maximum horizon, the expanding-window boundary, and the final holdout are approved. The remaining decisions above are not.
