---
document_id: "DOC-NRD-SOP-002"
document_title: "Warehouse Receiving SOP"
document_type: "sop"
department: "warehouse_operations"
business_domain: "warehouse"
region_scope: "enterprise"
audience: "operations_staff"
effective_date: "2025-01-01"
review_date: "2025-12-31"
version: "1.0"
owner_role: "Director of Warehouse Operations"
confidentiality_level: "internal"
tags:
  - warehouse_receiving
  - inbound_receipt
  - goods_receipt
  - receiving_check
  - putaway
  - discrepancy_handling
  - operational_control
  - auditability
source_system: "edip_phase_5_docs"
company_name: "NorthStar Retail & Distribution"
document_status: "active"
approval_level: "director"
related_structured_domains:
  - fact_inbound_shipments
  - fact_purchase_orders
  - fact_inventory_snapshot
source_path: "docs/sops/warehouse_receiving_sop.md"
---

# Warehouse Receiving SOP
## NorthStar Retail & Distribution (NRD)
## EDIP / Phase 5 RAG Knowledge Layer
## File: docs/sops/warehouse_receiving_sop.md

## 1. Purpose

This Standard Operating Procedure (SOP) defines the official inbound receiving process for NorthStar Retail & Distribution (NRD).

The purpose of this SOP is to ensure that all inbound deliveries are received, checked, recorded, and routed in a consistent and auditable manner. This SOP supports enterprise inventory accuracy, supplier performance monitoring, replenishment reliability, and traceable warehouse operations within EDIP.

---

## 2. SOP objectives

The objectives of this SOP are to:

- ensure inbound shipments are received consistently
- confirm that delivered goods match expected purchase and shipment records
- identify shortages, damages, over-deliveries, and documentation issues early
- protect inventory accuracy before putaway
- support supplier service-level measurement
- reduce downstream operational errors
- maintain a clean audit trail for warehouse receiving events

---

## 3. Scope

This SOP applies to:

- all NorthStar distribution centers
- all inbound warehouse receiving teams
- all standard supplier deliveries
- all purchase-order-linked inbound receipts
- all inventory receipts requiring stock update before putaway or release

This SOP does not apply to:

- non-inventory office supplies
- customer returns processed through separate returns workflow
- emergency off-system receipts unless separately approved
- internal maintenance material outside inventory control scope

---

## 4. Core operating principles

### 4.1 Accuracy before speed
Inbound inventory must not be accepted into available stock without appropriate receiving checks.

### 4.2 Documented exceptions
Any mismatch, damage, delay, or receipt issue must be recorded clearly and promptly.

### 4.3 Inventory control first
Received stock must only move into available inventory status after confirmation rules are met.

### 4.4 Traceability
Each receiving event must be traceable to shipment reference, purchase order, date, warehouse location, and responsible team.

### 4.5 Supplier accountability
Receiving records must support fair and consistent evaluation of supplier delivery quality and compliance.

---

## 5. Definitions

### 5.1 Inbound shipment
Any delivery of inventory from a supplier, vendor, or approved upstream source into a NorthStar warehouse.

### 5.2 Receiving
The process of unloading, checking, validating, and recording inbound stock before storage or onward movement.

### 5.3 Purchase order
The approved commercial order authorizing receipt of goods.

### 5.4 Advance shipment expectation
The expected inbound record, based on purchase order, shipment notice, or transport planning data.

### 5.5 Discrepancy
Any difference between expected and actual received goods, including quantity, SKU identity, packaging, quality, or timing.

### 5.6 Damaged goods
Items received in a condition that makes them unsellable, unsafe, incomplete, or requiring separate review.

### 5.7 Putaway
The process of moving received goods from receiving area into designated storage locations.

### 5.8 Quarantine area
A controlled location used for damaged, suspicious, undocumented, or review-pending inventory.

---

## 6. Roles and responsibilities

### 6.1 Receiving Associate
- unload and stage inbound goods safely
- verify shipment details against documentation
- count and inspect items
- record discrepancies immediately
- ensure stock is routed to correct status and location

### 6.2 Receiving Supervisor
- oversee receiving accuracy and workflow discipline
- review exception cases
- approve handling for minor discrepancies where allowed
- escalate significant issues to warehouse leadership or procurement

### 6.3 Inventory Control Analyst
- validate receipt accuracy patterns
- investigate repeated mismatch trends
- support reconciliation and audit review
- monitor receiving-related data quality

### 6.4 Procurement Team
- support supplier-side clarification
- resolve PO-related receiving issues
- coordinate with suppliers on shortages, substitutions, or service failures

### 6.5 Warehouse Operations Manager
- ensure SOP compliance
- review severe or repeated receipt issues
- support escalation decisions where operational risk exists

### 6.6 EDIP / Decision Support Layer
- consume receiving signals for supplier service tracking, replenishment logic, and exception monitoring
- support visibility but not replace warehouse control decisions requiring human review

---

## 7. Receiving prerequisites

Before receiving begins, the warehouse team should confirm that:

- shipment is expected or can be matched to approved documentation
- receiving dock or zone is available
- required receiving documents are accessible
- receiving staff have scanner, checklist, and system access where applicable
- safety procedures are ready for unloading
- quarantine area is available for exception cases if needed

If the inbound shipment cannot be matched to a valid expected reference, the case must be reviewed before stock is accepted into available inventory.

---

## 8. Standard receiving workflow

### 8.1 Arrival confirmation
When a shipment arrives, the receiving team must:

- record arrival date and time
- identify carrier or delivery source
- confirm purchase order or shipment reference
- assign receiving lane, dock, or intake area
- note any visible external packaging issues before unloading

### 8.2 Unloading
The receiving team must unload goods safely and stage them in the designated receiving area.

During unloading:
- observe visible damage
- separate suspicious or broken pallets or cartons
- maintain SKU traceability where labeling exists
- avoid mixing inbound goods from unrelated receipts

### 8.3 Document check
The receiving team must compare shipment documentation with expected records.

Minimum checks:
- supplier name
- PO number
- shipment or delivery reference
- SKU identifiers where available
- expected quantity
- delivery date alignment

### 8.4 Physical count
A physical quantity check must be performed using approved counting method.

Count method may include:
- carton count
- unit count
- pallet-based count with validation
- scan-based confirmation where supported

Count results must be recorded before inventory is released as available stock.

### 8.5 Condition inspection
The receiving team must inspect goods for obvious issues such as:

- crushed packaging
- water damage
- broken seals
- missing labels
- visible product damage
- contamination signs
- incorrect packaging format
- mixed-SKU packaging when not expected

### 8.6 System receipt entry
After validation, the receiving event must be recorded in the approved system process.

The receipt record should capture:
- receipt reference
- PO number
- receipt date and time
- warehouse location
- received quantity
- discrepancy quantity if any
- damage status if any
- receiving user or team reference

### 8.7 Status assignment
Received goods must be assigned to one of the following statuses:

- accepted for putaway
- accepted with discrepancy under review
- accepted partial
- held in quarantine
- rejected pending supplier resolution

### 8.8 Putaway release
Only goods confirmed as acceptable may move to standard putaway process.

Goods under unresolved discrepancy or quality concern must not be released into normal available inventory.

---

## 9. Discrepancy handling procedure

### 9.1 Types of discrepancies
A discrepancy may include:

- short shipment
- over-delivery
- wrong SKU
- damaged goods
- undocumented substitution
- mixed-label issue
- missing documentation
- receipt timing mismatch

### 9.2 Immediate action
When a discrepancy is identified, the receiving team must:

- stop normal release for affected goods
- separate affected items if necessary
- document the discrepancy clearly
- notify receiving supervisor
- record supporting evidence when available

### 9.3 Evidence collection
Where practical, discrepancy evidence should include:

- shipment reference
- item count notes
- photos of damage or labeling issue
- affected SKU list
- carton or pallet identifiers
- supplier or carrier remarks if provided

### 9.4 Minor discrepancy handling
Minor discrepancies may be processed locally when approved by warehouse rules and receiving supervisor authority.

### 9.5 Major discrepancy handling
Major discrepancies must be escalated when they involve:

- high-value inventory
- repeated supplier issue pattern
- critical SKU availability risk
- major quantity difference
- safety or contamination concern
- unclear ownership or documentation

### 9.6 Inventory update restriction
Affected items must not be made broadly available until status is resolved according to warehouse control rules.

---

## 10. Damaged goods handling

### 10.1 Initial damage response
Damaged goods must be identified and separated during receiving.

### 10.2 Quarantine rule
Damaged, suspicious, or review-pending goods must be placed in the designated quarantine area.

### 10.3 Documentation
The receiving team must record:

- SKU or item description
- affected quantity
- damage type
- likely severity
- supplier or shipment reference
- date and responsible receiving staff

### 10.4 Escalation
Damage cases should be escalated when:

- product safety may be affected
- damage value is material
- damage pattern suggests supplier or transport failure
- critical products are impacted
- disposal or return decision requires management review

---

## 11. Partial receipt procedure

A partial receipt occurs when less than the expected quantity is received but at least part of the shipment is valid and acceptable.

In such cases:
- received valid quantity must be recorded accurately
- missing quantity must be logged as shortage or pending
- affected PO line must remain traceable
- procurement must be informed when shortage is material or repeated
- replenishment and supplier service tracking must reflect the shortfall

---

## 12. Over-delivery procedure

When actual delivered quantity exceeds expected quantity:

- do not automatically accept excess into normal stock
- verify whether excess quantity is approved, documented, or known
- hold uncertain excess quantity for review
- notify supervisor and procurement where required
- update inventory only according to approved disposition decision

---

## 13. Wrong-SKU or undocumented substitution procedure

If the delivered item does not match expected SKU or approved substitution rules:

- do not book item into expected SKU inventory
- hold the item for review
- document mismatch clearly
- notify supervisor and procurement
- wait for approved disposition before putaway or rejection

---

## 14. Timing and receiving discipline

### 14.1 Same-day entry expectation
Receiving events should be recorded on the same business day whenever operationally possible.

### 14.2 Delay risk
Delayed receipt entry creates risk for:

- inaccurate available inventory
- false stockout signals
- weak supplier measurement
- incorrect replenishment recommendations
- audit trail gaps

### 14.3 Work queue priority
Critical SKU shipments, urgent replenishment receipts, and exception-sensitive deliveries should receive higher receiving priority.

---

## 15. Inventory accuracy control rules

The warehouse team must ensure that:

- receipt quantities reflect actual validated counts
- quarantined goods are not mixed into available stock
- rejected items are clearly separated
- partial receipts remain linked to PO context
- discrepancy adjustments are documented
- putaway follows accepted quantity only

Inventory accuracy is more important than intake speed when the two are in conflict.

---

## 16. Supplier performance support

Receiving records must support supplier performance analysis by capturing indicators such as:

- on-time vs late arrival
- short shipment frequency
- over-delivery frequency
- damage frequency
- documentation accuracy
- repeat discrepancy behavior

This data may be used by EDIP and business teams for supplier service-level review and procurement decisions.

---

## 17. Data and audit traceability requirements

Each receiving event should be traceable to:

- supplier
- purchase order
- shipment reference
- warehouse
- receipt date and time
- receiving staff or team
- quantity received
- discrepancy type
- item status disposition
- escalation reference where applicable

This traceability is required for audit readiness, root-cause analysis, and trustworthy downstream planning.

---

## 18. Compliance requirements

A receiving event is considered compliant when:

- shipment is matched to approved reference
- quantity is validated
- condition is checked
- discrepancy handling is documented
- stock status is correctly assigned
- accepted goods only are released for putaway
- exception cases are escalated when required
- system receipt record is complete and timely

Non-compliance includes:

- receiving stock without validation
- booking damaged or wrong goods into normal inventory
- failing to record shortages or over-deliveries
- mixing quarantine stock with accepted stock
- delaying receipt entry without cause
- bypassing escalation for major receipt issues

---

## 19. Example RAG questions supported by this SOP

This document should help EDIP answer questions such as:

- Why was this inbound shipment held in quarantine?
- Why was only part of the purchase order received?
- Why is this supplier showing repeated receiving discrepancies?
- Why was this receipt not released to available inventory?
- Why does wrong-SKU delivery require review?
- Why is a receiving delay affecting replenishment visibility?

---

## 20. Review and maintenance

This SOP must be reviewed at least annually or earlier when major changes occur in:

- warehouse process design
- receiving technology
- supplier operating model
- inventory-control standards
- audit requirements
- escalation governance

All updates must be version-controlled and approved by the responsible operations owner.

---

## 21. Final SOP statement

NorthStar Retail & Distribution will manage warehouse receiving through a controlled, accurate, traceable, and policy-aligned process that protects inventory accuracy, supplier accountability, and reliable downstream decision-making within EDIP.