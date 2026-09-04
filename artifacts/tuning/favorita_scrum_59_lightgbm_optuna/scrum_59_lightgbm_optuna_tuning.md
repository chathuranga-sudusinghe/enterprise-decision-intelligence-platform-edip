# SCRUM-59 Shared LightGBM Optuna Tuning

## Experiment Contract

- Trials: 6 paired trials
- Target: `unit_sales`
- Validation: four canonical expanding-window folds, horizons 1 through 16
- Objective: mean of Contextual overall MAE and Time-Aware overall MAE

## Compute Mode

- Frozen mode: `cpu`
- GPU smoke check: GPU unavailable; CPU frozen: LightGBMError: No OpenCL device found

## Search Space

```json
{
  "feature_fraction": {
    "high": 1.0,
    "kind": "float",
    "low": 0.6
  },
  "learning_rate": {
    "high": 0.15,
    "kind": "float",
    "log": true,
    "low": 0.01
  },
  "min_data_in_leaf": {
    "high": 200,
    "kind": "int",
    "log": true,
    "low": 10
  },
  "num_boost_round": {
    "high": 500,
    "kind": "int",
    "low": 100,
    "step": 50
  },
  "num_leaves": {
    "high": 128,
    "kind": "int",
    "low": 16
  }
}
```

## Trial Results

Optuna ranks trials only by shared MAE. All six overall metrics remain required evidence.

| Trial | Arm | MAE | RMSE | WAPE | Bias | RMSLE | NWRMSLE | Shared MAE |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | Contextual | 4.97351358926 | 20.2739136 | 0.606321333808 | -0.00850541580785 | 0.697817571735 | 0.696504859736 | 4.572059145 |
| 0 | Time-Aware | 4.17060470074 | 19.7988179777 | 0.508427434054 | -0.275112890066 | 0.592643016211 | 0.591069709812 | 4.572059145 |
| 1 | Contextual | 5.25439165545 | 20.6283404641 | 0.640568268571 | -0.0351068998157 | 0.726661903354 | 0.725578107617 | 4.73380873956 |
| 1 | Time-Aware | 4.21322582367 | 19.8266342405 | 0.513624490543 | -0.367114342739 | 0.598071847251 | 0.596550104501 | 4.73380873956 |
| 2 | Contextual | 5.51100678388 | 20.9699505125 | 0.671857024982 | -0.0305853115749 | 0.774505381857 | 0.772646641595 | 5.0197118536 |
| 2 | Time-Aware | 4.52841692333 | 20.0657068921 | 0.552054314851 | -0.285286417079 | 0.660131660936 | 0.657665718943 | 5.0197118536 |
| 3 | Contextual | 5.31630084032 | 20.5843945199 | 0.648117435093 | -0.0329729500997 | 0.74174564772 | 0.740413149507 | 4.78389154076 |
| 3 | Time-Aware | 4.2514822412 | 19.8380217822 | 0.518288459679 | -0.360646241044 | 0.609141167643 | 0.607335396247 | 4.78389154076 |
| 4 | Contextual | 4.98528027034 | 20.3923486648 | 0.607554189359 | 0.110887017296 | 0.693950143095 | 0.69281980754 | 4.60900850854 |
| 4 | Time-Aware | 4.23273674674 | 19.9315589702 | 0.515967022051 | -0.00874665824189 | 0.599987980953 | 0.598497248499 | 4.60900850854 |
| 5 | Contextual | 5.02256035403 | 20.3328424571 | 0.612276013969 | 0.0361783641456 | 0.696967944625 | 0.696028599599 | 4.62561215232 |
| 5 | Time-Aware | 4.22866395062 | 19.9608924713 | 0.51548371834 | -0.127051987977 | 0.598464889602 | 0.597007832318 | 4.62561215232 |

## Best Optuna Trial by Shared MAE

- Trial: 0
- Shared MAE: 4.572059145
- Primary-objective parameter configuration: `{"feature_fraction": 0.8394633936788146, "learning_rate": 0.02757359293934948, "min_data_in_leaf": 89, "num_boost_round": 150, "num_leaves": 123}`
- This is the Optuna shared-MAE winner, not a final complete-profile model selection.

## Contextual Metric Profile

| Metric | Value |
|---|---:|
| mae | 4.97351358926 |
| rmse | 20.2739136 |
| wape | 0.606321333808 |
| bias | -0.00850541580785 |
| rmsle | 0.697817571735 |
| nwrmsle | 0.696504859736 |

## Time-Aware Metric Profile

| Metric | Value |
|---|---:|
| mae | 4.17060470074 |
| rmse | 19.7988179777 |
| wape | 0.508427434054 |
| bias | -0.275112890066 |
| rmsle | 0.592643016211 |
| nwrmsle | 0.591069709812 |

## Bias Evidence

Bias is retained as signed mean prediction minus actual; closer to zero is better.

## Research Interpretation

Optuna identifies the primary-objective winner by shared MAE. MAE, RMSE, WAPE, RMSLE, NWRMSLE, and signed Bias must all be reviewed before final model-selection or research conclusions. SCRUM-19 performs the final research interpretation.

## Protected Holdout

The protected holdout was not loaded, scored, or selected against.

## Limitations

Only six paired trials and the five approved dimensions were evaluated. Results remain conditional on the canonical folds and frozen compute mode.
