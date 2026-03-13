SET search_path TO analytics, public;

-- =========================================================
-- Phase 1.6 — Fact Validation Checks
-- EDIP / NorthStar Retail & Distribution
-- Scope:
--   fact_purchase_orders
--   fact_inbound_shipments
--   fact_stock_movements
--   fact_inventory_snapshot
-- =========================================================

-- ---------------------------------------------------------
-- 1) Row counts
-- ---------------------------------------------------------
SELECT 'fact_purchase_orders' AS table_name, COUNT(*) AS row_count
FROM analytics.fact_purchase_orders
UNION ALL
SELECT 'fact_inbound_shipments', COUNT(*)
FROM analytics.fact_inbound_shipments
UNION ALL
SELECT 'fact_stock_movements', COUNT(*)
FROM analytics.fact_stock_movements
UNION ALL
SELECT 'fact_inventory_snapshot', COUNT(*)
FROM analytics.fact_inventory_snapshot
ORDER BY table_name;


-- ---------------------------------------------------------
-- 2) Primary key null checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'fact_purchase_orders.po_line_id' AS check_name, COUNT(*) AS bad_rows
FROM analytics.fact_purchase_orders
WHERE po_line_id IS NULL

UNION ALL
SELECT 'fact_inbound_shipments.inbound_shipment_line_id', COUNT(*)
FROM analytics.fact_inbound_shipments
WHERE inbound_shipment_line_id IS NULL

UNION ALL
SELECT 'fact_stock_movements.stock_movement_id', COUNT(*)
FROM analytics.fact_stock_movements
WHERE stock_movement_id IS NULL

UNION ALL
SELECT 'fact_inventory_snapshot.inventory_snapshot_id', COUNT(*)
FROM analytics.fact_inventory_snapshot
WHERE inventory_snapshot_id IS NULL
ORDER BY check_name;


-- ---------------------------------------------------------
-- 3) Duplicate grain checks
-- Expected:
--   PO duplicate grain = 0 rows
--   Inbound duplicate grain = 0 rows
--   Inventory duplicate grain = 0 rows
-- ---------------------------------------------------------

-- 3A) Purchase order duplicate business grain
SELECT
    po_number,
    product_id,
    warehouse_id,
    po_date_id,
    COUNT(*) AS dup_count
FROM analytics.fact_purchase_orders
GROUP BY po_number, product_id, warehouse_id, po_date_id
HAVING COUNT(*) > 1;

-- 3B) Inbound shipment duplicate business grain
SELECT
    shipment_number,
    product_id,
    warehouse_id,
    COUNT(*) AS dup_count
FROM analytics.fact_inbound_shipments
GROUP BY shipment_number, product_id, warehouse_id
HAVING COUNT(*) > 1;

-- 3C) Inventory snapshot duplicate business grain
SELECT
    snapshot_date_id,
    product_id,
    location_type,
    COALESCE(store_id, -1) AS store_id_check,
    COALESCE(warehouse_id, -1) AS warehouse_id_check,
    COUNT(*) AS dup_count
FROM analytics.fact_inventory_snapshot
GROUP BY
    snapshot_date_id,
    product_id,
    location_type,
    COALESCE(store_id, -1),
    COALESCE(warehouse_id, -1)
HAVING COUNT(*) > 1;


-- ---------------------------------------------------------
-- 4) Required-column null checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'fpo.purchase_order_id' AS check_name, COUNT(*) AS bad_rows
FROM analytics.fact_purchase_orders
WHERE purchase_order_id IS NULL

UNION ALL
SELECT 'fpo.po_number', COUNT(*) FROM analytics.fact_purchase_orders WHERE po_number IS NULL
UNION ALL
SELECT 'fpo.po_date_id', COUNT(*) FROM analytics.fact_purchase_orders WHERE po_date_id IS NULL
UNION ALL
SELECT 'fpo.expected_receipt_date_id', COUNT(*) FROM analytics.fact_purchase_orders WHERE expected_receipt_date_id IS NULL
UNION ALL
SELECT 'fpo.supplier_id', COUNT(*) FROM analytics.fact_purchase_orders WHERE supplier_id IS NULL
UNION ALL
SELECT 'fpo.warehouse_id', COUNT(*) FROM analytics.fact_purchase_orders WHERE warehouse_id IS NULL
UNION ALL
SELECT 'fpo.product_id', COUNT(*) FROM analytics.fact_purchase_orders WHERE product_id IS NULL
UNION ALL
SELECT 'fpo.ordered_qty', COUNT(*) FROM analytics.fact_purchase_orders WHERE ordered_qty IS NULL
UNION ALL
SELECT 'fpo.unit_cost', COUNT(*) FROM analytics.fact_purchase_orders WHERE unit_cost IS NULL
UNION ALL
SELECT 'fpo.line_amount', COUNT(*) FROM analytics.fact_purchase_orders WHERE line_amount IS NULL
UNION ALL
SELECT 'fpo.order_status', COUNT(*) FROM analytics.fact_purchase_orders WHERE order_status IS NULL
UNION ALL
SELECT 'fpo.priority_level', COUNT(*) FROM analytics.fact_purchase_orders WHERE priority_level IS NULL

UNION ALL
SELECT 'fis.inbound_shipment_id', COUNT(*) FROM analytics.fact_inbound_shipments WHERE inbound_shipment_id IS NULL
UNION ALL
SELECT 'fis.shipment_number', COUNT(*) FROM analytics.fact_inbound_shipments WHERE shipment_number IS NULL
UNION ALL
SELECT 'fis.purchase_order_id', COUNT(*) FROM analytics.fact_inbound_shipments WHERE purchase_order_id IS NULL
UNION ALL
SELECT 'fis.po_line_id', COUNT(*) FROM analytics.fact_inbound_shipments WHERE po_line_id IS NULL
UNION ALL
SELECT 'fis.supplier_id', COUNT(*) FROM analytics.fact_inbound_shipments WHERE supplier_id IS NULL
UNION ALL
SELECT 'fis.warehouse_id', COUNT(*) FROM analytics.fact_inbound_shipments WHERE warehouse_id IS NULL
UNION ALL
SELECT 'fis.product_id', COUNT(*) FROM analytics.fact_inbound_shipments WHERE product_id IS NULL
UNION ALL
SELECT 'fis.expected_arrival_date_id', COUNT(*) FROM analytics.fact_inbound_shipments WHERE expected_arrival_date_id IS NULL
UNION ALL
SELECT 'fis.shipped_qty', COUNT(*) FROM analytics.fact_inbound_shipments WHERE shipped_qty IS NULL
UNION ALL
SELECT 'fis.received_qty', COUNT(*) FROM analytics.fact_inbound_shipments WHERE received_qty IS NULL
UNION ALL
SELECT 'fis.rejected_qty', COUNT(*) FROM analytics.fact_inbound_shipments WHERE rejected_qty IS NULL
UNION ALL
SELECT 'fis.damaged_qty', COUNT(*) FROM analytics.fact_inbound_shipments WHERE damaged_qty IS NULL
UNION ALL
SELECT 'fis.shipment_status', COUNT(*) FROM analytics.fact_inbound_shipments WHERE shipment_status IS NULL
UNION ALL
SELECT 'fis.delay_days', COUNT(*) FROM analytics.fact_inbound_shipments WHERE delay_days IS NULL

UNION ALL
SELECT 'fsm.movement_date_id', COUNT(*) FROM analytics.fact_stock_movements WHERE movement_date_id IS NULL
UNION ALL
SELECT 'fsm.product_id', COUNT(*) FROM analytics.fact_stock_movements WHERE product_id IS NULL
UNION ALL
SELECT 'fsm.location_type', COUNT(*) FROM analytics.fact_stock_movements WHERE location_type IS NULL
UNION ALL
SELECT 'fsm.movement_type', COUNT(*) FROM analytics.fact_stock_movements WHERE movement_type IS NULL
UNION ALL
SELECT 'fsm.movement_reason', COUNT(*) FROM analytics.fact_stock_movements WHERE movement_reason IS NULL
UNION ALL
SELECT 'fsm.quantity_change', COUNT(*) FROM analytics.fact_stock_movements WHERE quantity_change IS NULL

UNION ALL
SELECT 'finv.snapshot_date_id', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE snapshot_date_id IS NULL
UNION ALL
SELECT 'finv.product_id', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE product_id IS NULL
UNION ALL
SELECT 'finv.location_type', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE location_type IS NULL
UNION ALL
SELECT 'finv.on_hand_qty', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE on_hand_qty IS NULL
UNION ALL
SELECT 'finv.reserved_qty', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE reserved_qty IS NULL
UNION ALL
SELECT 'finv.available_qty', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE available_qty IS NULL
UNION ALL
SELECT 'finv.in_transit_qty', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE in_transit_qty IS NULL
UNION ALL
SELECT 'finv.damaged_qty', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE damaged_qty IS NULL
UNION ALL
SELECT 'finv.reorder_point_qty', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE reorder_point_qty IS NULL
UNION ALL
SELECT 'finv.safety_stock_qty', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE safety_stock_qty IS NULL
UNION ALL
SELECT 'finv.inventory_status', COUNT(*) FROM analytics.fact_inventory_snapshot WHERE inventory_status IS NULL
ORDER BY check_name;


-- ---------------------------------------------------------
-- 5) Foreign-key integrity checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'fpo -> dim_calendar (po_date_id)' AS check_name, COUNT(*) AS bad_rows
FROM analytics.fact_purchase_orders f
LEFT JOIN analytics.dim_calendar d
    ON f.po_date_id = d.date_id
WHERE d.date_id IS NULL

UNION ALL
SELECT 'fpo -> dim_calendar (expected_receipt_date_id)', COUNT(*)
FROM analytics.fact_purchase_orders f
LEFT JOIN analytics.dim_calendar d
    ON f.expected_receipt_date_id = d.date_id
WHERE d.date_id IS NULL

UNION ALL
SELECT 'fpo -> dim_supplier', COUNT(*)
FROM analytics.fact_purchase_orders f
LEFT JOIN analytics.dim_supplier s
    ON f.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL

UNION ALL
SELECT 'fpo -> dim_warehouse', COUNT(*)
FROM analytics.fact_purchase_orders f
LEFT JOIN analytics.dim_warehouse w
    ON f.warehouse_id = w.warehouse_id
WHERE w.warehouse_id IS NULL

UNION ALL
SELECT 'fpo -> dim_product', COUNT(*)
FROM analytics.fact_purchase_orders f
LEFT JOIN analytics.dim_product p
    ON f.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL
SELECT 'fis -> fact_purchase_orders (po_line_id)', COUNT(*)
FROM analytics.fact_inbound_shipments i
LEFT JOIN analytics.fact_purchase_orders f
    ON i.po_line_id = f.po_line_id
WHERE f.po_line_id IS NULL

UNION ALL
SELECT 'fis -> dim_supplier', COUNT(*)
FROM analytics.fact_inbound_shipments i
LEFT JOIN analytics.dim_supplier s
    ON i.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL

UNION ALL
SELECT 'fis -> dim_warehouse', COUNT(*)
FROM analytics.fact_inbound_shipments i
LEFT JOIN analytics.dim_warehouse w
    ON i.warehouse_id = w.warehouse_id
WHERE w.warehouse_id IS NULL

UNION ALL
SELECT 'fis -> dim_product', COUNT(*)
FROM analytics.fact_inbound_shipments i
LEFT JOIN analytics.dim_product p
    ON i.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL
SELECT 'fsm -> dim_calendar', COUNT(*)
FROM analytics.fact_stock_movements m
LEFT JOIN analytics.dim_calendar d
    ON m.movement_date_id = d.date_id
WHERE d.date_id IS NULL

UNION ALL
SELECT 'fsm -> dim_product', COUNT(*)
FROM analytics.fact_stock_movements m
LEFT JOIN analytics.dim_product p
    ON m.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL
SELECT 'finv -> dim_calendar', COUNT(*)
FROM analytics.fact_inventory_snapshot s
LEFT JOIN analytics.dim_calendar d
    ON s.snapshot_date_id = d.date_id
WHERE d.date_id IS NULL

UNION ALL
SELECT 'finv -> dim_product', COUNT(*)
FROM analytics.fact_inventory_snapshot s
LEFT JOIN analytics.dim_product p
    ON s.product_id = p.product_id
WHERE p.product_id IS NULL
ORDER BY check_name;


-- ---------------------------------------------------------
-- 6) Business-rule checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'fpo ordered_qty <= 0' AS check_name, COUNT(*) AS bad_rows
FROM analytics.fact_purchase_orders
WHERE ordered_qty <= 0

UNION ALL
SELECT 'fpo unit_cost <= 0', COUNT(*)
FROM analytics.fact_purchase_orders
WHERE unit_cost <= 0

UNION ALL
SELECT 'fpo line_amount < 0', COUNT(*)
FROM analytics.fact_purchase_orders
WHERE line_amount < 0

UNION ALL
SELECT 'fpo expected_receipt_date_id < po_date_id', COUNT(*)
FROM analytics.fact_purchase_orders
WHERE expected_receipt_date_id < po_date_id

UNION ALL
SELECT 'fis shipped_qty < 0', COUNT(*)
FROM analytics.fact_inbound_shipments
WHERE shipped_qty < 0

UNION ALL
SELECT 'fis received_qty < 0', COUNT(*)
FROM analytics.fact_inbound_shipments
WHERE received_qty < 0

UNION ALL
SELECT 'fis rejected_qty < 0', COUNT(*)
FROM analytics.fact_inbound_shipments
WHERE rejected_qty < 0

UNION ALL
SELECT 'fis damaged_qty < 0', COUNT(*)
FROM analytics.fact_inbound_shipments
WHERE damaged_qty < 0

UNION ALL
SELECT 'fis received+rejected > shipped', COUNT(*)
FROM analytics.fact_inbound_shipments
WHERE received_qty + rejected_qty > shipped_qty

UNION ALL
SELECT 'fis actual_arrival_date_id < expected_arrival_date_id but delay_days > 0', COUNT(*)
FROM analytics.fact_inbound_shipments
WHERE actual_arrival_date_id < expected_arrival_date_id
  AND delay_days > 0

UNION ALL
SELECT 'fsm quantity_change = 0', COUNT(*)
FROM analytics.fact_stock_movements
WHERE quantity_change = 0

UNION ALL
SELECT 'finv negative on_hand_qty', COUNT(*)
FROM analytics.fact_inventory_snapshot
WHERE on_hand_qty < 0

UNION ALL
SELECT 'finv negative reserved_qty', COUNT(*)
FROM analytics.fact_inventory_snapshot
WHERE reserved_qty < 0

UNION ALL
SELECT 'finv negative available_qty', COUNT(*)
FROM analytics.fact_inventory_snapshot
WHERE available_qty < 0

UNION ALL
SELECT 'finv available_qty > on_hand_qty', COUNT(*)
FROM analytics.fact_inventory_snapshot
WHERE available_qty > on_hand_qty

UNION ALL
SELECT 'finv negative in_transit_qty', COUNT(*)
FROM analytics.fact_inventory_snapshot
WHERE in_transit_qty < 0

UNION ALL
SELECT 'finv negative damaged_qty', COUNT(*)
FROM analytics.fact_inventory_snapshot
WHERE damaged_qty < 0

UNION ALL
SELECT 'finv invalid location_type=store structure', COUNT(*)
FROM analytics.fact_inventory_snapshot
WHERE location_type = 'store'
  AND (store_id IS NULL OR warehouse_id IS NOT NULL)

UNION ALL
SELECT 'finv invalid location_type=warehouse structure', COUNT(*)
FROM analytics.fact_inventory_snapshot
WHERE location_type = 'warehouse'
  AND (warehouse_id IS NULL OR store_id IS NOT NULL)
ORDER BY check_name;


-- ---------------------------------------------------------
-- 7) Cross-table consistency checks
-- Expected: review, but usually 0 for the mismatch checks
-- ---------------------------------------------------------

-- 7A) Inbound shipment should match PO master keys
SELECT COUNT(*) AS inbound_po_key_mismatch
FROM analytics.fact_inbound_shipments i
JOIN analytics.fact_purchase_orders f
  ON i.po_line_id = f.po_line_id
WHERE i.purchase_order_id <> f.purchase_order_id
   OR i.supplier_id <> f.supplier_id
   OR i.warehouse_id <> f.warehouse_id
   OR i.product_id <> f.product_id;

-- 7B) Received qty should not exceed ordered qty
SELECT COUNT(*) AS inbound_received_gt_ordered
FROM analytics.fact_inbound_shipments i
JOIN analytics.fact_purchase_orders f
  ON i.po_line_id = f.po_line_id
WHERE i.received_qty > f.ordered_qty;

-- 7C) PO line amount should roughly equal ordered_qty * unit_cost
SELECT COUNT(*) AS po_amount_mismatch
FROM analytics.fact_purchase_orders
WHERE ABS(line_amount - ROUND(ordered_qty * unit_cost, 2)) > 0.01;


-- ---------------------------------------------------------
-- 8) Operational profile summaries
-- ---------------------------------------------------------
SELECT order_status, COUNT(*) AS row_count
FROM analytics.fact_purchase_orders
GROUP BY order_status
ORDER BY row_count DESC, order_status;

SELECT priority_level, COUNT(*) AS row_count
FROM analytics.fact_purchase_orders
GROUP BY priority_level
ORDER BY row_count DESC, priority_level;

SELECT shipment_status, COUNT(*) AS row_count
FROM analytics.fact_inbound_shipments
GROUP BY shipment_status
ORDER BY row_count DESC, shipment_status;

SELECT movement_type, COUNT(*) AS row_count
FROM analytics.fact_stock_movements
GROUP BY movement_type
ORDER BY row_count DESC, movement_type;

SELECT inventory_status, COUNT(*) AS row_count
FROM analytics.fact_inventory_snapshot
GROUP BY inventory_status
ORDER BY row_count DESC, inventory_status;

SELECT location_type, COUNT(*) AS row_count
FROM analytics.fact_inventory_snapshot
GROUP BY location_type
ORDER BY row_count DESC, location_type;


-- ---------------------------------------------------------
-- 9) Date range sanity checks
-- ---------------------------------------------------------
SELECT
    MIN(po_date_id) AS min_po_date_id,
    MAX(po_date_id) AS max_po_date_id,
    MIN(expected_receipt_date_id) AS min_expected_receipt_date_id,
    MAX(expected_receipt_date_id) AS max_expected_receipt_date_id
FROM analytics.fact_purchase_orders;

SELECT
    MIN(expected_arrival_date_id) AS min_expected_arrival_date_id,
    MAX(expected_arrival_date_id) AS max_expected_arrival_date_id,
    MIN(actual_arrival_date_id) AS min_actual_arrival_date_id,
    MAX(actual_arrival_date_id) AS max_actual_arrival_date_id
FROM analytics.fact_inbound_shipments;

SELECT
    MIN(snapshot_date_id) AS min_snapshot_date_id,
    MAX(snapshot_date_id) AS max_snapshot_date_id
FROM analytics.fact_inventory_snapshot;


-- ---------------------------------------------------------
-- 10) Ready-for-next-phase summary
-- ---------------------------------------------------------
SELECT
    (SELECT COUNT(*) FROM analytics.fact_purchase_orders)      AS fact_purchase_orders_rows,
    (SELECT COUNT(*) FROM analytics.fact_inbound_shipments)    AS fact_inbound_shipments_rows,
    (SELECT COUNT(*) FROM analytics.fact_stock_movements)      AS fact_stock_movements_rows,
    (SELECT COUNT(*) FROM analytics.fact_inventory_snapshot)   AS fact_inventory_snapshot_rows;