# EDIP Legacy Synthetic-Data Asset Audit

- Audit date: 14 August 2026
- Audit mode: Repository-wide evidence review and proposed cleanup plan
- Repository: `enterprise_decision_intelligence_platform_EDIP`
- Branch reviewed: `chore/audit-legacy-synthetic-assets`
- Commit reviewed: `dfa2079a24877c2d86b1465bea9ede9f3ad4f706`
- Result type: Audit and cleanup proposal; not an implementation or deletion record

> This report identifies repository assets from the former synthetic NorthStar Retail & Distribution implementation and separates them from the current real-data Corporación Favorita work and the reusable EDIP target architecture. No deletion, migration, code change, dataset rewrite, external-index operation, commit, push, merge, or pull request is approved or recorded by this document.

## 1. Technical Summary

EDIP now has a verified real-data path based on the Kaggle Corporación Favorita Grocery Sales Forecasting dataset, but substantial tracked source and ignored local output still belong to the earlier synthetic NorthStar implementation.

The highest-confidence deletion candidates are the synthetic table generators, the old synthetic ETL and feature module, the Kafka simulation and Airflow demo, fictional NorthStar RAG documents, generated NorthStar model/forecast/RAG outputs, and ordinary repository caches. These assets are identifiable through their contents and dependencies: they use `data/synthetic`, NorthStar company metadata, synthetic `fact_*` and `dim_*` tables, or identifiers such as `product_id`, `region_id`, `channel_id`, and `location_id` rather than Favorita's `store_nbr` and `item_nbr` grain.

Forecasting, inventory-risk decision support, RAG, LangGraph workflow orchestration, the FastAPI boundary, the UI, monitoring, and AWS deployment remain required or relevant capabilities under the canonical architecture. Their current implementations must therefore be assessed individually. Some contain reusable interfaces or infrastructure, but the current synthetic-coupled or unsafe implementation cannot be treated as the real-data target.

The current Favorita notebooks, cleaned-data lineage, model-ready feature code, feature-contract tests, source governance, and canonical architecture must be preserved. In particular, the following are protected from legacy cleanup:

- `pipelines/features/favorita_model_ready.py`
- `notebooks/favorita/08_build_model_ready_feature_dataset.ipynb`
- `tests/unit/test_favorita_model_ready_features.py`

## 2. Audit Objective and Current Context

The objective is to create a durable, evidence-based cleanup plan for assets that became obsolete when EDIP moved from a synthetic retail implementation to the real Kaggle Favorita dataset.

This is not a request to erase all historical work. The audit distinguishes:

- current Favorita source, transformation, feature, test, and lineage assets;
- canonical architecture and historical governance evidence;
- reproducible caches and generated outputs;
- synthetic-specific implementations that have no valid role in the current data path;
- capabilities that remain required but need a real-data or safety-oriented rebuild; and
- assets for which ownership or deletion impact cannot be established safely without human or external-system evidence.

The current Favorita grain is based on observed `(date, store_nbr, item_nbr)` rows. Its cleaning policy does not densify the panel or infer zero sales from absent source records. The current model-ready feature implementation uses exact calendar-date lag semantics and complete-window checks. The old synthetic feature pipeline instead assumes a different entity model and row-shift semantics; it is not an alternative implementation of the same executable contract.

## 3. Scope and Repository Areas Inspected

The audit reviewed tracked source and local ignored/untracked state across:

- `app/`
- `artifacts/`
- `configs/`
- `data/`
- `docs/`, including every tracked file under `docs/architecture/`
- `infra/`
- `monitoring/`
- `notebooks/`
- `pipelines/`
- `scripts/`
- `tests/`
- `tmp/`
- `ui/`
- root dependency, Docker, Compose, pytest, Git-ignore, licensing, and governance files
- `.github/workflows/`
- ignored caches, local environments, Terraform working state, and generated artifacts

The audit did not open or materialize the complete Favorita datasets. Dataset paths and lineage claims were checked through file metadata, small JSON manifests, notebook JSON, tracked code, and previously executed audit evidence at the same commit.

## 4. Audit Method and Evidence

Classification was not based on filenames or timestamps alone. The following evidence was used:

1. `git ls-files`, `git status --short`, `git check-ignore`, and path-specific `git log` history.
2. Imports and reverse references searched across application, pipelines, scripts, tests, Docker Compose, CI, configuration, and documentation.
3. FastAPI route registration in `app/main.py`.
4. Docker, Compose, Airflow, Kubernetes, Terraform, and GitHub Actions entrypoints.
5. Pytest collection and the prior baseline execution at the same reviewed commit.
6. Environment-variable and package usage, without disclosing local secret values.
7. Input/output paths, manifests, identifier columns, expected schemas, and artifact consumers.
8. Explicit `data/synthetic`, NorthStar, `dim_*`, and `fact_*` assumptions.
9. Current Favorita notebooks, manifests, feature module, and feature-contract tests.
10. The canonical target and phase gates in `docs/architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md`.
11. Deletion impact on imports, tests, API startup, Compose services, generated artifacts, and external resources.

### Current test evidence

At the reviewed commit, the audit baseline completed with:

```text
172 passed, 218 warnings in 57.54s
```

The current repository was subsequently recollected without writing pytest cache or Python bytecode:

```text
172 tests collected in 7.21s
```

All 218 baseline warnings came from deprecated resource-loading APIs imported by `kafka-python`. The test result is local fixture/mock evidence; it does not prove a live Kafka broker, Airflow DAG execution, live OpenAI or Pinecone access, AWS deployment, browser behavior, or production authorization.

## 5. Canonical Architecture Boundary

The canonical architecture is defined by `docs/architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md`. It requires or anticipates:

- a capability-oriented FastAPI modular monolith under `app/`;
- offline data, RAG, forecasting, and evaluation pipelines under `pipelines/`;
- a Next.js UI under `ui/`;
- governed RAG with source ownership, license, validity, supersession, ACL, stable chunk identities, compatibility manifests, and deletion/re-index controls;
- forecasting with temporal validation, uncertainty, immutable artifacts, and deterministic inventory-risk calculation;
- deterministic safety controls and durable human approval outside LLM authorization;
- durable business, approval, and audit state in PostgreSQL;
- immutable datasets, models, manifests, and evidence in S3;
- Pinecone for embeddings rather than durable business state;
- canonical monitoring under `monitoring/`; and
- ECS Fargate as the production deployment target.

The architecture explicitly avoids an initial microservices migration. Kafka, Airflow, Redis, and Kubernetes are gated or optional rather than mandatory core components. A concept appearing in the architecture is therefore not evidence that an older implementation of that concept should remain unchanged.

## 6. Classification Definitions

| Classification | Meaning in this audit |
|---|---|
| `KEEP` | Current Favorita work, reusable and aligned infrastructure, or architecture/governance evidence that must remain. Retention does not imply production readiness. |
| `DELETE CANDIDATE` | Generated/reproducible output, obsolete scaffold, or synthetic-specific implementation with sufficient evidence for a future controlled deletion batch. Deletion is not approved by this report. |
| `REBUILD` | The capability remains required or useful, but the current implementation, contract, or evidence is incompatible with Favorita or the canonical architecture. |
| `UNCERTAIN` | Evidence is insufficient, ownership is external, or deletion could damage local/cloud state. Human review is required. |

Tracking-state terms used below:

- **Tracked**: present in the Git index at the reviewed commit.
- **Ignored/generated**: local and excluded by `.gitignore` or `ui/.gitignore`.
- **Untracked**: local and not in the Git index; the important local data/artifact paths reviewed here are also ignored.

## 7. Master Asset Classification

Directory rows apply to every current child in that exact directory only when the evidence and recommendation are uniform. More granular exceptions are listed separately.

### 7.1 Current Favorita and governance assets

| Classification | Exact repository path | State | Current purpose and evidence | References and removal risk |
|---|---|---|---|---|
| `KEEP` | `notebooks/favorita/01_data_inventory_and_quality.ipynb` through `notebooks/favorita/08_build_model_ready_feature_dataset.ipynb` | Tracked | Current real-data workflow from source inventory through cleaned and model-ready feature data. All eight notebook JSON files were readable and had no saved error outputs during the audit. | Removing any notebook would break Favorita lineage and implementation evidence. |
| `KEEP` | `pipelines/features/favorita_model_ready.py` | Tracked | Current bounded real-data feature implementation using `store_nbr`, `item_nbr`, exact-date lags, complete calendar windows, and the cleaned Favorita source. | Imported by `tests/unit/test_favorita_model_ready_features.py` and used by Notebook 08. Must not be included in legacy feature deletion. |
| `KEEP` | `tests/unit/test_favorita_model_ready_features.py` | Tracked | Four focused tests for row-group correctness, exact origin-relative lags, training/inference parity, forbidden columns, and horizon rules. | Removing it would eliminate the executable contract for current model-ready features. |
| `KEEP` | `data/raw/favorita-grocery-sales-forecasting/` | Ignored/untracked | Local Kaggle Favorita raw files, including `train.csv`, `test.csv`, stores, items, transactions, holidays, oil, and sample submission. | Large source data; never include in generated or synthetic deletion. |
| `KEEP` | `data/processed/favorita_merged/favorita_merged_base.parquet` | Ignored/untracked | Current source-derived merged dataset. | Input to the cleaning workflow; deletion would remove the source-derived lineage. |
| `KEEP` | `data/processed/favorita_cleaned/favorita_cleaned.parquet` | Ignored/untracked | Current validated cleaned dataset. | Input to current feature construction. Do not rewrite or delete during legacy cleanup. |
| `KEEP` | `data/processed/favorita_cleaned/cleaning_manifest.json` | Ignored/untracked | SCRUM-10 schema, row-count, grain, null, and exact logical content evidence. | Required lineage/governance evidence. |
| `KEEP` | `data/processed/favorita_features/smoke/` | Ignored/untracked | Bounded real-data Notebook 08 smoke output and feature manifest. | Current validation evidence, not a legacy generated artifact. |
| `KEEP` | `artifacts/reports/favorita_eda/01_data_inventory_and_quality_summary.json` | Ignored/untracked | Bounded Favorita EDA summary produced by Notebook 01. | Current source-quality evidence. Exclude from broad `artifacts/reports/` deletion. |
| `KEEP` | `docs/phase-1/FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md` | Tracked | Current source, use, and governance record. | Required Favorita governance. |
| `KEEP` | `docs/phase-1/FAVORITA_POST_DOWNLOAD_VERIFICATION.md` | Tracked | Current raw-download verification evidence. | Required source-verification evidence. |
| `KEEP` | `docs/architecture/` | Tracked | Canonical target architecture. One tracked architecture file was present and reviewed. | Dated current-state statements can be updated later; the architecture must not be removed as legacy code. |
| `KEEP` | `docs/audits/` | Tracked | Historical and current repository audit evidence. | Historical references to later-deleted assets should remain as records, unless a future correction explicitly annotates them. |
| `KEEP` | `AI_USAGE.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE` | Tracked | Project governance, conduct, contribution, AI-use, and licensing. | Outside legacy cleanup scope. |

### 7.2 Synthetic data generation, ETL, feature, and artifact assets

| Classification | Exact repository path | State | Current purpose and evidence | References, risk, and prerequisites |
|---|---|---|---|---|
| `DELETE CANDIDATE` | `scripts/generate_phase_1_dimensions.py` | Tracked | Generates synthetic product, store, warehouse, channel, supplier, customer, and regional dimensions. Content uses `product_id`, `region_id`, `channel_id`, and fabricated codes. | Foundation for other synthetic generators. Delete only with the complete obsolete generator chain. |
| `DELETE CANDIDATE` | `scripts/generate_phase_1_procurement_inventory.py` | Tracked | Generates synthetic procurement, inventory, and inbound-shipment facts. | Referenced by later synthetic flows; not a Favorita input. |
| `DELETE CANDIDATE` | `scripts/generate_phase_2_sales_commercial.py` | Tracked | Generates synthetic sales/commercial facts. | Conflicts with the current Kaggle source lineage. |
| `DELETE CANDIDATE` | `scripts/generate_phase_2_promotions_price_history.py` | Tracked | Generates synthetic promotion and price-history tables against NorthStar dimensions. | Favorita promotion semantics and identifiers differ. |
| `DELETE CANDIDATE` | `scripts/generate_phase_3_forecast_replenishment.py` | Tracked | Generates synthetic forecast and replenishment records. | Not the current or target forecasting pipeline. |
| `DELETE CANDIDATE` | `scripts/generate_phase_4_planner_overrides_decision_logs.py` | Tracked | Generates synthetic planner override and decision-log data. | Durable audit remains architecturally required, but this fixture generator is not that implementation. |
| `DELETE CANDIDATE` | `pipelines/etl/build_training_dataset.py` | Tracked | Defaults to `data/synthetic` and joins synthetic `dim_*`/`fact_*` inputs. Produces legacy `units_sold` data keyed by product, channel, region, and location. | Replaced at the data-contract level by Favorita merged, cleaned, and model-ready work. |
| `DELETE CANDIDATE` | `pipelines/features/demand_features.py` | Tracked | Legacy feature builder using `product_id`, `region_id`, `channel_id`, `location_id`, `units_sold`, row shifts, and partial rolling windows. | Do not confuse with `favorita_model_ready.py`. Delete only after confirming no undocumented operator entrypoint remains. |
| `REBUILD` | `pipelines/training/train_demand_forecast.py` | Tracked | Trains legacy estimators against `data/processed/features/demand_features.parquet` and `target_units_sold_t_plus_1`. | Forecast training is required, but must use the Favorita feature contract, temporal evaluation, uncertainty, and immutable manifests. |
| `REBUILD` | `pipelines/training/evaluate_demand_forecast.py` | Tracked | Evaluates locally discovered legacy models and features; historical audit evidence records inadequate validation isolation. | Replace with rolling temporal evaluation and explicit baselines before removing. |
| `REBUILD` | `pipelines/inference/score_demand_forecast.py` | Tracked | Loads legacy local model/schema files and emits NorthStar-shaped scoring output. | Replace with an approved Favorita model artifact and compatibility checks. |
| `REBUILD` | `pipelines/inference/generate_recommendations.py` | Tracked | Explicitly reads `data/synthetic` inventory, inbound shipment, product, and supplier files and uses synthetic IDs. | Inventory decision support remains required, but needs real governed inventory inputs and deterministic policy. |
| `REBUILD` | `app/api/forecast.py` | Tracked | Registered online forecast route for legacy artifact-backed service. | Must change with the forecast service and its tests; deleting only artifacts would degrade the API. |
| `REBUILD` | `app/services/forecast_service.py` | Tracked | Reads `artifacts/forecasts/demand_forecast_scored.csv`, recommendations, and legacy evaluation reports. | Protected by 21 unit tests and 8 API tests that characterize the old contract. Replace service and tests together. |
| `REBUILD` | `tests/unit/test_forecast_service.py` | Tracked | Tests local CSV/JSON loading and legacy recommendation shapes. | Replace with real artifact compatibility, missing/stale artifact, uncertainty, and lineage tests. |
| `REBUILD` | `tests/integration/test_forecast_api.py` | Tracked | Eight tests characterize the current legacy forecast endpoints. | Replace with the API contract rather than delete independently. |

### 7.3 Kafka, event simulation, and Airflow

| Classification | Exact repository path | State | Current purpose and evidence | References, risk, and prerequisites |
|---|---|---|---|---|
| `DELETE CANDIDATE` | `configs/kafka_event_schema.yaml` | Tracked | NorthStar event schema referencing synthetic `analytics.fact_*` tables and synthetic identifiers. | Remove with the Kafka generator/producer/consumer chain. |
| `DELETE CANDIDATE` | `scripts/generate_phase_6_kafka_events.py` | Tracked | Generates simulated Kafka events from synthetic tables. | Its 54 collected integration tests are synthetic-specific. |
| `DELETE CANDIDATE` | `scripts/init_kafka_topics.py` | Tracked | Initializes the demo topic set. | Referenced by `docker-compose.yml`. Remove Compose entrypoint in the same batch. |
| `DELETE CANDIDATE` | `scripts/kafka_producer.py` | Tracked | Publishes generated JSONL event files. | Imported by producer and fake end-to-end tests. |
| `DELETE CANDIDATE` | `scripts/kafka_consumer.py` | Tracked | Consumes the demo topics and calls the legacy event-processing service. | Imported by consumer and fake end-to-end tests. |
| `DELETE CANDIDATE` | `app/services/event_processing_service.py` | Tracked | Processes events using legacy product, location, warehouse, store, and region identifiers. | Delete with Kafka consumers and its 11 unit tests. |
| `DELETE CANDIDATE` | `tests/integration/test_kafka_event_generation.py` | Tracked | Fifty-four collected tests validate generated synthetic event files. | Delete with event generator and schema. |
| `DELETE CANDIDATE` | `tests/integration/test_kafka_end_to_end_flow.py` | Tracked | Four collected fake-backed tests; no broker is used. | Delete with producer/consumer/service. |
| `DELETE CANDIDATE` | `tests/unit/test_kafka_producer.py` | Tracked | Eleven fake-backed producer tests. | Delete with producer. |
| `DELETE CANDIDATE` | `tests/unit/test_kafka_consumer.py` | Tracked | Fourteen fake-backed consumer tests. | Delete with consumer. |
| `DELETE CANDIDATE` | `tests/unit/test_event_processing_service.py` | Tracked | Eleven tests protect only the legacy event rules. | Delete with event service. |
| `DELETE CANDIDATE` | `pipelines/airflow_dags/edip_orchestration_demo_dag.py` | Tracked | Manually triggered demo DAG that chains legacy scoring and recommendation scripts. | No collected DAG-execution test. Airflow is gated by the architecture. |
| `REBUILD` | `docker-compose.yml` | Tracked | Default stack couples API startup to Kafka and topic initialization and includes Airflow/PostgreSQL services that install packages at container startup. | Rebuild as a minimal local stack with optional profiles only when justified. Preserve Prometheus/Grafana ownership. |
| `REBUILD` | `requirements.txt`, `requirements-dev.txt` | Tracked | `kafka-python` is needed only by the legacy Kafka scripts/tests. `pydantic-settings` and `requests` have no direct repository import. | Reconcile after code removal; do not remove packages before their consumers. `pandas`, `numpy`, `openai`, `pinecone`, and `langgraph` still support current or required capabilities. |

### 7.4 RAG assets

| Classification | Exact repository path | State | Current purpose and evidence | References, risk, and prerequisites |
|---|---|---|---|---|
| `DELETE CANDIDATE` | `docs/phase_5_rag_knowledge_scope.md` | Tracked | Explicitly defines a synthetic NorthStar knowledge layer aligned with synthetic Phases 1–4. | Delete as operational corpus only; historical audits remain. |
| `DELETE CANDIDATE` | `docs/rag_source/` | Tracked, 28 files | Every current document uses NorthStar business metadata and fictional operating content. | Generated metadata, chunks, embeddings, and old evaluation depend on this corpus. |
| `DELETE CANDIDATE` | `docs/policies/` | Tracked, 5 files | Fictional NorthStar business policies, not EDIP repository governance. | Delete with the synthetic RAG corpus. Do not confuse with architecture or audit documents. |
| `DELETE CANDIDATE` | `docs/reviews/` | Tracked, 3 files | Fictional NorthStar 2025 business reviews. | Delete with the synthetic RAG corpus. |
| `DELETE CANDIDATE` | `docs/sops/warehouse_receiving_sop.md` | Tracked | Fictional NorthStar warehouse SOP. | Delete with the synthetic RAG corpus. |
| `REBUILD` | `configs/rag_ingestion_config.yaml` | Tracked | Hard-codes NorthStar and declares `edip-rag-phase6` / `northstar-retail-v1`. Its declared output names conflict with script defaults. | Replace with an approved-source ingestion and compatibility contract. |
| `REBUILD` | `configs/rag_metadata_schema.yaml` | Tracked | Requires NorthStar company metadata, `DOC-NRD`-era facts, and synthetic source-system values. | Replace while preserving useful governance field concepts. |
| `REBUILD` | `scripts/build_rag_metadata.py` | Tracked | Enforces `company_name == "NorthStar Retail & Distribution"`. | Refactor into a governed offline RAG pipeline. |
| `REBUILD` | `scripts/chunk_rag_documents.py` | Tracked | Reusable chunking mechanics, but coupled to old configuration and artifact names. | Preserve useful mechanics; add stable IDs and manifest compatibility. |
| `REBUILD` | `scripts/embed_rag_chunks.py` | Tracked | Reusable embedding batching, but consumes obsolete chunks and inconsistent configuration. | Rebuild with approved corpus, model/dimension contract, and immutable manifest. |
| `REBUILD` | `scripts/load_rag_to_pinecone.py` | Tracked | Reusable Pinecone adapter mechanics, but defaults differ from ingestion YAML. | Add controlled index/namespace ownership, deletion, migration, and rollback. |
| `DELETE CANDIDATE` | `tests/integration/test_rag_retrieval.py` | Tracked but not collected by pytest | Executable NorthStar/Pinecone retrieval evaluator with synthetic-specific queries and a generated default output. | Replace with governed retrieval evaluation; do not treat its filename as proof that it is an active pytest test. |
| `REBUILD` | `app/api/rag.py`, `app/schemas/rag.py` | Tracked | Current online RAG request/response boundary. | Capability remains, but needs versioning, identity, tenancy, authorization, and safer readiness semantics. |
| `REBUILD` | `app/services/rag_query_service.py` | Tracked | Contains useful embedding/vector-store protocols and filters, but no tenant/document ACL enforcement. | Retain adapter ideas; rebuild authorization and compatibility controls. |
| `REBUILD` | `app/services/rag_generation_service.py` | Tracked | Current OpenAI generation service; system prompt names NorthStar. | Replace prompt/config contract and add grounded/insufficient-context controls. |
| `REBUILD` | `tests/integration/test_rag_api.py`, `tests/unit/test_rag_query_service.py`, `tests/unit/test_rag_generation_service.py` | Tracked | Thirty-five collected tests protect useful validation, adapter, threshold, fallback, context, and error behavior. | Adapt rather than delete wholesale; add ACL, source-authority, injection, compatibility, and citation tests. |

### 7.5 Workflow, API, UI, monitoring, and infrastructure

| Classification | Exact repository path | State | Current purpose and evidence | References, risk, and prerequisites |
|---|---|---|---|---|
| `REBUILD` | `app/agents/` | Tracked, 6 files | Current planner/retrieval/reasoning/analytics/execution workflow uses synthetic business identifiers and lacks durable fail-closed approval. | LangGraph remains required. Rebuild under the canonical workflow/safety contract. |
| `REBUILD` | `app/api/agent_workflow.py`, `app/services/agent_workflow_service.py`, `scripts/run_agent_workflow_demo.py` | Tracked | Demo workflow API/service/runner. | Replace with durable state, explicit failure states, policy enforcement, and human resume. |
| `REBUILD` | `tests/integration/test_agent_workflow_api.py` | Tracked, 4 collected tests | Characterizes current demo behavior. | Replace with safety, authorization, persistence, and resume tests. |
| `REBUILD` | `app/main.py` | Tracked | FastAPI entrypoint registers legacy forecast, RAG, and workflow routes without authentication, tenant context, versioning, or a distinct readiness endpoint. | Retain the application boundary but rebuild registration and readiness as capabilities migrate. |
| `REBUILD` | `app/core/config.py` | Tracked | Useful environment parsing, but contains legacy RAG defaults and permissive local CORS defaults. | Replace with one validated typed configuration and secure secret references. |
| `KEEP` | `app/core/logging.py`, `app/core/monitoring.py` | Tracked | Active cross-cutting logging and Prometheus instrumentation; no Favorita/synthetic schema coupling. | Preserve. |
| `KEEP` | `monitoring/` | Tracked | Canonical Prometheus/Grafana source under the architecture and Phase 0 monitoring ownership audit. | Preserve; reconcile deployment duplication separately. |
| `KEEP` | `tests/integration/test_monitoring_api.py` | Tracked, 3 collected tests | Protects app import and monitoring endpoint behavior. | Preserve during route migration. |
| `REBUILD` | `ui/src/app/chat/page.tsx`, `ui/src/app/page.tsx`, `ui/src/app/layout.tsx`, `ui/src/app/favicon.ico` | Tracked | Current UI is a synthetic workflow demo; root metadata still contains create-next-app defaults. | Rebuild for evidence, uncertainty, real identity, approval state, and accessibility. |
| `DELETE CANDIDATE` | `ui/README.md`, `ui/public/file.svg`, `ui/public/globe.svg`, `ui/public/next.svg`, `ui/public/vercel.svg`, `ui/public/window.svg` | Tracked | Unmodified create-next-app documentation and branding assets. | Remove during UI rebuild after confirming no intentional design use. |
| `UNCERTAIN` | `ui/src/components/ui/`, `ui/src/lib/utils.ts`, `ui/package.json`, `ui/package-lock.json`, `ui/components.json`, `ui/eslint.config.mjs`, `ui/next.config.ts`, `ui/postcss.config.mjs`, `ui/tsconfig.json`, `ui/src/app/globals.css` | Tracked | Generic Next.js/shadcn/Tailwind foundation with real imports. Not synthetic-specific, but future UI design is not approved. | Retain until the UI rebuild decides which primitives and dependencies remain. |
| `KEEP` | `.github/workflows/integration-ci.yml`, `.github/workflows/docker-ci.yml`, `Dockerfile`, `.dockerignore`, `.gitignore`, `pytest.ini` | Tracked | Active baseline build/test and repository hygiene. | Update only as dependent legacy modules are removed. |
| `REBUILD` | `infra/terraform/aws/` tracked Terraform files | Tracked | ECS Fargate aligns with the target, but current files use mutable image tags and task environment values for external-service secrets. | Rebuild for immutable images, Secrets Manager, private networking, S3/RDS, and rollback. |
| `REBUILD` | `.github/workflows/terraform-ci.yml` | Tracked | Validates both canonical AWS and optional local Kubernetes and supplies legacy RAG placeholder contract values. | Update with infrastructure/RAG ownership decisions. |
| `UNCERTAIN` | `infra/k8s/` | Tracked | Raw Kubernetes API and duplicated monitoring deployment evidence. Kubernetes is optional learning evidence, not canonical production. | Human decision required: retain, archive, or delete after confirming portfolio/learning value. |
| `UNCERTAIN` | `infra/terraform/local-k8s/` tracked Terraform files | Tracked | Alternative local-Kubernetes implementation that duplicates raw manifests and monitoring definitions. | Same ownership decision as `infra/k8s/`. |
| `REBUILD` | `README.md` | Tracked | Architecture overview is useful, but current-status text says Phase 1 has not started and describes earlier test/dependency limitations. | Update after cleanup so implementation status and evidence remain accurate. |

## 8. RAG Replacement Assessment

The RAG system must be separated by asset type; deleting the fictional corpus does not justify deleting reusable interfaces or the canonical RAG architecture.

### 8.1 Legacy source corpus

The exact synthetic corpus is:

- `docs/phase_5_rag_knowledge_scope.md`
- every current file under `docs/rag_source/`
- every current file under `docs/policies/`
- every current file under `docs/reviews/`
- `docs/sops/warehouse_receiving_sop.md`

Content evidence includes NorthStar company metadata, `DOC-NRD` identifiers, synthetic `fact_*` relationships, fictional business reviews, and an explicit statement that the knowledge layer supports the synthetic enterprise workflow built in earlier phases.

These are `DELETE CANDIDATE` assets as an operational corpus. They are not the same as EDIP repository governance in `docs/architecture/`, `docs/audits/`, or the Favorita source-governance documents.

### 8.2 Reusable RAG code

The following contain potentially reusable mechanics but require rebuild:

- `scripts/build_rag_metadata.py`
- `scripts/chunk_rag_documents.py`
- `scripts/embed_rag_chunks.py`
- `scripts/load_rag_to_pinecone.py`
- `app/services/rag_query_service.py`
- `app/services/rag_generation_service.py`
- `app/api/rag.py`
- `app/schemas/rag.py`
- the collected RAG API and unit tests

Reusable concepts include batching, adapter protocols, question validation, score thresholds, context construction, no-match fallback, and response-source construction. Missing target controls include approved-source registration, tenant/document ACL enforcement before return, stable corpus and chunk identities, source authority/freshness/supersession, prompt-injection tests, embedding/index compatibility, deletion/re-index operation, and explicit insufficient-context behavior.

### 8.3 Generated chunks and embeddings

The exact local generated RAG output is:

- `data/processed/rag/document_metadata.jsonl`
- `data/processed/rag/document_chunks.jsonl`
- `data/processed/rag/document_chunks.csv`
- `data/processed/rag/chunk_embeddings.jsonl`
- `data/processed/rag/chunk_embeddings.csv`
- `data/processed/rag/embedding_manifest.json`
- `data/processed/rag/pinecone_load_manifest.json`
- `data/processed/rag/retrieval_test_results.json`

All are ignored/untracked and derived from the old corpus. The embedding manifest contains stale absolute checkout lineage. They are `DELETE CANDIDATE` generated outputs, but removal should follow the corpus and external-index ownership decision.

### 8.4 Vector-index artifacts

The local Pinecone load manifest records an old index/namespace operation, but repository inspection cannot prove whether the remote vectors still exist, whether the namespace is shared, or whether another environment depends on it. Any remote index or namespace deletion is therefore `UNCERTAIN` and requires a credentialed inventory, named owner, retention decision, and explicit approval outside ordinary source cleanup.

## 9. Generated Caches and Local Working Files

### 9.1 Safe generated cleanup candidates

| Classification | Exact path | State | Evidence and removal impact |
|---|---|---|---|
| `DELETE CANDIDATE` | `.coverage` | Ignored/untracked | Reproducible coverage database. No runtime consumer. |
| `DELETE CANDIDATE` | `.pytest_cache/` | Ignored/untracked | Reproducible pytest cache. |
| `DELETE CANDIDATE` | every repository `**/__pycache__/` outside `.venv/` and `ui/node_modules/` | Ignored/untracked | Python bytecode caches. The audit observed 18 repository cache directories and 143 `.pyc` files before documentation creation. |
| `DELETE CANDIDATE` | `tmp/` | Ignored/untracked | Contained only three Notebook 05 helper `.pyc` files during the audit. No source helper was present. |
| `DELETE CANDIDATE` | `ui/.next/` | Ignored/untracked | Reproducible Next.js build/development output. |
| `DELETE CANDIDATE` | `infra/terraform/aws/.terraform/` | Ignored/untracked | Reproducible Terraform provider cache. |
| `DELETE CANDIDATE` | `infra/terraform/local-k8s/.terraform/` | Ignored/untracked | Reproducible Terraform provider cache. |
| `DELETE CANDIDATE` | `.vscode/settings.json` | Ignored/untracked | Local editor setting points to the stale path `D:/Dev/enterprise_decision_intelligence_platform_EDIP/venv/Scripts/python.exe`. |

### 9.2 Local files that must not be deleted automatically

| Classification | Exact path | State | Evidence and reason |
|---|---|---|---|
| `KEEP` | `.venv/` | Ignored/untracked | Active local Python environment used for the verified pytest baseline. Reproducible, but unrelated to synthetic-data cleanup and costly to recreate. |
| `KEEP` | `ui/node_modules/` | Ignored/untracked | Active local UI dependency installation. Reproducible, but unrelated to synthetic lineage. |
| `UNCERTAIN` | `.env` | Ignored/untracked | Contains active application and legacy RAG variable names, including secret-bearing keys. Values are not audit evidence and must not be exposed or deleted without migration. |
| `UNCERTAIN` | `ui/.env.local` | Ignored/untracked | Contains the frontend API-base configuration key. Retain until the UI/API migration is approved. |
| `UNCERTAIN` | `infra/terraform/aws/.terraform.lock.hcl`, `infra/terraform/local-k8s/.terraform.lock.hcl` | Ignored/untracked | Provider lockfiles support reproducibility and may need to become tracked. Do not treat them as disposable caches without an IaC policy decision. |
| `UNCERTAIN` | `infra/terraform/aws/terraform.tfstate`, `infra/terraform/local-k8s/terraform.tfstate`, `infra/terraform/local-k8s/terraform.tfstate.backup` | Ignored/untracked | Potentially authoritative resource ownership. Deletion could orphan or obscure local/cloud resources. |

## 10. Artifact Audit and Exact Generated-Artifact Candidates

All legacy artifacts below are ignored/untracked. Their local modification dates were considered only as supporting context, never as classification evidence.

### Legacy forecast outputs

- `artifacts/forecasts/demand_forecast_scored.csv`
- `artifacts/forecasts/demand_forecast_scoring_summary.json`
- `artifacts/forecasts/replenishment_recommendations.csv`
- `artifacts/forecasts/replenishment_recommendation_summary.json`

The scoring output uses the NorthStar product/store/warehouse/region/channel/location schema. The recommendation summary explicitly records synthetic inventory and inbound-shipment inputs. These files are read by `app/services/forecast_service.py`; the forecast and recommendation files are also referenced by the Airflow demo. They must not be deleted before the registered forecast API is replaced or retired.

### Legacy model artifacts

- `artifacts/models/demand_forecast_model.joblib`
- `artifacts/models/feature_schema.json`
- `artifacts/models/model_manifest.json`

The feature schema contains the legacy NorthStar identifiers and synthetic sales, price, promotion, and inventory features. The manifest identifies the target as `target_units_sold_t_plus_1`. Current training, evaluation, and scoring code references these files.

### Legacy evaluation and report output

- `artifacts/reports/model_comparison.csv`
- `artifacts/reports/model_evaluation_report.json`
- `artifacts/reports/demand_forecast_evaluation_report.json`
- `artifacts/reports/demand_forecast_validation_predictions.csv`
- `artifacts/reports/demand_forecast_error_summary.csv`
- `artifacts/reports/rag_frontmatter_fix_report.json`

The forecast reports are synthetic-era evaluation output and do not establish valid Favorita temporal performance. The RAG frontmatter report belongs to the NorthStar corpus and its current producer is absent. The current Favorita EDA report under `artifacts/reports/favorita_eda/` is explicitly excluded from this deletion set.

## 11. Exact Proposed Deletion List

This list is a proposal only. It is not approval to delete and it does not record completed deletion.

### 11.1 Generated/cache candidate batch

- `.coverage`
- `.pytest_cache/`
- root `__pycache__/`
- `app/__pycache__/`
- `app/agents/__pycache__/`
- `app/api/__pycache__/`
- `app/core/__pycache__/`
- `app/schemas/__pycache__/`
- `app/services/__pycache__/`
- `pipelines/__pycache__/`
- `pipelines/airflow_dags/__pycache__/`
- `pipelines/etl/__pycache__/`
- `pipelines/features/__pycache__/`
- `pipelines/inference/__pycache__/`
- `pipelines/training/__pycache__/`
- `scripts/__pycache__/`
- `tests/__pycache__/`
- `tests/integration/__pycache__/`
- `tests/unit/__pycache__/`
- `tmp/`
- `ui/.next/`
- `infra/terraform/aws/.terraform/`
- `infra/terraform/local-k8s/.terraform/`
- `.vscode/settings.json`

### 11.2 Synthetic source and feature candidate batch

- `scripts/generate_phase_1_dimensions.py`
- `scripts/generate_phase_1_procurement_inventory.py`
- `scripts/generate_phase_2_sales_commercial.py`
- `scripts/generate_phase_2_promotions_price_history.py`
- `scripts/generate_phase_3_forecast_replenishment.py`
- `scripts/generate_phase_4_planner_overrides_decision_logs.py`
- `pipelines/etl/build_training_dataset.py`
- `pipelines/features/demand_features.py`

### 11.3 Kafka and Airflow candidate batch

- `configs/kafka_event_schema.yaml`
- `scripts/generate_phase_6_kafka_events.py`
- `scripts/init_kafka_topics.py`
- `scripts/kafka_producer.py`
- `scripts/kafka_consumer.py`
- `app/services/event_processing_service.py`
- `tests/integration/test_kafka_event_generation.py`
- `tests/integration/test_kafka_end_to_end_flow.py`
- `tests/unit/test_kafka_producer.py`
- `tests/unit/test_kafka_consumer.py`
- `tests/unit/test_event_processing_service.py`
- `pipelines/airflow_dags/edip_orchestration_demo_dag.py`

The related Kafka/Airflow services, volumes, environment variables, and startup commands in `docker-compose.yml`, plus `kafka-python` in dependency files, are update prerequisites rather than standalone deletion targets.

### 11.4 Legacy RAG corpus and generated-output candidate batch

- `docs/phase_5_rag_knowledge_scope.md`
- `docs/rag_source/`
- `docs/policies/`
- `docs/reviews/`
- `docs/sops/warehouse_receiving_sop.md`
- `tests/integration/test_rag_retrieval.py`
- `data/processed/rag/document_metadata.jsonl`
- `data/processed/rag/document_chunks.jsonl`
- `data/processed/rag/document_chunks.csv`
- `data/processed/rag/chunk_embeddings.jsonl`
- `data/processed/rag/chunk_embeddings.csv`
- `data/processed/rag/embedding_manifest.json`
- `data/processed/rag/pinecone_load_manifest.json`
- `data/processed/rag/retrieval_test_results.json`
- `artifacts/reports/rag_frontmatter_fix_report.json`

No external Pinecone deletion is included.

### 11.5 Legacy forecast/model generated-output candidate batch

- `artifacts/forecasts/demand_forecast_scored.csv`
- `artifacts/forecasts/demand_forecast_scoring_summary.json`
- `artifacts/forecasts/replenishment_recommendations.csv`
- `artifacts/forecasts/replenishment_recommendation_summary.json`
- `artifacts/models/demand_forecast_model.joblib`
- `artifacts/models/feature_schema.json`
- `artifacts/models/model_manifest.json`
- `artifacts/reports/model_comparison.csv`
- `artifacts/reports/model_evaluation_report.json`
- `artifacts/reports/demand_forecast_evaluation_report.json`
- `artifacts/reports/demand_forecast_validation_predictions.csv`
- `artifacts/reports/demand_forecast_error_summary.csv`

These generated files must not be removed before the forecast API/service and offline forecast pipeline have an approved replacement or retirement plan.

### 11.6 Obsolete UI scaffold candidate batch

- `ui/README.md`
- `ui/public/file.svg`
- `ui/public/globe.svg`
- `ui/public/next.svg`
- `ui/public/vercel.svg`
- `ui/public/window.svg`

## 12. Assets That Must Be Preserved

The following exact assets are excluded from every proposed deletion batch:

- `pipelines/features/favorita_model_ready.py`
- `notebooks/favorita/01_data_inventory_and_quality.ipynb`
- `notebooks/favorita/02_temporal_sales_and_coverage_eda.ipynb`
- `notebooks/favorita/03_build_favorita_merged_base.ipynb`
- `notebooks/favorita/04_review_merged_dataset_quality.ipynb`
- `notebooks/favorita/05_define_data_cleaning_rules.ipynb`
- `notebooks/favorita/06_create_cleaned_favorita_dataset.ipynb`
- `notebooks/favorita/07_define_leakage_safe_feature_engineering_policy.ipynb`
- `notebooks/favorita/08_build_model_ready_feature_dataset.ipynb`
- `tests/unit/test_favorita_model_ready_features.py`
- `data/raw/favorita-grocery-sales-forecasting/`
- `data/processed/favorita_merged/favorita_merged_base.parquet`
- `data/processed/favorita_cleaned/favorita_cleaned.parquet`
- `data/processed/favorita_cleaned/cleaning_manifest.json`
- `data/processed/favorita_features/smoke/`
- `artifacts/reports/favorita_eda/01_data_inventory_and_quality_summary.json`
- `docs/phase-1/FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md`
- `docs/phase-1/FAVORITA_POST_DOWNLOAD_VERIFICATION.md`
- `docs/architecture/`
- `docs/audits/`
- `monitoring/`
- `app/core/monitoring.py`
- `app/core/logging.py`
- project governance, licensing, contribution, Git-ignore, and AI-use files

## 13. Recommended Cleanup Sequence

1. **Generated housekeeping only.** Remove reproducible caches and Terraform provider downloads. Confirm the worktree remains unchanged because these paths are ignored.
2. **Synthetic generators and superseded data preparation.** Remove the six synthetic generator scripts, old ETL, and `demand_features.py`. Re-run imports and tests to confirm no hidden entrypoint remains.
3. **Kafka/event simulation and Airflow demo.** Remove schema, scripts, event service, tied tests, and DAG in one controlled batch. Update Compose and dependencies in the same change so startup and collection remain coherent.
4. **Forecast replacement before artifact removal.** Establish a Favorita temporal training/evaluation/serving contract. Replace the API/service/tests, then remove legacy model, forecast, recommendation, and evaluation output.
5. **RAG corpus replacement.** Approve a governed source corpus and canonical metadata/index contract. Remove fictional documents and local generated vectors only after migration/retention is decided. Treat remote Pinecone operations as a separate approval.
6. **Workflow and UI rebuild.** Implement durable workflow state, deterministic safety, real identity/authorization, and human approval before retiring the demo contract.
7. **Infrastructure reconciliation.** Rebuild AWS deployment around immutable artifacts and secure secrets. Decide whether Kubernetes evidence is retained, archived, or removed. Migrate Terraform state before any state deletion.
8. **Documentation reconciliation.** Update `README.md`, active runbooks, dependency claims, route inventory, and implementation status. Preserve historical audits as dated evidence.

## 14. Required Validation After Future Cleanup

Every cleanup batch should begin and end with branch and worktree verification. Commands may be adjusted to the approved batch, but the evidence set should include:

```bash
git branch --show-current
git status --short --untracked-files=all
git diff --check
git diff --stat
```

### After cache-only cleanup

```bash
git status --short --untracked-files=all
```

No tracked change is expected.

### After tracked Python/module cleanup

```bash
python -B -c "from app.main import app; print(app.title)"
python -m compileall -q app pipelines scripts tests
pytest --collect-only -q
pytest -q
```

The compilation command normally creates bytecode; use an approved no-bytecode alternative or clean generated cache afterward if the batch requires a clean cache inventory.

### After Kafka/Airflow and dependency cleanup

```bash
grep -RIn "kafka\|KAFKA_\|airflow\|AIRFLOW_" app pipelines scripts tests configs docker-compose.yml requirements*.txt .github docs README.md
docker compose config --quiet
pytest --collect-only -q
pytest -q
```

Expected test-count changes must equal the explicitly approved test deletions and replacements. A lower count without a test-impact reconciliation is a failure.

### After forecast replacement

Validation must cover:

- Favorita feature schema compatibility;
- deterministic temporal train/validation/test splits;
- naive baselines and rolling backtests;
- missing, stale, incompatible, and rolled-back model artifacts;
- uncertainty and abstention behavior;
- source dataset and feature manifest lineage;
- API contract, authorization, and failure behavior; and
- preservation of `tests/unit/test_favorita_model_ready_features.py`.

### After RAG replacement

Validation must cover:

- canonical configuration ownership across application, pipeline, CI, Docker, and Terraform;
- approved source registry and licensing;
- stable document/chunk/corpus identifiers;
- metadata completeness, tenant, and document ACL enforcement;
- embedding model, vector dimension, index, namespace, and corpus compatibility;
- document deletion and re-index behavior;
- source authority, freshness, supersession, conflict, and citation behavior;
- prompt-injection resistance and explicit insufficient-context responses; and
- separate model-free and credentialed live-service evidence.

No credential or secret value should appear in test output or audit evidence.

### After UI/workflow and infrastructure replacement

Validation must include:

- authenticated identity and tenant context;
- fail-closed deterministic safety rules;
- durable approval, revalidation, resume, expiry, and separation of duties;
- no LLM authorization of irreversible actions;
- browser accessibility and safe error/debug behavior;
- immutable image and artifact identifiers;
- secret-manager references rather than plaintext task environment values;
- Terraform format/validate plus plan review against the correct backend; and
- container startup, health, readiness, monitoring, and rollback evidence.

## 15. Unresolved Decisions Requiring Human Approval

The following are not safe to infer from repository contents:

1. Whether the old Pinecone index or namespace still exists, is shared, or has retention value.
2. Which real, licensed, approved documents will form the replacement RAG corpus.
3. The tenant and document-ACL model for RAG and workflow APIs.
4. Whether Kafka or Airflow has a measured future requirement sufficient to justify rebuilding it.
5. Whether raw Kubernetes and local-Kubernetes Terraform should remain as portfolio/learning evidence, be archived, or be deleted.
6. Whether current Terraform state corresponds to active local or AWS resources and where its approved remote backend should be.
7. Whether ignored Terraform lockfiles should become tracked reproducibility assets.
8. The approved production identity provider, approval authority matrix, and deterministic safety thresholds.
9. The source and contract for real inventory, supplier, inbound-shipment, promotion-plan, and operational decision data beyond the Favorita sales dataset.
10. The approved replacement forecast model, evaluation protocol, artifact registry, and deployment promotion process.
11. Whether generic UI primitives and dependencies will be retained in the future product design.
12. The exact deletion batch and rollback point authorized by the repository owner.

## 16. Limitations and Conclusion

This audit proves repository relationships and local evidence at the reviewed commit. It does not prove production operation, external-system ownership, business-policy correctness, model quality on future data, or authorization to delete.

Git history was used as supporting provenance: most synthetic generators, legacy data/RAG configuration, and fictional corpus files share the same March 2026 introduction history, while workflow, UI, and infrastructure arrived in later focused commits. History was never the sole classification reason. Content, data paths, schemas, imports, tests, configuration, entrypoints, and architecture alignment supplied the decisive evidence.

The safest first future action is a separately approved generated-housekeeping batch. Tracked synthetic code should then be removed only in dependency-complete batches. Forecast, RAG, workflow, UI, and AWS assets require replacement contracts before destructive cleanup. Current Favorita assets and canonical governance remain protected throughout.

