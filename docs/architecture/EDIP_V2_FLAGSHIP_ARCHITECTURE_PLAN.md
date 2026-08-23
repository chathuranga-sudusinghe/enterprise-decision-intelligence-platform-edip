# EDIP Version 2 Flagship Architecture Plan

| Field | Value |
|---|---|
| Status | Authoritative target architecture; implementation evidence remains separate |
| Project | Enterprise Decision Intelligence Platform (EDIP) |
| Architecture style | Capability-oriented modular monolith |
| Canonical cloud target | Microsoft Azure |
| Engineering framework | Enterprise AI/ML Engineering Framework v2.1.0 |
| Project-management model | Jira Sprints and SCRUM work items |
| Production-readiness claim | None |

## 1. Purpose and authority

This document defines the approved target architecture for EDIP: a trustworthy enterprise decision-intelligence platform for inventory and demand-planning decisions. It records system boundaries, technology direction, engineering principles, delivery gates, research positioning, and unresolved decisions.

It is a design authority, not proof that a component has been implemented, deployed, or operated. Current truth comes from verified repository code, tests, data manifests, reviewed implementation records, and deployment evidence. Target components shown here require separately approved implementation work.

Supporting authorities are:

- [Research and Engineering Delivery Workflow](../governance/EDIP_RESEARCH_ENGINEERING_DELIVERY_WORKFLOW.md);
- [Favorita Dataset Source and Governance](../governance/FAVORITA_DATASET_SOURCE_AND_GOVERNANCE.md);
- [Favorita Temporal Validation Design](../research/favorita/FAVORITA_TEMPORAL_VALIDATION_DESIGN.md); and
- [Favorita Temporal Validation Contract](../research/favorita/FAVORITA_TEMPORAL_VALIDATION_CONTRACT.md).

## 2. Vision and decision scope

EDIP combines governed internal knowledge, approved external evidence, demand forecasting, inventory-risk analytics, deterministic policy controls, bounded LangGraph orchestration, Human-in-the-Loop approval, and controlled enterprise actions.

An authorized decision-maker should be able to determine:

- what is happening and which data supports it;
- what is forecast to happen and with what uncertainty;
- which inventory or service risk follows;
- what action is recommended and which deterministic rules apply;
- whether the evidence is sufficient or the system must abstain;
- who must approve an action; and
- what was executed, against which versioned inputs, with what outcome.

EDIP optimizes for decision quality, safety, traceability, and recoverability rather than maximum autonomy. Generated text is not authority, and an LLM must not authorize an irreversible action.

## 3. Framework and project-management alignment

The Enterprise AI/ML Engineering Framework v2.1.0 supplies the engineering lifecycle and quality-gate layer:

```text
Problem -> Data -> Baseline -> Advanced AI -> Evaluation -> Delivery -> Production -> Maintenance
```

The lifecycle is not a project schedule. Jira Sprints and SCRUM work items provide the active execution-management layer.

```text
Jira Sprint
-> approved SCRUM work item
-> feature branch from dev
-> bounded implementation and local validation
-> pull request to dev
-> CI and human review
-> reviewed release checkpoint
-> main
-> automated Continuous Deployment (CD)
-> Azure revision
```

A work item may traverse several framework stages, and a framework gate may span several Sprints. Old numbered delivery phases are historical vocabulary and are not the current execution model.

## 4. Architecture principles

1. **Decision before technology.** Every capability must serve a defined decision, user, outcome, or risk.
2. **Evidence before assertion.** Recommendations link to admissible evidence and versioned analytical artifacts.
3. **Baseline before advanced AI.** Advanced approaches must be compared fairly with credible simpler alternatives.
4. **Capability ownership.** Online behavior is grouped into bounded capabilities inside one modular monolith.
5. **Offline/online separation.** Ingestion, training, evaluation, and bulk scoring remain under `pipelines/`; online serving remains under `app/`.
6. **Deterministic safety.** Critical calculations, authorization, policy evaluation, approval requirements, idempotency, and irreversible-action checks remain deterministic.
7. **Least autonomous authority.** A workflow stage receives only the context and tools required for its responsibility.
8. **Abstention is valid.** Missing, conflicting, stale, unauthorized, or insufficient evidence must not be converted into confidence.
9. **Human accountability.** Named people approve consequential decisions and remain accountable for accepted risk.
10. **Immutable provenance.** Data, features, models, prompts, policies, evidence, and releases are versioned and checksummed.
11. **Durable state for durable decisions.** Workflow, approval, execution, and audit state survive process restarts.
12. **Observability is not audit.** Operational telemetry, model traces, and authoritative business records have distinct owners.
13. **One canonical cloud direction.** Microsoft Azure is the deployment target; detailed topology requires a dedicated ADR.
14. **Small reversible changes.** Work is delivered through bounded branches, reviewed pull requests, validation, and explicit rollback.
15. **Claims match evidence.** Static validation, local tests, CI, deployment, and live operation are reported separately.

## 5. Capability-oriented modular monolith

EDIP retains one FastAPI backend, one Next.js frontend, offline pipelines, and supporting repository areas. This boundary minimizes distributed-system complexity while allowing enforceable capability ownership.

```text
ui/                         Next.js user experience
app/
|-- core/                   configuration, logging, shared technical controls
|-- rag/                    governed online retrieval and generation
|-- forecasting/            online forecast access and artifact compatibility
|-- workflows/              LangGraph state, routing, and bounded stages
|-- approvals/              durable HITL decisions
|-- audit/                  durable business and execution evidence
`-- integrations/          approved MCP and enterprise adapters
pipelines/
|-- ingestion/              offline data and corpus ingestion
|-- features/               reproducible feature construction
|-- training/               baseline and model training
|-- evaluation/             temporal validation and comparative evaluation
`-- publication/            approved artifact packaging and promotion
```

These target packages should be created only with real implementation. EDIP does not require an initial microservices decomposition or a Python `src/` migration. A future service split requires evidence of independent scaling, security, reliability, or team-ownership need and an approved ADR.

## 6. User experience and API

### Next.js

The target frontend provides authenticated, accessible views for decision cases, evidence, forecasts, uncertainty, risks, approval queues, execution status, and audit history. It must expose loading, stale-data, insufficient-evidence, rejected, failed, and recovery states without presenting generated prose as verified fact.

### FastAPI

FastAPI owns typed request/response contracts, authentication and tenant context, authorization, capability orchestration, stable error codes, idempotency, correlation identifiers, health/readiness boundaries, and OpenAPI evidence.

External providers remain adapters behind typed interfaces. Business behavior must be testable without live network access, while credentialed integration evidence is validated separately.

## 7. Analytical and AI capabilities

### 7.1 Forecasting and inventory risk

The forecasting capability uses the governed Favorita foundation for current research. Its approved near-term model direction is LightGBM with selected alternatives and credible naive/statistical baselines evaluated under identical temporal splits and metrics.

The current temporal contract uses direct horizon-aware global forecasting for `unit_sales`, exact horizons 1 through 16, and no recursive prediction feedback. The approved eight-fold design and protected final holdout are defined in the linked research documents.

Forecast artifacts must identify their dataset, feature schema, model, baseline, training window, evaluation protocol, generation time, compatibility status, uncertainty representation, and checksum. Online services resolve approved immutable artifacts rather than developer-local “latest” files.

Inventory-risk calculations remain deterministic and distinguish forecast uncertainty, stock position, expected receipts, lead-time assumptions, service targets, shortage exposure, and recommendation confidence.

### 7.2 Internal RAG

Pinecone is the target semantic/vector retrieval service for approved internal knowledge. It is not the owner of source documents, access decisions, approvals, workflow state, or the business audit record.

A governed RAG corpus requires:

- an approved source registry with authority, ownership, licence, sensitivity, and freshness;
- stable document, chunk, corpus, and ingestion identifiers;
- tenant and document access control from ingestion through retrieval;
- embedding/index/namespace compatibility manifests;
- deletion, supersession, and re-index controls;
- retrieval baselines and predeclared metrics;
- grounding, citation, abstention, stale-source, conflict, and injection evaluation.

Claude is the target language-model direction for evaluated generation and reasoning use cases. Provider and model versions remain explicit, replaceable configuration and require separate quality, safety, cost, and data-handling evaluation.

### 7.3 Approved external evidence and benchmarking

External evidence enters EDIP only through a reviewed source registry. Each source records authority, licence or terms, permitted use, freshness, schema, geography, units, sensitivity, retrieval method, version, and supersession.

Benchmarking compares compatible internal and external measures. It must record normalization, comparability, uncertainty, missing coverage, source version, and limitations. It must not manufacture equivalence or causal conclusions.

### 7.4 LangGraph workflow

LangGraph orchestrates bounded, typed stages. It does not replace authorization, deterministic safety, approval persistence, or audit ownership.

A target workflow can include:

1. request and identity validation;
2. internal evidence retrieval;
3. approved external evidence retrieval;
4. forecasting and inventory-risk analysis;
5. evidence-sufficiency and uncertainty assessment;
6. deterministic safety and authorization;
7. recommendation assembly;
8. Human-in-the-Loop review;
9. controlled execution; and
10. outcome and audit recording.

Every transition has defined input, output, failure, retry, timeout, and terminal behavior. Durable resume must revalidate identity, approval, policy, and material inputs.

### 7.5 HITL and deterministic safety

Human approval binds a known actor to a specific versioned decision and action. Material input changes, expiry, policy changes, or authorization changes invalidate or require revalidation of approval.

Deterministic controls own:

- identity, tenant, and role checks;
- evidence sufficiency and staleness rules;
- materiality and approval thresholds;
- hard business constraints;
- action allowlists;
- idempotency and duplicate suppression;
- separation of duties where required; and
- post-action reconciliation.

### 7.6 Controlled MCP

MCP is a governed integration interface, not an authorization system. Tools are narrowly scoped, versioned, allowlisted, and separated into read and write permissions. Credentials remain with the approved server or secret broker. High-impact actions require deterministic checks, explicit approval, idempotency, bounded retries, and reconciliation.

## 8. Data, state, and artifact ownership

| Technology | Target responsibility | Must not own |
|---|---|---|
| PostgreSQL | Structured durable application, workflow, HITL, execution, policy-reference, and audit state | Large binary artifacts or vector retrieval |
| Pinecone | Semantic/vector retrieval for approved governed corpora | Source authority, approvals, business state, or audit truth |
| Azure Blob Storage | Large datasets, model packages, manifests, evaluation reports, evidence payloads, and suitable release artifacts | Transactional approval or authorization state |
| Azure Key Vault | Production secrets, keys, certificates, and secret references | Ordinary business data or model artifacts |
| Application Insights / Azure Monitor | Logs, metrics, traces, alerts, and operational diagnostics | Authoritative business decisions or approval records |

Generated data and artifacts remain outside Git. Manifests record immutable IDs, schema/version, producer revision, inputs and checksums, parameters, environment, coverage, validation, approval state, storage URI, retention, and successor/rollback relationships.

## 9. Azure target and delivery architecture

Microsoft Azure is the canonical cloud target. The intended high-level deployment path is:

```text
local development and training
-> local tests, API and Docker validation
-> GitHub pull request and review
-> GitHub Actions CI
-> reviewed merge/release checkpoint to main
-> automated Continuous Deployment (CD)
-> immutable image in Azure Container Registry
-> new Azure Container Apps revision
-> health, readiness, telemetry and rollback evidence
```

Target service responsibilities are:

- **Azure Container Registry:** immutable container images identified by digest;
- **Azure Container Apps:** revision-based FastAPI application deployment;
- **Azure Key Vault:** production secret references;
- **Azure Blob Storage:** large governed artifacts;
- **PostgreSQL:** structured durable application and workflow state;
- **Pinecone:** semantic retrieval;
- **Application Insights / Azure Monitor:** operational observability.

GitHub Actions is the intended CI/CD automation mechanism. CI validates code, tests, contracts, and builds before release. Feature or development pushes do not deploy production. Human approval occurs before the reviewed `main`/release merge; that merge is the deployment boundary. Continuous Deployment (CD) then automatically publishes the immutable image, deploys a new Azure revision, performs post-deployment validation, and preserves rollback evidence.

Terraform is the preferred Infrastructure as Code direction for Azure resource lifecycle. Infrastructure change and application deployment are distinct workflows: Terraform is reviewed when infrastructure changes, not required for every application revision.

Detailed Azure topology, subscriptions, regions, networking, identity, managed PostgreSQL choice, private connectivity, Terraform modules/backends, workflow YAML, scaling, backup, disaster recovery, and cost controls are deferred to a dedicated Azure deployment ADR and implementation task. This document does not claim that Azure infrastructure or CD is already implemented.

## 10. Security, trust, and observability

Production gates include authenticated identity, tenant isolation, least privilege, secure secret references, encryption, controlled egress, dependency and image review, threat modeling, audit retention, backup/recovery, incident procedures, and tested rollback.

Evaluation must distinguish:

- unit and deterministic contract tests;
- in-process or fake-backed integration tests;
- credentialed external-service tests;
- container construction and startup evidence;
- cloud deployment evidence; and
- sustained operational evidence.

Application Insights and Azure Monitor are the target operational telemetry layer. LangGraph or model-provider traces may support development and evaluation but do not replace the durable business audit store.

## 11. Evaluation and research positioning

EDIP is an engineering and research platform, not a production-readiness claim. Its research themes include temporal forecasting, governed retrieval, evidence sufficiency, uncertainty, abstention, bounded agentic workflows, deterministic safety, and Human-in-the-Loop decision quality.

Academic evidence requires a defensible question, governed data, justified methodology, declared baselines, reproducible experiments, quantitative and qualitative evaluation, negative results, uncertainty, threats to validity, ethics/licensing review, and critical discussion.

Claims such as “reliable,” “trustworthy,” “adaptive,” or “multi-agent” require defined measures and comparative evidence. Repository size, model complexity, or use of an LLM does not establish novelty or value.

## 12. Current state and target-state boundary

Confirmed repository evidence includes the Favorita governed source record, leakage-safe feature contract, exact 16-day forecast horizon, approved eight-fold temporal design, executable temporal-boundary validation, and bounded smoke evidence.

The following remain target work unless separately evidenced:

- trained and evaluated forecasting baselines and models;
- actual multi-fold model fitting and scoring;
- metric selection and negative-target policy;
- final holdout scoring;
- governed production RAG and approved corpus;
- durable identity, HITL, workflow, and audit persistence;
- controlled enterprise/MCP integrations;
- Azure infrastructure, CI/CD deployment, and live operations.

## 13. Historical transition

EDIP began as a broad engineering prototype. Legacy synthetic retail, event-streaming, and orchestration demonstrations, including Kafka and Airflow assets, were removed through bounded cleanup. The project then established the real-data Favorita foundation and moved to the current evidence-based architecture, governance, temporal-validation, and research direction.

This short transition explains provenance without making old implementation details the active roadmap or current project-management model.

## 14. Open decisions requiring human review

Dedicated decisions are still required for:

- Azure topology, identity, networking, regions, managed PostgreSQL, Terraform state, scaling, recovery, and cost;
- exact Claude model/provider configuration and evaluation thresholds;
- Pinecone index, namespace, corpus, access, retention, and deletion contracts;
- production identity provider, tenant mapping, and approval authority matrix;
- forecasting metrics, negative-`unit_sales` treatment, model alternatives, and promotion criteria;
- first controlled MCP integration and write action;
- operational service objectives, incident ownership, and retention; and
- research protocols involving users, organizations, or sensitive data.

Until approved and implemented, these remain target decisions rather than current operational capability.
