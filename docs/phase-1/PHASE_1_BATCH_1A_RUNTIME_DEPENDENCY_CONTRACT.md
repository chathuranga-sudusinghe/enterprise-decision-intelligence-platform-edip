# EDIP Phase 1 Batch 1A: Runtime and Dependency Contract

| Field | Value |
|---|---|
| Document status | Batch 1A.1 implemented and locally validated; Kafka collection blocker remains |
| Evidence date | 2026-08-01 |
| Branch inspected | `chore/phase-1-runtime-dependency-contract` |
| Scope | Python runtime, dependency manifests, imports, CI, Docker, Compose, LangGraph, Kafka test collection, and clean-environment risks |
| Change authority | Batch 1A inspection plus approved Batch 1A.1 implementation evidence |

## Purpose and evidence boundary

This document records the EDIP Phase 1 Batch 1A runtime and dependency baseline, its recommendations, and the approved Batch 1A.1 implementation result. Batch 1A.1 does not resolve Kafka and does not establish complete test-suite health.

Findings labelled **Confirmed** were observed in repository files or commands run in the current checkout. Items labelled **Recommendation** are future decisions and require implementation, validation, and review before they become repository fact.

## Executive decision summary

**Confirmed**

- The active repository virtual environment is a WSL/Linux environment using Python 3.12.3 and pytest 9.0.2.
- Docker uses the Python 3.12 minor line, while test CI and the README specify Python 3.11.
- `requirements.txt` is the runtime manifest; `requirements-dev.txt` recursively includes it and adds development tools. `requirements_full.txt` is a 271-entry environment snapshot with no defined authoritative role.
- LangGraph is imported by `app/agents/langgraph_workflow.py` but is absent from all three dependency files and absent from the current virtual environment.
- `app.main` imports successfully only because the LangGraph import catches every exception and substitutes `StateGraph = None`; constructing `EDIPLangGraphWorkflow` then raises `ImportError`.
- Full pytest collection under the current environment discovers 136 tests and stops with three Kafka import errors.
- The Kafka failure occurs at module-import time before any broker connection. `kafka-python==2.0.2` attempts `from kafka.vendor.six.moves import range`, but that vendored module is unavailable in the installed package/runtime combination.
- `python -m pip check` reports no broken installed requirements. This does not prove that manifests declare every package imported by the repository.

**Recommendation**

- Adopt Python 3.12 as the single supported minor version for Phase 1 because the active local environment and Docker already use it; align CI and contributor documentation to it.
- Implement runtime alignment and an explicit, validated LangGraph dependency as one small change. Keep Kafka resolution as a separate, reviewed follow-up so the cause, package decision, and rollback remain independently testable.

## 1. Current Python versions across local, CI, and Docker

### Confirmed findings

| Surface | Evidence | Current version contract | Assessment |
|---|---|---|---|
| Active local virtual environment | `.venv/pyvenv.cfg`; `.venv/bin/python --version` through WSL | Python 3.12.3 | Actual current local runtime; Unix-style environment, not a native Windows venv |
| Test CI | `.github/workflows/integration-ci.yml` | Python 3.11 | Conflicts with local and Docker |
| API Docker image | `Dockerfile` | `python:3.12-slim` | Python 3.12 minor line; patch and digest float |
| Compose topic initializer | `docker-compose.yml` | `python:3.12-slim` | Matches Docker minor line; patch and digest float |
| Airflow Compose services | `docker-compose.yml` | `apache/airflow:3.1.0` | Airflow-owned Python runtime is implicit, not the EDIP API contract |
| Contributor README | `README.md` | Python 3.11 | Follows CI but conflicts with the active environment and Docker |

No `.python-version`, `runtime.txt`, `pyproject.toml`, `setup.cfg`, `setup.py`, Pipfile, Poetry lock, or uv lock defines a repository-wide Python constraint.

### Recommendation

Support Python 3.12 as the single Phase 1 minor version. Record the exact patch used in each validation environment, but avoid claiming patch-level equivalence until CI and the container use a controlled image/version policy. Python 3.12.3 is confirmed locally; it is not yet proven to be the exact patch behind the floating Docker tag.

## 2. Runtime and development dependency manifests

### Confirmed findings

| File or mechanism | Content/behavior | Current role | Contract issue |
|---|---|---|---|
| `requirements.txt` | 14 exact direct pins | API runtime manifest | Missing LangGraph; includes legacy Kafka client |
| `requirements-dev.txt` | `-r requirements.txt` plus six exact development pins | Development/test manifest | Correctly inherits runtime, but CI installs `requirements.txt` first and then installs it again through this file |
| `requirements_full.txt` | 271 exact entries | Large local environment snapshot | Stale/non-canonical; contains packages and versions not present in the active venv and no declared generation process |
| Docker build | Copies both manifests but installs only `requirements.txt` | Runtime image | Copying the development manifest is unnecessary; missing LangGraph remains missing |
| Test CI | Installs runtime, then development manifest | CI environment | Redundant runtime resolution and Python-version drift |
| Compose service commands | Run unpinned `pip install` for Kafka and Airflow task dependencies | Service-local runtime mutation | Non-deterministic and separate from authored manifests |

`pytest.ini` contains only `pythonpath = .` and `testpaths = tests`. It defines discovery roots but no environment markers, live-test separation, or collection gate.

### Recommendation

- Keep `requirements.txt` as the lean online/API runtime input.
- Keep `requirements-dev.txt` as the single CI/test install entry point and install it once.
- Define separate offline/training dependencies rather than putting Airflow, notebooks, and the complete ML environment into the API runtime.
- Redefine or retire `requirements_full.txt`; do not treat it as a production or clean-environment lock.
- Replace Compose-time unpinned installs only in a later, separately validated container/orchestration batch.

## 3. Dependencies imported by code but missing from manifests

### Confirmed findings

| Import | Import location | `requirements.txt` / `requirements-dev.txt` | Effect |
|---|---|---|---|
| `langgraph.graph` | `app/agents/langgraph_workflow.py` | Missing | Application module import hides the absence; workflow construction fails |
| `joblib` | Forecast training, evaluation, and scoring pipelines | Missing | Offline pipeline imports fail in a clean base/dev install |
| `sklearn` (`scikit-learn`) | Forecast training/evaluation pipelines | Missing | Offline training/evaluation imports fail in a clean base/dev install |
| `airflow` | `pipelines/airflow_dags/edip_orchestration_demo_dag.py` | Missing | DAG parsing requires an Airflow-specific environment |

The last three packages exist in `requirements_full.txt`, but that snapshot is neither installed by CI/Docker nor defined as a supported manifest. Their absence from the API runtime may be appropriate if explicit offline and Airflow dependency boundaries are created.

### Recommendation

Add LangGraph to the online runtime manifest only after selecting and testing an exact compatible version under Python 3.12. Put offline forecasting and Airflow dependencies in capability-specific manifests rather than expanding the API image.

## 4. Duplicate, obsolete, or incompatible packages

### Confirmed findings

- CI resolves `requirements.txt` twice: directly, then recursively through `requirements-dev.txt`.
- `requirements.txt` pins `kafka-python==2.0.2`; `requirements_full.txt` records `kafka-python==2.3.0`; Compose installs unpinned `kafka-python`. These are three incompatible dependency contracts even though the active venv currently contains 2.0.2.
- `requirements_full.txt` records Airflow 3.1.8, while Compose uses Airflow image 3.1.0.
- `requirements_full.txt` contains `psycopg`, `psycopg-binary`, and `psycopg2-binary` without an application-level database-driver decision.
- `requirements_full.txt` contains both `PyYAML` and `PyYAML-ft`, multiple web frameworks, Jupyter tooling, Airflow, and broad ML tooling. This is consistent with an environment freeze, not a minimal EDIP runtime contract.
- The active venv does not contain LangGraph, joblib, scikit-learn, psycopg, psycopg2-binary, or SQLAlchemy, despite several of these appearing in `requirements_full.txt`.
- `pip check` reports no broken installed requirements. It validates installed distribution metadata, not undeclared imports or cross-manifest consistency.

### Recommendation

Do not bulk-upgrade or copy `requirements_full.txt` into the runtime. Decide one package owner and one manifest per execution context, remove redundant CI installation, and test each selected pin in a clean Python 3.12 environment.

## 5. LangGraph dependency status

### Confirmed findings

- `app/agents/langgraph_workflow.py` conditionally imports `END` and `StateGraph` from `langgraph.graph` inside `try/except Exception`.
- On failure it assigns `END = "__end__"` and `StateGraph = None`.
- The current environment reports `StateGraph` unavailable and `END` equal to the fallback string.
- `EDIPLangGraphWorkflow.__init__` raises `ImportError("LangGraph is not installed. Install it before using EDIPLangGraphWorkflow.")` when `StateGraph` is `None`.
- LangGraph is absent from `requirements.txt`, `requirements-dev.txt`, `requirements_full.txt`, and the active venv.
- `app.main` can therefore import while the advertised workflow remains non-constructible.

### Recommendation

Select and pin a Python-3.12-compatible LangGraph version, install it in a clean environment, and require both direct `langgraph.graph` import and actual EDIP workflow construction to pass. Replace the broad optional-import behavior with fail-fast behavior only after the manifest is authoritative and tests cover the failure contract.

## 6. Exact cause of the Kafka collection problem

### Confirmed finding

The current venv contains `kafka-python==2.0.2`, matching `requirements.txt`. Three test modules import `scripts.kafka_consumer` or `scripts.kafka_producer` at collection time:

- `tests/integration/test_kafka_end_to_end_flow.py`;
- `tests/unit/test_kafka_consumer.py`; and
- `tests/unit/test_kafka_producer.py`.

Those scripts import `KafkaConsumer` or `KafkaProducer` from `kafka`. Importing the installed package reaches `.venv/lib/python3.12/site-packages/kafka/codec.py`, which executes:

```python
from kafka.vendor.six.moves import range
```

Collection then fails with:

```text
ModuleNotFoundError: No module named 'kafka.vendor.six.moves'
```

This is a package/import compatibility failure in the current Python 3.12.3 plus `kafka-python==2.0.2` environment. The evidence does not show a broker connection attempt or broker failure. It also does not by itself prove which replacement package/version is correct.

### Recommendation

Do not patch vendored files or add an unrelated top-level `six` dependency as an assumed fix. In a separate Kafka decision batch, compare the smallest supported client options, verify producer and consumer imports under Python 3.12, run the existing fake-backed tests, and separately retain live-broker validation as later evidence.

## 7. Current pytest collection result

### Confirmed result

Command:

```bash
.venv/bin/python -m pytest --collect-only -q
```

Observed result:

- Python 3.12.3;
- pytest 9.0.2;
- 136 tests collected;
- three collection errors, all caused by the Kafka import described above;
- exit code 1;
- collection interrupted after 11.39 seconds; and
- a non-blocking warning that pytest could not write `.pytest_cache/v/cache/lastfailed` because of local permissions.

No tests were executed by this command. This is not evidence of full-suite health. CI on Python 3.11 was inspected but not rerun, and live external services were not exercised.

## 8. Clean-environment risks

### Confirmed risks

1. Python 3.11 and 3.12 surfaces can resolve or execute dependencies differently.
2. A clean runtime install lacks LangGraph, so the API can import while workflow construction fails later.
3. A clean base/dev install cannot import the offline training/evaluation pipelines that require joblib and scikit-learn.
4. Airflow DAG imports depend on an environment not described by the primary manifests.
5. `requirements_full.txt` cannot reproduce the active venv and is too broad to serve as the API contract.
6. Compose-time unpinned installation can change without a repository diff.
7. Root `/health` returns a static success payload and does not prove LangGraph or downstream readiness.
8. The API has no distinct `/health/live` and `/health/ready` contract.
9. PostgreSQL in Compose is Airflow metadata storage; no controlled empty-state initialization of EDIP application data is proven.
10. Local artifact availability and external credentials can affect runtime tests after collection is restored.
11. The WSL `.venv` is not a native Windows virtual environment and should not be presented as portable.

## 9. Recommended single supported Python version

### Recommendation: Python 3.12

Rationale:

- the active and directly measured local environment is Python 3.12.3;
- the API Dockerfile already uses the Python 3.12 minor line;
- the Compose Python helper already uses the Python 3.12 minor line;
- only test CI and contributor documentation currently select 3.11; and
- choosing 3.12 minimizes changed execution surfaces.

The supported contract should initially be stated as Python 3.12, with exact patch versions recorded in CI/container evidence. A later ADR may adopt stricter patch or image-digest pinning after compatibility and maintenance trade-offs are reviewed.

## 10. Smallest safe implementation scope

### Recommendation

Use two independently reviewable implementation steps; do not combine Kafka resolution with broad dependency cleanup.

**Step 1A.1 — runtime and LangGraph contract**

1. Align test CI and contributor instructions to Python 3.12.
2. Select and pin one validated LangGraph version in `requirements.txt`.
3. Replace the broad optional LangGraph import with the validated direct import so a broken runtime fails at startup rather than first workflow construction.
4. Install CI dependencies once through the unchanged `requirements-dev.txt`.
5. Add a focused runtime-contract test that imports `app.main`, imports `langgraph.graph`, and constructs the EDIP workflow with deterministic test doubles.
6. Validate from a new Python 3.12 environment and the API container.
7. Record the Kafka collection failure as an unchanged, explicit blocker.

**Step 1A.2 — Kafka dependency decision, separately approved**

Evaluate and select the supported Kafka client/version, then restore full collection. This document does not select or implement that solution.

This sequence is intentionally smaller than reconciling Airflow, forecasting, PostgreSQL initialization, Docker readiness, and all historical environment packages at once. It does not complete Phase 1.

## 11. Files that should change

### Recommended Step 1A.1 change set

| File | Recommended future change |
|---|---|
| `requirements.txt` | Add the selected, tested LangGraph pin; do not bulk-upgrade unrelated packages |
| `app/agents/langgraph_workflow.py` | Replace the broad optional-import fallback with the validated direct LangGraph import |
| `.github/workflows/integration-ci.yml` | Use Python 3.12, install `requirements-dev.txt` once, add explicit import/contract validation |
| `README.md` | Change the supported local Python instruction from 3.11 to 3.12 after validation |
| `tests/unit/test_runtime_dependency_contract.py` (new) | Prove application import, real LangGraph import, and workflow construction with deterministic doubles |

`Dockerfile` already selects Python 3.12 and need not change merely to align the minor version. A later container-hardening step should decide patch/digest pinning, remove the unused development-manifest copy, and add startup/liveness/readiness smoke evidence.

### Later, separately scoped files

- `requirements.txt`, Kafka scripts, and Kafka tests only after the Kafka client decision is approved;
- an offline dependency manifest for forecasting pipelines;
- an Airflow-specific constraint/manifest if Airflow remains justified; and
- database initialization and smoke-test assets for controlled PostgreSQL proof.

## 12. Files that must remain unchanged

For Step 1A.1, keep these files and areas unchanged unless a new finding requires an approved scope change:

- `requirements-dev.txt` and `pytest.ini`;
- all application business logic except the import contract in `app/agents/langgraph_workflow.py`;
- Kafka producer, consumer, topic initialization, generated events, and Kafka tests;
- forecasting model logic and generated artifacts;
- RAG configuration, credentials, code, and corpus;
- database DDL/DML and existing data;
- `docker-compose.yml` and Airflow services;
- Kubernetes, Terraform, monitoring, and ECS assets;
- frontend code; and
- the approved V2 architecture plan and Phase 0 audit history.

For this inspection batch, every existing repository file remains unchanged.

## 13. Validation commands

### Runtime and clean install

```bash
python3.12 --version
python3.12 -m venv .venv-clean
.venv-clean/bin/python -m pip install -r requirements-dev.txt
.venv-clean/bin/python -m pip check
```

Use a disposable environment outside the repository or remove it through the approved local cleanup workflow after evidence is captured.

### Imports and workflow contract

```bash
.venv-clean/bin/python -c "import app.main"
.venv-clean/bin/python -c "from langgraph.graph import END, StateGraph"
.venv-clean/bin/python -m pytest tests/unit/test_runtime_dependency_contract.py -q
```

### Collection and focused tests

```bash
.venv-clean/bin/python -m pytest --collect-only -q
.venv-clean/bin/python -m pytest tests/unit -q
.venv-clean/bin/python -m pytest tests/integration/test_monitoring_api.py tests/integration/test_forecast_api.py -q
```

Full collection must exit zero before claiming the collection gate is restored. Fake-backed Kafka tests must not be reported as live-broker evidence.

### Container evidence

```bash
docker build -t edip-api:phase-1-1a .
docker run --rm -d --name edip-api-1a -p 8000:8000 edip-api:phase-1-1a
curl --fail http://127.0.0.1:8000/health
docker logs edip-api-1a
docker stop edip-api-1a
```

A separate readiness endpoint and controlled test configuration are required before this becomes liveness/readiness acceptance evidence.

### Repository checks

```bash
git diff --check
git status --short
git diff --stat
```

## 14. Rollback approach

### Recommendation

1. Keep runtime alignment, LangGraph declaration, Kafka resolution, database initialization, and container readiness in separate commits/PRs.
2. Record the pre-change dependency files, Python outputs, collection error, and container behavior.
3. If Step 1A.1 fails, revert only its manifest, LangGraph import-contract, CI, README, and focused-test changes; do not edit the current `.venv` as a substitute for repository rollback.
4. Rebuild a disposable clean environment from the restored manifests and rerun import/collection checks.
5. Do not restore `requirements_full.txt` as the runtime source of truth.
6. Do not patch installed Kafka vendored files; recreate the environment from the approved manifest instead.

## 15. Residual limitations

- Kafka dependency selection and full collection remain unresolved by design.
- Full pytest execution has not been run because collection currently fails.
- CI Python 3.11 behavior was inspected from configuration, not rerun remotely.
- No clean Python 3.12 environment was created during this documentation-only batch.
- No dependency resolver test or package download was performed.
- No exact LangGraph version is recommended without clean-environment compatibility evidence.
- PostgreSQL empty-state initialization, deterministic forecast/RAG fixtures, and API readiness are later Phase 1 work.
- Root `/health` is not dependency-aware readiness.
- Docker image construction and Compose configuration do not prove container startup or service operation.
- Live Kafka, Pinecone, OpenAI, PostgreSQL, Airflow, AWS, ERP/CRM, Prometheus, and Grafana operation remain unverified.
- The local `.pytest_cache` permission warning remains an environment hygiene issue separate from the Kafka error.

## 16. Professional reflection

The strongest finding is that a successful module import and a green `pip check` can coexist with a broken runtime contract. The broad LangGraph exception hides a missing declared dependency until workflow construction, while Kafka fails earlier during collection. These are opposite failure modes caused by the same governance weakness: dependencies are not owned consistently across code, manifests, environments, and acceptance tests.

Choosing Python 3.12 is an architecture judgement based on minimizing change across verified execution surfaces, not a claim that every current package is compatible. Separating the LangGraph/runtime alignment from Kafka resolution keeps accountability and rollback clear. It also prevents an apparently convenient bulk upgrade from erasing the evidence needed to understand which decision fixed which risk.

Phase 1 should be accepted only when a clean, documented environment installs from authoritative manifests, imports the real application and workflow, collects the full suite, initializes controlled PostgreSQL state, uses deterministic fixtures, and starts the API container with meaningful liveness and readiness evidence. Until then, EDIP remains under controlled improvement and no complete test-suite or production-readiness claim is justified.

## Batch 1A.1 implementation result

### Selected contract

- **Python:** 3.12 is now the documented and CI-supported minor version; validation used Python 3.12.3. Docker already used `python:3.12-slim` and did not require modification.
- **LangGraph:** `langgraph==1.2.10`. An unpinned install in a disposable Python 3.12 environment resolved 1.2.10 as the current stable release. Its `END` and `StateGraph` imports succeeded, and the existing EDIP workflow compiled to `CompiledStateGraph` with deterministic inert agent doubles. No fallback version was required.

### Files changed

- deleted `requirements_full.txt` because it was not an authoritative manifest;
- added `langgraph==1.2.10` to `requirements.txt` while retaining its existing UTF-16LE encoding;
- replaced the broad optional LangGraph fallback in `app/agents/langgraph_workflow.py` with a direct import, without changing workflow logic;
- aligned `.github/workflows/integration-ci.yml` to Python 3.12 and one `requirements-dev.txt` installation;
- aligned the README's supported runtime statement to Python 3.12;
- added `tests/unit/test_runtime_dependency_contract.py`; and
- updated this implementation record.

`requirements-dev.txt`, the Dockerfile, Kafka files, and every explicitly excluded subsystem remained unchanged.

### Validation results

- clean Python 3.12.3 environment created under WSL `/tmp`;
- pip upgraded to 26.2;
- `requirements-dev.txt` installed successfully as the sole install entry point;
- `python -m pip check`: passed with no broken requirements;
- `python -c "import app.main"`: passed;
- `python -c "from langgraph.graph import END, StateGraph"`: passed;
- runtime dependency contract: 3 passed;
- existing monitoring and forecast checks: 11 passed;
- `python -m compileall -q app tests`: passed;
- `docker compose config --quiet`: passed; and
- repository diff, status, and stat checks were rerun after the final documentation update.

Both pytest runs emitted the known local `.pytest_cache` permission warning; it did not fail either test command.

### Unchanged Kafka blocker

Full collection discovered 139 tests and then stopped with three collection errors in:

- `tests/integration/test_kafka_end_to_end_flow.py`;
- `tests/unit/test_kafka_consumer.py`; and
- `tests/unit/test_kafka_producer.py`.

The exact remaining error is:

```text
ModuleNotFoundError: No module named 'kafka.vendor.six.moves'
```

The failure still originates from `kafka-python==2.0.2` importing `kafka.vendor.six.moves` under Python 3.12. No Kafka dependency, script, or test was changed.

### Residual limitations

- full pytest collection and full-suite execution are not healthy;
- CI configuration was updated but GitHub Actions was not run from this local batch;
- Docker Compose static validation does not prove image build or container startup;
- no live Kafka, OpenAI, Pinecone, PostgreSQL, Airflow, AWS, ERP/CRM, or network-backed test was run; and
- PostgreSQL initialization, deterministic forecast/RAG fixtures, and API readiness remain later Phase 1 work.

### Rollback instructions

Rollback must revert only the Batch 1A.1 implementation changes: restore the previous `requirements.txt`, LangGraph workflow import block, CI workflow, README runtime statement, and deleted `requirements_full.txt`; remove `tests/unit/test_runtime_dependency_contract.py`; and mark this result as reverted. Recreate a disposable environment from the restored manifests and rerun import and collection checks. Do not patch the active environment or Kafka vendored files as rollback.
