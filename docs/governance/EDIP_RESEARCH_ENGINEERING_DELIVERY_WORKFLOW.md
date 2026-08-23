# EDIP Research and Engineering Delivery Workflow

| Field | Value |
|---|---|
| Status | Active governance |
| Owner and accountable decision-maker | Human project owner/researcher |
| Engineering lifecycle | Enterprise AI/ML Engineering Framework v2.1.0 |
| Execution management | Jira Sprints and SCRUM work items |
| Architecture authority | [EDIP V2 Flagship Architecture Plan](../architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md) |
| AI-use policy | [AI Usage](../../AI_USAGE.md) |

## 1. Purpose and scope

This document defines how EDIP research questions, architecture decisions, engineering changes, releases, and outcomes move from evidence to a reviewed result. It operationalizes the architecture plan without converting target design into implementation evidence.

The workflow applies to APIs, data, feature engineering, forecasting, machine learning, RAG, LangGraph workflows, Human-in-the-Loop controls, MCP integrations, infrastructure, deployment, security, governance, and documentation that affects technical or research claims.

Current verified repository and execution evidence has priority for current implementation truth. The architecture plan and approved ADRs define target decisions. Dated historical records describe only the revision and boundary they inspected.

## 2. Two-layer operating model

EDIP separates lifecycle governance from execution management.

### Engineering lifecycle and quality layer

The Enterprise AI/ML Engineering Framework v2.1.0 supplies the lifecycle:

```text
Problem -> Data -> Baseline -> Advanced AI -> Evaluation -> Delivery -> Production -> Maintenance
```

Each stage defines questions, controls, evidence, and promotion gates. The lifecycle is not a Sprint plan and does not prescribe ticket numbering.

### Jira Sprint and SCRUM execution layer

Jira Sprints and SCRUM work items define planned delivery:

```text
Sprint goal
-> approved SCRUM work item
-> acceptance criteria and protected scope
-> feature branch from dev
-> implementation and local validation
-> pull request to dev
-> CI and human review
-> Sprint/release review
-> reviewed dev-to-main release checkpoint
-> approved CD
-> measured outcome and reflection
```

A work item may cover part of one framework stage or evidence spanning several stages. A framework quality gate may require several work items across several Sprints.

## 3. Evidence hierarchy

| Record | Purpose | Authority |
|---|---|---|
| Architecture plan | Approved target, boundaries, principles, and non-goals | Design authority unless formally superseded |
| Governance record | Repeatable evidence, decision, accountability, and release controls | Must conform to architecture and legal/research duties |
| Jira work item | Sprint scope, acceptance criteria, exclusions, owner, and dependencies | Execution authority for the bounded change |
| ADR | Architecture-significant decision, alternatives, consequences, and rollback | Required for material or difficult-to-reverse decisions |
| Dataset/corpus governance record | Source, licence, access, provenance, lineage, retention, and restrictions | Data-use authority for the named asset |
| Research design | Hypothesis, methodology, baseline, split, metrics, limitations, and approval | Evaluation authority for the named study |
| Implementation record | Files and behavior changed, migration, and rollback | Proves what changed, not that it is correct or deployed |
| Validation record | Commands, environment, inputs, outputs, failures, and evidence limits | Proves only the executed boundary |
| Release/deployment record | Approved immutable release and environment outcome | Proves the named deployment, not sustained operation |
| Outcome/reflection record | Observed result, negative evidence, learning, and next decision | Closes the evidence chain |

Records should link instead of duplicating large bodies. Historical records may be summarized or removed after unique evidence is consolidated, while Git history preserves their original form.

## 4. Roles and accountability

| Role | Contribution | Boundary |
|---|---|---|
| Human project owner/researcher | Frames questions, approves work and architecture, accepts risk, reviews evidence, owns academic integrity | Sole accountable decision-maker for project direction and claims |
| ChatGPT discussion and decision-support assistant | Explores evidence, alternatives, risks, questions, and draft plans | Advisory only; cannot approve work or validate unobserved facts |
| Codex bounded implementation assistant | Inspects authorized scope, implements approved changes, and runs proportionate checks | Cannot broaden scope, approve its own output, or manufacture evidence |
| Jira | Preserves Sprint goals, work-item scope, decisions, ownership, and status | Planning evidence; ticket closure alone is not technical completion |
| GitHub and CI/CD | Preserve branches, reviews, checks, releases, and deployment automation | Evidence surfaces; a merge or green check is not production readiness |
| Reviewer, supervisor, or stakeholder | Challenges requirements, design, ethics, method, and outcomes | Authority must be explicit; participation does not transfer owner accountability |

AI tools are not authors, approvers, or accountable decision-makers. The human owner verifies material AI-assisted claims, citations, code, test interpretation, and decisions. AI use must be disclosed consistently with `AI_USAGE.md`. Credentials, restricted data, personal data, and unpublished confidential material require explicit authority and appropriate handling.

## 5. Mandatory evidence chain

Every material work item preserves:

```text
finding -> risk -> decision -> implementation -> validation -> outcome -> reflection
```

- **Finding:** What was observed, at which revision, from which evidence?
- **Risk:** Why does it matter, to whom, with what likelihood and impact?
- **Decision:** What did the human owner approve, reject, or defer?
- **Implementation:** What changed and what remained protected?
- **Validation:** Which checks ran, with which environment and evidence boundary?
- **Outcome:** Did the change produce the intended technical or research result?
- **Reflection:** What was learned and what changes next?

A missing link is stated explicitly; it is never inferred or fabricated.

## 6. Work-item workflow

1. Inspect current evidence and applicable architecture, governance, research, and data contracts.
2. Define the problem, affected users, decision value, scope, non-goals, protected assets, and risk.
3. Compare alternatives, including a simple or non-AI baseline where appropriate.
4. Obtain human approval for the direction and consequential external actions.
5. Create or refine the Jira SCRUM work item with acceptance criteria, dependencies, evidence, rollback, and exclusions.
6. Branch from `dev` using a short-lived feature or chore branch.
7. Implement the smallest coherent change without unrelated cleanup.
8. Validate locally using evidence proportionate to risk.
9. Create a pull request to `dev`; interpret CI results and review feedback.
10. Record changed files, failures, limitations, rollback, and completion evidence.
11. Review the outcome in the Sprint and decide whether it contributes to a release checkpoint.
12. Obtain human approval for the reviewed release and merge the release checkpoint from `dev` to `main`.
13. Allow the approved GitHub Actions Continuous Deployment (CD) workflow to deploy the immutable application image automatically, perform post-deployment validation, and preserve rollback evidence.
14. Measure outcomes and record negative or inconclusive results.

Emergency exceptions require a named human approver, documented risk, minimum safe validation, bounded authority, and a follow-up completion/reflection record.

## 7. Branch, pull-request, and release controls

- `main` represents reviewed release checkpoints.
- `dev` integrates reviewed development work.
- Short-lived feature/chore branches start from `dev` and return through pull-request review.
- A feature or `dev` push is not a production release.
- CI must complete before the relevant merge or release decision.
- Human approval must occur before the reviewed release is merged to `main`.
- The approved `main`/release merge is the deployment boundary.
- Continuous Deployment (CD) is then triggered automatically by the approved GitHub Actions workflow.
- Commits and pull requests remain focused and do not conceal unrelated generated changes.
- Force-push, history rewrite, production deployment, data publication, or irreversible external action requires explicit authority.

## 8. CI/CD and infrastructure governance

### Continuous integration

CI validates the bounded revision before release. Depending on change type, it may include compilation, unit and integration tests, schema or contract checks, notebook validation, linting, type checking, container construction, dependency review, and static Infrastructure as Code checks.

CI evidence must identify mocks, skipped tests, unavailable services, and static-only checks. It does not prove cloud deployment or live operation.

### Continuous Deployment (CD)

After a human-reviewed release is merged to `main`, the approved GitHub Actions Continuous Deployment (CD) workflow automatically:

1. builds an immutable application container image;
2. publishes the image to Azure Container Registry;
3. deploys a new Azure Container Apps revision to the target Azure environment;
4. verifies health, readiness, version, and telemetry after deployment; and
5. preserves evidence and the ability to roll back to a known revision.

Feature or `dev` pushes do not deploy production. Human approval occurs before the `main`/release merge; that merge is the deployment boundary, after which CD performs the automated deployment and post-deployment validation.

### Infrastructure lifecycle

Terraform is the preferred direction for reviewed Azure infrastructure lifecycle. Infrastructure changes require focused IaC review, static validation, plan review, security/cost analysis, and environment-appropriate apply authority.

Application release and infrastructure lifecycle are distinct. Terraform is used when infrastructure changes; it is not a mandatory step for every application image deployment. Detailed Azure Terraform, identity, networking, and workflow configuration require a dedicated ADR and implementation task.

## 9. Evidence required by change type

| Change type | Minimum evidence |
|---|---|
| API/schema | Versioned contract, identity/authorization impact, stable errors, compatibility, migration/rollback, unit/integration/security tests |
| Data/features | Source/version/provenance, grain/schema, lineage, leakage/temporal controls, preservation rules, quality assertions, manifest |
| Forecasting/ML | Research question, governed data, chronological split, baseline, predeclared metrics, reproducibility, uncertainty/error analysis, artifact lineage |
| RAG/corpus | Approved source registry/licences, corpus and chunk manifests, ACL model, compatibility, retrieval baseline, grounding/citation/abstention/injection tests |
| LangGraph/workflow | State and transition contract, tool allowlist, identity, deterministic safety, HITL, idempotency, failure/resume/reconciliation tests |
| MCP/integration | Versioned tools, read/write separation, authorization, approval, idempotency, simulation, reconciliation, threat model |
| Infrastructure | ADR where required, environment owner, Terraform/backend contract, immutable versions, secrets, plan/security/cost/rollback evidence |
| Application release | Reviewed revision, CI, immutable image digest, deployment approval, health/readiness, telemetry, rollback |
| Research outcome | Protocol, comparator, results, uncertainty, threats, ethics/licensing, negative evidence, critical discussion |

## 10. Data, feature, and research integrity

Favorita work follows the [dataset source and governance record](FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md), [temporal validation design](../research/favorita/FAVORITA_TEMPORAL_VALIDATION_DESIGN.md), and [temporal validation contract](../research/favorita/FAVORITA_TEMPORAL_VALIDATION_CONTRACT.md).

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

- the finding, risk, user/research value, and Sprint relationship are evidence-based;
- architecture, governance, data/research contracts, and relevant ADRs are linked;
- scope, non-goals, protected assets, dependencies, and owner are clear;
- alternatives and a non-AI baseline are considered where appropriate;
- data access, licensing, privacy, ethics, and external authority are resolved or gated;
- acceptance criteria, evidence types, rollback, and review are written; and
- the human owner approves implementation.

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

An ADR records status, date, owner, linked work item, context, constraints, alternatives including status quo, approved decision, non-goals, consequences, security/privacy/licensing implications, validation, observability, migration, rollback, supersession, named human approval, and review date.

The detailed Azure topology, Terraform implementation, identity, networking, managed services, and CD workflow require a dedicated ADR before implementation.

## 15. Academic and professional evidence

MSc evidence requires a defensible research question, context/literature, justified method, governed data, comparative baselines, reproducibility, evaluation, ethics/licensing, limitations, negative results, and critical discussion. Repository activity alone is not academic contribution.

Professional evidence connects decisions and outcomes to responsibility, complexity, stakeholders, risk, quality, security, ethics, learning, and influence. AI output, commit volume, or document volume does not establish competence or an SFIA level.

A future PhD pathway requires a precise gap, reproducible method, credible comparators, repeated evaluation, threats to validity, ethical approval where required, and supervisor/peer challenge. Architecture ambition or LLM use does not establish novelty.

## 16. Supersession and review

Review this workflow when architecture, Jira practice, branch/release policy, CI/CD, regulated data, safety controls, research obligations, or repeated delivery failures change.

Changes require human approval and a focused pull request. A new governance record must identify what it supersedes. Historical evidence must not be silently rewritten to claim that it originally described a later state.
