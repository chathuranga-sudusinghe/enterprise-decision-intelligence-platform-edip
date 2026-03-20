---
document_id: "DOC-NRD-PLB-001"
document_title: "Planner Override Playbook"
document_type: "playbook"
department: "supply_chain_planning"
business_domain: "overrides"
region_scope: "enterprise"
audience: "cross_functional"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Director of Supply Chain Planning"
confidentiality_level: "internal"
tags:
  - planner_override
  - decision_governance
  - replenishment
  - escalation
  - exception_handling
  - auditability
  - decision_log
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
source_path: "docs/rag_source/planner_override_playbook.md"
---

# Planner Override Playbook
## NorthStar Retail & Distribution
## File: "docs/rag_source/planner_override_playbook.md"

## 1. Purpose

This playbook defines how planners at NorthStar Retail & Distribution (NRD) should review, justify, apply, and document overrides to system-generated recommendations.

Its purpose is to ensure that planner overrides are business-valid, consistent, traceable, and governed. This playbook supports EDIP by providing the operational decision rules needed to explain why a recommendation was changed, when human intervention is appropriate, and how override actions should be logged for audit and future analysis.

---

## 2. Playbook objectives

The objectives of this playbook are to:

- define when planner overrides are appropriate
- prevent unnecessary or weakly justified overrides
- improve consistency in human review decisions
- ensure overrides are supported by business evidence
- protect service level, inventory balance, and decision quality
- create strong decision traceability for EDIP explanations and audit review
- support learning from override patterns over time

---

## 3. Scope

This playbook applies to:

- system-generated replenishment recommendations
- priority and urgent review cases
- inventory-risk exceptions
- forecast-sensitive planning decisions
- supplier-related recovery decisions
- planner decisions requiring quantity, priority, or status changes
- override actions recorded in the approved decision process

This playbook does not apply to:

- routine recommendations accepted without modification
- executive-only decisions outside planner authority
- system defects requiring technical correction rather than business override
- changes made outside approved planning workflow

---

## 4. Override philosophy

### 4.1 System-first, not system-only
The system should be treated as the default recommendation engine, but not as the only source of judgment. Human planners are expected to intervene when business reality is not fully captured by the model or rule set.

### 4.2 Override by evidence, not instinct
An override must be based on business evidence, verified context, or approved operational knowledge. Personal preference alone is not a valid reason.

### 4.3 Governance over convenience
Planners must not override a recommendation simply because the system result is inconvenient, unexpected, or operationally uncomfortable.

### 4.4 Traceability is mandatory
If the recommendation changes in a material way, the reason must be recorded clearly enough for another reviewer to understand what happened and why.

### 4.5 Repeated overrides are signals
Repeated overrides on the same pattern may indicate deeper issues such as model weakness, data quality issues, supplier instability, or missing business rules.

---

## 5. Definitions

### 5.1 Override
A planner-initiated change to a system-generated recommendation or action classification.

### 5.2 Material override
Any override that changes order quantity, urgency level, priority status, action type, or escalation path in a meaningful way.

### 5.3 Override reason
The documented business explanation for why the planner changed the recommendation.

### 5.4 Decision log
The approved record of override action, rationale, timing, user, and related business context.

### 5.5 Escalated override
An override that exceeds normal planner authority or creates broader service, financial, or operational impact.

### 5.6 Exception case
A case where normal recommendation logic may not reflect actual business conditions due to unusual events, disruptions, or verified business context.

---

## 6. When an override is appropriate

A planner override may be appropriate when one or more of the following conditions apply:

- confirmed supplier disruption is not yet fully reflected in the system
- inbound shipment timing is unreliable despite open PO visibility
- forecast distortion is caused by temporary or known event behavior
- promotion timing or commercial action creates exceptional demand expectation
- warehouse capacity or operational constraint changes the practical decision
- regional allocation issue requires non-standard handling
- critical SKU business importance is higher than standard logic captures
- master-data issue is verified and materially affects the recommendation
- executive commercial instruction has been formally communicated
- urgent business event requires near-term decision adjustment

An override is appropriate only when the planner has enough evidence to justify the decision.

---

## 7. When an override is not appropriate

An override is not appropriate when:

- the planner simply dislikes the system result
- no supporting business evidence exists
- the case should instead be escalated
- the issue is caused by a known technical defect requiring system correction
- the override is being used to hide a process issue
- the planner cannot explain the logic clearly
- the decision would create unnecessary stock exposure or service risk without justification

Weak or habitual overrides reduce system trust and decision quality.

---

## 8. Common valid override categories

### 8.1 Supplier disruption override
Use when a supplier delivery, lead-time, or fulfillment issue is verified and the system recommendation assumes more supply certainty than is actually safe.

### 8.2 Forecast distortion override
Use when demand forecasts are temporarily distorted by unusual events, data problems, or special conditions not yet reflected in model behavior.

### 8.3 Promotion timing override
Use when promotion activation, delay, extension, or execution risk materially changes expected demand or stock exposure.

### 8.4 Warehouse constraint override
Use when receiving, storage, labor, or handling limits make the original recommendation impractical in the short term.

### 8.5 Critical SKU protection override
Use when product importance, channel exposure, or customer impact requires stronger protection than standard logic provided.

### 8.6 Master-data correction override
Use when a verified data issue such as wrong lead time, classification, or status is materially affecting the recommendation.

### 8.7 Executive instruction override
Use only when a formal and traceable business direction has been issued by an authorized decision owner.

---

## 9. Standard override review workflow

### 9.1 Step 1 — Review the system recommendation
The planner must first understand:

- recommended action type
- recommended quantity or urgency
- main risk indicators
- forecast context
- inventory position
- inbound supply status
- service-level exposure

### 9.2 Step 2 — Identify the trigger for concern
The planner should define clearly what seems incomplete, incorrect, or operationally risky in the recommendation.

Examples:
- inbound shipment is technically open but practically unreliable
- forecast uplift is likely temporary
- current warehouse intake capacity is constrained
- product criticality is understated

### 9.3 Step 3 — Gather supporting evidence
Before changing the recommendation, the planner should collect relevant evidence such as:

- supplier update
- receiving discrepancy pattern
- forecast review insight
- commercial schedule detail
- recent operational alert
- verified master-data issue
- leadership instruction reference

### 9.4 Step 4 — Decide action type
The planner should determine whether to:

- accept the system recommendation
- adjust quantity
- adjust urgency
- delay action
- escalate the case
- reject the system recommendation and apply alternate action within authority

### 9.5 Step 5 — Record the override
If the recommendation is changed materially, the planner must log:

- original recommendation
- overridden recommendation
- override category
- clear reason
- evidence summary
- date and time
- planner identity
- escalation reference where applicable

### 9.6 Step 6 — Escalate where required
If the override exceeds planner authority or creates major business exposure, it must be escalated according to governance rules.

---

## 10. Override decision rules

### 10.1 Quantity override rule
A planner may adjust recommended quantity when reliable business evidence shows that the system quantity is too high or too low relative to actual business conditions.

### 10.2 Urgency override rule
A planner may change urgency level when service risk, supplier behavior, or operational timing indicates the original priority is too weak or too strong.

### 10.3 Delay rule
A planner may delay action only when the delay is evidence-based and does not create unmanaged service risk.

### 10.4 Rejection rule
A planner may reject a recommendation only when the recommendation is clearly unsuitable and an alternate action path exists within approved governance.

### 10.5 Escalation rule
When the planner cannot safely resolve the case within authority, escalation is mandatory.

---

## 11. Required evidence standards

The strength of override evidence should match the size of the override impact.

### 11.1 Minimum evidence expectation
Every material override should have at least one clear business basis such as:

- confirmed supplier update
- verified warehouse issue
- approved promotion plan detail
- recent forecast review finding
- documented master-data issue
- leadership instruction trace

### 11.2 Higher-impact override expectation
Larger or riskier overrides should have stronger supporting evidence, broader review, or escalated approval.

### 11.3 Unsupported override rule
If no defensible evidence exists, the planner should not override the system recommendation.

---

## 12. Decision logging requirements

Every material override must be logged in the approved decision process.

### 12.1 Minimum required fields
A valid override log should capture:

- recommendation identifier
- SKU identifier
- location or region
- original recommendation
- overridden recommendation
- override type
- override reason
- evidence summary
- planner user
- decision timestamp
- escalation flag if applicable
- final decision status

### 12.2 Logging quality standard
The reason text must be specific enough that another planner, auditor, or manager can understand the decision without guessing.

### 12.3 Poor logging examples
Poor reason examples include:
- “planner choice”
- “adjusted”
- “felt too high”
- “not suitable”

These are not acceptable because they are vague and not auditable.

### 12.4 Strong logging examples
Stronger examples include:
- “Urgency increased due to confirmed supplier delay on open PO and critical SKU coverage below target.”
- “Quantity reduced due to verified warehouse intake constraint and excess inbound already scheduled.”
- “Recommendation delayed pending correction of incorrect supplier lead time in master data.”

---

## 13. Escalation guidance

A planner must escalate when:

- override exceeds approval authority
- service-level exposure is enterprise significant
- financial exposure is unusually high
- cross-region inventory reallocation is required
- executive or commercial conflict exists
- supporting evidence is incomplete but risk is major
- multiple teams must align before action is safe

Escalation should not be treated as failure. It is the correct control when business risk exceeds planner authority.

---

## 14. High-risk override scenarios

The following scenarios require additional caution:

### 14.1 Lowering urgency on a critical SKU
This may create hidden stockout risk if evidence is weak.

### 14.2 Increasing quantity significantly
This may create overstock, margin, and capacity exposure.

### 14.3 Ignoring supplier instability
Open supply visibility alone is not enough when service reliability is poor.

### 14.4 Overriding during active promotion period
Demand behavior may be unstable and harder to interpret.

### 14.5 Repeated overrides on the same SKU or supplier
This may indicate deeper structural issues requiring review, not just local override handling.

---

## 15. Override review patterns EDIP should monitor

Override data should be monitored for patterns such as:

- repeat overrides by SKU
- repeat overrides by supplier
- repeat overrides by planner
- frequent urgency increases
- frequent quantity reductions
- common override reasons
- escalation frequency
- conflict between system and planner outcomes

These patterns help identify:
- missing business rules
- weak model behavior
- unstable upstream data
- supplier problems
- training or governance issues

---

## 16. Roles and responsibilities

### 16.1 Inventory Planner
- review system recommendations
- determine whether override is justified
- gather evidence
- record override properly
- escalate when authority is exceeded

### 16.2 Inventory Analyst
- support evidence gathering
- analyze override trends
- identify recurring pattern issues
- support decision-quality review

### 16.3 Supply Chain Manager
- review escalated or high-impact overrides
- ensure governance compliance
- approve within management authority where required

### 16.4 Procurement Team
- provide supplier-related context for override decisions
- support confirmation of delays, shortages, or fulfillment risk

### 16.5 Commercial / Operations Stakeholders
- provide event, promotion, or operational constraint context where relevant

### 16.6 EDIP Decision Support Layer
- present explainable recommendations
- capture original recommendation state
- support override logging and downstream analysis
- not replace human accountability for override governance

---

## 17. Example override use cases

### 17.1 Supplier delay case
The system recommends standard replenishment because an open PO exists. The planner increases urgency after verified supplier delay and low remaining stock coverage.

### 17.2 Forecast spike distortion case
The system recommends urgent action based on a demand spike. The planner reduces urgency after confirming that the spike was a temporary anomaly and not structural demand.

### 17.3 Warehouse capacity case
The system recommends a larger replenishment quantity. The planner reduces quantity because the receiving site has confirmed short-term intake constraints.

### 17.4 Critical SKU protection case
The system classifies the action as monitor. The planner upgrades to priority because the SKU is strategically important and channel exposure is high.

### 17.5 Master-data issue case
The system uses an incorrect lead time. The planner delays final acceptance of the recommendation and logs a master-data correction override with evidence.

---

## 18. Example RAG questions supported by this playbook

This document should help EDIP answer questions such as:

- Why did the planner override this recommendation?
- Why was urgency increased even though supply was already open?
- Why was quantity reduced from the system recommendation?
- Why did this case require escalation?
- Why is evidence required for an override?
- Why are repeated overrides treated as important signals?

---

## 19. Review and maintenance

This playbook must be reviewed at least annually or earlier when major changes occur in:

- replenishment operating model
- override governance rules
- approval authority structure
- system recommendation logic
- supplier-risk operating patterns
- audit or compliance expectations

All updates must be version-controlled and approved by the responsible business owner.

---

## 20. Final playbook statement

NorthStar Retail & Distribution will manage planner overrides through an evidence-based, controlled, and auditable process. Overrides are a valid part of enterprise decision-making when supported by business reality, but they must always remain traceable, governed, and aligned with service, inventory, and operational risk objectives within EDIP.