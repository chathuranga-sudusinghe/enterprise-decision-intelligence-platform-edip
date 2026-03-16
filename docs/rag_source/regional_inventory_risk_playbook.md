---
document_id: "DOC-NRD-PLB-004"
document_title: "Regional Inventory Risk Playbook"
document_type: "playbook"
department: "supply_chain_planning"
business_domain: "inventory"
region_scope: "enterprise"
audience: "cross_functional"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Director of Regional Inventory Planning"
confidentiality_level: "internal"
tags:
  - regional_inventory_risk
  - stock_risk
  - service_risk
  - regional_planning
  - coverage_days
  - supplier_risk
  - allocation
  - escalation
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
document_status: "active"
approval_level: "director"
related_structured_domains:
  - fact_inventory_snapshot
  - fact_replenishment_recommendation
  - fact_stock_movements
source_path: "docs/rag_source/regional_inventory_risk_playbook.md"
---

# Regional Inventory Risk Playbook
## NorthStar Retail & Distribution
## File: docs/rag_source/regional_inventory_risk_playbook.md

## 1. Purpose

This playbook defines how NorthStar Retail & Distribution (NRD) should identify, interpret, prioritize, and respond to inventory risk at the regional level.

Its purpose is to help planners and operational teams move beyond enterprise averages and recognize where local demand, supply, inventory, and execution conditions create materially different risk profiles. This playbook supports EDIP by providing a grounded framework for explaining why one region may require higher attention, earlier action, tighter monitoring, or escalation.

---

## 2. Playbook objectives

The objectives of this playbook are to:

- standardize regional inventory-risk review
- ensure local risk is not hidden by enterprise averages
- improve early identification of service and stock exposure
- support region-aware replenishment and allocation decisions
- reduce avoidable stockout and overstock outcomes
- strengthen cross-functional regional coordination
- provide explainable, auditable inventory-risk reasoning within EDIP

---

## 3. Scope

This playbook applies to:

- regional inventory-risk review across NorthStar operations
- region-specific stockout and overstock risk interpretation
- regional demand and supply imbalance cases
- allocation-sensitive decisions
- supplier, inbound, and receiving issues affecting local availability
- cases where planner review, priority action, or escalation is needed due to regional conditions

This playbook does not apply to:

- purely enterprise-level summary reporting without local risk interpretation
- technical model-debugging activity
- pricing-only decisions unless they materially affect regional inventory risk
- warehouse execution procedures already governed in separate SOPs

---

## 4. Core principles

### 4.1 Local reality matters
A region may be high-risk even when enterprise metrics look stable.

### 4.2 Risk is multi-factor
Regional inventory risk must be reviewed using demand, stock, supply, service, and execution signals together.

### 4.3 Early signals are valuable
Narrowing coverage, weak inbound confidence, or local demand concentration may justify attention before a stockout actually happens.

### 4.4 One response does not fit all regions
Different regions may require different levels of caution, review frequency, and action.

### 4.5 Traceability is required
Material regional risk decisions must be documented clearly enough to support auditability and future learning.

### 4.6 Regional review supports enterprise control
Better local review improves enterprise decision quality, not just regional visibility.

---

## 5. Definitions

### 5.1 Regional inventory risk
The probability that a region will face material inventory imbalance, service pressure, or stock-related disruption because of local demand, supply, or execution conditions.

### 5.2 Service risk
The likelihood that product availability will fall below acceptable business expectation.

### 5.3 Coverage pressure
A situation where available inventory is declining faster than comfort threshold relative to expected demand.

### 5.4 Allocation conflict
A case where limited inventory must be shared between regions with competing needs.

### 5.5 Recovery confidence
The level of trust that planned inbound supply and execution will restore inventory in time.

### 5.6 Regional exception
A case where local inventory conditions differ enough from enterprise norms to require separate interpretation or action.

---

## 6. Regional risk review workflow

### 6.1 Step 1 — Identify the region-specific case
Confirm:

- affected region
- affected SKU or category
- current stock position
- forecast and demand pattern
- current replenishment state
- whether the case is isolated or repeated

### 6.2 Step 2 — Review local demand conditions
Check:

- recent regional sales movement
- strength versus enterprise average
- volatility or instability
- promotion or price effects
- local event effects
- whether demand concentration is affecting a few high-risk items

### 6.3 Step 3 — Review inventory condition
Check:

- on-hand and available stock
- coverage days
- safety stock position
- recent stockout or near-stockout history
- excess stock condition
- inventory aging where relevant

### 6.4 Step 4 — Review inbound and supplier support
Check:

- open purchase orders
- planned transfers
- supplier timing reliability
- partial shipment risk
- receiving delay risk
- region-specific delivery constraints
- confidence that recovery will arrive in time

### 6.5 Step 5 — Review business importance
Check:

- regional revenue importance
- service-level sensitivity
- critical SKU status
- substitution difficulty
- channel exposure
- customer-impact sensitivity

### 6.6 Step 6 — Determine action outcome
Classify the case as one of the following:

- stable
- monitor
- priority review
- urgent intervention
- allocation review
- escalate

### 6.7 Step 7 — Log and route the case
Material regional risk decisions must be recorded with reason, evidence, and next action.

---

## 7. Risk outcome framework

### 7.1 Stable
Use when stock, demand, and recovery conditions remain within acceptable regional tolerance.

### 7.2 Monitor
Use when local uncertainty is rising but immediate intervention is not yet required.

### 7.3 Priority review
Use when the region is showing clear early warning signals that justify faster planner attention.

### 7.4 Urgent intervention
Use when the region is close to material service failure or rapid availability loss.

### 7.5 Allocation review
Use when inventory is limited and regional trade-offs must be reviewed before action.

### 7.6 Escalate
Use when the regional case exceeds planner or regional management authority.

---

## 8. Stable regional case criteria

A regional case may be considered stable when:

- coverage is healthy
- demand is within expected range
- supplier and inbound support are reliable
- no unusual receiving or execution issue exists
- service-level exposure is low
- local performance is aligned with normal planning tolerance

Stable does not mean no monitoring. It means no unusual action is currently required.

---

## 9. Monitor case criteria

A region should move into monitor status when:

- coverage is narrowing
- demand is strengthening faster than expected
- supplier or inbound confidence is slightly weaker
- stock balance is becoming less comfortable
- recent local volatility exists
- early service pressure is visible but not yet critical

Monitor cases should remain visible in the next review cycle.

---

## 10. Priority review criteria

A region should move into priority review when:

- several early warning signals appear together
- strong demand and lower coverage are occurring together
- inbound recovery is uncertain
- local service sensitivity is meaningful
- supplier inconsistency affects important SKUs
- delay may create avoidable risk before the next cycle

Priority review means faster planner attention and earlier action consideration.

---

## 11. Urgent intervention criteria

A region should move into urgent intervention when:

- stockout is likely
- safety stock protection is materially threatened
- supplier or inbound recovery is unlikely to arrive in time
- critical SKUs face immediate local service risk
- local demand remains strong while stock is weak
- operational delays are worsening the recovery path

Urgent regional cases should not wait for routine review timing.

---

## 12. Allocation review criteria

Allocation review is required when:

- supply is insufficient to fully support multiple regions
- one region’s recovery may reduce another region’s protection
- critical SKU availability must be prioritized
- service trade-offs must be made between regions
- enterprise averages do not resolve the local conflict

Allocation review must be evidence-based and governed.

---

## 13. Escalation criteria

Escalation is appropriate when:

- regional teams cannot safely resolve the case within authority
- allocation conflict is enterprise significant
- financial or service exposure is unusually high
- cross-functional approval is required
- local mitigation options are inadequate
- repeated regional exceptions suggest broader structural weakness

Escalation is the correct path when the regional case exceeds normal control.

---

## 14. Demand-aware regional interpretation rules

### 14.1 Strong local demand case
If regional demand is stronger than enterprise average, replenishment and risk logic should reflect local reality rather than aggregate averages.

### 14.2 Soft-demand case
If local demand is weaker, the reviewer should check whether the weakness is real, temporary, or caused by inventory visibility or execution issues.

### 14.3 Volatile-demand case
If demand is unstable, the reviewer should avoid overreacting without stronger evidence.

### 14.4 Promotion-affected case
If a region is under promotion or recent promotion carryover, local demand should be interpreted with campaign timing in mind.

### 14.5 Stock-constrained case
If sales are low because local stock was weak, true demand may be understated.

---

## 15. Inventory-aware regional interpretation rules

### 15.1 Healthy coverage case
If coverage remains comfortable and demand is manageable, the region may remain stable even if enterprise risk elsewhere is rising.

### 15.2 Narrowing coverage case
If coverage is declining, the reviewer must decide whether it is normal movement or meaningful early warning.

### 15.3 Safety stock entry
When projected inventory enters safety stock range, the region should receive higher attention.

### 15.4 Safety stock breach
If projected inventory falls below safety stock and recovery is uncertain, the case should move into priority or urgent attention.

### 15.5 Overstock pocket
If local inventory remains high while movement softens, replenishment should be slowed or reviewed rather than continued blindly.

---

## 16. Supply-aware regional interpretation rules

### 16.1 Reliable recovery case
If suppliers and inbound receipts are dependable, planned recovery can be treated with higher confidence.

### 16.2 Weak recovery confidence case
If supplier timing or fulfillment is unstable, the region should not rely fully on inbound visibility alone.

### 16.3 Receiving-sensitive case
If the receiving site is under operational pressure, actual availability may lag behind shipment arrival.

### 16.4 Region-specific delivery issue
If transport or routing issues affect one region more than others, risk must be reviewed locally.

### 16.5 Partial support case
If only partial recovery is expected, planners should avoid treating the region as fully protected.

---

## 17. Business criticality rules

Regional risk must receive stronger attention when one or more of the following apply:

- the SKU is critical
- the region has high commercial importance
- substitute options are limited
- customer-impact sensitivity is high
- service failure in the region may create wider business consequences
- channel importance is high

Business importance changes how local inventory risk should be interpreted.

---

## 18. Common regional risk scenarios

### 18.1 Strong demand with weak recovery
The region shows healthy demand, but inbound recovery timing is unreliable. This should move to priority or urgent review depending on coverage.

### 18.2 Low sales with low stock
Observed movement is soft, but inventory was also weak. The case should not be treated as simple demand softness without further review.

### 18.3 Overstock in slower regional pocket
Demand softened, but inventory remains elevated. Replenishment should be reviewed and possibly slowed.

### 18.4 Allocation conflict between regions
A limited pool of stock must be divided between regions with different demand and service conditions. Allocation review is required.

### 18.5 Repeated regional exception pattern
The same region repeatedly shows coverage pressure or inbound weakness. This may indicate structural local risk requiring escalation or broader planning change.

---

## 19. Decision evidence standards

### 19.1 Minimum evidence expectation
Every material regional inventory-risk decision should be supported by evidence such as:

- regional demand pattern
- stock coverage position
- safety stock status
- supplier and inbound reliability
- receiving condition
- promotion or price context
- critical SKU status
- allocation constraints where relevant

### 19.2 Higher-impact case expectation
Urgent, allocation, and escalated cases require stronger evidence and clearer business reasoning.

### 19.3 Unsupported action rule
If the regional action cannot be explained with evidence, the case should not be changed casually.

---

## 20. Decision logging requirements

Material regional risk outcomes must be recorded in the approved decision process.

### 20.1 Minimum logging fields
A valid regional inventory-risk log should include:

- risk case identifier
- region
- SKU or category
- current risk status
- evidence summary
- action outcome
- owner or reviewer
- timestamp
- escalation flag where applicable
- next review or action note

### 20.2 Logging quality standard
The log note must be specific enough that another reviewer can understand why the region was classified and what should happen next.

### 20.3 Weak logging examples
Weak examples include:
- “region risky”
- “monitor this”
- “low stock”
- “needs attention”

These are not acceptable without context.

### 20.4 Strong logging examples
Stronger examples include:
- “Priority review assigned due to strong West demand, tightening coverage, and low recovery confidence on open inbound supply.”
- “Allocation review triggered because available stock is insufficient to protect both West and Central regions for a critical SKU.”
- “Monitor status maintained because coverage remains acceptable, but supplier timing variability has increased.”

---

## 21. Roles and responsibilities

### 21.1 Inventory Planner
- review regional risk cases
- interpret demand, stock, and supply evidence
- recommend action path
- document the case
- escalate when required

### 21.2 Regional Manager
- provide local operational context
- support interpretation of execution constraints
- coordinate region-specific response where needed

### 21.3 Inventory Analyst
- identify recurring regional patterns
- support evidence preparation
- improve risk visibility and reporting

### 21.4 Procurement Team
- provide supplier and inbound confidence input
- support assessment of recovery reliability

### 21.5 Operations / Warehouse Team
- provide receiving and execution feasibility context
- flag timing or capacity issues affecting the region

### 21.6 Supply Chain Manager
- review priority, urgent, allocation, and escalated cases
- ensure governed action quality

### 21.7 EDIP Decision Support Layer
- surface region-aware risk signals
- support explainable local risk reasoning
- maintain traceability support
- not replace governed human accountability

---

## 22. Example RAG questions supported by this playbook

This document should help EDIP answer questions such as:

- Why is this region considered high-risk even though enterprise performance looks stable?
- Why did West move into priority review?
- Why is open inbound supply not enough to remove local concern?
- Why was allocation review required between regions?
- Why did this regional case need escalation?
- Why is local demand strength more important than enterprise average in this case?

---

## 23. Related documents

This playbook should be used together with:

- Inventory Replenishment Policy Manual
- Replenishment Decision Playbook
- Forecast Review Checklist
- Supplier Service Level Summary
- Warehouse Receiving SOP
- Executive Exception Escalation Policy
- Regional Performance Review — West

---

## 24. Review and maintenance

This playbook must be reviewed at least annually or earlier when major changes occur in:

- regional planning model
- allocation governance
- supplier risk profile
- distribution network behavior
- service-level strategy
- EDIP decision logic

All updates must be version-controlled and approved by the responsible business owner.

---

## 25. Final playbook statement

NorthStar Retail & Distribution will manage regional inventory risk through a region-aware, evidence-based, and traceable decision framework. Regional cases within EDIP must be interpreted using local demand, stock, supply, service, and execution context so that inventory actions remain controlled, explainable, and aligned with enterprise priorities.