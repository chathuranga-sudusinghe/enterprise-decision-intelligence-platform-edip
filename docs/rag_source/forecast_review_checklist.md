# Forecast Review Checklist
## NorthStar Retail & Distribution
## File: docs/rag_source/forecast_review_checklist.md

---

document_id: DOC-NRD-PLAY-002  
document_title: Forecast Review Checklist  
document_type: checklist  
department: demand_planning  
business_domain: forecast_review  
region_scope: enterprise  
audience: demand_planners_inventory_planners_analysts_supply_chain_managers_commercial_review  
effective_date: 2025-01-01  
review_date: 2025-12-31  
version: 1.0  
owner_role: Director of Demand Planning  
confidentiality_level: internal  
tags: forecast, demand_planning, forecast_review, checklist, forecast_exception, demand_variance, planning_governance  
source_system: edip_phase_5_docs  
company_name: NorthStar Retail & Distribution  

---

## 1. Purpose

This checklist defines the standard business review steps for evaluating forecast outputs at NorthStar Retail & Distribution (NRD).

Its purpose is to ensure that forecast review is consistent, explainable, and operationally useful. The checklist helps planners and analysts determine whether a forecast is reliable enough for normal planning use, whether exceptions require adjustment or escalation, and which business signals must be considered before action is taken. This checklist supports EDIP by providing a grounded review framework for forecast-aware decision support.

---

## 2. Checklist objectives

The objectives of this checklist are to:

- standardize forecast review across teams
- improve consistency in interpreting forecast outputs
- reduce weak or instinct-based forecast adjustments
- ensure forecast decisions consider business context
- strengthen demand, replenishment, and inventory coordination
- support explainable forecast-related reasoning in EDIP
- improve auditability of forecast review activity

---

## 3. Scope

This checklist applies to:

- regular forecast review cycles
- SKU-level and regional forecast exception review
- demand patterns relevant to replenishment planning
- forecast outputs used in inventory and supply decisions
- cases where business review may support forecast acceptance, caution, adjustment, or escalation

This checklist does not apply to:

- detailed model development procedures
- full statistical validation documentation
- purely technical model debugging
- commercial approval workflows outside forecast review context

---

## 4. Forecast review principles

### 4.1 Forecasts are decision inputs, not isolated truths
Forecasts should be reviewed as business decision inputs, not accepted or rejected without context.

### 4.2 Business context matters
A forecast that is statistically reasonable may still need caution if promotions, supply disruption, or regional events change its practical meaning.

### 4.3 Review before override
Forecast outputs should be reviewed carefully before planners or analysts apply manual adjustments.

### 4.4 Exceptions are signals
Forecast exceptions should be treated as learning signals. They may reflect temporary noise, demand change, supply distortion, or missing business context.

### 4.5 Traceability is required
Material forecast review decisions should be explainable and recorded in a way that supports auditability and future learning.

---

## 5. Definitions

### 5.1 Forecast review
The business process of evaluating whether forecast output is reasonable, usable, and aligned with current operating context.

### 5.2 Forecast exception
A case where forecast output appears materially misaligned with observed demand, business expectations, or operational context.

### 5.3 Accept
The forecast is considered usable without material intervention.

### 5.4 Monitor
The forecast is directionally usable, but should be watched closely because risk or uncertainty remains.

### 5.5 Adjust
The forecast requires a controlled manual or governed change based on strong business evidence.

### 5.6 Escalate
The forecast case exceeds normal review confidence or authority and needs higher-level attention.

### 5.7 Demand distortion
A situation where observed demand does not cleanly represent true baseline demand because of temporary events, stock constraints, promotions, pricing effects, or data issues.

---

## 6. Standard forecast review checklist

### 6.1 Review the forecast output itself
Confirm the following:

- the forecast is available for the correct SKU, region, channel, and time horizon
- the forecast is current and approved for review use
- forecast values are complete and not obviously missing or corrupted
- the case is linked to the correct planning context

### 6.2 Compare forecast with recent actual demand
Check whether recent observed movement is:

- broadly aligned with forecast expectation
- materially above forecast
- materially below forecast
- highly volatile or unstable
- affected by one-time spikes or dips

### 6.3 Review demand pattern type
Check whether the demand pattern appears to be:

- stable baseline demand
- post-promotion normalization
- temporary spike behavior
- soft-demand period
- seasonal transition
- localized regional change
- demand affected by stock availability limitation

### 6.4 Check inventory context
Review:

- current stock coverage
- recent stockout or near-stockout events
- excess stock exposure
- inbound recovery timing
- whether low sales may actually reflect stock constraint

### 6.5 Check promotion context
Confirm whether the item is affected by:

- active promotion
- recent promotion carryover
- promotion end effect
- delayed campaign execution
- planned upcoming promotion that may change demand interpretation

### 6.6 Check pricing context
Confirm whether recent or current pricing actions may affect demand interpretation:

- discount period
- markdown activity
- base price reset
- price-response sensitivity
- inconsistent local pricing effect

### 6.7 Check supplier and inbound context
Review whether supply conditions may distort demand interpretation or planning usefulness:

- late supplier recovery
- unreliable open purchase orders
- receiving delays
- partial inbound receipts
- weak supplier confidence for the affected flow

### 6.8 Check regional and channel variation
Review whether the forecast should be interpreted differently because of:

- stronger local demand than enterprise average
- weaker local demand than enterprise average
- region-specific volatility
- channel-specific movement differences
- local commercial activity

### 6.9 Check for master-data or input issues
Confirm there is no known issue with:

- SKU status
- lifecycle classification
- lead time
- product mapping
- calendar alignment
- promotion flagging
- location assignment
- data completeness

### 6.10 Determine review outcome
After reviewing the case, classify the forecast outcome as one of the following:

- accept
- monitor
- adjust
- escalate

---

## 7. Accept criteria

A forecast may be accepted when:

- observed demand is broadly aligned with expected movement
- no major promotion, pricing, or supply distortion is present
- inventory context does not contradict the forecast interpretation
- regional variation is manageable
- no major data quality issue is known
- the forecast is usable for standard replenishment and planning activity

Acceptance does not mean perfect accuracy. It means the forecast is good enough for normal operational use.

---

## 8. Monitor criteria

A forecast should be classified as monitor when:

- it is directionally usable but uncertainty is elevated
- demand volatility is present but not yet severe
- inventory or supply conditions create interpretation caution
- promotion or price effects may be fading
- regional deviation exists but is not yet critical
- recent exceptions may be temporary rather than structural

Monitor cases should stay visible in the next review cycle.

---

## 9. Adjust criteria

A forecast may be adjusted when:

- strong business evidence shows the forecast is materially misrepresenting demand
- the distortion is meaningful enough to affect planning quality
- the adjustment logic is specific and explainable
- the change is not just personal preference
- the adjustment follows approved governance

Examples include:
- verified promotion timing shift
- known temporary anomaly not representative of baseline demand
- structural regional uplift confirmed through review
- confirmed master-data issue affecting forecast interpretation

---

## 10. Escalate criteria

A forecast case should be escalated when:

- the forecast error creates major service or inventory risk
- the case affects critical SKUs or major regional exposure
- the review requires authority beyond the reviewer
- demand behavior is highly unstable and high-impact
- commercial and operational interpretation conflicts
- supply issues make local review insufficient
- repeated forecast exceptions suggest deeper model or process issue

Escalation is appropriate when the reviewer cannot safely resolve the issue within standard review authority.

---

## 11. Forecast review questions

The reviewer should ask the following questions.

### 11.1 Demand alignment questions
- Does recent demand broadly support the forecast?
- Is the gap temporary, structural, or unclear?
- Are there repeated misses in the same direction?

### 11.2 Inventory questions
- Is low sales volume caused by weak demand or limited stock?
- Is current stock coverage consistent with forecasted movement?
- Would accepting this forecast create stockout or overstock risk?

### 11.3 Commercial questions
- Did promotion or price change distort the recent pattern?
- Is this item showing temporary uplift or true baseline shift?
- Is campaign timing affecting interpretation?

### 11.4 Supply questions
- Is inbound recovery reliable enough to trust the planning implication?
- Are supplier or receiving issues changing the practical use of the forecast?

### 11.5 Regional questions
- Is this pattern enterprise-wide or localized?
- Does the region require separate interpretation?

### 11.6 Governance questions
- Can this case be handled locally?
- Is there enough evidence to adjust?
- Should the case be escalated instead of manually changed?

---

## 12. Review evidence standards

### 12.1 Minimum evidence expectation
Every material forecast review decision should be supported by identifiable business evidence such as:

- actual demand trend
- promotion calendar detail
- price history context
- inventory coverage signal
- supplier or inbound condition
- regional demand pattern
- verified data issue

### 12.2 Stronger evidence for bigger actions
Larger adjustments or escalations require stronger evidence and clearer business rationale.

### 12.3 Unsupported adjustment rule
If the reviewer cannot explain why an adjustment is needed, the forecast should not be changed casually.

---

## 13. Recording requirements

Material forecast review outcomes should be recorded in the approved review process.

### 13.1 Minimum logging content
A valid review log should include:

- forecast review identifier
- SKU or grouping identifier
- region or channel
- review outcome
- main reason
- supporting evidence summary
- reviewer name or role
- review timestamp
- escalation flag where applicable

### 13.2 Quality standard
The review note should be specific enough that another planner or manager can understand the reasoning without guessing.

### 13.3 Weak logging examples
Weak examples include:
- “forecast changed”
- “looked wrong”
- “too high”
- “needs review”

These are not acceptable without business context.

### 13.4 Strong logging examples
Stronger examples include:
- “Forecast placed in monitor status due to post-promotion normalization and lower recent sell-through in Region West.”
- “Forecast adjusted after confirmed promotion delay changed expected demand timing.”
- “Forecast escalated because demand volatility on a critical SKU created material service risk.”

---

## 14. Common review scenarios

### 14.1 Stock-constrained case
Recent sales are low, but inventory availability was also low. The forecast should not be reduced automatically without checking whether true demand was suppressed by stockout risk.

### 14.2 Post-promotion normalization case
Demand fell after campaign end. The reviewer should check whether the decline is normal normalization or a deeper structural demand shift.

### 14.3 Temporary spike case
A demand spike appears in recent data. The reviewer should confirm whether it reflects real sustained uplift or short-term anomaly.

### 14.4 Regional uplift case
One region shows stronger movement than enterprise average. The reviewer should determine whether a regional adjustment or monitoring flag is justified.

### 14.5 Supplier-distorted case
Demand interpretation is complicated because supply recovery is weak. Low sales may not reflect low demand; they may reflect reduced stock availability.

---

## 15. Roles and responsibilities

### 15.1 Demand Planner
- perform forecast review
- classify the case outcome
- support explainable acceptance, monitoring, adjustment, or escalation

### 15.2 Inventory Planner
- provide stock, coverage, and replenishment context
- highlight service-risk implications

### 15.3 Commercial Analyst or Category Team
- provide price, promotion, or local commercial context where relevant

### 15.4 Supply Chain Manager
- review escalated or high-risk forecast cases
- ensure governance discipline

### 15.5 EDIP Decision Support Layer
- surface relevant context for forecast review
- support evidence visibility and traceable reasoning
- not replace governed human review where required

---

## 16. Example RAG questions supported by this checklist

This document should help EDIP answer questions such as:

- Why was this forecast accepted without change?
- Why was this case marked as monitor instead of adjusted?
- Why did the reviewer check promotion and price history first?
- Why might low sales not justify lowering the forecast?
- Why did this forecast case require escalation?
- Why is regional context important in forecast review?

---

## 17. Related documents

This checklist should be used together with:

- Inventory Replenishment Policy Manual
- Pricing and Discount Policy
- Supplier Service Level Summary
- Monthly Demand Review Report — January 2025
- Regional Performance Review — West
- Planner Override Playbook

---

## 18. Review and maintenance

This checklist must be reviewed at least annually or earlier when major changes occur in:

- forecast operating model
- business review process
- promotion governance
- price-history controls
- inventory-planning integration
- audit and decision-trace requirements

All updates must be version-controlled and approved by the responsible business owner.

---

## 19. Final checklist statement

NorthStar Retail & Distribution will review forecasts through a business-aware, evidence-based, and traceable process. Forecast outputs must be evaluated in the context of demand behavior, inventory position, promotion activity, pricing signals, supply reliability, and regional variation so that planning decisions within EDIP remain controlled, explainable, and operationally useful.