---
document_id: "DOC-NRD-GDE-009"
document_title: "Planning Response to Supplier Fill Rate Drop"
document_type: "guide"
department: "supply_chain_planning"
business_domain: "supplier"
region_scope: "enterprise"
audience: "cross_functional"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Supply Planning and Supplier Performance Governance Office"
confidentiality_level: "internal"
tags:
  - supplier_fill_rate
  - supplier_performance
  - shortfall_response
  - replenishment_adjustment
  - allocation_adjustment
  - escalation_support
  - auditability
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
document_status: "active"
approval_level: "director"
related_structured_domains:
  - fact_purchase_orders
  - fact_inbound_shipments
  - fact_replenishment_recommendation
source_path: "docs/rag_source/planning_response_to_supplier_fill_rate_drop.md"
---

## 1. Purpose

This guide defines the standard planning response when supplier fill rate drops below expected service levels at NorthStar Retail & Distribution (NRD).

Its purpose is to ensure that declining supplier fill performance is identified early, assessed consistently, communicated clearly, and managed in a controlled, business-focused way before it creates avoidable stockout risk, replenishment instability, warehouse disruption, or repeated emergency overrides.

This guide supports the Enterprise Decision Intelligence Platform (EDIP) by providing governed knowledge for:

- supplier fill rate deterioration detection
- planning response to reduced supplier performance
- shortfall and shortage-risk review
- replenishment and allocation adjustment
- supplier performance escalation support
- audit-aware decision traceability

---

## 2. Scope

This guide applies to supplier fill rate decline situations involving:

- lower-than-expected PO fulfillment
- repeated short shipment behavior
- partial order confirmation patterns
- reduced case-fill or line-fill performance
- supplier service degradation on key SKUs
- regional supply instability caused by fill-rate decline
- campaign or seasonal risk linked to poor supplier fulfillment
- supplier performance weakness that materially affects planning decisions
- repeated supplier service deterioration requiring escalated planning response

This guide applies to teams such as:

- supply chain planning
- procurement
- demand planning
- warehouse operations
- regional operations
- store operations
- inventory control
- commercial planning where campaign items are affected
- finance support where business exposure is relevant
- executive stakeholders for major service-risk cases

---

## 3. Definition of Supplier Fill Rate Drop

A supplier fill rate drop exists when a supplier delivers materially less than the requested, expected, or committed quantity across one or more review periods, resulting in meaningful service, inventory, or planning risk.

Examples include:

- supplier fulfills only part of ordered quantities
- case fill rate falls below the expected threshold for key SKUs
- line fill performance weakens across repeated purchase orders
- supplier confirms lower quantities than requested before dispatch
- partial deliveries create unstable replenishment outcomes
- repeated fill-rate decline affects the same category, region, or item family

A supplier fill rate drop is not only a supplier scorecard issue.  
It is a supply continuity and planning stability risk.

---

## 4. Core Principles

All planning responses to supplier fill rate decline must follow these principles.

### 4.1 Detect deterioration early
The business should react when supplier service weakens, not only after repeated stockouts occur.

### 4.2 Focus on service and continuity impact
The response must assess how the fill-rate decline affects availability, replenishment reliability, and downstream business stability.

### 4.3 Protect critical supply first
When supplier fulfillment weakens, priority should go to service-critical items, high-velocity SKUs, and high-risk locations.

### 4.4 Use validated performance evidence
Response actions must be based on real fill-rate, shortfall, ETA, and coverage facts rather than assumption.

### 4.5 Coordinate planning and procurement response
Material fill-rate decline requires alignment between planning mitigation and supplier-facing recovery action.

### 4.6 Preserve traceability
Major mitigation, allocation, override, escalation, and approval decisions must be documented appropriately.

---

## 5. Typical Causes of Supplier Fill Rate Drop

Supplier fill rate may decline due to:

- production shortfall
- raw material shortage
- supplier capacity constraint
- allocation of supplier output to other customers
- quality hold or rejection
- labor shortage
- transport or dispatch limitation
- packaging or labeling issue
- inaccurate supplier inventory visibility
- demand surge beyond supplier readiness
- repeated forecast miss creating unstable order pattern
- weak supplier planning discipline
- temporary external disruption
- structural supplier performance weakness

The actual cause should be validated before major corrective action is taken.

---

## 6. Common Response Categories

### 6.1 Localized fill-rate decline
Supplier fill weakness affects selected SKUs or one part of the network.

### 6.2 Repeated short shipment response
The supplier repeatedly fulfills less than requested quantities across recent orders.

### 6.3 Strategic SKU supply response
Fill-rate decline affects high-priority or service-critical items.

### 6.4 Campaign-support risk response
Poor supplier fulfillment threatens promotion, launch, or seasonal support.

### 6.5 Regional continuity response
Supplier fill weakness creates broader regional service instability.

### 6.6 Temporary supplier recovery response
Planning applies controlled short-term actions while procurement works on supplier stabilization.

### 6.7 Structural supplier performance review
Repeated fill-rate decline indicates a broader supplier-management or sourcing problem requiring governance review.

---

## 7. Trigger Conditions

A supplier fill-rate issue should be treated as a formal response case when one or more of the following apply:

- fill rate falls below local review threshold
- repeated short shipment is visible across recent cycles
- high-priority or high-velocity SKU is affected
- stockout risk rises because expected supply is not fully arriving
- campaign, launch, or seasonal support is exposed
- multiple stores, regions, or warehouses are affected
- local planning action alone is insufficient
- procurement escalation is required
- allocation, transfer, or exception action may be required
- executive or policy exception may be needed

---

## 8. Required Assessment Fields

Every material supplier fill-rate response review should capture, where available:

- supplier ID / supplier name
- purchase order or order-cycle reference
- SKU / item ID and description
- requested quantity
- confirmed quantity
- received quantity
- fill rate percentage
- review period
- response category
- likely cause
- current on-hand and usable inventory
- projected cover or shortage risk
- affected store, warehouse, or region scope
- campaign or seasonal relevance if applicable
- mitigation options considered
- priority classification
- response owner
- escalation status
- next review time
- final resolution and outcome

---

## 9. Standard Response Workflow

The normal planning response workflow should follow this sequence:

1. detect the fill-rate decline signal
2. validate supplier performance and quantity facts
3. classify the response type and urgency
4. assess business impact and affected scope
5. identify feasible mitigation options
6. prioritize high-risk service needs
7. assign response owner
8. communicate to impacted teams
9. escalate if local action is insufficient
10. document final action, decision, and closure

The response should focus on protecting continuity while maintaining governance and supplier-performance discipline.

---

## 10. Severity Levels

### Level 1 — Local manageable decline
Fill-rate weakness exists but can be handled through local adjustment with minimal wider impact.

Examples:
- one low-priority SKU short shipment
- isolated supplier shortfall with adequate stock buffer
- one-cycle issue with low service exposure

### Level 2 — Managed operational decline
Fill-rate weakness affects important availability decisions and requires broader visibility.

Examples:
- moderate shortfall on important SKU
- repeated partial supply across recent orders
- selected stores or regions exposed to lower cover
- temporary allocation or transfer may be needed

### Level 3 — Cross-functional supplier service risk
Supplier fill decline materially affects multiple locations, key items, or campaign support and requires coordinated action.

Examples:
- high-velocity SKU family underfilled across region
- supplier shortfall combined with low cover and limited alternate supply
- planning, procurement, and warehouse coordination required
- service-critical replenishment instability emerging

### Level 4 — Executive or governance escalation
Supplier fill-rate decline creates major service, commercial, or strategic exposure and requires exceptional action or approval.

Examples:
- strategic SKU family underfilled across multiple regions
- key campaign support at major risk due to persistent supplier shortfall
- controlled allocation or policy exception required
- repeated major supplier underperformance requiring senior review

---

## 11. Business Impact Assessment

Supplier fill-rate decline cases should be assessed across the following areas.

### 11.1 Service impact
Will the lower fill rate reduce product availability or increase stockout exposure?

### 11.2 Replenishment impact
Will normal replenishment plans fail because expected quantities are no longer reliable?

### 11.3 Warehouse and flow impact
Will short or partial receipts distort receiving, staging, or allocation plans?

### 11.4 Commercial impact
Will promotions, launches, or strategic demand commitments be affected?

### 11.5 Governance impact
Does the case require exception approval, executive review, or formal decision logging?

---

## 12. Immediate Planning Response Options

Depending on the situation, teams may consider:

- revising short-term replenishment assumptions
- protecting highest-risk stores first
- initiating inter-location transfer review
- applying controlled allocation where approved
- adjusting inbound expectations in planning logic
- reducing dependency on uncertain supplier quantities in near-term decisions
- reviewing substitute or alternate supply where approved
- increasing monitoring frequency until supply stabilizes
- escalating to procurement for supplier recovery action
- escalating for controlled policy exception or executive approval

Any material deviation from normal policy must follow approved governance and approval paths.

---

## 13. Prioritization Rules During Fill-Rate Decline

When available supply is constrained due to fill-rate weakness, prioritization should generally favor:

1. service-critical and high-velocity SKUs
2. stores or regions facing the earliest shortage risk
3. campaign, launch, or seasonal support items
4. strategically important or high-visibility demand commitments
5. lower-risk replenishment after higher-exposure needs are protected

Priority decisions should be documented when they materially change standard replenishment or allocation behavior.

---

## 14. Communication Standards

When communicating a supplier fill-rate decline case, the message should include:

- what supplier and item scope is affected
- requested versus confirmed or received quantity
- fill-rate position and timing
- likely cause
- expected business impact
- actions already taken
- action or decision now needed
- owner
- next update time

Avoid vague messages such as:

- “supplier performance is low”
- “we got less stock”
- “fill rate dropped”
- “please review urgently”

Good communication must be clear, specific, and action-oriented.

---

## 15. Escalation Guidance

Escalation should be considered when:

- local planning action is not enough
- multiple stores or regions are affected
- service-critical items are exposed
- campaign or key trading period support is at risk
- procurement and planning need coordinated mitigation
- repeated underfill pattern suggests structural weakness
- controlled allocation or policy deviation requires approval
- executive approval is needed for exception action

Escalation messages should state:

- issue summary
- affected business scope
- current supplier fill-rate deterioration
- actions already taken
- decision or support required
- owner and timing

---

## 16. Investigation Guidance by Scenario

### 16.1 Repeated short shipment
Check:
- order-by-order fulfillment pattern
- whether the same SKUs are repeatedly underfilled
- supplier explanation quality
- current cover and next supply timing
- need for supplier performance escalation

### 16.2 Strategic SKU underfill
Check:
- item criticality
- service risk timing
- alternate recovery options
- whether transfer or allocation is needed
- urgency of planning intervention

### 16.3 Campaign-support exposure
Check:
- campaign timing
- required inventory positioning date
- current stock buffer
- whether underfill can still be recovered in time
- need for commercial visibility or escalation

### 16.4 Regional continuity risk
Check:
- regional stock exposure
- whether one warehouse or multiple locations are affected
- available rebalancing options
- transport feasibility
- expected duration of supplier weakness

### 16.5 Structural supplier weakness
Check:
- trend of fill-rate decline over time
- category or SKU-family pattern
- frequency of emergency planning response
- whether sourcing or supplier governance review is needed
- need for executive visibility

---

## 17. Link to EDIP Decisioning

Supplier fill-rate decline matters to EDIP because it can directly affect:

- replenishment recommendations
- stockout risk interpretation
- transfer suggestions
- allocation decisions
- planner override behavior
- campaign support readiness
- executive exception decisioning

For this reason, material supplier fill-rate response cases should be visible to relevant planning, procurement, operations, and governance functions when they alter downstream decisions.

---

## 18. Data Quality and Traceability Expectations

Supplier fill-rate response records should meet these standards:

- valid supplier and order reference
- valid item and location scope
- usable timestamp
- requested, confirmed, and received quantity reference
- clear fill-rate calculation or category
- owner identity
- next review time for active case
- mitigation or escalation note
- final resolution and learning captured for material cases

Poor-quality fill-rate response records reduce planning quality and weaken trust in supply-risk decision support.

---

## 19. Example Response Messages

### Example A — Repeated underfill
**Subject:** Immediate planning review required for repeated supplier underfill

**Message:**  
Supplier S-184 has delivered below requested quantities for SKU 44219 across the last three order cycles, and current fill-rate performance is now below the local review threshold. The reduced supply is beginning to weaken cover across selected West region stores. Planning should review short-term allocation and transfer options immediately, while procurement confirms supplier recovery timing by 11:30 AM today.

### Example B — Strategic SKU exposure
**Subject:** Supplier fill-rate drop creating service risk for priority SKU family

**Message:**  
A strategic beverage SKU family supplied by Supplier S-247 is now experiencing materially lower fulfillment against requested quantities. Current stock position is sufficient only for a limited near-term window in North region stores, and the next expected receipt may also be partial. Planning, procurement, and regional operations coordination is required today to protect service continuity.

### Example C — Campaign-support risk
**Subject:** Campaign inventory support at risk due to supplier fill-rate decline

**Message:**  
Supplier fill-rate performance for an approved weekend snack campaign item has weakened materially, and the latest order cycle delivered below the quantity needed to support planned store positioning. Current risk suggests that campaign availability may become uneven across affected stores if no action is taken today. Planning should review controlled allocation options, and procurement should confirm supplier recovery probability before 2:00 PM.

### Example D — Executive escalation
**Subject:** Executive approval required for response to major supplier fill-rate decline

**Message:**  
A major supplier fill-rate decline now affects a strategic SKU family across two regions, and standard replenishment behavior is no longer sufficient to protect service. Planning recommends temporary controlled allocation and near-term supply prioritization while procurement escalates supplier recovery actions. Executive direction is required before 4:00 PM today.

---

## 20. Non-Compliant Handling Examples

The following are poor practices:

- treating fill-rate decline as only a supplier reporting issue
- continuing normal replenishment assumptions despite repeated underfill
- waiting for actual stockout before escalating persistent supplier weakness
- changing allocation priorities without documented reasoning
- failing to inform impacted teams about material service exposure
- using vague supplier-performance messages without quantity context
- closing repeated cases without structural supplier review

---

## 21. Link to Governance Documents

This guide should be used alongside:

- supplier delay operational response guide
- stockout risk response playbook
- replenishment policy exception guide
- inbound supply resequencing guide
- regional operations escalation playbook
- audit logging and decision trace policy
- approval authority matrix
- replenishment decision playbook
- supplier service level summary

---

## 22. RAG Retrieval Guidance

For knowledge retrieval use, this document should be indexed as:

- document_type: guide
- domain: supplier_performance_response
- business_function: fill_rate_management
- sensitivity: internal
- primary_topics:
  - supplier fill rate drop
  - repeated short shipment
  - underfill planning response
  - supply continuity risk
  - allocation response
  - supplier escalation

Useful retrieval prompts include:
- planning response to supplier fill rate drop
- how to respond to supplier underfill
- repeated short shipment handling
- supplier fill-rate decline mitigation
- when supplier performance weakens

---

## 23. Ownership

**Primary Owner:** Supply Planning and Supplier Performance Governance Office  
**Supporting Stakeholders:** Supply Chain Planning, Procurement, Demand Planning, Warehouse Operations, Regional Operations, Store Operations, Inventory Control, Commercial Planning, Finance Support  
**Review Frequency:** Annual or after major supplier-performance governance change

---

## 24. Summary

NRD requires planning responses to supplier fill-rate decline to be handled with early detection, business-focused prioritization, disciplined communication, procurement alignment, and proper traceability.

This guide helps teams respond before lower supplier fulfillment turns into unmanaged stockout risk, unstable replenishment, campaign failure, or repeated emergency decision-making within EDIP.