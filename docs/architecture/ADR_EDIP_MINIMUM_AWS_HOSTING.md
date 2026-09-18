# ADR: Minimum EDIP backend hosting

Status: accepted for implementation by the project owner in this task, 2026-09-15.
Scope: independent EDIP MSc research project; no shared/Vora resource changes.

## Decision

Deploy one FastAPI backend task on ECS Fargate behind an internet-facing ALB.
Use two public subnets in an EDIP VPC, an internet gateway, and task public IPs
for outbound ECR/S3 access. Do not add NAT, a database, frontend service, or
CloudFront. Task ingress on port 8000 is permitted only from the ALB security group.
Start with 0.5 vCPU and 1 GiB memory; validate the real model before increasing.

The temporary URL is HTTP on the generated ALB DNS name. Public listener rules
allow GET/HEAD only on /health, /ready, /docs and /openapi.json. The schema is
required for Swagger UI; it documents forecasting but does not permit executing
it through the ALB. All other paths and methods return 403, including forecast
and metrics. CORS is not an authorization control. Do not submit sensitive data.
HTTPS/custom domain and authentication remain prerequisites to exposing forecasts.
Add a certificate and HTTPS listener later without changing the ECS service.

## Model and image delivery

The existing S3 bucket stores model.txt and metadata.json under a reviewed
versioned prefix. Deployments pin both S3 version IDs and SHA-256 hashes.
A short startup module downloads exactly those versions with the task role,
verifies hashes, then starts the existing load-only API. No training occurs.
Publishing the selected real bundle requires an operator action; test bundles
must not be silently promoted.

Terraform owns networking, roles, log group, task definition and service.
The initial service has desired_count=0 until a real image is published.
CD registers a revision based on the Terraform task definition, substitutes
only a digest-pinned backend image, updates the service to one task and waits.
Terraform ignores service task_definition and desired_count to avoid rolling
back a CD release. Every CD run starts from the Terraform-owned template so
reviewed environment/role changes reach the next release.

Terraform also owns a compact CloudWatch operations dashboard and three alarms.
The dashboard covers ECS CPU/memory plus ALB traffic, latency, 5xx responses and
target health. Alarms cover sustained 80% ECS CPU, sustained 80% ECS memory and
unhealthy ALB targets; they intentionally have no notification actions during
the MSc research phase. These metrics and seven-day container logs support
operational diagnosis. They do not replace the authoritative EDIP decision audit
trail for model identity, research inputs, outputs and decision provenance.

Existing protected Terraform plan/apply remains first. A protected reusable
application workflow builds and pushes to the existing ECR, rolls out ECS,
verifies running tasks use the intended revision and checks public readiness,
docs/schema plus denied forecast/metrics. Final Release Gate requires both
Terraform and application success when hosting is enabled. Failure blocks gate.
ECS deployment circuit breaker rolls back failed deployments; CD must still
fail when ECS falls back to an older revision.

## Identity and infrastructure ownership

Reuse the existing exact-subject GitHub OIDC release role. Repository variables
provide role/environment/region; no personal owner or long-lived AWS credentials.
Execution role: ECR pull and one log group. Task role: two exact versioned S3
objects. Release role: this service, task family and two PassRole targets.
Bootstrap IAM must be reviewed/applied separately before the hosting root.
Infrastructure IAM uses explicit API actions and EDIP name/tag scoping.
Describe/list APIs and ECR authorization require resource "*"; ARN suffix
wildcards represent generated resource IDs, never blanket service permissions.
First-use ECS/ELB service-linked roles may require account administrator creation;
do not change an existing shared role.

## Cost, risks and alternatives

ALB and public IPv4 addresses have ongoing cost even with zero tasks.
One task is not highly available. Logs expire after seven days. Model memory,
startup time and rollback behavior require real deployment evidence.
No model publication, ECR push, Terraform apply or Git push is authorized by
implementation alone. The first external deployment remains a separate action.
The temporary HTTP endpoint is research/demo hosting, not secure forecasting.

Alternatives: two services add cost and the UI calls an unimplemented endpoint;
CloudFront is unnecessary for this explicitly accepted HTTP demo; private tasks
plus NAT increase idle cost. Keep them deferred until justified.

## Validation and rollback

Run Terraform format/validate and inspect saved plans, API/model delivery tests,
Docker build and real-bundle startup. Verify ALB rules statically and with CD.
Rollback by deploying a previous digest using the same workflow/template;
the ECS circuit breaker covers failed health rollouts. For immediate withdrawal,
set desired count to zero or remove public listener rules using reviewed changes.
Do not destroy foundation storage as a hosting rollback.
