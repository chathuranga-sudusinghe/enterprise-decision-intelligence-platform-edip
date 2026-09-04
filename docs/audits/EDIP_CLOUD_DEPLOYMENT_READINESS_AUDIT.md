# EDIP Cloud Deployment Readiness Audit

Audit date: 2026-09-04  
Repository branch reviewed: `chore/azure-canonical-cloud-cleanup`  
Scope: tracked application, pipeline, infrastructure, monitoring, UI, CI, test, and research-evidence files. Generated training and evaluation were not run. Historical evidence was inspected but not modified.

Severity definitions used here:

- **Critical**: blocks deployment of the selected forecasting capability or creates an unacceptable production exposure.
- **High**: must be addressed before a public or production deployment, but does not prevent a foundation-only development deployment.
- **Medium**: materially affects portability, operability, or repeatability and should be planned soon.
- **Low**: cleanup or hardening that can safely follow the first controlled deployment.

## 1. Executive summary

EDIP is **not ready to deploy the selected Time-Aware LightGBM forecasting capability**. The repository can build a foundation FastAPI image and has useful local Kubernetes, Prometheus, and Grafana scaffolding, but it does not contain a versioned final model bundle, model loading contract, online feature/input contract, or forecast API route. The current LightGBM adapter can predict only after fitting in the same process, so deploying it as-is would require rebuilding training data and retraining—unacceptable for request-time inference.

The most important production blockers are:

1. Export and register an immutable Time-Aware model bundle, including the LightGBM booster and all preprocessing state.
2. Add a load-only inference service and forecast endpoint that never invokes training or research materialization.
3. Define object-storage retrieval, integrity verification, caching, and readiness behavior for the model bundle and any required inference reference data.
4. Add production authentication/authorization and HTTPS before exposing business or forecast APIs publicly.

Microsoft Azure is the sole canonical cloud target. The superseded non-Azure infrastructure has been removed; Azure infrastructure and Continuous Deployment remain unimplemented and require a dedicated ADR and task. Research evidence should remain historical; its two machine-absolute source paths should not be silently rewritten.

## 2. Current deployment assumptions

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `Dockerfile` | 1, 5, 7, 19, 23 | Assumes Python 3.12, application root `/app`, the complete repository as build context, and fixed Uvicorn port 8000. | Medium | The foundation API works under this layout, but the command ignores configured `API_HOST`/`API_PORT`, and the image has no explicit model delivery mechanism. | Keep `/app` as the container contract, but make the startup command consume validated host/port settings and add a separate, explicit model-bundle location configuration. |
| `docker-compose.yml` | 11-20 | Assumes a repository-root `.env` and bind-mounts the entire checkout at `/app`. | Medium | Local development behavior differs from the immutable image used in cloud, masking missing files and packaging errors. | Put development overrides in a Compose override/profile; run deployment smoke tests without the source bind mount. |
| `app/core/config.py` | 12-14, `Settings` | Calculates a source-tree project root and opportunistically loads `.env`. | Medium | Environment variables work in containers, but behavior depends on whether a root `.env` happens to exist. Invalid values can silently fall back. | Make environment injection authoritative outside local development; use validated settings that fail fast for required production values, with optional `.env` loading enabled only for local use. |
| `pipelines/evaluation/run_favorita_lightgbm_evaluation.py` | 79-92 | Research paths are relative to the process current working directory. | Medium | Commands fail or write to unexpected locations when launched outside the repository root. | Preserve CLI defaults for research, but resolve paths from an explicit workspace/data root or require paths at deployment/batch-job boundaries. Do not import these defaults into online serving. |
| `README.md` | 147, 157 | Correctly states that forecast, Retrieval-Augmented Generation (RAG), and workflow APIs are future work and the UI is a baseline. | Informational | Confirms that current infrastructure deploys a foundation, not the forecast product. | Keep this statement until the serving contract is implemented; add a deployment runbook once it exists. |

## 3. Critical blockers

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `pipelines/models/favorita_lightgbm.py` | `FavoritaLightGBMAdapter`, 314-397, 463-713 | The adapter only holds an in-memory booster. It exposes `fit`, `fit_parquet`, and prediction, but no save/load API for the booster or preprocessing state (`fitted_feature_columns`, excluded columns, categorical levels, feature contract, parameters). | Critical | A new API process cannot reconstruct the validated final model without training again. | Define a versioned model-bundle schema and implement export/load functions. Include `Booster.save_model()` output plus canonical JSON metadata for feature contract, fitted columns, categorical levels, model parameters, rounds, training/evidence identifiers, dependency versions, and checksums. |
| `app/main.py` | Entire application, especially 25-70 | Only `/health` and `/metrics` are registered; no forecast route or model lifecycle exists. | Critical | There is no deployable interface for Time-Aware predictions. | Add a thin forecast router and a load-only inference service. Load and validate one immutable model bundle during application lifespan; inject it into the route. Do not import evaluation/tuning runners. |
| `pipelines/models/favorita_lightgbm.py` | `fit_parquet`, 524-658 | The reusable disk path is training-oriented and requires local Parquet plus temporary disk-backed labels before a booster exists. | Critical | Treating this as deployment inference would rebuild training state, consume large CPU/RAM/disk, increase startup time, and risk accidental retraining. | Make serving depend exclusively on a prebuilt model bundle. Keep `fit_parquet` in offline jobs and prevent it from being reachable from API startup or request handlers. |
| `.dockerignore` | 13-14, 24-25 | Excludes `data`, `artifacts`, Parquet, and JSONL from the image; no alternative model/object-storage contract exists. | Critical | The image cannot contain the final model or feature data, and the task definition supplies no remote model URI. | Keep large data excluded. Add `MODEL_BUNDLE_URI`, expected checksum/version, startup cache directory, and provider credentials through Azure Managed Identity. Fetch the bundle from object storage before declaring readiness. |
| `artifacts/evaluation/favorita_scrum_19_final_holdout/scrum_19_final_holdout.json` | Overall evidence; source paths at 1300 and 1305 | The final evidence records metrics and parameters but not a serialized deployable model. | Critical | Selection evidence cannot itself be served. | Run a separately governed final-fit/export job using the approved Time-Aware contract and frozen configuration; link its immutable model version and digest back to SCRUM-19 evidence without modifying the recorded holdout results. |

## 4. High-priority issues

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `app/main.py` | `health_check`, 25-31 | `/health` is only process liveness; it does not prove model availability, bundle integrity, database connectivity, or other required dependencies. | High | Load balancers may route forecast requests to an instance that cannot serve them. | Split `/live` (process only) and `/ready` (model loaded and verified; required dependencies available). Point Azure Container Apps and local Kubernetes readiness to `/ready` and liveness to `/live`. |
| `infra/k8s/api-deployment.yaml` | 36-46 | Both readiness and liveness probe `/metrics`. | High | A process can expose metrics while its serving dependencies are unavailable; liveness also cannot distinguish dependency failure from a dead process. | Use the dedicated `/ready` and `/live` endpoints and configure startup probe/delays around bounded model loading. Apply the same change to `infra/terraform/local-k8s/api.tf` lines 54-71. |
| `app/core/config.py` | `_get_env_int`, 24-33; `_get_env_bool`, 36-47 | Malformed configuration silently falls back to defaults. No production-required fields or model/storage/database settings exist. | High | Misconfiguration can start apparently healthy with wrong CORS, port, or missing model location. | Replace silent fallback for supplied invalid values with startup validation; add typed required production settings for model URI/version/checksum, cache path, environment, and external services. |
| `infra/k8s/api-deployment.yaml` | 22-23 | Uses a personal Docker Hub image and `latest` with `IfNotPresent`. | High | Clusters can run stale or unreviewed images and depend on a personal registry namespace. | Parameterize the organization-owned registry and pin an immutable digest. Add `imagePullSecrets` or Azure Managed Identity only where required. |
| `docker-compose.yml` | 46-47, 60-62; `infra/k8s/grafana-deployment.yaml` 25-29 | Hard-coded `admin/admin` Grafana credentials and `edip/edip` PostgreSQL credentials are present in deployment-like manifests. | High if exposed; Medium for isolated local development | Copying these manifests to a shared/cloud environment immediately exposes known credentials. | Label Compose as local-only, read credentials from ignored local env for development, and use Azure Key Vault/Kubernetes external secrets for deployed environments. Remove defaults from deployable manifests. |
| `infra/terraform/local-k8s/variables.tf` | 53-63; tracked `infra/terraform/local-k8s/terraform.tfvars` 9-10 | A sensitive variable has a public default and the tracked tfvars repeats it. | High if reused outside local cluster | Terraform sensitivity hides output but does not make the literal secret safe. | Remove the password default and tracked value; inject it through an external secret mechanism or ephemeral local-only untracked tfvars. |
| `.github/workflows/docker-ci.yml` | 28-29 | CI only builds the image; it does not start it, check health/readiness, run as non-root, or test model retrieval/loading. | High | A syntactically buildable but non-serving image can pass. | Add an image smoke test, unprivileged-user check, health/readiness checks, vulnerability/SBOM scan, and—once available—a small fixture model-load/predict contract test. |
| `.github/workflows/integration-ci.yml` | 49-69 | Installs dev dependencies and runs tests, but has no MyPy, UI build, configuration-failure, deployment manifest, or service integration gate. | High | Deployment-critical incompatibilities can merge undetected. | Add MyPy for serving modules, `npm ci && npm run build && npm run lint`, production config validation tests, and a bounded API/model integration test. |
| `ui/src/app/chat/page.tsx` | 86-87, 171-196 | Browser API URL falls back to loopback and calls `/agents/workflow/run`, which the current backend does not implement. | High for end-to-end deployment | A deployed browser resolves `127.0.0.1` to the user's machine; the baseline UI cannot operate against the current API. | Require `NEXT_PUBLIC_API_BASE_URL` at build/deploy time or use a same-origin reverse proxy; add an API contract test and deploy UI only with a compatible backend. |

## 5. Medium-priority issues

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `requirements.txt` | Entire file | Fully pinned runtime versions are positive, but the file is UTF-16 LE with CRLF rather than the ecosystem-standard UTF-8. Runtime and research dependencies are also combined. | Medium | Some scanners, dependency bots, shell tooling, and build systems may misread it; the API image installs heavy research packages including Optuna. | Normalize to UTF-8 in a dedicated change and split minimal serving dependencies from training/research/dev dependencies while retaining lock-level reproducibility. Verify the Docker build after conversion. |
| `Dockerfile` | 1, 9-19 | Runs as root, installs build tools in the final image, copies the full repository, and uses an unpinned base-image digest. | Medium | Larger attack surface, writable application tree, and weaker supply-chain reproducibility. | Use a multi-stage build, pin the base digest, copy only runtime files, create a non-root user, and run with a read-only root filesystem plus explicit writable cache/temp mounts. |
| `Dockerfile` | 23; `app/core/config.py` 72-73 | Uvicorn's hard-coded command does not consume `API_HOST` or `API_PORT`; the container command ignores both. | Medium | Configuration inventory and actual runtime behavior diverge. | Use one entrypoint that reads the validated settings, or remove unused variables and make the container-port contract explicit. |
| `app/core/logging.py` | `configure_logging`, 32-69 | Console logs are human-formatted rather than structured; optional file logging writes under `monitoring/logs`. | Medium | File logs are ephemeral or may fail on a read-only filesystem; text-only logs reduce cloud queryability. | Default cloud operation to JSON structured stdout/stderr with timestamp, severity, request/trace ID, model version, and safe business context. Disable file logging in containers. |
| `app/core/monitoring.py` | `observe_http_request`, 78-106 | Uses raw request path as a Prometheus label. | Medium | Dynamic path segments could cause high-cardinality metrics when real resource routes are added. | Label by normalized route template (`request.scope["route"].path`) and use a stable fallback for unmatched routes. |
| `app/core/monitoring.py` | 46-72, 123-183 | Forecast/workflow counters exist, but there are no model-load, prediction latency, batch size, model version, feature validation, or drift/freshness metrics. | Medium | Operators cannot distinguish API availability from model-serving quality. | Add bounded-cardinality serving metrics after the inference contract exists; never use item/store IDs as metric labels. |
| `pipelines/models/favorita_lightgbm.py` | `_LabelMemmapContext`, 281-310 | Offline fitting depends on OS temporary storage with space proportional to target rows. | Medium for batch jobs; not a serving blocker | Cloud batch jobs can exhaust ephemeral storage; Windows-specific cleanup commentary indicates cross-platform care but no capacity check. | Make the offline scratch directory configurable, document required capacity, monitor free space, and allocate explicit ephemeral storage in the batch-job definition. Do not use this path in serving. |
| `pipelines/features/favorita_model_ready.py` | Writer setup 787 and atomic JSON 1201; fixture temp dir 1292 | Feature materialization writes local files and expects `Path`/PyArrow local filesystem semantics. | Medium | Direct Azure Blob URIs are not supported by the current public contract, and atomic rename assumptions do not map directly to object stores. | Keep local staging for bounded Parquet creation, then publish through a small artifact-store interface with upload-to-versioned-key, checksum, and completion marker semantics. |
| `pipelines/features/build_favorita_fold_datasets.py` | Defaults 35-43; manifest construction 514-555 | Generated fold artifacts and manifests point to local repository-relative paths. | Medium | Offline jobs require a known working directory and generated Parquet is absent from Git by design. | Accept explicit input/output URIs in cloud batch jobs and store immutable generated datasets/manifests in object storage; retain relative paths only for local research convenience. |
| `pipelines/evaluation/run_favorita_lightgbm_evaluation.py` | Writers 409-461, 726-837; staging 1245-1250 | Evaluation writes local staged files and publishes by filesystem operations. | Medium | Ephemeral containers lose outputs; filesystem atomicity does not provide durable cloud publication. | Run evaluation as a batch job with explicit scratch volume, then upload finalized files and manifest/digests to object storage. |
| `infra/k8s/api-deployment.yaml` | 29-35 | 500m CPU/512Mi memory limits were set for the foundation API, not measured LightGBM serving. | Medium | Model loading or concurrent prediction may be OOM-killed or throttled. | Benchmark the exported bundle and representative bounded requests, then set requests/limits and concurrency from measured peak memory and latency. |
| `monitoring/grafana/provisioning/alerting/edip-alert-rules.yml` | API-down rule | Repository monitoring is useful but notification destinations, durable storage, and cloud-managed integration are not defined. | Medium | Alerts may exist only in the local Grafana instance and disappear with it. | Route alerts to an approved managed destination and provision persistent/managed monitoring per cloud; test alert delivery. |

## 6. Low-priority cleanup

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `app/core/config.py` | 8, 50-56, 77 | Uses mutable `typing.List` annotations in a frozen dataclass. | Low | No meaningful deployment failure, but immutability is shallow. | Use tuples or immutable collections when settings are next revised. |
| `app/main.py` | 26, 37, 66 | Public functions omit explicit return types. | Low | Does not affect runtime; modest type-checking gap. | Add return annotations during the serving API work. |
| `docker-compose.yml` | 8, 24, 40, 58 | Fixed `container_name` values reduce Compose project isolation. | Low | Parallel local stacks can conflict. | Remove fixed names and let Compose namespace services. |
| `docker-compose.yml` | 23, 39 | Prometheus and Grafana use `latest`. | Low for local-only use; High if promoted | Local runs can change unexpectedly. | Pin tested versions even for development; never promote this Compose file directly to production. |
| Notebook outputs | `notebooks/favorita/01_data_source_validation.ipynb`, `02_temporal_sales_and_coverage_eda.ipynb` executed outputs | Historical outputs contain `/mnt/d/...` WSL/Windows-drive paths. | Low | They are documentary machine metadata, not imported runtime configuration. | Leave historical outputs intact; make future notebooks use parameters and emit logical dataset IDs alongside optional local paths. |

## 7. Hard-coded path inventory

No active Python or infrastructure code was found with hard-coded `/home/...` or Windows drive paths. The active portability issues are current-working-directory-relative defaults, one UI loopback URL, local Kubernetes `~/.kube/config`, and historical evidence/notebook metadata.

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `artifacts/evaluation/favorita_scrum_19_final_holdout/scrum_19_final_holdout.json` | 1300, 1305 | Two source-state records contain `/home/chathuranga/projects/.../favorita_cleaned.parquet`. | Low historical / Medium for automated evidence consumers | Evidence is machine-specific but still valid as historical provenance. | Do **not** rewrite this completed evidence. Future schemas should record a logical dataset URI/version and digest as primary identity, with local resolved path optional and explicitly informational. |
| `notebooks/favorita/01_data_source_validation.ipynb` and `02_temporal_sales_and_coverage_eda.ipynb` | Executed cell outputs containing `/mnt/d/...` | WSL-mounted Windows-drive paths are embedded in historical output. | Low | No runtime dependency; cloned notebook output is not portable as an execution instruction. | Preserve history; parameterize data roots for future executions and avoid treating rendered paths as dataset identity. |
| `ui/src/app/chat/page.tsx` | 86-87 | Default API URL is `http://127.0.0.1:8000`. | High | Fails from deployed clients. | Require a deployment-provided URL or same-origin proxy. |
| `infra/terraform/local-k8s/terraform.tfvars` | 1 | Kubeconfig uses `~/.kube/config`. | Low/local-only | Correct for a developer cluster but not automation-portable. | Keep local module explicitly local; inject an agent/CI kubeconfig or use in-cluster/provider authentication in deployment automation. |
| `app/core/logging.py` | 44-52 | Optional log file defaults to `monitoring/logs/edip.log`, relative to current working directory. | Medium | Can write unexpectedly or fail on immutable containers. | Use stdout in cloud; if file output remains for local use, require an explicit path. |
| `pipelines/features/build_favorita_fold_datasets.py` | 35-43 | Defaults to `data/processed/...` and several `artifacts/features/...` roots. | Medium/offline | Requires repository-root launch and local disk. | Supply explicit batch-job paths/URIs; retain defaults only for documented local research. |
| `pipelines/evaluation/run_favorita_lightgbm_evaluation.py` | 79-92 | Defaults to local source, fold, and evaluation roots. | Medium/offline | Same current-directory and ephemeral-storage risk. | Supply explicit paths and durable publication in cloud batch jobs. |
| `pipelines/evaluation/run_favorita_lightgbm_final_holdout.py` | 58-60, 89-93, `_source_state` 121-127 | Uses local default output and intentionally resolves the source path into evidence. | Low historical / Medium if reused | Appropriate for the completed controlled run, but not a serving or generic cloud job interface. | Freeze SCRUM-19 results; for future runs, add logical URI/digest metadata without changing historical output. |
| `pipelines/evaluation/run_favorita_lightgbm_optuna_tuning.py` | 48, 54-58 | Tuning defaults to a local artifact root. | Low for deployment | Tuning is offline and must not be in the serving path. | Keep offline; when cloud batch tuning is needed, use explicit object-storage output and job scratch paths. |

## 8. Runtime configuration inventory

| Setting/source | File and line | Current behavior | Readiness assessment | Exact recommended fix |
|---|---|---|---|---|
| `APP_NAME`, `APP_VERSION`, `APP_ENV` | `app/core/config.py` 67-69 | Optional environment variables with development defaults. | Acceptable for local; production values are not validated. | Require a known `APP_ENV`; derive build/version metadata from release and expose immutable revision/model versions. |
| `API_HOST`, `API_PORT` | `app/core/config.py` 72-73; `Dockerfile` 23 | Settings exist, but Docker starts fixed `0.0.0.0:8000`. | Configuration is internally inconsistent. | Make one startup owner consume these values, or remove them and document the fixed container contract. |
| `ALLOW_CREDENTIALS`, `ALLOWED_ORIGINS` | `app/core/config.py` 76-85 | Defaults to credentials enabled and local origins, including `192.168.8.161`. | Local-network assumption; cloud values can be unsafe. | Enforce environment-specific origin allowlists and reject invalid wildcard/credentials combinations. |
| Root `.env` | `app/core/config.py` 12-14; `.gitignore` 15 | Automatically loaded if present and correctly ignored. Local file currently contains OpenAI, Pinecone, RAG, and application variable names; values were not included in this audit. | No tracked root secret was found, but no `.env.example` exists and most external-service fields are not represented in `Settings`. | Add a value-free `.env.example`/configuration reference, remove stale variables, validate required fields, and use managed secrets/Azure Managed Identity in cloud. |
| UI `.env.local` | `ui/.gitignore` 34; `ui/src/app/chat/page.tsx` 86-87 | Ignored local configuration supplies `NEXT_PUBLIC_API_BASE_URL`; fallback is loopback. | Not deployment-ready by default. | Document and validate the public build-time URL or proxy configuration. Never put secrets in `NEXT_PUBLIC_*`. |
| Database URL | Repository-wide | Compose starts PostgreSQL, but application settings/code expose no database URL or connection lifecycle. | PostgreSQL is presently unused scaffolding. | Do not claim database readiness. When persistence is implemented, add a validated secret-backed URL, pool lifecycle, migrations, TLS, and readiness behavior. |
| Model storage | Repository-wide | No model URI, version, checksum, cache, or load policy. | Critical gap. | Add provider-neutral model bundle settings and startup validation. |

## 9. Model/inference deployment readiness

The selected arm can be identified from SCRUM-19 evidence, and the adapter already has useful target-free prediction methods. However, `predict_frame()` and `predict()` require the same adapter instance to have been fitted. Prediction preprocessing depends on state learned during fit, so saving only the LightGBM text model would be insufficient.

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `pipelines/models/favorita_lightgbm.py` | `_record_fitted_state`, 446-461 | Preprocessing state is held only in Python memory. | Critical | A raw booster loaded alone may encode categories differently or use the wrong columns. | Serialize and validate all fitted state in a versioned, language-neutral metadata file next to the booster. |
| `pipelines/models/favorita_lightgbm.py` | `predict_frame`, 678-682; `predict`, 684-713 | Prediction logic is reusable only after fitting, and the frame route requires the full training/evaluation schema, including columns later excluded from booster input validation. | High | Online callers lack a stable, minimal request-to-feature contract. | Create a serving facade that accepts a versioned target-free feature schema, performs the same deterministic preparation, and calls a loaded booster. Reuse adapter validation logic rather than copying it. |
| `pipelines/features/favorita_model_ready.py` | `materialize_feature_dataset` and feature-building helpers | Features are built from historical local Parquet over forecast origins; this is an offline research materializer, not an online feature service. | Critical if used at request time | Prediction would require large source data access and expensive rebuilding. | Define which Time-Aware inputs are supplied by request, operational stores, and precomputed feature tables. Build those features upstream/batch or behind a bounded feature-retrieval interface. |
| `requirements.txt` | 6-14 after decoding | LightGBM and its numerical stack are pinned, which is a good basis for reproducibility. | Positive with gap | Runtime compatibility is known, but the bundle lacks its own compatibility metadata. | Record LightGBM, Python, NumPy, pandas, PyArrow, feature schema, and code revision in the bundle; reject incompatible major/schema versions at load. |
| Repository-wide model artifacts | Search for `save_model`, `model_file`, pickle/joblib loaders | No model serializer/loader or model binary is tracked. | Critical | No deployable model exists. | Store immutable model bundles in Azure Blob, not Git; publish checksum/signature and promotion metadata in a small registry/manifest. |

Minimum cloud model bundle:

- LightGBM model file.
- Bundle/schema version and model version.
- Time-Aware feature-contract name and exact ordered candidate/fitted columns.
- Excluded all-null features and categorical levels/encoding contract.
- Effective model parameters and `num_boost_round`.
- Training data/version digest, code commit, SCRUM-19 evidence identifier, and dependency versions.
- File checksums, creation time, approval/promotion status, and optional signature.

The inference container should download this bundle once at startup to a bounded writable cache, validate it, instantiate a load-only predictor, and only then report ready. It must not rebuild training datasets or invoke Optuna/evaluation code.

## 10. Data and artifact storage readiness

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `.gitignore` | Data/artifact/model sections | Correctly excludes datasets, Parquet, predictions, and model artifacts from Git while allowing selected JSON/Markdown evidence. | Positive with operational gap | Prevents large/sensitive data commits, but leaves no durable cloud artifact system. | Preserve exclusions and add object-storage lifecycle/versioning plus a manifest/catalog. |
| `.dockerignore` | 13-14, 24-25 | Correctly excludes large research data from the image. | Positive with critical gap | Requires remote delivery, which is absent. | Implement object-storage download and cache contracts rather than removing exclusions. |
| `pipelines/features/favorita_model_ready.py` | Parquet writers and `write_json_atomic` | Local atomic file operations provide good single-host safety. | Medium | Object stores do not support identical rename semantics. | Publish immutable keys and a final completion manifest after checksum verification; never expose partial uploads. |
| Evaluation/fold manifests under `artifacts/evaluation` | Artifact path fields | Many manifests reference ignored local Parquet/prediction files that are not portable with the Git checkout. | Medium | Metrics remain readable, but full reproduction/audit cannot retrieve referenced binary evidence from Git alone. | Archive referenced Parquet/predictions in governed object storage and record durable logical URIs, hashes, retention class, and access policy. |
| Repository-wide | Object storage libraries/interfaces | No Azure Blob client or provider-neutral artifact repository is implemented. | High | Azure Container Apps cannot retrieve model or data artifacts through application code. | Add one narrow `ArtifactStore` interface (`get`, `put`, `exists`, metadata/checksum) with an Azure Blob adapter or a tested provider-neutral filesystem contract. Keep provider SDKs at the boundary. |
| Offline temporary files | `pipelines/models/favorita_lightgbm.py` 281-310; evaluation runners' `TemporaryDirectory` usage | Scratch storage is automatically cleaned, which is good, but capacity/location is implicit. | Medium | Managed batch jobs may have insufficient ephemeral storage. | Make scratch root and capacity requirements explicit; publish only completed artifacts and monitor cleanup/failures. |

Recommended storage split:

- **Object storage:** model bundles, immutable datasets/features, prediction evidence, reports, and large evaluation artifacts.
- **Metadata database/catalog:** model promotion status, logical dataset IDs, checksums, lineage, retention, and run status.
- **Container local disk:** read-through model cache and job scratch only; never the sole durable copy.
- **Git:** code, schemas, lightweight manifests, and approved human-readable evidence only.

## 11. Docker/container readiness

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `Dockerfile` | Entire file | Foundation image is simple and likely buildable, but not production hardened or forecast-capable. | High for forecast deployment | It starts the foundation API only. | Add multi-stage/minimal non-root runtime, healthcheck/smoke validation, and model bundle bootstrap after the inference contract is implemented. |
| `Dockerfile` | 14-17 | Copies dev requirements but installs only runtime requirements; runtime file also includes research stack. | Medium | Confusing dependency boundary and unnecessarily large serving image. | Copy/install a serving lock only; keep training dependencies in a separate batch/research image. |
| `Dockerfile` | 19 | `COPY . .` relies on `.dockerignore` and still includes tests, infra, docs, UI source, and tracked evidence. | Medium | Larger image/context and unnecessary information exposure. | Copy only application/serving packages and required metadata. |
| `docker-compose.yml` | 15-16 | Source bind mount overwrites the built `/app`. | Medium | Local success can depend on uncommitted or host-only content. | Add an immutable-image Compose smoke profile with no bind mount. |
| `infra/k8s/api-deployment.yaml` | 29-46 | Resource values and probes are foundation assumptions. | High once model loads | Model startup and inference may fail orchestration checks. | Benchmark, add startup/readiness/liveness probes, graceful termination, and explicit cache volume/ephemeral limit. |
| `.github/workflows/docker-ci.yml` | 28-29 | No multi-architecture need is established; build only is still insufficient. | High | Does not prove runnable behavior. | Smoke-run the exact built image and test deployment-critical endpoints/configuration. |

Python 3.12 is consistent across `Dockerfile`, GitHub Actions, and Ruff configuration, which is a strength. Exact dependency pins also improve reproducibility, subject to the encoding and dependency-boundary issues above.

## 12. FastAPI/backend readiness

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `app/main.py` | 25-31, 65-70 | Health and metrics handlers are synchronous but trivial; this is acceptable. | Informational | No current event-loop blocking concern in these handlers. | Keep cheap handlers; use async only when awaiting true async I/O. |
| `app/main.py` | Future forecast path; repository-wide | No inference endpoint, request/response schema, timeout, payload limit, batching, or concurrency policy. | Critical | Forecasting cannot be served safely or consistently. | Define versioned Pydantic schemas, bounded batch sizes/horizons, timeouts, error mapping, and a separately tested inference service. |
| `pipelines/models/favorita_lightgbm.py` | `predict_frame`/LightGBM call | Prediction is CPU-bound synchronous work. | High once exposed | Calling it directly in an async route would block an event-loop worker and amplify latency under load. | Use a bounded worker/thread/process strategy or synchronous route with tuned worker count; cap concurrency from benchmarks. Avoid loading duplicate large models per worker unintentionally. |
| `app/main.py` | Application construction | No lifespan startup/shutdown hook exists. | High | Model may be loaded per request if implemented naively, causing severe latency and memory churn. | Load once during lifespan, verify integrity, warm a bounded fixture prediction, and release resources on shutdown. |
| `app/main.py` | Middleware 36-59 | Metrics middleware correctly records time and decrements in `finally`, but has no correlation ID or centralized exception envelope. | Medium | Troubleshooting distributed requests is difficult; error responses may be inconsistent. | Add correlation propagation and safe centralized error handlers without leaking internals. |
| `app/main.py` | CORS 76-82 | Allows all methods and headers. | Medium | Broader browser attack surface than necessary for authenticated APIs. | Restrict methods/headers to the actual API contract after routes are defined. |
| `app/core/config.py` | `Settings` | No database, model, object storage, identity, tracing, or request-limit configuration exists. | High | Backend cannot configure required production integrations. | Extend settings only as each integration becomes real; validate production-required values at startup. |

## 13. Security readiness

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| Root `.env`, `.gitignore` | `.gitignore` 14-16 | `.env` is ignored and not tracked; no exposed root API-key values were found in tracked source. | Positive | Basic secret hygiene is present. | Continue secret scanning in CI and rotate immediately if any local credential was ever published elsewhere. |
| `docker-compose.yml` | 46-47, 60-62 | Known local credentials are committed. | High if deployed | Immediate compromise of Grafana/PostgreSQL when exposed. | Confine to local-only configuration and inject non-default secrets elsewhere. |
| `infra/k8s/grafana-deployment.yaml` | 25-29 | Known Grafana admin password is embedded in a Kubernetes manifest. | High | Anyone with repository/manifest access knows the deployed credential. | Replace with an external secret reference; force rotation for any cluster where this manifest was applied. |
| `app/main.py` | Entire API | No authentication/authorization or tenant isolation. | Critical for future business APIs | Local-only trust cannot extend to cloud. | Implement identity and authorization before adding public business routes. |
| `ui/src/app/chat/page.tsx` | 142-158 | Payload contains user role/scope supplied by the browser. | High once backend route exists | Client-provided roles/scopes cannot be trusted for authorization. | Derive identity, roles, and tenant scope from verified server-side claims; treat payload fields only as requested filters subject to authorization. |

No debug server flag or hard-coded production API credential was found in tracked application code. The local `.env` values were intentionally not printed or recorded in this audit.

## 14. Observability readiness

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `app/core/logging.py` | 32-73 | stdout logging support exists, which fits container collection. | Positive with Medium gap | Cloud log drivers can collect it, but fields are unstructured. | Emit structured logs and include correlation/revision/model identifiers. |
| `app/core/monitoring.py` | 19-72 | HTTP, workflow, RAG, and forecast Prometheus metrics are defined. | Positive with Medium gap | Good foundation; forecast metrics are not connected because no route exists. | Instrument actual service lifecycle and prediction behavior when implemented. |
| `app/main.py` | 36-59, 65-70 | Middleware and `/metrics` expose request telemetry. | Positive with Medium risk | Raw path labels may become high-cardinality. | Normalize route labels and secure or network-restrict metrics exposure in production. |
| `monitoring/prometheus/prometheus.yml` | 5-10 | Static Compose target assumes service name `edip-api`. | Low/local-only | Not suitable for dynamic cloud discovery. | Use managed monitoring/service discovery in cloud; keep this file for local Compose. |
| `infra/k8s/grafana-alerting-configmap.yaml` | 16-39 | `noDataState: OK` on API-down alert can hide a missing metrics pipeline. | Medium | Monitoring failure may be interpreted as healthy. | Treat no-data as alerting or add an independent dead-man/scrape-health alert. |
| Repository-wide | Tracing and service-level objectives | No OpenTelemetry traces, forecast Service-Level Indicators/Objectives (SLIs/SLOs), model-load alerts, or error-budget policy. | Medium | Cross-service diagnosis and operational acceptance are incomplete. | Add traces and explicit availability/latency/error/model-readiness objectives after endpoint design. |

## 15. CI/CD readiness

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| `.github/workflows/integration-ci.yml` | 40-69 | Python 3.12, lint, unit, and integration tests are automated. | Positive | Good code-quality baseline. | Preserve and extend with serving/deployment gates. |
| `.github/workflows/docker-ci.yml` | 20-29 | Docker build is validated on major branches and features. | Positive with High gap | Catches Dockerfile/dependency build failures, not runtime failures. | Add immutable-image smoke and security tests. |
| `.github/workflows/terraform-ci.yml` | 26-89 | Only local Kubernetes Terraform formatting/validation is currently checked; no Azure Terraform exists. | Positive with Medium gap | Syntax/provider contracts are checked, but not plans, policy, security, cost, or drift. | Add policy/security scanning and environment-specific reviewed plans; keep applies approval-gated. |
| `.github/workflows/integration-ci.yml` | Workflow triggers | No `paths` filter means backend tests run broadly, while there is no UI CI job. | Medium | UI regressions and API/UI contract mismatch are not gated. | Add a UI job using `npm ci`, lint, type/build, and contract tests. |
| Repository-wide CI | Release process | No image push, signing, deployment, environment promotion, rollback, or post-deploy verification workflow exists. | High for production | Infrastructure code cannot produce a governed deployment. | Implement build-once/promote-by-digest pipeline with approval, provenance/SBOM/signature, deployment, readiness smoke, and rollback. |
| Repository-wide CI | Deployment fixtures | No load-only model bundle fixture test exists because the bundle contract is absent. | Critical for forecast release | CI cannot prove that a fresh container can load and predict without training. | Add a tiny synthetic model bundle and contract test; never use the protected holdout or heavy training in CI. |
| `requirements.txt`, `ui/package-lock.json`, Terraform provider constraints | Dependency definitions | Python versions are exactly pinned and npm has a lockfile; Terraform providers use bounded major versions. | Positive with Medium gap | Reproducibility is reasonable but container base/actions/images are not digest-pinned and Python serving/research deps are mixed. | Add controlled dependency updates, lock/constraints for serving, immutable container references, and automated vulnerability review. |

## 16. Azure canonical deployment notes

| File | Line or function | Issue | Severity | Deployment impact | Exact recommended fix |
|---|---|---|---|---|---|
| Repository-wide | Azure infrastructure | No Azure Terraform, Container Apps environment, Azure Container Registry, Blob Storage, Key Vault, Managed Identity, PostgreSQL, Application Insights, or Azure Monitor resources are implemented. | High | The canonical target is documented but cannot yet be provisioned from this repository. | Define the detailed Azure topology in a dedicated ADR, then implement reviewed Azure Terraform in a separate task. |
| Application storage boundary | Repository-wide | No model/artifact storage abstraction or Azure Blob adapter exists. | High | Container Apps cannot retrieve the immutable model bundle. | Introduce a narrow provider-neutral artifact-store port and an Azure Blob implementation using Managed Identity, logical model URI, version, and checksum. |
| `Dockerfile` | Container runtime | The OCI container is compatible with Azure Container Apps in principle. | Positive with gap | The same image can be promoted through ACR once model loading and readiness exist. | Build once, publish to ACR, and deploy by immutable digest; do not bake credentials into the image. |
| `app/core/logging.py`, `app/core/monitoring.py` | Telemetry boundary | stdout and Prometheus metrics are portable, but Application Insights / Azure Monitor integration is absent. | Medium | Azure operations lack correlated logs, traces, metrics, and alerts. | Add OpenTelemetry-compatible export and Azure configuration while keeping application telemetry interfaces provider-neutral. |
| Repository-wide | Identity and secrets | No Azure Managed Identity or Key Vault integration exists. | High | Artifact and secret access would otherwise invite static credentials. | Assign least-privilege Managed Identity to Container Apps and resolve secrets through Key Vault references. |
| GitHub Actions | Deployment | CI exists, but no ACR publish or Container Apps revision deployment workflow exists. | High | No governed Azure release path is available. | After the ADR and Terraform exist, add build-once/promote-by-digest GitHub Actions with environment approval, post-deploy readiness, and rollback evidence. |

Application boundaries should remain provider-neutral where practical, but infrastructure is Azure-only. The repository must not reintroduce a parallel production-cloud path without a new authoritative architecture decision.

## 17. Recommended fixes before SCRUM-20

These are the exact blockers that must be fixed **before any claim that the selected forecasting model is cloud-deployable**:

1. Specify and implement the immutable model-bundle export/load contract, including preprocessing state and integrity/version metadata.
2. Produce a governed final Time-Aware model artifact outside the protected holdout evaluation. Link it to the frozen configuration and evidence; do not alter SCRUM-19 metrics.
3. Add a load-only inference service and bounded forecast request/response contract. Prove a clean process can load and predict without data materialization, fitting, evaluation, or Optuna.
4. Add Azure Blob model/artifact retrieval behind a provider-neutral application boundary with checksum verification, local cache controls, Azure Managed Identity, and readiness gating.
5. Add `/live` and dependency-aware `/ready`; update Azure Container Apps and local Kubernetes probes.
6. Add production configuration validation, including explicit model URI/version/checksum and safe CORS rules.
7. Before public production exposure, add HTTPS and approved authentication/authorization/tenant isolation. Client-supplied roles must never be trusted.
8. Add a non-heavy CI container test that loads a tiny fixture bundle and performs one deterministic prediction, plus image smoke/security checks.

Recommended order: model bundle contract → load-only predictor → feature/input contract → artifact store → API/lifecycle/readiness → security/configuration → deployment manifests and CI release gates. This sequence prevents infrastructure work from encoding the wrong model-serving assumptions.

## 18. Fixes that can wait until later

The following items are safe to defer while SCRUM-20 or subsequent application work continues, provided no production-readiness claim is made:

- Normalize historical notebook path outputs. They are not runtime dependencies.
- Normalize the two absolute paths inside completed SCRUM-19 evidence. Prefer preserving them and improving only future evidence schemas.
- Replace mutable type annotations in the frozen settings dataclass.
- Remove fixed Compose container names.
- Implement Azure Terraform only after the dedicated topology ADR is approved.
- Add sophisticated drift monitoring, canary deployment, autoscaling, and full SLO/error-budget automation before the first controlled non-production serving proof.
- Move local Prometheus/Grafana to managed services before local observability has outlived its purpose.
- Optimize image size beyond the immediate non-root/minimal serving boundary.
- Add a production PostgreSQL service until an implemented application feature actually requires it.

Items that may wait for production but **not** for an internet-accessible staging environment are HTTPS, authentication/authorization, non-default credentials, safe CORS, and secret management.

## 19. Final deployment-readiness verdict

**Verdict: not ready for cloud deployment of the forecasting capability.** The foundation FastAPI service is container-buildable and has basic metrics, health, local Kubernetes, and CI validation. Those are useful assets, but they currently deploy only a health/monitoring shell.

**Exact blockers to fix now for forecasting deployment:** no serialized/versioned final model; no load path for preprocessing state; no independent inference service or forecast route; no operational feature/input contract; no object-storage delivery/integrity/readiness contract; and no CI proof that inference works from a clean container without training. HTTPS and identity controls are additionally mandatory before public production exposure.

**Exact items safe to defer:** historical evidence/notebook path normalization, Compose naming cleanup, shallow settings immutability cleanup, full Azure infrastructure, advanced autoscaling/canary/SLO automation, and production PostgreSQL until it has a real consumer.

**SCRUM-20 decision:** SCRUM-20 can proceed before full cloud deployment if it is research, planning, or implementation work that does not claim production readiness. If SCRUM-20 depends on serving the selected forecast model, its first acceptance criteria should cover the model bundle, load-only inference boundary, input-feature contract, and artifact storage described above. A full production platform—the complete Azure production topology—is not required before SCRUM-20, but the critical serving contract should be established before more API or infrastructure code is built around assumptions.
