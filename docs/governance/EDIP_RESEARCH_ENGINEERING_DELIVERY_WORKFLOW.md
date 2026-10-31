# EDIP Research and Engineering Delivery Workflow

| Field | Value |
|---|---|
| Status | Active governance |
| Decision control | Explicit human approval; acceptance is recorded separately |
| Engineering lifecycle | Enterprise AI/ML Engineering Framework v2.1.0 |
| Execution management | Approved GitHub Issues |
| Architecture authority | [EDIP V2 Flagship Architecture Plan](../architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md) |
| Coding-agent and AI-assistance policy | [Agent instructions](../../AGENTS.md) |

## 1. Purpose and scope

This document defines how EDIP research questions, architecture decisions, engineering changes, releases, and outcomes move from evidence to a reviewed result. It operationalizes the architecture plan without converting target design into implementation evidence.

The workflow applies to APIs, data, feature engineering, forecasting, machine learning, RAG, LangGraph workflows, Human-in-the-Loop controls, MCP integrations, infrastructure, deployment, security, governance, and documentation that affects technical or research claims.

Current verified repository and execution evidence has priority for current implementation truth. The architecture plan and approved ADRs define target decisions. Dated historical records describe only the revision and boundary they inspected.

The current MSc study has one primary hypothesis-driven experiment: the Favorita forecasting comparison defined by the approved research design. RAG, LangGraph orchestration, Human-in-the-Loop controls, and enterprise integration remain applied EDIP system capabilities unless a separately approved research protocol introduces another research question. This positioning does not change the evidence hierarchy or governance workflow below.

## 2. Two-layer operating model

EDIP separates lifecycle governance from execution management.

### Engineering lifecycle and quality layer

The Enterprise AI/ML Engineering Framework v2.1.0 supplies the lifecycle:

```text
Problem -> Data -> Baseline -> Advanced AI -> Evaluation -> Delivery -> Production -> Maintenance
```

Each stage defines questions, controls, evidence, and promotion gates. The lifecycle does not prescribe delivery schedules or issue numbering.

### GitHub issue execution layer

Delivery is governed through approved GitHub Issues:

```text
Finding/problem
-> proposed issue content
-> review and explicit approval
-> issue creation
-> local branch command
-> separately authorized implementation
-> proportional validation
-> review
-> authorized pull request to dev
-> acceptance decision
-> separately approved release checkpoint and deployment
-> measured outcome and reflection
```

Issue creation is not automatic. An applicable existing issue may be reused.
Implementation, Git mutations, experiment execution, and deployment have distinct
approval boundaries under [AGENTS.md](../../AGENTS.md).

Legacy Jira/SCRUM labels are historical provenance, not active execution authority.
This clarification is transitional and may be removed after active planning
references have been reconciled and verified. Historical evidence remains intact.

A work item may cover part of one framework stage or evidence spanning several
stages. A framework quality gate may require several issues.

## 3. Evidence hierarchy

| Record | Purpose | Authority |
|---|---|---|
| Architecture plan | Approved target, boundaries, principles, and non-goals | Design authority unless formally superseded |
| Governance record | Repeatable evidence, decision, accountability, and release controls | Must conform to architecture and legal/research duties |
| GitHub issue | Approved scope, acceptance criteria, exclusions, and dependencies | Execution record; separate authorization is required for implementation and consequential operations |
| ADR | Architecture-significant decision, alternatives, consequences, and rollback | Required for material or difficult-to-reverse decisions |
| Dataset/corpus governance record | Source, licence, access, provenance, lineage, retention, and restrictions | Data-use authority for the named asset |
| Research design | Hypothesis, methodology, baseline, split, metrics, limitations, and approval | Evaluation authority for the named study |
| Implementation record | Files and behavior changed, migration, and rollback | Proves what changed, not that it is correct or deployed |
| Validation record | Commands, environment, inputs, outputs, failures, and evidence limits | Proves only the executed boundary |
| Release/deployment record | Approved immutable release and environment outcome | Proves the named deployment, not sustained operation |
| Outcome/reflection record | Observed result, negative evidence, learning, and next decision | Closes the evidence chain |

Records should link instead of duplicating large bodies. Historical records may be summarized or removed after unique evidence is consolidated, while Git history preserves their original form.

## 4. Approval and accountability

Project direction, architecture, risk acceptance, research integrity, implementation
acceptance, and publication remain subject to human review. AI output is advisory
and must not be treated as approval or as validation of unobserved facts.

Coding and independent-review responsibilities, reviewer-driven change approval,
and AI-assistance disclosure are defined in [AGENTS.md](../../AGENTS.md). Material
claims, citations, code, test interpretation, and decisions require verification.
Credentials, restricted data, personal data, and unpublished confidential material
require explicit authority and appropriate handling.

GitHub and CI/CD preserve bounded revision, review, check, release, and deployment
evidence. Issue closure, merges, and green checks alone do not establish acceptance
or production readiness.

## 5. Mandatory evidence chain

Every material work item preserves:

```text
finding -> risk -> decision -> implementation -> validation -> outcome -> reflection
```

- **Finding:** What was observed, at which revision, from which evidence?
- **Risk:** Why does it matter, to whom, with what likelihood and impact?
- **Decision:** What was approved, rejected, or deferred, and what evidence records that decision?
- **Implementation:** What changed and what remained protected?
- **Validation:** Which checks ran, with which environment and evidence boundary?
- **Outcome:** Did the change produce the intended technical or research result?
- **Reflection:** What was learned and what changes next?

A missing link is stated explicitly; it is never inferred or fabricated.

## 6. Work-item workflow

1. Inspect current evidence and applicable architecture, governance, research, and data contracts.
2. Define the problem, decision value, scope, non-goals, protected assets, and risk.
3. Compare alternatives, including a simple or non-AI baseline where appropriate.
4. Present proposed GitHub issue content and obtain explicit approval before creation; reuse an applicable existing issue where appropriate.
5. Record acceptance criteria, dependencies, evidence, rollback, and exclusions in the issue.
6. Provide the local branch command from `dev`; branch creation requires separate authorization when automated.
7. Obtain implementation approval and make the smallest coherent change without unrelated cleanup.
8. Validate proportionately. Training-related commands, real-model execution, protected evaluation, and consequential operations require separate explicit permission under AGENTS.md.
9. Review evidence and obtain explicit approval before reviewer-driven edits.
10. Prepare a pull request to `dev`; creation and Git mutations require explicit authorization.
11. Record changed files, failures, limitations, rollback, and completion evidence.
12. Assess release readiness separately; a completed feature does not automatically justify promotion to `main`.
13. Obtain explicit authorization for release and deployment operations after workflow triggers and impact have been inspected.
14. Measure outcomes and record negative or inconclusive results.

Emergency exceptions require explicit approval, documented risk, minimum safe
validation, bounded authority, and a follow-up completion/reflection record.

## 7. Branch, pull-request, and release controls

- `main` represents reviewed release checkpoints.
- `dev` integrates reviewed development work.
- Short-lived feature/chore branches start from `dev` and return through pull-request review.
- A feature or `dev` push is not a production release.
- CI must complete before the relevant merge or release decision.
- Explicit approval is required before the reviewed release is merged to `main`.
- The approved `main`/release merge is the deployment boundary.
- Deployment triggers must be inspected before release operations; automated deployment is authorized only within the explicitly approved workflow and environment.
- Commits and pull requests remain focused and do not conceal unrelated generated changes.
- Force-push, history rewrite, production deployment, data publication, or irreversible external action requires explicit authority.

## 8. CI/CD and infrastructure governance

### Continuous integration

CI validates the bounded revision before release. Depending on change type, it may include compilation, unit and integration tests, schema or contract checks, notebook validation, linting, type checking, container construction, dependency review, and static Infrastructure as Code checks.

CI evidence must identify mocks, skipped tests, unavailable services, and static-only checks. It does not prove cloud deployment or live operation.

### Continuous Deployment (CD)

For the target release design, an explicitly approved GitHub Actions Continuous Deployment (CD) workflow is intended to perform the following after an approved release merge to `main`. This list is a design contract, not evidence that these capabilities are implemented or deployed:

1. builds an immutable application container image;
2. publishes immutable backend and frontend images to Amazon ECR by digest;
3. updates the approved Amazon ECS Fargate services behind the Application Load Balancer;
4. verifies health, readiness, version, and telemetry after deployment; and
5. preserves evidence and the ability to roll back to a known revision.

In the target release design, feature or `dev` pushes do not deploy production. Explicit approval is required before the `main`/release merge. Actual workflow triggers and environment evidence must be verified before deployment behavior is claimed or a release operation is authorized.

### Infrastructure lifecycle

Terraform owns the reviewed AWS infrastructure lifecycle. Infrastructure changes require focused IaC review, static validation, plan review, security/cost analysis, and environment-appropriate apply authority. Production infrastructure must not be provisioned manually.

Application release and infrastructure lifecycle are distinct. Terraform is used when infrastructure changes; it is not a mandatory step for every application image deployment. GitHub Actions CD uses AWS OpenID Connect (OIDC) and narrowly scoped roles to publish ECR images and update ECS Fargate services; it must not use long-lived AWS credentials. Detailed AWS Terraform, identity, networking, artifact delivery, and workflow configuration require a dedicated ADR and implementation task.

## 9. Evidence required by change type

| Change type | Minimum evidence |
|---|---|
| API/schema | Versioned contract, identity/authorization impact, stable errors, compatibility, migration/rollback, unit/integration/security tests |
| Data/features | Source/version/provenance, grain/schema, lineage, leakage/temporal controls, preservation rules, quality assertions, manifest |
| Forecasting/ML | Research question, governed data, chronological split, baseline, predeclared metrics, reproducibility, uncertainty/error analysis, artifact lineage |
| RAG/corpus | Approved source registry/licences, corpus and chunk manifests, ACL model, compatibility, retrieval baseline, grounding/citation/abstention/injection tests |
| LangGraph/workflow | State and transition contract, tool allowlist, identity, deterministic safety, HITL, idempotency, failure/resume/reconciliation tests |
| MCP/integration | Versioned tools, read/write separation, authorization, approval, idempotency, simulation, reconciliation, threat model |
| Infrastructure | ADR where required, environment accountability, Terraform/backend contract, immutable versions, secrets, plan/security/cost/rollback evidence |
| Application release | Reviewed revision, CI, immutable image digest, deployment approval, health/readiness, telemetry, rollback |
| Research outcome | Protocol, comparator, results, uncertainty, threats, ethics/licensing, negative evidence, critical discussion |

## 10. Data, feature, and research integrity

Favorita work follows the [dataset source and governance record](FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md), [research hypothesis and experiment design](../research/favorita/FAVORITA_RESEARCH_HYPOTHESIS_AND_EXPERIMENT_DESIGN.md), [temporal validation design](../research/favorita/FAVORITA_TEMPORAL_VALIDATION_DESIGN.md), and [temporal validation contract](../research/favorita/FAVORITA_TEMPORAL_VALIDATION_CONTRACT.md).

Research records must preserve:

- question or hypothesis and decision relevance;
- dataset identity, permitted use, provenance, grain, date coverage, and checksums;
- leakage-safe temporal splits and holdout protection;
- baseline and model comparison under identical conditions;
- predeclared metrics, aggregation, segments, thresholds, and negative-target treatment;
- code revision, environment, seeds where meaningful, and artifact identifiers;
- uncertainty, error, subgroup and sensitivity analysis;
- limitations, failed hypotheses, and negative results.

Raw data is not redistributed. Sparse absent rows are not silently interpreted as zero demand. Synthetic fixtures may test logic but cannot establish real-world model quality.

## 11. RAG, agentic, and safety evidence

RAG sources require human-approved authority, licensing, sensitivity, freshness, access, and supersession. Corpus and retrieval evidence is versioned. Model-free, fake-backed, credentialed live-service, and production evidence are reported separately.

LangGraph work records state transitions, interrupts, resume rules, actor identity, tool permissions, decision provenance, and deterministic post-model controls. Tests cover insufficient evidence, abstention, unauthorized tools, stale approval, changed inputs, replay, partial failure, timeout, and durable resume.

An LLM must not authorize irreversible action. Human approval binds a known actor to a specific action and versioned inputs and expires or revalidates when material conditions change.

## 12. Definition of Ready

A work item is ready only when:

- the finding, risk, decision value, and applicable GitHub issue are evidence-based;
- architecture, governance, data/research contracts, and relevant ADRs are linked;
- scope, non-goals, protected assets, dependencies, and approval boundaries are clear;
- alternatives and a non-AI baseline are considered where appropriate;
- data access, licensing, privacy, ethics, and external authority are resolved or gated;
- acceptance criteria, evidence types, rollback, and review are written; and
- implementation has been explicitly approved.

## 13. Definition of Done

A work item is done only when:

- implementation matches approved scope and unexplained changes are absent;
- required checks ran and exact pass/fail/skip evidence is recorded;
- contracts, manifests, documentation, and executed behavior agree;
- relevant security, privacy, licensing, accessibility, and integrity controls were reviewed;
- rollback is feasible and versioned assets are recoverable;
- the pull request is reviewed and CI evidence is interpreted;
- residual risks and unverified live behavior are explicit;
- release/deployment status is stated accurately; and
- outcome measurement and reflection are recorded at the appropriate time.

“Code written,” “ticket closed,” “PR merged,” or “tests passed” alone is insufficient.

## 14. ADR discipline

Create or update an ADR when a decision changes a system boundary, public/data contract, security/tenant model, persistence, external provider, model/corpus strategy, deterministic safety rule, deployment topology, irreversible-action control, or other difficult-to-reverse choice.

An ADR records status, date, approval record, linked work item, context, constraints, alternatives including status quo, approved decision, non-goals, consequences, security/privacy/licensing implications, validation, observability, migration, rollback, supersession, explicit approval evidence, and review date.

The detailed AWS topology, Terraform implementation, identity, networking, managed services, S3 model delivery, and GitHub Actions CD workflow require a dedicated ADR before implementation.

## 15. Academic and professional evidence

MSc evidence requires a defensible research question, context/literature, justified method, governed data, comparative baselines, reproducibility, evaluation, ethics/licensing, limitations, negative results, and critical discussion. Repository activity alone is not academic contribution.

Professional evidence connects decisions and outcomes to responsibility, complexity, stakeholders, risk, quality, security, ethics, learning, and influence. AI output, commit volume, or document volume does not establish competence or an SFIA level.

A future PhD pathway requires a precise gap, reproducible method, credible comparators, repeated evaluation, threats to validity, ethical approval where required, and supervisor/peer challenge. Architecture ambition or LLM use does not establish novelty.

## 16. Supersession and review

Review this workflow when architecture, issue workflow, branch/release policy, CI/CD, regulated data, safety controls, research obligations, or repeated delivery failures change.

Changes require human approval and a focused pull request. A new governance record must identify what it supersedes. Historical evidence must not be silently rewritten to claim that it originally described a later state.
