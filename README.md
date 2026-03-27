# Enterprise Decision Intelligence Platform (EDIP)

## Business Problem Solved

Modern enterprises often struggle with fragmented data, slow decision cycles, policy-heavy operations, and weak connections between analytics and action. In many organizations, business teams can access dashboards and reports, but still cannot quickly answer high-value operational questions such as:

- Why was urgent replenishment recommended?
- Is this location at high stockout risk next week?
- Should the store reorder inventory or transfer stock from another location?
- Which business policy or operational context supports this recommendation?

The result is delayed action, inconsistent decisions, and limited trust in enterprise analytics systems.

**Enterprise Decision Intelligence Platform (EDIP)** solves this problem by combining enterprise retrieval, grounded AI reasoning, forecasting signals, and decision-oriented recommendations in one production-oriented system.

This project is built around a practical enterprise use case:

**Demand Forecasting + Inventory Decision Support for NorthStar Retail & Distribution**

---

## System Overview

EDIP is a production-oriented enterprise AI system designed to support real business decision workflows. It combines:

- **RAG + LLM reasoning** for grounded business explanations
- **Multi-agent orchestration** for structured decision workflow execution
- **Predictive and prescriptive analytics** for forecasting and replenishment support
- **Business-facing APIs and UI** for operational access
- **Testing, observability, and deployment readiness** for enterprise delivery

At a high level, EDIP transforms enterprise data and knowledge into explainable business recommendations.

### Current Decision Flow

**Planner → Retrieval → Reasoning → Analytics → Execution**

### Workflow Behavior

1. A business user submits a decision-oriented request.
2. The **Planner Agent** identifies the task type and required workflow path.
3. The **Retrieval Agent** gathers relevant enterprise documents, policy context, and business knowledge.
4. The **Reasoning Agent** interprets the request using grounded evidence.
5. The **Analytics Agent** adds forecast and recommendation logic when numerical support is needed.
6. The **Execution Agent** converts the result into a business-facing response.
7. The system returns structured outputs through API and frontend UI.

This design helps bridge the gap between raw enterprise data, knowledge retrieval, analytical reasoning, and operational action.

---

## Official Demo Scenarios

The project currently demonstrates three official enterprise decision scenarios.

### 1) Urgent Replenishment

**Question:**  
Why was urgent replenishment recommended for SKU-100245 at store 210?

**What this demonstrates:**  
This is the strongest end-to-end EDIP scenario. It shows how the system combines retrieval, grounded reasoning, forecast signals, and prescriptive recommendation logic to explain why immediate replenishment is required.

---

### 2) High Stockout Risk

**Question:**  
Is there a high stockout risk for SKU-100245 at store 210 next week?

**What this demonstrates:**  
This scenario shows risk-focused decision support using business context, forecast-related signals, and structured explanation output.

---

### 3) Reorder vs Transfer

**Question:**  
Should store 210 reorder SKU-100245 or transfer stock from another location?

**What this demonstrates:**  
This scenario shows action-choice decision intelligence, where the system recommends the better operational action based on business context and decision logic.

---

## Architecture

EDIP is designed as a layered enterprise AI system.

### 1. Unified Data Layer

Structured and semi-structured enterprise data is unified to support downstream decision intelligence.

**Used / planned components**
- synthetic enterprise data foundation
- normalized business entities and fact tables
- forecasting input datasets
- Kafka event payload exports
- enterprise document sources

### 2. RAG + LLM Layer

Enterprise policies, SOPs, reviews, and knowledge assets are embedded, indexed, retrieved, and used for grounded reasoning.

**Core components**
- OpenAI
- Pinecone
- RAG ingestion pipeline
- metadata schema and chunking pipeline
- enterprise markdown document corpus

### 3. AI Agent Orchestration Layer

The decision workflow is controlled through modular agents with clearly separated responsibilities.

**Agents**
- Planner Agent
- Retrieval Agent
- Reasoning Agent
- Analytics Agent
- Execution Agent

### 4. Predictive + Prescriptive Analytics Layer

EDIP goes beyond language generation by adding business analytics and decision logic.

**Core functions**
- demand forecasting
- stockout risk support
- replenishment recommendation logic
- structured business outputs for action support

### 5. API + Frontend Layer

This layer provides the business-facing interaction surface.

**Backend**
- FastAPI

**Frontend**
- React / Next.js / TypeScript

**Current frontend workflow display**
- Why
- Decision
- Forecast Summary
- Recommendation
- Workflow Overview
- Debug Payload

### 6. Workflow Orchestration Layer

EDIP also includes scheduled and orchestration-ready workflow capability.

**Orchestration**
- Airflow

### 7. Production Engineering Layer

The system is designed with deployment, monitoring, and infrastructure management in mind.

**Production-oriented components**
- Docker
- Kubernetes
- Terraform
- GitHub Actions
- Prometheus
- Grafana
- logging, monitoring, and governance direction

---

## Core Capabilities

EDIP is designed to support enterprise decision intelligence through the following capabilities:

- grounded business question answering
- retrieval-based enterprise reasoning
- demand forecasting support
- replenishment recommendation support
- explainable decision responses
- multi-agent workflow orchestration
- API-based enterprise integration
- business-facing frontend interaction
- monitoring and deployment readiness

---

## Repository Structure

```text
ENTERPRISE_DECISION_INTELLIGENCE_PLATFORM_EDIP/
├── app/
│   ├── agents/                  # Planner, Retrieval, Reasoning, Analytics, Execution agents
│   ├── api/                     # FastAPI routers
│   ├── core/                    # Config, logging, metrics, monitoring
│   ├── schemas/                 # API request/response schemas
│   ├── services/                # Workflow, forecast, RAG, event-processing services
│   └── main.py                  # FastAPI application entry point
├── artifacts/
│   ├── forecasts/               # Forecast and recommendation outputs
│   ├── models/                  # Trained model artifacts and schema files
│   └── reports/                 # Evaluation and validation reports
├── configs/                     # Kafka schema, RAG config, metadata schema
├── data/
│   ├── exports/                 # Kafka event exports
│   ├── processed/               # Processed datasets
│   ├── raw/                     # Raw datasets
│   └── synthetic/               # Generated synthetic enterprise data
├── database/
│   ├── ddl/                     # Database DDL files
│   ├── dml/                     # DML / loading logic
│   ├── migrations/              # Migration placeholders / files
│   └── seeds/                   # Seed placeholders / files
├── docs/
│   ├── policies/                # Policy documents
│   ├── rag_source/              # RAG knowledge sources
│   ├── reviews/                 # Business review documents
│   └── sops/                    # Standard operating procedures
├── infra/
│   ├── docker/                  # Docker-related infra assets
│   ├── k8s/                     # Kubernetes manifests
│   └── terraform/               # Terraform for AWS and local-k8s
├── monitoring/
│   ├── grafana/                 # Grafana dashboards and provisioning
│   └── prometheus/              # Prometheus configuration
├── pipelines/
│   ├── airflow_dags/            # Airflow orchestration DAGs
│   ├── etl/                     # Training dataset build pipeline
│   ├── features/                # Feature engineering
│   ├── inference/               # Forecast scoring and recommendations
│   └── training/                # Forecast model train/evaluate pipelines
├── scripts/                     # Data generation, RAG, Kafka, and demo scripts
├── tests/
│   ├── integration/             # API and workflow integration tests
│   └── unit/                    # Service and component unit tests
├── ui/                          # Next.js frontend
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── requirements_full.txt
└── README.md
