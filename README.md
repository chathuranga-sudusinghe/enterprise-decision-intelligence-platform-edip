# Enterprise Decision Intelligence Platform (EDIP)

## Business Problem Solved

Enterprises often struggle with fragmented data, slow decision cycles, policy-heavy workflows, and weak links between analytics and action. EDIP solves this by combining grounded enterprise retrieval, AI reasoning, predictive analytics, and business-ready recommendations in one system.

This project focuses on a practical enterprise use case:

**Demand Forecasting + Inventory Decision Support for NorthStar Retail & Distribution**

EDIP helps answer business questions such as:
- Why was urgent replenishment recommended?
- Is there a high stockout risk next week?
- Should a store reorder stock or transfer it from another location?

---

## System Overview

EDIP is a production-oriented enterprise AI system that combines:

- **RAG + LLM reasoning** for grounded business explanations
- **Multi-agent orchestration** for controlled workflow execution
- **Predictive and prescriptive analytics** for demand and replenishment decisions
- **Business-facing APIs and UI** for operational use
- **Testing, governance, and deployment readiness** for enterprise delivery

The current decision flow is:

**Planner → Retrieval → Reasoning → Analytics → Execution**

### Current workflow behavior

1. A business user asks a decision-oriented question.
2. The **Planner Agent** detects the task type and required workflow path.
3. The **Retrieval Agent** gathers relevant enterprise knowledge and document context.
4. The **Reasoning Agent** interprets the request using grounded business evidence.
5. The **Analytics Agent** runs forecast and recommendation logic when needed.
6. The **Execution Agent** converts the result into a business-facing recommendation or explanation.
7. The system returns structured outputs through API and frontend UI.

---

## Official Demo Scenarios

### 1. Urgent Replenishment
**Question:** Why was urgent replenishment recommended for SKU-100245 at store 210?

**Purpose:**  
Shows the strongest end-to-end scenario with grounded explanation, forecast summary, and prescriptive replenishment recommendation.

### 2. High Stockout Risk
**Question:** Is there a high stockout risk for SKU-100245 at store 210 next week?

**Purpose:**  
Shows risk-focused decision support using enterprise context plus analytical signals.

### 3. Reorder vs Transfer
**Question:** Should store 210 reorder SKU-100245 or transfer stock from another location?

**Purpose:**  
Shows action-choice decisioning where the system recommends the better operational action.

---

## Architecture

### 1. Unified Data Layer
Enterprise structured and unstructured data is unified for downstream decision intelligence.

**Planned / used components**
- Snowflake
- Kafka
- batch / connector-driven ingestion
- normalized enterprise data model

### 2. RAG + LLM Layer
Business knowledge is embedded, indexed, retrieved, and used for grounded reasoning.

**Core components**
- OpenAI
- Pinecone
- enterprise documents
- retrieval pipelines
- embeddings pipeline

### 3. AI Agent Orchestration Layer
The workflow is controlled through modular enterprise agents.

**Agents**
- Planner Agent
- Retrieval Agent
- Reasoning Agent
- Analytics Agent
- Execution Agent

### 4. Predictive + Prescriptive Analytics Layer
This layer adds numerical forecasting and decision support beyond language reasoning.

**Core functions**
- demand forecasting
- replenishment recommendation
- stockout risk support
- decision-oriented structured outputs

### 5. API + Frontend Layer
This is the business-facing surface of EDIP.

**Backend**
- FastAPI

**Frontend**
- React / Next.js

The frontend currently displays:
- Why
- Decision
- Forecast Summary
- Recommendation
- Workflow Overview
- Debug Payload

### 6. Workflow Orchestration Layer
EDIP also includes batch/scheduled workflow capability.

**Orchestration**
- Airflow

### 7. Production Engineering Layer
The project is designed with enterprise deployment direction.

**Production stack direction**
- Docker
- Kubernetes
- GitHub Actions
- Terraform
- monitoring / logging
- governance / auditability

---

## Tech Stack

### Core AI / Decision System
- Python
- FastAPI
- OpenAI
- Pinecone
- multi-agent workflow design

### Analytics
- Python forecasting / recommendation workflow
- scikit-learn style ML layer
- predictive + prescriptive decision logic

### Frontend
- React
- Next.js
- TypeScript
- shadcn/ui
- Framer Motion

### Data / Orchestration / Infra
- Snowflake
- Kafka
- Airflow
- Docker
- Kubernetes
- Terraform
- GitHub Actions

---

## Current Project Status

### Completed
- Agent workflow API is working
- Frontend workflow UI is working
- Official demo scenarios are working
- Urgent replenishment scenario is stable
- Stockout risk scenario is working
- Reorder vs transfer scenario is working
- Integration tests for the workflow API are passing

### Current validated flow
- backend API working
- frontend UI working
- manual demo validation completed
- official workflow API tests passed

---

## API Endpoints

### Health
`GET /agents/workflow/health`

### Run full workflow
`POST /agents/workflow/run`

This endpoint returns a structured response including:
- `business_answer`
- `decision_summary`
- `forecast_summary`
- `recommendation_summary`
- `workflow_overview`
- `debug`

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