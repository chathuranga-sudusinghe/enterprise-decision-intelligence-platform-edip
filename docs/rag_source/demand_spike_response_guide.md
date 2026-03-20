---
document_id: "DOC-NRD-GDE-001"
document_title: "Demand Spike Response Guide"
document_type: "guide"
department: "supply_chain_planning"
business_domain: "forecast"
region_scope: "enterprise"
audience: "cross_functional"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Director, Demand Planning and Retail Availability"
confidentiality_level: "internal"
tags:
  - demand_spike
  - demand_review
  - replenishment_adjustment
  - transfer_response
  - allocation_response
  - escalation
  - approval_support
  - operational_reasoning
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
document_status: "active"
approval_level: "director"
related_structured_domains:
  - fact_demand_forecast
  - fact_replenishment_recommendation
  - fact_inventory_snapshot
source_path: "docs/rag_source/demand_spike_response_guide.md"
---

# Demand Spike Response Guide
## NorthStar Retail & Distribution (NRD)
## EDIP / Phase 5 RAG Knowledge Layer
## File: docs/rag_source/demand_spike_response_guide.md

## 1. Purpose

This guide defines the standard response approach for demand spike situations at NorthStar Retail & Distribution (NRD).

Its purpose is to ensure that sudden or unusually high demand is identified early, assessed consistently, communicated clearly, and managed in a controlled, business-focused way before it causes stockouts, poor promotion execution, service instability, or avoidable operational disruption.

This guide supports the Enterprise Decision Intelligence Platform (EDIP) by providing governed knowledge for:

- demand spike detection
- short-term availability protection
- replenishment adjustment
- transfer and allocation response
- promotion and event-related demand review
- escalation and approval support
- audit-aware operational reasoning

---

## 2. Scope

This guide applies to demand spike situations involving:

- sudden store-level demand uplift
- regional demand surges
- promotion-driven demand above plan
- weather-related demand increase
- event-driven demand concentration
- social or viral demand effects
- competitor disruption shifting demand unexpectedly
- short-term demand acceleration on high-velocity SKUs
- repeated forecast miss caused by abrupt uplift
- demand uplift that threatens warehouse, replenishment, or store execution stability

This guide applies to teams such as:

- demand planning
- supply chain planning
- regional operations
- store operations
- warehouse operations
- procurement
- merchandising and commercial teams
- inventory control
- executive stakeholders for major demand-driven business risk

---

## 3. Definition of Demand Spike

A demand spike exists when actual or near-term expected demand rises materially above normal, forecasted, or operationally planned levels within a short period and creates risk to inventory availability, replenishment timing, or execution stability.

Examples include:

- sales rate rises sharply beyond forecast
- store cluster shows unusual uplift for a key SKU
- promotion response materially exceeds expected range
- sudden local demand event depletes stock faster than planned
- regional demand increases due to weather, holiday, or social trend
- competitor out-of-stock shifts demand unexpectedly to NRD stores

A demand spike is not only a sales observation.  
It is a planning, replenishment, and operational continuity risk.

---

## 4. Core Principles

All demand spike responses must follow these principles.

### 4.1 Detect early
The business should react to unusual demand acceleration before service breaks.

### 4.2 Validate the signal
Teams should confirm that the uplift is real and not caused by data error, timing lag, or inventory distortion.

### 4.3 Protect critical availability first
When demand exceeds plan, priority should go to high-velocity, service-critical, and commercially important items and locations.

### 4.4 Use realistic operational constraints
Response actions must reflect actual warehouse, transport, supplier, and store execution capability.

### 4.5 Coordinate across functions
Demand spikes often require planning, operations, procurement, and commercial alignment.

### 4.6 Preserve traceability
Major reprioritization, override, allocation, and escalation decisions must be documented appropriately.

---

## 5. Typical Causes of Demand Spikes

Demand spikes may arise from:

- successful promotion performance above plan
- holiday or seasonal uplift
- extreme weather conditions
- local event or festival activity
- media or viral social attention
- competitor stockout or campaign failure
- sudden bulk or institutional buying behavior
- public concern or panic buying pattern
- assortment change shifting demand to fewer SKUs
- store execution improvement increasing sell-through unexpectedly
- delayed prior demand creating concentrated catch-up buying

The actual cause should be reviewed before major corrective action is taken.

---

## 6. Common Demand Spike Categories

### 6.1 Store-level demand spike
One store or a small cluster of stores experiences sharp uplift.

### 6.2 Regional demand spike
A wider geographic area shows unusual demand concentration.

### 6.3 Promotion-linked demand spike
A campaign drives stronger-than-expected demand.

### 6.4 Event-driven demand spike
Demand rises due to external event timing, holiday, festival, or local activity.

### 6.5 Competitor-shift demand spike
Demand moves to NRD because competing retailers face stockout, pricing issue, or execution failure.

### 6.6 Weather-linked demand spike
Demand rises because of temperature, rainfall, storm preparation, or related short-term factors.

### 6.7 Multi-factor demand spike
Demand acceleration is driven by more than one factor and requires cross-functional interpretation.

---

## 7. Trigger Conditions

A demand spike should be treated as a formal response case when one or more of the following apply:

- sales rate materially exceeds forecast or normal range
- projected cover drops rapidly due to accelerated demand
- multiple stores or a region show the same uplift pattern
- demand spike affects high-priority or high-velocity SKU
- active promotion or key trading window is exposed
- warehouse or transfer flow may not recover demand in time
- supplier lead time prevents normal replenishment recovery
- repeated near-term forecast miss is visible
- local action alone is insufficient
- executive or policy exception may be required

---

## 8. Required Assessment Fields

Every material demand spike review should capture, where available:

- SKU / item ID and description
- affected store, region, or channel scope
- current sales rate
- planned forecast or baseline demand
- size of demand uplift
- current on-hand and usable inventory
- projected days of cover
- next confirmed replenishment, transfer, or inbound timing
- likely cause category
- promotion or event relevance
- mitigation options considered
- priority classification
- response owner
- escalation status
- next review time
- final resolution

---

## 9. Standard Response Workflow

The normal demand spike response workflow should follow this sequence:

1. detect the demand spike signal
2. validate sales, inventory, and timing facts
3. classify the spike type and urgency
4. assess business impact and affected scope
5. identify feasible mitigation options
6. prioritize high-risk items and locations
7. assign response owner
8. communicate to impacted teams
9. escalate if local action is insufficient
10. document final action, decision, and closure

The response should focus on protecting service continuity while maintaining operational discipline and governance.

---

## 10. Severity Levels

### Level 1 — Local manageable spike
Demand increase exists but can be handled through normal short-term replenishment adjustment.

Examples:
- isolated store uplift with nearby replenishment support
- one lower-risk SKU with sufficient stock buffer
- short-lived local increase with limited business impact

### Level 2 — Managed operational spike
Demand increase affects important availability decisions and requires cross-team visibility.

Examples:
- moderate uplift on important SKU
- multiple nearby stores showing the same demand pattern
- promotion item performing above expected range
- transfer support may be needed

### Level 3 — Cross-functional demand disruption
Demand spike materially affects multiple locations, priority items, or major commercial activity and requires coordinated action.

Examples:
- regional uplift on high-velocity SKU family
- campaign demand materially above planned inventory support
- warehouse and planning both affected by recovery needs
- supplier timing limits replenishment recovery

### Level 4 — Executive or governance escalation
Demand spike creates major service or commercial exposure and requires exception approval or executive direction.

Examples:
- large regional shortage risk due to extreme demand surge
- national or multi-region campaign uplift beyond planned capacity
- controlled allocation decision required
- urgent exception to normal replenishment priorities needed

---

## 11. Business Impact Assessment

Demand spike cases should be assessed across the following areas.

### 11.1 Customer service impact
Will shelves empty earlier than expected or product choice narrow materially?

### 11.2 Sales and revenue impact
Will the spike create missed sales if supply response is too slow?

### 11.3 Promotion and campaign impact
Is the uplift linked to a campaign that now requires revised support?

### 11.4 Operational impact
Will stores, warehouses, transfers, or transport require revised action?

### 11.5 Governance impact
Does the case require exception approval, executive review, or formal decision logging?

---

## 12. Immediate Mitigation Options

Depending on the situation, teams may consider:

- accelerating replenishment review cadence
- reprioritizing available stock to highest-risk stores
- initiating inter-location transfer review
- temporarily adjusting replenishment quantities
- protecting highest-velocity SKUs first
- delaying lower-priority allocations
- coordinating with procurement for supply recovery where feasible
- reviewing substitute item support where approved
- revising promotion support assumptions if needed
- increasing monitoring frequency until demand stabilizes
- escalating for controlled allocation or exception approval

Any material deviation from normal policy must follow approved governance and approval paths.

---

## 13. Prioritization Rules During Demand Spike

When available stock cannot support the full unexpected uplift, prioritization should generally favor:

1. service-critical and highest-velocity SKUs
2. stores or regions with the earliest projected depletion
3. active promotion or campaign support items
4. strategically important or high-visibility locations
5. normal lower-priority replenishment after higher-risk availability is protected

Priority decisions should be documented when they materially change standard replenishment behavior.

---

## 14. Communication Standards

When communicating a demand spike, the message should include:

- what item or item group is affected
- affected stores, region, or channel
- size and timing of the demand uplift
- likely cause
- expected business impact
- actions already taken
- action or decision now needed
- owner
- next update time

Avoid vague messages such as:

- “sales are high”
- “demand is increasing”
- “stock is moving fast”
- “please monitor urgently”

Good communication must be clear, specific, and action-oriented.

---

## 15. Escalation Guidance

Escalation should be considered when:

- local recovery action is not enough
- multiple stores or regions are affected
- current stock will not cover demand until next supply event
- warehouse or supplier limits block recovery
- promotion or key trading period is exposed
- transfer or allocation changes require management approval
- repeated spike pattern suggests broader planning review
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

### 16.1 Promotion-linked spike
Check:
- campaign status
- uplift size vs planned range
- affected stores
- current stock support
- whether store execution amplified demand
- need for campaign support adjustment

### 16.2 Weather-linked spike
Check:
- weather pattern relevance
- affected geography
- SKU sensitivity to condition
- expected duration
- available supply recovery options

### 16.3 Competitor-shift spike
Check:
- competitor disruption evidence if available
- affected products
- local or regional pattern
- duration likelihood
- need for temporary allocation changes

### 16.4 Event-driven spike
Check:
- event date and duration
- local demand concentration
- store cluster exposure
- whether uplift is predictable for future events
- immediate replenishment support options

### 16.5 Forecast miss spike
Check:
- baseline forecast assumption
- recent trend break
- whether issue is isolated or systematic
- planner override history
- need for short-term forecasting adjustment

### 16.6 Inventory integrity concern
Check:
- whether demand signal is real sales or distorted by stock timing issue
- recent count or adjustment history
- physical availability confidence
- urgency of inventory validation

---

## 17. Link to EDIP Decisioning

Demand spikes matter to EDIP because they directly affect:

- short-term demand interpretation
- replenishment recommendations
- transfer suggestions
- regional inventory risk scoring
- planner override decisions
- promotion support evaluation
- executive exception decisioning

For this reason, material demand spike events should be visible to relevant planning, operations, procurement, and governance functions when they alter downstream decisions.

---

## 18. Data Quality and Traceability Expectations

Demand spike records should meet these standards:

- valid SKU and location scope
- usable timestamp
- current sales rate or uplift reference
- forecast or baseline comparison
- current stock or cover reference
- clear spike classification
- owner identity
- next review time for active case
- mitigation or escalation note
- final resolution captured for material cases

Poor-quality demand spike records reduce response quality and weaken trust in decision support.

---

## 19. Example Response Messages

### Example A — Store-level spike
**Subject:** Immediate review required for demand spike on high-velocity SKU

**Message:**  
Store 118 is showing demand materially above forecast for SKU 44219 during the current trading window. Current sales rate suggests the item may deplete before the next standard replenishment cycle if no action is taken. Planning should review short-term recovery options immediately, and store operations should confirm current shelf and backroom availability by 11:30 AM.

### Example B — Regional spike
**Subject:** Regional demand spike emerging for beverage SKU family

**Message:**  
West region shows a sharp uplift in demand across four beverage SKUs relative to the current forecast baseline. The pattern is visible across seven stores and is reducing projected cover faster than expected. Planning, warehouse operations, and regional operations coordination is required today to determine transfer and replenishment priorities before service impact increases.

### Example C — Promotion-driven spike
**Subject:** Campaign item demand exceeds planned support level

**Message:**  
A featured snack SKU in the approved weekend campaign is performing materially above the planned demand range in the North region. Current stock position is likely insufficient to support the remaining campaign window without reallocation or revised replenishment support. Commercial and planning teams should review mitigation options before 2:00 PM today.

### Example D — Executive escalation
**Subject:** Executive approval required for controlled allocation due to major demand surge

**Message:**  
A major demand spike now affects a strategic SKU family across two regions ahead of a key trading period. Current inventory and confirmed supply are insufficient to support normal replenishment priorities through the expected demand window. Planning recommends temporary controlled allocation to protect highest-priority stores. Executive direction is required before 4:00 PM today.

---

## 20. Non-Compliant Response Examples

The following are poor practices:

- waiting until actual stockout before responding to clear demand acceleration
- assuming the uplift will fade without evidence
- changing replenishment priorities without documented reasoning
- ignoring campaign overperformance risk
- failing to inform impacted teams of material demand change
- using vague “high sales” messages without scope or timing
- not checking whether the spike is real versus a data or timing issue

---

## 21. Link to Governance Documents

This guide should be used alongside:

- stockout risk response playbook
- replenishment decision playbook
- regional inventory risk playbook
- promotion impact review guide
- regional operations escalation playbook
- executive exception escalation policy
- audit logging and decision trace policy
- approval authority matrix
- promotion execution policy where campaign support is affected

---

## 22. RAG Retrieval Guidance

For knowledge retrieval use, this document should be indexed as:

- document_type: guide
- domain: demand_management
- business_function: short_term_response
- sensitivity: internal
- primary_topics:
  - demand spike
  - unexpected uplift
  - short-term replenishment response
  - campaign overperformance
  - allocation decision
  - availability protection

Useful retrieval prompts include:
- demand spike response guide
- how to respond to sudden demand increase
- promotion demand above forecast
- unexpected sales surge handling
- allocation response for demand spike

---

## 23. Ownership

**Primary Owner:** Demand Planning and Availability Response Office  
**Supporting Stakeholders:** Demand Planning, Supply Chain Planning, Warehouse Operations, Regional Operations, Store Operations, Procurement, Commercial Operations  
**Review Frequency:** Annual or after major short-term planning process change

---

## 24. Summary

NRD requires demand spikes to be handled with early detection, validated analysis, business-focused prioritization, disciplined communication, and proper traceability.

This guide helps teams respond before sudden demand growth turns into stockouts, campaign failure, or unmanaged operational disruption, while supporting governed decision-making within EDIP.