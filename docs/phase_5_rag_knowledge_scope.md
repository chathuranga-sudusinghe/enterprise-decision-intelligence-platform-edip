# Phase 5 — RAG Knowledge Scope
## EDIP / NorthStar Retail & Distribution
## File: docs/phase_5_rag_knowledge_scope.md

---

## 1. Purpose

This document defines the official **Phase 5 RAG knowledge scope** for the **Enterprise Decision Intelligence Platform (EDIP)**.

Phase 5 introduces the **business document layer** that will support:

- enterprise retrieval
- grounded LLM responses
- multi-agent reasoning
- audit-friendly business explanations
- policy-aware decision support

This RAG layer must use **NorthStar Retail & Distribution (NRD)** documents only, so the retrieved knowledge stays consistent with the structured data, planning logic, and synthetic enterprise workflow already built in Phases 1–4.

---

## 2. Phase 5 objective

The objective of Phase 5 is to create a clean, enterprise-grade set of synthetic business documents that can be:

1. stored in document folders
2. chunked and indexed
3. embedded into the vector database
4. retrieved by agents and APIs
5. used to explain forecasts, replenishment actions, overrides, alerts, and decision logs

This phase is not only about creating text files.  
It is about defining the **official business knowledge boundary** for EDIP.

---

## 3. Knowledge design principles

All Phase 5 documents must follow these rules:

### 3.1 One-company consistency
Every document must belong to **NorthStar Retail & Distribution** only.

Do not mix:
- unrelated public documents
- other company names
- generic policy text that breaks the NorthStar flow

### 3.2 Business-data consistency
Documents must agree with the structured data logic already locked in the system.

Examples:
- replenishment policy must align with forecast and recommendation behavior
- supplier SLA documents must align with supplier lead-time logic
- pricing policy must align with promotions and price-history behavior
- escalation policies must align with planner override and decision-log logic

### 3.3 Retrieval usefulness
Documents must be written in a way that helps RAG answer questions such as:
- why a recommendation was made
- what policy applies
- what rule was violated
- what service level target is expected
- what escalation path should be followed

### 3.4 Enterprise realism
Documents should sound like real internal business material:
- policy manuals
- SOPs
- memos
- reviews
- decision playbooks
- escalation guides

### 3.5 Auditability
Documents should support traceable business explanations, not only general chatbot answers.

---

## 4. Official document categories

Phase 5 will include these main knowledge categories.

### 4.1 Corporate policy documents
Purpose:
High-level internal policy guidance used by planners, managers, and operations teams.

Examples:
- inventory policy
- pricing policy
- promotion policy
- service-level policy
- escalation policy

### 4.2 Standard operating procedures (SOPs)
Purpose:
Step-by-step operational instructions for stores, warehouses, procurement, and inventory teams.

Examples:
- store operations SOP
- warehouse receiving SOP
- inventory adjustment SOP
- supplier issue handling SOP
- low-stock response SOP

### 4.3 Planning and decision documents
Purpose:
Documents that explain how planning decisions should be made.

Examples:
- replenishment playbook
- planner override rules
- forecast review checklist
- exception response matrix
- decision approval guide

### 4.4 Performance and review documents
Purpose:
Periodic summaries that help explain trends, exceptions, and business outcomes.

Examples:
- monthly demand review report
- regional performance review
- promotion performance memo
- supplier performance summary
- executive exception review

### 4.5 HR / governance / rules documents
Purpose:
Enterprise governance and employee guidance for internal operations and compliance.

Examples:
- analyst handbook excerpt
- planner responsibility matrix
- approval authority rules
- access and audit policy
- internal communication rules

### 4.6 Supplier and procurement documents
Purpose:
Documents related to supplier expectations, receiving, lead times, and service commitments.

Examples:
- supplier SLA summary
- inbound receiving standards
- procurement lead-time rules
- shortage escalation guide
- supplier performance classification guide

---

## 5. Official Phase 5 starter document set

The first document set for EDIP V1 should include these files.

### 5.1 Policies
- `inventory_replenishment_policy_manual.md`
- `pricing_and_discount_policy.md`
- `promotion_execution_policy.md`
- `executive_exception_escalation_policy.md`
- `planner_override_governance_policy.md`

### 5.2 SOPs
- `store_operations_sop.md`
- `warehouse_receiving_sop.md`
- `inventory_adjustment_sop.md`
- `low_stock_response_sop.md`
- `supplier_issue_handling_sop.md`

### 5.3 Planning / decision playbooks
- `replenishment_decision_playbook.md`
- `forecast_review_checklist.md`
- `planner_override_playbook.md`
- `regional_inventory_risk_playbook.md`
- `promotion_impact_review_guide.md`

### 5.4 Reviews / memos
- `monthly_demand_review_report_jan_2025.md`
- `monthly_demand_review_report_feb_2025.md`
- `regional_performance_review_west.md`
- `promotion_planning_memo_q4.md`
- `supplier_service_level_summary.md`

### 5.5 Governance / HR / access
- `planning_team_roles_and_responsibilities.md`
- `approval_authority_matrix.md`
- `audit_logging_and_decision_trace_policy.md`
- `internal_operational_communication_guidelines.md`

---

## 6. Suggested folder structure

Phase 5 documents should be organized like this:

```text
docs/
├── policies/
│   ├── inventory_replenishment_policy_manual.md
│   ├── pricing_and_discount_policy.md
│   ├── promotion_execution_policy.md
│   ├── executive_exception_escalation_policy.md
│   └── planner_override_governance_policy.md
│
├── sops/
│   ├── store_operations_sop.md
│   ├── warehouse_receiving_sop.md
│   ├── inventory_adjustment_sop.md
│   ├── low_stock_response_sop.md
│   └── supplier_issue_handling_sop.md
│
├── reviews/
│   ├── monthly_demand_review_report_jan_2025.md
│   ├── monthly_demand_review_report_feb_2025.md
│   ├── regional_performance_review_west.md
│   ├── promotion_planning_memo_q4.md
│   └── supplier_service_level_summary.md
│
└── rag_source/
    ├── replenishment_decision_playbook.md
    ├── forecast_review_checklist.md
    ├── planner_override_playbook.md
    ├── regional_inventory_risk_playbook.md
    ├── promotion_impact_review_guide.md
    ├── planning_team_roles_and_responsibilities.md
    ├── approval_authority_matrix.md
    ├── audit_logging_and_decision_trace_policy.md
    └── internal_operational_communication_guidelines.md