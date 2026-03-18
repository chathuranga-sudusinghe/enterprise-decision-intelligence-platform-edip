---
document_id: "DOC-NRD-GDE-002"
document_title: "Forecast Error Exception Response Guide"
document_type: "guide"
department: "supply_chain_planning"
business_domain: "forecast"
region_scope: "enterprise"
audience: "cross_functional"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Director, Forecasting and Inventory Strategy"
confidentiality_level: "internal"
tags:
  - forecast_error
  - exception_classification
  - forecast_review
  - replenishment_impact
  - planner_follow_up
  - operations_follow_up
  - escalation
  - operational_reasoning
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
source_path: "docs/rag_source/forecast_error_exception_response_guide.md"
---

# Forecast Error Exception Response Guide
## NorthStar Retail & Distribution (NRD)
## EDIP / Phase 5 RAG Knowledge Layer
## File: docs/rag_source/forecast_error_exception_response_guide.md

## 1. Purpose

This guide defines the standard response approach for forecast error exception situations at NorthStar Retail & Distribution (NRD).

Its purpose is to ensure that material forecast errors are identified early, assessed consistently, communicated clearly, and managed in a controlled, business-focused way before they create avoidable stockouts, overstock, poor replenishment decisions, or repeated planner overrides.

This guide supports the Enterprise Decision Intelligence Platform (EDIP) by providing governed knowledge for:

- forecast error detection
- exception classification
- short-term and structural forecast review
- replenishment impact assessment
- planner and operations follow-up
- escalation and approval support
- audit-aware operational reasoning

---

## 2. Scope

This guide applies to forecast error exception situations involving:

- short-term forecast underestimation
- short-term forecast overestimation
- repeated forecast bias
- localized forecast misses
- regional forecast instability
- promotion-related forecast miss
- event-driven forecast miss
- model-driven forecast breakdown
- forecast input quality issue
- forecast error that materially affects replenishment, transfer, or stock positioning decisions

This guide applies to teams such as:

- demand planning
- supply chain planning
- regional operations
- store operations
- warehouse operations
- procurement
- commercial and merchandising teams where campaign items are affected
- inventory control
- data and analytics support
- executive stakeholders for major business risk cases

---

## 3. Definition of Forecast Error Exception

A forecast error exception exists when forecast output differs from actual demand or near-term realized demand strongly enough to create meaningful operational, commercial, or control risk.

Examples include:

- actual sales materially exceed forecast and reduce cover faster than planned
- actual sales materially fall below forecast and create excess inventory exposure
- the same SKU shows repeated forecast underestimation
- the same region shows repeated forecast overestimation
- promotion demand behaves far outside the forecast support range
- forecast instability causes repeated override behavior
- model output appears inconsistent with recent demand reality

A forecast error exception is not only a model metric issue.  
It is a business decision quality issue with downstream operational impact.

---

## 4. Core Principles

All forecast error exception responses must follow these principles.

### 4.1 Detect early
The business should identify material forecast error before it creates large service or inventory distortion.

### 4.2 Validate facts before acting
Teams should confirm whether the issue is a true forecast error, a data timing issue, an inventory visibility problem, or an execution problem.

### 4.3 Focus on business impact
Response should consider service level, stock risk, overstock exposure, working capital, and campaign performance impact.

### 4.4 Separate short-term response from root-cause review
Immediate mitigation may be needed now, but structural forecast improvement should also be addressed.

### 4.5 Coordinate across functions
Forecast exceptions often require planning, commercial, operations, procurement, and analytics alignment.

### 4.6 Preserve traceability
Major exception decisions, overrides, escalations, and corrective actions must be documented appropriately.

---

## 5. Typical Causes of Forecast Error Exceptions

Forecast error exceptions may arise from:

- unexpected demand spike
- promotion uplift above or below plan
- competitor activity
- weather-driven demand shift
- local event effect
- poor promotion input assumptions
- missing or delayed business input
- data quality issue
- item master or hierarchy mapping issue
- inventory distortion affecting demand signal interpretation
- recent trend break not captured by model
- seasonality shift
- new product substitution effect
- repeated planner override without closed-loop learning
- model logic or feature weakness

The actual cause should be investigated before major structural action is taken.

---

## 6. Common Forecast Error Categories

### 6.1 Underforecast exception
Actual demand is materially higher than forecast, creating service or stockout risk.

### 6.2 Overforecast exception
Actual demand is materially lower than forecast, creating excess inventory or working capital exposure.

### 6.3 Localized forecast miss
Forecast performs poorly for a store, cluster, or specific location group.

### 6.4 Regional forecast miss
Forecast error affects a wider geographic scope.

### 6.5 Promotion-linked forecast error
Forecast for an active or planned campaign performs materially outside the expected range.

### 6.6 Input-quality-related forecast error
The error appears driven by weak, missing, late, or inconsistent business inputs.

### 6.7 Structural forecast instability
Repeated or patterned error suggests a broader forecasting process or model weakness.

---

## 7. Trigger Conditions

A forecast issue should be treated as a formal exception response case when one or more of the following apply:

- forecast error exceeds local review threshold
- actual demand creates immediate stockout or overstock exposure
- repeated forecast bias is visible for the same SKU, category, store, or region
- high-priority or high-velocity SKU is affected
- promotion or key trading period is exposed
- replenishment decisions are being distorted materially
- repeated override behavior suggests forecast trust breakdown
- local action alone is insufficient
- multiple functions need coordinated response
- executive or policy exception may be required

---

## 8. Required Assessment Fields

Every material forecast error exception review should capture, where available:

- SKU / item ID and description
- affected store, region, warehouse, or channel scope
- forecast value
- actual demand value
- error direction
- error magnitude
- forecast period and review period
- likely cause category
- current inventory or cover position
- affected promotion or event reference if relevant
- current mitigation options
- priority classification
- response owner
- escalation status
- next review time
- final resolution

---

## 9. Standard Response Workflow

The normal forecast error exception workflow should follow this sequence:

1. detect the forecast error signal
2. validate the demand, inventory, and timing facts
3. classify the error type and urgency
4. assess business impact and affected scope
5. identify immediate mitigation options
6. assign response owner
7. communicate to impacted teams
8. escalate if local action is insufficient
9. investigate root cause
10. document final action, learning, and closure

The response should balance short-term business protection with longer-term forecast improvement.

---

## 10. Severity Levels

### Level 1 — Local manageable exception
Forecast error exists but can be handled through normal local adjustment.

Examples:
- isolated store miss with low business exposure
- moderate overforecast on low-priority SKU
- one-time underforecast with easy replenishment recovery

### Level 2 — Managed operational exception
Forecast error affects important inventory or service decisions and requires cross-team visibility.

Examples:
- repeated miss on important SKU
- moderate regional error
- campaign item outside forecast tolerance
- repeated short-term override need

### Level 3 — Cross-functional forecast exception
Forecast error materially affects multiple locations, priority items, or commercial performance and requires coordinated response.

Examples:
- high-velocity SKU family underforecast across region
- repeated overforecast causing significant excess
- promotion support error affecting store execution
- warehouse, procurement, and planning all affected

### Level 4 — Executive or governance escalation
Forecast error creates major service, financial, or policy exposure and requires exceptional action or senior review.

Examples:
- strategic SKU family forecast breakdown
- large campaign forecast failure
- major regional stock or overstock exposure
- repeated systemic forecast weakness requiring governance intervention

---

## 11. Business Impact Assessment

Forecast error cases should be assessed across the following areas.

### 11.1 Service impact
Will the error create stockout risk, missed availability, or poor shelf execution?

### 11.2 Inventory impact
Will the error create overstock, excess cover, stock imbalance, or poor transfer decisions?

### 11.3 Commercial impact
Will the issue affect promotion performance, launch readiness, or revenue-critical demand?

### 11.4 Operational impact
Will stores, warehouses, procurement, or replenishment plans need to change materially?

### 11.5 Governance impact
Does the case require exception approval, executive review, or formal decision logging?

---

## 12. Immediate Mitigation Options

Depending on the situation, teams may consider:

- adjusting short-term replenishment quantities
- increasing review cadence for affected items
- initiating inter-location transfer review
- reprioritizing available stock
- protecting highest-risk stores first
- reducing future inbound exposure for clear overforecast cases where feasible
- reviewing supplier timing flexibility
- updating campaign support assumptions
- validating inventory accuracy where stock confidence is weak
- escalating for controlled allocation or exception approval
- flagging the item or scope for urgent forecast review

Any material deviation from normal policy must follow approved governance and approval paths.

---

## 13. Prioritization Rules During Forecast Error Response

When response capacity or supply flexibility is limited, prioritization should generally favor:

1. service-critical and high-velocity SKUs
2. locations with the earliest or highest service risk
3. active promotion or campaign support items
4. strategically important or high-visibility regions
5. normal lower-priority correction work after higher-risk exposure is protected

Priority decisions should be documented when they materially change standard planning behavior.

---

## 14. Communication Standards

When communicating a forecast error exception, the message should include:

- what item or scope is affected
- forecast versus actual position
- timing and direction of the error
- likely cause
- expected business impact
- actions already taken
- action or decision now needed
- owner
- next update time

Avoid vague messages such as:

- “forecast is wrong”
- “sales are different than expected”
- “numbers are off”
- “please review urgently”

Good communication must be clear, specific, and action-oriented.

---

## 15. Escalation Guidance

Escalation should be considered when:

- local adjustment is not enough
- multiple stores or regions are affected
- repeated forecast bias is visible
- promotion or key trading period is exposed
- inventory or service impact is material
- warehouse, procurement, and planning need coordinated mitigation
- repeated override behavior indicates trust breakdown
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

### 16.1 Underforecast exception
Check:
- actual uplift pattern
- current cover
- whether the demand shift is temporary or persistent
- supplier and replenishment recovery options
- whether inventory accuracy distorts visibility
- need for transfer or allocation action

### 16.2 Overforecast exception
Check:
- excess inventory position
- future inbound already committed
- whether the issue is localized or broad
- whether promotion or markdown support needs review
- whether the item substitution pattern changed
- working capital exposure

### 16.3 Promotion-linked forecast error
Check:
- campaign setup and timing
- uplift versus planned range
- store execution quality
- display or pricing support
- remaining campaign window
- need for commercial coordination

### 16.4 Input-quality-related error
Check:
- missing promotional input
- missing event or seasonality signal
- late business updates
- hierarchy or item mapping issue
- upstream data delays
- whether the model received the correct planning context

### 16.5 Structural instability
Check:
- repeated error history
- same direction bias over time
- item group or regional pattern
- override history
- model or ruleset limitation
- need for governance or analytics review

---

## 17. Link to EDIP Decisioning

Forecast error exceptions matter to EDIP because they can directly affect:

- replenishment recommendations
- transfer suggestions
- stockout risk scoring
- overstock risk awareness
- planner override decisions
- promotion support evaluation
- executive exception decisioning

For this reason, material forecast error events should be visible to relevant planning, operations, analytics, and governance functions when they alter downstream decisions.

---

## 18. Data Quality and Traceability Expectations

Forecast error exception records should meet these standards:

- valid SKU and location scope
- usable timestamp
- forecast and actual reference values
- clear error direction and magnitude
- known review period
- clear exception classification
- owner identity
- next review time for active case
- mitigation or escalation note
- final resolution and learning captured for material cases

Poor-quality forecast exception records reduce improvement quality and weaken trust in decision support.

---

## 19. Example Response Messages

### Example A — Underforecast case
**Subject:** Immediate review required for underforecast on high-velocity SKU

**Message:**  
SKU 44219 is currently performing materially above forecast in the West region, and the gap is now reducing projected cover faster than planned across five stores. The item is high velocity, and the current replenishment path may not recover service in time without intervention. Planning should review transfer and replenishment options immediately, and regional operations should confirm local execution conditions by 11:30 AM.

### Example B — Overforecast case
**Subject:** Forecast overestimation creating excess inventory review need

**Message:**  
SKU family 7701–7715 is currently tracking materially below forecast in South region stores, resulting in rising excess cover and potential overstock exposure. The issue appears broader than one store and may require adjustment to near-term replenishment and inbound decisions. Planning and procurement should review exposure by end of day.

### Example C — Promotion-linked forecast miss
**Subject:** Campaign forecast error requires cross-functional review

**Message:**  
A featured snack SKU in the approved weekend campaign is performing materially outside the forecast support range in the North region. Current demand is stronger than planned, and the risk of campaign stockout is increasing. Planning, commercial, and store operations coordination is required today to review mitigation and execution support options.

### Example D — Executive escalation
**Subject:** Executive review required for major forecast exception exposure

**Message:**  
A major forecast exception now affects a strategic SKU family across two regions ahead of a key trading period. Current forecast error magnitude is large enough to distort standard replenishment behavior and create material service risk if not addressed through controlled action. Planning recommends temporary exception handling and executive direction before 4:00 PM today.

---

## 20. Non-Compliant Response Examples

The following are poor practices:

- treating forecast error as only a reporting metric with no operational response
- changing replenishment or allocation behavior without documented reasoning
- ignoring repeated bias because local overrides temporarily hide the issue
- failing to separate data issue from true demand shift
- using vague statements without forecast-versus-actual detail
- not informing impacted teams when service or inventory exposure is material
- closing the issue without root-cause review for repeated cases

---

## 21. Link to Governance Documents

This guide should be used alongside:

- demand spike response guide
- stockout risk response playbook
- transfer execution failure response guide
- promotion impact review guide
- regional inventory risk playbook
- planner override governance policy
- audit logging and decision trace policy
- approval authority matrix
- replenishment decision playbook

---

## 22. RAG Retrieval Guidance

For knowledge retrieval use, this document should be indexed as:

- document_type: guide
- domain: forecast_governance
- business_function: exception_response
- sensitivity: internal
- primary_topics:
  - forecast error
  - underforecast
  - overforecast
  - forecast bias
  - promotion forecast miss
  - corrective action

Useful retrieval prompts include:
- forecast error exception response guide
- how to respond to underforecast
- overforecast operational response
- repeated forecast bias handling
- promotion forecast miss review

---

## 23. Ownership

**Primary Owner:** Demand Planning Governance Office  
**Supporting Stakeholders:** Demand Planning, Supply Chain Planning, Regional Operations, Warehouse Operations, Procurement, Commercial Operations, Analytics Support  
**Review Frequency:** Annual or after major forecasting process change

---

## 24. Summary

NRD requires forecast error exceptions to be handled with early detection, validated analysis, business-focused prioritization, disciplined communication, root-cause review, and proper traceability.

This guide helps teams respond before forecast error turns into unmanaged stockout, overstock, campaign failure, or repeated override dependence, while strengthening governed decision-making within EDIP.