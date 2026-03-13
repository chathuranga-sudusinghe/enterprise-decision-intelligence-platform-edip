-- loading will be stoped when SQL load error
\set ON_ERROR_STOP on

SET search_path TO analytics, public;

-- =========================================================
-- Phase 1.5C — Corrected fact loading script
-- File: database/dml/03_load_phase_1_facts.sql
-- Run from project root:
-- psql -U postgres -d edip_local -f ".\database\dml\03_load_phase_1_facts.sql"
-- =========================================================

-- ---------------------------------------------------------
-- 0) Fix inbound uniqueness rule before loading
-- Old rule was too strict for generated shipment data
-- ---------------------------------------------------------
DROP INDEX IF EXISTS analytics.ux_fact_inbound_shipments_shipment_line;

CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_inbound_shipments_shipment_line
    ON analytics.fact_inbound_shipments(shipment_number, po_line_id);

-- ---------------------------------------------------------
-- 1) Clean reload target tables
-- ---------------------------------------------------------
BEGIN;

TRUNCATE TABLE
    analytics.fact_inbound_shipments,
    analytics.fact_stock_movements,
    analytics.fact_inventory_snapshot,
    analytics.fact_purchase_orders
RESTART IDENTITY;

COMMIT;

-- ---------------------------------------------------------
-- 2) fact_purchase_orders
-- ---------------------------------------------------------
\copy analytics.fact_purchase_orders (po_line_id, purchase_order_id, po_number, po_date_id, expected_receipt_date_id, supplier_id, warehouse_id, product_id, ordered_qty, unit_cost, line_amount, currency_code, order_status, priority_level, buyer_name, contract_reference, created_timestamp) FROM './data/synthetic/fact_purchase_orders.csv' WITH (FORMAT csv, HEADER true);

-- ---------------------------------------------------------
-- 3) fact_inbound_shipments
-- ---------------------------------------------------------
\copy analytics.fact_inbound_shipments (inbound_shipment_line_id, inbound_shipment_id, shipment_number, purchase_order_id, po_line_id, supplier_id, warehouse_id, product_id, shipped_date_id, expected_arrival_date_id, actual_arrival_date_id, received_date_id, shipped_qty, received_qty, rejected_qty, damaged_qty, shipment_status, delay_days, carrier_name, transport_mode, qc_pass_flag, created_timestamp) FROM './data/synthetic/fact_inbound_shipments.csv' WITH (FORMAT csv, HEADER true);

-- ---------------------------------------------------------
-- 4) fact_stock_movements
-- ---------------------------------------------------------
\copy analytics.fact_stock_movements (stock_movement_id, movement_date_id, product_id, location_type, store_id, warehouse_id, movement_type, movement_reason, quantity_change, reference_type, reference_id, source_location_type, source_store_id, source_warehouse_id, target_location_type, target_store_id, target_warehouse_id, unit_cost, created_timestamp) FROM './data/synthetic/fact_stock_movements.csv' WITH (FORMAT csv, HEADER true);

-- ---------------------------------------------------------
-- 5) fact_inventory_snapshot
-- ---------------------------------------------------------
\copy analytics.fact_inventory_snapshot (inventory_snapshot_id, snapshot_date_id, product_id, location_type, store_id, warehouse_id, on_hand_qty, reserved_qty, available_qty, in_transit_qty, damaged_qty, reorder_point_qty, safety_stock_qty, inventory_status, stockout_flag, days_of_cover_estimate, created_timestamp) FROM './data/synthetic/fact_inventory_snapshot.csv' WITH (FORMAT csv, HEADER true);