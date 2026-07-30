# EDIP Phase 0 Batch 0C — Monitoring Ownership Audit

- Audit date: 30 July 2026
- Repository: `enterprise-decision-intelligence-platform-edip`
- Branch inspected: `chore/phase-0-batch-0c-monitoring-ownership`
- Audit mode: Read-only monitoring ownership assessment
- Change scope: Documentation only
- Production status: Monitoring is not verified as production-ready

## 1. Purpose and scope

This document records the findings of the completed read-only EDIP Phase 0 Batch 0C monitoring ownership audit. The audit traced application metric definitions, metric recording, the `/metrics` endpoint, Prometheus and Grafana assets, deployment copies, and monitoring-related test references.

The assessment was limited to monitoring ownership and duplication. It did not modify or redesign runtime code, tests, Docker Compose, infrastructure, workflows, or monitoring assets.

Confirmed facts and recommendations are presented separately. Recommendations in this document are not implementation records.

## 2. Files inspected

The audit inspected or searched the following scoped paths:

### Application

- `app/core/metrics.py`
- `app/core/monitoring.py`, discovered as the active monitoring dependency
- `app/main.py`
- monitoring imports and recording-call references under `app/`

### Monitoring assets

- `monitoring/prometheus/prometheus.yml`
- `monitoring/grafana/provisioning/datasources/datasource.yml`
- `monitoring/grafana/provisioning/dashboards/dashboard.yml`
- `monitoring/grafana/provisioning/alerting/edip-alert-rules.yml`
- `monitoring/grafana/dashboards/edip-overview.json`

### Deployment configuration

- Monitoring-related sections of `docker-compose.yml`
- Monitoring-related files under `infra/k8s/`
- Monitoring-related definitions under `infra/terraform/local-k8s/`
- CloudWatch logging references under `infra/terraform/aws/`

### Tests

- `tests/**` only for monitoring imports, `/metrics`, metric helpers, or monitoring endpoint references

No monitoring-related test reference was found.

## 3. Current active monitoring flow

The confirmed active flow is:

1. `app/main.py` imports monitoring helpers exclusively from `app.core.monitoring`.
2. FastAPI HTTP middleware increments the in-progress gauge before each request.
3. The middleware records request count, status, duration, and HTTP errors in its `finally` path.
4. RAG, forecast, and workflow API modules call capability-specific recording helpers from `app.core.monitoring`.
5. The `/metrics` endpoint calls `metrics_response()`.
6. `metrics_response()` calls `prometheus_client.generate_latest()` against the default registry.
7. Prometheus is configured to scrape `/metrics`.
8. Grafana uses Prometheus as its datasource and loads provisioned dashboards and alert rules.
9. Docker Compose mounts Prometheus and Grafana configuration from `monitoring/`.

The active application implementation is `app/core/monitoring.py`. No active import or use of `app/core/metrics.py` was found within the inspected scope.

## 4. Current `/metrics` endpoint ownership

Exactly one application endpoint registration was found:

```python
@app.get("/metrics", tags=["Monitoring"])
```

It is owned by `app/main.py` and returns the response produced by `app.core.monitoring.metrics_response()`.

Other `/metrics` references have different responsibilities:

| Location | Use |
|---|---|
| `monitoring/prometheus/prometheus.yml` | Prometheus scrape path |
| `infra/k8s/prometheus-configmap.yaml` | Raw-Kubernetes Prometheus scrape path |
| `infra/terraform/local-k8s/prometheus.tf` | Terraform-managed Prometheus scrape path |
| `infra/k8s/api-deployment.yaml` | Readiness and liveness probe path |
| `infra/terraform/local-k8s/api.tf` | Terraform-managed readiness and liveness probe path |

The infrastructure probe references are consumers of the endpoint, not additional registrations.

No test was found that protects the `/metrics` registration, response, content type, or expected metric families.

## 5. Current Prometheus metric definitions

### Active definitions

`app/core/monitoring.py` defines eight active metric families:

| Metric | Type | Purpose |
|---|---|---|
| `edip_http_requests_total` | Counter | HTTP requests by method, path, and status |
| `edip_http_request_errors_total` | Counter | Failed HTTP requests by method, path, and status |
| `edip_http_request_duration_seconds` | Histogram | HTTP request duration by method and path |
| `edip_http_requests_in_progress` | Gauge | Requests currently being processed |
| `edip_workflow_runs_total` | Counter | Workflow runs by scenario and status |
| `edip_workflow_run_errors_total` | Counter | Workflow failures by scenario |
| `edip_rag_requests_total` | Counter | RAG requests by result status |
| `edip_forecast_requests_total` | Counter | Forecast requests by result status |

The histogram also exposes its normal Prometheus bucket, count, and sum series. The default Prometheus Python collectors expose process and Python runtime metrics used by parts of the Grafana dashboard.

### Inactive duplicate definitions

`app/core/metrics.py` defines six metric families whose Prometheus names duplicate active definitions:

- `edip_http_requests_total`
- `edip_http_request_duration_seconds`
- `edip_http_requests_in_progress`
- `edip_workflow_runs_total`
- `edip_forecast_requests_total`
- `edip_rag_requests_total`

The stale file does not define the two active error counters and does not provide the active recording or response helpers.

No import or use of `app/core/metrics.py` was found. If both modules were imported into the same process, their repeated names could cause duplicate time-series registration errors in Prometheus's default registry.

## 6. Ownership boundaries

The intended boundary is:

| Area | Owner | Responsibility |
|---|---|---|
| Application metrics | `app/` | Define metric families, instrument application behaviour, record metric observations, and expose `/metrics` |
| Monitoring assets | `monitoring/` | Own Prometheus scrape configuration, Grafana datasource and provisioning configuration, alert rules, and dashboard source assets |
| Deployment | `infra/` and Docker Compose | Package, mount, or deploy the monitoring-owned assets for each target environment |

### Current conformance

- `app/core/monitoring.py` and `app/main.py` conform to the application ownership boundary.
- `app/core/metrics.py` conflicts with the application ownership boundary by defining a second inactive set of metric families.
- Docker Compose largely follows the boundary by mounting files from `monitoring/`.
- Raw Kubernetes and local-k8s Terraform do not fully follow the boundary because they embed independent copies of monitoring content.
- The dashboard file under `monitoring/` is contaminated with Kubernetes deployment packaging and is not a valid standalone Grafana JSON asset.

## 7. Duplicate, stale, misleading, or conflicting monitoring components

### Confirmed duplicate or stale application code

`app/core/metrics.py` is an unused duplicate. Six of its six metric names are already defined by the active module. Retaining it creates ambiguity and a latent duplicate-registry risk.

### Confirmed dashboard conflict

`monitoring/grafana/dashboards/edip-overview.json` is not valid JSON. It is a Kubernetes ConfigMap YAML wrapper containing dashboard JSON under a data key.

It is byte-identical to:

```text
infra/k8s/grafana-dashboard-json-configmap.yaml
```

Both files had SHA-256:

```text
827BDCCCF22A0B9AA83D6D33D524B4F9B9E116A1429638CFD0AE3C99B3AB9726
```

Docker Compose mounts the `monitoring/grafana/dashboards/` directory as Grafana's dashboard directory. The ConfigMap wrapper is therefore misleading in that location and cannot be parsed as a standalone JSON dashboard.

### Confirmed dashboard drift

- The monitoring/raw-Kubernetes dashboard payload contains 16 panels.
- The Terraform-managed dashboard contains one panel: `EDIP API Up`.

The Terraform deployment therefore exposes a materially reduced dashboard compared with the monitoring and raw-Kubernetes definitions.

### Confirmed semantic duplication

Equivalent Prometheus and Grafana content is maintained independently in:

- `monitoring/`
- `infra/k8s/`
- `infra/terraform/local-k8s/`

Duplicated responsibilities include:

- Prometheus scrape configuration
- Grafana datasource provisioning
- Grafana dashboard provisioning
- Grafana alert rules
- Grafana dashboard content

### Other confirmed misleading or conflicting details

- Raw Kubernetes and Terraform use `/metrics` for both readiness and liveness probes. Metrics availability is not equivalent to application readiness.
- The API-down alert uses `noDataState: OK`; disappearance of the scrape target can therefore avoid alerting.
- Prometheus and Grafana deployment definitions use mutable `latest` image tags.
- Two dashboard panels share the title `Process Memory`. One is a stat panel and one is a time-series panel, so they are functionally distinct but ambiguously named.
- `infra/k8s/grafana-datasource-configmap.yaml` begins with an incorrect Prometheus ConfigMap comment.
- AWS Terraform configures CloudWatch application logging but does not deploy the Prometheus or Grafana assets.
- No monitoring endpoint or metric-family regression test was found.

## 8. Risks

| Risk | Evidence | Severity |
|---|---|---|
| Duplicate Prometheus registry failure | Two modules define six identical metric names | High |
| Unclear application metric ownership | Active and inactive definition modules coexist | High |
| Compose dashboard provisioning failure | The mounted `.json` file is actually YAML | High |
| Environment-specific observability drift | Terraform has one dashboard panel; other definitions have 16 | High |
| Repeated configuration drift | Monitoring content is independently embedded in three locations | High |
| False health confidence | Kubernetes probes use `/metrics` for readiness and liveness | Medium |
| Missing-target alert suppression | API-down rule uses `noDataState: OK` | High |
| Unprotected monitoring contract | No `/metrics` or metric-family test exists | Medium |
| Metric label cardinality growth | Middleware records the raw request path label | Medium |
| Non-deterministic deployment images | Prometheus and Grafana use mutable tags | Medium |

These risks do not establish that a live monitoring stack is failing, because no live stack was executed. They identify code, configuration, and validation weaknesses in the inspected repository state.

## 9. Smallest safe cleanup recommendation for Batch 0C

### Confirmed basis

- `app/core/metrics.py` is not imported or used.
- Its metric names duplicate the active definitions.
- `app/core/monitoring.py` is the active implementation.
- `app/main.py` owns the single `/metrics` registration.

### Recommended atomic cleanup

The smallest safe Batch 0C change is:

1. Delete `app/core/metrics.py`.
2. Add one focused monitoring API test that verifies:
   - `app.main` imports successfully;
   - exactly one `/metrics` route is registered;
   - `/metrics` returns HTTP 200;
   - the response uses Prometheus content;
   - representative active metric families are present.
3. Leave the active monitoring implementation and all deployment assets unchanged.

This cleanup resolves the immediate application-level ownership conflict without combining it with infrastructure packaging or monitoring-behaviour changes.

Dashboard extraction and infrastructure deduplication should be a separately reviewed follow-up because they require coordinated Compose, raw-Kubernetes, Terraform, Grafana, and rollback validation.

## 10. Files that should change

For the smallest recommended cleanup:

| File | Recommended action |
|---|---|
| `app/core/metrics.py` | Delete the unused duplicate module |
| `tests/integration/test_monitoring_api.py` | Add a focused `/metrics` ownership and response regression test |

If repository test conventions require a different monitoring-test location, use the established location while preserving the same narrow assertions.

No change to either file has been performed by this audit record.

## 11. Files that should not change yet

The smallest cleanup should not change:

- `app/core/monitoring.py`
- `app/main.py`
- RAG, forecast, or workflow instrumentation call sites
- active metric names, labels, descriptions, or helper behaviour
- `monitoring/prometheus/prometheus.yml`
- Grafana datasource, dashboard provisioning, alerts, or dashboard queries
- `docker-compose.yml`
- raw Kubernetes manifests
- local-k8s Terraform
- AWS Terraform or CloudWatch logging
- `/metrics` readiness or liveness probes
- Prometheus or Grafana image tags
- authentication or exposure of `/metrics`
- request-path label behaviour
- the existence or selection of alternative Kubernetes deployment approaches

Those concerns require separate decisions and validation. They should not be silently combined with removal of the unused Python module.

## 12. Validation commands required after cleanup

### Application ownership and import checks

```bash
grep -RIn "app\.core\.metrics\|core\.metrics" app tests
test ! -e app/core/metrics.py

python -B -c \
  "from app.main import app; paths=[route.path for route in app.routes]; assert paths.count('/metrics') == 1"
```

### Focused monitoring test

```bash
pytest -q tests/integration/test_monitoring_api.py
```

The test should check the response status, Prometheus content type, and representative active metric families.

### Compilation and repository checks

```bash
python -m compileall -q app tests
docker compose config --quiet
git diff --check
git status --short
git diff --stat
```

### Additional validation required only for later asset canonicalisation

If a later change touches `monitoring/` or `infra/`, require:

```bash
promtool check config monitoring/prometheus/prometheus.yml
jq empty monitoring/grafana/dashboards/edip-overview.json
terraform -chdir=infra/terraform/local-k8s fmt -check -recursive
terraform -chdir=infra/terraform/local-k8s init -backend=false
terraform -chdir=infra/terraform/local-k8s validate
kubectl apply --dry-run=client -f infra/k8s/
docker compose config --quiet
```

A live local validation should then confirm:

- successful Prometheus scraping;
- Grafana datasource provisioning;
- loading of all expected dashboard panels;
- loading of alert rules; and
- visible separation between monitoring source assets and deployment packaging.

## 13. Residual limitations

After the smallest cleanup:

- monitoring configuration would still be duplicated across `monitoring/`, raw Kubernetes, and Terraform;
- the Compose-mounted dashboard would still not be valid standalone JSON;
- Terraform dashboard drift would remain;
- `/metrics` would still be used for Kubernetes health probes;
- the API-down rule would still treat no data as OK;
- images would still use mutable tags;
- request-path cardinality risk would remain;
- AWS would still deploy CloudWatch logging without the Prometheus/Grafana stack; and
- live Prometheus, Grafana, Kubernetes, or AWS behaviour would remain unverified.

Therefore, removal of `app/core/metrics.py` must not be presented as making EDIP monitoring production-ready. It establishes a clearer application-code owner and a protected endpoint contract only.

## 14. Rollback approach

Before commit, restore the removed module and discard the new focused test:

```bash
git restore --source=HEAD --staged --worktree -- app/core/metrics.py
rm tests/integration/test_monitoring_api.py
```

If the cleanup is committed, revert the focused commit rather than rewriting history.

The rollback should be followed by:

```bash
python -B -c "from app.main import app"
git status --short
```

This audit file itself is documentation-only. Before commit, it can be removed without affecting runtime behaviour; after commit, revert its focused documentation commit.

## 15. Professional reflection

Monitoring ownership spans application code, operational assets, and deployment packaging. Treating all monitoring-related files as one undifferentiated concern would hide the different risks: duplicate Python metric registration can break application startup, malformed dashboard packaging can break local observability, and independently embedded infrastructure assets can drift without affecting source-code tests.

The smallest responsible change is therefore not the broadest possible deduplication. Removing the demonstrably unused metric module resolves a confirmed ownership conflict with a narrow rollback boundary. Adding a focused endpoint test converts that ownership decision into repeatable evidence.

The more extensive dashboard and infrastructure issues remain important, but correcting them safely requires explicit packaging decisions and environment-level validation. Recording those limitations rather than silently expanding the batch supports controlled migration, clear causality, and honest evidence of what has and has not been verified.

No SFIA level is assigned. This document records technical evidence, risk-based judgment, proposed validation, and rollback boundaries; it does not claim production readiness or professional competence solely from repository artifacts.
## 16. Implementation result

Implementation was performed on 30 July 2026 within the approved Batch 0C scope:

- deleted `app/core/metrics.py`;
- created `tests/integration/test_monitoring_api.py`; and
- did not change `app/core/monitoring.py`, `app/main.py`, monitoring assets, Docker Compose, infrastructure, workflows, requirements, README, or existing tests.

The new focused test verifies:

- successful import of `app.main`;
- exactly one `/metrics` route;
- HTTP 200 from `GET /metrics`;
- a Prometheus-compatible response content type; and
- the six representative active metric families approved for this batch.

Validation results:

| Validation | Result |
|---|---|
| Monitoring reference search | Passed; no `app.core.metrics` or `core.metrics` reference remained |
| `test ! -e app/core/metrics.py` | Passed |
| Single `/metrics` route import assertion | Blocked during `app.main` import by `ModuleNotFoundError: No module named 'dotenv'` |
| `pytest -q tests/integration/test_monitoring_api.py` | Blocked during collection by the same missing `dotenv` dependency; zero tests executed |
| Pytest cache | Three local permission warnings were reported |
| `python -m compileall -q app tests` | Passed |
| `docker compose config --quiet` | Passed |
| `git diff --check` | Passed |

The implementation is complete at file scope, but runtime acceptance is not fully verified in the current Python environment. The import and focused test must be rerun in a dependency-complete environment before the batch is represented as fully validated. No dependency or test weakening was introduced to bypass the existing environment limitation.