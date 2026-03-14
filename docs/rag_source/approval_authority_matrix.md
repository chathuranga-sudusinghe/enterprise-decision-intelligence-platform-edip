# Approval Authority Matrix
## NorthStar Retail & Distribution
## File: docs/rag_source/approval_authority_matrix.md

---

document_id: DOC-NRD-GOV-002  
document_title: Approval Authority Matrix  
document_type: governance  
department: enterprise_decision_governance  
business_domain: approval_authority  
region_scope: enterprise  
audience: inventory_planners_demand_planners_supply_chain_managers_procurement_leadership_commercial_leadership_operations_managers_executive_review  
effective_date: 2025-01-01  
review_date: 2025-12-31  
version: 1.0  
owner_role: Chief Operations Officer  
confidentiality_level: internal  
tags: approval_authority, governance, decision_rights, escalation, override_approval, replenishment_control, exception_handling, auditability  
source_system: edip_phase_5_docs  
company_name: NorthStar Retail & Distribution  

---

## 1. Purpose

This document defines the formal approval authority structure for NorthStar Retail & Distribution (NRD).

Its purpose is to clarify which roles may approve, reject, escalate, or review different types of planning, inventory, supplier, pricing, promotional, and exception-based decisions. This document supports EDIP by creating a clear decision-rights framework so that material business actions remain governed, traceable, and aligned with enterprise control standards.

---

## 2. Document objectives

The objectives of this document are to:

- define who can approve which decision types
- prevent decisions from being made outside authority
- reduce ambiguity during exception handling
- support consistent escalation paths
- improve auditability of business decisions
- support grounded RAG explanations about approval ownership
- strengthen governance quality inside EDIP

---

## 3. Scope

This document applies to:

- replenishment decision approvals
- planner override approvals
- forecast exception escalation
- regional inventory-risk escalation
- supplier-risk response approvals
- promotion and pricing-related approval boundaries
- executive exception cases
- decision logging and traceability expectations linked to approvals

This document does not apply to:

- payroll or HR approval chains
- legal-signature authority outside planning and operations governance
- pure IT release approvals
- informal working discussions that do not create a material business decision

---

## 4. Core approval principles

### 4.1 Authority must be explicit
A material business decision must be approved by a role with defined authority.

### 4.2 Approval must match risk
The higher the business exposure, the higher the approval level should normally be.

### 4.3 Local authority should be used when appropriate
Not every case needs senior approval. Routine decisions should remain at the lowest safe authority level.

### 4.4 Escalation is required when authority is exceeded
If a decision exceeds local approval rights, it must be escalated rather than forced through.

### 4.5 Cross-functional cases may require joint review
Some cases need more than one function to review before final approval is valid.

### 4.6 Approval must be traceable
Every material approval must be identifiable in the decision record.

---

## 5. Definitions

### 5.1 Approval authority
The formal right of a role to approve, reject, modify, or escalate a defined business decision.

### 5.2 Decision owner
The primary role responsible for preparing or proposing the decision.

### 5.3 Approver
The role with authority to authorize the action.

### 5.4 Reviewer
A supporting role that provides input but does not hold final approval authority unless separately assigned.

### 5.5 Escalation
The formal routing of a case to a higher level of authority when the current role cannot safely approve it.

### 5.6 Joint approval
A case where more than one function must review or approve before action is valid.

### 5.7 Material decision
A decision with meaningful service, inventory, financial, operational, or governance impact.

---

## 6. Approval role tiers

The standard approval tiers used in NorthStar planning governance are:

### 6.1 Tier 1 — Planner / Analyst operating authority
Used for routine, low-risk decisions within approved rules.

Typical roles:
- Demand Planner
- Inventory Planner
- Inventory Analyst where explicitly authorized

### 6.2 Tier 2 — Functional manager authority
Used for medium-risk, exception, or approval-required decisions beyond standard planner scope.

Typical roles:
- Supply Chain Planning Manager
- Warehouse Operations Manager
- Procurement Manager
- Commercial / Pricing Manager
- Regional Operations Manager

### 6.3 Tier 3 — Department leadership authority
Used for high-impact, cross-functional, or broader business-risk decisions.

Typical roles:
- Director of Supply Chain Planning
- Director of Procurement
- Director of Commercial Strategy
- Director of Commercial Operations
- Regional Operations Director

### 6.4 Tier 4 — Executive authority
Used for enterprise-significant exceptions, major trade-offs, or unusually high exposure.

Typical roles:
- Chief Operations Officer
- Executive Review Sponsor
- Other authorized executive leaders where applicable

---

## 7. General decision-rights framework

### 7.1 Tier 1 authority is limited to governed local actions
Tier 1 roles may act only when the case is within policy, within risk tolerance, and within the role’s defined operating scope.

### 7.2 Tier 2 authority handles managed exceptions
Tier 2 roles may approve more sensitive decisions when policy allows and the case does not exceed managerial authority.

### 7.3 Tier 3 authority handles major cross-functional or high-risk cases
Tier 3 roles are expected to review decisions with broader regional, financial, or strategic impact.

### 7.4 Tier 4 authority handles enterprise exceptions
Tier 4 authority is required when local or departmental authority is not sufficient to manage the exposure safely.

---

## 8. Approval matrix by decision type

## 8.1 Forecast review outcome

### Accept forecast
Decision owner:
- Demand Planner

Approver:
- Demand Planner within normal review authority

Reviewer:
- Inventory Planner where needed

Escalate when:
- critical SKU exposure is high
- repeated high-impact forecast exceptions exist
- local review confidence is insufficient

### Adjust forecast
Decision owner:
- Demand Planner

Approver:
- Demand Planner for low-risk governed adjustments
- Supply Chain Planning Manager for higher-impact adjustments

Reviewer:
- Commercial / Pricing Partner
- Inventory Planner

Escalate when:
- major regional or enterprise exposure exists
- commercial and planning interpretation conflict
- the adjustment has material downstream risk

### Escalate forecast case
Decision owner:
- Demand Planner

Approver:
- Supply Chain Planning Manager or Director of Supply Chain Planning depending on impact

Reviewer:
- Commercial / Pricing Partner
- Inventory Planner
- Executive Review Sponsor if required

---

## 8.2 Replenishment decision outcome

### Standard replenishment
Decision owner:
- Inventory Planner

Approver:
- Inventory Planner within governed local authority

Reviewer:
- Inventory Analyst where needed

Escalate when:
- critical SKU exposure is high
- supplier recovery is unreliable
- business impact exceeds local tolerance

### Priority replenishment
Decision owner:
- Inventory Planner

Approver:
- Inventory Planner for lower-impact priority cases
- Supply Chain Planning Manager for higher-risk cases

Reviewer:
- Procurement Partner
- Warehouse / Operations Partner where needed

Escalate when:
- multi-region effect exists
- service exposure becomes unusually high
- execution constraints block safe action

### Urgent replenishment
Decision owner:
- Inventory Planner

Approver:
- Supply Chain Planning Manager
- Director of Supply Chain Planning for broader or higher-risk cases

Reviewer:
- Procurement Partner
- Warehouse / Operations Partner
- Regional Planning Lead if locally sensitive

Escalate when:
- enterprise-significant service exposure exists
- non-standard recovery action is required
- financial or operational risk exceeds departmental authority

### No action / monitor
Decision owner:
- Inventory Planner

Approver:
- Inventory Planner within normal authority

Reviewer:
- Inventory Analyst
- Demand Planner where forecast interpretation is sensitive

Escalate when:
- inaction may create hidden major exposure
- uncertainty is too high for local comfort

---

## 8.3 Planner override approval

### Local material override
Decision owner:
- Inventory Planner

Approver:
- Inventory Planner if clearly within local authority and risk tolerance

Reviewer:
- Inventory Analyst
- Procurement Partner or Warehouse / Operations Partner where relevant

Escalate when:
- override changes major quantity, urgency, or regional priority
- evidence is incomplete but risk is high
- authority boundary is unclear

### High-impact override
Decision owner:
- Inventory Planner

Approver:
- Supply Chain Planning Manager
- Director of Supply Chain Planning for broader or more sensitive cases

Reviewer:
- Procurement Manager
- Regional Planning Lead
- Commercial / Pricing Partner if campaign-related

Escalate when:
- override affects multiple regions
- financial or service impact is unusually high
- cross-functional conflict exists

### Escalated override
Decision owner:
- Supply Chain Planning Manager

Approver:
- Director of Supply Chain Planning
- Chief Operations Officer if enterprise impact is material

Reviewer:
- Executive Review Sponsor where required

---

## 8.4 Regional inventory-risk review

### Stable / monitor regional case
Decision owner:
- Regional Planning Lead
- Inventory Planner

Approver:
- Regional Planning Lead within defined scope
- Supply Chain Planning Manager where needed

Reviewer:
- Inventory Analyst

Escalate when:
- risk trends worsen rapidly
- allocation conflict emerges
- service exposure becomes material

### Priority regional case
Decision owner:
- Regional Planning Lead

Approver:
- Supply Chain Planning Manager
- Regional Operations Manager where execution support is required

Reviewer:
- Procurement Partner
- Warehouse / Operations Partner

Escalate when:
- region cannot be protected within standard controls
- another region must give up protection
- cross-functional intervention is required

### Urgent / allocation regional case
Decision owner:
- Regional Planning Lead

Approver:
- Director of Supply Chain Planning
- Regional Operations Director
- Chief Operations Officer for enterprise-significant trade-offs

Reviewer:
- Executive Review Sponsor where needed

---

## 8.5 Supplier-risk response

### Standard supplier issue interpretation
Decision owner:
- Procurement Partner

Approver:
- Procurement Manager for supplier-side action
- Inventory Planner for planning response

Reviewer:
- Warehouse / Operations Partner if receiving issues exist

Escalate when:
- supplier failure creates major service exposure
- local supplier action is insufficient
- cross-functional recovery is needed

### Major supplier failure response
Decision owner:
- Procurement Manager

Approver:
- Director of Procurement
- Director of Supply Chain Planning for planning-impact actions

Reviewer:
- Supply Chain Planning Manager
- Warehouse Operations Manager

Escalate when:
- supplier disruption is enterprise significant
- recovery requires executive trade-off approval

---

## 8.6 Promotion and pricing approval

### Standard promotion launch
Decision owner:
- Category Manager
- Commercial Analyst for supporting review

Approver:
- Pricing Manager for pricing structure
- Commercial Operations Manager for execution control

Reviewer:
- Inventory Planner
- Supply Chain Manager

Escalate when:
- stock readiness is weak
- discount depth is unusually high
- campaign risk is broader than routine

### Campaign extension
Decision owner:
- Category Manager

Approver:
- Commercial Operations Manager
- Pricing Manager
- Supply Chain Planning Manager if inventory risk is meaningful

Reviewer:
- Inventory Planner
- Commercial Analyst

Escalate when:
- extension creates service-level risk
- major financial or supply concerns exist

### High-risk pricing or promotion conflict
Decision owner:
- Commercial / Pricing Manager

Approver:
- Director of Commercial Strategy
- Director of Supply Chain Planning where planning impact is material

Reviewer:
- Executive Review Sponsor if cross-functional conflict is severe

Escalate when:
- commercial goals conflict with operational feasibility
- enterprise exposure becomes material

---

## 8.7 Executive exception case

### Enterprise exception
Decision owner:
- Supply Chain Planning Manager, Director, or other initiating business leader depending on case origin

Approver:
- Chief Operations Officer
- Executive Review Sponsor or equivalent executive authority

Reviewer:
- Director of Supply Chain Planning
- Director of Procurement
- Director of Commercial Strategy
- Regional Operations Director
- Other functions as relevant

This level is required when:
- service exposure is enterprise significant
- financial risk is unusually high
- cross-region trade-offs are material
- local and departmental authority are insufficient

---

## 9. Approval rules by business risk level

### 9.1 Low-risk decision
Typical approval level:
- Tier 1

Characteristics:
- routine
- reversible
- within standard policy
- limited local impact

### 9.2 Medium-risk decision
Typical approval level:
- Tier 2

Characteristics:
- exception-based
- some service or inventory sensitivity
- moderate regional or operational effect
- may require supporting review

### 9.3 High-risk decision
Typical approval level:
- Tier 3

Characteristics:
- high-value or critical SKU exposure
- broader cross-functional impact
- multiple regions or channels affected
- elevated financial or service risk

### 9.4 Enterprise-significant decision
Typical approval level:
- Tier 4

Characteristics:
- major service risk
- executive trade-offs required
- unusually high financial or brand exposure
- enterprise-wide consequences possible

---

## 10. Joint-approval situations

Joint approval may be required when:

- pricing and planning implications are both material
- supplier and operational recovery both affect the decision
- commercial campaign continuation depends on inventory and service readiness
- cross-region allocation affects multiple business priorities
- an override changes both planning logic and commercial exposure

Typical joint-approval pairs may include:
- Pricing Manager + Supply Chain Planning Manager
- Director of Commercial Strategy + Director of Supply Chain Planning
- Director of Procurement + Director of Supply Chain Planning
- Regional Operations Director + Director of Supply Chain Planning

Joint approval must still identify one final accountable decision record.

---

## 11. Escalation rules

### 11.1 Escalate when authority is exceeded
No role should approve a case outside its defined authority.

### 11.2 Escalate when evidence is incomplete but risk is high
A risky decision with weak evidence should move upward, not be forced through locally.

### 11.3 Escalate when cross-functional conflict cannot be resolved locally
Conflicting priorities between planning, procurement, commercial, and operations must be escalated when local alignment fails.

### 11.4 Escalate when enterprise trade-offs are required
A decision that protects one area while materially harming another must be escalated if trade-offs exceed local authority.

---

## 12. Logging requirements for approvals

Every material approval must be reflected in the approved decision log.

### 12.1 Minimum logging fields
A valid approval record should include:

- decision identifier
- decision type
- decision owner
- approver role
- approver name or user reference
- approval timestamp
- approval outcome
- escalation flag where applicable
- supporting reviewer roles where relevant
- final status

### 12.2 Logging quality standard
The record must show clearly who approved the case and under what authority level.

### 12.3 Approval visibility rule
Approvals must not be implied or assumed. They must be visible in the record.

---

## 13. Non-compliant approval behavior

The following are not compliant:

- approving outside defined authority
- acting without required approval
- using verbal or informal approval without traceable record
- skipping joint review where policy requires it
- forcing local approval for enterprise-significant cases
- failing to log final approver identity

These behaviors weaken governance and auditability.

---

## 14. Common approval scenarios

### 14.1 Routine local replenishment case
The Inventory Planner approves standard replenishment within normal authority. This is compliant.

### 14.2 High-impact override case
The Inventory Planner proposes a major override. The Supply Chain Planning Manager reviews and approves within manager authority. This is compliant when logged.

### 14.3 Promotion extension with stock pressure
The commercial team wants an extension, but stock is tightening. Joint review by Commercial Operations Manager, Pricing Manager, and Supply Chain Planning Manager is required.

### 14.4 Cross-region allocation conflict
A limited stock pool must be split between West and Central. The case moves to departmental or executive approval depending on exposure.

### 14.5 Executive exception case
A major supplier failure creates enterprise service risk. The case is escalated to executive authority. This is compliant and necessary.

---

## 15. Roles and responsibilities

### 15.1 Decision owner
- prepare the decision case
- gather required evidence
- identify whether approval is needed
- route the case correctly
- ensure the final record is complete

### 15.2 Approver
- review the case within authority
- approve, reject, modify, or escalate
- ensure the decision is policy-compliant
- maintain approval traceability

### 15.3 Reviewer
- provide relevant input
- strengthen decision quality
- not claim final approval if not authorized

### 15.4 Manager / Director / Executive approvers
- apply risk-based judgment
- protect enterprise control
- ensure escalation is used correctly
- support cross-functional resolution when needed

### 15.5 EDIP Decision Support Layer
- surface authority-aware workflows
- preserve decision ownership and approval traceability
- support audit-friendly decision flow
- not replace human approval authority

---

## 16. Example RAG questions supported by this document

This document should help EDIP answer questions such as:

- Who was allowed to approve this decision?
- Why did this case require manager approval?
- Why was this decision escalated instead of approved locally?
- Why did multiple teams need to approve this promotion extension?
- Who owns the decision and who only reviews it?
- Why is approver identity required in the decision log?

---

## 17. Related documents

This document should be used together with:

- Planning Team Roles and Responsibilities
- Planner Override Governance Policy
- Planner Override Playbook
- Executive Exception Escalation Policy
- Replenishment Decision Playbook
- Forecast Review Checklist
- Promotion Execution Policy
- Audit Logging and Decision Trace Policy

---

## 18. Review and maintenance

This document must be reviewed at least annually or earlier when major changes occur in:

- authority structure
- planning governance
- escalation model
- executive review process
- audit requirements
- EDIP workflow controls

All updates must be version-controlled and approved by the responsible business owner.

---

## 19. Final governance statement

NorthStar Retail & Distribution will manage approvals through a clear, risk-aware, authority-based, and traceable governance framework. Approval rights within EDIP must remain explicit, documented, and aligned with business exposure so that routine decisions stay efficient, while high-risk and enterprise-significant decisions receive the correct level of control.