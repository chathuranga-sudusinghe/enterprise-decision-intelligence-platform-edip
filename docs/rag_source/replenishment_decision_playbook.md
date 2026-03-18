---
document_id: "DOC-NRD-PLB-003"
document_title: "Replenishment Decision Playbook"
document_type: "playbook"
department: "supply_chain_planning"
business_domain: "replenishment"
region_scope: "enterprise"
audience: "cross_functional"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Director of Supply Chain Planning"
confidentiality_level: "internal"
tags:
  - replenishment
  - decision_playbook
  - stock_risk
  - safety_stock
  - service_level
  - lead_time
  - planner_review
  - inventory_balance
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
document_status: "active"
approval_level: "director"
related_structured_domains:
  - fact_demand_forecast
  - fact_replenishment_recommendation
  - fact_planner_override
source_path: "docs/rag_source/replenishment_decision_playbook.md"
---

# Replenishment Decision Playbook
## NorthStar Retail & Distribution
## File: docs/rag_source/replenishment_decision_playbook.md

## 1. Purpose

This playbook defines how NorthStar Retail & Distribution (NRD) should review, interpret, and act on replenishment decisions in a controlled, explainable, and business-aware way.

Its purpose is to help planners and related teams move from system signals to grounded action by combining forecast context, inventory position, supplier reliability, service-level risk, and operational feasibility. This playbook supports EDIP by providing the decision framework needed to explain why replenishment action was taken, delayed, changed, or escalated.

---

## 2. Playbook objectives

The objectives of this playbook are to:

- standardize replenishment decision-making
- reduce inconsistent or instinct-only planner actions
- protect service levels while avoiding unnecessary overstock
- ensure replenishment actions reflect real business conditions
- support explainable and auditable decisioning within EDIP
- improve coordination between planning, procurement, warehouse, and leadership
- strengthen learning from recurring replenishment exceptions

---

## 3. Scope

This playbook applies to:

- system-generated replenishment recommendations
- planner review of standard, priority, and urgent replenishment cases
- inventory-risk and stock coverage decisions
- forecast-led replenishment actions
- supplier- and inbound-sensitive replenishment review
- escalated replenishment situations requiring higher-level governance

This playbook does not apply to:

- routine cases accepted automatically with no material review
- technical model debugging procedures
- pricing-only commercial decisions
- warehouse execution details already governed in SOP documents
- executive-only actions outside planning workflow unless linked to escalation review

---

## 4. Decision principles

### 4.1 Service first, but not service at any cost
Replenishment must protect product availability, but not through uncontrolled inventory build.

### 4.2 Evidence over instinct
Every material replenishment decision should be explainable through business evidence and policy logic.

### 4.3 Forecast-aware, not forecast-blind
The forecast is a major input, but it must be interpreted together with inventory, supply, pricing, promotions, and local conditions.

### 4.4 Inbound supply is not always protection
Open purchase orders or planned receipts should not be treated as fully protective when supplier or receiving reliability is weak.

### 4.5 Early attention prevents late escalation
Strong early review of risk cases is better than delayed reaction under emergency conditions.

### 4.6 Traceability is mandatory
Material replenishment actions, changes, and exceptions must be traceable in the approved decision process.

---

## 5. Definitions

### 5.1 Replenishment decision
A controlled decision on whether, when, and how much inventory should be ordered, expedited, delayed, adjusted, or escalated.

### 5.2 Coverage days
The estimated number of days current inventory can support expected demand.

### 5.3 Reorder threshold
A decision point at which replenishment should be considered to prevent service risk before the next supply arrives.

### 5.4 Priority case
A case requiring faster-than-normal review because risk is above standard but not yet urgent.

### 5.5 Urgent case
A case requiring immediate review because delay may cause material stockout or service impact.

### 5.6 Escalated case
A case where normal planner authority is insufficient.

### 5.7 Recovery confidence
The level of trust that inbound supply, supplier delivery, and warehouse receipt will restore stock in time.

---

## 6. Standard replenishment review workflow

### 6.1 Step 1 — Review the recommendation
Confirm the system recommendation details:

- recommended action type
- recommended quantity
- urgency or priority classification
- affected SKU and location
- expected timing
- main risk indicators

### 6.2 Step 2 — Review demand context
Check:

- recent demand trend
- forecast pattern
- demand stability or volatility
- promotion effect
- pricing effect
- regional or channel variation
- whether the current demand picture is structural or temporary

### 6.3 Step 3 — Review inventory context
Check:

- current on-hand and available stock
- coverage days
- safety stock position
- recent stockout or near-stockout signal
- existing excess inventory
- stock balance across locations where relevant

### 6.4 Step 4 — Review supply context
Check:

- open purchase orders
- expected inbound timing
- supplier lead time
- lead-time reliability
- partial shipment risk
- receiving or warehouse delay risk
- whether open supply can be trusted as real protection

### 6.5 Step 5 — Review business criticality
Check:

- SKU importance
- channel exposure
- service-level sensitivity
- availability impact if the item fails
- substitution difficulty
- regional importance

### 6.6 Step 6 — Decide action path
Based on the full picture, classify the replenishment outcome as:

- no action
- monitor
- replenish standard
- replenish priority
- replenish urgent
- escalate

### 6.7 Step 7 — Log and route the decision
If the case is material, changed, or escalated, it must be logged with reason, evidence, and final action path.

---

## 7. Action outcome framework

### 7.1 No action
Use when inventory position, demand outlook, and inbound protection are sufficient and no material service risk exists.

### 7.2 Monitor
Use when the case is not yet severe but uncertainty is increasing and closer follow-up is needed.

### 7.3 Replenish standard
Use when policy thresholds indicate normal replenishment should proceed under stable or manageable conditions.

### 7.4 Replenish priority
Use when the case is more sensitive than normal and earlier action is justified to reduce service risk.

### 7.5 Replenish urgent
Use when immediate replenishment attention is needed because delay may create stockout or significant service disruption.

### 7.6 Escalate
Use when the decision exceeds planner authority or creates major cross-functional, financial, or enterprise exposure.

---

## 8. When to take no action

A no-action decision may be appropriate when:

- coverage is healthy
- inbound recovery is reliable
- forecast demand is stable and manageable
- safety stock is not threatened
- service-level exposure is low
- recent movement does not justify new action
- existing inventory plus inbound already protects the case sufficiently

No action should still be explainable, not passive neglect.

---

## 9. When to monitor

A monitor decision may be appropriate when:

- the case is not yet severe
- coverage is narrowing but not critical
- demand volatility is present but unclear
- promotion or price impact may be temporary
- inbound supply exists but confidence is not perfect
- regional variation suggests caution
- a clearer signal is expected soon

Monitor cases should not disappear from view. They require structured follow-up.

---

## 10. When to replenish standard

A standard replenishment decision may be appropriate when:

- reorder conditions are met
- the demand signal is usable
- inventory is falling within expected planning logic
- inbound protection is insufficient for full coverage
- supplier conditions are acceptable
- no unusual escalation or override is required

This is the normal governed replenishment path.

---

## 11. When to replenish priority

A priority replenishment decision may be appropriate when:

- coverage is tightening faster than standard tolerance
- the SKU has higher business importance
- supplier lead time or delivery reliability creates added risk
- demand is stronger than expected
- stock recovery timing is becoming uncertain
- regional or channel service exposure is meaningful
- waiting for the next standard cycle may create avoidable risk

Priority does not mean emergency, but it requires earlier attention than routine cases.

---

## 12. When to replenish urgent

An urgent replenishment decision may be appropriate when:

- stockout is likely before recovery
- safety stock protection is being breached materially
- inbound supply cannot be trusted to arrive in time
- critical SKU exposure is high
- demand remains strong while coverage is weak
- supplier failure is creating immediate service threat
- delay would create significant business harm

Urgent cases must enter the high-priority review and execution path.

---

## 13. When to escalate

Escalation is appropriate when:

- the planner cannot safely act within authority
- cross-region allocation trade-offs are required
- the case has major service or financial exposure
- supplier failure cannot be managed locally
- commercial and operational priorities conflict
- warehouse or transport limits block recovery
- recovery requires non-standard action or senior approval

Escalation is a governance tool, not a sign of planner weakness.

---

## 14. Coverage and safety stock interpretation

### 14.1 Healthy coverage
Coverage is considered healthy when expected demand, safety stock, and inbound timing remain comfortably aligned.

### 14.2 Narrowing coverage
When coverage begins to tighten, the reviewer should determine whether the trend is temporary, acceptable, or early warning.

### 14.3 Safety stock entry
When projected stock enters safety stock range, the case requires higher attention because protection buffer is being consumed.

### 14.4 Safety stock breach
When projected stock is expected to fall below safety stock and recovery is uncertain, the case should usually move into priority or urgent review.

### 14.5 False comfort risk
Coverage should not be judged only by current stock if the forecast, supplier reliability, or receiving timing is unstable.

---

## 15. Demand interpretation rules

### 15.1 Stable demand case
If demand is steady and inventory is behaving normally, standard replenishment logic is usually sufficient.

### 15.2 Strong-demand case
If demand is stronger than expected, the reviewer should decide whether the change is structural, regional, promotional, or temporary before increasing action.

### 15.3 Soft-demand case
If demand is softer than expected, the reviewer should check whether sales are truly weak or whether inventory, allocation, or visibility problems are distorting the signal.

### 15.4 Volatile-demand case
If demand is unstable, the reviewer should avoid extreme action unless evidence supports it.

### 15.5 Promotion- or price-affected case
If demand is influenced by discounting or promotion timing, the replenishment decision should be made with commercial context in mind.

---

## 16. Supply and supplier interpretation rules

### 16.1 Reliable supplier case
If supplier timing and quantity fulfillment are dependable, open inbound supply can be treated with higher confidence.

### 16.2 Unstable supplier case
If supplier reliability is weak, open PO visibility alone should not remove replenishment concern.

### 16.3 Partial inbound risk
If partial shipment risk is elevated, the planner should not assume full inventory recovery.

### 16.4 Receiving delay risk
If warehouse intake or receipt timing is under pressure, the practical stock recovery date may be later than nominal shipment arrival.

### 16.5 Supply recovery confidence rule
The lower the recovery confidence, the more cautious the planner should be in delaying or reducing replenishment response.

---

## 17. Overstock prevention rules

A replenishment decision should be slowed, reduced, or reconsidered when:

- forecast support is weak
- current inventory is already elevated
- inbound pipeline is already heavy
- demand appears softer or temporary
- lifecycle or markdown risk exists
- storage or capacity constraints are meaningful
- alternative balancing options exist

The goal is not only to avoid stockout, but also to avoid creating avoidable excess inventory.

---

## 18. Regional and location-aware decision rules

The replenishment decision should account for local conditions when:

- the region is showing stronger demand than enterprise average
- local supplier or inbound conditions are weaker
- service sensitivity differs by channel or location
- substitute availability differs by location
- a regional review indicates special caution is needed

Enterprise averages should not hide meaningful local risk.

---

## 19. Decision evidence standards

### 19.1 Minimum evidence expectation
Every material replenishment decision should be based on identifiable evidence such as:

- forecast and demand pattern
- stock coverage position
- safety stock status
- supplier and inbound condition
- regional demand signal
- promotion or price context
- business criticality

### 19.2 Higher-impact decision expectation
Priority, urgent, and escalated cases require stronger evidence and clearer reasoning.

### 19.3 Unsupported action rule
If the planner cannot explain why the action is needed, the case should not be changed casually.

---

## 20. Decision logging requirements

Material replenishment actions should be logged in the approved process.

### 20.1 Minimum logging fields
A valid replenishment decision log should include:

- decision identifier
- SKU identifier
- location or region
- original recommendation
- final decision
- action type
- reason summary
- evidence summary
- planner or owner
- timestamp
- escalation flag where applicable

### 20.2 Logging quality standard
The note must be specific enough that another reviewer can understand why the action was taken.

### 20.3 Weak logging examples
Weak examples include:
- “replenished”
- “changed priority”
- “looked risky”
- “needed action”

These are not acceptable without business context.

### 20.4 Strong logging examples
Stronger examples include:
- “Urgent replenishment confirmed due to low projected coverage, critical SKU status, and unreliable supplier recovery.”
- “Standard replenishment maintained because demand remains stable and inbound timing is within normal tolerance.”
- “Priority classification applied due to strong regional movement and tightening coverage despite open PO visibility.”

---

## 21. Common decision scenarios

### 21.1 Strong demand with low coverage
Demand exceeds expectation and coverage is tightening. The planner should review whether urgent or priority action is justified.

### 21.2 Soft demand with high stock
Movement is weaker and inventory is already high. The planner should review whether replenishment should be slowed or held.

### 21.3 Open PO but weak supplier confidence
Supply exists on paper, but delivery reliability is weak. The planner should treat the case with caution rather than assuming protection.

### 21.4 Promotion uplift case
Demand is temporarily stronger because of promotion. The planner should determine whether the uplift is temporary or requires more immediate protection.

### 21.5 Regional exception case
One region faces stronger demand or weaker recovery than the enterprise pattern. The planner should use localized logic rather than only aggregate averages.

### 21.6 Cross-functional conflict case
Commercial wants continued availability support, but operational constraints limit safe replenishment. The case may require escalation.

---

## 22. Roles and responsibilities

### 22.1 Inventory Planner
- review the recommendation
- evaluate evidence
- choose the action path
- document the decision
- escalate when necessary

### 22.2 Inventory Analyst
- support data interpretation
- identify recurring risk patterns
- strengthen evidence for high-impact cases

### 22.3 Procurement Team
- provide supplier and inbound reliability context
- support recovery feasibility review

### 22.4 Warehouse / Operations Team
- provide receiving and execution feasibility context
- flag capacity or timing constraints

### 22.5 Supply Chain Manager
- review priority, urgent, and escalated cases
- support governed decision quality

### 22.6 EDIP Decision Support Layer
- surface explainable risk signals
- support policy-aware recommendation review
- maintain decision traceability support
- not replace governed human accountability

---

## 23. Example RAG questions supported by this playbook

This document should help EDIP answer questions such as:

- Why did the system recommend priority replenishment?
- Why was this case treated as urgent?
- Why was no action taken even though stock was lower than usual?
- Why is open supply not enough to remove concern?
- Why did the planner escalate this replenishment case?
- Why was regional context important for the decision?

---

## 24. Related documents

This playbook should be used together with:

- Inventory Replenishment Policy Manual
- Forecast Review Checklist
- Planner Override Playbook
- Executive Exception Escalation Policy
- Supplier Service Level Summary
- Warehouse Receiving SOP
- Regional Performance Review — West

---

## 25. Review and maintenance

This playbook must be reviewed at least annually or earlier when major changes occur in:

- replenishment operating model
- service-level strategy
- supplier risk profile
- inventory governance
- escalation authority structure
- EDIP recommendation logic

All updates must be version-controlled and approved by the responsible business owner.

---

## 26. Final playbook statement

NorthStar Retail & Distribution will manage replenishment through a forecast-aware, inventory-aware, supply-aware, and evidence-based decision framework. Replenishment decisions within EDIP must remain explainable, traceable, and aligned with service protection, overstock control, and governed enterprise execution.