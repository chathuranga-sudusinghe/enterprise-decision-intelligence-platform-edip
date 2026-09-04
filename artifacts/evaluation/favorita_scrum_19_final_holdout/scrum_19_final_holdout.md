# SCRUM-19 Final Forecasting Research Evidence

## Final Holdout Contract

- Forecast origin: `2017-07-30`
- Holdout dates: `2017-07-31` through `2017-08-15`
- Horizons: 1 through 16
- This is the final protected-holdout evaluation.

## Frozen Model Configuration

- Source: SCRUM-59 Trial 0 frozen configuration
- Parameters: `{"feature_fraction": 0.8394633936788146, "learning_rate": 0.02757359293934948, "min_data_in_leaf": 89, "num_leaves": 123}`
- Boost rounds: 150
- Tuning performed: No
- Optuna invoked: No

## Overall Metrics

| Arm | Rows | MAE | RMSE | WAPE | Bias | RMSLE | NWRMSLE |
|---|---:|---:|---:|---:|---:|---:|---:|
| Contextual | 1668475 | 4.96142957761 | 18.3394998311 | 0.623608396204 | 0.369157616204 | 0.709811564028 | 0.708664440979 |
| Time-Aware | 1668475 | 4.24906700629 | 17.155536482 | 0.534065606887 | 0.814313855621 | 0.617361350514 | 0.615370109499 |

## Metric-by-Metric Comparison

| Metric | Contextual | Time-Aware | Better arm | Basis |
|---|---:|---:|---|---|
| MAE | 4.96142957761 | 4.24906700629 | time-aware | lower is better |
| RMSE | 18.3394998311 | 17.155536482 | time-aware | lower is better |
| WAPE | 0.623608396204 | 0.534065606887 | time-aware | lower is better |
| BIAS | 0.369157616204 | 0.814313855621 | contextual | closer to zero |
| RMSLE | 0.709811564028 | 0.617361350514 | time-aware | lower is better |
| NWRMSLE | 0.708664440979 | 0.615370109499 | time-aware | lower is better |

## Research Interpretation

This report summarizes final holdout evidence but does not automatically conclude H0 or H1. Final interpretation belongs to the SCRUM-19 research review.
