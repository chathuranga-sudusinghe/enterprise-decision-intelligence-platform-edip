# Enterprise Decision Intelligence Platform (EDIP)

> Full AI Production System: RAG + Multi-Agent Workflow + XGBoost Forecasting + Replenishment Recommendation + FastAPI + React/Next.js UI + Kafka Event Simulation + Airflow Orchestration + Monitoring + CI/CD + Kubernetes + Terraform

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![XGBoost](https://img.shields.io/badge/XGBoost-Forecasting-orange)
![RAG](https://img.shields.io/badge/RAG-Grounded%20Reasoning-purple)
![Agents](https://img.shields.io/badge/Multi--Agent-Workflow-red)
![Kafka](https://img.shields.io/badge/Kafka-Event%20Simulation-black)
![Airflow](https://img.shields.io/badge/Airflow-Orchestration-darkred)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-orange)
![Grafana](https://img.shields.io/badge/Grafana-Dashboards-yellow)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-brightgreen)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Deployment-326ce5)
![Terraform](https://img.shields.io/badge/Terraform-IaC-623ce4)

## Business Problem Solved

Modern enterprises often struggle with fragmented data, slow decision cycles, policy-heavy operations, and weak connections between analytics and action. In many organizations, teams can access dashboards and reports, but still cannot quickly answer high-value operational questions such as:

- Why was urgent replenishment recommended?
- Is this location at high stockout risk next week?
- Should the store reorder inventory or transfer stock from another location?
- Which policy or operational context supports this recommendation?

The result is delayed action, inconsistent decisions, and limited trust in enterprise analytics systems.

**Enterprise Decision Intelligence Platform (EDIP)** solves this problem by combining enterprise retrieval, grounded AI reasoning, forecasting signals, and decision-oriented recommendations in one production-oriented system.

This project is built around a practical enterprise use case:

**Demand Forecasting + Inventory Decision Support for NorthStar Retail & Distribution**

---

## System Overview

EDIP is a production-oriented enterprise AI system designed to support real business decision workflows. It combines:

- **RAG + LLM reasoning** for grounded business explanations
- **Multi-agent orchestration** for structured workflow execution
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
5. The **Analytics Agent** adds forecasting and recommendation logic when numerical support is needed.
6. The **Execution Agent** converts the result into a business-facing response.
7. The system returns structured outputs through the API and frontend UI.

This design helps bridge the gap between raw enterprise data, enterprise knowledge, analytical reasoning, and operational action.

---

## Live Endpoints

### Local API Docs
- Swagger UI: `http://127.0.0.1:8000/docs`

### Core Endpoints
- Health: `GET /health`
- Metrics: `GET /metrics`

### RAG
- Health: `GET /rag/health`
- Query: `POST /rag/query`

### Forecast
- Health: `GET /forecast/health`
- Overview: `GET /forecast/overview`
- Recommendations: `GET /forecast/recommendations`
- Forecast Response: `GET /forecast`

### Agent Workflow
- Health: `GET /agents/workflow/health`
- Run Workflow: `POST /agents/workflow/run`

---

## Official Demo Scenarios

The project currently demonstrates three official enterprise decision scenarios.

### 1) Urgent Replenishment

**Question:**  
Why was urgent replenishment recommended for SKU-100245 at store 210?

**What this demonstrates:**  
This is the strongest end-to-end EDIP scenario. It shows how the system combines retrieval, grounded reasoning, forecasting signals, and prescriptive recommendation logic to explain why immediate replenishment is required.

### 2) High Stockout Risk

**Question:**  
Is there a high stockout risk for SKU-100245 at store 210 next week?

**What this demonstrates:**  
This scenario shows risk-focused decision support using business context, forecast-related signals, and structured explanation output.

### 3) Reorder vs Transfer

**Question:**  
Should store 210 reorder SKU-100245 or transfer stock from another location?

**What this demonstrates:**  
This scenario shows action-choice decision intelligence, where the system recommends the better operational action based on business context and decision logic.

---

## Example Official Demo Payload

```json
{
  "question": "Why was urgent replenishment recommended for SKU-100245 at store 210?",
  "user_role": "planner",
  "region_scope": "west",
  "product_id": 100245,
  "store_id": 210,
  "warehouse_id": 12,
  "region_id": 3,
  "horizon_days": 7,
  "include_recommendations": true,
  "require_approval": false,
  "metadata": {
    "source": "official_demo",
    "scenario": "urgent_replenishment",
    "channel": "frontend"
  }
}
```

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
```
## Tech Stack

### Core AI / Decision System
- Python
- FastAPI
- OpenAI
- Pinecone
- Multi-agent workflow orchestration

### Analytics
- Demand forecasting
- Replenishment recommendation logic
- Predictive analytics
- Prescriptive decision support

### Frontend
- React
- Next.js
- TypeScript
- shadcn/ui

### Data / Workflow / Infrastructure
- Kafka
- Airflow
- Docker
- Kubernetes
- Terraform
- GitHub Actions

### Monitoring / Observability
- Prometheus
- Grafana

### Knowledge / RAG Layer
- Enterprise markdown documents
- Metadata-driven chunking
- Vector retrieval pipeline

## Current Project Status

### Completed
- Multi-agent workflow API implemented
- Frontend workflow UI implemented
- Three official business demo scenarios prepared
- Forecasting and replenishment artifacts generated
- RAG ingestion and retrieval pipeline included
- Integration and unit tests included
- Monitoring assets included
- Kubernetes manifests included
- Terraform structure included

### Current Validated Flow
- Backend API working
- Frontend UI working
- Official demo workflow runs end-to-end
- Forecast and recommendation outputs generated
- RAG-supported reasoning integrated into the workflow
- Core workflow API tests included

## API Endpoints

### Health
`GET /agents/workflow/health`

### Run Workflow
`POST /agents/workflow/run`

Returns structured business workflow outputs such as:
- business_answer
- decision_summary
- forecast_summary
- recommendation_summary
- workflow_overview
- debug

---
## Author

Chathuranga Sudusinghe  
AI Systems Engineer | Generative AI & LLM Architect | Production ML & MLOps | Decision-Centric AI Systems

Linkedin: https://www.linkedin.com/in/chathuranga-sudusinghe
GutHub: https://github.com/chathuranga-sudusinghe
