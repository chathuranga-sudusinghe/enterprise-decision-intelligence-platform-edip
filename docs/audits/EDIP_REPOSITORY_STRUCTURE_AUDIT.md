# EDIP Repository Structure and File Architecture Audit

- Audit date: 29 July 2026
- Audit mode: Read-only
- Repository: enterprise-decision-intelligence-platform-edip
- Branch audited: main
- Purpose: Repository structure, file ownership, duplication, dependency, and migration-risk assessment
- Result type: Audit evidence; not an implementation record

> This report records a read-only repository audit. No repository restructuring or implementation changes were performed as part of the audit.
This was a strictly read-only audit. No files were changed, no secrets were displayed, and no restructuring is recommended without repository evidence. The final recommendation prioritizes simplicity, maintainability, low coupling, and atomic migration.

## 1. Executive conclusion

The current structure is not fundamentally broken. It is best described as:

- A lightweight monorepo at repository level.
- A modular-monolith backend under `app/`.
- A separate frontend application under `ui/`.
- Offline data/ML pipelines and operational infrastructure in the same repository.

The problem is not the number of folders. It is inconsistent ownership inside several capabilities.

Key conclusions:

| Question | Conclusion |
|---|---|
| Is broad restructuring justified? | **No.** Targeted capability-oriented consolidation is justified. |
| Dedicated `app/rag/` package? | **Yes, now**, because online RAG already spans API, schemas, services, adapters, configuration, and tests. |
| Dedicated `app/workflows/` package? | **Yes, now or immediately after RAG**, because the current “agents” are workflow stages and graph ownership is misplaced. |
| Dedicated `app/forecasting/` package? | **Justified later**, after clean runtime/artifact behavior is established. |
| `src/` migration? | **No.** It solves no demonstrated problem and would disturb imports, scripts, Docker, Airflow, and tests. |
| Rename `app/` to `backend/`? | **No.** `app/` is clear and conventional. |
| Rename `ui/` to `frontend/`? | **No.** The name is adequate; reproducibility matters more than naming. |
| Microservices? | **Not justified.** |
| Preferred strategy | Incremental transition from horizontal layers toward a capability-oriented modular monolith. |

Recommended architecture:

- Retain `app/`, `ui/`, `pipelines/`, `scripts/`, `infra/`, `monitoring/`, `docs/`, and `tests/`.
- Consolidate online RAG into `app/rag/`.
- Consolidate orchestration and workflow stages into `app/workflows/`.
- Keep deterministic safety, approval, authorization, and audit controls separate from LLM-controlled logic.
- Keep offline RAG and forecasting pipelines outside the application runtime.
- Make ECS Fargate the canonical AWS deployment path.
- Keep Kubernetes explicitly optional.
- Do not create empty future capability folders until real implementation exists.

---

## 2. Audit method and limitations

Reconfirmed:

- Clean `main` aligned with `origin/main`.
- 217 tracked files.
- Top-level tracked distribution:

| Area | Tracked files |
|---|---:|
| `.github` | 9 |
| Root | 14 |
| `app` | 27 |
| `configs` | 4 |
| `data` | 1 |
| `database` | 23 |
| `docs` | 39 |
| `infra` | 30 |
| `monitoring` | 6 |
| `pipelines` | 8 |
| `scripts` | 16 |
| `tests` | 15 |
| `ui` | 25 |

Inspected:

- Python imports and imported-by relationships.
- FastAPI router registration.
- Workflow construction.
- RAG scripts and configuration paths.
- Forecast artifact paths.
- Docker, Compose, Airflow, Terraform, Kubernetes, CI, Kafka, monitoring, and frontend references.
- Ignored local artifacts and the nested `ui/.git`.
- Repeated filenames and actual content duplication.

Validation evidence from the immediately preceding read-only audit remains applicable:

- Focused Python unit tests: 32 passed.
- Full Python suite: blocked by 10 dependency-related collection errors.
- Frontend lint and current-checkout build: passed.
- AWS and local-k8s Terraform: format and validation passed.
- Docker Compose configuration: parsed successfully.

External services and clean-clone builds were not rerun for this structure-only pass. No package was installed.

---

## 3. Complete repository inventory

The following inventory groups are exhaustive across all 217 tracked files. Files are grouped only where ownership, use, status, and recommendation are the same.

### Root files

| Files | Purpose and evidence of use | Status | Decision |
|---|---|---|---|
| `.gitignore` | Controls all generated/local content; line 197 incorrectly ignores all `ui/` | **MISLEADING** | **COMPLETE IMPLEMENTATION** |
| `.dockerignore` | Defines API image build context; excludes data and artifacts | **ACTIVE** but deployment-sensitive | **KEEP AND DOCUMENT** |
| `Dockerfile` | Builds FastAPI image and runs `app.main:app` | **ACTIVE** | **KEEP** |
| `docker-compose.yml` | Local API, Kafka, Airflow, Postgres, Prometheus, Grafana | **ACTIVE** but development-oriented | **KEEP AND DOCUMENT** |
| `requirements.txt` | API runtime dependencies | **PARTIALLY USED**; misses LangGraph | **COMPLETE IMPLEMENTATION** |
| `requirements-dev.txt` | Test/lint dependencies | **ACTIVE** | **KEEP** |
| `requirements_full.txt` | Large local environment freeze | **STALE** as a deployable dependency source | **ARCHIVE** or redefine |
| `pytest.ini` | Pytest discovery/configuration | **ACTIVE** | **KEEP** |
| `README.md` | Main repository documentation | **ACTIVE** but overstated/stale in places | **KEEP AND DOCUMENT** |
| `AI_USAGE.md` | AI-use disclosure | **ACTIVE** | **KEEP** |
| `CONTRIBUTING.md` | Contribution workflow | **ACTIVE** | **KEEP** |
| `CODE_OF_CONDUCT.md` | Community conduct policy | **ACTIVE** | **KEEP** |
| `LICENSE` | MIT license | **ACTIVE** | **KEEP** |
| root `__init__.py` | Makes repository root importable as a package, but no import depends on it | **UNUSED** | **REMOVE** after import check |

### GitHub files

All issue templates and the PR template have clear repository-governance ownership.

| Files | Status | Decision |
|---|---|---|
| `.github/ISSUE_TEMPLATE/{bug_report,documentation,feature_request,good_first_issue}.md` | **ACTIVE** | **KEEP** |
| `.github/ISSUE_TEMPLATE/config.yml` | **ACTIVE** | **KEEP** |
| `.github/PULL_REQUEST_TEMPLATE.md` | **ACTIVE** | **KEEP** |
| `.github/workflows/integration-ci.yml` | **ACTIVE**, but tests do not exercise all advertised integrations | **KEEP AND DOCUMENT** |
| `.github/workflows/docker-ci.yml` | **ACTIVE**, build-only validation | **KEEP AND DOCUMENT** |
| `.github/workflows/terraform-ci.yml` | **ACTIVE**, duplicated dummy configuration values | **KEEP AND DOCUMENT** |

### Backend application

#### Core

| Files | Purpose/use | Status | Decision |
|---|---|---|---|
| `app/main.py` | FastAPI construction, router registration, CORS, metrics | **ACTIVE** | **KEEP** |
| `app/core/config.py` | Application settings; imported by `main.py` | **ACTIVE** | **KEEP**, expand as canonical runtime configuration |
| `app/core/logging.py` | Logging used by agents, pipelines, and Kafka scripts | **ACTIVE** | **KEEP** |
| `app/core/monitoring.py` | Actual Prometheus metric definitions and helpers | **ACTIVE** | **KEEP** as canonical metric owner |
| `app/core/metrics.py` | Defines the same metric names as `monitoring.py`; not imported | **DUPLICATED RESPONSIBILITY** | **REMOVE** after verification |
| package `__init__.py` files | Python package markers | **ACTIVE** or harmless | **KEEP** |

#### RAG

| Current file | Purpose/imported by | Status | Decision |
|---|---|---|---|
| `app/api/rag.py` | `/rag` routes; registered by `app.main` | **ACTIVE BUT MISPLACED** | **MOVE** to `app/rag/api.py` |
| `app/schemas/rag.py` | RAG Pydantic contracts | **ACTIVE BUT MISPLACED** | **MOVE** to `app/rag/schemas.py` |
| `app/services/rag_query_service.py` | Embedding, Pinecone query, context, citations/source shaping, orchestration | **ACTIVE BUT MISPLACED** and over-broad | **SPLIT** within `app/rag/` |
| `app/services/rag_generation_service.py` | Prompt construction and OpenAI generation | **ACTIVE BUT MISPLACED** | **MOVE** to `app/rag/generator.py` |
| `app/agents/retrieval_agent.py` | Workflow adapter around RAG | **ACTIVE BUT MISPLACED** | **MOVE** to workflow package, not RAG ownership |

#### Workflow stages

| Current files | Purpose/use | Status | Decision |
|---|---|---|---|
| `app/agents/planner_agent.py` | Rule-based request classification | **ACTIVE BUT MISPLACED** | **MOVE** to `app/workflows/planner.py` |
| `app/agents/reasoning_agent.py` | Deterministic evidence/signal reasoning | **ACTIVE BUT MISPLACED** | **MOVE** to `app/workflows/reasoning.py` |
| `app/agents/analytics_agent.py` | Forecast service adapter | **ACTIVE BUT MISPLACED** | **MOVE** to `app/workflows/analytics_stage.py` |
| `app/agents/execution_agent.py` | Final response/action packaging | **ACTIVE BUT MISPLACED** | **MOVE** to `app/workflows/execution.py` |
| `app/agents/langgraph_workflow.py` | State, graph construction, nodes, routing | **ACTIVE BUT MISPLACED** and over-broad | **SPLIT** into graph/state/routing |
| `app/services/agent_workflow_service.py` | Workflow facade and response shaping | **ACTIVE BUT MISPLACED** | **MOVE** to `app/workflows/service.py` |
| `app/api/agent_workflow.py` | Workflow API, schemas, RAG adapter, dependency construction | **ACTIVE BUT MISPLACED** and over-broad | **SPLIT** into workflow API/schemas/adapters |

#### Forecasting and events

| Files | Purpose/use | Status | Decision |
|---|---|---|---|
| `app/api/forecast.py` | Forecast routes | **ACTIVE** | **KEEP initially**; later move to `app/forecasting/api.py` |
| `app/services/forecast_service.py` | Artifact loading and serving | **ACTIVE**, but combines several responsibilities | **KEEP initially**, later **SPLIT** |
| `app/services/event_processing_service.py` | Kafka event-to-decision mapping | **ACTIVE** | Later **MOVE** to `app/events/service.py` |
| `app/services/app/services` | Empty anomalous file | **EMPTY** and **MISLEADING** | **REMOVE** |
| other application `__init__.py` files | Package markers | **ACTIVE** | **KEEP** until their packages are migrated |

### Configuration

| File | Ownership | Status | Decision |
|---|---|---|---|
| `configs/kafka_event_schema.yaml` | Event-envelope contract | **ACTIVE** | **KEEP**, later move to `configs/events/` |
| `configs/rag_ingestion_config.yaml` | Offline RAG ingestion configuration | **ACTIVE**, but paths drift from scripts | **KEEP**, later move to `configs/rag/ingestion.yaml` |
| `configs/rag_metadata_schema.yaml` | RAG document metadata contract | **ACTIVE** | **KEEP**, later move to `configs/rag/metadata_schema.yaml` |
| `configs/.gitkeep` | No longer needed in non-empty folder | **STALE** | **REMOVE** |

### Database

| Files | Status | Decision |
|---|---|---|
| `database/ddl/01_create_schemas.sql` | **EMPTY**, later DDL depends on it | **COMPLETE IMPLEMENTATION** |
| `database/ddl/02_extensions.sql` | **EMPTY** | **COMPLETE IMPLEMENTATION** or **REMOVE** if no extension is required |
| `database/ddl/03_…08_*.sql` | Substantive dimensional/fact schemas | **ACTIVE**, not runtime-integrated | **KEEP AND DOCUMENT** |
| `database/dml/01_…12_*.sql` | Synthetic-data loading and validation | **ACTIVE**, working-directory dependent | **KEEP AND DOCUMENT** |
| `database/migrations/.gitkeep` | Valid placeholder only if migrations are planned | **PARTIALLY USED** | **KEEP AND DOCUMENT** or remove directory |
| `database/seeds/.gitkeep` | Valid placeholder only if seed ownership is defined | **PARTIALLY USED** | **KEEP AND DOCUMENT** |
| `database/.gitkeep` | Redundant because directory is populated | **STALE** | **REMOVE** |

### Documentation and RAG corpus

Tracked documentation consists of:

- 5 files under `docs/policies/`
- 27 operational guides under `docs/rag_source/`
- 3 files under `docs/reviews/`
- `docs/sops/warehouse_receiving_sop.md`
- `docs/phase_5_rag_knowledge_scope.md`
- `docs/.gitkeep`

All business policy, review, SOP, and guide files are included as RAG source directories by [rag_ingestion_config.yaml](D:/my_AI_projects/enterprise_decision_intelligence_platform_EDIP/configs/rag_ingestion_config.yaml:47).

| Files | Status | Decision |
|---|---|---|
| `docs/policies/*.md` | **ACTIVE**, RAG corpus | **KEEP**, later group under `docs/knowledge/policies/` |
| `docs/sops/*.md` | **ACTIVE**, RAG corpus | **KEEP**, later group under `docs/knowledge/sops/` |
| `docs/reviews/*.md` | **ACTIVE**, RAG corpus | **KEEP**, later group under `docs/knowledge/reviews/` |
| `docs/rag_source/*.md` | **PARTIALLY USED**; many frontmatter errors | **KEEP**, validate, later rename folder to `docs/knowledge/guides/` |
| `docs/phase_5_rag_knowledge_scope.md` | Engineering/RAG scope documentation | **ACTIVE BUT MISPLACED** | **MOVE** later to `docs/architecture/` or `docs/rag/` |
| `docs/.gitkeep` | Redundant | **STALE** | **REMOVE** |

### Infrastructure

| Files | Ownership/status | Decision |
|---|---|---|
| `infra/terraform/aws/*.tf` and `terraform.tfvars` | Canonical planned AWS ECS path; static validation passes | **KEEP AND DOCUMENT** |
| `infra/terraform/local-k8s/*.tf` and `terraform.tfvars` | Local Kubernetes learning/development path | **CONFIGURATION ONLY** | **KEEP**, explicitly mark optional |
| `infra/k8s/*.yaml` | Raw K8s deployment and monitoring definitions | **CONFIGURATION ONLY**, overlaps local-k8s Terraform | **ARCHIVE** or mark optional after comparison |
| `infra/.gitkeep` | Redundant | **STALE** | **REMOVE** |

Root `Dockerfile` and `docker-compose.yml` should remain at root because they describe repository-wide default development/build behavior.

### Monitoring

| Files | Status | Decision |
|---|---|---|
| `monitoring/prometheus/prometheus.yml` | Canonical Prometheus source configuration | **ACTIVE** | **KEEP** |
| `monitoring/grafana/dashboards/edip-overview.json` | Canonical dashboard | **ACTIVE** | **KEEP** |
| provisioning datasource/dashboard/alert YAML files | Canonical Grafana provisioning | **ACTIVE** | **KEEP** |
| `monitoring/.gitkeep` | Redundant | **STALE** | **REMOVE** |

### Pipelines

| Files | Purpose/status | Decision |
|---|---|---|
| `pipelines/etl/build_training_dataset.py` | Forecast training dataset | **ACTIVE** | Later **MOVE** to `pipelines/forecasting/dataset.py` |
| `pipelines/features/demand_features.py` | Feature engineering | **ACTIVE** | Later **MOVE** to `pipelines/forecasting/features.py` |
| `pipelines/training/train_demand_forecast.py` | Training | **ACTIVE** | Later **MOVE** to `pipelines/forecasting/train.py` |
| `pipelines/training/evaluate_demand_forecast.py` | Evaluation | **ACTIVE**, holdout ownership weak | Later **MOVE** to `pipelines/forecasting/evaluate.py` |
| `pipelines/inference/score_demand_forecast.py` | Batch scoring | **ACTIVE** | Later **MOVE** to `pipelines/forecasting/score.py` |
| `pipelines/inference/generate_recommendations.py` | Deterministic recommendation generation | **ACTIVE** | Later **MOVE** to `pipelines/forecasting/recommend.py` |
| `pipelines/airflow_dags/edip_orchestration_demo_dag.py` | Manual demo DAG | **CONFIGURATION ONLY** | **KEEP AND DOCUMENT** |
| `pipelines/.gitkeep` | Redundant | **STALE** | **REMOVE** |

### Scripts

| Files | Ownership/status | Decision |
|---|---|---|
| `generate_phase_1_…phase_4_*.py` | Synthetic data generation | **ACTIVE** operator scripts | **KEEP** |
| `generate_phase_6_kafka_events.py` | Event export generation | **ACTIVE** | **KEEP** |
| `init_kafka_topics.py`, `kafka_producer.py`, `kafka_consumer.py` | Kafka operator/runtime adapters | **ACTIVE** | **KEEP**, later move reusable logic to `app/events/` |
| `build_rag_metadata.py`, `chunk_rag_documents.py`, `embed_rag_chunks.py`, `load_rag_to_pinecone.py` | Offline RAG pipeline implementations | **ACTIVE BUT MISPLACED** as substantial modules | Move reusable logic to `pipelines/rag/`; retain thin CLI wrappers |
| `run_agent_workflow_demo.py` | Workflow demonstration | **ACTIVE** | **KEEP AND DOCUMENT** |
| `scripts/__init__.py` | Allows tests/imports | **ACTIVE** | **KEEP** |

### Tests

| Files | Status | Decision |
|---|---|---|
| `tests/unit/test_forecast_service.py` | **ACTIVE**, verified | **KEEP**; update imports after forecasting move |
| `tests/unit/test_event_processing_service.py` | **ACTIVE**, verified | **KEEP** |
| RAG service unit tests | **ACTIVE**, fake-client based | **KEEP**; move beside new RAG package ownership |
| Kafka producer/consumer tests | **ACTIVE**, fake transport | **KEEP**, accurately label as unit tests |
| Forecast/RAG/workflow API tests | **ACTIVE**, dependency-overridden | **KEEP** as in-process API integration tests |
| `test_kafka_end_to_end_flow.py` | Uses fake Kafka objects | **MISLEADING** | **RENAME** to reflect simulated event flow |
| `test_kafka_event_generation.py` | Generated-artifact integration | **ACTIVE** | **KEEP** |
| `test_rag_retrieval.py` | CLI-style live evaluator with zero pytest tests | **ACTIVE BUT MISPLACED** | **MOVE** to evaluation/operator location or convert to pytest |
| test `__init__.py` files | Package markers | **KEEP** |
| `tests/.gitkeep` | Redundant | **REMOVE** |

### Frontend

All 25 tracked UI files have valid frontend ownership, but root `.gitignore` makes future additions unsafe.

| Files | Status | Decision |
|---|---|---|
| `ui/package.json`, lockfile, TS/Next/PostCSS/ESLint configs | **ACTIVE** | **KEEP** |
| `ui/src/app/{layout,page,chat/page,globals.css}` | **ACTIVE** | **KEEP** |
| `ui/src/components/ui/*.tsx` | **ACTIVE** UI primitives | **KEEP** |
| `ui/public/*.svg`, favicon | Mostly create-next-app assets | **PARTIALLY USED** or **STALE** | Verify use; remove only when confirmed |
| `ui/README.md` | Generic Next.js documentation | **STALE** | **RENAME/REWRITE** later |
| `ui/.gitignore` | Valid frontend-local ignore rules | **ACTIVE** | **KEEP** |
| ignored `ui/src/lib/utils.ts` | Required by tracked imports | **LOCAL ONLY**, causes clean-clone failure | **KEEP** by tracking it |
| nested `ui/.git/` | Independent stale repository metadata | **LOCAL ONLY** and **MISLEADING** | Review then remove locally |

---

## 4. Folder ownership assessment

| Folder | Ownership | Overlap/problem | Recommendation |
|---|---|---|---|
| `app/` | Online backend runtime | Correct | Keep |
| `app/api/` | Horizontal transport layer | Fragments established capabilities | Gradually replace with capability-owned APIs |
| `app/schemas/` | Horizontal Pydantic schemas | Only contains RAG while workflow schemas are embedded elsewhere | Migrate schemas into feature packages |
| `app/services/` | General application services | Becoming a dumping ground | Migrate RAG/workflow; keep only during transition |
| `app/agents/` | Claimed agents | Actually deterministic workflow stages plus graph | Replace with `app/workflows/` |
| `configs/` | Offline/event configuration | Flat but only three substantive files | Add `rag/` and `events/` only during matching migrations |
| `data/` | Generated/source datasets | Correct conceptually | Keep with explicit contract |
| `artifacts/` | Models, outputs, reports | Correct conceptually but runtime coupling is undocumented | Keep local convention; back with immutable storage |
| `database/` | Warehouse schema/load assets | Not integrated with runtime | Keep and document as batch/data subsystem |
| `docs/` | Engineering docs and RAG corpus | Business corpus and engineering evidence are mixed | Introduce `docs/knowledge/` and evidence categories incrementally |
| `infra/` | Deployment definitions | ECS and two K8s approaches overlap | Make AWS/ECS canonical; K8s optional |
| `monitoring/` | Monitoring source assets | Correct; duplicated downstream | Keep as canonical source |
| `pipelines/` | Offline ML/data work | Generic stage folders contain only forecasting code | Later consolidate under `pipelines/forecasting/` |
| `scripts/` | Operator commands | Some scripts contain reusable pipeline modules | Retain CLIs; migrate reusable RAG logic |
| `tests/` | Automated checks/evaluations | Some integration/e2e labels are misleading | Refine categories |
| `ui/` | Frontend application | Entire path ignored; nested Git | Keep name, repair tracking |
| `tmp/` | Local scratch | Empty and ignored | Ignore; remove locally when unused |

---

## 5. Genuine duplication findings

### 5.1 Prometheus metric definitions

- [app/core/metrics.py](D:/my_AI_projects/enterprise_decision_intelligence_platform_EDIP/app/core/metrics.py:9)
- [app/core/monitoring.py](D:/my_AI_projects/enterprise_decision_intelligence_platform_EDIP/app/core/monitoring.py:20)

Both define identical metric names such as:

- `edip_http_requests_total`
- `edip_http_request_duration_seconds`
- `edip_http_requests_in_progress`
- `edip_workflow_runs_total`
- `edip_rag_requests_total`
- `edip_forecast_requests_total`

Canonical owner: `app/core/monitoring.py`, because it is imported by the application and includes recording helpers.

Recommendation: **MERGE/REMOVE `metrics.py`**. Migration risk: low, provided an import search remains empty.

### 5.2 Grafana dashboard duplication

These files have the exact same SHA-256:

- `monitoring/grafana/dashboards/edip-overview.json`
- `infra/k8s/grafana-dashboard-json-configmap.yaml`

The latter is named YAML but is byte-identical JSON, not a ConfigMap wrapper.

Canonical owner: `monitoring/grafana/dashboards/edip-overview.json`.

Recommendation: K8s should mount, package, or generate a ConfigMap from the canonical dashboard. Do not maintain two copies.

### 5.3 Alert and Prometheus configuration duplication

Equivalent definitions appear in:

- `monitoring/grafana/provisioning/alerting/edip-alert-rules.yml`
- `infra/k8s/grafana-alerting-configmap.yaml`
- `infra/terraform/local-k8s/grafana.tf`
- `monitoring/prometheus/prometheus.yml`
- `infra/k8s/prometheus-configmap.yaml`
- `infra/terraform/local-k8s/prometheus.tf`

Canonical owner: `monitoring/`.

Recommendation: deployment tooling should package the canonical files instead of embedding copies. Migration risk: medium because Terraform and K8s rendering must be validated.

### 5.4 Kubernetes deployment ownership

Both raw manifests and Terraform define API, Prometheus, Grafana, namespace, services, probes, and resources.

- `infra/k8s/`
- `infra/terraform/local-k8s/`

This is genuine duplicate deployment responsibility.

Recommendation: retain one optional local-k8s approach. Terraform is more consistent with the AWS IaC direction; raw YAML can become reference material or be archived.

### 5.5 RAG path/configuration ownership

Configuration declares:

- `rag_chunks.jsonl`
- `rag_embeddings.jsonl`
- `rag_embeddings.parquet`

Scripts actually use:

- `document_chunks.jsonl`
- `chunk_embeddings.jsonl`
- `chunk_embeddings.csv`

This is not benign repetition; it is conflicting ownership.

Canonical owner: `configs/rag/ingestion.yaml`, consumed consistently by every offline stage.

### 5.6 RAG endpoint and workflow adapter behavior

`RagRetrievalAdapter` in `app/api/agent_workflow.py` performs interface translation that belongs beside workflow construction, not HTTP transport. It also falls back to `answer_question()`, duplicating retrieval plus unnecessary generation.

Recommendation: implement a retrieval-only application interface owned by `app/rag/retriever.py`; keep the workflow adapter in `app/workflows/adapters.py`.

---

## 6. Valid repeated filenames

The following repetitions are not inherently duplicates:

- `__init__.py`: valid package markers under `app/`, `scripts/`, and `tests/`.
- `README.md`: root project documentation and frontend-specific documentation have different intended scopes.
- `.gitkeep`: valid only for intentionally empty, tracked directories such as a planned migrations or seeds directory.
- `terraform.tfvars`: AWS and local-k8s values target different environments.
- `requirements.txt` and `requirements-dev.txt`: valid runtime/development separation.

Problematic instances:

- Root `__init__.py` has no demonstrated need.
- `.gitkeep` files in populated folders are stale.
- `ui/README.md` has valid ownership but stale generic content.
- `requirements_full.txt` lacks a clearly defined reproducibility role.

---

## 7. Empty, stale, generated and misleading paths

### Empty tracked paths

- `app/services/app/services`: remove.
- `database/ddl/01_create_schemas.sql`: complete.
- `database/ddl/02_extensions.sql`: complete or remove.
- Root `__init__.py`: likely remove.
- Redundant `.gitkeep` files in populated folders: remove.

### Valid empty placeholders

Only retain when the roadmap assigns ownership:

- `database/migrations/.gitkeep`
- `database/seeds/.gitkeep`
- `data/synthetic/.gitkeep`, because generated CSVs are ignored

### Local-only/generated content

Must remain ignored:

- `.venv/`, `__pycache__/`, `.pytest_cache/`, `.coverage`
- `ui/node_modules/`, `ui/.next/`, `ui/next-env.d.ts`
- `.terraform/`, state, lock files if deliberately regenerated
- generated datasets and artifacts
- local logs and `tmp/`

### Local content needing action

| Path | Issue | Recommendation |
|---|---|---|
| `ui/src/lib/utils.ts` | Required runtime source but ignored | Track it |
| `ui/.git/` | Stale nested repository | Verify no unique history, then remove locally |
| `.git/refs/codex/...` | Broken internal ref reported by Git | Repair separately after backup |
| ignored model/RAG/forecast artifacts | Required by current local runtime | Add manifests and external delivery contract |
| empty `data/raw/`, `infra/docker/`, `monitoring/logs/` | No current content or clear ownership | Remove locally or document before retaining |

---

## 8. RAG structure assessment

A dedicated online `app/rag/` package is justified now.

### Recommended initial package

```text
app/rag/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── retriever.py
├── generator.py
├── vector_store.py
└── exceptions.py
```

### Responsibility mapping

| Proposed file | Existing responsibility | Current source | Create now? | Risk |
|---|---|---|---|---|
| `api.py` | FastAPI routes and dependency entry point | `app/api/rag.py` | Yes | Low |
| `schemas.py` | RAG request/response models | `app/schemas/rag.py` | Yes | Low |
| `service.py` | Coordinates retrieve → context → generate → response | `rag_query_service.py` | Yes | Medium |
| `retriever.py` | Embedding, thresholding, source shaping, retrieval-only interface | `rag_query_service.py` | Yes | Medium |
| `generator.py` | Prompt and OpenAI response handling | `rag_generation_service.py` | Yes | Low |
| `vector_store.py` | Pinecone adapter/protocol | `rag_query_service.py` | Yes | Medium |
| `exceptions.py` | Stable domain exceptions | Currently generic exceptions | Yes only if API mapping is introduced | Low |
| `citations.py` | Dedicated citation validation | Only basic source shaping exists | Later | Low |
| `evidence_quality.py` | Quality/authority/conflict logic | Not implemented | Later; do not scaffold now | Medium |
| `access_control.py` | Document ACL enforcement | Not implemented | Later with authentication | High |
| `prompt_security.py` | Injection controls | Not implemented | Later with tests | Medium |
| `evaluation.py` | Runtime evaluation abstraction | Existing evaluator is an operator script | Not in online package now | Medium |

Correct relationships:

- `app/rag/` owns online retrieval and generation.
- `app/workflows/retrieval_stage.py` adapts RAG output into workflow state.
- Pinecone is an infrastructure adapter behind a retrieval protocol.
- The retrieval agent/stage must not own RAG logic.
- Offline ingestion belongs under `pipelines/rag/`.
- Live evaluation belongs under `tests/e2e/rag/` or a dedicated operator command.
- LangSmith tracing should later wrap RAG/workflow operations through observability adapters, not become core retrieval logic.

### Offline RAG target

```text
pipelines/rag/
├── metadata.py
├── chunking.py
├── embeddings.py
└── index.py

scripts/
├── build_rag_metadata.py
├── chunk_rag_documents.py
├── embed_rag_chunks.py
└── load_rag_to_pinecone.py
```

Scripts should become thin CLI wrappers. This move should occur after online RAG consolidation, not in the same commit.

---

## 9. Agent and workflow structure assessment

The classes are workflow stages, not autonomous agents:

- Planner: deterministic substring routing.
- Retrieval: service adapter.
- Reasoning: deterministic heuristics/templates.
- Analytics: forecast-service adapter.
- Execution: result packaging, not external execution.

A dedicated workflow package is justified:

```text
app/workflows/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── graph.py
├── state.py
├── routing.py
├── adapters.py
├── planner.py
├── retrieval_stage.py
├── reasoning.py
├── analytics_stage.py
└── execution.py
```

Ownership:

- `graph.py`: node registration and edges.
- `state.py`: `WorkflowState` and serialization.
- `routing.py`: deterministic routing and safety-transition functions.
- `adapters.py`: RAG and forecast protocol adapters.
- Stage files: one bounded stage responsibility each.
- `service.py`: invoke graph and shape application result.
- `api.py`: transport only.
- `schemas.py`: API request/response models.

Future capabilities:

- Uncertainty and abstention belong in deterministic state/routing/safety code.
- Approvals should later be a separate `app/approvals/` capability with persistence and authorization.
- Retries/timeouts/failure states belong in graph/state/routing, not individual prompt code.
- MCP tool bindings should later live under `app/integrations/mcp/` or a similarly concrete integration package.
- LangSmith tracing should be an observability adapter around graph/stages.

Do not create `approvals/`, `integrations/`, or `audit/` until the first real implementation file exists.

---

## 10. Forecasting and analytics structure assessment

Current separation between online serving and offline pipelines is conceptually correct:

- Online: `app/api/forecast.py`, `app/services/forecast_service.py`
- Offline: `pipelines/`
- Generated: `artifacts/`

A dedicated `app/forecasting/` package is justified eventually, but it is not the first structural change.

Recommended online target:

```text
app/forecasting/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── artifacts.py
└── rules.py
```

Responsibilities:

- `api.py`: HTTP routes.
- `schemas.py`: stable API contracts.
- `service.py`: request use cases.
- `artifacts.py`: versioned artifact loading and readiness.
- `rules.py`: deterministic replenishment and safety rules.

Offline target:

```text
pipelines/forecasting/
├── dataset.py
├── features.py
├── train.py
├── evaluate.py
├── score.py
└── recommend.py
```

Keep separate:

- Online serving
- Offline model training
- Evaluation
- Artifact loading
- Deterministic business rules

Do not move forecasting until artifact delivery and clean-runtime behavior are specified. Otherwise the move would only rearrange the same hidden coupling.

---

## 11. Data and artifact boundary

| Category | Purpose | Git | S3/object storage | Versioning and evidence | May runtime require local presence? |
|---|---|---|---|---|---|
| `data/raw/` | Immutable source extracts | Ignore | Required for real data | Source URI, timestamp, license, schema, checksum | No |
| `data/synthetic/` | Generated development data | Ignore full datasets; generators tracked | Optional for large evidence | Generator version, seed, row counts, checksum | Only local dev |
| `data/processed/` | Derived training/RAG datasets | Ignore | Required for repeatable training | Parent manifest, transform version, schema, checksum | No online dependency |
| `data/exports/` | Kafka/replay/export payloads | Ignore | Optional with retention policy | Event schema, generation time, checksum | No |
| `artifacts/models/` | Trained model packages | Ignore binaries | Required | Immutable model ID, code/data versions, metrics, checksum | Yes, after controlled download |
| `artifacts/forecasts/` | Scored outputs/recommendations | Ignore bulk outputs | Required for artifact-serving mode | Model ID, input dataset ID, timestamp, checksum | Yes, but never implicitly |
| `artifacts/reports/` | Generated evaluations/manifests | Ignore raw generated reports | Required for audit archive | Provenance and checksum | No |
| `docs/evidence/` | Reviewed human-readable evidence | Track selected summaries | Optional archive | Links to immutable source artifacts | No |

Every generated dataset/artifact family should have:

- Immutable ID
- Creation timestamp
- Producer command/code revision
- Input artifact IDs
- Schema version
- SHA-256
- Row/file counts
- Environment/runtime version
- Validation result

The API must not silently depend on whatever happens to exist in local ignored folders.

---

## 12. Configuration ownership

### Canonical sources

| Configuration type | Canonical owner |
|---|---|
| Runtime application settings | `app/core/config.py` populated from environment |
| Secrets | Runtime secret store; `.env` only for local development |
| Offline RAG ingestion | `configs/rag/ingestion.yaml` |
| RAG metadata contract | `configs/rag/metadata_schema.yaml` |
| Event schema | `configs/events/kafka_event_schema.yaml` |
| Frontend API URL | `NEXT_PUBLIC_API_BASE_URL` |
| AWS resource configuration | Terraform variables |
| Local service topology | Docker Compose |
| Monitoring content | `monitoring/` |
| CI-only test values | Workflow `env`, clearly non-production |

### Confirmed conflicts

- RAG config uses `edip-rag-phase6` / `northstar-retail-v1`.
- Application, scripts, tests, and Terraform use `edip-rag-index` / `edip-phase-6`.
- RAG configured output filenames differ from script defaults.
- `rag_query_service.py` reads environment variables directly instead of relying on `Settings`.
- Kafka defaults differ between container (`kafka:29092`) and host scripts (`localhost:9092`), which is valid only if explicitly documented by environment.
- Image tags use mutable `latest` in multiple locations.
- Grafana/Prometheus image versions are repeated across Compose, Terraform, and raw manifests.
- CI duplicates many runtime defaults already represented in application/Terraform configuration.

Recommended `configs/` structure:

```text
configs/
├── rag/
│   ├── ingestion.yaml
│   └── metadata_schema.yaml
└── events/
    └── kafka_event_schema.yaml
```

`configs/application/` is not justified. Application configuration belongs in typed runtime settings.

---

## 13. Test structure assessment

Recommended structure when real coverage exists:

```text
tests/
├── unit/
├── integration/
├── e2e/
├── reliability/
├── security/
└── fixtures/
```

Do not create empty `e2e`, `reliability`, or `security` directories before adding the first test.

Findings:

- Unit tests are generally correctly categorized.
- API tests with dependency overrides are valid in-process integration tests, but they do not verify external integrations.
- `test_kafka_end_to_end_flow.py` is not end-to-end because it uses fake messages and consumers.
- `test_rag_retrieval.py` is a CLI evaluator masquerading as a pytest module; it contains zero pytest tests.
- No package-level tests cover planner, reasoning, execution, graph routing, or workflow state.
- No frontend tests exist.
- Similar fake service/client definitions are repeated across test files; a `tests/fixtures/` package becomes justified once two or more packages share the same stable fake.
- Avoid a generic fixture dumping ground: organize fixtures by capability, such as `fixtures/rag.py` and `fixtures/workflows.py`.

Recommended categorization:

- Fake-only Kafka flow → `tests/integration/test_event_flow.py`
- Live Pinecone/OpenAI retrieval → `tests/e2e/rag/test_live_retrieval.py`
- Standalone retrieval reporting command → `scripts/evaluate_rag_retrieval.py`
- Workflow failure/retry/abstention → `tests/reliability/workflows/`
- Auth, ACL, prompt injection → `tests/security/`

---

## 14. Infrastructure and monitoring structure

Canonical deployment direction: AWS ECS Fargate.

Recommended classification:

| Area | Role |
|---|---|
| Root `Dockerfile` | Canonical API image |
| Root `docker-compose.yml` | Local development/integration topology |
| `infra/terraform/aws/` | Canonical AWS deployment |
| `infra/terraform/local-k8s/` | Optional learning/local alternative |
| `infra/k8s/` | Duplicate reference implementation; archive or explicitly deprecate |
| `monitoring/` | Canonical monitoring source assets |
| `.github/workflows/` | CI validation only, not deployment |

Docker files should remain at root because that is the most discoverable conventional location.

Monitoring should remain separate from `infra/`:

- `monitoring/` owns what to monitor and dashboard.
- `infra/` owns how those assets are deployed.

Deployment code should package monitoring assets from `monitoring/`, not copy their content.

Kubernetes should not move into the primary target architecture. If retained:

```text
infra/optional/k8s/
```

That move is optional and documentation-driven; it should not precede application stabilization.

---

## 15. Documentation and CITP evidence structure

Recommended eventual structure:

```text
docs/
├── architecture/
├── decisions/
├── operations/
├── security/
├── testing/
├── research/
├── citp/
├── stakeholder/
├── evidence/
└── knowledge/
    ├── policies/
    ├── sops/
    ├── reviews/
    └── guides/
```

Purpose:

- `architecture/`: current system design and boundaries.
- `decisions/`: ADRs and alternatives.
- `operations/`: deployment, rollback, incident, and recovery runbooks.
- `security/`: threat models, privacy, access-control design.
- `testing/`: test strategy and evaluation methodology.
- `research/`: hypotheses, experiment protocols, results.
- `citp/`: evidence index, reflection, responsibility, outcomes.
- `stakeholder/`: requirements, reviews, decisions, feedback.
- `evidence/`: reviewed summaries pointing to immutable generated evidence.
- `knowledge/`: only RAG-ingested company/business material.

Do not create all directories immediately. Create each with its first real document.

The current RAG corpus should eventually move as follows:

- `docs/policies` → `docs/knowledge/policies`
- `docs/sops` → `docs/knowledge/sops`
- `docs/reviews` → `docs/knowledge/reviews`
- `docs/rag_source` → `docs/knowledge/guides`

That move affects RAG ingestion configuration, processed manifests, Pinecone source metadata, citations, and retrieval tests. It should therefore be its own migration batch.

---

## 16. Path dependency matrix

| Proposed change | Python imports | FastAPI | Workflow | Tests | Docker/Compose | CI | Terraform/K8s | Airflow/Kafka | Frontend | Docs/scripts/artifacts |
|---|---|---|---|---|---|---|---|---|---|---|
| Track `ui/src/lib/utils.ts`; stop ignoring `ui/` | None | None | None | Add clean-clone build check | Docker API unaffected | Frontend CI should be added | None | None | Critical | Update contributor docs |
| Remove `app/core/metrics.py` | Confirm no imports | None | None | Import smoke test | None | Python tests | Dashboard names unchanged | None | None | None |
| RAG API/schema move | Update imports | Update `app.main` router import | Adapter imports | RAG API/unit monkeypatch paths | API image paths internal | Python CI | Env names unchanged | Demo script | API URL unchanged | Docs/import examples |
| Split RAG service | Multiple internal imports | Dependency builder | Retrieval adapter | RAG unit/integration tests | Runtime dependency behavior | Python CI | Pinecone configuration | Demo script | Response contract must remain | Generated metadata/source paths unchanged |
| Move RAG offline code | Script imports/entry points | None | None | Evaluator imports | Compose-mounted repo paths | Add pipeline checks | None | None | None | Config/default paths and operator commands |
| Move workflow package | All `app.agents` imports | `app.main` and workflow API | Entire graph construction | Workflow/API tests | Uvicorn entry unchanged | Python CI | None | Demo script | Contract unchanged | README diagrams |
| Forecast package move | Forecast imports | Router import | Analytics adapter | Forecast tests | Artifact paths must remain stable | Python CI | ECS env unchanged | Airflow script paths if offline files move | Contract unchanged | Docs and artifact manifests |
| Move forecast pipelines | Module/script paths | None | Artifact consumers | Pipeline tests | Airflow DAG paths change | Pipeline CI | None | Airflow commands change | None | Runbooks/manifests |
| Move RAG corpus | No runtime import | None | Source metadata/citations | Retrieval fixtures | Data excluded from image | Evaluation CI | None | Ingestion commands | Citation paths may display | Config source dirs, Pinecone reindex, manifests |
| Canonicalize monitoring | Monitoring imports unchanged | Metrics names unchanged | None | Metrics smoke tests | Compose volume paths | Config validation | Terraform/K8s packaging | None | None | Dashboard/alert docs |
| Archive raw K8s | None | None | None | None | None | Terraform path filters may change | Direct impact | None | None | Deployment docs |
| Complete DB initialization | None currently | None | Audit persistence later | PostgreSQL tests | Compose Postgres | Add DB CI | Future AWS DB | DML execution | None | Runbooks |

---

## 17. Structure options

### Option A — Minimal targeted cleanup

```text
app/
├── agents/
├── api/
├── core/
├── schemas/
└── services/
```

Changes only:

- Repair UI tracking.
- Remove stale files.
- Consolidate monitoring.
- Fix configuration drift.
- Document folder ownership.

Benefits:

- Lowest migration risk.
- Fastest stabilization.
- Preserves every current import.

Weaknesses:

- RAG remains fragmented.
- Workflow stages remain mislabeled.
- Future approvals/evidence controls would increase horizontal scattering.

Effort: low.

Suitability: good short-term cleanup, insufficient as final 2026 architecture.

CITP value: moderate; shows risk control but limited architectural evolution.

### Option B — Capability-oriented modular monolith

```text
app/
├── core/
├── rag/
├── workflows/
├── forecasting/
└── events/
```

Retains `ui/`, `pipelines/`, `scripts/`, `infra/`, `monitoring/`, and `docs/`.

Benefits:

- Clear capability ownership.
- RAG and workflow fragmentation reduced.
- Deterministic workflow controls can be isolated.
- Supports later approvals, audit, and integrations without microservices.
- Easier package-level testing.

Weaknesses:

- Requires staged import changes.
- Temporary mixed structure during migration.
- Poorly sequenced moves could break API and tests.

Effort: medium.

Operational risk: manageable with atomic batches.

Suitability: **best fit for EDIP**.

CITP value: strong, because architectural rationale, migration risk, tests, and outcomes can be documented.

### Option C — Broader monorepo restructuring

```text
apps/
├── backend/
└── frontend/
packages/
pipelines/
platform/
```

Benefits:

- Clear multi-application naming.
- Could support many deployable services later.

Weaknesses:

- No current need for `packages/` or multiple services.
- Large Docker, import, CI, Airflow, Terraform, and documentation impact.
- Encourages premature abstraction.

Effort: high.

Operational risk: high.

Suitability: poor at the current stage.

Recommendation: **Option B, implemented incrementally with Option A first**.

---

## 18. Final recommended lean target structure

```text
app/
├── main.py
├── core/
│   ├── config.py
│   ├── logging.py
│   └── monitoring.py
├── rag/
│   ├── api.py
│   ├── schemas.py
│   ├── service.py
│   ├── retriever.py
│   ├── generator.py
│   ├── vector_store.py
│   └── exceptions.py
├── workflows/
│   ├── api.py
│   ├── schemas.py
│   ├── service.py
│   ├── graph.py
│   ├── state.py
│   ├── routing.py
│   ├── adapters.py
│   ├── planner.py
│   ├── retrieval_stage.py
│   ├── reasoning.py
│   ├── analytics_stage.py
│   └── execution.py
├── forecasting/
│   ├── api.py
│   ├── schemas.py
│   ├── service.py
│   ├── artifacts.py
│   └── rules.py
└── events/
    └── service.py

configs/
├── rag/
└── events/

pipelines/
├── rag/
├── forecasting/
└── airflow_dags/

scripts/
tests/
ui/
database/
monitoring/
infra/
docs/
data/
artifacts/
```

Future capabilities, created only with real code:

- `app/approvals/`: durable approval state, role checks, resume behavior.
- `app/audit/`: protected decision/audit persistence.
- `app/integrations/`: ERP, CRM, MCP, and approved external-evidence adapters.
- RAG `citations.py`, `evidence_quality.py`, `access_control.py`, and `prompt_security.py`.

This remains one deployable backend. No microservices are introduced.

---

## 19. Files and folders that should remain unchanged

Keep their current names and top-level positions:

- `app/main.py`
- `app/core/config.py`
- `app/core/logging.py`
- `app/core/monitoring.py`
- `ui/`
- `database/`
- `monitoring/`
- `infra/terraform/aws/`
- `.github/`
- root `Dockerfile`
- root `docker-compose.yml`
- `requirements.txt`
- `requirements-dev.txt`
- `pytest.ini`
- `LICENSE`
- `AI_USAGE.md`
- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- generated-data and artifact top-level categories
- synthetic data generators
- Kafka operator scripts until reusable event logic is extracted

The source contents may later require fixes, but their structural ownership is valid.

---

## 20. Files and folders that should move, merge or be removed

### Move/split now or soon

- RAG API, schemas, query service, generation service → `app/rag/`
- Workflow API, service, graph, and stage classes → `app/workflows/`
- `RagRetrievalAdapter` → workflow adapters
- RAG ingestion modules → `pipelines/rag/`, retaining thin scripts

### Move later

- Forecast API/service → `app/forecasting/`
- Forecast pipeline files → `pipelines/forecasting/`
- Event processing service → `app/events/`
- RAG corpus → `docs/knowledge/`
- K8s assets → explicitly optional location if retained

### Merge/remove

- Merge/remove `app/core/metrics.py`
- Remove empty `app/services/app/services`
- Remove redundant `.gitkeep` files
- Remove root `__init__.py` if final import verification confirms no need
- Replace duplicate embedded dashboards/alerts with canonical `monitoring/` assets
- Archive or redefine `requirements_full.txt`
- Rename misleading Kafka “end-to-end” test
- Move or convert the non-pytest RAG retrieval evaluator

---

## 21. Safe migration sequence

Each step should be one focused commit.

### Step 1 — Frontend reproducibility

Files: root `.gitignore`, `ui/src/lib/utils.ts`.

Checks:

- Fresh-copy tracked-file build
- `npm run lint`
- `npm run build`
- Parent Git status

Rollback: revert the single commit.

Acceptance: UI builds using only tracked source.

### Step 2 — Remove unambiguous stale tracked paths

Files:

- `app/services/app/services`
- redundant `.gitkeep` files
- possibly root `__init__.py`

Checks:

- Python import smoke test
- Test collection
- Docker context inspection

Rollback: revert deletion commit.

Acceptance: no import or build references removed files.

### Step 3 — Monitoring canonicalization

Files:

- `app/core/metrics.py`
- `monitoring/`
- local-k8s Terraform
- raw K8s monitoring manifests

Checks:

- FastAPI import
- `/metrics` test
- Compose config
- Terraform validation
- K8s render/config validation

Rollback: restore duplicate deployment definitions from commit.

Acceptance: one metric-definition module and one source dashboard/alert set.

### Step 4 — RAG path/config contract

Files:

- RAG YAML
- four RAG scripts
- retrieval evaluator
- documentation

Checks:

- Configuration parsing
- Metadata/chunk path unit tests
- Dry-run validation using fixtures
- Manifest-name assertions

Rollback: revert configuration contract commit.

Acceptance: every stage consumes the same configured filenames and index/namespace.

### Step 5 — Online RAG package migration

Files: existing RAG API/schema/service files plus imports/tests.

Checks:

- RAG unit tests
- API integration tests
- `app.main` import
- Docker build check when authorized
- Stable OpenAPI/response contract

Rollback: revert one substep at a time; use compatibility re-exports temporarily if necessary.

Acceptance: all online RAG code is owned by `app/rag/`.

### Step 6 — Workflow package migration

Files: `app/agents/*`, workflow API/service, demo script, tests.

Checks:

- Planner/routing/state unit tests
- Workflow integration tests using real stage objects
- API contract tests
- Demo command
- Import smoke test

Rollback: revert workflow package commit or retain temporary re-exports.

Acceptance: no runtime imports remain under `app.agents`.

### Step 7 — Offline RAG modules

Files: RAG scripts and new `pipelines/rag/` modules.

Checks:

- Script `--help`
- Fixture-based metadata/chunk tests
- Embedding client fakes
- Index adapter tests

Acceptance: scripts are thin wrappers; reusable code is importable.

### Step 8 — Data/artifact contract

Files: manifests, documentation, artifact loader configuration, deployment paths.

Checks:

- Checksum validation
- Missing/stale artifact tests
- Container startup without developer-local folders
- Provenance assertions

Acceptance: runtime artifacts are resolved by immutable ID, not incidental local presence.

### Step 9 — Forecasting package

Files: forecast API/service, pipeline paths, Airflow DAG, tests.

Checks:

- Forecast service tests
- API tests
- pipeline syntax/import tests
- Airflow DAG import
- Docker/Compose checks

Acceptance: online and offline forecasting boundaries are explicit.

### Step 10 — Documentation and evidence migration

Files: `docs/` corpus and evidence documents; RAG config and source metadata.

Checks:

- All Markdown frontmatter
- Link validation
- RAG ingestion dry run
- Citation source-path migration
- Pinecone reindex plan

Acceptance: knowledge corpus, architecture, research, stakeholder, and CITP evidence are clearly separated.

---

## 22. Phase 0 implementation batches

| Batch | Scope | Evidence to preserve |
|---|---|---|
| 0A — Frontend reproducibility | Stop ignoring `ui/`; track required source | Issue, root cause, clean-clone build logs, PR review, reflection |
| 0B — Unambiguous stale paths | Empty anomaly, redundant markers, nested Git decision | Inventory, removal rationale, import checks, rollback |
| 0C — Monitoring ownership | Canonical metrics/dashboard/alerts | ADR, duplicate hashes, Terraform/Compose checks |
| 0D — RAG configuration contract | Align filenames, index, namespace | Before/after config matrix, dry-run evidence |
| 0E — Online RAG package | Capability-owned API/retrieval/generation | ADR, dependency matrix, tests, OpenAPI comparison |
| 0F — Workflow package | Stages, graph, state, routing, adapters | Alternatives, routing tests, failure risks, review |
| 0G — Data/artifact contract | S3/version/checksum/provenance contract | Data decision record, artifact manifest evidence |
| 0H — Forecast boundary | Online serving vs offline pipeline | Architecture decision, pipeline/API tests |
| 0I — Documentation/CITP alignment | Knowledge, architecture, research, stakeholder evidence | Review records, outcomes, reflection |

For every batch, preserve:

- The issue and observed evidence
- Decision rationale
- Alternatives considered
- Migration and rollback risks
- Commands and results
- PR and reviewer feedback
- Outcome against acceptance criteria
- Short professional reflection

No SFIA level should be claimed.

---

## 23. Acceptance criteria

Repository-level structural acceptance requires:

1. A clean clone contains every required frontend and backend source file.
2. No broad ignore rule hides source directories.
3. Runtime dependency manifests include every required application dependency.
4. One canonical owner exists for each metric, dashboard, alert, and runtime configuration value.
5. Online RAG code resides under one capability package.
6. Workflow state, routing, stages, and transport have distinct ownership.
7. Retrieval stages use a retrieval-only interface.
8. Online and offline forecasting are separate.
9. Generated data/artifacts are not tracked, but are immutable, checksummed, manifested, and retrievable.
10. Application startup does not depend on undocumented developer-local files.
11. Fake-backed integration tests are labeled honestly.
12. Live external-service evaluations are distinct from unit/in-process integration tests.
13. ECS remains the canonical AWS path; Kubernetes is explicitly optional.
14. RAG knowledge documents are separate from architecture, research, CITP, and stakeholder evidence.
15. Every migration batch has independent tests, rollback, review, and evidence.

---

## 24. First implementation batch

The first batch should be only the frontend reproducibility repair.

Recommended scope:

- Correct the root `.gitignore` rule that ignores all `ui/`.
- Preserve explicit ignores for `ui/node_modules/`, `ui/.next/`, local environment files, and build output.
- Add the already-required `ui/src/lib/utils.ts` to parent-repository tracking.
- Do not move frontend files.
- Do not remove the nested `ui/.git` in the same batch.
- Do not combine this with RAG, workflow, dependency, or documentation work.

Required checks:

```powershell
git check-ignore -v ui/src/lib/utils.ts
git ls-files ui/src/lib/utils.ts
npm.cmd run lint
npm.cmd run build
git status --short
```

Additional clean-clone acceptance check:

- Export or clone only tracked files into an isolated directory.
- Install from `ui/package-lock.json`.
- Run lint and production build.
- Confirm no source file is required from the original working copy.

Commit boundary: one focused commit.

Rollback: revert that commit.

Acceptance criteria:

- `ui/src/lib/utils.ts` is tracked.
- New legitimate files under `ui/src/` are not silently ignored.
- Generated UI content remains ignored.
- Lint passes.
- Production build passes from tracked source only.
- No backend, API contract, deployment, or visual behavior changes.

No changes were performed during this audit.
