SET search_path TO analytics, public;

-- =========================================================
-- Phase 1.4 — validation + data quality checks
-- =========================================================

-- ---------------------------------------------------------
-- 1) Row-count validation
-- ---------------------------------------------------------
SELECT 'dim_calendar' AS table_name, COUNT(*) AS row_count FROM analytics.dim_calendar
UNION ALL
SELECT 'dim_region', COUNT(*) FROM analytics.dim_region
UNION ALL
SELECT 'dim_store', COUNT(*) FROM analytics.dim_store
UNION ALL
SELECT 'dim_warehouse', COUNT(*) FROM analytics.dim_warehouse
UNION ALL
SELECT 'dim_channel', COUNT(*) FROM analytics.dim_channel
UNION ALL
SELECT 'dim_supplier', COUNT(*) FROM analytics.dim_supplier
UNION ALL
SELECT 'dim_product', COUNT(*) FROM analytics.dim_product
UNION ALL
SELECT 'dim_customer', COUNT(*) FROM analytics.dim_customer
ORDER BY table_name;

-- ---------------------------------------------------------
-- 2) Primary key null checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'dim_calendar.date_id' AS check_name, COUNT(*) AS bad_rows
FROM analytics.dim_calendar WHERE date_id IS NULL
UNION ALL
SELECT 'dim_region.region_id', COUNT(*) FROM analytics.dim_region WHERE region_id IS NULL
UNION ALL
SELECT 'dim_store.store_id', COUNT(*) FROM analytics.dim_store WHERE store_id IS NULL
UNION ALL
SELECT 'dim_warehouse.warehouse_id', COUNT(*) FROM analytics.dim_warehouse WHERE warehouse_id IS NULL
UNION ALL
SELECT 'dim_channel.channel_id', COUNT(*) FROM analytics.dim_channel WHERE channel_id IS NULL
UNION ALL
SELECT 'dim_supplier.supplier_id', COUNT(*) FROM analytics.dim_supplier WHERE supplier_id IS NULL
UNION ALL
SELECT 'dim_product.product_id', COUNT(*) FROM analytics.dim_product WHERE product_id IS NULL
UNION ALL
SELECT 'dim_customer.customer_id', COUNT(*) FROM analytics.dim_customer WHERE customer_id IS NULL
ORDER BY check_name;

-- ---------------------------------------------------------
-- 3) Duplicate business-key checks
-- Expected: no rows returned
-- ---------------------------------------------------------
SELECT 'dim_region.region_code' AS key_name, region_code AS key_value, COUNT(*) AS dup_count
FROM analytics.dim_region
GROUP BY region_code
HAVING COUNT(*) > 1

UNION ALL

SELECT 'dim_store.store_code', store_code, COUNT(*)
FROM analytics.dim_store
GROUP BY store_code
HAVING COUNT(*) > 1

UNION ALL

SELECT 'dim_warehouse.warehouse_code', warehouse_code, COUNT(*)
FROM analytics.dim_warehouse
GROUP BY warehouse_code
HAVING COUNT(*) > 1

UNION ALL

SELECT 'dim_channel.channel_code', channel_code, COUNT(*)
FROM analytics.dim_channel
GROUP BY channel_code
HAVING COUNT(*) > 1

UNION ALL

SELECT 'dim_supplier.supplier_code', supplier_code, COUNT(*)
FROM analytics.dim_supplier
GROUP BY supplier_code
HAVING COUNT(*) > 1

UNION ALL

SELECT 'dim_product.sku_code', sku_code, COUNT(*)
FROM analytics.dim_product
GROUP BY sku_code
HAVING COUNT(*) > 1

UNION ALL

SELECT 'dim_customer.customer_code', customer_code, COUNT(*)
FROM analytics.dim_customer
GROUP BY customer_code
HAVING COUNT(*) > 1;

-- ---------------------------------------------------------
-- 4) Required-column null checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'dim_calendar.full_date' AS check_name, COUNT(*) AS bad_rows
FROM analytics.dim_calendar WHERE full_date IS NULL
UNION ALL
SELECT 'dim_calendar.day_of_week', COUNT(*) FROM analytics.dim_calendar WHERE day_of_week IS NULL
UNION ALL
SELECT 'dim_calendar.month_name', COUNT(*) FROM analytics.dim_calendar WHERE month_name IS NULL
UNION ALL
SELECT 'dim_calendar.season_name', COUNT(*) FROM analytics.dim_calendar WHERE season_name IS NULL

UNION ALL
SELECT 'dim_region.region_code', COUNT(*) FROM analytics.dim_region WHERE region_code IS NULL
UNION ALL
SELECT 'dim_region.region_name', COUNT(*) FROM analytics.dim_region WHERE region_name IS NULL

UNION ALL
SELECT 'dim_store.store_code', COUNT(*) FROM analytics.dim_store WHERE store_code IS NULL
UNION ALL
SELECT 'dim_store.store_name', COUNT(*) FROM analytics.dim_store WHERE store_name IS NULL
UNION ALL
SELECT 'dim_store.region_id', COUNT(*) FROM analytics.dim_store WHERE region_id IS NULL
UNION ALL
SELECT 'dim_store.city', COUNT(*) FROM analytics.dim_store WHERE city IS NULL

UNION ALL
SELECT 'dim_warehouse.warehouse_code', COUNT(*) FROM analytics.dim_warehouse WHERE warehouse_code IS NULL
UNION ALL
SELECT 'dim_warehouse.warehouse_name', COUNT(*) FROM analytics.dim_warehouse WHERE warehouse_name IS NULL
UNION ALL
SELECT 'dim_warehouse.region_id', COUNT(*) FROM analytics.dim_warehouse WHERE region_id IS NULL
UNION ALL
SELECT 'dim_warehouse.city', COUNT(*) FROM analytics.dim_warehouse WHERE city IS NULL

UNION ALL
SELECT 'dim_channel.channel_code', COUNT(*) FROM analytics.dim_channel WHERE channel_code IS NULL
UNION ALL
SELECT 'dim_channel.channel_name', COUNT(*) FROM analytics.dim_channel WHERE channel_name IS NULL

UNION ALL
SELECT 'dim_supplier.supplier_code', COUNT(*) FROM analytics.dim_supplier WHERE supplier_code IS NULL
UNION ALL
SELECT 'dim_supplier.supplier_name', COUNT(*) FROM analytics.dim_supplier WHERE supplier_name IS NULL
UNION ALL
SELECT 'dim_supplier.supplier_tier', COUNT(*) FROM analytics.dim_supplier WHERE supplier_tier IS NULL

UNION ALL
SELECT 'dim_product.sku_code', COUNT(*) FROM analytics.dim_product WHERE sku_code IS NULL
UNION ALL
SELECT 'dim_product.product_name', COUNT(*) FROM analytics.dim_product WHERE product_name IS NULL
UNION ALL
SELECT 'dim_product.category', COUNT(*) FROM analytics.dim_product WHERE category IS NULL
UNION ALL
SELECT 'dim_product.supplier_id', COUNT(*) FROM analytics.dim_product WHERE supplier_id IS NULL

UNION ALL
SELECT 'dim_customer.customer_code', COUNT(*) FROM analytics.dim_customer WHERE customer_code IS NULL
UNION ALL
SELECT 'dim_customer.customer_segment', COUNT(*) FROM analytics.dim_customer WHERE customer_segment IS NULL
UNION ALL
SELECT 'dim_customer.region_id', COUNT(*) FROM analytics.dim_customer WHERE region_id IS NULL
UNION ALL
SELECT 'dim_customer.preferred_channel_id', COUNT(*) FROM analytics.dim_customer WHERE preferred_channel_id IS NULL
ORDER BY check_name;

-- ---------------------------------------------------------
-- 5) Foreign-key integrity checks
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'dim_store -> dim_region' AS check_name, COUNT(*) AS bad_rows
FROM analytics.dim_store s
LEFT JOIN analytics.dim_region r
    ON s.region_id = r.region_id
WHERE r.region_id IS NULL

UNION ALL

SELECT 'dim_warehouse -> dim_region', COUNT(*)
FROM analytics.dim_warehouse w
LEFT JOIN analytics.dim_region r
    ON w.region_id = r.region_id
WHERE r.region_id IS NULL

UNION ALL

SELECT 'dim_product -> dim_supplier', COUNT(*)
FROM analytics.dim_product p
LEFT JOIN analytics.dim_supplier s
    ON p.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL

UNION ALL

SELECT 'dim_customer -> dim_region', COUNT(*)
FROM analytics.dim_customer c
LEFT JOIN analytics.dim_region r
    ON c.region_id = r.region_id
WHERE r.region_id IS NULL

UNION ALL

SELECT 'dim_customer -> dim_channel', COUNT(*)
FROM analytics.dim_customer c
LEFT JOIN analytics.dim_channel ch
    ON c.preferred_channel_id = ch.channel_id
WHERE ch.channel_id IS NULL
ORDER BY check_name;

-- ---------------------------------------------------------
-- 6) Business-rule validation
-- Expected: all 0
-- ---------------------------------------------------------
SELECT 'dim_product list_price <= unit_cost' AS check_name, COUNT(*) AS bad_rows
FROM analytics.dim_product
WHERE list_price <= unit_cost

UNION ALL

SELECT 'dim_product reorder_point_default < 0', COUNT(*)
FROM analytics.dim_product
WHERE reorder_point_default < 0

UNION ALL

SELECT 'dim_product safety_stock_default < 0', COUNT(*)
FROM analytics.dim_product
WHERE safety_stock_default < 0

UNION ALL

SELECT 'dim_supplier lead_time_days_avg <= 0', COUNT(*)
FROM analytics.dim_supplier
WHERE lead_time_days_avg <= 0

UNION ALL

SELECT 'dim_supplier on_time_rate outside 0-100', COUNT(*)
FROM analytics.dim_supplier
WHERE on_time_rate < 0 OR on_time_rate > 100

UNION ALL

SELECT 'dim_supplier quality_score outside 0-100', COUNT(*)
FROM analytics.dim_supplier
WHERE quality_score < 0 OR quality_score > 100

UNION ALL

SELECT 'dim_supplier contract_end_date < contract_start_date', COUNT(*)
FROM analytics.dim_supplier
WHERE contract_end_date < contract_start_date

UNION ALL

SELECT 'dim_calendar week_of_year outside 1-53', COUNT(*)
FROM analytics.dim_calendar
WHERE week_of_year < 1 OR week_of_year > 53

UNION ALL

SELECT 'dim_calendar month outside 1-12', COUNT(*)
FROM analytics.dim_calendar
WHERE month < 1 OR month > 12

UNION ALL

SELECT 'dim_calendar quarter outside 1-4', COUNT(*)
FROM analytics.dim_calendar
WHERE quarter < 1 OR quarter > 4
ORDER BY check_name;

-- ---------------------------------------------------------
-- 7) Calendar continuity check
-- Expected: 0 missing dates
-- ---------------------------------------------------------
WITH expected_dates AS (
    SELECT generate_series(
        (SELECT MIN(full_date) FROM analytics.dim_calendar),
        (SELECT MAX(full_date) FROM analytics.dim_calendar),
        interval '1 day'
    )::date AS full_date
)
SELECT COUNT(*) AS missing_calendar_dates
FROM expected_dates e
LEFT JOIN analytics.dim_calendar c
    ON e.full_date = c.full_date
WHERE c.full_date IS NULL;

-- ---------------------------------------------------------
-- 8) Basic profile summaries for sanity check
-- ---------------------------------------------------------
SELECT category, COUNT(*) AS product_count
FROM analytics.dim_product
GROUP BY category
ORDER BY product_count DESC, category;

SELECT supplier_tier, COUNT(*) AS supplier_count
FROM analytics.dim_supplier
GROUP BY supplier_tier
ORDER BY supplier_count DESC, supplier_tier;

SELECT customer_segment, COUNT(*) AS customer_count
FROM analytics.dim_customer
GROUP BY customer_segment
ORDER BY customer_count DESC, customer_segment;

SELECT loyalty_tier, COUNT(*) AS customer_count
FROM analytics.dim_customer
GROUP BY loyalty_tier
ORDER BY customer_count DESC, loyalty_tier;

SELECT channel_name, COUNT(*) AS channel_count
FROM analytics.dim_channel
GROUP BY channel_name
ORDER BY channel_name;

SELECT region_name, COUNT(*) AS store_count
FROM analytics.dim_store s
JOIN analytics.dim_region r
    ON s.region_id = r.region_id
GROUP BY region_name
ORDER BY region_name;

SELECT region_name, COUNT(*) AS warehouse_count
FROM analytics.dim_warehouse w
JOIN analytics.dim_region r
    ON w.region_id = r.region_id
GROUP BY region_name
ORDER BY region_name;

-- ---------------------------------------------------------
-- 9) Ready-for-facts summary
-- ---------------------------------------------------------
SELECT
    (SELECT COUNT(*) FROM analytics.dim_calendar)   AS dim_calendar_rows,
    (SELECT COUNT(*) FROM analytics.dim_region)     AS dim_region_rows,
    (SELECT COUNT(*) FROM analytics.dim_store)      AS dim_store_rows,
    (SELECT COUNT(*) FROM analytics.dim_warehouse)  AS dim_warehouse_rows,
    (SELECT COUNT(*) FROM analytics.dim_channel)    AS dim_channel_rows,
    (SELECT COUNT(*) FROM analytics.dim_supplier)   AS dim_supplier_rows,
    (SELECT COUNT(*) FROM analytics.dim_product)    AS dim_product_rows,
    (SELECT COUNT(*) FROM analytics.dim_customer)   AS dim_customer_rows;