---
document_id: "DOC-NRD-GDE-011"
document_title: "Promotion Impact Review Guide"
document_type: "guide"
department: "commercial"
business_domain: "promotions"
region_scope: "enterprise"
audience: "cross_functional"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Director of Commercial Analytics"
confidentiality_level: "internal"
tags:
  - promotion_impact
  - campaign_review
  - demand_uplift
  - price_effect
  - sell_through
  - forecast_review
  - replenishment_risk
  - commercial_analysis
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
document_status: "active"
approval_level: "director"
related_structured_domains:
  - fact_promotions
  - fact_price_history
  - fact_sales
source_path: "docs/rag_source/promotion_impact_review_guide.md"
---

# Promotion Impact Review Guide
## NorthStar Retail & Distribution
## File: docs/rag_source/promotion_impact_review_guide.md


## 1. Purpose

This guide defines how NorthStar Retail & Distribution (NRD) should review and interpret the business impact of promotions.

Its purpose is to help planners, analysts, pricing teams, and commercial stakeholders evaluate whether a promotion created meaningful demand uplift, margin pressure, inventory risk, or service-level strain. This guide supports EDIP by providing a grounded framework for explaining why demand changed during a campaign period, whether that change was healthy or risky, and what actions should follow.

---

## 2. Guide objectives

The objectives of this guide are to:

- standardize promotion-impact review across teams
- improve consistency in evaluating demand uplift and sell-through effects
- distinguish healthy promotional performance from distorted or risky outcomes
- connect promotions to price history, demand behavior, and replenishment decisions
- support explainable business reasoning in EDIP
- reduce weak or overly simplistic interpretation of campaign results
- improve auditability of promotion-impact commentary and action decisions

---

## 3. Scope

This guide applies to:

- promotion-linked demand review
- discount and markdown campaign analysis
- post-promotion performance interpretation
- campaign effects on replenishment and inventory planning
- promotion-driven regional or channel variation
- business review of campaign outcomes captured in EDIP

This guide does not apply to:

- media-spend optimization models
- detailed marketing attribution beyond operational business review
- creative campaign design procedures
- legal approval of promotions
- technical ETL or model-debugging procedures

---

## 4. Promotion review principles

### 4.1 Promotions must be judged by business effect, not activity alone
A promotion is not successful simply because it ran. It must be evaluated by what it changed and whether the change was useful.

### 4.2 Uplift without control can still be harmful
A campaign may increase volume but still create margin loss, stock pressure, or unstable planning conditions.

### 4.3 Price and promotion must be interpreted together
Promotion impact should not be reviewed without checking the related price change, discount depth, and campaign timing.

### 4.4 Demand uplift must be interpreted carefully
Not every increase during a promotion reflects true underlying demand growth. Some uplift may be temporary, pulled forward, localized, or inventory-constrained.

### 4.5 Promotion review must support action
The review should help teams decide whether to repeat, refine, slow, or avoid similar campaigns in the future.

### 4.6 Traceability is required
Material promotion-impact conclusions should be documented clearly enough for commercial, planning, and audit review.

---

## 5. Definitions

### 5.1 Promotion
A controlled commercial action intended to influence demand through discounting, campaign visibility, bundling, or other planned merchandising activity.

### 5.2 Promotion window
The approved time period during which the campaign is active.

### 5.3 Baseline demand
Expected demand without the promotional effect.

### 5.4 Demand uplift
The increase in observed demand relative to the expected baseline or comparable normal condition.

### 5.5 Promotion carryover
Continued elevated demand or operational effect after the official campaign period ends.

### 5.6 Promotion fade
A decline in demand after the campaign ends, especially when uplift does not persist.

### 5.7 Distorted result
A campaign outcome that is hard to interpret cleanly because of stock constraints, supply instability, poor timing, data issues, or overlapping commercial activity.

---

## 6. Standard promotion-impact review workflow

### 6.1 Step 1 — Confirm campaign context
Review:

- promotion identifier
- campaign type
- start and end dates
- affected SKU or product group
- channel and region scope
- target business objective
- discount or price-change structure

### 6.2 Step 2 — Review price and commercial setup
Check:

- base price before campaign
- active promotion price
- discount depth
- whether markdown and promotion logic overlap
- whether campaign timing matched the approved plan
- whether the promotion had broad or limited visibility

### 6.3 Step 3 — Review demand behavior
Check:

- demand before promotion
- demand during promotion
- demand immediately after promotion
- whether movement exceeded normal range
- whether uplift appeared stable, temporary, or uneven
- whether performance differed by region or channel

### 6.4 Step 4 — Review inventory and service interaction
Check:

- stock coverage before campaign
- whether the promotion created low-stock or stockout pressure
- whether inbound recovery kept pace
- whether realized sales were constrained by availability
- whether the campaign increased urgent replenishment activity

### 6.5 Step 5 — Review margin and pricing effect
Check:

- whether discount depth was commercially justified
- whether uplift was large enough to support the pricing action
- whether repeated discounting risk increased
- whether margin pressure appears acceptable or concerning

### 6.6 Step 6 — Determine performance outcome
Classify the promotion outcome as one of the following:

- effective and controlled
- effective but operationally strained
- mixed result
- weak result
- distorted result
- escalate for deeper review

### 6.7 Step 7 — Record findings and next action
Material campaign conclusions should be logged with evidence, business interpretation, and recommended follow-up.

---

## 7. Outcome framework

### 7.1 Effective and controlled
Use when the promotion created useful demand uplift and remained operationally manageable.

### 7.2 Effective but operationally strained
Use when uplift was strong, but stock pressure, receiving delay, or replenishment strain created concern.

### 7.3 Mixed result
Use when some goals were achieved but other outcomes weakened the overall result.

### 7.4 Weak result
Use when uplift or commercial value was limited relative to the discount or campaign effort.

### 7.5 Distorted result
Use when the outcome cannot be interpreted cleanly because supply, stock, price overlap, or execution issues affected the result.

### 7.6 Escalate for deeper review
Use when the campaign created unusually high exposure, conflict, or unclear high-impact outcome.

---

## 8. Effective and controlled criteria

A promotion may be considered effective and controlled when:

- observed uplift was meaningful
- stock remained sufficiently protected
- supplier and inbound support were adequate
- discount depth remained commercially reasonable
- post-promotion performance normalized in a manageable way
- no major operational or governance issue occurred

This is the preferred promotion outcome.

---

## 9. Effective but operationally strained criteria

A promotion may fit this outcome when:

- demand uplift was strong
- the business objective was broadly achieved
- stock coverage tightened materially
- inbound recovery struggled to keep pace
- urgent replenishment pressure increased
- local service risk became uncomfortable

This means the campaign worked commercially but stressed operations.

---

## 10. Mixed-result criteria

A promotion may be considered mixed when:

- demand improved but margin pressure was high
- some regions or channels performed well while others did not
- uplift was short-lived
- inventory improved for some SKUs but not others
- post-promotion fade was stronger than expected
- the campaign result is usable but not clearly repeatable without adjustment

Mixed result means learn, refine, and avoid oversimplified success claims.

---

## 11. Weak-result criteria

A promotion may be considered weak when:

- uplift was limited or unclear
- discount depth was not justified by demand response
- commercial objective was not meaningfully advanced
- inventory remained imbalanced
- sales movement changed little relative to expectation
- similar campaigns have repeatedly underperformed

Weak result should trigger review before repeating the same structure.

---

## 12. Distorted-result criteria

A promotion may be considered distorted when:

- stockouts suppressed realized sales
- low stock prevented fair evaluation of demand response
- supplier or receiving issues interrupted availability
- overlapping promotions or pricing events confused interpretation
- campaign timing was not executed as planned
- master-data or event-tagging issues affected the record
- regional variation was so uneven that one conclusion is not reliable

Distorted result means the outcome should be interpreted carefully before business decisions are made.

---

## 13. Escalation criteria

Escalation is appropriate when:

- the campaign created material service-level exposure
- pricing and commercial objectives conflict with inventory protection
- financial or margin risk is unusually high
- cross-functional disagreement exists about campaign continuation or extension
- campaign-driven demand created major replenishment or allocation conflict
- repeated promotion underperformance suggests broader structural issue
- the result affects high-visibility or strategically important SKUs

Escalation should support governed decision-making, not blame assignment.

---

## 14. Demand-interpretation rules

### 14.1 Baseline comparison rule
Always compare campaign movement against a reasonable baseline, not only raw in-period sales.

### 14.2 Temporary uplift rule
A promotion spike should not automatically be treated as permanent demand growth.

### 14.3 Carryover rule
If demand remains elevated after campaign end, determine whether the carryover is real, local, or short-lived.

### 14.4 Fade rule
If demand falls sharply after the campaign, review whether the uplift was pulled forward rather than sustainable.

### 14.5 Stock-constrained rule
If product availability was weak during the campaign, observed sales may understate actual promotional demand.

---

## 15. Price-interpretation rules

### 15.1 Discount-depth rule
Deeper discounts require stronger evidence of useful uplift or inventory benefit.

### 15.2 Price-history rule
Promotion results must be interpreted together with the relevant price history record.

### 15.3 Repeated-discount rule
If repeated campaigns are needed to move the same SKU, review whether the underlying pricing strategy is weak.

### 15.4 Markdown overlap rule
When markdowns and promotions overlap, clarify whether the effect is promotional uplift, clearance effect, or both.

### 15.5 Return-to-base rule
After campaign end, confirm whether price returned correctly to approved normal state.

---

## 16. Inventory and replenishment rules

### 16.1 Pre-campaign readiness rule
A promotion should be reviewed against pre-campaign stock readiness, not only campaign-period sales.

### 16.2 Stock-pressure rule
If uplift outpaces available coverage, planners should review whether the campaign created avoidable service risk.

### 16.3 Recovery-confidence rule
Open inbound supply should not be treated as fully protective when supplier or receiving reliability is weak.

### 16.4 Post-campaign inventory rule
If the campaign did not clear stock as intended, planners should review whether excess inventory remains.

### 16.5 Replenishment-stress rule
If the promotion caused repeated urgent or priority replenishment actions, note that as an operational side effect.

---

## 17. Regional and channel review rules

### 17.1 Regional variation rule
Promotions may perform differently by region. Regional averages should be reviewed before drawing broad conclusions.

### 17.2 Channel variation rule
The campaign may affect store, e-commerce, mobile app, and marketplace demand differently.

### 17.3 Local-strength rule
If one region shows unusually strong uplift, check whether the effect is structural, localized, or event-driven.

### 17.4 Uneven-result rule
A campaign should not be called broadly successful if performance was strong only in a narrow segment while weak elsewhere.

---

## 18. Common promotion-impact scenarios

### 18.1 Strong uplift with healthy stock
The campaign increased demand meaningfully and remained operationally controlled. This is a strong result.

### 18.2 Strong uplift with stock pressure
Demand increased sharply, but coverage fell too quickly and service risk rose. This is commercially positive but operationally strained.

### 18.3 Weak uplift despite deep discount
The price cut was material, but demand response was limited. This is a weak result and should trigger pricing review.

### 18.4 Campaign blocked by stock shortage
Observed sales did not rise much, but stock availability was poor. The result may be distorted rather than weak demand.

### 18.5 Strong regional response only
One region responded well while others remained normal. The campaign should be interpreted locally, not only at enterprise level.

### 18.6 Post-promotion drop
Demand fell sharply after the campaign ended. The uplift may have been temporary or pulled forward.

---

## 19. Evidence standards

### 19.1 Minimum evidence expectation
Every material promotion-impact conclusion should be supported by evidence such as:

- campaign window
- price change and discount depth
- pre-, during-, and post-promotion demand pattern
- stock coverage condition
- supplier and inbound support
- region or channel variation
- margin or pricing concern
- related replenishment stress signals

### 19.2 Higher-impact review expectation
Escalated or high-visibility campaigns require stronger evidence and clearer business explanation.

### 19.3 Unsupported conclusion rule
If the reviewer cannot explain why the campaign succeeded or failed, the result should not be labeled too confidently.

---

## 20. Logging requirements

Material promotion-impact reviews should be logged in the approved process.

### 20.1 Minimum logging fields
A valid promotion-impact review log should include:

- promotion review identifier
- promotion identifier
- affected SKU or scope
- region or channel
- outcome classification
- evidence summary
- reviewer
- timestamp
- next action recommendation
- escalation flag where applicable

### 20.2 Logging quality standard
The review note must be specific enough that another analyst or manager can understand the campaign outcome and why it was classified that way.

### 20.3 Weak logging examples
Weak examples include:
- “promo worked”
- “sales up”
- “not good”
- “review later”

These are not acceptable without business context.

### 20.4 Strong logging examples
Stronger examples include:
- “Promotion classified as effective but operationally strained due to strong uplift, fast coverage decline, and unreliable inbound recovery.”
- “Promotion classified as distorted because campaign demand could not be fairly evaluated under repeated stockout conditions.”
- “Promotion classified as mixed result because uplift was visible in West and E-commerce, but margin pressure and weak post-period normalization reduced overall quality.”

---

## 21. Roles and responsibilities

### 21.1 Commercial Analyst
- review campaign performance
- interpret uplift, timing, and business effect
- document findings clearly

### 21.2 Demand Planner
- assess whether observed demand change should influence forecast interpretation
- identify temporary versus structural movement

### 21.3 Inventory Planner
- assess stock pressure, replenishment strain, and post-campaign inventory impact

### 21.4 Pricing Manager
- review discount depth, price-history consistency, and margin implication

### 21.5 Category Manager
- review category strategy fit and repeatability of the campaign structure

### 21.6 Supply Chain Manager
- review operational strain and escalate where campaign effect creates broader risk

### 21.7 EDIP Decision Support Layer
- surface price, demand, stock, and campaign signals together
- support explainable promotion-impact reasoning
- maintain traceability support
- not replace governed business accountability

---

## 22. Example RAG questions supported by this guide

This document should help EDIP answer questions such as:

- Why did demand increase during this campaign period?
- Why was this promotion called effective but operationally strained?
- Why is this campaign result considered distorted?
- Why does stock availability matter when judging promotion success?
- Why is price history needed to interpret campaign impact?
- Why should planners care about promotion-related demand changes?

---

## 23. Related documents

This guide should be used together with:

- Pricing and Discount Policy
- Monthly Demand Review Report — January 2025
- Forecast Review Checklist
- Replenishment Decision Playbook
- Regional Performance Review — West
- Supplier Service Level Summary

---

## 24. Review and maintenance

This guide must be reviewed at least annually or earlier when major changes occur in:

- promotion operating model
- pricing governance
- campaign measurement approach
- replenishment coordination process
- demand-planning integration
- EDIP commercial analytics logic

All updates must be version-controlled and approved by the responsible business owner.

---

## 25. Final guide statement

NorthStar Retail & Distribution will review promotion impact through a business-aware, evidence-based, and traceable framework. Promotion outcomes within EDIP must be interpreted using demand behavior, price history, inventory condition, supply reliability, and regional variation so that campaign decisions remain explainable, operationally useful, and aligned with enterprise commercial and service objectives.