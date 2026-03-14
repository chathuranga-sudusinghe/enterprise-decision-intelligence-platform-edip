# Planner Override Governance Policy
## NorthStar Retail & Distribution
## File: docs/policies/planner_override_governance_policy.md

---

document_id: DOC-NRD-POL-005  
document_title: Planner Override Governance Policy  
document_type: policy  
department: supply_chain_planning_governance  
business_domain: planner_override_governance  
region_scope: enterprise  
audience: inventory_planners_supply_chain_managers_inventory_analysts_procurement_leadership_operations_governance_executive_review  
effective_date: 2025-01-01  
review_date: 2025-12-31  
version: 1.0  
owner_role: Director of Supply Chain Planning  
confidentiality_level: internal  
tags: planner_override, governance, decision_control, replenishment, exception_handling, auditability, decision_log, escalation  
source_system: edip_phase_5_docs  
company_name: NorthStar Retail & Distribution  

---

## 1. Purpose

This policy defines the governance rules for planner overrides at NorthStar Retail & Distribution (NRD).

Its purpose is to ensure that planner overrides are controlled, justified, traceable, and aligned with enterprise decision standards. This policy supports EDIP by establishing the formal governance boundary between system-generated recommendations and human intervention, so that override activity remains explainable, auditable, and operationally disciplined.

---

## 2. Policy objectives

The objectives of this policy are to:

- define formal governance rules for planner overrides
- ensure overrides are used only when justified by business evidence
- prevent weak, excessive, or undocumented human intervention
- protect service level, inventory balance, and decision quality
- maintain clear accountability for override decisions
- support audit-ready decision traceability within EDIP
- create governance signals from repeated override patterns

---

## 3. Scope

This policy applies to:

- planner changes to system-generated replenishment recommendations
- planner changes to urgency, priority, quantity, timing, or status
- business overrides linked to supplier, forecast, inventory, operational, or commercial context
- override decisions that affect material planning outcomes
- override logging, review, escalation, and governance monitoring

This policy does not apply to:

- standard recommendations accepted without change
- technical correction of software defects
- master-data fixes that do not involve override decisioning
- executive-only decisions outside planner authority
- informal discussion not resulting in a material decision change

---

## 4. Governance principles

### 4.1 System recommendations are the controlled baseline
System recommendations are the default governed starting point for planning decisions.

### 4.2 Human intervention is allowed, but not casual
A planner may override the system only when a valid business reason exists and the case is supported by evidence.

### 4.3 Overrides must improve decision quality
Overrides must be used to correct, strengthen, or contextualize decisions, not to bypass governance.

### 4.4 Traceability is mandatory
Every material override must be recorded clearly enough for another reviewer, manager, or auditor to understand what changed and why.

### 4.5 Authority matters
Not every override can be made by every planner. Authority level must be respected.

### 4.6 Repetition is a governance signal
Repeated overrides on the same pattern may indicate deeper issues requiring model review, policy refinement, data correction, or supplier review.

---

## 5. Definitions

### 5.1 Planner override
A planner-initiated change to a system-generated recommendation.

### 5.2 Material override
An override that changes the business meaning or action path of a recommendation in a significant way.

### 5.3 Override governance
The formal control framework that determines when, how, and by whom override activity may occur.

### 5.4 Override reason
The documented business explanation for why the planner changed the recommendation.

### 5.5 Approval authority
The approved level of decision ownership allowed to make or approve an override.

### 5.6 Escalated override
An override that exceeds normal planner authority or has wider business exposure.

### 5.7 Override review
The process of checking whether override behavior remains valid, controlled, and policy-compliant.

---

## 6. What qualifies as a material override

A planner action should be treated as a material override when it changes one or more of the following:

- replenishment quantity
- urgency level
- priority classification
- timing of action
- recommendation status
- escalation path
- decision outcome with meaningful business impact

Material overrides must follow full governance requirements.

---

## 7. Valid override conditions

An override may be permitted when one or more of the following apply:

- verified supplier disruption affects recovery confidence
- forecast output is materially distorted by a known temporary event
- promotion timing changes the practical demand picture
- warehouse or operational constraints affect feasible execution
- regional allocation conditions require non-standard treatment
- critical SKU or service exposure is not fully captured by standard logic
- verified master-data issue materially affects the recommendation
- approved commercial or executive instruction changes the decision context
- urgent business event requires controlled local intervention

An override is permitted only when the evidence is strong enough to justify changing the governed baseline.

---

## 8. Invalid override conditions

An override is not policy-compliant when:

- it is based only on intuition or habit
- the planner cannot explain the logic clearly
- there is no supporting business evidence
- the override is used to avoid normal review discipline
- the planner is acting outside authority
- the action hides a process issue instead of addressing it
- the case should have been escalated instead

Invalid override behavior weakens trust in both the system and the planning process.

---

## 9. Override authority rules

### 9.1 Standard planner authority
A planner may apply overrides only within their approved scope of authority.

### 9.2 Higher-risk override handling
Overrides involving larger business exposure, broader geographic scope, or critical items may require manager approval.

### 9.3 Escalated override requirement
If the override exceeds planner authority, the case must be escalated rather than forced through local decision-making.

### 9.4 Temporary urgent action
Where urgent action is required to protect service, a temporary override may be applied if policy allows, but it must still be logged and reviewed according to governance.

---

## 10. Standard override governance workflow

### 10.1 Step 1 — Review the original recommendation
The planner must first understand the system recommendation and its main drivers.

### 10.2 Step 2 — Identify the business reason for change
The planner must define what makes the standard recommendation insufficient, risky, or incomplete.

### 10.3 Step 3 — Gather supporting evidence
The planner must collect evidence relevant to the decision, such as supplier update, demand review, inventory signal, operational alert, or approved commercial information.

### 10.4 Step 4 — Check authority level
The planner must determine whether the override can be made locally or must be escalated.

### 10.5 Step 5 — Apply or escalate the override
If within authority and supported by evidence, the planner may apply the override. Otherwise, the case must be escalated.

### 10.6 Step 6 — Log the override
Every material override must be recorded in the approved decision process.

### 10.7 Step 7 — Review override quality
Override activity should be reviewed periodically for governance quality, repeat patterns, and policy compliance.

---

## 11. Evidence standards

### 11.1 Minimum evidence expectation
Every material override must have at least one clear business evidence source, such as:

- confirmed supplier update
- forecast review finding
- inventory coverage signal
- safety stock breach risk
- warehouse or receiving issue
- promotion or price event
- verified master-data issue
- approved leadership direction

### 11.2 Stronger evidence for higher-impact overrides
Larger or riskier overrides require stronger evidence and, where appropriate, broader review.

### 11.3 Unsupported override prohibition
If the planner cannot provide defensible evidence, the override should not be made.

---

## 12. Override reason standards

### 12.1 Reason must be specific
The override reason must describe what changed and why.

### 12.2 Reason must be business-based
Reason text must reflect business context, not vague preference.

### 12.3 Reason must be auditable
Another reviewer should be able to understand the decision logic from the recorded reason.

### 12.4 Weak reason examples
The following are not acceptable as complete reasons:

- “planner choice”
- “felt too high”
- “adjusted”
- “not correct”
- “changed urgently”

### 12.5 Strong reason examples
Better examples include:

- “Urgency increased due to confirmed supplier delay and critical SKU coverage below target.”
- “Quantity reduced due to verified warehouse intake constraint and excess inbound already scheduled.”
- “Recommendation delayed pending correction of incorrect lead-time master data.”

---

## 13. Logging requirements

Every material override must be logged in the approved decision process.

### 13.1 Minimum required fields
A valid override log should include:

- override identifier
- recommendation identifier
- SKU or grouping identifier
- region or location
- original recommendation
- overridden recommendation
- override category
- override reason
- evidence summary
- planner identity
- timestamp
- approval or escalation reference where applicable
- final decision status

### 13.2 Logging quality standard
The override record must be specific enough that another planner, manager, or auditor can understand the decision without asking for missing context.

### 13.3 Late logging prohibition
Material overrides must not be left undocumented or logged long after the event without clear cause.

---

## 14. Approval and escalation rules

### 14.1 Approval-required override cases
Additional approval may be required when:

- the override affects critical SKUs
- business exposure is unusually high
- quantity change is large
- multiple regions are affected
- service-level risk is significant
- financial risk is elevated

### 14.2 Escalation triggers
An override must be escalated when:

- planner authority is exceeded
- cross-functional coordination is required
- local evidence is incomplete but risk is high
- the override may create enterprise-level service exposure
- the decision conflicts with commercial or executive direction
- the case requires non-standard action beyond local control

### 14.3 Governance over speed
Speed does not remove the need for approval or escalation discipline.

---

## 15. Override monitoring and review

Override activity should be reviewed as part of governance control.

### 15.1 Review themes
Governance review should check for:

- repeated overrides by SKU
- repeated overrides by supplier
- repeated overrides by planner
- frequent urgency increases
- frequent quantity reductions
- common override categories
- escalation frequency
- override quality and completeness

### 15.2 Governance meaning of patterns
Patterns may indicate:

- weak recommendation logic
- missing business rules
- unstable supplier conditions
- training gaps
- weak data quality
- poor local discipline

### 15.3 Corrective response
Where override quality or frequency becomes concerning, management should consider:

- additional planner coaching
- policy clarification
- model or rule review
- data remediation
- supplier review
- tighter approval control

---

## 16. Compliance requirements

Override activity is considered compliant when:

- the override has a valid business reason
- evidence supports the action
- the planner acts within authority
- logging is complete and timely
- escalation is used where required
- the override remains aligned with policy and enterprise objectives

Non-compliance includes:

- undocumented overrides
- unsupported overrides
- override behavior outside authority
- vague or weak reason logging
- repeated habit-based override patterns
- bypassing escalation when required

---

## 17. Roles and responsibilities

### 17.1 Inventory Planner
- review the system recommendation
- determine whether override is justified
- gather evidence
- act within authority
- log the override correctly
- escalate when needed

### 17.2 Inventory Analyst
- support evidence gathering
- analyze override trends
- help identify repeated pattern risk

### 17.3 Supply Chain Manager
- review high-impact or escalated overrides
- ensure governance compliance
- support corrective action where override patterns are weak

### 17.4 Procurement Team
- provide supplier-related context relevant to override decisions

### 17.5 Operations / Warehouse Team
- provide execution and capacity context where relevant to the override

### 17.6 Governance / Audit Review
- monitor override control quality
- review compliance and traceability
- support control improvement recommendations

### 17.7 EDIP Decision Support Layer
- preserve original recommendation state
- support override logging and explanation
- surface override pattern visibility
- not replace human accountability for governance

---

## 18. Common governance scenarios

### 18.1 Valid local override
The planner changes urgency based on confirmed supplier delay and low coverage. The override is within authority and properly logged. This is compliant.

### 18.2 Escalation-required override
The planner wants to change allocation across multiple regions. This exceeds local authority and must be escalated.

### 18.3 Weak override attempt
The planner wants to reduce urgency because the system result feels aggressive, but no evidence exists. This is not compliant.

### 18.4 Repeated pattern concern
The same SKU is overridden repeatedly for the same reason. Governance review should check whether a deeper system or policy issue exists.

### 18.5 Late documentation issue
The planner made a material override but did not log it on time. This weakens traceability and is not compliant.

---

## 19. Example RAG questions supported by this policy

This document should help EDIP answer questions such as:

- Why was the planner allowed to override this recommendation?
- Why did this override require approval?
- Why was this case escalated instead of changed locally?
- Why is evidence required for a planner override?
- Why are repeated overrides treated as governance signals?
- Why is late override logging a problem?

---

## 20. Related documents

This policy should be used together with:

- Planner Override Playbook
- Inventory Replenishment Policy Manual
- Executive Exception Escalation Policy
- Replenishment Decision Playbook
- Forecast Review Checklist
- Audit Logging and Decision Trace Policy
- Approval Authority Matrix

---

## 21. Review and maintenance

This policy must be reviewed at least annually or earlier when major changes occur in:

- override operating model
- approval authority structure
- audit or compliance expectations
- EDIP recommendation logic
- supplier risk environment
- planning governance requirements

All updates must be version-controlled and approved by the responsible business owner.

---

## 22. Final policy statement

NorthStar Retail & Distribution will govern planner overrides through a controlled, evidence-based, authority-aware, and auditable policy framework. Override activity within EDIP must remain justified, traceable, and aligned with enterprise decision discipline so that human intervention improves decision quality without weakening governance.