# Favorita Real Model Inference Validation

## Scope and result

Validation passed for the actual selected Time-Aware LightGBM model through the
existing native bundle, `FavoritaBundlePredictor`, FastAPI forecast endpoint,
and Docker serving image. Direct, host FastAPI, and Docker predictions matched
within `rtol=1e-10` and `atol=1e-10`, and request row order was preserved.

This is serving-correctness validation. It does not rerun model-quality
evaluation, tune hyperparameters, invoke Optuna, or make a new model-selection
decision. The prior tiny synthetic API-test bundle remains useful for automated
contract tests; it is different from the real fitted model validated here.

## Model bundle

- Model version:
  `favorita_time_aware_origin_20170730_20260907T064049Z`
- Bundle path:
  `artifacts/models/favorita_time_aware_origin_20170730_20260907T064049Z`
- Bundle schema: `1`
- Model arm: `time_aware`
- Feature contract: `time-aware`
- Target: `unit_sales`
- Git commit: `da276f21a244cd9bb48a9549005075148ed52efc`
- Native trees / boost rounds: `150`
- `model.txt` SHA-256:
  `9851f8b01469de843b4c387a60d040f53f9922e71d9997ed781f905fe267b61e`

The bundle contains `model.txt` and `metadata.json`. Metadata records the exact
ordered fitted features, categorical columns and learned levels, all-null
excluded features, effective LightGBM parameters, runtime versions, source
identity and digest, code commit, model version, model checksum, and SCRUM-19
research provenance.

The selected parameters remained frozen:

```text
learning_rate = 0.02757359293934948
num_leaves = 123
min_data_in_leaf = 89
feature_fraction = 0.8394633936788146
num_boost_round = 150
```

## Training boundary and provenance

The final model reused the existing Time-Aware materializer and feature
contract. It trained on all approved observed target rows available through the
final forecast origin:

- Cleaned source:
  `data/processed/favorita_cleaned/favorita_cleaned.parquet`
- Cleaned source SHA-256:
  `845b435622fc4fb31c5336fb1f6eda22195f64edba61a0de813e94f831c626e4`
- Forecast origins: `2016-12-31` through `2017-07-29` (`211` daily origins)
- Training target dates: `2017-01-01` through `2017-07-30`
- Stores: all `54`; no item cap
- Training rows: `340,237,925`
- Training row-key/target SHA-256:
  `c2274be7678d0b0bfce80c16c0d66462dfe6527f300d00fe627262fcc525879a`
- Materialized training Parquet SHA-256:
  `20d69f5ad766c186cfd58a556a36aa539934719d0fbe767f948768c53a16b36f`

This boundary is appropriate for a deployable model at forecast origin
`2017-07-30`: every fitted label is dated on or before that origin, and every
feature row remains origin-bounded. The rematerialized training artifact
matched the existing SCRUM-19 Time-Aware training row count, boundaries,
cardinalities, horizons, duplicate count, and row-key/target digest.

The fit/export job did not use the SCRUM-19 holdout rows dated `2017-07-31`
through `2017-08-15` as training labels. Hashes of the protected SCRUM-19 JSON
and Markdown evidence were checked before and after export and were unchanged.

## Real inference sample

Three model-ready rows were selected without looking at target values: the
first sorted store/item row for horizons `[16, 1, 8]`, in that fixed order, from
a store `1` Time-Aware materialization at forecast origin `2017-07-30`.

| Row | Forecast date | Horizon | Store | Item | Actual `unit_sales` | Prediction |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 2017-08-15 | 16 | 1 | 103665 | 1.0 | 2.88205769546974 |
| 2 | 2017-07-31 | 1 | 1 | 96995 | 2.0 | 2.3457857954895713 |
| 3 | 2017-08-07 | 8 | 1 | 96995 | 2.0 | 2.3738855171835347 |

The ignored sample provenance and request evidence is under
`artifacts/validation/favorita_time_aware_origin_20170730_20260907T064049Z`.
The source materialization SHA-256 is
`3a2dabdaf39ea30f97ada28c1aa3288991c8df755fbe1441ca666ff54332d06f`;
the three-row sample Parquet SHA-256 is
`fdfd4166f14f6a7031236e70d8bc22b707f0f8ceabfe6f70ead262e0f861f4cf`.

## Serving consistency

| Path | Health | Ready | Forecast | Predictions in request order |
| --- | ---: | ---: | ---: | --- |
| Direct load-only predictor | N/A | N/A | N/A | `[2.88205769546974, 2.3457857954895713, 2.3738855171835347]` |
| Host FastAPI | 200 | 200 | 200 | `[2.88205769546974, 2.3457857954895713, 2.3738855171835347]` |
| Docker FastAPI | 200 | 200 | 200 | `[2.88205769546974, 2.3457857954895713, 2.3738855171835347]` |

`FavoritaBundlePredictor.load()` verified the model checksum and native feature
order before prediction. The direct inference process confirmed that training,
feature-materialization, evaluation, and Optuna modules were not imported.
Repeated and reversed-order API requests also matched direct prediction, proving
stable output and row-order preservation. Docker used image
`sha256:bb9e5ddfa82b2ef05e1a77b86cde2f3066352e37d73d39a0200fb6a72581fe50`
and mounted the same bundle at `/models/favorita` read-only.

## Resource observations and limitations

Training-data materialization took approximately `2,870` seconds and model
fitting approximately `2,209` seconds (`5,080` seconds total, about 84.7
minutes). Peak process resident memory was approximately `37.9 GiB`.

The heavy bundle, training materialization, real sample, request, and runtime
