# EDIP Initial System Baseline Audit

- Audit date: 29 July 2026
- Audit mode: Comprehensive read-only repository audit
- Repository: enterprise-decision-intelligence-platform-edip
- Branch audited: main
- Baseline purpose: Record the pre-transformation EDIP system condition
- Overall maturity: PARTIALLY IMPLEMENTED — integrated engineering demonstrator
- Production status: Not production ready
- Change status: Historical evidence; no implementation changes performed during the original audit

## 1. Historical baseline notice

> This document records the EDIP system state before Phase 0 implementation. Some findings have since been resolved by later commits. They remain unchanged here to preserve an honest historical baseline. Current repository truth must be determined from later implementation audits, Git history, tests, and current architecture documents.

The repository was audited in strict read-only mode. No tracked or source files were changed, no secret values were displayed, and restructuring is recommended only where evidence demonstrates an operational problem. The final Git status remained clean on `main`.

This baseline must not be read as a statement of the repository's current condition. In particular, the original frontend clean-clone reproducibility defect and stale-path findings remain recorded because they were verified pre-Phase-0 evidence, even where later focused commits have resolved them.

---

## 2. Executive summary

EDIP is an ambitious, technically broad applied-AI prototype with several genuinely implemented components. It is not currently a production system.

Overall maturity: **PARTIALLY IMPLEMENTED — integrated engineering demonstrator**.

Strongest verified capabilities:

- A real FastAPI application with health, metrics, RAG, forecast, and workflow routes in [`app/main.py`](../../app/main.py#L20).
- Deterministic data-generation, feature-engineering, forecasting, recommendation, RAG-ingestion, and Kafka-event code.
- Existing ignored local evidence: synthetic datasets, a trained model, forecast outputs, 134 RAG embeddings, and a five-query retrieval report.
- A working frontend in the current checkout: lint and Next.js production build both pass.
- Meaningful service-level unit testing: 32 executable tests passed in the available environment.
- Terraform for both AWS and local Kubernetes passes `fmt -check` and `validate`.
- Prometheus metrics, Grafana dashboards, alert configuration, Docker Compose, and CI definitions are more than empty scaffolding.

Most serious weaknesses:

1. **The tracked frontend is not clean-clone reproducible.** `.gitignore` ignores the entire `ui/` tree, while tracked code imports an untracked `ui/src/lib/utils.ts`. The current build succeeds only because that ignored local file exists.
2. **The advertised workflow is not deployable from `requirements.txt`.** `langgraph` is used but absent from all primary dependency manifests. The API image can start, but workflow construction will fail.
3. **The AWS/container image excludes the data and artifacts required by the artifact-based forecast service.** `.dockerignore` excludes both `data/` and `artifacts/`.
4. **There is no authentication or authorization.** Workflow, RAG, forecast, metrics, health, debug data, and document metadata are exposed without identity or role enforcement.
5. **Workflow risk reasoning occurs before analytics.** Forecast confidence, stockout risk, and service-level signals cannot influence the normal reasoning stage.
6. **Forecast evaluation is not credible production evidence.** Model selection used only two validation rows; the separate evaluator can fall back to the general feature dataset rather than a dedicated holdout.
7. **RAG governance remains incomplete.** There is no ACL enforcement, prompt-injection testing, conflict-detection algorithm, authority weighting, or answer-grounding evaluation.
8. **The database path is broken from a fresh database.** `database/ddl/01_create_schemas.sql` and `02_extensions.sql` are empty while subsequent DDL assumes the `analytics` schema exists.

Readiness decisions:

- Stakeholder architecture/code review: **possible**, provided the system is explicitly presented as a prototype and the critical truth/reproducibility issues are disclosed.
- Stakeholder operational decision pilot: **not ready**.
- AWS deployment: **not ready**.
- Folder restructuring now: **no broad restructuring required**. Targeted repository cleanup is mandatory; a `src/` migration or full monorepo reorganization would add risk without solving the principal problems.

---

## 3. Audit method and limitations

Inspected:

- All 217 tracked files and root-level ignored/local artifacts.
- Git status, branches, history, tracked files, ignored files, branch divergence, remotes, and sensitive filename/pattern indicators.
- Backend, frontend, RAG, agents, forecasting, data, SQL, Kafka, Airflow, monitoring, Docker, Kubernetes, Terraform, CI, tests, and documentation.
- Ignored local artifacts by name, size, record count, and non-secret summary metadata.

Commands and results:

| Command/check | Result |
|---|---|
| `git status --short --branch` | Clean `main`, aligned with `origin/main` |
| Git history/branches | 57 commits; one backup branch, 11 behind and 1 ahead |
| Redacted tracked-secret indicator scan | No matches for tested key/private-key patterns |
| Sensitive filenames in history | No `.env`, private-key, or Terraform-state filenames found |
| `python -m pytest -q -p no:cacheprovider` | **BROKEN:** 10 collection errors |
| Focused forecast/event unit tests | **32 passed in 0.30s** |
| `npm.cmd run lint` | Passed |
| `npm.cmd run build` | Passed; `/` and `/chat` generated |
| AWS Terraform `fmt -check` and `validate` | Passed |
| local-k8s Terraform `fmt -check` and `validate` | Passed |
| `docker compose config --quiet` | Passed |
| GitHub repository lookup | Repository confirmed public; no combined status entries returned for current commit |
| `gh run list` | Could not run because `gh` is not installed |

No dependencies were installed. A Docker image build was not run because it would execute package installation, which the audit brief prohibits.

External services not exercised:

- OpenAI Responses or Embeddings APIs
- Pinecone live retrieval
- Kafka broker
- PostgreSQL loading
- Airflow runtime
- Prometheus/Grafana runtime
- Kubernetes cluster
- AWS account, ECR, ECS, ALB, IAM, or CloudWatch
- Live browser-to-backend workflow
- Current GitHub Actions logs

The frontend build refreshed only ignored build artifacts. Final tracked Git status remained clean.

---

## 4. Verified repository inventory

| Component | Location | Actual implementation and integration | Status |
|---|---|---|---|
| Git repository | root, `.git/` | Clean `main`; broken internal Codex ref; stale backup branch | **PARTIALLY IMPLEMENTED** |
| FastAPI backend | `app/main.py`, `app/api/` | Ten route operations, Prometheus middleware, CORS, service builders | **VERIFIED WORKING** for import-independent code paths; full runtime not verified |
| Forecast service | `app/services/forecast_service.py` | Synchronously reads ignored forecast/recommendation artifacts | **VERIFIED WORKING** in focused unit tests |
| RAG service | `app/services/rag_*` | OpenAI embeddings/generation plus Pinecone query adapter | **IMPLEMENTED BUT NOT VERIFIED** live |
| RAG ingestion | `scripts/build_rag_metadata.py` through `load_rag_to_pinecone.py` | Real validation, chunking, embedding, and upsert scripts | **IMPLEMENTED BUT NOT VERIFIED** in this audit |
| Multi-stage workflow | `app/agents/`, `langgraph_workflow.py` | Deterministic in-process LangGraph stage graph | **PARTIALLY IMPLEMENTED** |
| Execution layer | `execution_agent.py` | Produces response objects and recommendation labels; no external action | **SIMULATED OR MOCKED** |
| Forecast ML pipeline | `pipelines/{etl,features,training,inference}` | Real scikit-learn/XGBoost-style training and artifact generation | **PARTIALLY IMPLEMENTED** |
| Synthetic data | `scripts/generate_phase_*`, ignored CSVs | Large generated retail datasets with validations | **VERIFIED WORKING** by local artifact presence; generation not rerun |
| Database | `database/ddl`, `database/dml` | Extensive schema/load scripts, but initialization files are empty | **BROKEN** as a clean sequence |
| Kafka | `scripts/kafka_*`, event service, Compose | Producer/consumer and event handling exist; most tests use fakes | **PARTIALLY IMPLEMENTED** |
| Airflow | demo DAG and Compose services | Manual scoring/recommendation DAG with one retry | **CONFIGURATION ONLY** until runtime verified |
| Frontend | `ui/` | Workflow form and decision display integrated with `/agents/workflow/run` | **VERIFIED WORKING** only in current non-reproducible checkout |
| Monitoring | `app/core/monitoring.py`, `monitoring/` | Real metrics and provisioning assets | **IMPLEMENTED BUT NOT VERIFIED** live |
| Docker Compose | `docker-compose.yml` | API, Kafka, Airflow, Postgres, Prometheus, Grafana | **CONFIGURATION ONLY**; syntax verified |
| AWS Terraform | `infra/terraform/aws/` | VPC, ECR, ECS Fargate, ALB, IAM, CloudWatch | **CONFIGURATION ONLY**; static validation passed |
| Kubernetes | `infra/k8s`, local-k8s Terraform | API and monitoring manifests | **CONFIGURATION ONLY** and currently premature |
| CI | `.github/workflows/` | Python tests, Docker build, Terraform validation | **IMPLEMENTED BUT NOT VERIFIED** for current commit |
| Documentation | README, AI usage, contribution docs, RAG corpus | Extensive, but several maturity claims exceed evidence | **PARTIALLY IMPLEMENTED** |

---

## 5. Folder-structure assessment

### Current structural strengths

The principal split is reasonable:

- `app/`: API and application runtime
- `ui/`: independent Next.js frontend
- `pipelines/`: batch ML/data workflows
- `scripts/`: operator-facing generation and loading commands
- `infra/` and `monitoring/`: operational assets
- `tests/`: unit and integration definitions
- `docs/`: documentation and RAG source material

This is already a practical lightweight monorepo. A wholesale move to `backend/`, `frontend/`, or Python `src/` layout is not justified before functional reliability is restored.

### Mandatory structural corrections

| Problem and evidence | Impact | Migration risk and affected paths | Decision |
|---|---|---|---|
| Root [`.gitignore`](../../.gitignore#L197) ignores all `ui/`; `layout.tsx` imports ignored `ui/src/lib/utils.ts` | Clean clone cannot build; future UI additions silently remain untracked | Low. Update ignore rules and add the required file; validate npm build and Docker/CI expectations | **Mandatory, critical** |
| `ui/.git/` is an embedded stale repository with one initial commit and untracked UI work relative to itself | Confusing ownership, tooling, history, and contributor behavior | Low if parent repository is canonical; verify before removing nested metadata | **Mandatory local cleanup** |
| Empty tracked `app/services/app/services` | Misleading path and packaging noise | Very low; confirm no external tooling references it | **Mandatory cleanup** |
| Empty `database/ddl/01_create_schemas.sql` and `02_extensions.sql` | Later SQL assumes `analytics` schema and cannot initialize cleanly | Medium; requires PostgreSQL validation and a documented execution sequence | **Mandatory functional fix** |
| Duplicate `app/core/metrics.py` defines the same Prometheus metric names as `monitoring.py` | Importing both can cause duplicate-registration errors | Low; retain one canonical module and update imports/tests | **Mandatory before expansion** |
| Ignored runtime artifacts are also required by the forecast service | Local behavior differs from container/AWS behavior | Medium; establish artifact packaging or external artifact storage contract | **Mandatory deployment fix** |

### Items that should remain unchanged

- `app/api`, `app/services`, `app/agents`, and `app/core` as top-level runtime domains.
- Separate `ui/`, `infra/`, `monitoring/`, `docs/`, and `tests/`.
- RAG source documents under `docs/`, provided validation is repaired.
- Batch logic in `pipelines/`.
- Operator commands such as data generation, Pinecone loading, and Kafka initialization under `scripts/`.

### Generated/local-only items that should remain ignored

- `.env`, `.env.local`
- `.venv`, `node_modules`, `.next`
- `__pycache__`, `.pytest_cache`, coverage output
- Terraform state and `.terraform/`
- Generated synthetic, processed, exported, model, forecast, and RAG embedding artifacts
- Local logs and temporary files

Ignored artifacts still need reproducible manifests, provenance, checksums, and a deployment delivery mechanism.

### Optional structural improvements

Once the baseline is stable:

- Separate `app/services` into `rag`, `forecast`, `workflow`, and `events` subpackages if ownership or change volume warrants it.
- Add a documented artifact contract such as `artifacts/README.md` or immutable object-storage manifest.
- Convert reusable batch functions into importable application packages while keeping thin CLI scripts.
- Add migration tooling around `database/` instead of managing numbered SQL manually.

No broad `src/` migration is recommended. It would affect imports, Docker `PYTHONPATH`, Airflow paths, tests, script entry points, and CI without addressing the current blockers.

### Safe future migration sequence

1. Repair ignore rules and clean-clone frontend reproducibility.
2. Establish one dependency and runtime matrix.
3. Complete and test database initialization.
4. Consolidate duplicate metrics.
5. Define artifact production, versioning, and deployment boundaries.
6. Add characterization tests for imports, routes, workflow output, and artifact loading.
7. Only then consider small domain-package moves, one module at a time.

---

## 6. Backend audit

Actual routes:

- `GET /health`
- `GET /metrics`
- `GET /rag/health`
- `POST /rag/query`
- `GET /forecast/health`
- `GET /forecast/overview`
- `GET /forecast/recommendations`
- `GET /forecast`
- `GET /agents/workflow/health`
- `POST /agents/workflow/run`

Strengths:

- Transport code is separated from most service logic.
- Pydantic validation exists for RAG and workflow inputs.
- Dependency overrides are possible in API tests.
- Monitoring middleware records count, errors, duration, and in-progress requests.
- RAG errors usually avoid returning upstream exception text.

Weaknesses:

- No API versioning.
- No authentication, authorization, rate limiting, request-size limits, or tenant context.
- Forecast and workflow endpoints disclose internal exception strings, for example [`forecast.py`](../../app/api/forecast.py#L77) and [`agent_workflow.py`](../../app/api/agent_workflow.py#L341).
- Workflow health includes raw initialization exception text.
- `rag_health()` unconditionally returns both readiness fields as `true` without constructing or testing either client.
- Root `/health` is a process liveness check, not readiness.
- The workflow response always includes a large `debug.raw_summary`, rather than gating it to a privileged debug mode.
- Forecast endpoints synchronously load potentially multi-million-row CSV artifacts per request.
- Service builders create new clients/services for requests instead of using explicit lifespan-managed dependencies.
- Logging is human-readable plain text, not structured JSON, and has no correlation ID.
- Linux compatibility is plausible for most Python code, but SQL examples and stored artifact paths contain Windows-style assumptions.

Backend classification: **PARTIALLY IMPLEMENTED**.

---

## 7. Frontend audit

The tracked UI is a single workflow-oriented Next.js application.

Verified current behavior:

- `npm run lint`: passed.
- `npm run build`: passed.
- Static routes `/` and `/chat` compiled.
- The chat page posts to `${NEXT_PUBLIC_API_BASE_URL}/agents/workflow/run`.
- It displays workflow status, output type, risk flags, trace, forecast bounds, confidence, recommendation quantity, service level, and stockout risk.
- Loading and basic error states exist.

Material gaps:

- Clean-clone build is **BROKEN** because `ui/src/lib/utils.ts` is ignored and untracked.
- `require_approval` is hardcoded to `false`; there is no approval UI.
- No authentication/session handling exists.
- Retrieved sources and citations are not presented to the user.
- “Confidence” is displayed without clarifying that the backend derives it from expected service level.
- No separation of retrieval confidence, model confidence, and business risk.
- No abstention or insufficient-evidence visual state beyond generic output text.
- Debug output can display the entire workflow response.
- No frontend test framework or test files were found.
- Metadata remains the create-next-app default in [`layout.tsx`](../../ui/src/app/layout.tsx#L18).
- `ui/README.md` is still the generic Next.js/Vercel template.
- Accessibility is partial: native controls help, but no systematic keyboard, screen-reader, contrast, focus, or automated accessibility evidence exists.

Integration classification: **genuinely connected to one backend workflow endpoint, but demonstrative rather than operational**.

---

## 8. RAG audit

### Implemented

- Frontmatter extraction and schema validation.
- Heading/paragraph-aware chunking.
- OpenAI embedding generation with bounded retries.
- Pinecone index creation and upsert.
- Metadata filters and source objects.
- Score thresholding.
- Explicit no-context and unusable-context responses.
- Prompt instructions to remain grounded and acknowledge weak or conflicting context.
- Local artifacts show 37 documents, 134 chunks, 134 embeddings, and 134 Pinecone-loaded vectors.
- A local retrieval report records five of five cases as passed.

### Deficiencies

- Live OpenAI/Pinecone calls were not run in this audit.
- `tests/integration/test_rag_retrieval.py` defines no pytest test functions; CI invocation of the directory does not execute its `main()` retrieval evaluation.
- Configuration drift exists:
  - ingestion config: `edip-rag-phase6` / `northstar-retail-v1`
  - application/Terraform/local manifest: `edip-rag-index` / `edip-phase-6`
- A local frontmatter audit reported 21 parsing errors and 15 documents that would require frontmatter relocation.
- `min_score` defaults to `0.0`.
- No source-authority scoring or quality-weighted ranking exists.
- No algorithm detects conflicting evidence.
- No claim-to-source entailment or citation correctness evaluation exists.
- No document-level authorization is applied, despite fields such as confidentiality and owner role.
- No prompt-injection sanitization, isolation, canarying, or adversarial test exists.
- No freshness/version invalidation behavior is proven.
- No recall, precision, MRR, nDCG, groundedness, faithfulness, or hallucination metric is reported.
- The workflow’s `RagRetrievalAdapter` calls `answer_question()`, causing an LLM generation call whose answer is discarded, then forwards source previews to the reasoning stage. This adds cost and latency while reducing evidence fidelity.

Classification:

- Ingestion pipeline: **IMPLEMENTED BUT NOT VERIFIED**
- Query service: **IMPLEMENTED BUT NOT VERIFIED**
- Local historical retrieval evidence: **PARTIALLY IMPLEMENTED**
- Source conflict, ACL, injection resistance, and trust evaluation: **NOT FOUND**

---

## 9. Multi-stage workflow audit

The claimed Planner → Retrieval → Reasoning → Analytics → Execution design is implemented as five Python classes in one synchronous LangGraph process. These are useful modular workflow stages, not independently operating agents.

Verified graph:

- Planner is always the entry point.
- Retrieval is conditional.
- Reasoning always follows retrieval or planner.
- Analytics is conditional after reasoning.
- Execution always runs last.
- The graph is acyclic, which inherently prevents loops.

Important findings:

- Planner routing is substring-based and explicitly described as rule-based v1.
- Reasoning is deterministic template and heuristic construction, not LLM reasoning.
- Analytics reads precomputed forecast artifacts; it does not perform request-time model inference.
- Execution creates structured response actions but does not execute external changes.
- No checkpoint store, persistence, resumability, durable state, or human resume token exists.
- `require_approval` only changes the output to `review_required`; it does not implement an approval workflow.
- No per-agent retry, timeout, circuit breaker, fallback model, or failure-state routing exists.
- Exceptions propagate to a 500 response.
- No tool permission model or role-based execution control exists.
- There are no agent-specific unit tests.
- The four workflow API tests replace the actual workflow service with a fake.
- Analytics signals cannot influence reasoning risk flags because reasoning executes first.
- The workflow always reaches execution even when the planner’s declared steps omit execution.
- `langgraph` is absent from runtime requirements, making the default deployed workflow unavailable.

Classification: **PARTIALLY IMPLEMENTED deterministic stage orchestration**; external execution is **SIMULATED OR MOCKED**.

---

## 10. Forecasting and analytics audit

### Implemented strengths

- Synthetic data generation with explicit retail dimensions and facts.
- ETL aggregation and many-to-one merge validation.
- Lag and rolling features shift historical demand to reduce direct leakage.
- Next-day supervised target construction.
- Time-based train/validation split.
- Multiple candidate regressors and deterministic seeds.
- MAE, RMSE, MAPE, WAPE, sMAPE, bias, and R² calculations.
- Model, feature-schema, comparison, scoring, and recommendation artifacts.
- Deterministic replenishment rules and risk scoring.

### Evidence limitations

The existing model comparison reports:

- 254 training rows
- 2 validation rows
- XGBoost selected

This is far too small for reliable model comparison.

The later evaluation report shows 256 rows and near-perfect metrics, but [`evaluate_demand_forecast.py`](../../pipelines/training/evaluate_demand_forecast.py#L191) falls back to `demand_features.parquet` if no dedicated validation dataset exists. Unless an explicit split column is present, [`apply_validation_split_filter`](../../pipelines/training/evaluate_demand_forecast.py#L308) returns the complete dataset. These results therefore cannot be classified as independent holdout performance.

Additional limitations:

- All available data is synthetic.
- No seasonal-naive or last-value business baseline is reported.
- No backtesting across multiple time windows.
- No prediction-interval calibration.
- Forecast bounds are hardcoded to ±10%.
- “Confidence” is populated from expected service level, which conflates distinct concepts.
- The API selects the first recommendation when no requested scope matches.
- The service is artifact-based and ignores request horizon during computation.
- No drift detection, retraining trigger, model registry, model approval, rollback test, or production data contract.
- Model dependencies such as scikit-learn, joblib, XGBoost, and LightGBM are absent from `requirements.txt`.
- The forecast service’s required artifacts are excluded from the Docker image.

Classification: **prototype-level real ML and deterministic analytics, not production-grade forecasting**.

---

## 11. Data and pipeline audit

Data is almost entirely synthetic. This is appropriate for engineering development but must be prominently disclosed in stakeholder and research outputs.

Positive evidence:

- Large local synthetic tables exist.
- Generation scripts contain numerous consistency validations.
- ETL uses explicit grain assumptions and merge validation.
- Kafka event envelopes and business rules have tests.
- RAG metadata/chunk/embedding manifests exist.

Gaps:

- No real source-system connector.
- No formal immutable raw-data manifest or checksum set.
- No end-to-end lineage system.
- No application use of the SQL database.
- The first two database initialization scripts are empty.
- DML uses `psql \copy` with working-directory-dependent relative paths.
- No database migration runner is integrated into Docker, CI, or application startup.
- Kafka “end-to-end” tests use fake consumers/messages rather than a broker.
- Auto-commit is enabled by default; no proven idempotency store, deduplication ledger, dead-letter topic, or replay policy exists.
- Airflow’s DAG is manually triggered and only chains scoring and recommendations.
- Airflow containers install packages during every startup.
- No Kafka-to-Airflow or database-to-model production path is verified.
- Pipeline failure notification and artifact rollback are absent.

Classification:

- Data generation and batch scripts: **PARTIALLY IMPLEMENTED**
- PostgreSQL integration: **SCAFFOLDED OR PLACEHOLDER**
- Kafka production integration: **SIMULATED OR MOCKED**
- Airflow integration: **CONFIGURATION ONLY**

---

## 12. Testing and evaluation audit

There are 120 pytest-style test definitions across the repository, plus a non-pytest RAG retrieval script.

| Validation | Result |
|---|---|
| Full pytest | 10 collection errors; no complete result |
| Focused forecast/event unit tests | 32 passed |
| Frontend lint | Passed |
| Frontend build | Passed only with ignored local dependency |
| Terraform AWS | Format and validation passed |
| Terraform local-k8s | Format and validation passed |
| Compose parsing | Passed |

Full test blockers:

- `ModuleNotFoundError: dotenv`
- `ModuleNotFoundError: yaml`
- `ModuleNotFoundError: openai`
- `ModuleNotFoundError: kafka.vendor.six.moves`

Test-quality limitations:

- Workflow API tests fake the workflow service.
- Forecast API tests fake the forecast service.
- RAG API tests fake retrieval.
- Kafka tests mainly use fake producer/consumer objects.
- Pinecone retrieval evaluation is not a pytest test.
- No frontend tests.
- No agent-level tests.
- No database tests.
- No Airflow DAG execution tests.
- No prompt-injection, authorization, security-header, privacy, concurrency, timeout, retry, load, chaos, or recovery tests.
- No repeated-run consistency test.
- No coverage threshold is enforced in CI.
- No model-evaluation acceptance gate exists.
- Current GitHub Actions execution could not be verified; the GitHub status query returned no entries and `gh` was unavailable.

Testing classification: **meaningful unit coverage around selected services, but insufficient system and reliability evidence**.

---

## 13. Monitoring and observability audit

Implemented assets:

- HTTP count, errors, duration, and in-progress metrics.
- Workflow, RAG, and forecast counters.
- `/metrics`.
- Prometheus scrape configuration.
- Grafana dashboard.
- Two alert rules.
- CloudWatch log group configuration for ECS.

Problems:

- No live stack was verified.
- `app/core/metrics.py` duplicates metric names from `monitoring.py`.
- Alerting only covers API-down and workflow-error count.
- API-down uses `noDataState: OK`, which may suppress alerts when the metric series disappears entirely.
- No notification/contact-point configuration was found.
- No traces, OpenTelemetry wiring, correlation IDs, request IDs, or distributed context.
- No RAG latency/quality, per-agent latency/failure, forecast drift, model freshness, artifact age, token use, cost, approval backlog, or business-outcome metric.
- Execution audit records are returned in memory but not durably stored or protected.
- Dashboard/config content is duplicated across monitoring, Kubernetes YAML, and Terraform, increasing drift risk.
- Logs can include user questions, filters, raw matches, decision payloads, and debug summaries without redaction policy.

Classification: **IMPLEMENTED BUT NOT VERIFIED**, with limited operational depth.

---

## 14. Security and privacy audit

Current security posture is a deployment blocker.

Critical gaps:

- Authentication: **NOT FOUND**
- Authorization/RBAC: **NOT FOUND**
- Tenant/data isolation: **NOT FOUND**
- Document ACL enforcement: **NOT FOUND**
- HTTPS: **NOT FOUND** in AWS Terraform
- Prompt-injection defenses beyond prompt wording: **NOT FOUND**
- Rate limiting and abuse controls: **NOT FOUND**
- Audit-record integrity/persistence: **NOT FOUND**

Additional risks:

- AWS Terraform injects OpenAI and Pinecone keys as ECS plaintext environment values rather than using Secrets Manager or SSM references.
- The public ALB listens on HTTP port 80 from `0.0.0.0/0`.
- ECS tasks receive public IPs.
- CORS defaults combine `allowed_origins="*"` with credentials enabled in Terraform.
- Compose uses known development passwords for Grafana, Postgres, and Airflow.
- Workflow debug data is returned to every caller.
- Forecast/workflow exceptions may expose paths or upstream error details.
- Retrieved document metadata includes governance/confidentiality fields but does not restrict access.
- User questions and event payloads are logged without documented minimization.
- Containers do not declare a non-root user.
- Images use mutable `latest` tags.
- No dependency vulnerability or container scan is configured.
- No security tests or threat model were found.

Positive evidence:

- `.env` and Terraform state are ignored.
- No tested high-confidence secret pattern was found in tracked files.
- No sensitive filename was found in the inspected Git history.
- Terraform variables mark API keys as sensitive.

This is not proof that the entire object history is secret-free; a dedicated history scanner remains warranted.

---

## 15. Infrastructure and AWS-readiness audit

### Verified statically

- AWS and local-k8s Terraform format and validation pass.
- Compose configuration parses.
- Docker CI and Terraform CI definitions exist.
- ECS, ECR, ALB, IAM roles, CloudWatch logging, VPC, and health checks are represented.

### Deployment blockers

- `langgraph` is missing from the image dependencies.
- Required forecast/model/data artifacts are excluded by `.dockerignore`.
- AWS deploys only the API, not the frontend.
- No HTTPS certificate or redirect.
- No WAF, authentication layer, private task networking, NAT/VPC endpoint design, or secrets service.
- Tasks use public subnets and public IPs.
- Image tags default to `latest`.
- Desired count defaults to one; no autoscaling or multi-AZ resilience evidence.
- No deployment rollback strategy or immutable release promotion.
- No backup/recovery design for business/audit data.
- The task role has no explicit capability for a durable artifact or audit store.
- No deployment smoke test or live readiness gate.
- Root `/health` does not check RAG, artifacts, or downstream dependencies.
- Forecast artifact serving would be empty in ECS.
- Monitoring assets are not deployed by the AWS Terraform path.
- Cost budgets, alarms, token limits, and lifecycle controls are incomplete.

Kubernetes judgment: **unnecessary for the current AWS target**. ECS Fargate is already the simpler intended runtime. Maintaining Compose, raw Kubernetes YAML, local-k8s Terraform, and ECS Terraform duplicates operational work before a stable application baseline exists. Keep Kubernetes as optional learning evidence, but do not make it part of the deployment critical path.

AWS readiness: **BROKEN for the intended full EDIP behavior**, although the Terraform syntax itself is valid.

---

## 16. Documentation and claim-verification audit

| Claim | Source | Evidence | Status | Correction required |
|---|---|---|---|---|
| “Full AI Production System” | README line 3 | Major runtime, security, evaluation, and deployment blockers | **BROKEN** | Replace with integrated prototype or production-oriented engineering project |
| “Production-oriented enterprise AI system” | README lines 30–46 | Appropriate as direction, not current maturity | **PARTIALLY IMPLEMENTED** | Add explicit current limitations |
| Multi-agent orchestration | README and `app/agents` | Five deterministic in-process stages exist | **PARTIALLY IMPLEMENTED** | Describe as staged LangGraph workflow |
| XGBoost forecasting | README | Model artifact and pipeline exist | **IMPLEMENTED BUT NOT VERIFIED** | Disclose synthetic data and invalidly small selection holdout |
| Frontend workflow UI implemented/working | README lines 294–305 | Current build passes, but tracked clean clone fails | **BROKEN** as reproducibility claim | Fix tracking, then revalidate from clean clone |
| RAG grounded reasoning | README | Pinecone/OpenAI code and historical artifacts exist | **PARTIALLY IMPLEMENTED** | Disclose missing ACL, injection, conflict, and groundedness evaluation |
| Kafka end-to-end tests | README | Tests use fake broker objects | **SIMULATED OR MOCKED** | Rename as event-flow integration tests with fakes |
| Airflow orchestration | README | Manual demo DAG exists | **CONFIGURATION ONLY** | State that runtime execution is unverified |
| Monitoring and deployment readiness | README | Assets exist; Terraform validates | **CONFIGURATION ONLY** | Avoid “readiness” until live and security gates pass |
| Kubernetes deployment | badges/README | Manifests exist, no cluster evidence | **CONFIGURATION ONLY** | Say manifests included, not deployed |
| Repository structure shown | README | Lists absent or empty paths as substantive components | **STALE OR DUPLICATED** | Reconcile with tracked clean-clone inventory |
| AI-assisted outputs reviewed and tested | README/AI_USAGE | Some outputs tested; complete suite currently cannot collect | **CANNOT VERIFY** as universal statement | Narrow to reviewed “as appropriate” and link validation evidence |

Documentation strengths include MIT licensing, contribution guidance, AI-use disclosure, code of conduct, policy documents, operational playbooks, and limitations sections in several business documents.

Missing or weak documentation:

- Threat model
- Security architecture
- Data protection/privacy assessment
- Model card and dataset card
- Artifact provenance and checksums
- Deployment runbook
- Incident response and rollback
- Cost model
- Research protocol
- Architecture decision records
- Stakeholder review records
- Measured business outcomes

---

## 17. CITP evidence assessment

No SFIA level is assigned.

| Area | Evidence strength | Assessment |
|---|---|---|
| Machine Learning | **Moderate** | Real pipeline and artifacts; validation evidence is weak |
| Software Design | **Moderate** | Clear layers and service boundaries; several integration flaws |
| Programming/Development | **Strong** | Broad Python, TypeScript, SQL, YAML, Terraform implementation |
| Data Engineering | **Moderate** | Synthetic generation, ETL, SQL, Kafka assets; no real source integration |
| Systems Integration and Build | **Moderate** | API/UI/RAG/forecast composition and CI assets; clean build/runtime gaps |
| Solution Architecture | **Moderate** | Broad architecture and trade-off opportunities; excessive technology breadth |
| Testing | **Moderate** | Meaningful tests, but major system paths are mocked or unexecuted |
| Infrastructure Design | **Moderate** | ECS/Kubernetes/Compose/Terraform assets; not operationally validated |
| Availability and Resilience | **Weak** | Health checks and one retry; no proven recovery or redundancy |
| Information Security | **Weak** | Secret ignoring exists, but core identity/access/transport controls are absent |
| AI and Data Ethics | **Weak** | Human-accountability language exists; systematic ethics evidence is missing |
| Emerging Technology Monitoring | **Undocumented** | Technology use is visible, but evaluation of alternatives is not documented |

Professional evidence:

- Responsibility/autonomy: **undocumented**
- Professional judgment: **moderate** in code choices, weak in recorded rationale
- Alternatives/trade-offs: **weak**
- Risk management: **moderate** in policies, weak in engineering controls
- Stakeholder requirements: **weak**
- Ethical consideration: **weak**
- Measurable outcomes: **missing** beyond technical metrics
- Lessons learned/reflection: **missing**
- Peer or stakeholder review: **missing**
- Professional reflection: **missing**

The repository can become useful CITP evidence, but commits and files alone do not demonstrate responsibility, judgment, stakeholder influence, outcomes, or reflection. Those require dated decision records and review evidence.

---

## 18. Research-alignment assessment

Research direction: adaptive and trustworthy multi-agent AI using RAG, uncertainty-aware decisions, and human oversight.

### Current research evidence

- Conditional rule-based routing.
- RAG corpus, chunking, embeddings, and retrieval.
- Deterministic risk flags and escalation labels.
- Structured workflow trace.
- Insufficient-evidence fallback in the RAG service.
- Synthetic scenarios that can support controlled experiments.

### Engineering foundations

- Modular planner/retrieval/reasoning/analytics/execution interfaces.
- Explicit workflow state.
- Artifact-based forecasting.
- Source metadata.
- Audit-shaped outputs.
- Metrics and test scaffolding.

### Missing experimental capability

- Adaptive routing learned or optimized from evidence.
- Separate retrieval, model, and business confidence.
- Calibrated uncertainty.
- Formal abstention threshold and policy.
- Durable human approval/resume.
- Conflicting-source datasets and detection.
- Prompt-injection and malicious-source experiments.
- Agent coordination-failure injection.
- Per-agent and end-to-end benchmark suites.
- Repeated-run and stochastic reliability measurement.
- Comparative baselines: single-agent, no-RAG, no-analytics, deterministic-only.
- Evaluation dataset provenance and statistical power.
- Hypothesis, protocol, acceptance thresholds, and reproducible experiment manifests.

### Potential extensions

- Evidence-quality router using authority, freshness, agreement, and retrieval strength.
- Deterministic safety-policy gate after analytics and before execution.
- Calibrated abstention model.
- Human-approval experiments comparing risk, latency, and decision quality.
- Fault-injection framework for retrieval, model, tool, and state failures.
- Trace-based evaluation of complete-system reliability.

Research alignment is **promising but foundational**, not yet experimental evidence.

---

## 19. Ethics and governance assessment

Implemented or documented:

- Human accountability language in several policy and playbook documents.
- Approval authority and escalation documents.
- Audit-record concepts.
- AI-use disclosure.
- MIT license.
- Some business-document limitations and prohibited pricing behavior.

Documentation-only or absent:

- Privacy and data minimization controls
- PII classification and retention
- Bias and fairness analysis
- Equality, Diversity and Inclusion assessment
- Accessibility evaluation
- Sustainability/energy assessment
- Model and data provenance
- Formal human appeal and override workflow
- Prohibited system uses
- Accountability for model errors
- Legal review of retrieved content
- BCS Code of Conduct mapping
- Responsible Generative AI threat model
- User-facing explanation of limitations
- Governance review evidence

The current synthetic data lowers immediate privacy risk, but the architecture is not ready to receive real enterprise or personal data.

Ethics/governance classification: **mostly documentation direction, with few enforced technical controls**.

---

## 20. Risk register

| ID | Risk and evidence | Likelihood | Impact | Severity | Mitigation | Dependency / owner / phase |
|---|---|---:|---:|---|---|---|
| R1 | Clean-clone UI build fails because `ui/` is ignored and `utils.ts` untracked | High | High | Critical | Repair ignore rules; validate isolated clean clone | Repo maintainer; Phase 0 |
| R2 | Workflow unavailable in deployed runtime because `langgraph` is missing | High | High | Critical | Define/runtime-lock dependency; container smoke test | Backend owner; Phase 1 |
| R3 | ECS forecast/workflow has no artifacts because image excludes them | High | High | Critical | Immutable artifact packaging or S3-based loading | ML/platform owners; Phase 1/7 |
| R4 | Unauthenticated public decision APIs and debug data | High | Critical | Critical | Identity, RBAC, debug gating, rate limits | Security/backend; Phase 6 |
| R5 | Analytics risk cannot affect reasoning due graph order | High | High | High | Redesign sequence or add post-analytics safety gate | AI workflow owner; Phase 3 |
| R6 | Forecast metrics overstate model quality | High | High | High | Dedicated temporal holdout and rolling backtest | ML owner; Phase 1/5 |
| R7 | RAG may expose confidential documents | Medium | Critical | Critical | Enforce caller/document ACLs before retrieval | Security/RAG; Phase 2/6 |
| R8 | Prompt-injected documents influence answers | Medium | High | High | Content isolation, injection tests, deterministic policy gate | RAG/security; Phase 2/5 |
| R9 | Database initialization fails | High | Medium | High | Complete schema scripts and database integration test | Data owner; Phase 1 |
| R10 | Secrets appear in ECS env/Terraform state | Medium | High | High | Secrets Manager/SSM references and state controls | Platform/security; Phase 7 |
| R11 | Kafka duplicate/lost processing due auto-commit and no idempotency | Medium | High | High | Manual commit, idempotency ledger, DLQ/replay tests | Data/platform; Phase 3/5 |
| R12 | Alerting misses total target disappearance | Medium | High | High | Correct no-data behavior and test notifications | SRE; Phase 6/7 |
| R13 | Debug/error responses leak internal data | High | Medium | High | Redaction, stable error codes, privileged diagnostics | Backend/security; Phase 1/6 |
| R14 | Four deployment stacks cause maintenance drift | High | Medium | Medium | Make ECS canonical; treat Kubernetes as optional | Architect/platform; Phase 0/7 |
| R15 | Mutable image tags prevent deterministic rollback | High | High | High | Deploy digest or commit SHA; retain releases | Platform; Phase 7 |

---

## 21. Dependency and complexity assessment

Necessary current runtime dependencies:

- FastAPI, Uvicorn, Pydantic
- pandas/numpy for artifact-serving paths
- OpenAI and Pinecone for current RAG architecture
- Prometheus client
- python-dotenv and PyYAML
- Kafka client only where event scripts run

Missing or inconsistent:

- `langgraph` is required by the workflow but absent.
- scikit-learn/joblib/XGBoost/LightGBM are needed for ML pipelines but absent from the primary runtime manifest.
- CI Python is 3.11 while Docker uses 3.12.
- Local `kafka-python==2.0.2` fails under the active Python 3.12 interpreter.
- `requirements_full.txt` contains a very large environment including Airflow, Jupyter, multiple web frameworks, ML libraries, observability stacks, and notebook tooling. It is not a suitable production runtime lock.

Premature or duplicated technologies:

- Raw Kubernetes plus Terraform-managed Kubernetes plus ECS plus Compose.
- Duplicate monitoring definitions across application, Compose, K8s, and Terraform.
- Both `metrics.py` and `monitoring.py`.
- Airflow for a two-step manually triggered pipeline.
- PostgreSQL warehouse scripts not connected to the application.

Hidden coupling:

- API behavior depends on ignored local artifacts.
- Workflow construction depends on an undeclared package.
- Agent retrieval calls an answer-generating RAG interface instead of a retrieval-only interface.
- SQL loading depends on the current working directory.
- UI build depends on an ignored file.
- Airflow depends on runtime package installation and mounted repository state.

Vendor lock-in:

- OpenAI embeddings/generation
- Pinecone vector storage
- AWS ECS/ECR/ALB
- Moderate and manageable if interfaces and evaluation fixtures are preserved

Cost risks:

- RAG agent performs an unnecessary generation call before its own reasoning.
- No token, request, or monthly spend limits.
- Always-on ALB, ECS, NAT if later added, Pinecone, Airflow, Prometheus/Grafana, and Kafka can exceed the value of the current prototype.
- Kubernetes would increase operational cost without a proven scaling requirement.

---

## 22. Prioritised findings

### Critical

1. Repair tracked frontend reproducibility.
2. Add and lock the actual workflow runtime dependency.
3. Define how forecast/model artifacts reach container and AWS environments.
4. Add authentication, authorization, and document access control.
5. Stop presenting current deployment assets as a deployable full production system.
6. Establish secure secret and HTTPS handling before AWS.

### High priority

- Correct workflow ordering or add a post-analytics deterministic safety gate.
- Produce credible temporal forecast evaluation.
- Complete database initialization.
- Remove raw debug and exception leakage.
- Add agent/workflow tests using real stage objects.
- Make RAG evaluation executable in CI.
- Add prompt-injection, conflicting-source, and insufficient-evidence tests.
- Implement durable approval and audit storage.
- Establish Kafka idempotency and replay behavior.
- Correct alert no-data behavior.

### Medium priority

- Consolidate monitoring definitions.
- Pin container image versions.
- Add structured logging and correlation IDs.
- Add frontend tests and accessibility checks.
- Reconcile README and UI documentation.
- Create model/dataset cards and provenance manifests.
- Remove stale nested Git and backup/ref metadata after review.

### Optional

- Python `src/` layout.
- Full backend/frontend top-level renaming.
- Kubernetes deployment.
- Learned adaptive routing.
- Additional agent autonomy.
- New databases or vector stores.
- More dashboards before core reliability is measured.

---

## 23. Phased upgrade roadmap

> **Historical-roadmap note:** The current EDIP implementation plan has since been refined into smaller repository migration batches. The original roadmap is retained as historical evidence and must not replace the current authoritative plan.

### Phase 0 — Repository truth and cleanup

Objective: make tracked source reproducible and claims accurate.

Work: repair UI ignore rules, track required UI files, clean nested Git, remove bogus empty file, reconcile README, declare canonical runtimes and deployment path.

Acceptance: clean clone installs from documented manifests; frontend lint/build and backend import checks pass; documentation matches evidence.

Effort: small to medium. Excludes feature additions.

### Phase 1 — Stable local end-to-end baseline

Objective: one deterministic local workflow that works without hidden state.

Work: add LangGraph dependency, complete database initialization, define artifact fixtures, container smoke test, real workflow tests, stable error responses.

Acceptance: documented local command runs UI → API → real agent objects → deterministic artifact-backed result from a clean clone.

Effort: medium.

### Phase 2 — RAG and evidence reliability

Objective: trustworthy retrieval behavior.

Work: fix frontmatter, unify index/namespace, retrieval-only adapter, quality/authority metadata, ACL filtering, conflict fixtures, injection controls.

Acceptance: versioned evaluation set with retrieval metrics, ACL tests, abstention cases, and citation checks.

Effort: medium to high.

### Phase 3 — Multi-stage reliability and deterministic controls

Objective: make stage orchestration failure-aware.

Work: reorder reasoning/analytics or add a safety gate, stage timeouts, bounded retries, explicit failure states, Kafka idempotency, tool permission model.

Acceptance: every failure produces a controlled state; no unsafe action is marked ready.

Effort: high.

### Phase 4 — Uncertainty, abstention, and human approval

Objective: separate confidence and risk.

Work: retrieval confidence, calibrated model uncertainty, business-risk score, abstention policy, durable approval/resume state, role enforcement.

Acceptance: deterministic tests demonstrate act, abstain, request evidence, and request approval outcomes.

Effort: high.

### Phase 5 — Evaluation and failure testing

Objective: produce defensible reliability evidence.

Work: temporal backtests, naive baselines, per-agent evaluation, complete-system scenarios, repeated runs, prompt injection, conflict, outage, timeout, and recovery tests.

Acceptance: versioned evaluation report with thresholds and reproducible commands.

Effort: high.

### Phase 6 — Security, governance, and stakeholder review

Objective: safe controlled review.

Work: authentication, RBAC, privacy assessment, threat model, audit protection, debug gating, accessibility, incident runbook, stakeholder review pack.

Acceptance: security and governance checklist passes; named reviewers approve pilot scope.

Effort: high.

### Phase 7 — AWS production deployment

Objective: secure, reversible AWS deployment.

Work: immutable image/artifact promotion, Secrets Manager, HTTPS, private ECS tasks, autoscaling, alarms, budgets, deployment smoke tests, rollback.

Acceptance: deployment and rollback proven; live readiness checks include downstream dependencies; no mutable tags or plaintext secrets.

Effort: high. Kubernetes explicitly excluded unless scaling evidence later justifies it.

### Phase 8 — Final validation, CITP evidence, and research reporting

Objective: convert engineering results into professional and research evidence.

Work: decision records, trade-offs, stakeholder outcomes, ethics reflection, experimental report, lessons learned, evidence index.

Acceptance: every claim links to code, test, review, metric, or deployment evidence.

Effort: medium.

This sequence is achievable before 31 December 2026 if infrastructure expansion remains deferred until the baseline and evaluation gates pass.

---

## 24. Recommended stakeholder-review version

The minimum credible stakeholder version should be a controlled local or protected test-environment demonstrator.

Must work:

- Clean-clone setup.
- Authenticated user with at least viewer/planner/approver roles.
- One end-to-end inventory scenario.
- Retrieval with visible citations and ACL filtering.
- Forecast/recommendation from a versioned artifact.
- Separate retrieval confidence, forecast uncertainty, and business risk.
- Explicit abstain/insufficient-evidence result.
- Human approval request and durable decision record.
- Trace, latency, error, and approval metrics.
- Reproducible evaluation report.

May remain out of scope:

- Kafka production broker
- Airflow production scheduling
- Kubernetes
- Automated operational execution
- Multiple forecasting models
- Real-time streaming
- Broad multi-domain RAG
- Autonomous agent behavior

Evidence to collect:

- Clean-clone build log
- Test and coverage report
- Versioned dataset/model/RAG manifests
- Scenario results, including failures
- Security and privacy checklist
- Stakeholder decisions and action items
- Measured latency, groundedness, abstention, and approval outcomes

Review participants:

- Demand/inventory planner
- Business owner
- Data/ML engineer
- Software/platform engineer
- Security/privacy reviewer
- Accessibility representative
- Independent technical reviewer

Success criteria:

- No unsupported answer is presented as confident.
- Every recommendation links to evidence and model/artifact version.
- High-risk decisions require approval.
- Unauthorized documents cannot be retrieved.
- Failure states are visible and recoverable.
- Stakeholders can understand and challenge the recommendation.
- All advertised behavior is reproduced from the reviewed release.

---

## 25. Immediate next actions

Strict execution order:

1. Correct the root UI ignore rule and track every frontend dependency required by a clean clone.
2. Reproduce frontend lint/build from an isolated clean checkout.
3. Reconcile `requirements.txt`, CI Python, and Docker Python; add the actual LangGraph runtime dependency.
4. Add a clean-container smoke test covering `/health`, `/forecast/health`, `/rag/health`, and workflow health.
5. Define a versioned forecast/RAG artifact delivery contract that works outside the developer checkout.
6. Correct README production, validation, Kafka, Airflow, Kubernetes, and frontend claims.
7. Complete and test database schema initialization from an empty PostgreSQL instance.
8. Correct workflow ordering and introduce a deterministic post-analytics safety/approval gate.
9. Replace the two-row model-selection evidence with a dedicated temporal holdout and rolling backtest.
10. Add authentication, RBAC, document ACLs, debug gating, HTTPS, and secure secret injection before any AWS deployment.

No repository changes were made during this audit.

---

## 26. Baseline-to-transformation evidence use

This document is the fixed initial point for demonstrating controlled transformation. It should be linked to later evidence through the following chain:

```text
Initial baseline finding
→ risk or weakness
→ architecture decision
→ implementation batch
→ validation evidence
→ stakeholder outcome
→ professional reflection
```

The chain prevents later success from erasing the original problem and prevents historical findings from being mistaken for current repository truth. Each implementation record should identify the baseline finding it addresses, state the chosen boundary and alternatives, preserve commands and results, and record the outcome against acceptance criteria.

| Baseline evidence | Transformation evidence | Recorded position at creation of this baseline |
|---|---|---|
| R1 — Clean-clone UI failure | Phase 0 Batch 0A — Frontend reproducibility | **Resolved** by later focused implementation evidence; retain R1 here as the original finding |
| Empty anomalous and redundant stale paths | Phase 0 Batch 0B — Unambiguous stale-path cleanup | **Resolved** by later focused implementation evidence; retain the original inventory here |
| Duplicate metric ownership | Phase 0 Batch 0C — Monitoring ownership | **Pending**; determine current truth from the later batch record |
| RAG filenames, index, and namespace drift | Phase 0 Batch 0D — RAG configuration contract | **Pending** |
| Fragmented online RAG ownership | Phase 0 Batch 0E — Online RAG package | **Pending** |
| Workflow-stage and graph ownership | Phase 0 Batch 0F — Workflow package | **Pending** |

A future evidence index should link each row to the relevant architecture decision, commit or pull request, validation log, review outcome, and reflection. Status changes belong in those later records, not as edits that rewrite this baseline.

---

## 27. Professional reflection

The original audit required systems thinking because EDIP combined application code, AI workflows, RAG, forecasting, data pipelines, event processing, observability, and several deployment approaches. A passing build or the presence of infrastructure files could not by itself establish production readiness. The audit therefore separated **implemented**, **verified**, **partially implemented**, **simulated or mocked**, **configuration only**, **broken**, and **not found** evidence.

Preserving the initial findings after later repairs is professionally important. Retrospectively removing resolved weaknesses would obscure the reasoning that justified the work, weaken traceability, and make improvement appear inevitable rather than controlled. Conversely, treating this baseline as current truth would ignore subsequent evidence. The appropriate professional record connects the original observation to a risk, an explicit decision, a bounded implementation batch, proportionate validation, stakeholder consequences, and reflection.

The move from broad roadmap phases to small repository migration batches illustrates controlled change. Focused batches reduce causal ambiguity, limit rollback scope, and allow failures or environmental constraints to be reported honestly. They also make it possible to distinguish technical activity from professional evidence: code and commits demonstrate implementation, but do not alone prove responsibility, judgment, stakeholder influence, ethical consideration, measurable outcomes, or learning.

No SFIA level is assigned by this document. Its value for BCS CITP evidence lies in the traceable record of the initial system, the limitations acknowledged at the time, the risks used to prioritise change, and the disciplined evidence chain expected from subsequent work.

