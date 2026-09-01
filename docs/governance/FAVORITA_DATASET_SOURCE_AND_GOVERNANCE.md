# Corporacion Favorita Dataset Source and Governance

| Field | Value |
|---|---|
| Dataset | Corporacion Favorita Grocery Sales Forecasting |
| Provider | Corporacion Favorita C.A. |
| Platform | Kaggle |
| Classification | `real_public_restricted_access` |
| Verified local raw path | `data/raw/favorita-grocery-sales-forecasting/` |
| Local verification date | 2026-08-02 |
| Raw data tracked in Git | No |
| Research status | Governed source foundation; downstream claims remain evidence-gated |

## 1. Purpose and evidence boundary

This record is the authority for Favorita source identity, access classification, local raw-file evidence, preservation, redistribution, provenance, and research-use boundaries in EDIP.

It consolidates the original source/governance record and post-download verification. It proves the directly inspected extracted file set and recorded checksums. It does not prove the exact Kaggle access timestamp, archive identity, dataset revision, competition-rules snapshot, institutional approval, research readiness, or production readiness.

Related current records:

- [EDIP Architecture Plan](../architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md);
- [Favorita Research Hypothesis and Experiment Design](../research/favorita/FAVORITA_RESEARCH_HYPOTHESIS_AND_EXPERIMENT_DESIGN.md);
- [Favorita Temporal Validation Design](../research/favorita/FAVORITA_TEMPORAL_VALIDATION_DESIGN.md); and
- [Favorita Temporal Validation Contract](../research/favorita/FAVORITA_TEMPORAL_VALIDATION_CONTRACT.md).

## 2. Official source and access classification

Official source: [Corporacion Favorita Grocery Sales Forecasting](https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting).

The source is classified as `real_public_restricted_access`:

- **real:** it contains observed grocery-sales records rather than EDIP-generated synthetic observations;
- **public:** the competition page is publicly discoverable; and
- **restricted access:** access and use remain governed by Kaggle competition access and applicable rules.

Public discoverability does not establish an open-data licence or redistribution permission. Neither Kaggle nor Corporacion Favorita is claimed to have reviewed, approved, sponsored, or endorsed EDIP.

## 3. Permitted EDIP use

Subject to verified competition rules and research governance, the dataset is intended for:

- MSc research on demand forecasting and trustworthy decision intelligence;
- reproducible training, validation, and testing;
- EDIP engineering and governance evidence; and
- preparation for future research into forecasting, uncertainty, evidence sufficiency, and Human-in-the-Loop decision support.

This record grants no new usage right. Institutional, supervisor, ethics, privacy, retention, or data-owner approvals must be obtained where required.

## 4. Raw-data preservation and redistribution

The raw boundary is `data/raw/favorita-grocery-sales-forecasting/`.

Raw files must remain:

- byte-preserved and outside Git;
- access-controlled;
- separate from interim, processed, feature, split, model, forecast, and evaluation outputs; and
- protected from cleaning, transformation, sampling, renaming, or write access during verification.

Raw or extracted competition data must not be redistributed through Git, releases, pull requests, issues, documentation, model packages, public demonstrations, mirrors, or example fixtures. Reviewed aggregate findings, schemas, checksums, lineage, and non-sensitive metadata may be published only when compatible with verified rules and governance.

The repository ignore rule `data/raw/*` protected the inspected path. At verification, no raw file was tracked, staged, or present in the Git change set. Packaging, Docker contexts, reports, releases, and staging must be checked again before publication.

## 5. Inspection method

The eight expected CSV files were inspected read-only. A streaming scanner:

- read each file sequentially without loading `train.csv` fully into memory;
- calculated SHA-256 from unchanged bytes;
- counted rows and malformed widths;
- collected headers, null counts, date/numeric ranges, and bounded identifier sets;
- checked strictly increasing IDs for the three large ID-bearing files; and
- performed exact row-set duplicate checks for the smaller files.

Only bounded sets and scalar aggregates were retained. No raw file was opened for writing, renamed, moved, transformed, sampled, or deleted.

The original archive was not present, so archive identity, checksum, acquisition evidence, and extraction reproducibility were not verified.

## 6. Verified raw inventory

Counts exclude headers.

| Filename | Bytes | Rows | Columns/date range | SHA-256 |
|---|---:|---:|---|---|
| `holidays_events.csv` | 22,309 | 350 | 6; `2012-03-02` to `2017-12-26` | `81a183d6c4d691b57f84a0fde6bbf734a5b3c36a74b97378bf33a592648e2999` |
| `items.csv` | 101,841 | 4,100 | 4 | `1efd8295f52c8531ec5bf6c3de37228a56bad2f2c653e79c4869baaf637edcc6` |
| `oil.csv` | 20,580 | 1,218 | 2; `2013-01-01` to `2017-08-31` | `944b23b857580f9d804399346fd3ed69bffcb7facfd98c55fdb408b8d057cca7` |
| `sample_submission.csv` | 40,445,582 | 3,370,464 | 2 | `50b93078008e68bdd0818b18ca2493c23e7ad7e2c506b2b263c3347dad1d77db` |
| `stores.csv` | 1,387 | 54 | 5 | `af503b2bce11d7906d249f81cc0598f10e2addcc9f6c59aa2d95c9f2652c296b` |
| `test.csv` | 126,163,026 | 3,370,464 | 5; `2017-08-16` to `2017-08-31` | `b9d3bef11ca9b058bdd4c1fa3a69b8a595f4ef39983051eb5ab416e255f13ae6` |
| `train.csv` | 4,997,452,288 | 125,497,040 | 6; `2013-01-01` to `2017-08-15` | `ccf4236a6b58b0db937b8c5006a0ad8fffef6acd06bed1c10cd5cd4d68d93248` |
| `transactions.csv` | 1,552,637 | 83,488 | 3; `2013-01-01` to `2017-08-15` | `e116384a6981af74932832436aa2f6a43121f77ca81accc44e3a5160158ca03c` |

Local modification timestamps spanned `2017-10-19T15:30:05Z` to `2017-10-19T15:30:31Z`. They are filesystem metadata, not verified access dates or dataset-version evidence.

## 7. Verified schemas and quality facts

| File | Header |
|---|---|
| `holidays_events.csv` | `date`, `type`, `locale`, `locale_name`, `description`, `transferred` |
| `items.csv` | `item_nbr`, `family`, `class`, `perishable` |
| `oil.csv` | `date`, `dcoilwtico` |
| `sample_submission.csv` | `id`, `unit_sales` |
| `stores.csv` | `store_nbr`, `city`, `state`, `type`, `cluster` |
| `test.csv` | `id`, `date`, `store_nbr`, `item_nbr`, `onpromotion` |
| `train.csv` | `id`, `date`, `store_nbr`, `item_nbr`, `unit_sales`, `onpromotion` |
| `transactions.csv` | `date`, `store_nbr`, `transactions` |

Verified observations:

- zero malformed-width rows across all eight files;
- `train.csv` contains 21,657,651 null `onpromotion` values (17.257499%);
- the promotion profile is 21,657,651 null, 96,028,767 false, and 7,810,622 true;
- `oil.csv` contains 43 null `dcoilwtico` values (3.530378%);
- training `unit_sales` ranges from -15,372 to 89,440, with mean 8.554865;
- training contains 7,795 negative, zero zero-valued, and 125,489,245 positive target rows;
- training IDs are strictly increasing from 0 to 125,497,039;
- test and sample-submission IDs are strictly increasing from 125,497,040 to 128,867,503;
- no exact duplicate rows were found under the recorded inspection method.

Nulls and negative sales are observations, not automatic defects. Their treatment belongs to explicit downstream cleaning, modeling, and evaluation contracts.

## 8. Identifier and grain evidence

- `stores.csv` contains 54 unique stores, numbered 1 through 54.
- `items.csv` contains 4,100 unique items.
- Training references 54 stores and 4,036 items, all covered by the master files.
- Test references 54 stores and 3,901 items, all covered by the master files.
- Transactions reference 54 stores, all covered by `stores.csv`.
- The observed sales grain is `(date, store_nbr, item_nbr)`.

The source is sparse. An absent store-item-date row is not evidence of zero demand. EDIP must not densify absent rows, manufacture labels, or mix synthetic relationships into real ground truth without a separately approved research design and explicit provenance.

## 9. Current forecasting linkage

The current forecast target is `unit_sales`. Labelled history ends on `2017-08-15`; the official unlabelled competition test period covers `2017-08-16` through `2017-08-31`, an inclusive 16-day inference window.

EDIP therefore uses an approved maximum direct forecast horizon of 16 days. The redesigned temporal methodology uses four expanding-window validation folds across modeling and evaluation targets from `2017-01-01` through `2017-07-30`. It protects the final labelled holdout with origin `2017-07-30` and dates `2017-07-31` through `2017-08-15`. Earlier eight-fold and superseded four-fold schedules are historical context only.

The model-comparison and hypothesis logic are governed by the linked research hypothesis and experiment design; model-feature definitions are maintained in their dedicated feature and experiment authorities rather than duplicated here. The exact leakage, fold, horizon, and holdout rules are defined in the linked temporal design and contract. Kaggle `test.csv` has no `unit_sales` and is not local metric evidence.

## 10. Provenance and governance gaps

The inspected files do not directly prove:

- exact authenticated Kaggle access date/time;
- accepted competition-rules version or preserved snapshot;
- dataset revision;
- original archive filename, size, checksum, or extraction method;
- custody before local extraction;
- final privacy and sensitive-field assessment;
- retention, backup, deletion, access-control, and incident decisions;
- institutional, supervisor, ethics, or data-owner approval;
- final model, metric, publication, or deployment approval.

A future machine-readable manifest should bind the exact extracted paths and checksums to a stable dataset ID, source/rules evidence, acquisition details, code revision, inspection environment, quality results, and every downstream dataset, feature, model, forecast, and evaluation artifact. Checksum mismatch must fail closed and trigger provenance review.

## 11. Acceptance and prohibited claims

**Acceptance:** the expected extracted local raw file set is verified as an immutable governed input for controlled downstream work.

This does not establish an open licence, redistribution permission, research readiness, publication approval, production readiness, institutional approval, model quality, real-world decision value, Corporacion Favorita endorsement, or a professional/academic award.

Every downstream claim must remain bounded by the evidence actually executed and approved.
