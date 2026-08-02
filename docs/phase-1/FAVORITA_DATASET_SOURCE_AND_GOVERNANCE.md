# Corporación Favorita Dataset Source and Governance Record

- Record status: post-download local file-set verification completed
- Verification date: 2026-08-02
- Verification boundary: eight expected extracted CSVs; no original archive observed
- Classification: `real_public_restricted_access`
- Verified local raw-data path: `data/raw/favorita-grocery-sales-forecasting/`

EDIP is an enterprise-grade research and engineering project developed for MSc Individual Project evaluation, future CITP professional evidence, and progression toward PhD research in trustworthy Human-in-the-Loop and agentic decision systems.

## 1. Dataset identity

| Field | Recorded value |
|---|---|
| Dataset | Corporación Favorita Grocery Sales Forecasting |
| Provider | Corporación Favorita C.A. |
| Platform | Kaggle |
| Access type | Kaggle competition dataset |
| Classification | `real_public_restricted_access` |
| Local acquisition state | Expected eight-file extracted CSV set locally present and verified |
| Verified local path | `data/raw/favorita-grocery-sales-forecasting/` |

This record proves the directly inspected local file set only. Exact Kaggle access time, dataset revision, accepted competition-rules snapshot, original archive identity/checksum, institutional approvals, retention decision, and final research split remain pending.

## 2. Official source

Official source: [Corporación Favorita Grocery Sales Forecasting](https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting)

`https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting`

The source URL identifies the competition entry point. It does not by itself establish an open licence, redistribution permission, a dataset revision, or approval of EDIP.

## 3. Provider and platform

- Provider: Corporación Favorita C.A.
- Distribution platform: Kaggle
- Access mechanism: Kaggle competition dataset access

Kaggle provides the access platform. Neither Kaggle nor Corporación Favorita is claimed to have reviewed, approved, sponsored, endorsed, or participated in EDIP. EDIP is not Corporación Favorita's operational platform.

## 4. Access and usage classification

Classification: `real_public_restricted_access`.

- `real`: the source provides real grocery-sales observations rather than EDIP-generated synthetic observations.
- `public`: the competition page is publicly discoverable.
- `restricted_access`: access and use remain governed by Kaggle competition access and applicable rules, not an assumed open-data licence.

The classification must not be shortened to `open_data`. This record does not grant usage rights.

## 5. Intended EDIP use

Permitted EDIP purposes, subject to verified competition rules and research governance, are:

- MSc Individual Project research;
- real-data demand-forecasting training, validation, and testing;
- EDIP decision-intelligence research;
- future CITP evidence of professional engineering practice; and
- preparation for a future PhD research pathway.

The three strategic EDIP targets are MSc Individual Project, future CITP professional evidence, and future PhD research pathway.

## 6. Raw-data storage policy

The verified raw boundary is `data/raw/favorita-grocery-sales-forecasting/`.

Raw competition data must remain byte-preserved, outside Git, access-controlled, and separate from interim, processed, feature, split, model, forecast, and evaluation outputs. No raw CSV was renamed, moved, cleaned, transformed, sampled, deleted, or opened for writing during verification.

All eight expected names are regular files directly under the raw directory. No nested directory, including a directory with a `.csv` suffix, was observed.

## 7. Redistribution restrictions

Raw or extracted competition data must not be redistributed through Git, releases, issues, pull requests, documentation, model packages, public demonstrations, mirrors, or example fixtures. Public discoverability does not establish redistribution permission.

Only reviewed aggregate findings, schemas, validation summaries, lineage records, and non-sensitive metadata may be published when compatible with the verified competition rules and research governance.

## 8. Git tracking policy

`raw_data_tracked_in_git` is `false`.

The current `.gitignore` rule `data/raw/*` ignores the verified raw path. `git ls-files`, staged-diff inspection, and raw-path status inspection returned no raw file. Git may track governance records, manifest/schema definitions, code, source/rules references, checksums, bounded inventories, and reviewed non-redistributive quality summaries only.

Future Docker contexts, release packages, reports, and staging operations must be checked again before use.

## 9. Verified file inventory

Counts exclude headers. Checksums were calculated from unchanged bytes during streaming inspection.

| Filename | Relative path | Bytes | Rows | Columns | Date range | SHA-256 |
|---|---|---:|---:|---|---|---|
| `holidays_events.csv` | `data/raw/favorita-grocery-sales-forecasting/holidays_events.csv` | 22,309 | 350 | `date`, `type`, `locale`, `locale_name`, `description`, `transferred` | 2012-03-02 to 2017-12-26 | `81a183d6c4d691b57f84a0fde6bbf734a5b3c36a74b97378bf33a592648e2999` |
| `items.csv` | `data/raw/favorita-grocery-sales-forecasting/items.csv` | 101,841 | 4,100 | `item_nbr`, `family`, `class`, `perishable` | not applicable | `1efd8295f52c8531ec5bf6c3de37228a56bad2f2c653e79c4869baaf637edcc6` |
| `oil.csv` | `data/raw/favorita-grocery-sales-forecasting/oil.csv` | 20,580 | 1,218 | `date`, `dcoilwtico` | 2013-01-01 to 2017-08-31 | `944b23b857580f9d804399346fd3ed69bffcb7facfd98c55fdb408b8d057cca7` |
| `sample_submission.csv` | `data/raw/favorita-grocery-sales-forecasting/sample_submission.csv` | 40,445,582 | 3,370,464 | `id`, `unit_sales` | not applicable | `50b93078008e68bdd0818b18ca2493c23e7ad7e2c506b2b263c3347dad1d77db` |
| `stores.csv` | `data/raw/favorita-grocery-sales-forecasting/stores.csv` | 1,387 | 54 | `store_nbr`, `city`, `state`, `type`, `cluster` | not applicable | `af503b2bce11d7906d249f81cc0598f10e2addcc9f6c59aa2d95c9f2652c296b` |
| `test.csv` | `data/raw/favorita-grocery-sales-forecasting/test.csv` | 126,163,026 | 3,370,464 | `id`, `date`, `store_nbr`, `item_nbr`, `onpromotion` | 2017-08-16 to 2017-08-31 | `b9d3bef11ca9b058bdd4c1fa3a69b8a595f4ef39983051eb5ab416e255f13ae6` |
| `train.csv` | `data/raw/favorita-grocery-sales-forecasting/train.csv` | 4,997,452,288 | 125,497,040 | `id`, `date`, `store_nbr`, `item_nbr`, `unit_sales`, `onpromotion` | 2013-01-01 to 2017-08-15 | `ccf4236a6b58b0db937b8c5006a0ad8fffef6acd06bed1c10cd5cd4d68d93248` |
| `transactions.csv` | `data/raw/favorita-grocery-sales-forecasting/transactions.csv` | 1,552,637 | 83,488 | `date`, `store_nbr`, `transactions` | 2013-01-01 to 2017-08-15 | `e116384a6981af74932832436aa2f6a43121f77ca81accc44e3a5160158ca03c` |

Local modification times range from 2017-10-19T15:30:05Z to 2017-10-19T15:30:31Z. They do not prove Kaggle access time or dataset revision.

Verified quality evidence:

- zero malformed rows across all eight files;
- `train.csv`: 21,657,651 null `onpromotion` values (17.257499%); other columns non-null;
- `oil.csv`: 43 null `dcoilwtico` values (3.530378%); other columns non-null;
- all test and other inspected small-file fields are non-null;
- training promotion profile: 21,657,651 null, 96,028,767 false, 7,810,622 true;
- training target: minimum -15,372, maximum 89,440, mean 8.554865, 7,795 negative, zero zero-valued, and 125,489,245 positive rows;
- training IDs are strictly increasing from 0 to 125,497,039; test and sample IDs are strictly increasing from 125,497,040 to 128,867,503;
- strict ID ordering establishes no exact duplicate rows in those large ID-bearing files; exact row-set checks found no duplicates in the other files.

## 10. Provenance fields pending verification

The extracted files directly prove local presence, paths, bytes, headers, row counts, observed ranges, null/duplicate summaries, identifiers, relationships, and per-file checksums. They do not directly prove:

- exact Kaggle access date/time or authenticated acquisition evidence;
- accepted competition-rules version/snapshot;
- dataset version or competition data revision;
- download command, archive filename/size/checksum, or extraction tool/version;
- final privacy/sensitive-field assessment;
- retention, backup, deletion, and incident decisions;
- institutional ethics approval, academic supervisor approval, or data-owner review; or
- final MSc grains, temporal splits, feature scope, and evaluation design.

Local presence was verified on 2026-08-02. Access time must not be inferred from the verification date or file metadata.

## 11. Checksum and manifest requirements

The extracted-file inventory and SHA-256 calculation are complete. A future machine-readable manifest must bind these paths/checksums to an immutable dataset ID, code revision, inspection environment, source/rules evidence, quality results, and every downstream interim, processed, split, feature, model, forecast, and evaluation artifact.

Any later checksum difference must fail closed and trigger provenance review. If the original archive becomes available, its exact filename, byte size, checksum, acquisition evidence, and extraction method must be recorded separately.

```yaml
dataset_name: "Corporación Favorita Grocery Sales Forecasting"
provider: "Corporación Favorita C.A."
platform: "Kaggle"
source_url: "https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting"
source_type: "kaggle_competition_dataset"
classification: "real_public_restricted_access"
intended_use:
  - "MSc Individual Project research"
  - "real-data demand forecasting training and evaluation"
  - "EDIP decision-intelligence research"
  - "future CITP professional evidence"
  - "future PhD research preparation"
redistribution_allowed: false
raw_data_tracked_in_git: false
local_raw_path: "data/raw/favorita-grocery-sales-forecasting/"
access_date: "pending_verification"
archive_checksum_sha256: "pending_verification"
file_inventory_status: "verified_expected_file_set"
dataset_version: "pending_verification"
competition_rules_reference: "pending_verification"
research_scope:
  - "MSc Individual Project"
  - "future CITP professional evidence"
  - "future PhD research pathway"
```

## 12. MSc Individual Project relevance

The real Favorita observations are intended for forecasting training, validation, and testing. Research use still requires approved cleaning semantics, leakage-safe temporal splits, baselines, grains/horizons, metrics, error analysis, ethics/privacy review, manifests, and limitations. The verified raw set is not yet research-ready.

## 13. CITP evidence relevance

This work may support future CITP evidence through responsible restricted-data handling, provenance/rules/privacy judgment, reproducible engineering, architecture trade-offs, review evidence, limitations, and reflection. It does not establish professional competence, influence, outcomes, an SFIA level, a CITP award, or production readiness.

## 14. PhD research pathway relevance

The dataset may support future preparation in trustworthy forecasting, calibrated uncertainty, evidence sufficiency, abstention, HITL decision quality, policy-grounded recommendations, and safe simulated execution. These are directions only and require separate hypotheses, ethics, governance, experimental design, statistical analysis, and approvals.

## 15. Real-data and synthetic-data boundary

Real Favorita observations may become ML ground truth only after approved governance and transformation gates. Synthetic EDIP data may supplement missing inventory, supplier, warehouse, purchase-order, approval, and simulated-execution capabilities.

Synthetic operational data must not be mixed into real ML ground truth without explicit field/relationship provenance and an approved experimental design. Generated relationships must never be described as real Corporación Favorita facts.

## 16. Prohibited claims

Do not claim an open licence, redistribution permission, a verified archive/access timestamp/version/rules snapshot, research readiness, institutional approval, Corporación Favorita endorsement, EDIP equivalence to its operational platform, real status for synthetic relationships, production readiness, real-world decision value without evaluation, or a CITP/PhD outcome.

## 17. Post-download validation checklist

- [x] Confirm eight expected CSVs are regular files directly under the verified raw path.
- [x] Confirm no nested `.csv` directories remain.
- [x] Record relative paths, bytes, headers, rows, schemas, date ranges, nulls, duplicates, key ranges, and SHA-256 values.
- [x] Stream `train.csv` without loading it completely into memory.
- [x] Verify train/test store and item references and transaction-store references.
- [x] Verify the raw path is ignored and no raw file is tracked, staged, or reported as changed.
- [ ] Record reliable Kaggle access evidence, dataset revision, rules snapshot, and original archive details.
- [ ] Approve privacy, retention, backup, deletion, and incident responsibilities.
- [ ] Create and validate the machine-readable manifest.
- [ ] Approve cleaning rules, target semantics, grains, splits, and evaluation scope.
- [ ] Obtain required institutional, academic-supervisor, and data-owner reviews.
- [ ] Recheck Docker context, releases, reports, and Git staging before publication or packaging.
