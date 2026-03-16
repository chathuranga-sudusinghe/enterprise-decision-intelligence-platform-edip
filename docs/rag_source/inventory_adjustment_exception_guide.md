---
document_id: "DOC-NRD-GDE-006"
document_title: "Inventory Adjustment Exception Guide"
document_type: "guide"
department: "inventory_control"
business_domain: "inventory"
region_scope: "enterprise"
audience: "cross_functional"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Director, Inventory Integrity and Store Operations"
confidentiality_level: "internal"
tags:
  - inventory_adjustment
  - inventory_discrepancy
  - exception_classification
  - store_adjustment
  - warehouse_adjustment
  - root_cause_investigation
  - planner_follow_up
  - audit_support
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
source_path: "docs/rag_source/inventory_adjustment_exception_guide.md"
---

# Inventory Adjustment Exception Guide
## NorthStar Retail & Distribution (NRD)
## EDIP / Phase 5 RAG Knowledge Layer
## File: docs/rag_source/inventory_adjustment_exception_guide.md

## 1. Purpose

This guide defines the standard approach for identifying, communicating, reviewing, and resolving inventory adjustment exceptions at NorthStar Retail & Distribution (NRD).

Its purpose is to ensure that inventory adjustments are handled in a controlled, traceable, and business-relevant way, especially when the adjustment indicates an unusual operational issue, data integrity problem, process breakdown, or possible financial exposure.

This guide supports the Enterprise Decision Intelligence Platform (EDIP) by providing governed knowledge for:

- inventory discrepancy review
- exception classification
- store and warehouse adjustment analysis
- root-cause investigation support
- planner and operations follow-up
- audit-aware decision support

---

## 2. Scope

This guide applies to inventory adjustment exceptions across:

- stores
- warehouses
- transit-related inventory control points
- returns handling processes
- damaged stock workflows
- cycle count reconciliation activities
- stock correction events
- shrink-related investigations
- system-to-physical inventory mismatch review

This document applies to teams such as:

- inventory control
- store operations
- warehouse operations
- finance control
- supply chain planning
- audit and governance
- loss prevention where relevant
- data and analytics support

---

## 3. Definition of Inventory Adjustment Exception

An inventory adjustment exception is any stock adjustment event that falls outside normal controlled operating expectations and therefore requires review, explanation, or escalation.

Examples include:

- unusually large positive or negative adjustment
- repeated adjustments for the same SKU or location
- adjustments without clear operational reason
- mismatch between physical count and system record beyond tolerance
- damage-related write-off spike
- receiving correction inconsistent with shipment evidence
- adjustment pattern suggesting process failure or control weakness

An inventory adjustment exception is not just a number change.  
It is a potential signal of business, operational, or control risk.

---

## 4. Core Principles

All inventory adjustment exceptions must be managed using the following principles.

### 4.1 Accuracy first
The business must confirm the facts before concluding why the adjustment occurred.

### 4.2 Operational context matters
The same adjustment may have different meaning depending on item value, location type, trading period, and recent activity.

### 4.3 Traceability is required
Material adjustments must be traceable to a source event, reason, owner, and timestamp.

### 4.4 Root cause over surface correction
Teams should not only correct the number. They should also determine why the exception happened.

### 4.5 Business impact focus
Review should consider service risk, financial exposure, shrink risk, and planning impact.

### 4.6 Controlled escalation
Escalation should be based on materiality, repetition, or control risk.

---

## 5. Typical Causes of Inventory Adjustment Exceptions

Inventory adjustment exceptions may arise from:

- receiving errors
- put-away errors
- shelf-to-system mismatch
- unrecorded damage
- returns processing errors
- transfer booking errors
- picking errors
- counting mistakes
- barcode or item master issues
- timing mismatch between physical movement and system update
- process non-compliance
- theft or unexplained loss
- manual correction without adequate justification

The guide should be used to review the actual evidence before assigning cause.

---

## 6. Common Exception Categories

### 6.1 Count variance exception
Physical count differs from expected system balance beyond approved tolerance.

### 6.2 Repeated adjustment exception
The same SKU, store, warehouse, or process area shows repeated adjustments within a review period.

### 6.3 Large value adjustment exception
The quantity or financial value of the adjustment is materially high.

### 6.4 Damage write-off exception
Damage-related adjustment exceeds normal pattern or approved expectation.

### 6.5 Receiving correction exception
Adjustment occurs after receiving due to mismatch, shortage, overage, or processing issue.

### 6.6 Transfer reconciliation exception
Stock sent, received, or booked in transfer flow does not reconcile correctly.

### 6.7 Return-related adjustment exception
Returned stock creates unusual inventory correction or mismatch.

### 6.8 Unexplained shrink exception
Negative adjustment exists without sufficiently supported operational cause.

### 6.9 Master data or system mapping exception
Adjustment appears linked to item setup issue, barcode mismatch, unit-of-measure problem, or other system mapping concern.

---

## 7. Exception Trigger Conditions

An inventory adjustment should be treated as an exception when one or more of the following apply:

- value exceeds local review threshold
- quantity exceeds reasonableness threshold
- repeated correction for same SKU/location is observed
- no valid reason code exists
- physical evidence conflicts with system event history
- adjustment affects service-critical or high-value item
- financial control concern is raised
- adjustment occurs during promotion or peak trading period
- process owner cannot explain the event clearly
- issue indicates possible systemic weakness

---

## 8. Required Review Fields

Every material inventory adjustment exception review should capture, where available:

- adjustment ID
- date and time
- store ID / warehouse ID
- SKU / item ID
- item description
- adjustment quantity
- unit cost or value impact
- adjustment direction (positive / negative)
- reason code
- source process
- user or system actor
- related shipment, transfer, count, or return reference
- approval status if required
- investigation note
- final resolution

---

## 9. Review Workflow

The standard inventory adjustment exception workflow should follow this sequence:

1. detect the adjustment exception
2. validate the basic transaction facts
3. confirm physical and system context
4. classify the exception type
5. assess business impact and materiality
6. assign review owner
7. investigate likely root cause
8. decide correction, escalation, or monitoring action
9. document resolution and lessons if needed

The workflow should focus on both immediate correction and control improvement.

---

## 10. Exception Severity Levels

### Level 1 — Local review
Small or isolated exception that can be handled by local store, warehouse, or inventory control owner.

Examples:
- minor count mismatch
- isolated damage correction with clear evidence
- one-time receiving correction with confirmed documentation

### Level 2 — Managed exception
Issue needs broader review because of higher value, repeat pattern, or planning relevance.

Examples:
- repeated adjustments on same SKU
- moderate unexplained negative adjustment
- recurring receiving mismatch
- adjustment affecting important item availability

### Level 3 — Cross-functional exception
Issue needs coordination between inventory control, operations, finance, planning, or warehouse teams.

Examples:
- repeated regional mismatch pattern
- large transfer reconciliation issue
- material write-off spike
- process breakdown affecting multiple locations

### Level 4 — Governance or executive exception
Issue indicates serious control weakness, high financial exposure, or unusual business risk.

Examples:
- major unexplained shrink event
- repeated unsupported manual adjustments
- large-value discrepancy with unclear ownership
- issue requiring audit, finance, or executive attention

---

## 11. Business Impact Assessment

Inventory adjustment exceptions should be reviewed for impact across the following areas:

### 11.1 Service impact
Does the issue reduce actual product availability or distort replenishment planning?

### 11.2 Financial impact
Does the adjustment create meaningful write-off, valuation, margin, or control risk?

### 11.3 Operational impact
Does the issue indicate a process breakdown in receiving, counting, transfer, returns, or shelf execution?

### 11.4 Planning impact
Does the incorrect inventory position affect forecast interpretation, replenishment recommendation, or override behavior?

### 11.5 Governance impact
Does the issue require stronger review, policy attention, or audit follow-up?

---

## 12. Investigation Guidance by Scenario

### 12.1 Count variance
Check:
- latest cycle count record
- last movement history
- recent sales or picks
- recent receiving or transfer events
- item location accuracy
- count method quality

### 12.2 Receiving correction
Check:
- purchase order reference
- ASN or shipment record if available
- received quantity evidence
- put-away timing
- discrepancy note from receiving team
- supplier-related pattern

### 12.3 Damage write-off
Check:
- damage category
- date of identification
- handling or storage issue
- repeat pattern by location or supplier
- approval evidence for write-off

### 12.4 Transfer mismatch
Check:
- transfer dispatch record
- transfer receipt confirmation
- in-transit timing
- quantity mismatch details
- booking or scanning gap

### 12.5 Unexplained shrink
Check:
- repeated loss history
- high-risk item status
- store or warehouse control environment
- timing of negative adjustments
- physical verification evidence
- need for loss prevention escalation

---

## 13. Communication Standards

When communicating an inventory adjustment exception, the message should include:

- what happened
- where it happened
- item or item group affected
- quantity and value relevance
- why it is considered an exception
- immediate risk
- action or review needed
- owner and timing

Avoid vague messages such as:
- “inventory issue found”
- “numbers do not match”
- “please check stock urgently”

Good communication must be specific and actionable.

---

## 14. Approval and Escalation Guidance

Some inventory adjustments require only local documentation. Others require approval or escalation.

Escalation should be considered when:

- the financial value is material
- the issue repeats with no clear resolution
- planning or availability is being distorted
- multiple locations are affected
- reason codes are weak or missing
- the issue suggests fraud, shrink, or control weakness
- the issue requires finance or governance review

Approval may be required for:
- large write-offs
- major correction entries
- sensitive stock categories
- repeated manual adjustments
- unusual end-of-period correction events

---

## 15. Link to EDIP Decisioning

Inventory adjustment exceptions matter to EDIP because poor stock accuracy can distort:

- demand interpretation
- replenishment recommendations
- transfer suggestions
- regional risk scoring
- planner override behavior
- promotion readiness evaluation

For this reason, material adjustment exceptions should be visible to the relevant planning and control functions when they can change downstream decisions.

---

## 16. Data Quality Expectations

Exception records should meet the following standards:

- valid SKU and location reference
- non-null timestamp
- valid reason code or approved justification
- no duplicate adjustment event record at business grain
- clear adjustment direction
- consistent quantity and value mapping
- actor identity available where required
- linked evidence or source process where available

Poor-quality adjustment records reduce trust and must be corrected.

---

## 17. Example Exception Messages

### Example A — Store count variance
**Subject:** Review required for repeated count variance on high-velocity SKU

**Message:**  
Store 144 recorded a negative inventory adjustment of 28 units for SKU 55102 during cycle count review at 9:20 AM. This is the third adjustment for the same item in the last two weeks and now creates potential shelf availability distortion. Inventory control and store operations should review movement history and physical handling process today. Initial update required by 3:00 PM.

### Example B — Warehouse receiving correction
**Subject:** Receiving adjustment exception requires warehouse review

**Message:**  
Warehouse W02 posted a positive adjustment after inbound reconciliation for SKU group 7701–7715. The quantity difference is above normal receiving tolerance and does not fully align with shipment support currently on file. Warehouse operations to review receiving records and put-away timing by end of day. Finance control to be informed if variance remains unsupported.

### Example C — Damage write-off spike
**Subject:** Damage-related inventory adjustment exceeds normal threshold

**Message:**  
South region stores recorded above-threshold damage write-off adjustments for chilled beverage SKUs during the current review week. The pattern suggests a possible handling or storage control issue rather than isolated item damage. Regional operations and inventory control should review affected locations and confirm root cause by tomorrow 11:00 AM.

### Example D — Transfer mismatch escalation
**Subject:** Cross-functional review required for transfer reconciliation mismatch

**Message:**  
A transfer-related negative adjustment in Warehouse W05 and corresponding store-side shortage signal indicate possible booking or receipt mismatch for an inter-location movement completed yesterday. The issue affects a priority SKU group and may distort replenishment logic. Warehouse, store operations, and inventory control coordination is required today.

---

## 18. Non-Compliant Handling Examples

The following are poor practices:

- posting manual adjustment without usable reason
- closing the issue after correcting quantity only
- ignoring repeated adjustment pattern
- failing to assess financial exposure
- not informing planning when stock accuracy affects replenishment logic
- escalating without confirming the basic transaction facts
- using vague comments instead of clear investigation notes

---

## 19. Link to Governance Documents

This guide should be used alongside:

- audit logging and decision trace policy
- internal operational communication guidelines
- store execution exception communication guide
- regional operations escalation playbook
- executive exception escalation policy
- approval authority matrix
- replenishment decision playbook where stock accuracy affects decisions

---

## 20. RAG Retrieval Guidance

For knowledge retrieval use, this document should be indexed as:

- document_type: guide
- domain: inventory_control
- business_function: exception_management
- sensitivity: internal
- primary_topics:
  - inventory adjustment exception
  - count variance
  - shrink investigation
  - receiving correction
  - transfer mismatch
  - write-off review

Useful retrieval prompts include:
- inventory adjustment exception guide
- how to review count variance
- unexplained shrink handling
- receiving correction exception rules
- transfer reconciliation mismatch guidance

---

## 21. Ownership

**Primary Owner:** Inventory Control and Operations Governance  
**Supporting Stakeholders:** Store Operations, Warehouse Operations, Finance Control, Supply Chain Planning, Audit, Loss Prevention  
**Review Frequency:** Annual or after major inventory control process change

---

## 22. Summary

NRD requires inventory adjustment exceptions to be reviewed with facts, business context, ownership, and proper traceability.

This guide helps teams move beyond simple quantity correction and instead understand the operational, financial, and planning significance of unusual inventory adjustments so that downstream decisions in EDIP remain reliable.