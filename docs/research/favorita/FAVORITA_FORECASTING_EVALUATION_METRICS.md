# Favorita Forecasting Evaluation Metric Contract

| Field | Value |
|---|---|
| Status | Active SCRUM-17 metric contract |
| Target | `unit_sales` |
| Primary selection metric | MAE (Mean Absolute Error) |
| Forecast horizons | Exact integers 1 through 16 |

## 1. Evaluation views

The source dataset and cleaned Parquet remain unchanged. No evaluation row is silently dropped.

**Raw-target evaluation** uses the original actual and prediction values for MAE, RMSE, and Bias.

**Demand-oriented non-negative evaluation** uses WAPE, RMSLE, and NWRMSLE with:

```text
evaluation_target = max(actual_unit_sales, 0)
evaluation_prediction = max(predicted_unit_sales, 0)
```

This transformation is evaluation-only.

## 2. Metric definitions

For `n` evaluated rows, let `y_i` be actual `unit_sales`, `p_i` be the prediction, `y_i+ = max(y_i, 0)`, and `p_i+ = max(p_i, 0)`.

```text
MAE = (1 / n) * sum(|p_i - y_i|)
RMSE = sqrt((1 / n) * sum((p_i - y_i)^2))
Bias = (1 / n) * sum(p_i - y_i)
WAPE = sum(|p_i+ - y_i+|) / sum(y_i+)
RMSLE = sqrt((1 / n) * sum((log(1 + p_i+) - log(1 + y_i+))^2))
NWRMSLE = sqrt(sum(w_i * (log(1 + p_i+) - log(1 + y_i+))^2) / sum(w_i))
```

NWRMSLE uses the Favorita perishability convention: `w_i = 1.25` when `perishable = 1`, otherwise `w_i = 1.0`. Normalization is by the sum of row weights. This document uses **NWRMSLE** for that exact normalized weighted RMSLE definition.

WAPE is returned as a ratio and multiplied by 100 only for percentage display. If `sum(y_i+) = 0`, WAPE is undefined and evaluation raises an explicit error; no epsilon, fallback score, or row removal is used.

## 3. Selection and interpretation

SCRUM-18 compares Contextual LightGBM and Proposed Time-Aware LightGBM under this identical metric contract. MAE remains the primary selection metric; RMSE, WAPE, RMSLE, and NWRMSLE remain supporting evidence, and Bias remains diagnostic.

| Metric | Role | Best direction | Perfect value |
|---|---|---|---|
| MAE (Mean Absolute Error) | Primary model selection | decrease | 0 |
| RMSE (Root Mean Squared Error) | Supporting | decrease | 0 |
| WAPE (Weighted Absolute Percentage Error) | Business-oriented supporting | decrease | 0% |
| RMSLE (Root Mean Squared Logarithmic Error) | Supporting log-scale | decrease | 0 |
| NWRMSLE (Normalized Weighted Root Mean Squared Logarithmic Error) | Additional weighted evidence | decrease | 0 |
| Bias (Mean Forecast Error) | Diagnostic | closer to zero | 0 |

Bias equal to zero indicates no systematic directional error. Positive Bias indicates over-forecasting; negative Bias indicates under-forecasting.

## 4. Required reporting grain

Every evaluated model must report the complete metric set:

- overall across all included validation rows;
- separately for each validation fold; and
- separately for each `forecast_horizon` from 1 through 16.

Contextual LightGBM and Proposed Time-Aware LightGBM must receive equivalent overall, per-fold, and per-horizon reporting. Overall MAE recomputed from pooled row-level errors is the primary accuracy evidence. Fold-level results provide consistency evidence by showing whether the direction and magnitude of performance differences are stable across the four canonical windows. No conclusion may cherry-pick a favorable fold, horizon, or supporting metric; all predeclared views and metrics must be disclosed and interpreted together.

Overall metrics are recomputed from pooled row-level errors; they are not unweighted averages of fold or horizon metrics. Fold and horizon grouping belongs to the separately approved backtesting implementation. This contract does not implement folds, train a model, score the final holdout, or change source data.

## 5. Executable contract

Reusable deterministic functions are defined in `pipelines/evaluation/favorita_metrics.py`. They require non-empty, equal-length, finite inputs, reject invalid perishability indicators, do not mutate inputs, and do not silently remove rows.
