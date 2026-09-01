# Favorita Research Hypothesis and Experiment Design

## 1. Purpose

This document defines the hypothesis-driven Favorita forecasting experiment for SCRUM-18. It governs the research question, comparison, controlled variables, interpretation, holdout protection, and acceptance evidence without changing source data, temporal boundaries, feature implementations, model parameters, or the evaluation metric contract.

## 2. MSc Research Positioning

The primary MSc research contribution is the Favorita grocery-sales forecasting experiment. It tests whether adding leakage-safe historical time-series information to a controlled global LightGBM approach improves forecast accuracy and consistency.

## 3. Relationship to EDIP

EDIP applies the forecasting result inside a broader production-oriented decision-support architecture. RAG, LangGraph orchestration, Human-in-the-Loop approval, deterministic controls, approved external evidence, MCP integration, and enterprise workflow integration are applied system contributions. They are not a second independent MSc hypothesis unless a separately approved research protocol introduces another research question.

## 4. Research Question

Does adding leakage-safe temporal and time-series features to a Contextual LightGBM model improve grocery-sales forecast accuracy and consistency over the same model without those features?

## 5. Hypotheses

### H1 (Alternative)

Adding leakage-safe temporal and time-series features to a contextual LightGBM model improves forecast accuracy and consistency over the same model without those features.

### H0 (Null)

Adding leakage-safe temporal and time-series features to a contextual LightGBM model does not improve forecast accuracy or consistency over the same model without those features.

## 6. Experimental Comparison

### Contextual LightGBM

The Contextual LightGBM comparator uses the approved contextual feature groups without the leakage-safe temporal and time-series feature group being tested. It must not be intentionally weakened through removal of useful contextual information, inferior preprocessing, reduced training scope, or less favorable model configuration. Its exact feature-column list is not frozen by this document and remains the next SCRUM-18 design step.

### Proposed Time-Aware LightGBM

The Proposed Time-Aware LightGBM uses the same Contextual LightGBM features plus leakage-safe temporal and time-series features available at each forecast origin. Its current canonical execution is complete for all four folds: `completed_folds = [1, 2, 3, 4]`.

Naive or statistical baselines may be reported as secondary reference evidence. They do not replace the Contextual-versus-Proposed Time-Aware LightGBM hypothesis comparison.

## 7. Feature Groups

The intended relationship is:

```text
Proposed Time-Aware LightGBM features
= Contextual LightGBM features
+ leakage-safe temporal and time-series features
```

The feature-group boundary is frozen, but the exact feature-column lists are not. The next SCRUM-18 design step must record and approve the precise contextual columns and added temporal/time-series columns without redefining feature calculations in this document.

## 8. Controlled Variables

The comparison controls:

- target: `unit_sales`;
- the same canonical four expanding-window folds;
- exact forecast horizons 1 through 16;
- the same training scope and eligibility rule per fold;
- the same global LightGBM model family;
- the same evaluation metric contract and reporting grains;
- the same sparse observed-row semantics and entity population;
- equivalent preprocessing and execution conditions except where the feature difference necessarily requires otherwise; and
- core model configuration and tuning effort wherever required for a fair feature-information comparison.

One approach must not receive more aggressive tuning than the other for this hypothesis test. Any unavoidable difference must be documented and treated as a threat to validity.

## 9. Independent Variable

The independent variable is the addition of the approved leakage-safe temporal and time-series feature group to the same Contextual LightGBM baseline. All other material experimental conditions are held equivalent as far as practicable.

## 10. Dependent Variables and Metrics

Forecast accuracy and consistency are evaluated under [Favorita Forecasting Evaluation Metric Contract](FAVORITA_FORECASTING_EVALUATION_METRICS.md). Pooled overall MAE is the primary accuracy evidence. RMSE, WAPE, RMSLE, and NWRMSLE are supporting evidence, while Bias is diagnostic. Fold-level MAE and the complete fold-level metric set provide consistency evidence; per-horizon results expose horizon-dependent behavior.

## 11. Canonical Temporal Validation

Both approaches use the exact four expanding-window folds in the [Favorita Temporal Validation Design](FAVORITA_TEMPORAL_VALIDATION_DESIGN.md) and [Favorita Temporal Validation Contract](FAVORITA_TEMPORAL_VALIDATION_CONTRACT.md). They share the same `2017-01-01` modeling-target start, fold-specific training cutoff, 16-day validation windows, direct horizon-aware strategy, and leakage controls. Random splitting, changed fold boundaries, or comparator-specific training windows are prohibited.

## 12. Accuracy and Consistency Interpretation

H1 receives support only when the complete predeclared evidence shows a lower pooled overall MAE for the Proposed model and fold-level results provide credible consistency evidence rather than dependence on a cherry-picked window. Supporting metrics, Bias, and all horizon views must be disclosed even when they conflict with MAE.

SCRUM-18 must define before comparison review how many folds, direction-of-effect patterns, or material contradictions constitute sufficient consistency. The experiment may report practical differences and descriptive stability, but it must not claim statistical significance unless a separately approved statistical procedure is implemented.

## 13. Final Holdout Protection

The final holdout has origin `2017-07-30` and target dates `2017-07-31` through `2017-08-15`. It remains unscored during SCRUM-18 and must not inform feature decisions, tuning, model selection, hypothesis evaluation, thresholds, sensitivity-design selection, or promotion criteria. A later approved work item may score it only after the candidate and promotion rules are frozen.

## 14. Reproducibility and Artifact Evidence

Each approach must preserve its code revision, environment, exact feature schema, model configuration, fold identifiers, training scope, row counts, seeds where meaningful, runtime evidence, predictions, complete metrics, and immutable artifact identifiers or checksums. Artifact namespaces must distinguish Contextual and Proposed Time-Aware results and must not overwrite historical or protected evidence.

## 15. Threats to Validity

Threats include imperfect isolation of the feature-group difference, unequal tuning or preprocessing, changing store/item populations, sparse observed-row coverage, repeated representation of realized targets across origins, limited seasonal and business-regime coverage, and only four validation windows. Results are bounded to this dataset, target, period, feature contracts, model family, and experimental design. The experiment does not prove that temporal features are universally superior.

## 16. SCRUM-18 Acceptance Criteria

SCRUM-18 is acceptable when:

- the Contextual LightGBM feature boundary is explicit, reviewed, and does not intentionally weaken the comparator;
- the shared contextual features and added leakage-safe temporal/time-series features are recorded precisely;
- both approaches use the same target, four folds, horizons, fold training scopes, metric contract, LightGBM family, and controlled model configuration;
- tuning effort is equivalent and holdout outcomes remain unavailable;
- both approaches report complete pooled-overall, per-fold, and per-horizon evidence;
- pooled overall MAE is used as primary accuracy evidence and fold-level results as consistency evidence;
- favorable folds, horizons, or supporting metrics are not cherry-picked;
- candidate-selection and later holdout-promotion criteria are documented before holdout scoring;
- reproducibility and artifact lineage evidence is preserved;
- limitations, contradictions, and negative results are reported; and
- no statistical-significance or universal-superiority claim exceeds the implemented evidence.
