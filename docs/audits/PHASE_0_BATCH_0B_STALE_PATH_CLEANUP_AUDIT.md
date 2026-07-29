# EDIP Phase 0 Batch 0B — Stale-Path Cleanup Audit

- Audit date: 29 July 2026
- Repository: `enterprise-decision-intelligence-platform-edip`
- Branch: `main`
- Batch: Phase 0 Batch 0B — Unambiguous stale-path cleanup
- Evidence basis: `docs/audits/EDIP_REPOSITORY_STRUCTURE_AUDIT.md`
- Change state: Staged locally; not committed or pushed

## 1. Purpose and scope

This record documents the controlled removal of eight tracked, zero-byte paths that the authoritative repository structure audit classified as empty, stale, redundant, or misleading. The batch is deliberately limited to paths with no identified operational role.

No source code, dependency manifest, test, Docker file, CI file, `README.md`, RAG implementation, workflow implementation, forecasting implementation, monitoring implementation, or infrastructure definition is changed by this batch.

## 2. Initial repository state

- The active branch was `main`.
- The repository was aligned with `origin/main` before the Batch 0B changes.
- All eight paths selected for removal were tracked by Git.
- All eight selected files were zero bytes.
- Reference inspection found no operational dependency on any selected path.
- The eight deletions were staged when this record was prepared.
- The authoritative audit remained unchanged.

## 3. Exact removed paths

| Removed path | Previous condition | Audit classification |
|---|---|---|
| `app/services/app/services` | Tracked, zero-byte anomalous file | **EMPTY** and **MISLEADING** |
| `configs/.gitkeep` | Tracked, zero-byte marker in a populated directory | **STALE** |
| `database/.gitkeep` | Tracked, zero-byte marker in a populated directory | **STALE** |
| `docs/.gitkeep` | Tracked, zero-byte marker in a populated directory | **STALE** |
| `infra/.gitkeep` | Tracked, zero-byte marker in a populated directory | **STALE** |
| `monitoring/.gitkeep` | Tracked, zero-byte marker in a populated directory | **STALE** |
| `pipelines/.gitkeep` | Tracked, zero-byte marker in a populated directory | **STALE** |
| `tests/.gitkeep` | Tracked, zero-byte marker in a populated directory | Redundant; **REMOVE** |

## 4. Why each category was removed

### Empty anomalous path

`app/services/app/services` was not a Python module, configuration file, data artifact, or documented interface. Its duplicated directory-like name could mislead maintainers about package ownership. Its zero-byte content and absence from operational references provided no evidence of a runtime purpose.

### Redundant directory markers

The seven removed `.gitkeep` files were located in directories that already contain tracked substantive files. Git therefore does not require those markers to preserve the directories. Removing them reduces structural noise without removing directory ownership, executable content, configuration, tests, or documentation.

## 5. Intentionally retained placeholders

| Retained path | Reason for retention |
|---|---|
| `database/migrations/.gitkeep` | Preserves a specifically named migration location while database migration ownership remains planned or partially defined. |
| `database/seeds/.gitkeep` | Preserves a specifically named seed-data location while seed ownership remains planned or partially defined. |
| `data/synthetic/.gitkeep` | Preserves the directory boundary for generated synthetic datasets, which are intentionally ignored rather than tracked. |

These placeholders represent distinct future or generated-content boundaries. They are not equivalent to redundant markers in already populated parent directories.

## 6. Deferred decisions

### Root `__init__.py`

The root `__init__.py` remains unchanged. Although the authoritative audit identified it as likely unused, deletion requires a separate final import and packaging decision. It is therefore not treated as an unambiguous Batch 0B removal.

### `app/core/metrics.py`

`app/core/metrics.py` remains unchanged. The authoritative audit identified duplicated monitoring responsibility and recommended removal only after verification. That decision belongs to monitoring canonicalisation, including import, metric-registration, dashboard, Compose, and deployment checks, and is deferred to a separate batch.

## 7. Reference and dependency inspection

Inspection established that:

- no operational references to the eight removed paths were found;
- all eight files were tracked and zero bytes before deletion;
- the removed `.gitkeep` files did not carry configuration or executable content;
- each affected directory remains represented by other tracked files;
- `app/services/app/services` was not an importable `.py` module and had no identified application dependency; and
- the retained placeholders and deferred files were explicitly excluded from the deletion set.

The successful application imports, compilation check, route smoke test, and Compose configuration check provide additional evidence that the removed paths were not required by the validated runtime surfaces.

## 8. Validation commands and results

| Validation command or recorded check | Result |
|---|---|
| Branch and upstream-state inspection | `main`; aligned with `origin/main` before changes |
| Git tracking and file-size inspection | All eight removed files were tracked and zero bytes |
| Repository reference search | No operational references found |
| `python -c "import app"` | Passed |
| `python -c "from app.main import app; print(app.title)"` | Passed; application title was `EDIP API` |
| `python -m compileall -q app pipelines scripts tests` | Passed |
| FastAPI route smoke test | Passed; 14 registered routes |
| Focused pytest validation run | 130 passed, 3 failed |
| Full pytest collection | Blocked by `ModuleNotFoundError: No module named 'kafka.vendor.six.moves'` |
| `git diff --check` | Passed |
| `docker compose config --quiet` | Passed |

The focused pytest result is deliberately recorded as mixed, not as a complete pass.

## 9. Known unrelated test limitations

Three focused tests failed:

- `test_agent_workflow_urgent_replenishment_demo`
- `test_agent_workflow_stockout_risk_demo`
- `test_agent_workflow_reorder_vs_transfer_demo`

These tests depend on external Pinecone access and returned HTTP 500. Their failure mode concerns an external RAG dependency, not any removed zero-byte path.

Full pytest collection was separately blocked by:

```text
ModuleNotFoundError: No module named 'kafka.vendor.six.moves'
```

The affected modules were:

- `tests/integration/test_kafka_end_to_end_flow.py`
- `tests/unit/test_kafka_consumer.py`
- `tests/unit/test_kafka_producer.py`

Pytest also reported a local `.pytest_cache` permission warning. These dependency and local-environment limitations pre-existed the stale-path cleanup and are outside Batch 0B. They must not be represented as successful validation, but their observed failure modes provide no evidence that the eight deletions caused them.

## 10. Risk assessment

| Risk | Assessment | Control |
|---|---|---|
| Hidden runtime dependency on a removed path | Low | Reference search, application imports, compilation, route smoke test, and Compose validation |
| Loss of an intentionally reserved directory | Low | Only redundant parent markers were removed; three meaningful placeholders were retained |
| Accidental scope expansion | Low | Exact eight-path deletion set; deferred ambiguous files; no implementation edits |
| Misrepresenting validation quality | Controlled | Passing, failing, blocked, and warning outcomes are reported separately |
| Difficult rollback | Low | All deletions are tracked in Git and can be restored from `HEAD` or reverted as one focused commit |

No evidence shows that the deletions changed runtime behaviour. This conclusion is limited to the inspected references and validation surfaces; it does not convert the unrelated external-service and dependency failures into passing tests.

## 11. Outcome

Batch 0B removes one misleading empty anomaly and seven redundant directory markers while preserving meaningful placeholders and deferring files that require separate architectural decisions.

The import, compilation, FastAPI route, diff-integrity, and Compose checks passed. Focused tests produced 130 passes and three external-Pinecone-related HTTP 500 failures. Full pytest collection remained blocked by the Kafka dependency error. On the available evidence, the cleanup is structurally safe and no runtime behaviour change is attributable to the eight deletions.

## 12. Rollback method

Before commit, restore the staged and working-tree deletions from `HEAD` for the exact eight paths:

```bash
git restore --source=HEAD --staged --worktree -- \
  app/services/app/services \
  configs/.gitkeep \
  database/.gitkeep \
  docs/.gitkeep \
  infra/.gitkeep \
  monitoring/.gitkeep \
  pipelines/.gitkeep \
  tests/.gitkeep
```

If the batch is later committed, use a focused `git revert <commit>` so the restoration remains explicit and auditable. No destructive history rewrite is required.

## 13. Professional reflection

This batch demonstrates controlled migration through classification, dependency inspection, narrow change boundaries, proportionate validation, and an explicit rollback path. Systems thinking is reflected in distinguishing cosmetic-looking files by their architectural role: redundant markers in populated directories can be removed safely, while migration, seed, and synthetic-data placeholders preserve meaningful subsystem boundaries.

The decision also separates low-risk structural hygiene from monitoring ownership, Python packaging, external RAG availability, and Kafka dependency repair. Keeping those concerns in independent batches reduces causal ambiguity, makes review and rollback simpler, and prevents a small cleanup from acquiring unrelated operational risk. The mixed test evidence is retained without being overstated, supporting an honest professional record of both the validated outcome and the repository limitations that remain.
