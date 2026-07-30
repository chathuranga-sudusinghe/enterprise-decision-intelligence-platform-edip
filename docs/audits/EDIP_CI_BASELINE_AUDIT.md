# EDIP CI Baseline Audit

- Audit date: 30 July 2026
- Repository: `enterprise-decision-intelligence-platform-edip`
- Audit mode: Read-only inspection of three GitHub Actions workflow definitions
- Files inspected:
  - `.github/workflows/integration-ci.yml`
  - `.github/workflows/docker-ci.yml`
  - `.github/workflows/terraform-ci.yml`
- Change scope: Documentation only
- Operational status: Configuration evidence; no workflow run or external service was executed

## 1. Purpose and scope

This audit records what the three selected GitHub Actions workflows are configured to do, what evidence a successful run would provide, and what remains unproven. It does not inspect or modify workflow dependencies, application source, tests, Docker definitions, Terraform modules, infrastructure, or existing audit records.

No current GitHub Actions run logs were inspected. Statements about workflow behaviour are therefore based on the YAML definitions, not on a verified current run.

## 2. Executive conclusion

The repository contains substantive CI configuration for Python tests, Docker image construction, and Terraform formatting and validation. The workflows provide useful early feedback, but they do not establish complete system correctness or deployment readiness.

In particular:

- full pytest currently has known Kafka- and Pinecone-related problems;
- a successful Docker build proves image construction, not application startup or runtime correctness;
- `terraform validate` proves configuration-level validity, not deployability or operational readiness; and
- current CI does not prove live OpenAI, Pinecone, Kafka, PostgreSQL, Airflow, AWS, or Kubernetes operation.

## 3. Workflow summary

| Workflow | Primary purpose | Runner | Principal command evidence |
|---|---|---|---|
| `integration-ci.yml` | Install Python dependencies and run unit and integration test directories | `ubuntu-latest` | `pytest tests/unit` and `pytest tests/integration` |
| `docker-ci.yml` | Confirm that the repository Docker build can produce an image | `ubuntu-latest` | `docker build -t edip-api-ci:latest .` |
| `terraform-ci.yml` | Check formatting and static validity of local-k8s and AWS Terraform configurations | `ubuntu-latest` | `terraform fmt -check -recursive` and `terraform validate` |

## 4. Integration CI workflow

### 4.1 Purpose

`integration-ci.yml` defines one job named `Run unit and integration tests`. It checks out the repository, provisions Python, installs the two declared requirements files when present, and runs the unit and integration test directories as separate pytest invocations.

### 4.2 Branch and path triggers

| Event | Branch filters | Path filters |
|---|---|---|
| `push` | `main`, `master`, `develop`, `dev`, `feature/**` | None |
| `pull_request` | Target branches `main`, `master`, `develop`, `dev` | None |
| `workflow_dispatch` | Manual | None |

With no path filter, any qualifying repository change can trigger this workflow. The YAML does not establish whether all listed long-lived branches still exist or remain part of the current branching policy.

### 4.3 Runtime and actions

- Runner: `ubuntu-latest`, which is a moving GitHub-hosted runner label rather than a fixed operating-system image.
- Checkout: `actions/checkout@v4`.
- Python setup: `actions/setup-python@v5`.
- Python version: `3.11`.
- Pip caching: enabled through `cache: "pip"`.

The workflow pins action major versions but not immutable action commit SHAs.

### 4.4 Environment and external-service assumptions

The job defines test-mode application configuration and placeholder OpenAI and Pinecone credentials. It also defines RAG model, index, namespace, API, CORS, and application settings.

No OpenAI or Pinecone service is provisioned by the workflow. No Kafka, PostgreSQL, Airflow, Prometheus, Grafana, Kubernetes, or AWS service container or authenticated environment is configured. Placeholder credentials are suitable only for tests that avoid live external calls through fakes, dependency overrides, or other isolation.

If a collected test attempts a live Pinecone or OpenAI request, these placeholder settings do not create a valid external test environment. Kafka-dependent imports likewise depend on the installed Python environment; no broker is started.

### 4.5 Installation commands

```bash
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
```

Both requirements-file checks are conditional. A missing manifest does not fail at the installation step, although later imports or tests may fail. The workflow does not install the project as a package, use a constraints file, require dependency hashes, or report an installed-dependency inventory.

### 4.6 Test commands

Unit tests:

```bash
pytest tests/unit -v --maxfail=1
```

Integration tests:

```bash
pytest tests/integration -v --maxfail=1
```

Each command first checks that its target directory exists and fails if the directory is absent. The integration step runs only if all preceding steps, including the unit-test step, succeed.

These are two directory-specific invocations, not one full-repository `pytest` command. `--maxfail=1` stops each invocation after its first failure, limiting the diagnostic evidence available from one run.

### 4.7 What a successful run actually proves

A successful run would prove that, for the checked-out revision and that GitHub-hosted Python 3.11 environment:

- dependency installation completed from the available manifests;
- pytest collected and passed the tests under `tests/unit`;
- pytest subsequently collected and passed the tests under `tests/integration`; and
- the tests completed using the workflow's configured test environment.

It would not by itself prove that the tests exercise real external integrations. Fake-backed or dependency-overridden tests prove the simulated or in-process behaviour encoded by those tests.

### 4.8 Known risks and misleading configuration

- Full pytest currently has known Kafka- and Pinecone-related problems. The workflow must not be described as proof that the unrestricted full suite passes.
- Kafka import or dependency incompatibility can block relevant test collection before broker behaviour is evaluated.
- Pinecone-dependent paths can fail when a test reaches the external service because the workflow provides placeholders, not live authenticated integration.
- No coverage command, coverage threshold, test report upload, or retained failure artifact is configured.
- `--maxfail=1` reduces visibility into concurrent failures.
- The workflow name suggests broad integration coverage, but no external service is provisioned.
- Python 3.11 is the only configured interpreter; compatibility with other development or container Python versions is not established here.
- The `master`, `develop`, and `dev` filters may be deliberate compatibility aliases, but their continuing need is not evidenced by this file.
- A successful run does not prove frontend behaviour, Docker runtime behaviour, Terraform validity, database initialization, or deployed infrastructure.

## 5. Docker CI workflow

### 5.1 Purpose

`docker-ci.yml` checks out the repository and asks the runner-provided Docker engine to build one image from the repository root.

### 5.2 Branch and path triggers

| Event | Branch filters | Path filters |
|---|---|---|
| `push` | `main`, `master`, `develop`, `dev`, `feature/**` | None |
| `pull_request` | Target branches `main`, `master`, `develop`, `dev` | None |
| `workflow_dispatch` | Manual | None |

Any qualifying repository change can trigger a Docker build. No path filter narrows the workflow to Docker, dependency, application, or build-context changes.

### 5.3 Runtime and installation

- Runner: `ubuntu-latest`.
- Checkout: `actions/checkout@v4`.
- Docker version: not declared; the workflow uses the Docker engine supplied by the current runner image.
- Buildx or a separately pinned Docker setup action: not configured.
- Registry authentication: not configured.

The workflow itself performs no host-level dependency installation. Dependency installation that occurs inside the image build belongs to the Docker build definition and was outside this audit's inspection scope.

### 5.4 Build command

```bash
docker build -t edip-api-ci:latest .
```

The tag is local to the CI runner and uses the mutable label `latest`. The workflow does not push the image or retain an image digest as release evidence.

### 5.5 What a successful run actually proves

A successful run proves that Docker accepted the repository build context and completed the configured image-build instructions on the selected runner at that time.

It does not prove:

- that the container starts;
- that application imports succeed inside the image;
- that health or readiness endpoints respond;
- that required model, forecast, RAG, or data artifacts are available;
- that environment configuration is complete;
- that the image can communicate with external services;
- that the image is secure, minimal, non-root, or vulnerability-free;
- that Docker Compose starts the wider system; or
- that the image is deployable to AWS or Kubernetes.

Docker build success must therefore not be represented as runtime correctness.

### 5.6 Known risks and misleading configuration

- No container startup or smoke test follows the build.
- No health-check request is executed.
- No image inspection, software-bill-of-materials generation, dependency scan, secret scan, or vulnerability scan is configured.
- No multi-platform build is attempted.
- The Docker engine and runner operating system are not fixed to immutable versions.
- The image is tagged `latest`, but no immutable digest or commit-derived tag is recorded.
- No cache strategy or retained build artifact supports reproducibility analysis.
- The workflow's broad triggers may consume CI capacity for changes that cannot affect the image.

## 6. Terraform CI workflow

### 6.1 Purpose and job structure

`terraform-ci.yml` contains two independent jobs:

- `terraform-local-k8s` validates the Terraform configuration under `infra/terraform/local-k8s`.
- `terraform-aws` validates the Terraform configuration under `infra/terraform/aws`.

Both jobs run on `ubuntu-latest` and use `hashicorp/setup-terraform@v3`.

### 6.2 Branch and path triggers

| Event | Branch filters | Path filters |
|---|---|---|
| `push` | `main`, `master`, `develop`, `dev`, `feature/**` | `infra/terraform/**`, `.github/workflows/terraform-ci.yml` |
| `pull_request` | Target branches `main`, `master`, `develop`, `dev` | `infra/terraform/**`, `.github/workflows/terraform-ci.yml` |
| `workflow_dispatch` | Manual | Not restricted by path |

Automatic runs occur only when a matching Terraform path or the workflow file changes. Changes outside those paths do not automatically revalidate Terraform even if they alter the application or container that the infrastructure is intended to run.

### 6.3 Runtime and installation

- Runner: `ubuntu-latest`.
- Checkout: `actions/checkout@v4`.
- Terraform setup action: `hashicorp/setup-terraform@v3`.
- Terraform CLI version: not declared in the workflow; the effective version depends on the setup action's default resolution at run time.

Neither job configures AWS credentials, a Kubernetes cluster, `kubectl`, Helm, or a deployment target.

### 6.4 Local Kubernetes validation commands

Working directory:

```text
infra/terraform/local-k8s
```

Commands:

```bash
terraform init -backend=false
terraform fmt -check -recursive
terraform validate
```

Initialization with `-backend=false` supports local static validation without configuring a remote state backend. It can still require network access to obtain providers or modules not already available on the runner.

### 6.5 AWS validation commands

Working directory:

```text
infra/terraform/aws
```

Commands:

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

Before initialization, the job creates a `terraform.tfvars` file containing dummy validation inputs. Those inputs include a mutable image tag, permissive CORS-style values, placeholder API credentials, application settings, and RAG configuration. They enable variable resolution for static validation; they are not evidence of a secure or approved deployment configuration.

### 6.6 What successful runs actually prove

For each selected working directory, success proves that:

- the configuration satisfied `terraform fmt -check -recursive`;
- `terraform init -backend=false` completed where configured; and
- `terraform validate` accepted the initialized configuration and supplied validation inputs.

This is useful syntax, internal-consistency, provider-schema, and formatting evidence. It does not prove:

- successful `terraform plan`;
- successful AWS or Kubernetes authentication;
- correct account, region, quota, network, IAM, or cluster behaviour;
- absence of destructive or costly changes;
- successful deployment;
- application or container runtime readiness;
- secure secrets handling;
- live health checks, observability, rollback, backup, or disaster recovery; or
- production readiness.

Terraform validation must not be represented as deployment readiness.

### 6.7 Known risks and misleading configuration

- The Terraform CLI version is not pinned.
- Neither job creates or reviews a saved plan.
- No policy, security, cost, drift, or destructive-change check is configured.
- No remote-state or locking behaviour is exercised.
- No real AWS or Kubernetes target is contacted.
- The AWS dummy variables include values that would be insecure or non-deterministic if copied into a real deployment, including a mutable image tag, wildcard-style origin configuration, and placeholder secrets.
- The local-k8s job validates configuration but does not create a cluster or deploy resources.
- The AWS job validates configuration but does not prove that IAM, networking, load balancing, ECS, logging, or health checks operate in an AWS account.
- Formatting occurs before `terraform init` in the AWS job and after initialization in the local-k8s job. The inconsistency is not itself a failure, but a common ordering would make workflow intent clearer.

## 7. Cross-workflow external-service assumptions

| Capability | Provisioned or exercised by these workflows? | Evidence boundary |
|---|---|---|
| OpenAI | No | Placeholder test configuration only |
| Pinecone | No | Placeholder test configuration only; Pinecone-related test problems are known |
| Kafka | No | No broker or service container; Kafka-related collection/dependency problems are known |
| PostgreSQL | No | No database service or schema initialization |
| Airflow | No | No scheduler, webserver, DAG parse, or task execution |
| Prometheus/Grafana | No | No observability stack startup or query |
| AWS | No | Terraform static validation only; no credentials, plan, apply, or smoke test |
| Kubernetes | No | Terraform static validation only; no cluster or resource deployment |
| Docker runtime | No | Image construction only; container is not started |
| Frontend | No | No Node installation, lint, test, or build step |

The absence of provisioned services is not necessarily incorrect for fast CI. It must, however, remain explicit so simulated tests and configuration checks are not interpreted as live integration evidence.

## 8. What the current CI baseline proves

| Evidence class | Proven by configuration if the workflow succeeds | Not proven |
|---|---|---|
| Python | Unit and integration directories pass under one Python 3.11 CI environment | Unrestricted full pytest health, live service integration, multi-version compatibility, coverage quality |
| Docker | Root image build completes | Startup, imports, health, readiness, artifacts, security, deployment |
| Terraform local-k8s | Formatting and initialized validation pass | Cluster creation, Kubernetes deployment, runtime operation |
| Terraform AWS | Formatting and initialized validation pass with dummy inputs | Plan safety, AWS deployability, application readiness, production operation |

No combination of the three workflows proves the complete EDIP system operates end to end.

## 9. Recommended minimal future corrections

These are recommendations only; no workflow change is made by this audit.

### Integration CI

1. Resolve or explicitly isolate the known Kafka collection/dependency problem.
2. Separate fake-backed in-process tests from opt-in live Pinecone/OpenAI tests.
3. Ensure ordinary CI never attempts live external calls with placeholder credentials.
4. Add a full-suite collection gate once dependency issues are resolved.
5. Retain complete failure evidence rather than stopping at the first failure, or use `--maxfail=1` only for a deliberately fast gate.
6. Add a measured coverage report and an evidence-based threshold only after the suite is stable.
7. Add frontend validation in a separate workflow if frontend CI is within the current plan.

### Docker CI

1. Start the built container with controlled test configuration.
2. Run application import and health/readiness smoke checks inside or against the container.
3. Verify the required artifact-delivery contract rather than relying on developer-local files.
4. Tag evidence with the commit SHA or record the image digest.
5. Add proportionate image and dependency scanning.

### Terraform CI

1. Pin the Terraform CLI to an explicitly reviewed version.
2. Keep formatting and validation, but label them as static checks.
3. Add non-deploying `terraform plan` review only when safe credentials, backend strategy, and environment ownership are defined.
4. Replace deployment-like dummy values with clearly named validation fixtures that cannot be mistaken for approved production configuration.
5. Add policy, security, and cost checks only when their rules and ownership are agreed.
6. Keep Kubernetes optional and do not make live cluster validation a production gate unless the architecture decision requires Kubernetes.

### Trigger and supply-chain hygiene

1. Confirm the current branch policy and remove obsolete branch filters only with repository-owner approval.
2. Consider narrow path filters where they reduce cost without hiding relevant changes.
3. Review action major versions and move to immutable commit pinning if required by the repository's supply-chain policy.

## 10. Residual limitations

Even after the minimal corrections above, CI would remain only one evidence layer. Production readiness would still require:

- controlled environment configuration and secret handling;
- real-service integration tests in an appropriate protected environment;
- data and artifact provenance;
- security, privacy, access-control, and abuse testing;
- performance and resilience evaluation;
- deployment and rollback evidence;
- monitoring and incident-response validation; and
- stakeholder acceptance against explicit operational criteria.

Live OpenAI, Pinecone, Kafka, PostgreSQL, Airflow, AWS, and Kubernetes operation must be evidenced separately. A green CI badge must not substitute for those results.

## 11. Rollback

This audit creates one documentation file and changes no workflow. Before commit, rollback consists of removing:

```text
docs/audits/EDIP_CI_BASELINE_AUDIT.md
```

If the audit is later committed, revert the focused documentation commit. Future workflow corrections should be delivered as small independent commits so each can be reverted without removing unrelated validation.

## 12. Professional reflection

CI evidence is easy to overstate because each green job compresses several distinct questions into one status. Systems thinking requires separating construction, static validation, simulated testing, live integration, deployment, and operational readiness.

The three workflows have legitimate but bounded purposes. Python test success can establish behaviour under the collected test doubles and environment; Docker build success establishes image construction; Terraform validation establishes configuration consistency. None establishes that the full sociotechnical system is safe, secure, useful, or recoverable in operation.

An evidence-based improvement strategy should preserve those fast checks while naming their limits, then add stronger evidence only where a clear risk and owner justify it. This keeps CI maintainable, avoids expensive or unsafe live dependencies in ordinary pull requests, and produces a more honest professional record of what was tested, what was simulated, and what remains unknown.
