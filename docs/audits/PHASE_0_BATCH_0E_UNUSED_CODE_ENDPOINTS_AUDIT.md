# EDIP Phase 0 Batch 0E — Unused Code and Endpoint Cleanup Audit

- Audit date: 30 July 2026
- Audit mode: Read-only
- Repository: enterprise-decision-intelligence-platform-edip
- Branch audited: `chore/phase-0-batch-0e-unused-code-endpoints`
- Purpose: Endpoint ownership, reference, reachability, and safe unused-code assessment
- Result type: Audit evidence; not an implementation record

> This report records a read-only repository audit. No runtime code, endpoint, service, test, frontend file, script, pipeline, configuration file, or existing audit file was changed as part of the inspection.

## 1. Purpose and Scope

This audit examined EDIP application endpoints and application-owned code before Phase 0 Batch 0E. Its objectives were to:

- inventory every route registered by the FastAPI application;
- identify repository evidence for frontend, test, script, pipeline, infrastructure, monitoring, and documented use;
- identify unused, duplicate, stale, or unreachable application code;
- identify modules with no imports or operational references;
- separate confirmed unused items from items whose external use is uncertain;
- recommend only small, safe Phase 0 deletions;
- avoid major refactoring or Version 2 implementation.

The audit did not delete code, alter endpoint behaviour, change route contracts, update tests, or make frontend changes.

## 2. Files Inspected

The inspection covered:

- `app/main.py`
- `app/api/agent_workflow.py`
- `app/api/forecast.py`
- `app/api/rag.py`
- all modules under `app/services/`
- all modules under `app/core/`
- application-agent imports needed to confirm service reachability under `app/agents/`
- `app/schemas/rag.py` where required to trace the RAG API
- all files under `tests/`
- frontend API usage under `ui/src/`
- `ui/README.md`, `ui/next.config.ts`, and `ui/package.json`
- scripts under `scripts/` for application imports and endpoint references
- pipelines under `pipelines/` for application imports and endpoint references
- repository documentation needed to confirm documented endpoint contracts
- Docker, monitoring, workflow, and infrastructure references needed to confirm health and metrics consumers
- tracked empty application marker files

Generated dependency directories were not treated as application-owned evidence.

## 3. Endpoint Inventory

The registered application was imported using the repository's existing WSL virtual environment with bytecode generation disabled. Fourteen routes were registered: four framework-provided routes and ten EDIP-defined routes.

| Method | Path | Registered name | Ownership |
|---|---|---|---|
| `GET`, `HEAD` | `/openapi.json` | `openapi` | FastAPI-generated |
| `GET`, `HEAD` | `/docs` | `swagger_ui_html` | FastAPI-generated |
| `GET`, `HEAD` | `/docs/oauth2-redirect` | `swagger_ui_redirect` | FastAPI-generated |
| `GET`, `HEAD` | `/redoc` | `redoc_html` | FastAPI-generated |
| `GET` | `/health` | `health_check` | `app/main.py` |
| `GET` | `/metrics` | `get_metrics` | `app/main.py` |
| `GET` | `/rag/health` | `rag_health` | `app/api/rag.py` |
| `POST` | `/rag/query` | `query_rag` | `app/api/rag.py` |
| `GET` | `/forecast/health` | `forecast_health` | `app/api/forecast.py` |
| `GET` | `/forecast/overview` | `get_forecast_overview` | `app/api/forecast.py` |
| `GET` | `/forecast/recommendations` | `get_forecast_recommendations` | `app/api/forecast.py` |
| `GET` | `/forecast` | `get_forecast_response` | `app/api/forecast.py` |
| `GET` | `/agents/workflow/health` | `agent_workflow_health` | `app/api/agent_workflow.py` |
| `POST` | `/agents/workflow/run` | `run_agent_workflow` | `app/api/agent_workflow.py` |

All three EDIP routers are imported and registered by `app/main.py`.

## 4. Reference Evidence

| Endpoint | Confirmed repository references | Classification |
|---|---|---|
| `/openapi.json` | Automatically registered by FastAPI | Framework route; external use uncertain |
| `/docs` | Documented in `README.md`; automatically registered by FastAPI | Documented framework route |
| `/docs/oauth2-redirect` | Automatically registered as part of Swagger UI support | Framework dependency; retain |
| `/redoc` | Automatically registered by FastAPI | Framework route; external use uncertain |
| `/health` | Documented in `README.md`; Terraform AWS ALB health-check default | Operationally referenced |
| `/metrics` | Documented in `README.md`; monitoring Prometheus configuration; Kubernetes and Terraform monitoring/probe configuration; `tests/integration/test_monitoring_api.py` | Operationally referenced and tested |
| `/rag/health` | Documented in `README.md`; `tests/integration/test_rag_api.py` | Documented and tested |
| `/rag/query` | Documented in `README.md`; success and validation cases in `tests/integration/test_rag_api.py` | Documented and tested |
| `/forecast/health` | Documented in `README.md`; `tests/integration/test_forecast_api.py` | Documented and tested |
| `/forecast/overview` | Documented in `README.md`; success and failure cases in `tests/integration/test_forecast_api.py` | Documented and tested |
| `/forecast/recommendations` | Documented in `README.md`; success, filtering, and failure cases in `tests/integration/test_forecast_api.py` | Documented and tested |
| `/forecast` | Documented in `README.md`; success and failure cases in `tests/integration/test_forecast_api.py` | Documented and tested |
| `/agents/workflow/health` | Documented in `README.md`; `tests/integration/test_agent_workflow_api.py` | Documented and tested |
| `/agents/workflow/run` | Used by `ui/src/app/chat/page.tsx`; documented in `README.md`; tested in `tests/integration/test_agent_workflow_api.py` | Frontend-facing, documented, and tested |

The frontend directly calls only `POST /agents/workflow/run`. Absence of a frontend call is not evidence that another documented or operational endpoint is unused.

`scripts/run_agent_workflow_demo.py` uses the workflow, forecast, and RAG service builders directly rather than calling an HTTP endpoint. The Kafka consumer imports and constructs `EventProcessingService` directly. No endpoint calls were found in `pipelines/**`.

## 5. Module and Service Reachability

### Confirmed active modules

- `app/api/agent_workflow.py`, `app/api/forecast.py`, and `app/api/rag.py` are imported and registered by `app/main.py`.
- `app/core/config.py` is imported by `app/main.py`.
- `app/core/monitoring.py` is imported by `app/main.py` and all three API modules, and is covered by the monitoring integration test.
- `app/core/logging.py` is imported by agent modules, application services, Kafka scripts, the workflow demo, the event generator, topic initialization, and the training pipeline.
- `app/services/agent_workflow_service.py` is used by the agent-workflow API and workflow demo.
- `app/services/forecast_service.py` is used by the forecast API, agent-workflow API, workflow demo, event-processing tests, and forecast tests.
- `app/services/rag_query_service.py` is used by the RAG API, agent-workflow API, workflow demo, and RAG tests.
- `app/services/rag_generation_service.py` is used by the RAG query service and its focused tests.
- `app/services/event_processing_service.py` is used by `scripts/kafka_consumer.py`, unit tests, and the Kafka end-to-end integration contract.
- the agent modules are imported through `app/services/agent_workflow_service.py` and `app/agents/langgraph_workflow.py`.

No application module under `app/api/`, `app/services/`, or `app/core/` was confirmed to have no imports or operational references.

### Package markers

The tracked zero-byte files:

- `app/__init__.py`
- `app/api/__init__.py`
- `app/core/__init__.py`
- `app/services/__init__.py`

are Python package markers. Their lack of textual references does not make them safely unused, and they should remain.

## 6. Confirmed Unused Code or Endpoints

### Confirmed unused endpoint result

No EDIP-defined endpoint is confirmed unused. Every EDIP route is documented, tested, used by the frontend, or used by monitoring or infrastructure.

No endpoint deletion is recommended for Batch 0E.

### Confirmed unused repository items

#### `app/.gitkeep`

- tracked;
- zero bytes;
- located in the already populated `app/` directory;
- has no import, runtime, test, script, pipeline, frontend, documentation, or infrastructure reference;
- no longer performs its placeholder purpose.

It is safe to delete.

#### Inert logging debris in `pipelines/training/train_demand_forecast.py`

The file contains:

- an `import logging` statement confirmed unused by Python AST inspection;
- a standalone triple-quoted string after logger construction;
- an obsolete logging description and apparent `setup_logging()` definition inside that string;
- commented experimental logger statements at the end of the file.

The apparent local `setup_logging()` function is text inside a string and is not executable Python. The active `setup_logging(level="INFO")` call resolves to the function imported from `app.core.logging`.

Removing the unused `logging` import, inert string block, and commented logger experiments does not change the active logging import or call.

## 7. Duplicate, Stale, or Potentially Misleading Components

### Confirmed duplication that remains active

`RagRetrievalAdapter` is implemented in:

- `app/api/agent_workflow.py`
- `scripts/run_agent_workflow_demo.py`

Both copies are actively constructed in their respective API and demonstration flows. Their duplication may be a future maintainability concern, but neither is unused. Consolidating them would be refactoring and is outside this Phase 0 cleanup.

### Overlapping endpoints that remain active

- `GET /forecast` combines data also exposed by `/forecast/overview` and `/forecast/recommendations`.
- `/health`, `/rag/health`, `/forecast/health`, and `/agents/workflow/health` overlap in naming but report different scopes.
- FastAPI exposes both Swagger UI and ReDoc documentation routes.

These routes are documented, tested, operationally referenced, framework-owned, or potentially externally consumed. Overlap is not sufficient evidence for deletion.

### Potentially misleading but not unused

`GET /rag/health` reports retrieval and generation readiness without building or checking external dependencies. This is a behavioural and readiness-semantics issue, not evidence that the endpoint is unused. It should not be changed in Batch 0E.

## 8. Uncertain Items That Must Remain

The following must remain because repository-only inspection cannot disprove external consumption:

- `/openapi.json`
- `/docs`
- `/docs/oauth2-redirect`
- `/redoc`
- all EDIP-defined endpoints
- the combined `/forecast` endpoint
- service-specific health endpoints
- both active `RagRetrievalAdapter` implementations
- public service builders and service classes
- package `__init__.py` markers

Tests are evidence of supported contracts but do not prove live production use. Conversely, a missing frontend reference does not prove non-use by external clients, operators, API tools, or deployment checks.

## 9. Risks

- Deleting a route based only on the absence of a frontend reference could break documented or external clients.
- Removing framework documentation routes would change FastAPI behaviour and developer tooling.
- Deleting service-specific health endpoints could remove diagnostic contracts even where the root health endpoint remains.
- Consolidating the duplicate RAG adapters would cross API and script boundaries and introduce unnecessary Phase 0 refactoring risk.
- Package markers can affect import compatibility across Python versions and tooling.
- Static symbol counts can misclassify decorator-registered endpoints because route functions are referenced through decorators rather than direct calls.
- Repository inspection cannot identify consumers in external dashboards, API clients, automation, or deployed environments.
- The Windows interpreter used for one route-import attempt lacked `python-dotenv`; the registered route inventory was therefore verified with the existing WSL virtual environment instead.

## 10. Smallest Safe Cleanup

The smallest safe Batch 0E implementation is:

1. Delete the tracked zero-byte `app/.gitkeep`.
2. In `pipelines/training/train_demand_forecast.py`, remove only:
   - the unused `import logging`;
   - the inert standalone triple-quoted logging block;
   - the commented experimental logger statements at the end of the file.
3. Preserve `from app.core.logging import get_logger, setup_logging`.
4. Preserve the active `setup_logging(level="INFO")` call.
5. Do not delete or modify any endpoint, router, service, test, frontend API call, workflow, Docker file, infrastructure file, or dependency.

This cleanup removes confirmed repository debris without changing runtime behaviour or public API surface.

## 11. Files That Should Change

For a future implementation of the approved smallest cleanup:

- delete `app/.gitkeep`;
- modify `pipelines/training/train_demand_forecast.py` only as described above.

No new runtime or test file is required.

## 12. Files That Should Remain Unchanged

The following should remain unchanged:

- `app/main.py`
- `app/api/**`
- `app/services/**`
- `app/core/**`
- `app/agents/**`
- `app/schemas/**`
- `tests/**`
- `ui/**`
- `scripts/**`
- all other `pipelines/**`
- `.github/workflows/**`
- `docker-compose.yml`
- `Dockerfile`
- `infra/**`
- `monitoring/**`
- dependency files
- README files
- existing audit files

No Version 2 work, service redesign, route consolidation, adapter extraction, or health-semantics redesign should be included.

## 13. Validation Commands Required After Cleanup

The following validation is required after implementing the recommended cleanup:

```bash
test ! -e app/.gitkeep

grep -n "^import logging$" \
  pipelines/training/train_demand_forecast.py || true

grep -n "def setup_logging\\|commented experimental logger" \
  pipelines/training/train_demand_forecast.py || true

grep -n \
  "from app.core.logging import get_logger, setup_logging" \
  pipelines/training/train_demand_forecast.py

grep -n 'setup_logging(level="INFO")' \
  pipelines/training/train_demand_forecast.py

python -B -c "from app.main import app; paths=[route.path for route in app.routes]; assert len(paths) == 14; assert len(paths) == len(set(paths))"

pytest -q \
  tests/integration/test_monitoring_api.py \
  tests/integration/test_rag_api.py \
  tests/integration/test_forecast_api.py \
  tests/integration/test_agent_workflow_api.py

python -m compileall -q app scripts pipelines tests
docker compose config --quiet

git diff --check
git status --short
git diff --stat
```

The route assertion should be supplemented with explicit checks for the ten EDIP-defined paths so that an accidental route replacement cannot preserve the count while changing the contract.

## 14. Residual Limitations

After the recommended cleanup:

- duplicate RAG adapters will remain;
- the combined forecast endpoint will remain alongside its component endpoints;
- service-specific health endpoints will remain;
- RAG health semantics will remain unchanged;
- static and test evidence will not prove the absence of external API consumers;
- framework-generated route use will remain externally uncertain;
- known external-service dependencies can still affect credentialed RAG and workflow tests;
- the existing full-suite Kafka dependency issue is outside this cleanup;
- no live OpenAI, Pinecone, Kafka, database, Airflow, AWS, or Kubernetes operation will be proven by the cleanup validation.

These limitations do not justify expanding Batch 0E into refactoring or endpoint redesign.

## 15. Rollback

Rollback for the recommended implementation is limited and deterministic:

```bash
git restore --source=HEAD --staged --worktree -- \
  app/.gitkeep \
  pipelines/training/train_demand_forecast.py
```

This restores the tracked placeholder and the prior training-pipeline text. No database, external service, secret, generated artifact, or infrastructure rollback is required because the recommended cleanup has no external-state effect.

## 16. Professional Reflection

Unused-code cleanup requires more than counting textual references. FastAPI route decorators register functions without conventional callers, package markers can affect import behaviour despite having no contents, and infrastructure or monitoring may be the principal consumer of an endpoint that the frontend never calls.

The inspection therefore used several forms of evidence: live route registration, import tracing, frontend calls, tests, scripts, pipeline imports, documentation, monitoring configuration, and infrastructure health checks. This prevented documented or operational endpoints from being misclassified as unused.

The safest Phase 0 outcome is intentionally small. Removing one obsolete placeholder and clearly inert logging debris improves repository clarity without changing public contracts. Duplicate adapters, overlapping routes, and readiness semantics may warrant later design decisions, but combining those decisions with unused-code deletion would weaken reversibility and increase migration risk.
