# EDIP Research and Engineering Delivery Workflow

- Version: 1.0
- Status: Active governance
- Effective date: 14 August 2026
- Owner and accountable decision-maker: Human project owner/researcher
- Architecture authority: [EDIP V2 Flagship Architecture Plan](../architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md)
- AI-use policy: [AI Usage](../../AI_USAGE.md)

## 1. Purpose, authority and scope

This document defines how EDIP research questions, architecture decisions and engineering changes move from evidence to a reviewed outcome. It operationalizes the authoritative architecture plan; it does not replace it, redefine its target architecture or certify implementation maturity.

The workflow applies to repository research, APIs, data, feature engineering, forecasting, machine learning, RAG, agent workflows, deterministic safety, infrastructure, deployment and governance records. It governs both implementation and documentation-only work when either could affect an architectural claim, research conclusion, professional-evidence claim or operational boundary.

Where records disagree, use the evidence precedence in architecture-plan section 1.1: current verified repository and test evidence takes priority for current implementation truth; dated audits remain evidence of the state they inspected; the architecture plan and accepted ADRs define the approved target and decisions. A plan is not implementation evidence, and a historical implementation record is not automatically current truth.

Review this workflow when any of the following occurs:

- the architecture authority, branching model or phase gates change;
- a new regulated, safety-critical, external-data or irreversible-action capability is proposed;
- research, academic, licensing, privacy or professional-evidence requirements change;
- repeated delivery failures show that an evidence or approval gate is ineffective;
- an audit finds a contradiction between this workflow and repository practice; or
- at each major phase checkpoint before promotion from `dev` to `main`.

Changes to this workflow require human approval, a focused pull request and an explicit supersession note. They must not be inferred from an AI-generated suggestion.

## 2. Record hierarchy and evidence roles

| Record type | Purpose | Authority and expected relationship |
|---|---|---|
| Architecture plan | Defines the approved target, principles, boundaries, gates and non-goals | Highest design authority unless formally superseded; see architecture-plan sections 1, 5–7 and 31 |
| Governance record | Defines repeatable decision, evidence and accountability controls | Must conform to the architecture plan and applicable legal, academic and professional obligations |
| ADR | Records one architecture-significant decision, alternatives, consequences and rollback | Required by architecture-plan section 34 triggers; cannot silently override the architecture plan |
| Audit | Records verified conditions, risks and limitations at a named revision and date | Historical evidence remains unchanged; later records link to it and state what resolved or superseded it |
| Phase record | Defines or reviews a bounded phase, gate and acceptance decision | Links work items, ADRs, validation and unresolved risks to architecture-plan sections 27–31 |
| Experiment record | Defines a question or hypothesis, protocol, baseline, dataset and evaluation | Results may inform a decision but do not become runtime truth without approval and implementation evidence |
| Implementation record | Identifies scoped files, branch, commits, migration and rollback | Proves what changed, not that the change is correct, useful, safe or deployed |
| Validation record | Preserves commands, environment, inputs, outputs, failures and evidence limits | Must distinguish static, mocked, local, credentialed, deployment and live-operational evidence |
| Reflection/outcome record | Compares observed outcomes with intended outcomes and records learning | Must include negative or inconclusive results and follow-up decisions |

Records should link rather than duplicate large sections of another authority. A later resolution record may classify an earlier finding as resolved, partially resolved or superseded, but it must not rewrite the original audit.

## 3. Roles and decision authority

| Role | Permitted contribution | Decision/accountability boundary |
|---|---|---|
| Human project owner/researcher | Frames research, owns requirements, evaluates evidence, approves decisions and accepts risk | Sole accountable owner for repository direction, academic integrity, professional claims and release/phase decisions |
| ChatGPT discussion and decision-support assistant | Helps explore evidence, alternatives, risks, questions and draft plans | Cannot approve work, own authorship/accountability, validate unobserved facts or substitute for supervisor/stakeholder judgement |
| Codex bounded coding and validation assistant | Inspects the authorized scope, implements approved changes and runs proportionate checks | Must obey file/action boundaries; cannot broaden authority, approve its own output or convert generated text into verified evidence |
| GitHub and CI | Preserve branches, reviews, commits, workflow logs and check results | Evidence surfaces only; a merge or green check is not by itself proof of research validity, security, deployment or production readiness |
| Stakeholder, supervisor or reviewer | Challenges requirements, design, ethics, evaluation and outcomes within their remit | Approval authority must be explicit; review participation does not transfer the project owner's accountability |

AI tools are not authors, approvers, accountable decision-makers or substitutes for academic or professional judgement. The human owner must verify every material AI-assisted claim, citation, code change, test interpretation and decision before acceptance. AI assistance must be disclosed consistently with [AI_USAGE.md](../../AI_USAGE.md), including its bounded role and the human verification performed. Credentials, personal data, restricted data and unpublished confidential material must not be exposed to an AI tool without explicit authorization and an appropriate data-handling basis.

## 4. Mandatory lifecycle

Every material work item must preserve this chain:

`finding → risk → decision → implementation → validation → outcome → reflection`

The chain is mandatory because each link answers a different question:

- **Finding:** What was observed, at which revision, using what evidence?
- **Risk:** Why does the finding matter, to whom, and with what likelihood/impact?
- **Decision:** What option did the human owner approve, and which alternatives were rejected or deferred?
- **Implementation:** What changed, where, by whom, and with what rollback boundary?
- **Validation:** Which checks ran, with which inputs/environment, and what passed, failed, was skipped or remained untested?
- **Outcome:** Did the change produce the intended technical, research or stakeholder result?
- **Reflection:** What was learned, what assumptions failed, and what should change next?

Missing links must be marked explicitly; they must not be filled with inferred or fabricated evidence.

## 5. Discussion-to-Codex delivery workflow

1. **Evidence review.** Inspect current code, data contracts, tests, prior decisions, audits and applicable architecture sections. Record the revision and evidence limits.
2. **Problem definition.** State the observed problem, affected users/systems, scope, non-goals and risk.
3. **Alternatives and non-AI baseline.** Compare reasonable alternatives, including a deterministic or non-AI baseline where AI is proposed. Record cost, safety, reversibility and evidence needs.
4. **Human approval.** The project owner approves the direction and any consequential external action. AI discussion is advisory only.
5. **Work item and acceptance criteria.** Define files/capabilities in scope, exclusions, required evidence, rollback and phase relationship before coding.
6. **Scoped Codex prompt.** Name the repository, branch, exact authorized changes, protected assets, validation and prohibited actions.
7. **Implementation.** Make the smallest coherent change. Preserve unrelated work and do not combine cleanup, redesign and new capability work without an approved reason.
8. **Validation.** Run proportionate checks; preserve exact commands/results; distinguish simulated/static evidence from live or deployment evidence.
9. **Completion record.** Reconcile implementation with acceptance criteria, failures, residual risks, changed files and rollback.
10. **PR and phase gate.** Obtain review, resolve comments, inspect CI evidence and apply the relevant architecture-plan section 31 gate before integration or promotion.
11. **Outcome measurement and reflection.** Measure the agreed outcome after sufficient observation, record negative/inconclusive results and decide whether to retain, revise, roll back or supersede.

## 6. Branch, commit and pull-request rules

The branching policy follows architecture-plan section 32:

- `main` holds reviewed stable checkpoints;
- `dev` holds integrated development;
- short-lived work branches start from `dev` and return to `dev` through review;
- a reviewed phase checkpoint moves from `dev` to `main`;
- commits are focused, explain intent and do not conceal unrelated generated changes;
- a PR links its work item, relevant finding/audit, ADR when required, acceptance criteria, validation and rollback;
- required checks and human review must be interpreted, not merely counted; failures, skips and mocked boundaries remain visible; and
- no force-push, history rewrite, external deployment or irreversible operation is implied by this workflow.

Emergency exceptions require a named human approver, documented risk, minimum safe validation and a follow-up completion/reflection record.

## 7. Evidence required by change type

| Change type | Minimum required records and evidence |
|---|---|
| API or schema | Versioned contract, OpenAPI impact, identity/authorization analysis, error and compatibility contract, migration/rollback, unit/integration/security tests |
| Data or feature engineering | Source/version/provenance, grain and schema contract, lineage, leakage and temporal controls, row/value preservation rules, quality assertions, reproducible manifest and rollback |
| Forecasting or ML experiment | Research question, dataset/version, chronological split, non-AI/naive baselines, predeclared metrics/thresholds, uncertainty/error analysis, reproducibility, artifact lineage, negative results |
| RAG or corpus | Approved source registry and licences, corpus/chunk manifests, ACL/tenant model, index/embedding compatibility, retrieval baseline, grounding/citation/abstention/staleness/injection tests |
| Agent, workflow or deterministic safety | State/transition contract, tool allow-list, authorization boundary, deterministic safety rules, HITL and revalidation behavior, failure/idempotency/reconciliation tests, durable audit evidence |
| Infrastructure or deployment | ADR where triggered, environment ownership, immutable versions, secret handling, state/backend, static validation, plan review, security/cost review, deployment/health/rollback evidence appropriate to the claim |

## 8. API and schema evidence

API changes must align with architecture-plan sections 10, 11, 19, 20 and 23. The change record must include:

- versioned request and response schemas, representative valid/invalid examples and the affected OpenAPI surface;
- authentication, tenant context, role/permission checks and fail-closed authorization behavior;
- stable error codes, safe error messages, correlation/audit identifiers and retry/idempotency semantics where relevant;
- backward/forward compatibility, deprecation window, consumer impact, migration and rollback;
- unit tests for validation/business rules, in-process integration tests for routing and dependency boundaries, and security tests for unauthorized, cross-tenant and malformed requests; and
- an explicit statement when live consumer, performance, external-service or deployment behavior was not exercised.

## 9. Data, feature and ML/research evidence

Data and model work must follow architecture-plan sections 16, 24, 26, 29–31 and the applicable dataset governance, including the [Favorita source and governance record](../phase-1/FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md).

Before evaluation, record:

- the hypothesis or research question and intended decision relevance;
- dataset identifier/version, access terms, provenance, checksums/manifests, grain and date coverage;
- leakage controls, chronological train/validation/test splits and any embargo or rolling-origin protocol;
- naive, rules-based or other non-AI baselines;
- metrics, aggregation rules, segments, thresholds and statistical comparison method;
- reproducible environment, seeds where meaningful, code/commit and artifact identifiers.

After evaluation, record uncertainty, calibration where relevant, error and subgroup analysis, sensitivity, limitations, failed hypotheses and negative results. Promotion requires evidence that the selected approach improves on declared baselines for the intended use; an experiment notebook or model artifact alone is not approval for serving or decision use.

## 10. RAG evidence

RAG work must use the controls in architecture-plan sections 14, 23, 24 and 26. At minimum preserve:

- a human-approved source registry with owner, authority, licence, sensitivity, freshness and supersession status;
- corpus, document, chunk and ingestion manifests with stable identifiers and hashes;
- tenant and document ACL enforcement from ingestion through retrieval and citation;
- embedding model, dimension, index and namespace compatibility plus deletion/re-index behavior;
- deterministic lexical/vector or other retrieval baselines and predeclared retrieval metrics;
- grounding, citation correctness, unsupported-answer abstention, conflicting-source, stale-source and insufficient-context tests; and
- prompt-injection, malicious-document, cross-tenant and data-exfiltration tests.

Model-free tests, fake-backed tests and credentialed live-service evaluations must be reported separately. No source may enter the corpus solely because an AI tool generated or recommended it.

## 11. Agent, workflow and deterministic-safety evidence

Workflow changes must align with architecture-plan sections 12, 13, 19 and 20. Record state transitions, interrupt/resume rules, actor identity, tool permissions, decision provenance and deterministic post-model controls. An LLM must not authorize irreversible action.

Tests must cover evidence insufficiency, abstention, unauthorized tools, stale approvals, changed inputs after approval, duplicate/replayed requests, partial failures, compensation/reconciliation, timeout and durable resume. Human approval must bind a known actor to a specific versioned action and expire or revalidate when material inputs change.

## 12. Infrastructure and deployment evidence

Infrastructure work must preserve the ECS Fargate canonical direction and Kubernetes optionality defined by the architecture plan. Record environment/account ownership, Terraform/backend state, immutable image and artifact identifiers, network/IAM boundaries, secret-manager references, observability, backup/recovery and rollback.

`terraform validate`, Docker build, configuration rendering and CI success are static or construction evidence. Deployment, health, load, resilience, security and recovery require separate environment evidence. A plan or successful build must never be labelled production readiness.

## 13. ADR triggers and contents

Create or update an ADR when a decision changes a system boundary, public/API/data contract, security or tenant model, persistence/state model, external provider, model/corpus strategy, deterministic safety rule, deployment topology, irreversible-action control, canonical framework, or a previously accepted architecture decision. Also use an ADR when a difficult-to-reverse choice has material cost, compliance or research consequences. See architecture-plan section 34.

Every ADR must state:

- status, date, owner and linked work item/finding;
- context, constraints, risks and decision drivers;
- considered alternatives, including status quo and non-AI baseline where applicable;
- approved decision and explicit scope/non-goals;
- consequences, security/privacy/ethics/licensing implications;
- validation, observability, migration and rollback;
- superseded/superseding ADR links; and
- named human approval and review date.

## 14. Definition of Ready

A work item is ready only when:

- the finding, risk, user/research value and scope are evidence-based;
- architecture sections, prior audits and relevant ADRs are linked;
- alternatives and a non-AI baseline have been considered where applicable;
- data access, licensing, privacy, ethics and external-service authority are resolved or explicitly gated;
- acceptance criteria, exclusions, evidence types, rollback and owner are written;
- dependencies and protected assets are identified;
- required stakeholder/supervisor review is scheduled; and
- the human owner has approved implementation.

## 15. Definition of Done

A work item is done only when:

- implementation matches the approved scope and no unexplained changes remain;
- required tests/checks ran and exact pass/fail/skip evidence is recorded;
- contracts, manifests, documentation and audit trails are consistent with executed behavior;
- security, privacy, licensing, accessibility and research-integrity controls relevant to the change were reviewed;
- rollback is feasible and versioned assets are recoverable;
- the PR is reviewed and applicable CI/phase-gate evidence is interpreted;
- residual risks, limitations and unverified external/live behavior are explicit;
- outcome measurement is defined or completed at the appropriate time; and
- the completion record links the entire mandatory lifecycle and includes reflection.

“Code written,” “PR merged” or “tests passed” alone does not satisfy this definition.

## 16. Academic and professional evidence

### MSc evidence

MSc evidence should demonstrate a defensible research question, literature/context review, justified methodology, governed dataset/provenance, comparative baselines, reproducible experiments, quantitative and qualitative evaluation, ethics/privacy/licensing review, limitations, negative results and a critical discussion connecting results to the question. Repository activity alone is not academic contribution.

### CITP evidence

Professional evidence should connect decisions and outcomes to responsibility, complexity, stakeholder communication, risk, governance, quality, security, ethics, learning and influence. Preserve the project owner's personal contribution, review feedback and measured outcome rather than presenting AI output or commit volume as competence. This workflow does not assign an SFIA level, award CITP or predict an assessment outcome; see architecture-plan section 29.

### PhD pathway evidence

A PhD pathway requires a precise research gap, systematic literature evidence, a reproducible method, credible comparators, repeated evaluation across relevant settings, statistical/qualitative rigor, threats to validity, ethical approval where required and peer/supervisor challenge. Architecture ambition, system breadth or use of an LLM does not establish novelty. Novelty and contribution may be claimed only after comparative evidence supports them; see architecture-plan section 30.

## 17. Research-integrity controls

- Preserve source and artifact provenance, dataset/corpus versions, code revision and environment details.
- Make experiments reproducible to the extent permitted by access, privacy and provider constraints; document unavoidable nondeterminism.
- Review ethics, bias, safety, privacy, consent, confidentiality, retention and stakeholder impact proportionately.
- Respect licences and restricted-access terms; do not redistribute Favorita or other restricted data without permission.
- Disclose AI assistance and record human verification; do not cite an AI answer as source evidence.
- Preserve negative, null and inconclusive results and changes to hypotheses or thresholds.
- Never fabricate test output, metrics, citations, approvals, users, deployments, external-service checks or stakeholder outcomes.
- Separate observation from inference and planned target from implemented/validated state.
- Correct errors through a linked amendment or supersession record; do not silently rewrite historical evidence.

## 18. Traceability matrix template

| Work item | Finding/evidence | Risk | ADR/decision | Branch | PR | Commit | Test/validation | Dataset/model/corpus artifact | Result | Outcome | Reflection |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `SCRUM-XX` | Audit/path/revision | Impact and owner | `ADR-XXX` or approved decision | `type/name` | `#NN` | Full SHA | Command/run/link and status | Manifest/version/hash or N/A | Pass/fail/partial | Measured effect or pending | Link and learning |

Each cell should contain a durable identifier or an explicit `N/A` with reason. “Passed” without the command, environment and revision is insufficient.

## 19. Rollback, supersession and historical evidence

Tracked changes should normally be rolled back with a focused Git revert, not destructive history rewriting. Data, model, vector-index, database and infrastructure rollback also requires explicit external-state, compatibility and reconciliation procedures; a source revert alone may be insufficient.

Documents use explicit status and links:

- a replacement record names what it supersedes and why;
- the superseded record remains unchanged and retains its original date/revision;
- current documents link back to the original finding and forward to resolution evidence;
- corrections are recorded as dated amendments when factual accuracy requires them; and
- no historical audit is edited merely to make old findings appear current or resolved.

The human project owner decides rollback, acceptance and supersession after reviewing evidence and stakeholder obligations.
