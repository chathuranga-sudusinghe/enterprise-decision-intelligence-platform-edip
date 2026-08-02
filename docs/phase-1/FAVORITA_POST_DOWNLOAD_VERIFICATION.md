# Favorita Post-Download Verification

- Verification date: 2026-08-02
- Dataset: Corporación Favorita Grocery Sales Forecasting
- Classification: `real_public_restricted_access`
- Raw-data path: `data/raw/favorita-grocery-sales-forecasting/`
- Result: expected extracted file set verified; downstream research-readiness gates remain open

## 1. Verification purpose

This report records a read-only, post-download inspection of the local Corporación Favorita competition data. It establishes the files and measurable properties observed locally without claiming a verified Kaggle access timestamp, archive identity, dataset revision, open licence, redistribution permission, research approval, or research readiness.

## 2. Inspection method

The eight expected CSV files were inspected without modifying them. A Python standard-library scanner read each file sequentially, parsed CSV rows, and calculated SHA-256 from the same unchanged byte stream. It collected headers, row counts, malformed-row counts, null counts, bounded identifier sets, date and numeric ranges, and practical duplicate evidence.

The inspection did not rename, move, clean, transform, sample, delete, or open any raw file for writing. Counts in this report exclude the header row.

## 3. Raw directory confirmation

The verified directory is `data/raw/favorita-grocery-sales-forecasting/`.

Exactly eight expected regular files were present directly beneath that directory:

- `holidays_events.csv`
- `items.csv`
- `oil.csv`
- `sample_submission.csv`
- `stores.csv`
- `test.csv`
- `train.csv`
- `transactions.csv`

No nested directory, including a directory with a `.csv` suffix, was observed. The original downloaded archive was not present in the inspected boundary and therefore could not be identified or checksummed.

## 4. Verified file inventory

| Filename | Bytes | Rows | Columns | SHA-256 |
|---|---:|---:|---:|---|
| `holidays_events.csv` | 22,309 | 350 | 6 | `81a183d6c4d691b57f84a0fde6bbf734a5b3c36a74b97378bf33a592648e2999` |
| `items.csv` | 101,841 | 4,100 | 4 | `1efd8295f52c8531ec5bf6c3de37228a56bad2f2c653e79c4869baaf637edcc6` |
| `oil.csv` | 20,580 | 1,218 | 2 | `944b23b857580f9d804399346fd3ed69bffcb7facfd98c55fdb408b8d057cca7` |
| `sample_submission.csv` | 40,445,582 | 3,370,464 | 2 | `50b93078008e68bdd0818b18ca2493c23e7ad7e2c506b2b263c3347dad1d77db` |
| `stores.csv` | 1,387 | 54 | 5 | `af503b2bce11d7906d249f81cc0598f10e2addcc9f6c59aa2d95c9f2652c296b` |
| `test.csv` | 126,163,026 | 3,370,464 | 5 | `b9d3bef11ca9b058bdd4c1fa3a69b8a595f4ef39983051eb5ab416e255f13ae6` |
| `train.csv` | 4,997,452,288 | 125,497,040 | 6 | `ccf4236a6b58b0db937b8c5006a0ad8fffef6acd06bed1c10cd5cd4d68d93248` |
| `transactions.csv` | 1,552,637 | 83,488 | 3 | `e116384a6981af74932832436aa2f6a43121f77ca81accc44e3a5160158ca03c` |

The observed local modification timestamps span 2017-10-19T15:30:05Z through 2017-10-19T15:30:31Z. These timestamps are filesystem metadata, not verified access dates or dataset-version evidence.

## 5. Schema summary

| File | Verified header |
|---|---|
| `holidays_events.csv` | `date`, `type`, `locale`, `locale_name`, `description`, `transferred` |
| `items.csv` | `item_nbr`, `family`, `class`, `perishable` |
| `oil.csv` | `date`, `dcoilwtico` |
| `sample_submission.csv` | `id`, `unit_sales` |
| `stores.csv` | `store_nbr`, `city`, `state`, `type`, `cluster` |
| `test.csv` | `id`, `date`, `store_nbr`, `item_nbr`, `onpromotion` |
| `train.csv` | `id`, `date`, `store_nbr`, `item_nbr`, `unit_sales`, `onpromotion` |
| `transactions.csv` | `date`, `store_nbr`, `transactions` |

All rows in all eight files matched their respective header width; zero malformed-width rows were observed.

## 6. Large-file inspection method

`train.csv` was streamed one record at a time and was never loaded fully into memory. SHA-256, row count, null counts, date and identifier ranges, promotion profile, and target summary were accumulated in one sequential pass. Only bounded sets of store and item identifiers and scalar aggregates were retained.

The same streaming approach was used for `test.csv` and `sample_submission.csv`. Because their `id` fields were strictly increasing and unique across their complete scans, exact duplicate records are impossible in those files. Smaller files were checked with exact row-set duplicate detection.

## 7. Row counts and date ranges

| File | Rows | Observed date range |
|---|---:|---|
| `holidays_events.csv` | 350 | 2012-03-02 to 2017-12-26 |
| `items.csv` | 4,100 | not applicable |
| `oil.csv` | 1,218 | 2013-01-01 to 2017-08-31 |
| `sample_submission.csv` | 3,370,464 | not applicable |
| `stores.csv` | 54 | not applicable |
| `test.csv` | 3,370,464 | 2017-08-16 to 2017-08-31 |
| `train.csv` | 125,497,040 | 2013-01-01 to 2017-08-15 |
| `transactions.csv` | 83,488 | 2013-01-01 to 2017-08-15 |

Training `unit_sales` has minimum -15,372, maximum 89,440, and arithmetic mean 8.554865. The scan found 7,795 negative, zero zero-valued, and 125,489,245 positive target rows. Negative target semantics require an explicit cleaning and modelling decision; they were not altered during verification.

## 8. Identifier and referential-integrity findings

- `stores.csv` contains 54 unique `store_nbr` values, ranging from 1 to 54.
- `items.csv` contains 4,100 unique `item_nbr` values, ranging from 96,995 to 2,134,244.
- `train.csv` references 54 stores and 4,036 items. Every observed training store and item identifier is present in its master file.
- `test.csv` references 54 stores and 3,901 items. Every observed test store and item identifier is present in its master file.
- `transactions.csv` references 54 stores. Every observed transaction store identifier is present in `stores.csv`.
- Training IDs are strictly increasing and unique from 0 through 125,497,039.
- Test IDs are strictly increasing and unique from 125,497,040 through 128,867,503.
- Sample-submission IDs are strictly increasing and unique over the same 125,497,040 through 128,867,503 range.

These are observed child-to-master coverage checks. They do not claim that every master item occurs in every fact file, or that all business relationships needed by EDIP exist in this competition dataset.

## 9. Null and duplicate findings

- `train.csv` contains 21,657,651 null `onpromotion` values, or 17.257499% of rows. All other training fields are non-null.
- Its promotion profile is 21,657,651 null, 96,028,767 false, and 7,810,622 true values.
- `oil.csv` contains 43 null `dcoilwtico` values, or 3.530378% of rows. Its date field is non-null.
- All inspected fields in the other six files are non-null.
- No exact duplicate rows were found in the five smaller files checked with row sets.
- No exact duplicate rows can occur in `train.csv`, `test.csv`, or `sample_submission.csv` because each complete scan found a strictly increasing unique `id` field.

Nulls and negative sales are documented observations, not automatically defects. Their treatment remains an approved downstream data-contract decision.

## 10. Git-ignore and redistribution controls

`git check-ignore -v data/raw/favorita-grocery-sales-forecasting/train.csv` identified `.gitignore` line 113, rule `data/raw/*`, as the applicable ignore rule.

`git ls-files data/raw/favorita-grocery-sales-forecasting` returned no tracked path. Staged-diff and raw-path status checks also returned no raw file. Therefore, the inspected raw set is ignored, untracked, unstaged, and absent from the Git change set at verification time.

Raw competition data must not be committed, packaged, mirrored, attached to issues or releases, embedded in documentation, or otherwise redistributed. This report records aggregate metadata and checksums only; it does not grant redistribution rights.

## 11. Confirmed facts

- The eight expected extracted CSV files are locally present at the verified path.
- Each path is a regular file and its header, byte size, row count, SHA-256, and bounded quality profile were measured directly.
- `train.csv` was processed by streaming rather than full-memory loading.
- All observed train/test item and store references and transaction store references are covered by the corresponding master file.
- Null promotion and oil-price values and negative training sales exist at the measured rates/counts.
- No malformed-width record was observed.
- The raw path is currently protected by Git ignore and no raw file is tracked or staged.

## 12. Unverified governance decisions

The following remain `pending_verification` or pending approval:

- exact Kaggle access timestamp and authenticated acquisition evidence;
- accepted competition-rules version or preserved rules snapshot;
- Kaggle dataset revision and original archive filename, byte size, and SHA-256;
- download command, extraction tool/version, and custody trail before local extraction;
- final privacy and sensitive-field assessment;
- retention, backup, deletion, access-control, and incident-response decisions;
- institutional ethics, academic-supervisor, and data-owner approvals where required;
- cleaning semantics for negative sales, missing promotions, and missing oil prices;
- research grains, horizons, leakage-safe temporal splits, baselines, metrics, and evaluation design; and
- machine-readable manifest creation and downstream lineage binding.

## 13. Risks and limitations

- The original archive was not available, so archive-level integrity and extraction reproducibility are not verified.
- SHA-256 values establish the inspected local file identities but do not independently prove they match a named Kaggle revision.
- Filesystem modification times must not be treated as access timestamps.
- Exact duplicate detection for the three large ID-bearing files relies on complete-scan ID uniqueness and strict ordering; it does not separately materialize a full-row hash set.
- This is a structural and quality audit, not a statistical representativeness, bias, privacy, leakage, or forecasting-performance evaluation.
- Local data verification does not establish open licensing, redistribution rights, institutional approval, research readiness, production readiness, or real-world decision value.

## 14. Acceptance result

**Result: PARTIAL ACCEPTANCE — VERIFIED LOCAL RAW FILE SET.**

The extracted Favorita file set passes the post-download presence, identity, schema, parsability, bounded quality, referential-coverage, and Git-containment checks performed here. It is accepted as an immutable local raw input for the next controlled audit batch.

It is not accepted as research-ready, redistribution-approved, publication-ready, or production-ready. Downstream ingestion and modelling must remain gated on the governance and research-design decisions listed above.

## 15. Recommended next batch

`Phase 1 Favorita Data Foundation, Database, and RAG Audit`

That batch should define the canonical machine-readable manifest, schema and cleaning contracts, privacy and retention decisions, leakage-safe research splits, database ownership and loading boundaries, derived-data lineage, and the permitted RAG corpus boundary without placing raw competition data in Git.
