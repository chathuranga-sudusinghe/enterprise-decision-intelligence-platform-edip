# EDIP AWS Canonical Cloud Migration Audit

| Field | Value |
|---|---|
| Status | Active cloud-direction audit and migration record |
| Audit date | 2026-09-08 |
| Branch | `chore/aws-canonical-cloud-migration` |
| Scope | All tracked repository files |
| Production-readiness claim | None |

## Decision

Amazon Web Services (AWS) is the sole canonical production cloud target for
EDIP. No production AWS infrastructure or Continuous Deployment (CD) workflow
is implemented in this branch.

The approved production release path is:

```text
reviewed merge to main
-> GitHub Actions CD using AWS OpenID Connect (OIDC)
-> immutable backend and frontend images in Amazon ECR
-> Amazon ECS Fargate services updated by image digest
-> Application Load Balancer health and readiness checks
-> Amazon CloudWatch deployment and runtime evidence
```

Terraform owns production infrastructure lifecycle. Production deployment is
not performed manually. Application CD releases images and updates services;
it does not provision infrastructure during every release.

## Canonical AWS service boundaries

| Concern | Canonical direction |
|---|---|
| Container registry | Separate backend and frontend repositories in Amazon ECR; release by immutable digest |
| Runtime | Separate Amazon ECS Fargate services for FastAPI and Next.js |
| Ingress | Application Load Balancer with TLS, routing, and health checks |
| Model and artifact delivery | Versioned Amazon S3 objects with manifests, checksums, retention, and promotion state |
| Runtime identity | Least-privilege IAM execution roles and task roles |
| CI/CD identity | GitHub Actions OIDC with narrowly scoped assumable roles; no long-lived AWS access keys |
| Secrets | AWS Secrets Manager references; no credentials in images, Git, workflow variables, or task definitions |
| Observability | Amazon CloudWatch logs, metrics, dashboards, alarms, and deployment diagnostics |
| Durable relational state | PostgreSQL, using Amazon RDS for PostgreSQL when production persistence is required |
| Infrastructure lifecycle | Reviewed Terraform plans and controlled applies |

A pre-trained Favorita bundle is produced outside the serving environment,
published to a versioned S3 key, and selected through immutable deployment
configuration. The backend task uses its IAM task role to retrieve the approved
bundle into bounded task-local storage, verifies its checksum and metadata, and
reports ready only after `FavoritaBundlePredictor` loads it. ECS tasks must not
run or import training, feature materialization, Optuna, evaluation, or SCRUM-19
holdout workflows.

## Repository-wide reference classification

| Classification | Finding and action |
|---|---|
| Active architecture | Azure direction in `README.md` and `docs/architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md` was replaced with the canonical AWS services and delivery path. |
| Active delivery governance | `docs/governance/EDIP_RESEARCH_ENGINEERING_DELIVERY_WORKFLOW.md` now defines GitHub Actions OIDC, ECR publication, ECS Fargate service updates, and Terraform-owned infrastructure. |
| Active research handoff | The deployment-only remaining-work statements in `docs/research/favorita/FAVORITA_TEMPORAL_VALIDATION_CONTRACT.md` now point to S3 publication and AWS serving. Research design, results, metrics, and holdout evidence were unchanged. |
| Local validation | `docs/validation/FAVORITA_DOCKER_LOCAL_SERVING.md` keeps Compose and bind mounts local and describes their boundary with future S3-to-task-local delivery. Dated validation results remain evidence of what was tested. |
| Historical evidence | `docs/audits/EDIP_CLOUD_DEPLOYMENT_READINESS_AUDIT.md` remains an Azure-era 2026-09-04 snapshot. A superseded notice was added; its original findings and terminology were preserved. |
| Stale AWS references | None existed in tracked architecture or infrastructure before this migration. Package-lock integrity text was excluded as non-semantic data. |
| Other cloud direction | The generated `ui/README.md` Vercel deployment recommendation was replaced with the canonical ECR-to-ECS Fargate direction. Remaining Vercel URLs identify upstream Next.js/font resources and do not define deployment. |
| Obsolete or superseded infrastructure | No old AWS implementation is tracked. The existing `infra/terraform/local-k8s/` stack is local learning/validation infrastructure and is not a production-cloud template. |

Outside this migration record, every remaining Azure reference is confined to:

- `docs/audits/EDIP_CLOUD_DEPLOYMENT_READINESS_AUDIT.md`, where every occurrence
  belongs to the preserved Azure-era audit snapshot; and
- two dated scan observations in
  `docs/validation/FAVORITA_DOCKER_LOCAL_SERVING.md`, which accurately record
  that the 2026-09-07 validation looked for Azure resource identifiers.

This audit also uses the term only to explain the migration and classify
historical references. None of these remaining occurrences defines active
architecture.

## Existing Terraform assets

The only tracked Terraform root is `infra/terraform/local-k8s/`. It uses the
Terraform Kubernetes provider and a local kubeconfig to create:

- one namespace;
- FastAPI Deployment and Service resources;
- Prometheus configuration, Deployment, and Service resources;
- Grafana configuration, Deployment, and Service resources; and
- local outputs and variables.

`terraform-ci.yml` runs backend-free initialization, formatting checks, and
validation for this local stack. There is no AWS provider configuration, remote
state backend, ECR, ECS, S3, IAM, Secrets Manager, CloudWatch, ALB, networking,
or RDS Terraform. The local stack includes mutable image tags and development
credential defaults and must not be promoted or copied into production AWS
infrastructure.

The separate raw manifests under `infra/k8s/` are also local Kubernetes
learning/validation assets. They include a personal Docker Hub `latest` image,
mutable upstream image tags, local monitoring, development credentials, and
outdated API probes. They are retained as noncanonical local evidence and must
not be used as ECS, ECR, or production deployment inputs.

## Existing GitHub Actions workflows

| Workflow | Current behavior | Deployment status |
|---|---|---|
| `.github/workflows/integration-ci.yml` | Installs development dependencies, runs Ruff, then unit and integration tests | CI only |
| `.github/workflows/docker-ci.yml` | Builds the backend Docker image with a local CI tag | CI only; no ECR authentication or publication |
| `.github/workflows/terraform-ci.yml` | Formats and validates `infra/terraform/local-k8s/` | CI only; no AWS plan or apply |

No `cd.yml` or equivalent deployment workflow exists. No workflow requests an
OIDC token, assumes an AWS role, publishes to ECR, updates ECS, uploads a model
to S3, or performs post-deployment checks.

## Portability and deployment assumptions

- The root `Dockerfile` builds only the FastAPI backend. It uses Python 3.12,
  copies serving code without training/evaluation modules, listens on port
  8000, and expects a model bundle on the container filesystem.
- `.dockerignore` excludes datasets and artifacts, which is compatible with
  external S3 delivery, but no S3 retrieval/bootstrap component exists.
- `docker-compose.yml` is explicitly local-only. Its host bind mount, loopback
  ports, Prometheus/Grafana services, local PostgreSQL, and development
  credentials are not AWS production configuration.
- The Next.js frontend has no production Dockerfile. It reads
  `NEXT_PUBLIC_API_BASE_URL`; its build-time/runtime configuration and ALB route
  contract are not yet defined. Its previous generated Vercel deployment
  recommendation has been removed.
- FastAPI reads environment variables and requires explicit production CORS
  origins, but it has no S3 URI, expected bundle version/checksum, AWS SDK,
  Secrets Manager integration, database URL, or CloudWatch/OpenTelemetry export
  configuration.
- The backend readiness endpoint proves only that a local bundle loaded. It does
  not yet report S3 retrieval state, required persistence, or other production
  dependencies.
- The existing OCI backend image is portable to ECS Fargate in principle, but
  image hardening, non-root execution, inference-only dependencies, resource
  sizing, concurrency, and load evidence remain unresolved.

## What remains unimplemented

Before any AWS deployment claim, EDIP still needs:

1. an approved AWS deployment ADR covering environments, networking, DNS/TLS,
   ALB routing, IAM boundaries, S3 promotion, ECR layout, ECS topology,
   Terraform state, observability, retention, rollback, and the RDS decision;
2. bootstrap governance for Terraform remote state and GitHub OIDC without
   long-lived credentials;
3. AWS Terraform modules and environment composition;
4. a provider-bound S3 artifact adapter behind a small provider-neutral
   interface, with immutable identity, checksum verification, bounded local
   cache, failure behavior, and readiness gating;
5. production backend and frontend container definitions and measured Fargate
   CPU/memory/concurrency requirements;
6. Secrets Manager and IAM least-privilege policies for execution, application,
   deployment, and infrastructure roles;
7. CloudWatch logs, metrics, alarms, dashboards, correlation, and retention;
8. an optional RDS PostgreSQL design only when an implemented persistence
   consumer and migration/backup contract justify it;
9. AWS-focused Terraform checks, security/policy scanning, and reviewed plans;
   and
10. a separately reviewed GitHub Actions CD workflow that releases both images,
    updates ECS by digest, validates health/readiness/version, and records
    rollback evidence.

## Exact next implementation sequence

1. Approve the AWS deployment ADR and environment/security boundaries.
2. Implement the minimal Terraform/OIDC bootstrap under a dedicated reviewed
   task.
3. Implement AWS foundation Terraform: networking, ECR, S3, IAM, Secrets
   Manager, CloudWatch, ALB, ECS clusters/services, and optional RDS only if
   required.
4. Implement and test S3 model-bundle publication, retrieval, integrity,
   task-local caching, and readiness behavior without exposing training code to
   serving.
5. Harden the backend image and add a production frontend image; define ALB
   routing and environment contracts.
6. Extend CI for both images and AWS Terraform static/security checks.
7. Implement GitHub Actions CD with AWS OIDC, immutable ECR digests, ECS rolling
   updates, post-deployment validation, and rollback evidence.
8. Validate in a non-production AWS environment, resolve operational findings,
   then promote through the reviewed production release boundary.

This branch intentionally implements none of those infrastructure or CD steps.
It establishes one unambiguous AWS direction so later tasks do not encode
competing cloud assumptions.
