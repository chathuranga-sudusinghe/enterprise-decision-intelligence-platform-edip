# EDIP Phase 0 Batch 0D — RAG Configuration Contract Audit

- Audit date: 30 July 2026
- Audit mode: Read-only
- Repository: enterprise-decision-intelligence-platform-edip
- Branch audited: `chore/phase-0-batch-0d-rag-config-contract`
- Purpose: RAG configuration ownership, consistency, dependency, and migration-risk assessment
- Result type: Audit evidence; not an implementation record

> This report records a read-only repository audit. No runtime code, tests, workflows, Docker configuration, Terraform configuration, environment files, or existing audit files were changed as part of the inspection.

## 1. Purpose and Scope

This audit examined the EDIP RAG configuration contract before Phase 0 Batch 0D. Its purpose was to establish:

- the active RAG configuration flow;
- every RAG-related environment variable found in the inspected scope;
- Pinecone index and namespace values;
- embedding and chat model values;
- direct environment reads outside the typed `Settings` class;
- conflicting defaults across application code, scripts, pipelines, tests, CI, Docker, and Terraform;
- ingestion-path and output-filename conflicts;
- the current configuration ownership position;
- the smallest safe Batch 0D correction and its validation requirements.

The audit did not test live OpenAI or Pinecone connectivity, change credentials, execute ingestion, alter a Pinecone index, or implement any recommendation.

## 2. Files Inspected

The inspection covered:

- `app/core/config.py`
- `app/services/rag_query_service.py`
- `app/services/rag_generation_service.py`
- `app/api/rag.py`
- RAG references needed to trace application service construction
- `configs/rag_ingestion_config.yaml`, because the ingestion scripts identify it as their configuration input
- `configs/rag_metadata_schema.yaml`
- `scripts/build_rag_metadata.py`
- `scripts/chunk_rag_documents.py`
- `scripts/embed_rag_chunks.py`
- `scripts/load_rag_to_pinecone.py`
- `tests/unit/test_rag_query_service.py`
- `tests/unit/test_rag_generation_service.py`
- `tests/integration/test_rag_api.py`
- `tests/integration/test_rag_retrieval.py`
- `.github/workflows/integration-ci.yml`
- `.github/workflows/docker-ci.yml`
- `.github/workflows/terraform-ci.yml`
- `docker-compose.yml`
- RAG-related references under `infra/**`
- the tracked-file inventory for `.env.example` or an equivalent configuration example
- the names, but not the values, of RAG-related variables in the local `.env`
- the RAG-related inventory under `pipelines/**`

No RAG ingestion implementation or RAG ingestion orchestration was found under `pipelines/**`. The RAG ingestion implementation is currently held in standalone scripts.

## 3. Current Active RAG Configuration Flow

The confirmed active online configuration flow is:

1. `app/core/config.py` loads the repository-root `.env`.
2. It creates a frozen typed `Settings` instance named `settings`.
3. `app/main.py` consumes that instance for application metadata and CORS configuration.
4. `app/api/rag.py` registers the RAG API and calls `build_rag_query_service()` through a FastAPI dependency when `/rag/query` is invoked.
5. `build_rag_query_service()` does not use the typed `settings` instance. It independently reads OpenAI, Pinecone, retrieval, context, preview, and heading configuration from the environment.
6. The query factory constructs the OpenAI embedding client, Pinecone index client, and RAG generation service.
7. `build_rag_generation_service()` independently reads the OpenAI key, generation model, and maximum context length from the environment.
8. Terraform projects eight RAG variables into the ECS task environment.
9. Docker Compose supplies the root `.env` to the API container without declaring a separate RAG configuration contract.

The `/rag/health` endpoint returns `retrieval_ready=True` and `generation_ready=True` without validating API credentials, Pinecone index access, namespace access, OpenAI access, or external-service connectivity. It confirms route availability rather than operational RAG readiness.

The confirmed offline ingestion flow is:

```text
Markdown knowledge documents
  -> document_metadata.jsonl
  -> document_chunks.jsonl
  -> chunk_embeddings.jsonl + embedding_manifest.json
  -> Pinecone upsert + pinecone_load_manifest.json
```

The scripts name `configs/rag_ingestion_config.yaml` as their configuration input, but several of its keys and output declarations are not consumed by the current script resolvers.

## 4. Current Configuration Owner

### Confirmed facts

There is currently no single effective canonical owner.

- The intended typed owner for online application configuration is `app/core/config.py`.
- The active online RAG factories bypass that owner and read the environment directly.
- The intended ingestion owner is `configs/rag_ingestion_config.yaml`.
- Actual ingestion behaviour is determined by a combination of partially recognised YAML keys and script-local defaults.
- CI and Terraform restate or project configuration values; they are not a reliable single source of truth.
- Docker Compose passes `.env` into relevant containers but does not define the RAG contract.

### Recommended ownership

- `app/core/config.py` should own the online RAG environment contract.
- `configs/rag_ingestion_config.yaml` should own offline ingestion configuration.
- CI, Docker, and Terraform should supply or project those contracts without introducing competing names or defaults.

## 5. All RAG-Related Environment Variables

| Variable | Typed `Settings` field | Confirmed consumer or declaration |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Query factory, generation factory, embedding script, retrieval evaluator, CI, Terraform |
| `PINECONE_API_KEY` | Yes | Query factory, Pinecone loader, retrieval evaluator, CI, Terraform |
| `PINECONE_INDEX_NAME` | Yes | Query factory, CI, Terraform |
| `PINECONE_NAMESPACE` | Yes | Query factory, CI, Terraform |
| `OPENAI_EMBED_MODEL` | Yes | Query factory, CI, Terraform |
| `OPENAI_CHAT_MODEL` | Yes | Typed settings, CI, and Terraform; not consumed by the active generation factory |
| `RAG_TOP_K` | Yes | Query factory, CI, Terraform |
| `RAG_MAX_CONTEXT_CHARS` | Yes | Query factory, generation factory, CI, Terraform |
| `RAG_GENERATION_MODEL` | No | Active generation factory |
| `RAG_PREVIEW_CHARS` | No | Active query factory |
| `RAG_HEADING_LEVELS` | No | Active query factory |

The local `.env` contains the eight variables represented by the typed settings and deployment contract. Only their names were inspected. No environment-variable value, API key, token, credential, or secret was read or recorded.

No tracked `.env.example` or equivalent configuration example was found.

### Pinecone credential context

The old Pinecone account is deactivated. A new Pinecone API key will be configured separately through secure secret storage. No key is included in this report, and credential replacement is outside this read-only audit.

## 6. Pinecone Index and Namespace Values Found

| Source | Index value | Namespace value | Classification |
|---|---|---|---|
| Typed application settings | `edip-rag-index` | `edip-phase-6` | Intended application defaults |
| Online query factory | Required environment value with no internal default | Optional environment value with no internal default | Effective online runtime |
| Terraform/ECS | `edip-rag-index` | `edip-phase-6` | Deployment contract |
| Terraform variable values | `edip-rag-index` | `edip-phase-6` | Deployment input |
| Integration CI | `test-index` | `test-namespace` | Intentional non-live test placeholders |
| Ingestion YAML | `edip-rag-phase6` | `northstar-retail-v1` | Conflicting declared ingestion target |
| Pinecone loader fallback | `edip-rag-index` | `edip-phase-6` | Effective when the current YAML key is not recognised |
| Retrieval evaluator fallback | `edip-rag-index` | `edip-phase-6` | Effective when the current YAML key is not recognised |

The ingestion YAML stores its Pinecone configuration under `vector_database`. The loader and retrieval evaluator recognise `pinecone`, `vector_store`, and selected `retrieval` shapes, but not `vector_database`. The embedding script checks `pinecone` and `vector_db`, also not `vector_database`.

The declared YAML target `edip-rag-phase6` / `northstar-retail-v1` is therefore silently ignored by the current loader and retrieval evaluator, which fall back to `edip-rag-index` / `edip-phase-6`.

## 7. Embedding Model and Chat Model Values Found

### Embedding model

`text-embedding-3-small` is the only configured production or default embedding model found. It appears in:

- typed application settings;
- the online query-service default;
- the ingestion YAML;
- the embedding-script default;
- integration CI;
- Terraform.

The retrieval evaluator looks for `embedding.model`, while the ingestion YAML supplies `embedding.model_name`. It currently falls back to `text-embedding-3-small`, concealing the mismatch. A future YAML model change would not affect the evaluator unless the resolver is corrected.

### Chat model

`gpt-4.1-mini` is the only configured production or default chat model found.

- Typed settings, CI, and Terraform use `OPENAI_CHAT_MODEL`.
- The active generation factory uses `RAG_GENERATION_MODEL`.
- When `RAG_GENERATION_MODEL` is absent, the factory falls back internally to `gpt-4.1-mini`.

Changing the deployed `OPENAI_CHAT_MODEL` therefore has no effect on the active RAG generation factory.

Values such as `gpt-test`, `gpt-custom-mini`, and `gpt-4.1-mini-test` occur in tests and are test doubles rather than deployment settings.

## 8. Direct Environment Reads Outside Typed Settings

Confirmed direct reads outside `app/core/config.py` are:

| File | Direct reads |
|---|---|
| `app/services/rag_query_service.py` | `OPENAI_API_KEY`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `OPENAI_EMBED_MODEL`, `PINECONE_NAMESPACE`, `RAG_TOP_K`, `RAG_MAX_CONTEXT_CHARS`, `RAG_PREVIEW_CHARS`, `RAG_HEADING_LEVELS` |
| `app/services/rag_generation_service.py` | `OPENAI_API_KEY`, `RAG_GENERATION_MODEL`, `RAG_MAX_CONTEXT_CHARS` |
| `scripts/embed_rag_chunks.py` | `OPENAI_API_KEY` |
| `scripts/load_rag_to_pinecone.py` | `PINECONE_API_KEY` |
| `tests/integration/test_rag_retrieval.py` | `OPENAI_API_KEY`, `PINECONE_API_KEY` |

Direct secret reads in standalone credentialed scripts are operationally distinct from the duplicated online application settings. The material ownership defect is that both online RAG service factories bypass the typed `Settings` object.

## 9. Conflicting Defaults Across Application, Scripts, Pipelines, Tests, CI, Docker, and Terraform

| Layer | Confirmed configuration behaviour | Conflict or status |
|---|---|---|
| Application settings | Defaults to `edip-rag-index`, `edip-phase-6`, `text-embedding-3-small`, `gpt-4.1-mini`, top-k 5, and 12,000 context characters | Intended typed owner is bypassed by online RAG factories |
| Query service | Requires the index environment variable and permits a missing namespace | Typed index and namespace defaults are ineffective |
| Generation service | Reads `RAG_GENERATION_MODEL` | Conflicts with `OPENAI_CHAT_MODEL` used by typed settings, CI, and Terraform |
| Ingestion scripts | Use script-local defaults and recognise only selected YAML shapes | Current `vector_database` YAML section is ignored by relevant resolvers |
| Chunking script | Reads `min_words`, `max_words`, and `overlap_words` | YAML uses `target_chunk_size_min`, `target_chunk_size_max`, and `preferred_overlap` |
| Embedding script | Uses `text-embedding-3-small` and reads `embedding.model_name` | Model currently matches YAML; namespace resolver does not recognise `vector_database` |
| Retrieval evaluator | Looks for `embedding.model` and selected Pinecone shapes | Ignores YAML `embedding.model_name` and `vector_database` |
| Pipelines | No RAG ingestion pipeline or RAG orchestration was found | Standalone scripts currently own ingestion execution |
| Tests | Unit tests cover RAG service behaviour; the retrieval evaluator requires live credentials | No direct unit contract coverage was found for the ingestion resolvers or full artifact chain |
| CI | Uses non-live keys, `test-index`, `test-namespace`, and the typed model/default names | Appropriate placeholders, but does not prove live OpenAI or Pinecone operation |
| Docker | Supplies `.env` to the API container | No competing explicit RAG defaults; correctness depends on the external environment file |
| Terraform | Projects the eight typed-contract variables into ECS | `OPENAI_CHAT_MODEL` is projected but ignored by the active generation factory |

CI placeholder values are not classified as production conflicts. They are intentionally non-live and should not be treated as evidence of external-service operation.

## 10. Ingestion-Path or Output-Filename Conflicts

| Stage | Ingestion YAML declaration | Current script output or input |
|---|---|---|
| Metadata | `data/processed/rag/document_metadata.jsonl` | `data/processed/rag/document_metadata.jsonl` |
| Chunks | `rag_chunks.jsonl` and `rag_chunks.parquet` | `document_chunks.jsonl` and `document_chunks.csv` |
| Embeddings | `rag_embeddings.jsonl` and `rag_embeddings.parquet` | `chunk_embeddings.jsonl` and `chunk_embeddings.csv` |
| Embedding manifest | Not represented by the declared ingestion-manifest name | `embedding_manifest.json` |
| Pinecone load manifest | Not represented by the declared ingestion-manifest name | `pinecone_load_manifest.json` |
| Retrieval evaluation | `artifacts/reports/rag_retrieval_eval.json` | Retrieval evaluator defaults to `data/processed/rag/retrieval_test_results.json` |

The actual scripts form an internally consistent filename chain, but the YAML describes different names, formats, and report locations. This creates a risk that automation or operators following the YAML will consume missing or stale artifacts.

## 11. Risks

Confirmed risks are:

- ingestion and retrieval can silently use different Pinecone targets;
- the deployed chat-model variable can be ignored;
- duplicated parsing and defaults can drift independently;
- silent fallback can hide malformed or obsolete YAML;
- output-name drift can cause later stages to consume stale artifacts;
- `/rag/health` can report readiness without external-service validation;
- there is no tracked safe configuration example;
- ingestion configuration resolvers and the complete artifact chain lack focused contract tests;
- CI placeholders do not prove live OpenAI or Pinecone operation;
- the deactivated Pinecone account means live Pinecone validation cannot succeed until the replacement key is supplied through secure secret storage.

No evidence from this audit establishes that RAG is production-ready.

## 12. Smallest Safe Batch 0D Correction

The recommended correction is:

1. Make `app/core/config.py` the only online RAG environment reader.
2. Standardise generation on `OPENAI_CHAT_MODEL`.
3. Add typed settings for `RAG_PREVIEW_CHARS` and `RAG_HEADING_LEVELS`.
4. Make both online RAG factories consume one typed settings contract.
5. Preserve explicit validation for missing API keys.
6. Select `edip-rag-index` and `edip-phase-6` as the canonical values because these are the current application, script-fallback, retrieval-fallback, and Terraform values.
7. Align `configs/rag_ingestion_config.yaml` with the established script artifact chain and canonical Pinecone target.
8. Make the ingestion resolvers explicitly recognise the selected canonical YAML keys, including `vector_database` and `embedding.model_name`.
9. Add a safe tracked `.env.example` containing names and placeholders only.
10. Add focused contract tests so an unrecognised key cannot silently select a fallback target.

The ingestion scripts must not simply begin using the YAML's current conflicting `edip-rag-phase6` / `northstar-retail-v1` target. Doing so before resolving ownership could redirect ingestion to a different index and namespace.

## 13. Files That Should Change

Recommended Batch 0D file scope:

- `app/core/config.py`
- `app/services/rag_query_service.py`
- `app/services/rag_generation_service.py`
- `configs/rag_ingestion_config.yaml`
- `scripts/embed_rag_chunks.py`
- `scripts/load_rag_to_pinecone.py`
- `tests/integration/test_rag_retrieval.py`
- `tests/unit/test_rag_generation_service.py`
- `tests/unit/test_rag_query_service.py`
- new `.env.example`
- preferably one focused contract test such as `tests/unit/test_rag_configuration_contract.py`

`scripts/chunk_rag_documents.py` should change only if Batch 0D makes output paths dynamically owned by the YAML. The smaller alternative is to align the YAML with the script's established filenames and accepted chunk keys.

## 14. Files That Should Not Change Yet

The following should remain unchanged during the smallest safe correction:

- `app/api/rag.py`
- `app/main.py`
- `app/core/monitoring.py`
- `pipelines/**`
- `.github/workflows/**`
- `docker-compose.yml`
- `infra/**`
- RAG request and response schemas
- unrelated tests
- dependency files
- README files
- existing audit records
- local `.env`

The `/rag/health` readiness semantics should be addressed separately because changing them is API behaviour rather than configuration-contract consolidation.

Live Pinecone data, index creation, namespace migration, and replacement-secret configuration must also remain separate controlled operations.

## 15. Validation Commands Required After Cleanup

The recommended model-free and configuration validation is:

```bash
grep -RIn "os\.getenv\|os\.environ" \
  app/services/rag_query_service.py \
  app/services/rag_generation_service.py

grep -RIn \
  "RAG_GENERATION_MODEL\|OPENAI_CHAT_MODEL\|PINECONE_INDEX_NAME\|PINECONE_NAMESPACE" \
  app scripts tests .github/workflows infra .env.example

python -B -c "from app.core.config import Settings; from app.main import app; print(app.title)"
python -m compileall -q app scripts tests

pytest -q \
  tests/unit/test_rag_generation_service.py \
  tests/unit/test_rag_query_service.py \
  tests/unit/test_rag_configuration_contract.py \
  tests/integration/test_rag_api.py

python scripts/build_rag_metadata.py --help
python scripts/chunk_rag_documents.py --help
python scripts/embed_rag_chunks.py --help
python scripts/load_rag_to_pinecone.py --help
python tests/integration/test_rag_retrieval.py --help

docker compose config --quiet
terraform -chdir=infra/terraform/aws fmt -check
terraform -chdir=infra/terraform/aws validate

git diff --check
git status --short
git diff --stat
```

After a replacement Pinecone API key has been configured through secure secret storage, a separate credentialed validation should confirm that ingestion and retrieval use the same live index, namespace, and embedding model. That validation must not disclose the key and must not be conflated with model-free unit and contract tests.

## 16. Residual Limitations

Even after the recommended correction:

- configuration tests will not prove live OpenAI or Pinecone access;
- Docker configuration validation will not prove container runtime correctness;
- Terraform validation will not prove deployment readiness;
- the RAG health endpoint will remain a route-level readiness claim until separately corrected;
- the existing Pinecone corpus, vector dimensions, metadata completeness, and index contents will require credentialed verification;
- replacement-secret provisioning will remain an operational security activity;
- standalone scripts will remain outside an orchestrated RAG pipeline unless a later batch introduces controlled orchestration;
- changing an embedding model would require explicit compatibility and re-indexing assessment.

## 17. Rollback Approach

No implementation was performed during this audit, so no runtime rollback is required.

For a future Batch 0D implementation, rollback should restore every tracked file in the approved change set to the pre-batch commit and remove only new Batch 0D files after their exact paths have been verified. The prior environment contract and Pinecone target must be recorded before deployment. A credential or index rollback must be handled through secure secret and infrastructure processes, not through source control.

A safe source rollback pattern for tracked files is:

```bash
git restore --source=<pre-batch-commit> --staged --worktree -- \
  app/core/config.py \
  app/services/rag_query_service.py \
  app/services/rag_generation_service.py \
  configs/rag_ingestion_config.yaml \
  scripts/embed_rag_chunks.py \
  scripts/load_rag_to_pinecone.py \
  tests/integration/test_rag_retrieval.py \
  tests/unit/test_rag_generation_service.py \
  tests/unit/test_rag_query_service.py
```

Any new `.env.example` or contract-test file should be removed only if it was introduced by the batch and its exact path has been confirmed. The local `.env`, secure secret storage, live Pinecone indexes, and Pinecone namespaces must not be altered by this source rollback.

## 18. Professional Reflection

This inspection demonstrates that configuration ownership is a systems concern rather than a naming exercise. The online API, offline ingestion scripts, tests, CI, Docker, and Terraform each expose only part of the RAG operating model. Individually reasonable defaults become risky when one layer silently ignores another layer's contract.

The smallest controlled correction should preserve established runtime behaviour while removing ambiguity. In particular, switching a resolver to a previously ignored Pinecone target could redirect data even though the code change appears small. The correction therefore needs explicit ownership, contract tests, separate credential handling, and clear separation between model-free validation and credentialed external-service evidence.

Treating the deactivated Pinecone account and replacement key as a separate secure operational change also preserves an important boundary: repository configuration may define variable names and expected behaviour, but it must not contain or expose live credentials. This supports traceability, reversibility, and evidence-based migration without overstating production readiness.
