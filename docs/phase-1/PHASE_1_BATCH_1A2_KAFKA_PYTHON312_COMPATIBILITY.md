# EDIP Phase 1 Batch 1A.2: Kafka Python 3.12 Compatibility

**Status:** Implemented and locally validated
**Evidence date:** 2026-08-02
**Branch:** `fix/phase-1-kafka-python312-compatibility`
**Scope:** Kafka Python client import compatibility and dependency alignment only

## 1. Purpose and evidence boundary

This record documents the bounded correction of the Kafka Python client contract after EDIP standardized on Python 3.12. It separates confirmed local evidence from capabilities that were not exercised.

Confirmed evidence covers clean dependency installation, Kafka client imports, fake-backed producer and consumer unit tests, full pytest collection, the existing runtime dependency contract, Python byte compilation, and Docker Compose configuration parsing.

This batch did not start Kafka, execute a live-broker flow, run the complete test suite, or validate broker protocol, authentication, authorization, network, delivery, retry, or operational behavior. It does not establish production readiness.

## 2. Original failure

With Python 3.12.3 and the previously pinned `kafka-python==2.0.2`, both required import probes failed before any broker connection:

```text
ModuleNotFoundError: No module named 'kafka.vendor.six.moves'
```

The traceback originated in `kafka/codec.py` while importing `range` from the package's vendored `six` namespace. This prevented collection of:

- `tests/integration/test_kafka_end_to_end_flow.py`
- `tests/unit/test_kafka_consumer.py`
- `tests/unit/test_kafka_producer.py`

The fault was therefore a Python-package import compatibility problem, not evidence of a Kafka broker or network failure.

## 3. Inspected APIs and usage

Direct imports from the `kafka` namespace occur only in the following scripts.

| File | Imported API | Confirmed use |
|---|---|---|
| `scripts/kafka_producer.py` | `KafkaProducer`, `KafkaError` | Producer construction, serializer configuration, `send(...).get(...)`, `flush()`, and `close()` |
| `scripts/kafka_consumer.py` | `KafkaConsumer` | Consumer construction, topic subscription through constructor arguments, message iteration, and `close()` |
| `scripts/init_kafka_topics.py` | `KafkaAdminClient`, `NewTopic`, `TopicAlreadyExistsError` | Topic listing, topic definitions, `create_topics(...)`, duplicate-topic handling, and `close()` |

The inspected tests replace producer, consumer, service, and message behavior with deterministic fakes. The code's topics, event schemas, retry values, serializer behavior, security settings, and business logic were not changed.

## 4. Package options considered

### 4.1 Retain `kafka-python==2.0.2`

Rejected. A clean Python 3.12.3 environment reproduced the known `kafka.vendor.six.moves` failure for both public import probes.

### 4.2 Upgrade the existing `kafka-python` distribution

Selected. Running an unversioned upgrade query in the disposable environment resolved the current published release to `kafka-python==3.0.9`. The package retained the existing `kafka` import namespace and all APIs required by EDIP. The required imports, fake-backed tests, and full collection passed without source changes.

### 4.3 Change distribution name

Not selected. Alternatives such as a separately named distribution would change the dependency contract even if they exposed a compatible `kafka` namespace. EDIP's source imports are namespace-based, so a replacement exposing the same namespace might avoid code changes, but that alternative was unnecessary and was not treated as validated evidence after the maintained existing distribution passed.

### 4.4 Patch vendored compatibility code or add an import workaround

Rejected. Patching site-packages, adding a `six` shim, or changing EDIP imports would create local behavior outside the authoritative manifests and would be larger and less reproducible than correcting the package pin.

## 5. Selected dependency and rationale

The selected runtime dependency is:

```text
kafka-python==3.0.9
```

Selection was evidence-led rather than guessed:

1. `requirements-dev.txt` was installed into a disposable Python 3.12.3 environment, reproducing the failure with 2.0.2.
2. An unversioned `pip install --upgrade kafka-python` resolved to 3.0.9 on 2026-08-02.
3. Both required public import probes passed.
4. The 25 fake-backed Kafka unit tests passed.
5. Full pytest collection exited zero with 168 tests collected.
6. A second clean Python 3.12.3 environment installed the edited manifests and repeated the validations.

No broad dependency upgrade was performed in the repository.

## 6. Source compatibility result

No Python source or test changes were required. The existing producer, consumer, administration, topic, and error APIs remained import-compatible with `kafka-python==3.0.9`.

## 7. Docker Compose alignment

Compose contained five independent, unpinned installations of `kafka-python`:

- one in `kafka-topic-init`;
- four in the Airflow initialization, API server, scheduler, and DAG processor commands.

These installations are part of the same Python Kafka client contract because they install the distribution at container startup for repository scripts or workflows using the `kafka` namespace. All five were aligned to `kafka-python==3.0.9`. No Compose services, commands, dependencies other than this Kafka token, topics, or orchestration behavior were otherwise changed.

`docker compose config --quiet` exited zero on Windows. Docker was not available inside the WSL distribution, so the equivalent WSL invocation reported that the `docker` command was unavailable; Docker Desktop's Windows CLI provided the successful configuration validation. No containers were started.

## 8. Files changed

| File | Change |
|---|---|
| `requirements.txt` | Replaced `kafka-python==2.0.2` with the validated `kafka-python==3.0.9` pin |
| `docker-compose.yml` | Replaced five unpinned Kafka client installations with `kafka-python==3.0.9` |
| `docs/phase-1/PHASE_1_BATCH_1A2_KAFKA_PYTHON312_COMPATIBILITY.md` | Added this inspection and implementation record |

No Kafka scripts, tests, application capabilities, CI configuration, LangGraph, RAG, forecasting, PostgreSQL, frontend, infrastructure, or monitoring files were changed.

## 9. Validation results

The authoritative post-edit validation environment was a newly created Python 3.12.3 virtual environment under `/tmp`, outside the repository.

| Validation | Result |
|---|---|
| Install `requirements-dev.txt` | Passed; installed the edited runtime manifest including `kafka-python==3.0.9` |
| `python -m pip check` | Passed: `No broken requirements found.` |
| `from kafka import KafkaProducer, KafkaConsumer` | Passed |
| `from kafka.admin import KafkaAdminClient, NewTopic` | Passed |
| Kafka producer and consumer unit tests | Passed: 25 tests |
| `pytest --collect-only -q` | Passed: 168 tests collected; exit code 0 |
| Runtime dependency contract | Passed: 3 tests |
| `python -m compileall -q app scripts tests` | Passed; exit code 0 |
| `docker compose config --quiet` | Passed on Windows; exit code 0 |

The Kafka unit tests are fake-backed and required no live Kafka broker. They demonstrate local code/API compatibility, not live message delivery.

The Kafka package emitted 218 deprecation warnings during import-heavy pytest runs because its schema loader uses legacy `importlib.resources` helpers. Pytest also reported the existing permission warning when attempting to write `.pytest_cache` on the WSL-mounted repository. Neither warning caused a test or collection failure.

## 10. Residual limitations

- No live Kafka broker was started, and no end-to-end broker exchange was executed.
- Broker-version interoperability, topic creation against a broker, authentication, authorization, TLS, networking, partitions, consumer groups, offsets, retries, acknowledgements, and delivery guarantees remain unvalidated.
- Full pytest collection is restored, but the full 168-test suite was not executed in this batch.
- The package's legacy `importlib.resources` calls produce deprecation warnings under Python 3.12; they are upstream warnings and are not fixed here.
- Compose still performs startup-time package installation for several services. This batch only pins the Kafka client consistently; image-build dependency ownership remains a separate architecture and delivery concern.
- The WSL-mounted repository does not permit pytest to update its existing cache directory in this environment. Tests and collection still exit zero.
- A future Kafka version change requires a new clean-environment compatibility probe rather than an unreviewed upgrade.

## 11. Rollback instructions

To roll back only this batch before commit:

1. Restore `requirements.txt` and `docker-compose.yml` from the branch baseline.
2. Remove this Batch 1A.2 record.
3. Recreate the disposable environment from the restored manifests.
4. Run the import probes and collection again, recording that the Python 3.12 blocker is expected to return with 2.0.2.

A rollback to 2.0.2 is mechanically simple but knowingly restores the confirmed Python 3.12 import and collection failure.

## 12. Professional reflection

The smallest safe correction was a tested dependency pin, not an application-code workaround. Probing the maintained distribution first preserved the existing API contract and avoided introducing a second package identity or local compatibility shim. Aligning all Compose installations prevents local tests and container startup from silently selecting different Kafka clients. The evidence remains deliberately bounded: deterministic fakes and successful collection establish compatibility and test discoverability, while live-broker reliability requires a separately approved integration validation.

## 13. CI event-fixture reproducibility follow-up (2026-08-02)

### CI failure root cause

PR #26 exposed an environment-dependent test contract. `tests/integration/test_kafka_event_generation.py` read all eight JSONL outputs directly from `data/exports/kafka_events/`, but that generated directory is intentionally Git-ignored. The generator also reads eight CSV inputs from `data/synthetic/`; those datasets are likewise Git-ignored, with only `.gitkeep` tracked. A developer workspace containing prior generated files therefore passed while a clean GitHub Actions checkout failed at `test_expected_topic_files_exist`.

The CI workflow was not the correct ownership point for the fix. Adding a generation command there would still require unavailable ignored datasets and would preserve the test's dependency on repository runtime paths.

### Reproducibility fix

The integration module now owns a module-scoped pytest fixture built with `tmp_path_factory`. The fixture:

- writes one minimal deterministic CSV row for every source table expected by the existing generator;
- selects values that exercise the existing low-stock, delayed-shipment, and approved-replenishment filters;
- injects temporary synthetic and output directories through the existing `scripts.generate_phase_6_kafka_events.Paths` contract;
- calls the existing configuration loader, `generate_all_events`, and `save_topic_outputs` functions;
- replaces random event-ID generation only inside the fixture with a stable test-only function; and
- returns the temporary output path to the unchanged topic, envelope, schema, uniqueness, timestamp, and business-rule assertions.

No production generator, production path, topic, event schema, dependency, or CI workflow changed.

### Follow-up files changed

- `tests/integration/test_kafka_event_generation.py`
- `docs/phase-1/PHASE_1_BATCH_1A2_KAFKA_PYTHON312_COMPATIBILITY.md`

### Follow-up validation

Validation started by removing the eight local generated JSONL files and the `data/exports/kafka_events/` directory. Results in the disposable Python 3.12 environment were:

| Validation | Result |
|---|---|
| Kafka event-generation integration module | Passed: 54 tests |
| Unit suite | Passed: 91 tests |
| Integration suite | Passed: 77 tests |
| Full suite | Passed: 168 tests |
| `python -m compileall -q app scripts tests` | Passed |
| Repository Kafka output directory after tests | Absent; tests wrote only under pytest temporary storage |
| `git ls-files data/exports/kafka_events` | No output; no generated Kafka event files are tracked |

The test evidence remains local and deterministic. It does not demonstrate a live Kafka broker exchange or external-service operation. The existing upstream `kafka-python` deprecation warnings and WSL-mounted `.pytest_cache` permission warning remain non-failing limitations.
