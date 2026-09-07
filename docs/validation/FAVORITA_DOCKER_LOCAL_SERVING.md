# Local Favorita serving in Docker

This validates the existing FastAPI application and synchronous `FavoritaBundlePredictor` with an already exported bundle. It does not train, tune, evaluate, or establish production forecast quality.

This Compose configuration and host bind-mount strategy are for **local development and local validation only**. They do not define the future Azure architecture. Azure model delivery will be handled separately later; the same serving image should remain reusable. A future Azure deployment should supply environment configuration externally, including `EDIP_FAVORITA_MODEL_BUNDLE_PATH` pointing to the model location made available inside the container. No Azure resource names, external service URLs, or credentials belong in the image.

## Image and model delivery

The root `Dockerfile` uses Python 3.12, installs the existing pinned `requirements.txt`, and starts one Uvicorn process at `0.0.0.0:8000`. `libgomp1` supplies LightGBM's OpenMP runtime. Only the app, inference module and runtime path helper are copied into the image. Training/evaluation source, datasets, model bundles, and the repository `.env` are not copied. The runtime requirements still include research dependencies; splitting dependencies is deferred.

The application loads the bundle during lifespan startup. Requests reuse that predictor. Startup fails if the bundle cannot be loaded; the server does not accept requests before startup completes. `/ready` returns 503 when the application has no predictor, and 200 after successful loading. `/health`, `/api/v1/forecast`, and `/metrics` retain their existing behavior.

## Build and run

Run from the repository root in Linux/WSL. Choose an existing bundle containing `metadata.json` and `model.txt`; the sample below is the small local API-test bundle used for this validation, not a production model.

```bash
docker build -t edip-favorita:local .

FAVORITA_MODEL_BUNDLE_DIR=./artifacts/models/favorita_local_api_test_20260907101754
docker run -d --name edip-favorita-local \
  -p 127.0.0.1:8000:8000 \
  --mount "type=bind,source=$(realpath "$FAVORITA_MODEL_BUNDLE_DIR"),target=/models/favorita,readonly" \
  -e APP_ENV=local \
  -e EDIP_FAVORITA_MODEL_BUNDLE_PATH=/models/favorita \
  edip-favorita:local

docker logs edip-favorita-local
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body http://127.0.0.1:8000/ready
curl --fail-with-body http://127.0.0.1:8000/metrics
curl --fail-with-body -X POST http://127.0.0.1:8000/api/v1/forecast \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/favorita-forecast-request.json
```

The request file is an existing local validation input, not a tracked or image-baked asset. On another machine, supply an equivalent model-ready JSON request matching that bundle's feature contract. Host paths are resolved by the shell only for Docker's bind mount; the application sees `/models/favorita`. No host repository path is stored in Docker configuration. The model mount is read-only and does not require write access.

For Compose, start only the API service:

```bash
FAVORITA_MODEL_BUNDLE_DIR=./artifacts/models/favorita_local_api_test_20260907101754 \
  docker compose up -d --build api
```

Compose defaults to `./artifacts/models/favorita_time_aware` when the variable is absent and rejects a missing source directory. It no longer mounts the source repository. The existing API `env_file: .env` is preserved: provide the local `.env` file (it may be empty if no additional settings are needed). Explicit API environment entries override that file for `PYTHONPATH=/app`, `APP_ENV=local`, and `EDIP_FAVORITA_MODEL_BUNDLE_PATH=/models/favorita`, preventing a host model path from leaking into the container setting. The file is supplied at runtime and excluded from the image. Compose also uses `.env` for variable interpolation. Set `FAVORITA_API_HOST_PORT` to change the API host port; it defaults to 8000 and stays bound to `127.0.0.1`. The container continues to listen on `0.0.0.0:8000`. Adjust the curl URLs if using a different host port. Stop the direct-run container before using Compose on the same port. PostgreSQL, Prometheus, and Grafana retain their existing configuration. Their pre-existing development credentials and published ports are local-stack concerns, not cloud deployment defaults; the full Compose stack must not be treated as a production deployment template.

Cleanup for the direct-run example:

```bash
docker stop edip-favorita-local
docker rm edip-favorita-local
```

## Scope and deferred work

No Azure deployment, Terraform, or CI/CD changes are part of this work. Existing Docker CI builds the image only. Production model validation, image hardening, dependency splitting, concurrency/load testing, and cloud deployment are deferred. A small test model can return constant predictions: matching real predictions on reordered rows alone cannot prove ordering. A distinct sentinel prediction check can separately verify that the API preserves row positions.

## Recorded validation — 2026-09-07

- Final `docker build -t edip-favorita:local .`: passed, including installing the unchanged UTF-16 requirements file with pip. The final rebuild reused the installed dependency layer.
- Default Docker startup: one Uvicorn server process, application startup complete, listening on `0.0.0.0:8000`.
- `curl /health`: HTTP 200, `{"status":"ok","app":"EDIP API","version":"1.0.0"}`.
- `curl /ready`: HTTP 200, `{"status":"ready","favorita_predictor_loaded":true}`.
- `curl POST /api/v1/forecast` with the existing request: HTTP 200, `{"predictions":[15.5]}`, matching the load-only host reference.
- `curl /metrics`: HTTP 200 with Prometheus text output.
- A temporary in-container check using the existing bundle counted exactly one loader call across repeated and batched forecasts. It verified readiness is 503 before startup and after shutdown, 200 after loading, and that an unavailable bundle fails closed. No model fitting was performed.
- Ordering: real batched predictions matched per-row predictions; preprocessing retained the input horizon order `[3, 1, 2]`; a separate patched predictor returning distinct horizon values confirmed the API returned `[3.0, 1.0, 2.0]`. The real test bundle returns constant predictions, so real-model outputs alone are not discriminating ordering evidence.
- The temporary lifecycle check also passed with `--read-only` for the entire container filesystem. No training, feature-building, evaluation, or Optuna modules were imported.
- Default startup with a missing bundle exited nonzero instead of serving traffic.
- Docker mount inspection reported `writable=false`; an attempted temporary write failed with `EROFS`. Both model-file checksums remained unchanged.
- Image checks found no repository `.env` files, datasets, model artifacts, or training/evaluation source under `/app`. Explicit copies and ignore rules keep local credential files outside the image; this is not a comprehensive secret-scanner audit of third-party layers.
- `docker image inspect` reported 227,358,083 bytes (about 227 MB / 217 MiB); this is Docker's reported image size, not a runtime memory measurement.
- `FAVORITA_MODEL_BUNDLE_DIR=./artifacts/models/favorita_local_api_test_20260907101754 docker compose config --quiet`: passed. The Compose stack was not started.
- `.venv/bin/python -m pytest -q tests/integration/test_favorita_forecast_api.py -k 'startup_fails_safely or unavailable_before_startup'`: 3 passed, 3 deselected. These selected tests require no training; tests that build a tiny model were not run.
- `git diff --check`: passed. No repository Python code changed, so Ruff/MyPy were not required.

The temporary validation container was stopped and removed after checks; `edip-favorita:local` remains available locally. The existing bundle and request remain outside Git and outside the image. This is local serving validation of an API-test bundle, not validation of the selected production model or its predictive quality.


## Focused portability review

- `/app`, `/models/favorita`, `0.0.0.0`, and container port 8000 are stable internal conventions, not host/deployment hardcoding.
- `FAVORITA_MODEL_BUNDLE_DIR` controls the host model directory; the mount remains read-only. The timestamped bundle and temporary request path above identify local validation inputs and must be replaced with available inputs on another machine. Neither is baked into the image.
- `FAVORITA_API_HOST_PORT` controls the Compose API host port while exposure stays loopback-only.
- The API's original `.env` runtime import is restored. Unrelated Compose services are unchanged.
- No machine-specific paths, LAN addresses, Azure resource names, or cloud service dependencies were introduced. Loopback URLs are local validation endpoints only.
- The Dockerfile installs no development requirements or compiler toolchain. The shared `requirements.txt` still includes research packages, so this is not yet a minimal inference-only dependency set. Splitting that file is deferred because this review is restricted to four Docker/documentation files and preserves the existing dependency source.
- Review checks passed: `docker compose config` (JSON output captured without displaying environment values), custom host port 18000 and model-source overrides, read-only mount assertions, and `git diff --check`. Resolved PostgreSQL, Prometheus, and Grafana service configuration exactly matched the committed baseline. Existing API environment values were preserved except the intentional local app/model overrides.
- Four-file scanning found no user-home/mount paths, Windows drive paths, `192.168.*` addresses, Azure resource identifiers, or common secret-token formats. HTTP URLs were limited to local validation endpoints. The existing unrelated services' development password defaults remain present and were not misclassified as a clean credential-free Compose configuration.
- No new image build or runtime test was needed for this follow-up: only Compose configuration and documentation changed; the preceding image/startup/forecast results still apply to the unchanged Dockerfile.
