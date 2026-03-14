SET search_path TO analytics, public;

-- =========================================================
-- Phase 2 — Sales / Commercial Fact Validation Checks
-- EDIP / NorthStar Retail & Distribution
-- Scope:
--   fact_orders
--   fact_order_items
--   fact_sales
--   fact_returns
-- =========================================================

-- ---------------------------------------------------------
-- 1) Row counts
-- ---------------------------------------------------------
SELECT 'fact_orders' AS table_name, COUNT(*) AS row_count
FROM analytics.fact_orders
UNION ALL
SELECT 'fact_order_items', COUNT(*)
FROM analytics.fact_order_items
UNION ALL
SELECT 'fact_sales', COUNT(*)
FROM analytics.fact_sales
UNION ALL
SELECT 'fact_returns', COUNT(*)
FROM analytics.fact_returns
ORDER BY table_name;


-- ---------------------------------------------------------
-- 2) Primary key null checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'fact_orders.order_id' AS check_name, COUNT(*) AS bad_rows
FROM analytics.fact_orders
WHERE order_id IS NULL

UNION ALL
SELECT 'fact_order_items.order_item_id', COUNT(*)
FROM analytics.fact_order_items
WHERE order_item_id IS NULL

UNION ALL
SELECT 'fact_sales.sale_id', COUNT(*)
FROM analytics.fact_sales
WHERE sale_id IS NULL

UNION ALL
SELECT 'fact_returns.return_id', COUNT(*)
FROM analytics.fact_returns
WHERE return_id IS NULL
ORDER BY check_name;


-- ---------------------------------------------------------
-- 3) Duplicate grain checks
-- Expected:
--   order duplicate grain = 0 rows
--   order-item duplicate grain = 0 rows
--   sales duplicate grain = 0 rows
--   returns duplicate grain = 0 rows
-- ---------------------------------------------------------

-- 3A) order header duplicate business grain
SELECT
    order_number,
    COUNT(*) AS dup_count
FROM analytics.fact_orders
GROUP BY order_number
HAVING COUNT(*) > 1;

-- 3B) order-item duplicate grain
SELECT
    order_id,
    order_line_number,
    COUNT(*) AS dup_count
FROM analytics.fact_order_items
GROUP BY order_id, order_line_number
HAVING COUNT(*) > 1;

-- 3C) sales duplicate grain
SELECT
    order_item_id,
    COUNT(*) AS dup_count
FROM analytics.fact_sales
GROUP BY order_item_id
HAVING COUNT(*) > 1;

-- 3D) returns duplicate grain
SELECT
    sale_id,
    COUNT(*) AS dup_count
FROM analytics.fact_returns
GROUP BY sale_id
HAVING COUNT(*) > 1;


-- ---------------------------------------------------------
-- 4) Required-column null checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'fo.order_number' AS check_name, COUNT(*) AS bad_rows
FROM analytics.fact_orders
WHERE order_number IS NULL

UNION ALL
SELECT 'fo.order_date_id', COUNT(*) FROM analytics.fact_orders WHERE order_date_id IS NULL
UNION ALL
SELECT 'fo.customer_id', COUNT(*) FROM analytics.fact_orders WHERE customer_id IS NULL
UNION ALL
SELECT 'fo.channel_id', COUNT(*) FROM analytics.fact_orders WHERE channel_id IS NULL
UNION ALL
SELECT 'fo.region_id', COUNT(*) FROM analytics.fact_orders WHERE region_id IS NULL
UNION ALL
SELECT 'fo.order_status', COUNT(*) FROM analytics.fact_orders WHERE order_status IS NULL
UNION ALL
SELECT 'fo.payment_status', COUNT(*) FROM analytics.fact_orders WHERE payment_status IS NULL
UNION ALL
SELECT 'fo.fulfillment_type', COUNT(*) FROM analytics.fact_orders WHERE fulfillment_type IS NULL
UNION ALL
SELECT 'fo.item_count', COUNT(*) FROM analytics.fact_orders WHERE item_count IS NULL
UNION ALL
SELECT 'fo.total_units', COUNT(*) FROM analytics.fact_orders WHERE total_units IS NULL
UNION ALL
SELECT 'fo.gross_order_amount', COUNT(*) FROM analytics.fact_orders WHERE gross_order_amount IS NULL
UNION ALL
SELECT 'fo.discount_amount', COUNT(*) FROM analytics.fact_orders WHERE discount_amount IS NULL
UNION ALL
SELECT 'fo.shipping_fee', COUNT(*) FROM analytics.fact_orders WHERE shipping_fee IS NULL
UNION ALL
SELECT 'fo.tax_amount', COUNT(*) FROM analytics.fact_orders WHERE tax_amount IS NULL
UNION ALL
SELECT 'fo.net_order_amount', COUNT(*) FROM analytics.fact_orders WHERE net_order_amount IS NULL
UNION ALL
SELECT 'fo.currency_code', COUNT(*) FROM analytics.fact_orders WHERE currency_code IS NULL

UNION ALL
SELECT 'foi.order_id', COUNT(*) FROM analytics.fact_order_items WHERE order_id IS NULL
UNION ALL
SELECT 'foi.order_line_number', COUNT(*) FROM analytics.fact_order_items WHERE order_line_number IS NULL
UNION ALL
SELECT 'foi.order_date_id', COUNT(*) FROM analytics.fact_order_items WHERE order_date_id IS NULL
UNION ALL
SELECT 'foi.customer_id', COUNT(*) FROM analytics.fact_order_items WHERE customer_id IS NULL
UNION ALL
SELECT 'foi.channel_id', COUNT(*) FROM analytics.fact_order_items WHERE channel_id IS NULL
UNION ALL
SELECT 'foi.region_id', COUNT(*) FROM analytics.fact_order_items WHERE region_id IS NULL
UNION ALL
SELECT 'foi.product_id', COUNT(*) FROM analytics.fact_order_items WHERE product_id IS NULL
UNION ALL
SELECT 'foi.ordered_qty', COUNT(*) FROM analytics.fact_order_items WHERE ordered_qty IS NULL
UNION ALL
SELECT 'foi.allocated_qty', COUNT(*) FROM analytics.fact_order_items WHERE allocated_qty IS NULL
UNION ALL
SELECT 'foi.fulfilled_qty', COUNT(*) FROM analytics.fact_order_items WHERE fulfilled_qty IS NULL
UNION ALL
SELECT 'foi.cancelled_qty', COUNT(*) FROM analytics.fact_order_items WHERE cancelled_qty IS NULL
UNION ALL
SELECT 'foi.unit_list_price', COUNT(*) FROM analytics.fact_order_items WHERE unit_list_price IS NULL
UNION ALL
SELECT 'foi.unit_selling_price', COUNT(*) FROM analytics.fact_order_items WHERE unit_selling_price IS NULL
UNION ALL
SELECT 'foi.line_discount_amount', COUNT(*) FROM analytics.fact_order_items WHERE line_discount_amount IS NULL
UNION ALL
SELECT 'foi.gross_line_amount', COUNT(*) FROM analytics.fact_order_items WHERE gross_line_amount IS NULL
UNION ALL
SELECT 'foi.net_line_amount', COUNT(*) FROM analytics.fact_order_items WHERE net_line_amount IS NULL
UNION ALL
SELECT 'foi.stockout_flag', COUNT(*) FROM analytics.fact_order_items WHERE stockout_flag IS NULL
UNION ALL
SELECT 'foi.item_status', COUNT(*) FROM analytics.fact_order_items WHERE item_status IS NULL

UNION ALL
SELECT 'fs.sale_date_id', COUNT(*) FROM analytics.fact_sales WHERE sale_date_id IS NULL
UNION ALL
SELECT 'fs.order_id', COUNT(*) FROM analytics.fact_sales WHERE order_id IS NULL
UNION ALL
SELECT 'fs.order_item_id', COUNT(*) FROM analytics.fact_sales WHERE order_item_id IS NULL
UNION ALL
SELECT 'fs.customer_id', COUNT(*) FROM analytics.fact_sales WHERE customer_id IS NULL
UNION ALL
SELECT 'fs.channel_id', COUNT(*) FROM analytics.fact_sales WHERE channel_id IS NULL
UNION ALL
SELECT 'fs.region_id', COUNT(*) FROM analytics.fact_sales WHERE region_id IS NULL
UNION ALL
SELECT 'fs.product_id', COUNT(*) FROM analytics.fact_sales WHERE product_id IS NULL
UNION ALL
SELECT 'fs.units_sold', COUNT(*) FROM analytics.fact_sales WHERE units_sold IS NULL
UNION ALL
SELECT 'fs.unit_list_price', COUNT(*) FROM analytics.fact_sales WHERE unit_list_price IS NULL
UNION ALL
SELECT 'fs.unit_selling_price', COUNT(*) FROM analytics.fact_sales WHERE unit_selling_price IS NULL
UNION ALL
SELECT 'fs.gross_sales_amount', COUNT(*) FROM analytics.fact_sales WHERE gross_sales_amount IS NULL
UNION ALL
SELECT 'fs.discount_amount', COUNT(*) FROM analytics.fact_sales WHERE discount_amount IS NULL
UNION ALL
SELECT 'fs.net_sales_amount', COUNT(*) FROM analytics.fact_sales WHERE net_sales_amount IS NULL
UNION ALL
SELECT 'fs.unit_cost', COUNT(*) FROM analytics.fact_sales WHERE unit_cost IS NULL
UNION ALL
SELECT 'fs.gross_margin_amount', COUNT(*) FROM analytics.fact_sales WHERE gross_margin_amount IS NULL
UNION ALL
SELECT 'fs.fulfillment_type', COUNT(*) FROM analytics.fact_sales WHERE fulfillment_type IS NULL
UNION ALL
SELECT 'fs.sale_status', COUNT(*) FROM analytics.fact_sales WHERE sale_status IS NULL

UNION ALL
SELECT 'fr.sale_id', COUNT(*) FROM analytics.fact_returns WHERE sale_id IS NULL
UNION ALL
SELECT 'fr.order_id', COUNT(*) FROM analytics.fact_returns WHERE order_id IS NULL
UNION ALL
SELECT 'fr.order_item_id', COUNT(*) FROM analytics.fact_returns WHERE order_item_id IS NULL
UNION ALL
SELECT 'fr.return_date_id', COUNT(*) FROM analytics.fact_returns WHERE return_date_id IS NULL
UNION ALL
SELECT 'fr.customer_id', COUNT(*) FROM analytics.fact_returns WHERE customer_id IS NULL
UNION ALL
SELECT 'fr.channel_id', COUNT(*) FROM analytics.fact_returns WHERE channel_id IS NULL
UNION ALL
SELECT 'fr.region_id', COUNT(*) FROM analytics.fact_returns WHERE region_id IS NULL
UNION ALL
SELECT 'fr.product_id', COUNT(*) FROM analytics.fact_returns WHERE product_id IS NULL
UNION ALL
SELECT 'fr.returned_qty', COUNT(*) FROM analytics.fact_returns WHERE returned_qty IS NULL
UNION ALL
SELECT 'fr.return_reason', COUNT(*) FROM analytics.fact_returns WHERE return_reason IS NULL
UNION ALL
SELECT 'fr.return_status', COUNT(*) FROM analytics.fact_returns WHERE return_status IS NULL
UNION ALL
SELECT 'fr.refund_amount', COUNT(*) FROM analytics.fact_returns WHERE refund_amount IS NULL
UNION ALL
SELECT 'fr.restockable_flag', COUNT(*) FROM analytics.fact_returns WHERE restockable_flag IS NULL
UNION ALL
SELECT 'fr.damaged_flag', COUNT(*) FROM analytics.fact_returns WHERE damaged_flag IS NULL
UNION ALL
SELECT 'fr.inventory_disposition', COUNT(*) FROM analytics.fact_returns WHERE inventory_disposition IS NULL
ORDER BY check_name;


-- ---------------------------------------------------------
-- 5) Foreign-key integrity checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'fo -> dim_calendar' AS check_name, COUNT(*) AS bad_rows
FROM analytics.fact_orders o
LEFT JOIN analytics.dim_calendar d
    ON o.order_date_id = d.date_id
WHERE d.date_id IS NULL

UNION ALL
SELECT 'fo -> dim_customer', COUNT(*)
FROM analytics.fact_orders o
LEFT JOIN analytics.dim_customer c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL
SELECT 'fo -> dim_channel', COUNT(*)
FROM analytics.fact_orders o
LEFT JOIN analytics.dim_channel ch
    ON o.channel_id = ch.channel_id
WHERE ch.channel_id IS NULL

UNION ALL
SELECT 'fo -> dim_region', COUNT(*)
FROM analytics.fact_orders o
LEFT JOIN analytics.dim_region r
    ON o.region_id = r.region_id
WHERE r.region_id IS NULL

UNION ALL
SELECT 'foi -> fact_orders', COUNT(*)
FROM analytics.fact_order_items i
LEFT JOIN analytics.fact_orders o
    ON i.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL
SELECT 'foi -> dim_calendar', COUNT(*)
FROM analytics.fact_order_items i
LEFT JOIN analytics.dim_calendar d
    ON i.order_date_id = d.date_id
WHERE d.date_id IS NULL

UNION ALL
SELECT 'foi -> dim_customer', COUNT(*)
FROM analytics.fact_order_items i
LEFT JOIN analytics.dim_customer c
    ON i.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL
SELECT 'foi -> dim_channel', COUNT(*)
FROM analytics.fact_order_items i
LEFT JOIN analytics.dim_channel ch
    ON i.channel_id = ch.channel_id
WHERE ch.channel_id IS NULL

UNION ALL
SELECT 'foi -> dim_region', COUNT(*)
FROM analytics.fact_order_items i
LEFT JOIN analytics.dim_region r
    ON i.region_id = r.region_id
WHERE r.region_id IS NULL

UNION ALL
SELECT 'foi -> dim_product', COUNT(*)
FROM analytics.fact_order_items i
LEFT JOIN analytics.dim_product p
    ON i.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL
SELECT 'fs -> fact_orders', COUNT(*)
FROM analytics.fact_sales s
LEFT JOIN analytics.fact_orders o
    ON s.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL
SELECT 'fs -> fact_order_items', COUNT(*)
FROM analytics.fact_sales s
LEFT JOIN analytics.fact_order_items i
    ON s.order_item_id = i.order_item_id
WHERE i.order_item_id IS NULL

UNION ALL
SELECT 'fs -> dim_calendar', COUNT(*)
FROM analytics.fact_sales s
LEFT JOIN analytics.dim_calendar d
    ON s.sale_date_id = d.date_id
WHERE d.date_id IS NULL

UNION ALL
SELECT 'fs -> dim_customer', COUNT(*)
FROM analytics.fact_sales s
LEFT JOIN analytics.dim_customer c
    ON s.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL
SELECT 'fs -> dim_channel', COUNT(*)
FROM analytics.fact_sales s
LEFT JOIN analytics.dim_channel ch
    ON s.channel_id = ch.channel_id
WHERE ch.channel_id IS NULL

UNION ALL
SELECT 'fs -> dim_region', COUNT(*)
FROM analytics.fact_sales s
LEFT JOIN analytics.dim_region r
    ON s.region_id = r.region_id
WHERE r.region_id IS NULL

UNION ALL
SELECT 'fs -> dim_product', COUNT(*)
FROM analytics.fact_sales s
LEFT JOIN analytics.dim_product p
    ON s.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL
SELECT 'fr -> fact_sales', COUNT(*)
FROM analytics.fact_returns rt
LEFT JOIN analytics.fact_sales s
    ON rt.sale_id = s.sale_id
WHERE s.sale_id IS NULL

UNION ALL
SELECT 'fr -> fact_orders', COUNT(*)
FROM analytics.fact_returns rt
LEFT JOIN analytics.fact_orders o
    ON rt.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL
SELECT 'fr -> fact_order_items', COUNT(*)
FROM analytics.fact_returns rt
LEFT JOIN analytics.fact_order_items i
    ON rt.order_item_id = i.order_item_id
WHERE i.order_item_id IS NULL

UNION ALL
SELECT 'fr -> dim_calendar', COUNT(*)
FROM analytics.fact_returns rt
LEFT JOIN analytics.dim_calendar d
    ON rt.return_date_id = d.date_id
WHERE d.date_id IS NULL

UNION ALL
SELECT 'fr -> dim_customer', COUNT(*)
FROM analytics.fact_returns rt
LEFT JOIN analytics.dim_customer c
    ON rt.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL
SELECT 'fr -> dim_channel', COUNT(*)
FROM analytics.fact_returns rt
LEFT JOIN analytics.dim_channel ch
    ON rt.channel_id = ch.channel_id
WHERE ch.channel_id IS NULL

UNION ALL
SELECT 'fr -> dim_region', COUNT(*)
FROM analytics.fact_returns rt
LEFT JOIN analytics.dim_region r
    ON rt.region_id = r.region_id
WHERE r.region_id IS NULL

UNION ALL
SELECT 'fr -> dim_product', COUNT(*)
FROM analytics.fact_returns rt
LEFT JOIN analytics.dim_product p
    ON rt.product_id = p.product_id
WHERE p.product_id IS NULL
ORDER BY check_name;


-- ---------------------------------------------------------
-- 6) Business-rule checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'fo gross_order_amount < 0' AS check_name, COUNT(*) AS bad_rows
FROM analytics.fact_orders
WHERE gross_order_amount < 0

UNION ALL
SELECT 'fo discount_amount < 0', COUNT(*) FROM analytics.fact_orders WHERE discount_amount < 0
UNION ALL
SELECT 'fo net_order_amount < 0', COUNT(*) FROM analytics.fact_orders WHERE net_order_amount < 0
UNION ALL
SELECT 'fo shipping_fee < 0', COUNT(*) FROM analytics.fact_orders WHERE shipping_fee < 0
UNION ALL
SELECT 'fo tax_amount < 0', COUNT(*) FROM analytics.fact_orders WHERE tax_amount < 0
UNION ALL
SELECT 'fo total_units <= 0', COUNT(*) FROM analytics.fact_orders WHERE total_units <= 0
UNION ALL
SELECT 'fo item_count <= 0', COUNT(*) FROM analytics.fact_orders WHERE item_count <= 0

UNION ALL
SELECT 'foi ordered_qty <= 0', COUNT(*) FROM analytics.fact_order_items WHERE ordered_qty <= 0
UNION ALL
SELECT 'foi allocated_qty < 0', COUNT(*) FROM analytics.fact_order_items WHERE allocated_qty < 0
UNION ALL
SELECT 'foi fulfilled_qty < 0', COUNT(*) FROM analytics.fact_order_items WHERE fulfilled_qty < 0
UNION ALL
SELECT 'foi cancelled_qty < 0', COUNT(*) FROM analytics.fact_order_items WHERE cancelled_qty < 0
UNION ALL
SELECT 'foi allocated_qty > ordered_qty', COUNT(*)
FROM analytics.fact_order_items
WHERE allocated_qty > ordered_qty
UNION ALL
SELECT 'foi fulfilled_qty > ordered_qty', COUNT(*)
FROM analytics.fact_order_items
WHERE fulfilled_qty > ordered_qty
UNION ALL
SELECT 'foi cancelled_qty > ordered_qty', COUNT(*)
FROM analytics.fact_order_items
WHERE cancelled_qty > ordered_qty
UNION ALL
SELECT 'foi allocated+cancelled != ordered', COUNT(*)
FROM analytics.fact_order_items
WHERE allocated_qty + cancelled_qty <> ordered_qty
UNION ALL
SELECT 'foi gross_line_amount < 0', COUNT(*)
FROM analytics.fact_order_items
WHERE gross_line_amount < 0
UNION ALL
SELECT 'foi line_discount_amount < 0', COUNT(*)
FROM analytics.fact_order_items
WHERE line_discount_amount < 0
UNION ALL
SELECT 'foi net_line_amount < 0', COUNT(*)
FROM analytics.fact_order_items
WHERE net_line_amount < 0
UNION ALL
SELECT 'foi unit prices < 0', COUNT(*)
FROM analytics.fact_order_items
WHERE unit_list_price < 0 OR unit_selling_price < 0

UNION ALL
SELECT 'fs units_sold <= 0', COUNT(*) FROM analytics.fact_sales WHERE units_sold <= 0
UNION ALL
SELECT 'fs gross_sales_amount < 0', COUNT(*) FROM analytics.fact_sales WHERE gross_sales_amount < 0
UNION ALL
SELECT 'fs discount_amount < 0', COUNT(*) FROM analytics.fact_sales WHERE discount_amount < 0
UNION ALL
SELECT 'fs net_sales_amount < 0', COUNT(*) FROM analytics.fact_sales WHERE net_sales_amount < 0

UNION ALL
SELECT 'fr returned_qty <= 0', COUNT(*) FROM analytics.fact_returns WHERE returned_qty <= 0
UNION ALL
SELECT 'fr refund_amount < 0', COUNT(*) FROM analytics.fact_returns WHERE refund_amount < 0
ORDER BY check_name;


-- ---------------------------------------------------------
-- 7) Cross-table consistency checks
-- Expected: all 0
-- ---------------------------------------------------------

-- 7A) order header totals vs line totals
-- Note:
-- gross_order_amount and total_units are based on ordered quantities,
-- while line discount/net are based on fulfilled quantities.
-- So compare only the fields that are truly aggregated at header level.
SELECT COUNT(*) AS order_header_amount_mismatch
FROM (
    SELECT
        o.order_id,
        o.gross_order_amount,
        o.discount_amount,
        o.item_count,
        o.total_units,
        ROUND(COALESCE(SUM(i.gross_line_amount), 0), 2) AS calc_gross_order_amount,
        ROUND(COALESCE(SUM(i.line_discount_amount), 0), 2) AS calc_discount_amount,
        COUNT(i.order_item_id) AS calc_item_count,
        COALESCE(SUM(i.ordered_qty), 0) AS calc_total_units
    FROM analytics.fact_orders o
    LEFT JOIN analytics.fact_order_items i
        ON o.order_id = i.order_id
    GROUP BY
        o.order_id,
        o.gross_order_amount,
        o.discount_amount,
        o.item_count,
        o.total_units
) t
WHERE ABS(gross_order_amount - calc_gross_order_amount) > 0.01
   OR ABS(discount_amount - calc_discount_amount) > 0.01
   OR item_count <> calc_item_count
   OR total_units <> calc_total_units;

-- 7B) payment failed orders should not have sales
SELECT COUNT(*) AS failed_payment_with_sales
FROM analytics.fact_orders o
JOIN analytics.fact_sales s
    ON o.order_id = s.order_id
WHERE LOWER(o.payment_status) = 'failed';

-- 7C) cancelled orders should not have sales
SELECT COUNT(*) AS cancelled_order_with_sales
FROM analytics.fact_orders o
JOIN analytics.fact_sales s
    ON o.order_id = s.order_id
WHERE LOWER(o.order_status) = 'cancelled';

-- 7D) stockout order lines should not have fulfilled sales
SELECT COUNT(*) AS stockout_with_sales
FROM analytics.fact_order_items i
JOIN analytics.fact_sales s
    ON i.order_item_id = s.order_item_id
WHERE LOWER(i.item_status) = 'stockout';

-- 7E) item-level sales qty must equal fulfilled qty
SELECT COUNT(*) AS fulfilled_sales_qty_mismatch
FROM analytics.fact_order_items i
JOIN analytics.fact_sales s
    ON i.order_item_id = s.order_item_id
WHERE i.fulfilled_qty <> s.units_sold;

-- 7F) sales amounts must match units * price
SELECT COUNT(*) AS sales_amount_mismatch
FROM analytics.fact_sales
WHERE ABS(gross_sales_amount - ROUND(units_sold * unit_list_price, 2)) > 0.01
   OR ABS(net_sales_amount - ROUND(gross_sales_amount - discount_amount, 2)) > 0.01;

-- 7G) order-item amounts must match qty / price logic
SELECT COUNT(*) AS order_item_amount_mismatch
FROM analytics.fact_order_items
WHERE ABS(gross_line_amount - ROUND(ordered_qty * unit_list_price, 2)) > 0.01
   OR ABS(net_line_amount - ROUND((fulfilled_qty * unit_selling_price) - line_discount_amount, 2)) > 0.01;

-- 7H) return qty cannot exceed sold qty
SELECT COUNT(*) AS return_qty_gt_units_sold
FROM analytics.fact_returns r
JOIN analytics.fact_sales s
    ON r.sale_id = s.sale_id
WHERE r.returned_qty > s.units_sold;

-- 7I) return records must match product/order/customer of sale
SELECT COUNT(*) AS return_sale_key_mismatch
FROM analytics.fact_returns r
JOIN analytics.fact_sales s
    ON r.sale_id = s.sale_id
WHERE r.order_id <> s.order_id
   OR r.order_item_id <> s.order_item_id
   OR r.customer_id <> s.customer_id
   OR r.product_id <> s.product_id
   OR r.channel_id <> s.channel_id
   OR r.region_id <> s.region_id;

-- 7J) return date should be on or after sale date
SELECT COUNT(*) AS return_before_sale
FROM analytics.fact_returns r
JOIN analytics.fact_sales s
    ON r.sale_id = s.sale_id
WHERE r.return_date_id < s.sale_date_id;

-- 7K) returns should exist only for fulfilled / sold lines
SELECT COUNT(*) AS return_without_fulfilled_line
FROM analytics.fact_returns r
JOIN analytics.fact_order_items i
    ON r.order_item_id = i.order_item_id
WHERE i.fulfilled_qty <= 0;

-- 7L) order header payment / status logic
SELECT COUNT(*) AS invalid_order_status_logic
FROM analytics.fact_orders
WHERE (LOWER(payment_status) = 'failed' AND LOWER(order_status) NOT IN ('cancelled', 'confirmed'))
   OR (LOWER(payment_status) = 'paid' AND LOWER(order_status) = 'cancelled' AND net_order_amount > 0);

-- 7M) order header location logic
-- pickup_in_store should have a store_id;
-- non-pickup flows should not force a store_id.
SELECT COUNT(*) AS invalid_order_location_logic
FROM analytics.fact_orders
WHERE (LOWER(fulfillment_type) = 'pickup_in_store' AND store_id IS NULL)
   OR (LOWER(fulfillment_type) <> 'pickup_in_store' AND store_id IS NOT NULL);

-- 7N) line-level location logic
SELECT COUNT(*) AS invalid_order_item_location_logic
FROM analytics.fact_order_items
WHERE (store_id IS NULL AND warehouse_id IS NULL)
   OR (store_id IS NOT NULL AND warehouse_id IS NOT NULL);

-- 7O) sales-level location logic
SELECT COUNT(*) AS invalid_sales_location_logic
FROM analytics.fact_sales
WHERE (store_id IS NULL AND warehouse_id IS NULL)
   OR (store_id IS NOT NULL AND warehouse_id IS NOT NULL);

-- 7P) returns-level location logic
SELECT COUNT(*) AS invalid_returns_location_logic
FROM analytics.fact_returns
WHERE (store_id IS NULL AND warehouse_id IS NULL)
   OR (store_id IS NOT NULL AND warehouse_id IS NOT NULL);


-- ---------------------------------------------------------
-- 8) Operational profile summaries
-- ---------------------------------------------------------
SELECT order_status, COUNT(*) AS row_count
FROM analytics.fact_orders
GROUP BY order_status
ORDER BY row_count DESC, order_status;

SELECT payment_status, COUNT(*) AS row_count
FROM analytics.fact_orders
GROUP BY payment_status
ORDER BY row_count DESC, payment_status;

SELECT item_status, COUNT(*) AS row_count
FROM analytics.fact_order_items
GROUP BY item_status
ORDER BY row_count DESC, item_status;

SELECT channel_id, COUNT(*) AS row_count
FROM analytics.fact_orders
GROUP BY channel_id
ORDER BY row_count DESC, channel_id;

SELECT return_reason, COUNT(*) AS row_count
FROM analytics.fact_returns
GROUP BY return_reason
ORDER BY row_count DESC, return_reason;

SELECT
    ROUND(100.0 * SUM(CASE WHEN stockout_flag THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS stockout_line_pct
FROM analytics.fact_order_items;


-- ---------------------------------------------------------
-- 9) Date range sanity checks
-- ---------------------------------------------------------
SELECT
    MIN(order_date_id) AS min_order_date_id,
    MAX(order_date_id) AS max_order_date_id
FROM analytics.fact_orders;

SELECT
    MIN(order_date_id) AS min_order_item_date_id,
    MAX(order_date_id) AS max_order_item_date_id
FROM analytics.fact_order_items;

SELECT
    MIN(sale_date_id) AS min_sale_date_id,
    MAX(sale_date_id) AS max_sale_date_id
FROM analytics.fact_sales;

SELECT
    MIN(return_date_id) AS min_return_date_id,
    MAX(return_date_id) AS max_return_date_id
FROM analytics.fact_returns;


-- ---------------------------------------------------------
-- 10) Ready-for-next-phase summary
-- ---------------------------------------------------------
SELECT
    (SELECT COUNT(*) FROM analytics.fact_orders)      AS fact_orders_rows,
    (SELECT COUNT(*) FROM analytics.fact_order_items) AS fact_order_items_rows,
    (SELECT COUNT(*) FROM analytics.fact_sales)       AS fact_sales_rows,
    (SELECT COUNT(*) FROM analytics.fact_returns)     AS fact_returns_rows;