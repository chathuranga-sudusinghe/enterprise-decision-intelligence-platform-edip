---
document_id: "DOC-NRD-PLB-006"
document_title: "Stockout Risk Response Playbook"
document_type: "playbook"
department: "supply_chain_planning"
business_domain: "inventory"
region_scope: "enterprise"
audience: "cross_functional"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Supply Chain Planning and Availability Governance"
confidentiality_level: "internal"
tags:
  - stockout_risk
  - replenishment_response
  - transfer_response
  - regional_risk_escalation
  - store_availability
  - mitigation_prioritization
  - exception_approval
  - auditability
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
document_status: "active"
approval_level: "executive"
related_structured_domains:
  - fact_inventory_snapshot
  - fact_replenishment_recommendation
  - fact_stock_movements
source_path: "docs/rag_source/stockout_risk_response_playbook.md"
---

# Stockout Risk Response Playbook
## NorthStar Retail & Distribution (NRD)
## EDIP / Phase 5 RAG Knowledge Layer
## Version: 1.0
## Effective Date: 2025-01-01
## Review Cycle: Annual
## Owner: Supply Chain Planning and Availability Governance
## Approved By: VP, Supply Chain Planning and Retail Availability

## 1. Purpose

This playbook defines the standard response approach for stockout risk situations at NorthStar Retail & Distribution (NRD).

Its purpose is to ensure that emerging stockout risk is identified early, assessed consistently, communicated clearly, and managed in a controlled, business-focused way before customer service, sales performance, and operational stability are materially affected.

This playbook supports the Enterprise Decision Intelligence Platform (EDIP) by providing governed knowledge for:

- stockout risk detection
- replenishment and transfer response
- regional risk escalation
- store availability protection
- mitigation prioritization
- exception approval support
- audit-aware decision traceability

---

## 2. Scope

This playbook applies to stockout risk situations involving:

- store-level stockout risk
- warehouse depletion risk
- regional availability risk
- supplier-delay-driven stockout exposure
- promotion-driven stockout risk
- transfer execution failure causing availability risk
- forecast miss causing near-term undercoverage
- unexpected demand spike creating service risk
- inventory accuracy issue distorting available cover
- constrained replenishment capacity affecting availability

This playbook applies to teams such as:

- supply chain planning
- regional operations
- store operations
- warehouse operations
- procurement
- inventory control
- merchandising and commercial teams where campaign items are affected
- executive stakeholders for major service-risk events

---

## 3. Definition of Stockout Risk

A stockout risk exists when current available inventory, confirmed inbound supply, or executable replenishment flow is not sufficient, or may not be sufficient, to support expected demand within the required service window.

Examples include:

- projected days of cover fall below threshold before next confirmed replenishment
- inbound delay creates risk of shelf-out in priority stores
- demand spike exceeds forecast and current availability buffer
- warehouse stock cannot support planned regional replenishment
- promotion demand is likely to exhaust available inventory
- transfer execution failure removes expected coverage
- inventory record appears positive, but physical availability is doubtful

A stockout risk is not only a planning signal.  
It is a customer service, sales, and operational continuity risk.

---

## 4. Core Principles

All stockout risk responses must follow these principles.

### 4.1 Act early
Stockout risk should be addressed before actual service failure occurs.

### 4.2 Focus on business impact
Response actions must consider customer availability, sales impact, promotion relevance, and service priorities.

### 4.3 Protect critical availability first
When supply is constrained, service-critical items, high-velocity SKUs, and high-risk stores or regions should be prioritized.

### 4.4 Use validated facts
Decisions should be based on current cover, confirmed inbound timing, executable transfers, and realistic operational capability.

### 4.5 Coordinate across functions
Material stockout risk often requires planning, procurement, warehouse, and store coordination.

### 4.6 Preserve traceability
Major mitigation, override, allocation, and escalation decisions must be documented appropriately.

---

## 5. Typical Causes of Stockout Risk

Stockout risk may arise from:

- supplier delay
- forecast underestimation
- promotion uplift above expected level
- transfer delay or failure
- warehouse dispatch bottleneck
- store execution issue
- inventory accuracy failure
- replenishment cycle gap
- unexpected local demand spike
- supplier short shipment
- late decision-making
- constrained warehouse or transport capacity
- repeated override behavior masking structural issue

The actual cause should be validated before major corrective action is taken.

---

## 6. Common Stockout Risk Categories

### 6.1 Store-level stockout risk
One or more stores face likely out-of-stock condition within the near-term service window.

### 6.2 Regional stockout risk
Multiple stores in a region face shared depletion risk for the same SKU or category.

### 6.3 Warehouse support risk
Warehouse inventory or processing capability is insufficient to sustain required replenishment flow.

### 6.4 Supplier-linked stockout risk
Delay, short shipment, or uncertainty from supplier timing creates projected coverage failure.

### 6.5 Promotion-linked stockout risk
Campaign demand is likely to exceed available inventory or planned replenishment.

### 6.6 Inventory integrity-linked stockout risk
System stock suggests cover exists, but physical or usable stock may not support actual demand.

### 6.7 Transfer-recovery risk
Expected recovery depends on transfer execution, but transfer timing or quantity is uncertain.

---

## 7. Trigger Conditions

A stockout risk should be treated as a formal response case when one or more of the following apply:

- projected cover falls below local service threshold before next confirmed replenishment
- confirmed inbound arrives after required service window
- high-priority or high-velocity SKU is at risk
- multiple stores or a full region may be affected
- promotion or seasonal demand window is exposed
- transfer dependency exists but is not fully executable
- warehouse availability is insufficient to support demand
- inventory accuracy concern weakens confidence in available stock
- local action alone is insufficient
- executive or policy exception may be required

---

## 8. Required Assessment Fields

Every material stockout risk review should capture, where available:

- SKU / item ID and description
- affected store, warehouse, or region scope
- current on-hand and usable inventory
- projected days of cover
- expected demand window
- next confirmed inbound or transfer timing
- stockout risk category
- likely cause
- affected promotion or campaign reference if relevant
- current mitigation options
- priority classification
- response owner
- escalation status
- next review time
- final resolution

---

## 9. Standard Response Workflow

The normal stockout risk response workflow should follow this sequence:

1. detect the stockout risk signal
2. validate the current inventory and demand facts
3. classify the risk type and urgency
4. assess business impact and affected scope
5. identify feasible mitigation options
6. prioritize high-risk availability needs
7. assign response owner
8. communicate to impacted teams
9. escalate if local action is insufficient
10. document final action, decision, and closure

The response should focus on preventing service failure while maintaining governance and traceability.

---

## 10. Severity Levels

### Level 1 — Local manageable risk
Risk exists but can be handled through normal replenishment adjustment or local operational action.

Examples:
- isolated store risk with confirmed inbound already near
- one low-priority SKU with acceptable service buffer
- short demand spike with manageable correction path

### Level 2 — Managed operational risk
Risk affects important availability decisions and requires cross-team visibility.

Examples:
- moderate low-cover condition on important SKU
- transfer-dependent recovery case
- repeated stockout risk signals for same location
- selected campaign item with moderate exposure

### Level 3 — Cross-functional availability risk
Risk materially affects multiple locations, priority items, or campaign support and requires coordinated action.

Examples:
- high-velocity SKU risk across several stores
- warehouse plus supplier constraint affecting replenishment
- campaign inventory likely to run out before end of event
- urgent regional allocation need

### Level 4 — Executive or governance escalation
Risk creates major service or commercial exposure and requires exceptional action or approval.

Examples:
- major regional shortage for strategic SKU group
- high-impact promotion at risk of visible failure
- controlled allocation decision required across regions
- urgent exception to normal replenishment or distribution rules needed

---

## 11. Business Impact Assessment

Stockout risk cases should be assessed across the following areas.

### 11.1 Customer service impact
Will customers face empty shelves or reduced product choice?

### 11.2 Sales and revenue impact
Will the risk affect high-volume or commercially important demand?

### 11.3 Promotion and campaign impact
Does the issue threaten active or upcoming campaign execution?

### 11.4 Operational impact
Will stores, warehouses, transfers, or replenishment teams need to change planned activity?

### 11.5 Governance impact
Does the case require exception approval, executive review, or formal decision logging?

---

## 12. Immediate Mitigation Options

Depending on the situation, teams may consider:

- expediting confirmed inbound where feasible
- reprioritizing available stock to highest-risk stores
- initiating inter-location transfer review
- adjusting replenishment quantities temporarily
- protecting high-velocity and service-critical SKUs first
- delaying lower-priority allocations
- reviewing substitute or alternate item support where approved
- correcting inventory accuracy issue urgently if stock confidence is weak
- increasing review cadence until the risk stabilizes
- escalating for controlled allocation or exception approval

Any material deviation from normal policy must follow approved governance and approval paths.

---

## 13. Prioritization Rules During Stockout Risk

When available supply is constrained, prioritization should generally favor:

1. service-critical and high-velocity SKUs
2. stores or regions facing the earliest projected stockout
3. active promotion or campaign support items
4. strategically important or contract-sensitive demand commitments
5. normal lower-priority replenishment after higher-risk availability is protected

Priority decisions should be documented when they materially change standard replenishment behavior.

---

## 14. Communication Standards

When communicating a stockout risk, the message should include:

- what item or item group is at risk
- affected stores, warehouse, or region
- projected timing of stockout exposure
- likely cause
- expected business impact
- actions already taken
- action or decision now needed
- owner
- next update time

Avoid vague messages such as:

- “stock may run out”
- “inventory is low”
- “please check urgent”
- “there could be a problem with availability”

Good communication must be clear, specific, and action-oriented.

---

## 15. Escalation Guidance

Escalation should be considered when:

- local recovery action is not enough
- multiple stores or a region are affected
- a promotion or key trading period is exposed
- current cover is insufficient until the next confirmed supply event
- transfer or allocation changes require management approval
- warehouse or supplier limitation blocks normal response
- repeated stockout risk pattern suggests structural weakness
- executive approval is needed for exception action

Escalation messages should state:

- issue summary
- affected business scope
- current timing and severity
- actions already taken
- decision or support required
- owner and timing

---

## 16. Investigation Guidance by Scenario

### 16.1 Supplier-linked risk
Check:
- revised ETA
- quantity confidence
- current available cover
- possible partial shipment
- alternate supply options
- need for escalation

### 16.2 Forecast miss
Check:
- recent demand pattern
- uplift size vs forecast
- whether issue is local or broad
- planning assumptions
- need for override or model review

### 16.3 Promotion-linked risk
Check:
- campaign timing
- remaining event demand
- affected store scope
- current display or execution status
- availability of substitute or reallocation option
- commercial communication need

### 16.4 Transfer-dependent risk
Check:
- transfer source availability
- transfer dispatch timing
- receiving timing feasibility
- transport readiness
- whether transfer alone will fully cover demand

### 16.5 Inventory integrity-linked risk
Check:
- recent count or adjustment history
- physical verification status
- store or warehouse process issue
- risk of false positive stock record
- urgency of inventory correction

### 16.6 Warehouse support risk
Check:
- warehouse available stock
- dispatch readiness
- capacity constraints
- staging or dock issues
- priority allocation options

---

## 17. Link to EDIP Decisioning

Stockout risk matters to EDIP because it directly affects:

- replenishment recommendations
- transfer suggestions
- regional risk scoring
- planner override decisions
- promotion readiness evaluation
- executive exception decisioning
- downstream service and availability performance

For this reason, material stockout risk events should be visible to relevant planning, operations, procurement, and governance functions when they alter downstream decisions.

---

## 18. Data Quality and Traceability Expectations

Stockout risk records should meet these standards:

- valid SKU and location scope
- usable timestamp
- current cover or available stock reference
- known or estimated next supply timing
- clear risk classification
- owner identity
- next review time for active case
- mitigation or escalation note
- final resolution captured for material cases

Poor-quality stockout risk records reduce response effectiveness and weaken trust in decision support.

---

## 19. Example Response Messages

### Example A — Store-level risk
**Subject:** Immediate review required for projected stockout in priority store

**Message:**  
Store 118 is projected to stock out of SKU 44219 before the next confirmed replenishment window based on current sales rate and available cover. The item is a high-velocity SKU and the current replenishment cycle will not recover service in time unless action is taken today. Planning should review transfer feasibility immediately, and store operations should confirm current shelf and backroom availability by 11:30 AM.

### Example B — Regional risk
**Subject:** Regional stockout risk emerging for high-velocity beverage SKU

**Message:**  
West region now shows projected stockout risk for SKU 55102 across seven stores within the next two days. Current warehouse support is limited, and the next supplier-linked inbound remains under timing pressure. Planning, procurement, and warehouse operations coordination is required today to determine allocation and recovery options before service impact increases.

### Example C — Promotion-linked risk
**Subject:** Campaign availability at risk due to projected stock depletion

**Message:**  
A featured snack SKU in the approved weekend campaign is projected to deplete earlier than planned in the North region due to above-forecast demand. Current stock position is not sufficient to support the remaining campaign window without reallocation or controlled substitution. Commercial and planning teams should review mitigation options before 2:00 PM today.

### Example D — Executive escalation
**Subject:** Executive approval required for controlled allocation due to major stockout risk

**Message:**  
A major stockout risk now affects a strategic SKU family across two regions ahead of a key trading period. Current cover and confirmed supply are insufficient to support standard replenishment behavior. Planning recommends temporary controlled allocation to protect highest-priority stores. Executive direction is required before 4:00 PM today.

---

## 20. Non-Compliant Response Examples

The following are poor practices:

- waiting for actual stockout before acting on clear projected risk
- assuming inbound will recover service without confirmation
- changing allocation priorities without documented reasoning
- ignoring promotion exposure until launch failure occurs
- failing to inform impacted teams about material availability risk
- using vague low-stock messages without timing or scope
- not reviewing inventory accuracy when stock confidence is weak

---

## 21. Link to Governance Documents

This playbook should be used alongside:

- replenishment decision playbook
- regional inventory risk playbook
- supplier delay operational response guide
- warehouse capacity constraint response guide
- regional operations escalation playbook
- executive exception escalation policy
- audit logging and decision trace policy
- approval authority matrix
- promotion execution policy where campaign support is affected

---

## 22. RAG Retrieval Guidance

For knowledge retrieval use, this document should be indexed as:

- document_type: playbook
- domain: availability_management
- business_function: stockout_prevention
- sensitivity: internal
- primary_topics:
  - stockout risk
  - low cover response
  - availability protection
  - allocation decision
  - transfer mitigation
  - promotion stock risk

Useful retrieval prompts include:
- stockout risk response playbook
- how to respond to projected stockout
- low cover mitigation steps
- promotion stockout risk handling
- controlled allocation due to stock shortage

---

## 23. Ownership

**Primary Owner:** Supply Chain Planning and Availability Governance  
**Supporting Stakeholders:** Supply Chain Planning, Procurement, Warehouse Operations, Regional Operations, Store Operations, Inventory Control, Commercial Operations  
**Review Frequency:** Annual or after major availability management process change

---

## 24. Summary

NRD requires stockout risk to be handled with early detection, business-focused prioritization, disciplined communication, and proper traceability.

This playbook helps teams respond before low cover becomes actual service failure, protects high-priority availability, supports governed mitigation decisions, and strengthens decision quality within EDIP.