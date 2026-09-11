# Python packaging modernization

`pyproject.toml` is the authoritative Python metadata, dependency, and tool configuration. This change does not alter application/model logic, infrastructure, research evidence, or CI orchestration.

## Files changed

- `pyproject.toml`: PEP 621 metadata, runtime/dev dependencies, explicit package discovery, MyPy and Pytest configuration; existing Ruff settings preserved exactly.
- Both former requirements files: deleted after removing their last active technical use.
- `pytest.ini`: removed after moving both settings unchanged into the manifest.
- `Dockerfile`: copies the manifest and existing serving-source subset before installing `.`; removes generated build metadata afterward.
- `.github/workflows/integration-ci.yml`: installs `.[dev]` and keys pip caching on `pyproject.toml`; all jobs, triggers, and test commands remain unchanged.
- `README.md`: development/runtime installation and tool commands, plus installed-package path guidance.
- Five Favorita notebooks listed below: one root-marker condition changed in each; research logic, outputs, execution counts, and metadata preserved.
- `docs/PYTHON_PACKAGING.md`: this handoff and validation record.

## Manifest structure

- `[build-system]`: `setuptools>=77`, backend `setuptools.build_meta`.
- `[project]`: name `enterprise-decision-intelligence-platform-edip`, version `1.0.0` (aligned with the existing default API version), description, Python `>=3.12`, and pinned runtime dependencies. Python 3.12 remains the tested CI/container baseline; later interpreters have not been validated.
- `[project.optional-dependencies]`: `dev` contains the four tools below.
- `[tool.setuptools]`: package data disabled.
- `[tool.setuptools.packages.find]`: only `app`, `app.*`, `pipelines`, and `pipelines.*`; namespace discovery enabled because some directories lack tracked `__init__.py` files.
- `[tool.ruff]` and `[tool.ruff.lint]`: unchanged target, line length, exclusions, rules, and ignores.
- `[tool.mypy]`: Python 3.12, `app` and `pipelines`, namespace packages and explicit package bases. There was no previously configured or CI-enforced MyPy scope. This establishes a visible baseline without hiding errors.
- `[tool.pytest.ini_options]`: preserves `pythonpath = ["."]` and `testpaths = ["tests"]`.

Explicit discovery avoids flat-layout ambiguity and excludes unrelated top-level directories. See the [Setuptools package discovery documentation](https://setuptools.pypa.io/en/stable/userguide/package_discovery.html). The built wheel was inspected: only application/pipeline packages and distribution metadata are present, without data, artifacts, notebooks, UI, temporary outputs, or research evidence.

## Dependencies

All 14 runtime pins were compared directly with the decoded original requirements file and match exactly:

- `fastapi==0.117.1`
- `uvicorn==0.41.0`
- `python-dotenv==1.2.2`
- `pydantic==2.12.5`
- `pydantic-settings==2.13.1`
- `pandas==3.0.1`
- `numpy==2.4.3`
- `pyarrow==25.0.0`
- `langgraph==1.2.10`
- `requests==2.32.5`
- `httpx==0.28.1`
- `prometheus-client==0.24.1`
- `lightgbm==4.7.0`
- `optuna==4.9.0`

Development dependencies retained:

- `pytest==9.0.2`
- `pytest-cov==7.0.0`
- `ruff==0.16.5`
- `mypy==1.19.1`

Black 26.3.1 and isort 8.0.1 were removed from the development dependency set after a tracked-repository audit found no invocation or configuration outside their dependency declarations. Ruff already enables import sorting (`I`); Ruff formatting is now the documented formatter. No source files were reformatted and no new CI gates were introduced.

## Docker and installation behavior

Development: `python -m pip install -e ".[dev]"` (or non-editable `python -m pip install ".[dev]"`). Runtime: `python -m pip install .`. Run installation commands from the repository root.

The Dockerfile keeps Python 3.12 slim, `libgomp1`, `curl`, `/app`, `PYTHONPATH=/app`, port 8000, and the existing Uvicorn command. It copies the same application/inference/runtime-path source subset and installs no development tools. Research dependencies remain in the runtime set to preserve the original pins. Installing after copying source means source changes invalidate the dependency installation layer.

Wheel imports were checked from outside the checkout. Editable installation is preferred for local pipeline work: existing defaults derive filesystem paths from module locations. For a non-editable installation, configure absolute `EDIP_FAVORITA_SOURCE_PATH`, `EDIP_ARTIFACT_ROOT`, and `EDIP_FAVORITA_MODEL_BUNDLE_PATH` paths as appropriate. Local `.env` discovery also remains relative to the installed module layout; production should supply environment variables. No path logic was changed.

## Requirements-reference audit

The entire tracked working tree was searched, including notebooks. Classification before the follow-up edit:

| Category | Findings and action |
| --- | --- |
| Active runtime/build dependency | None; Docker already installs the project from its manifest. |
| Active CI dependency | None; CI already installs the development extra and keys its cache on the manifest. |
| Notebook/root-marker convenience | Five helpers listed below; migrated to a directory signature. |
| Historical documentation/evidence | Five mentions in the two documents listed below; preserved unchanged. |
| Obsolete | Both compatibility wrappers and this report's retention instructions; wrappers deleted and instructions updated. |

Changed notebook helpers:

- `notebooks/favorita/01_data_inventory_and_quality.ipynb:72`
- `notebooks/favorita/02_temporal_sales_and_coverage_eda.ipynb:72`
- `notebooks/favorita/03_build_favorita_merged_base.ipynb:61`
- `notebooks/favorita/05_define_data_cleaning_rules.ipynb:51`
- `notebooks/favorita/archive/04_review_merged_dataset_quality.ipynb:54`

Each helper walks the same ancestors as before and recognizes the simultaneous presence of the `app`, `pipelines`, `data`, and `notebooks` directories. It does not depend on a package provider, dependency filename, or Git metadata. The root, derived data/artifact paths, and outside-repository error are preserved. No research cells were run. The archive notebook's edited line uses LF to avoid an inherited CRLF whitespace warning; other bytes retain their original formatting.

Exact remaining tracked filename references are historical mentions of `requirements.txt` in:

- `docs/audits/EDIP_CLOUD_DEPLOYMENT_READINESS_AUDIT.md:67`
- `docs/audits/EDIP_CLOUD_DEPLOYMENT_READINESS_AUDIT.md:127`
- `docs/audits/EDIP_CLOUD_DEPLOYMENT_READINESS_AUDIT.md:218`
- `docs/validation/FAVORITA_DOCKER_LOCAL_SERVING.md:9`
- `docs/validation/FAVORITA_DOCKER_LOCAL_SERVING.md:88`

There are no active filename references. This new, currently untracked report also mentions `requirements.txt` and `requirements-dev.txt` to document their removal; these are explanatory references only. Both files can be and have been deleted. The follow-up explicitly authorizes deletion once active technical dependencies are removed; unrelated formatter/type-check debt does not require keeping wrappers.

## Initial validation (before wrapper removal)

- Existing environment: `pip check` passed; 270 unit tests and 9 integration tests passed.
- `ruff check .`: passed.
- `ruff format --check .`: 28 files need formatting; 36 already formatted. The same failures existed before the edit.
- `mypy`: 61 errors in 12 files, checking 28 source files. This matches the pre-edit invocation with explicit package bases, including missing pandas/PyArrow stubs and existing type errors. No errors were suppressed.
- Standard wheel build: passed; 33 entries, approximately 92 KB; imports verified outside the checkout.
- Minimal tracked Docker-source subset wheel: passed; exactly the expected 12 Python modules, approximately 12 KB. This is packaging validation, not a substitute for a Docker build.
- `docker build -t edip-pyproject-validation:local .`: blocked before build steps because Docker Desktop could not resolve `registry-1.docker.io` while resolving `python:3.12-slim`.
- Original runtime pins and Ruff configuration: exact equality checks passed.
- `python -m pip install -e ".[dev]"`: passed in the existing Python 3.12 environment; all 18 declared runtime/dev pins match exactly and post-install `pip check` passed. A separate clean Python 3.12 environment resolved dependencies and began downloading wheels, but was stopped because downloads were impractically slow (the NumPy wheel showed approximately 17 minutes remaining at 15.7 KB/s). Clean-environment installation is therefore incomplete, not a pass.
- Post-install tests: all 279 unit/integration tests passed together; Ruff lint passed again.
- `git diff --check`: passed.

## Follow-up validation

- Editable installation with the development extra: passed in the existing Python 3.12 environment after deleting both wrappers.
- `pip check` and `ruff check .`: passed.
- Notebook root detection: 30 cases passed across all five helpers, including repository root, notebook/archive directories, a checkout without Git metadata, an incomplete nested marker, and outside-repository failure. JSON comparison confirms only the intended source condition changed; stored research outputs and metadata are unchanged.
- `pytest tests/unit`: 270 passed.
- `pytest tests/integration`: 9 passed.
- Repository search: only the five historical tracked mentions listed above remain; this new report adds explanatory mentions on lines 87 and 95 and deletion-staging instructions on line 135.
- `git diff --check`: passed.
- `docker build -t edip-pyproject-validation:local .`: passed. Container API, inference, and LightGBM imports also passed with networking disabled and a read-only filesystem; no model bundle was loaded and this is not a forecast end-to-end test.
- The 28 formatter findings and 61 MyPy errors remain pre-existing technical debt. They were not fixed, suppressed, or re-scoped in this follow-up.

## Handoff

Branch: `chore/python-pyproject-modernization`. The working tree is Python-only; the earlier Terraform IAM edit is absent. No commit, push, branch change, or other Git-changing operation was performed.

The manifest is the sole Python dependency/configuration source. Notebook root markers no longer require compatibility files. Historical evidence is preserved. Direct dependency pins are unchanged; transitive dependencies remain unlocked, as before.

Suggested future commit: `chore(python): migrate dependencies to pyproject`. Review the scoped diff and validation results before staging. No PR is proposed in this task.


After reviewing the Python-only diff, the suggested staging and commit commands are below. They have not been executed:

```bash
git add -- pyproject.toml Dockerfile README.md .github/workflows/integration-ci.yml pytest.ini requirements.txt requirements-dev.txt docs/PYTHON_PACKAGING.md notebooks/favorita/01_data_inventory_and_quality.ipynb notebooks/favorita/02_temporal_sales_and_coverage_eda.ipynb notebooks/favorita/03_build_favorita_merged_base.ipynb notebooks/favorita/05_define_data_cleaning_rules.ipynb notebooks/favorita/archive/04_review_merged_dataset_quality.ipynb
git commit -m "chore(python): migrate dependencies to pyproject"
```

Next terminal command: `git diff --stat`. Next engineering step: review the complete migration and the new report before staging only the listed files.
