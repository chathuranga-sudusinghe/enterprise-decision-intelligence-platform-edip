# EDIP Legacy Synthetic-Asset Cleanup Completion Review

- Review date: 14 August 2026
- Repository: `enterprise_decision_intelligence_platform_EDIP`
- Documentation branch: `docs/research-governance-and-cleanup-completion`
- Reviewed synchronized checkpoint: `0833cfa79852d232c5bf809a7c7c3d3fa13b3ab7`
- Decision scope: Closure of the approved legacy synthetic-asset cleanup only
- Result: **CLOSED for the legacy cleanup scope; replacement capabilities remain open**

> This review records the transition from the obsolete synthetic NorthStar implementation to the current real-data Favorita foundation. It does not certify EDIP as production-ready or research-ready, and it does not claim that forecast, RAG or governed workflow replacements exist.

## 1. Purpose, evidence and limitations

The original problem and proposed classification are recorded in the [Legacy Synthetic-Data Asset Audit](LEGACY_SYNTHETIC_ASSET_AUDIT.md). That audit was a proposal, not deletion approval or implementation evidence. This completion review links the later, separately scoped cleanup commits and merged pull requests to the proposal while preserving the original audit unchanged.

Evidence reviewed for this record included current repository contents, local Git history and diffs, the cleanup audit, retained architecture/governance records, local validation results recorded during the cleanup batches, and read-only GitHub pull-request/check metadata for PRs #43–#50.

Evidence boundaries:

- Git proves tracked changes and merge ancestry, not deletion of ignored local files.
- The ignored artifact/cache cleanup was observed locally during the cleanup work but is not represented by Git commits.
- Local pytest evidence is model-free repository evidence; it does not prove live OpenAI, Pinecone, Kafka, Airflow, PostgreSQL, AWS or Kubernetes operation.
- GitHub Docker checks prove image construction only. Terraform checks prove formatting/static configuration validity only.
- No external Pinecone index or namespace was deleted or verified.
- This documentation review did not rewrite a Parquet dataset, retrain a model, deploy infrastructure or rerun live services.

## 2. Cleanup sequence and Git evidence

| Stage | Development PR | Main checkpoint PR | Cleanup commit | Verified repository outcome |
|---|---:|---:|---|---|
| Audit documentation | [#43](https://github.com/chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip/pull/43) | [#44](https://github.com/chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip/pull/44) | `c65e2e3f09f6532c1cedc9aa7ef398537a7b6623` | Added the approved audit; no cleanup deletion was represented as complete |
| Synthetic generators, ETL and feature module | [#45](https://github.com/chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip/pull/45) | [#46](https://github.com/chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip/pull/46) | `133722be66de325f2df48c4e1f3947a988f66871` | Deleted eight synthetic-only tracked pipeline files |
| Kafka/event simulation and Airflow demo | [#47](https://github.com/chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip/pull/47) | [#48](https://github.com/chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip/pull/48) | `3079392500f21523d0e8880f6adce9c7db3d098d` | Removed the dependency-complete demo batch and active Compose/dependency claims |
| Remaining forecast, RAG and demo workflow | [#49](https://github.com/chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip/pull/49) | [#50](https://github.com/chathuranga-sudusinghe/enterprise-decision-intelligence-platform-edip/pull/50) | `e8512e7b362c4ef8eb27ae1915c6cd02ad7fa50f` | Removed obsolete runtimes, corpus, pipelines and tied tests; reconciled active configuration |
| Synchronized reviewed checkpoint | — | #50 merge | `0833cfa79852d232c5bf809a7c7c3d3fa13b3ab7` | Current reviewed checkpoint containing the four stages above |

Read-only GitHub evidence confirmed that PRs #43–#50 are merged and that their heads/merge commits match the local ancestry. It did **not** show an all-green check suite: Docker build checks succeeded for the cleanup PR sequence, while the `Run unit and integration tests` workflow failed at its unit-test step and therefore did not run its integration step. PRs #49/#50 additionally show successful AWS and local-k8s Terraform static checks. These CI results are recorded without converting a failed workflow into a pass or static checks into deployment evidence.

## 3. Exact tracked capability groups removed

### 3.1 Synthetic source generation and preparation (`133722b`)

- `scripts/generate_phase_1_dimensions.py`
- `scripts/generate_phase_1_procurement_inventory.py`
- `scripts/generate_phase_2_sales_commercial.py`
- `scripts/generate_phase_2_promotions_price_history.py`
- `scripts/generate_phase_3_forecast_replenishment.py`
- `scripts/generate_phase_4_planner_overrides_decision_logs.py`
- `pipelines/etl/build_training_dataset.py`
- `pipelines/features/demand_features.py`

### 3.2 Kafka/event simulation and Airflow demo (`3079392`)

The tracked source/configuration group comprised:

- `configs/kafka_event_schema.yaml`
- `scripts/generate_phase_6_kafka_events.py`
- `scripts/init_kafka_topics.py`
- `scripts/kafka_producer.py`
- `scripts/kafka_consumer.py`
- `app/services/event_processing_service.py`
- `pipelines/airflow_dags/edip_orchestration_demo_dag.py`
- `tests/integration/test_kafka_event_generation.py`
- `tests/integration/test_kafka_end_to_end_flow.py`
- `tests/unit/test_kafka_producer.py`
- `tests/unit/test_kafka_consumer.py`
- `tests/unit/test_event_processing_service.py`

The same dependency-complete change removed Kafka/Airflow services, startup dependencies, commands, environment variables and dedicated volumes from `docker-compose.yml`; retained PostgreSQL as independent EDIP persistence; removed `kafka-python` from runtime requirements; and updated active README claims. Prometheus, Grafana, API and unrelated services were preserved.

### 3.3 Legacy forecast capability (`e8512e7`)

- `app/api/forecast.py`
- `app/services/forecast_service.py`
- `pipelines/inference/generate_recommendations.py`
- `pipelines/inference/score_demand_forecast.py`
- `pipelines/training/evaluate_demand_forecast.py`
- `pipelines/training/train_demand_forecast.py`
- `tests/integration/test_forecast_api.py`
- `tests/unit/test_forecast_service.py`

### 3.4 Legacy RAG capability and synthetic corpus (`e8512e7`)

- runtime: `app/api/rag.py`, `app/schemas/rag.py`, `app/services/rag_generation_service.py`, `app/services/rag_query_service.py`;
- ingestion configuration: `configs/rag_ingestion_config.yaml`, `configs/rag_metadata_schema.yaml`;
- ingestion scripts: `scripts/build_rag_metadata.py`, `scripts/chunk_rag_documents.py`, `scripts/embed_rag_chunks.py`, `scripts/load_rag_to_pinecone.py`;
- tied tests: `tests/integration/test_rag_api.py`, `tests/integration/test_rag_retrieval.py`, `tests/unit/test_rag_generation_service.py`, `tests/unit/test_rag_query_service.py`;
- synthetic scope/corpus: `docs/phase_5_rag_knowledge_scope.md`, five files under `docs/policies/`, 28 files under `docs/rag_source/`, three files under `docs/reviews/`, and `docs/sops/warehouse_receiving_sop.md`.

No remote Pinecone operation was included.

### 3.5 Demo agent/workflow capability (`e8512e7`)

- `app/api/agent_workflow.py`
- `app/services/agent_workflow_service.py`
- `app/agents/analytics_agent.py`
- `app/agents/execution_agent.py`
- `app/agents/langgraph_workflow.py`
- `app/agents/planner_agent.py`
- `app/agents/reasoning_agent.py`
- `app/agents/retrieval_agent.py`
- `scripts/run_agent_workflow_demo.py`
- `tests/integration/test_agent_workflow_api.py`

The commit also removed retired RAG settings and router registrations from active application, CI and AWS Terraform configuration, updated the runtime dependency contract test to test the retained LangGraph foundation rather than the deleted demo graph, and reconciled README/current configuration claims.

## 4. Ignored local generated artifacts removed

The cleanup removed the following ignored local synthetic-output groups after their producers/consumers were retired:

- four files under `artifacts/forecasts/`;
- three files under `artifacts/models/`;
- six legacy files directly under `artifacts/reports/`;
- eight generated RAG files under `data/processed/rag/`;
- repository Python `__pycache__`/`.pyc` output outside retained environments, `.coverage`, and obsolete `tmp/` bytecode content.

The exact artifact names are preserved in sections 10 and 11 of the original audit. These paths were ignored/untracked, so their local deletion is **not represented by any Git commit** and cannot be reconstructed from the cleanup commits alone. The inaccessible local `.pytest_cache/` was not falsely recorded as deleted; it remained an ignored cache residual at the time of cleanup because its Windows ACL prevented removal. Environment, Terraform-state/lock, UI dependency and unrelated local files were outside this cleanup.

## 5. Protected Favorita and governance assets

The cleanup preserved the current real-data foundation, including:

- all Favorita Notebooks 01–08, especially `notebooks/favorita/08_build_model_ready_feature_dataset.ipynb`;
- `pipelines/features/favorita_model_ready.py`;
- `tests/unit/test_favorita_model_ready_features.py`;
- raw, merged, cleaned and model-ready Favorita dataset locations and their manifests;
- Favorita cleaning, feature-contract, governance and audit evidence;
- [Favorita Dataset Source and Governance](../phase-1/FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md);
- [Favorita Post-Download Verification](../phase-1/FAVORITA_POST_DOWNLOAD_VERIFICATION.md);
- canonical architecture, licensing, contribution and historical audit records; and
- `artifacts/reports/favorita_eda/`, including its current Favorita EDA evidence.

Preservation means these assets were excluded from the cleanup; it does not make the restricted Favorita dataset redistributable or convert partial post-download acceptance into research/production readiness.

## 6. Current API and test baseline

After retirement of the legacy routers, the current FastAPI boundary consists of FastAPI-generated documentation/OpenAPI routes plus EDIP `/health` and `/metrics`. There is no active forecast, RAG or agent-workflow route.

The final local validation baseline recorded during cleanup was:

| Validation | Result |
|---|---:|
| Focused Favorita feature contract | 4 passed |
| Complete test collection | 9 tests collected |
| Complete remaining suite | 9 passed |

This is a local repository baseline. It does not override the failed GitHub unit-test workflow noted in section 2; the environments and executions are separate evidence surfaces.

### Historical test-count reconciliation

| Point | Collected tests | Change | Explanation |
|---|---:|---:|---|
| Legacy audit baseline | 172 | — | Full synthetic-era suite |
| After generator/ETL/feature source cleanup | 172 | 0 | No tests were deleted in that batch |
| After Kafka/Airflow demo cleanup | 78 | -94 | Five removed test files contained 94 collected cases |
| After forecast/RAG/workflow cleanup | 9 | -69 | Forecast 29, RAG 35, workflow 4 and one retired workflow-specific runtime contract case |
| Final baseline | 9 | -163 total | `94 + 69 = 163`; all remaining tests passed locally |

The reduction is intentional deletion of obsolete contract tests with the capabilities they protected, not an assertion that 163 current tests were fixed or replaced.

## 7. Current dependency and configuration truth

The cleanup reconciled active dependencies and configuration with the retained boundary:

- `kafka-python` was removed after repository-wide inspection found no retained imports;
- legacy RAG runtime packages and settings (`openai`, `pinecone`, `PyYAML` and RAG environment/configuration fields) were removed from the active dependency/configuration surfaces that used them;
- LangGraph remains declared and contract-tested as a target workflow foundation, but no demo workflow implementation is registered;
- Compose contains no Kafka or Airflow service, dependency, command, environment or dedicated volume; PostgreSQL remains independent;
- application startup registers no legacy forecast, RAG or workflow router;
- CI no longer injects obsolete RAG placeholder settings; and
- AWS Terraform no longer projects obsolete RAG variables into the ECS task.

These changes describe current repository configuration. They do not prove live container startup, database initialization or cloud deployment.

## 8. Current repository truth and operational supersession

At the reviewed checkpoint:

- there is no active legacy forecast runtime or model artifact;
- there is no active RAG implementation, synthetic corpus or local generated vector set;
- there is no active demo agent workflow;
- there is no Kafka event-simulation or Airflow orchestration demo; and
- governed Favorita forecast, RAG and workflow replacements have not yet been built.

The following retained records are now operationally superseded for current runtime truth but remain unchanged as historical evidence:

- [Phase 1 Batch 1A Runtime Dependency Contract](../phase-1/PHASE_1_BATCH_1A_RUNTIME_DEPENDENCY_CONTRACT.md), which recorded the then-active demo workflow dependency boundary; and
- [Phase 1 Batch 1A2 Kafka Python 3.12 Compatibility](../phase-1/PHASE_1_BATCH_1A2_KAFKA_PYTHON312_COMPATIBILITY.md), which recorded the then-active Kafka compatibility work.

The initial/system/structure/Phase 0 and RAG/endpoint audits similarly remain dated evidence of what existed when inspected. This completion review supplies the later resolution link; it does not rewrite them.

## 9. Remaining work and limitations

Legacy removal does not implement or complete the approved forecasting backlog sequence:

| Work item | Approved forecasting scope | Required evidence before closure |
|---|---|---|
| SCRUM-13 | Define temporal validation and backtesting | Approved chronological validation/backtesting protocol, leakage controls, rolling-origin design, metrics and acceptance criteria |
| SCRUM-14 | Build forecasting baselines | Reproducible naive and statistical baseline results evaluated under the SCRUM-13 protocol |
| SCRUM-15 | Train first global forecasting model | Versioned first global model, Favorita data/feature lineage, comparison with approved baselines, uncertainty/error analysis and reproducibility evidence |

Replacement RAG and governed agent/workflow capabilities remain unresolved target-architecture work. They are not assigned to SCRUM-14 or SCRUM-15 and require separately approved future work items before implementation.

Remaining limitations are explicit:

- no new Favorita forecast model or serving runtime exists;
- no replacement RAG system or approved replacement corpus exists;
- no governed agent workflow exists;
- no production-readiness, research-readiness, CITP-award, SFIA-level or PhD-novelty claim is made;
- no live external-service or deployment evidence was produced by cleanup;
- this documentation review did not run local Terraform CLI validation; current GitHub evidence for PRs #49/#50 shows successful AWS and local-k8s **static** Terraform checks, not deployment; and
- the residual inaccessible `.pytest_cache/` is ordinary ignored local state, not an active legacy capability.

## 10. Rollback and reversibility

Tracked cleanup is recoverable through Git history. The preferred rollback is a focused revert of the relevant cleanup commit, in reverse dependency order when restoring more than one batch:

1. revert `e8512e7` for forecast/RAG/workflow source and configuration;
2. revert `3079392` for Kafka/Airflow source, dependencies and Compose;
3. revert `133722b` for synthetic generators/ETL/features.

Restoring a tracked producer/consumer does not automatically restore ignored artifacts, credentials, external indexes or external services. Those require separate provenance, compatibility, security and authorization checks. Reverting all legacy code would also conflict with the approved real-data direction unless a new human decision justified it.

## 11. Professional reflection

The cleanup required architecture judgement rather than filename-based deletion. Capabilities still present in the target architecture were separated from synthetic-coupled implementations: forecast, RAG and controlled workflows remain legitimate goals, while their NorthStar/demo implementations were retired instead of being represented as reusable Favorita systems.

Evidence discipline required distinguishing the audit proposal, tracked commits, ignored local deletion, local tests, GitHub checks and live-operation evidence. Recording the failed GitHub test workflow alongside the passing local 4/9/9 baseline avoids manufacturing a single “green” conclusion from different environments. Preserving the original audits and negative/blocked evidence protects research integrity and explains why the decisions were made.

Small dependency-complete batches improved reversibility: generators, Kafka/Airflow, then forecast/RAG/workflow could each be reviewed and reverted without obscuring the affected boundary. The principal lesson is that removing misleading demonstrations can strengthen the evidence base even while reducing code and test counts, provided current capabilities, unresolved target work and validation limits are stated precisely.

## 12. Closure decision

**The approved legacy synthetic-asset cleanup is complete at synchronized checkpoint `0833cfa79852d232c5bf809a7c7c3d3fa13b3ab7`.**

This decision closes only the audited removal and reconciliation scope. It does not approve or complete SCRUM-13, SCRUM-14 or SCRUM-15, certify production/research readiness, or authorize deployment, external-index operations, data redistribution, commit, push or release.
