# SCRUM-13 Expanding-Window Fold Design Audit

## 1. Audit metadata

| Field | Value |
|---|---|
| Date | 2026-08-21 |
| Approval date | 2026-08-22 |
| Approved by | Project owner |
| Branch | `feature/scrum-13-temporal-validation-backtesting` |
| Work item | SCRUM-13 — design evidence for expanding-window temporal validation folds |
| Scope | Design and evidence audit only; no backtesting implementation |
| Status | **APPROVED — FOLD DESIGN LOCKED FOR SCRUM-13** |

## 2. Purpose

This audit records the eight approved evidence-based Favorita validation origins for later expanding-window backtesting. It uses the approved 16-calendar-day direct horizon-aware forecast contract, the cleaned source-derived dataset, saved notebook evidence, executable feature-contract code, focused tests, and the current SCRUM-13 audit trail.

The project owner approved the paired-season, recent-two-cycle strategy, all eight exact origins and corresponding validation windows, and retention of the final untouched holdout on 2026-08-22. The approved fold design is now the active SCRUM-13 temporal-validation fold specification. This audit is not an implementation, a completed backtest, or a claim that a metric, preprocessing policy, entity policy, or model has been selected.

## 3. Approved inputs / existing decisions

The following inputs are treated as fixed and are not reconsidered here:

- supervised target: `unit_sales`;
- forecast origin: end of calendar day `t`;
- strategy: direct horizon-aware forecasting with no recursive prediction feedback;
- exact `forecast_horizon` set: integers 1 through 16;
- target dates: `t+1` through `t+16`;
- validation duration: 16 calendar days;
- temporal validation: expanding-window backtesting; random splitting is forbidden;
- approved main validation-fold count: eight;
- final holdout origin: `2017-07-30`;
- final untouched holdout: `2017-07-31` through `2017-08-15`;
- historical 7-, 14-, and 28-day lags/windows remain unchanged, including `sales_lag_14`, `sales_rolling_mean_14`, `transactions_lag_14`, and `transactions_mean_14d`;
- sparse observed-row semantics remain in force: missing `(date, store_nbr, item_nbr)` rows are not created and absence is not interpreted as zero sales.

The final holdout decision supplied for this audit supersedes older design-stage text that left the holdout policy unresolved. Historical audits remain unchanged as evidence of their original state.

## 4. Evidence inspected

### Notebooks

- `notebooks/favorita/01_data_inventory_and_quality.ipynb`
- `notebooks/favorita/02_temporal_sales_and_coverage_eda.ipynb`
- `notebooks/favorita/03_build_favorita_merged_base.ipynb`
- `notebooks/favorita/04_review_merged_dataset_quality.ipynb`
- `notebooks/favorita/05_define_data_cleaning_rules.ipynb`
- `notebooks/favorita/06_create_cleaned_favorita_dataset.ipynb`
- `notebooks/favorita/07_define_leakage_safe_feature_engineering_policy.ipynb`
- `notebooks/favorita/08_build_model_ready_feature_dataset.ipynb`

All eight files parsed as nbformat 4.5 notebooks. Their combined 142 code cells had no saved error outputs. Notebook 07 is the Markdown-only leakage policy; Notebook 08 supplies bounded executable evidence for the 16-horizon feature contract.

### Code and tests

- `pipelines/features/favorita_model_ready.py`
- `tests/unit/test_favorita_model_ready_features.py`

The pipeline declares `TARGET_COLUMN = "unit_sales"`, `FORECAST_HORIZONS = tuple(range(1, 17))`, end-of-day origin semantics, direct horizon awareness, and recursive feedback disabled. The focused tests assert the exact 1-through-16 set and deterministic 32-row fixture construction.

### SCRUM-13 audits

- `docs/audits/SCRUM_13_TEMPORAL_VALIDATION_BACKTESTING_READINESS_AUDIT.md`
- `docs/audits/SCRUM_13_16_DAY_HORIZON_NOTEBOOK_ALIGNMENT_AUDIT.md`
- `docs/audits/SCRUM_13_16_DAY_HORIZON_PIPELINE_ALIGNMENT_AUDIT.md`
- `docs/audits/SCRUM_13_16_DAY_HORIZON_COMPLETION_AUDIT.md`

The readiness audit is explicitly pre-alignment historical evidence. Its earlier recent-period candidate set covered only the last 12 weeks and identified lack of seasonal robustness as a limitation. The 16-day completion audit is the current forecast-contract source of truth.

### Cleaned data evidence

- `data/processed/favorita_cleaned/cleaning_manifest.json`
- `data/processed/favorita_cleaned/favorita_cleaned.parquet`

The Parquet was inspected read-only with footer metadata, row-group date statistics, and bounded row-group reads. The full dataset was not loaded, rewritten, regenerated, or mutated.

## 5. Confirmed temporal-data coverage

The manifest and current Parquet footer agree on:

| Property | Confirmed value |
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

The manifest records source-row-only preservation, no densification, no inferred zero sales, no imputation, and no feature engineering. Therefore, a date with no observed rows cannot be repaired for validation by synthesizing targets.

For this audit, exact fold counts were obtained by projecting only `date` and six holiday/event lineage columns from row groups whose footer date ranges intersected a candidate window. The bounded scan read 59 of 502 row groups sequentially, covering 14,750,000 rows across the selected row groups. It did not materialize the complete dataset.

All eight approved windows contain observed targets on every one of their 16 calendar dates. Together they contain 12,678,867 cleaned source target rows. These are observed source-row counts, not guaranteed model-ready evaluation-row counts; later entity eligibility, history completeness, and feature-null rules can reduce the scored population.

## 6. Fold-selection methodology

The selected method is a **paired-season, recent-two-cycle stratification**:

1. Use four interpretable calendar regimes: September, the December holiday lead-in, mid-April through 1 May, and early July.
2. Repeat each regime in two annual cycles where the available data allows it.
3. Keep every 16-day target window non-overlapping and strictly before the approved holdout.
4. Require all 16 calendar dates to have at least one observed target row globally.
5. Retain at least 973 days of source history before the earliest approved origin, far exceeding the maximum approved 28-day historical lookback.
6. Use descriptive holiday/event lineage only to characterize regimes. It is not treated as causal evidence and is not authorization to expose post-origin holiday actuals as model features.

This design intentionally pairs the April 2016 `Terremoto Manabi` period with the same calendar window in 2017. That pairing makes an exceptional shock visible without making the entire evaluation recent-only or treating the shock as a recurring seasonal effect. The two December windows contain the recorded `Navidad-4` through `Navidad-1` lead-in. The September and July pairs provide less event-concentrated comparison periods.

An initially considered December 16–31 window was rejected in both years because the cleaned dataset has no observed target rows on December 25. Under the approved sparse-row policy, filling that missing date would be invalid. Moving the paired December windows to December 9–24 preserves a complete 16-date window and still captures the recorded pre-Christmas regime.

## 7. Alternative spacing strategies considered

| Strategy | Strength | Main weakness | Decision |
|---|---|---|---|
| Eight adjacent or near-adjacent recent windows | Strongest emphasis on the latest operating regime | Highly correlated windows; repeats a narrow season; the earlier readiness audit already identified last-12-weeks seasonal weakness | Rejected for the main design |
| Even spacing across the full 2013–2017 history | Maximum chronological breadth | Early folds have a less mature store/item population and may over-weight older operating regimes; equal spacing is not itself a research rationale | Retain only as a possible sensitivity design |
| Fixed quarterly origins | Simple and reproducible seasonal coverage | Calendar-quarter anchors can miss the supported December holiday lead-in and the April 2016 shock; repeated anchors may still introduce day-of-month bias | Not selected |
| Paired-season, recent-two-cycle stratification | Repeats comparable seasonal windows, includes normal and exceptional regimes, preserves recency, and supports paired interpretation | Not equally spaced; does not cover every month or all years | **Approved for SCRUM-13** |

The approved strategy is biased toward recent data: validation starts in September 2015 even though source history begins in January 2013. This is deliberate to improve relevance to the 2017 forecasting setting while retaining two annual cycles and substantial expanding training history. It does not prove robustness to every earlier structural regime.

## 8. Approved 8 fold origins

**APPROVED — FOLD DESIGN LOCKED FOR SCRUM-13**

1. `2015-08-31`
2. `2015-12-08`
3. `2016-04-15`
4. `2016-06-30`
5. `2016-08-31`
6. `2016-12-08`
7. `2017-04-15`
8. `2017-06-30`

The origin sequence is strictly increasing. Every origin precedes `2017-07-30`, and no approved validation window overlaps another approved window or the final holdout.

### Human approval record

- Approval date: 2026-08-22
- Approved by: Project owner
- Decision:
  - paired-season, recent-two-cycle spacing strategy approved;
  - all eight forecast origins approved;
  - all corresponding 16-calendar-day validation windows approved;
  - final untouched holdout retained.
- Remaining unresolved SCRUM-13 decisions:
  - metric policy and fold aggregation;
  - negative-`unit_sales` treatment;
  - entity eligibility and population policy;
  - training-origin schedule inside each fold;
  - preprocessing and feature-availability rules;
  - `forecast_horizon` model-input role;
  - earthquake and optional sensitivity-fold policy;
  - compute and artifact budgets.

This approval locks the fold specification only. It does not approve or imply approval of any remaining decision above.

## 9. Fold table

| Fold | Forecast origin | Validation start | Validation end | Duration | Observed target rows | Available source history through origin | Rationale and supported regime | Coverage concern |
|---:|---|---|---|---:|---:|---|---|---|
| 1 | `2015-08-31` | `2015-09-01` | `2015-09-16` | 16 calendar days | 1,387,388 | `2013-01-01`–`2015-08-31` (973 days; ~2.7 years) | First September shoulder-season reference; no holiday/event record appeared in the bounded window scan | Complete 16-date coverage; earlier entity population may be smaller than later folds |
| 2 | `2015-12-08` | `2015-12-09` | `2015-12-24` | 16 calendar days | 1,525,492 | `2013-01-01`–`2015-12-08` (1,072 days; ~2.9 years) | December demand regime with recorded `Navidad-4` through `Navidad-1` lead-in | Complete 16-date coverage; holiday effects are descriptive and publication-time feature availability is unproven |
| 3 | `2016-04-15` | `2016-04-16` | `2016-05-01` | 16 calendar days | 1,546,383 | `2013-01-01`–`2016-04-15` (1,201 days; ~3.3 years) | Exceptional `Terremoto Manabi` day and 15 recorded aftermath days; useful stress-regime evidence | Complete 16-date coverage; shock sensitivity could dominate aggregate results and must be reported separately |
| 4 | `2016-06-30` | `2016-07-01` | `2016-07-16` | 16 calendar days | 1,561,914 | `2013-01-01`–`2016-06-30` (1,277 days; ~3.5 years) | Early-July mid-year comparison window; only local July 3 event lineage was recorded | Complete 16-date coverage; local events may affect only part of the store population |
| 5 | `2016-08-31` | `2016-09-01` | `2016-09-16` | 16 calendar days | 1,539,969 | `2013-01-01`–`2016-08-31` (1,339 days; ~3.7 years) | Repeats Fold 1's September calendar regime one year later | Complete 16-date coverage; population drift limits a pure year-over-year interpretation |
| 6 | `2016-12-08` | `2016-12-09` | `2016-12-24` | 16 calendar days | 1,694,286 | `2013-01-01`–`2016-12-08` (1,438 days; ~3.9 years) | Repeats Fold 2's pre-Christmas window with the same recorded national holiday lead-in | Complete 16-date coverage; holiday metadata remains descriptive unless as-of-origin publication is proven |
| 7 | `2017-04-15` | `2017-04-16` | `2017-05-01` | 16 calendar days | 1,705,829 | `2013-01-01`–`2017-04-15` (1,566 days; ~4.3 years) | Calendar-matched comparison for Fold 3 without the 2016 earthquake sequence; includes local April 21 and national 1 May holiday lineage | Complete 16-date coverage; not a causal control for the earthquake fold |
| 8 | `2017-06-30` | `2017-07-01` | `2017-07-16` | 16 calendar days | 1,717,606 | `2013-01-01`–`2017-06-30` (1,642 days; ~4.5 years) | Most recent approved window and year-matched early-July comparison for Fold 4 | Complete 16-date coverage; remains 14 calendar days clear of the holdout start |

Each 16-day window contains two complete seven-day cycles plus two additional days. The exact weekday mix therefore differs slightly by origin, which should be retained in fold-level reporting because Notebook 02 records material descriptive weekday variation.

## 10. Expanding-window training-boundary rule

For a validation fold with forecast origin `O`:

- the training window begins at the earliest eligible historical training data and expands through `O`;
- every training example must satisfy `forecast_date <= O`;
- checking only `training_example.forecast_origin < O` is insufficient because that example's label could still occur after `O`;
- validation labels belong only to `O+1` through `O+16`;
- preprocessing, encoding, imputation, feature selection, thresholds, vocabularies, and model fitting must use only the fold's eligible training subset;
- validation actuals may be joined only after predictions have been produced;
- a completed earlier validation period may enter a later fold's training history only after it is in the later fold's simulated past.

This rule is documented here for later implementation. No fold-construction or training-boundary code was created in this task.

## 11. Final untouched holdout confirmation

The approved holdout remains:

- holdout origin: `2017-07-30`;
- untouched target dates: `2017-07-31` through `2017-08-15`.

The latest approved validation date is `2017-07-16`; therefore none of the eight validation windows overlaps the holdout. The 14 intervening dates `2017-07-17` through `2017-07-30` remain outside the approved validation windows.

The holdout target outcomes were not used to choose fold dates, compare spacing strategies, select a metric, define preprocessing, select a model, or tune any parameter. The approved holdout boundary was used only as a do-not-cross constraint. The final holdout must remain unavailable for model and workflow decisions until the complete validation design, metric policy, preprocessing policy, model selection, and tuning decisions are frozen.

## 12. Leakage considerations

- Random train/validation splitting remains forbidden.
- The training-label cutoff is `forecast_date <= fold_origin`.
- Historical lags and rolling features must remain origin-bounded; lag-14 and rolling-14 features are valid historical features and are not forecast-length definitions.
- Future actual `unit_sales`, transactions, oil prices, promotions, holiday actuals, and earthquake-derived features must not leak into fold inputs.
- Target-date promotions or holiday fields may be features only if their planned or published values can be proven available at the fold origin with the same semantics. The cleaned artifact does not provide that publication-time evidence.
- Holiday/event lineage used in this audit characterizes validation regimes only; it does not authorize those post-origin actual fields as model features.
- Earlier-horizon predictions must never become later-horizon inputs.
- Fold-level preprocessing and learned transformations must be fitted independently on the eligible expanding training subset.

## 13. Research justification

The approved eight-fold design is defensible for the main evaluation because they provide 128 validation calendar days, 12,678,867 observed source target rows, four paired calendar regimes, two annual cycles, one documented exceptional shock window, two holiday lead-in windows, and a recent pre-holdout comparison. The design is more representative than arbitrary dates or eight adjacent recent windows because each origin has an explicit coverage and temporal-regime rationale.

The paired structure supports transparent dissertation reporting: September 2015/2016, December 2015/2016, April–May 2016/2017, and July 2016/2017 can be compared as calendar-matched pairs while preserving expanding training history. These are descriptive evaluation strata, not causal matched pairs; store/item availability, promotions, economic conditions, and other factors can differ between years.

The eight approved folds should be sufficient for the main evaluation if human review also approves metric definitions, negative-target treatment, fold aggregation, entity eligibility, preprocessing, and sensitivity reporting. Eight folds are not sufficient to claim exhaustive robustness across all months, all earlier years, every holiday, every store-opening regime, or every extreme event. Fold-specific results and dispersion should be reported rather than relying only on one pooled score.

Optional sensitivity folds could later test an evenly spaced full-history design, an earthquake-excluded aggregate, or a more recent-heavy schedule. Those checks should be specified before viewing final holdout performance and should not replace the approved eight-fold main design without a documented decision.

## 14. Risks and limitations

1. **Observed source rows are not final scoring rows.** The exact counts in this audit precede entity-eligibility, feature-history, and null-feature filtering.
2. **Population drift exists.** Fold row counts rise from 1,387,388 to 1,717,606, and stores/items can enter or leave observed coverage. Metrics need a declared population and weighting policy.
3. **Recent-period bias is intentional.** Validation excludes 2013 through August 2015 despite their availability.
4. **Seasonal coverage is selective.** January, February, March, May, June, August, October, and November are not directly represented as standalone windows.
5. **The earthquake fold is exceptional.** Its inclusion improves stress coverage but may materially change aggregate results; report it separately and test sensitivity without silently removing it.
6. **Holiday metadata is retrospective.** Actual event records support regime description, not necessarily feature availability at the forecast origin.
7. **No causal conclusions follow.** Differences between paired windows can reflect population, promotion, macroeconomic, assortment, or operational changes.
8. **Sparse-row semantics remain.** The audit verifies at least one observed row on every selected date, not a dense store-item panel or identical entity coverage on every horizon.
9. **Compute cost is not yet measured.** Full model-ready fold construction and model fitting were outside scope.
10. **No metric policy is approved here.** Fold count and dates alone do not define weighting, transformations, aggregation, uncertainty, or statistical comparison.

## 15. Remaining decisions requiring human approval

The fold strategy, eight exact origins, corresponding validation windows, and final untouched holdout are resolved and approved. Before implementation, a human reviewer must still approve:

1. metric definitions, negative-`unit_sales` treatment, perishable weighting, fold aggregation, and uncertainty reporting;
2. the entity-eligibility and fixed-versus-dynamic population policy;
3. the training-origin schedule used to create eligible historical examples within each expanding window;
4. preprocessing, encoding, imputation, and feature-availability policies at each fold cutoff;
5. whether `forecast_horizon` is included as a model input and how that role is represented;
6. the pre-specified earthquake-fold sensitivity and separate-reporting policy;
7. whether any optional sensitivity folds will be pre-registered before model selection;
8. compute and artifact budgets for later implementation.

The approved fold specification, final holdout dates, and 16-day forecast contract are locked decisions. The remaining items above are intentionally unresolved.

## 16. Explicit non-scope

This task did not:

- create Notebook 09;
- implement a backtesting module, fold constructor, training-boundary function, metric, preprocessing workflow, baseline, model, or tuning procedure;
- build or modify a model-ready dataset;
- mutate the cleaned Parquet or cleaning manifest;
- change the 16-day forecast contract or any valid historical lag/window feature;
- perform SCRUM-14 or SCRUM-15 work;
- modify notebooks, application code, tests, infrastructure, CI/CD, or deployment files;
- commit, push, merge, stage, or switch branches.

## 17. Validation performed

- Repository root and branch were verified before work.
- All eight required notebooks parsed successfully as nbformat 4.5; 142 code cells were inventoried and no saved error outputs were present.
- `cleaning_manifest.json` was parsed and reconciled with current Parquet footer dimensions and date statistics.
- Candidate counts used bounded, sequential row-group reads with seven projected columns; the full 125,497,040-row dataset was never loaded into memory.
- Assertions confirmed exactly eight origins, strict chronological order, exact 16-calendar-day durations, no overlap between validation windows, all 16 dates observed in every approved window, and no overlap with the final holdout.
- `git -c core.whitespace=cr-at-eol diff --check` passed after the approval update.
- The audit file exists at exactly `docs/audits/SCRUM_13_EXPANDING_WINDOW_FOLD_DESIGN_AUDIT.md`.

## 18. Changed-file statement

The only repository file created or modified by this task is:

- `docs/audits/SCRUM_13_EXPANDING_WINDOW_FOLD_DESIGN_AUDIT.md`

No other repository file was created, regenerated, or modified.
