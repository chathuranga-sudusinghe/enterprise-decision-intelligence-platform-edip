SET search_path TO analytics, public;

-- =========================================================
-- Phase 3.1C — Forecast + Replenishment Validation Checks
-- EDIP / NorthStar Retail & Distribution
-- File: 10_phase_3_forecast_replenishment_validation.sql
-- =========================================================


-- =========================================================
-- 1) Row count check
-- =========================================================
SELECT 'fact_demand_forecast' AS check_name, COUNT(*) AS row_count
FROM analytics.fact_demand_forecast

UNION ALL

SELECT 'fact_replenishment_recommendation' AS check_name, COUNT(*) AS row_count
FROM analytics.fact_replenishment_recommendation;


-- =========================================================
-- 2) Required NULL check — forecast table
-- =========================================================
SELECT
    COUNT(*) AS invalid_required_null_rows
FROM analytics.fact_demand_forecast
WHERE forecast_id IS NULL
   OR forecast_run_id IS NULL
   OR forecast_date_id IS NULL
   OR target_date_id IS NULL
   OR product_id IS NULL
   OR region_id IS NULL
   OR forecast_units IS NULL
   OR forecast_lower_bound IS NULL
   OR forecast_upper_bound IS NULL
   OR model_name IS NULL
   OR model_version IS NULL
   OR confidence_score IS NULL
   OR created_timestamp IS NULL;


-- =========================================================
-- 3) Required NULL check — replenishment table
-- =========================================================
SELECT
    COUNT(*) AS invalid_required_null_rows
FROM analytics.fact_replenishment_recommendation
WHERE recommendation_id IS NULL
   OR forecast_run_id IS NULL
   OR recommendation_date_id IS NULL
   OR product_id IS NULL
   OR recommended_order_qty IS NULL
   OR recommended_transfer_qty IS NULL
   OR priority_level IS NULL
   OR reason_code IS NULL
   OR expected_stockout_risk IS NULL
   OR expected_service_level IS NULL
   OR approval_status IS NULL
   OR created_timestamp IS NULL;


-- =========================================================
-- 4) Forecast date logic check
-- target_date_id must be >= forecast_date_id
-- =========================================================
SELECT
    COUNT(*) AS invalid_date_logic_rows
FROM analytics.fact_demand_forecast
WHERE target_date_id < forecast_date_id;


-- =========================================================
-- 5) Forecast non-negative measure check
-- =========================================================
SELECT
    COUNT(*) AS invalid_negative_forecast_rows
FROM analytics.fact_demand_forecast
WHERE forecast_units < 0
   OR forecast_lower_bound < 0
   OR forecast_upper_bound < 0;


-- =========================================================
-- 6) Forecast interval logic check
-- lower <= forecast <= upper
-- =========================================================
SELECT
    COUNT(*) AS invalid_interval_rows
FROM analytics.fact_demand_forecast
WHERE forecast_lower_bound > forecast_units
   OR forecast_units > forecast_upper_bound;


-- =========================================================
-- 7) Confidence score range check
-- =========================================================
SELECT
    COUNT(*) AS invalid_confidence_score_rows
FROM analytics.fact_demand_forecast
WHERE confidence_score < 0
   OR confidence_score > 1;


-- =========================================================
-- 8) Forecast location presence check
-- must have exactly one location type
-- =========================================================
SELECT
    COUNT(*) AS invalid_location_rows
FROM analytics.fact_demand_forecast
WHERE (store_id IS NULL AND warehouse_id IS NULL)
   OR (store_id IS NOT NULL AND warehouse_id IS NOT NULL);


-- =========================================================
-- 9) Replenishment quantity non-negative check
-- =========================================================
SELECT
    COUNT(*) AS invalid_negative_qty_rows
FROM analytics.fact_replenishment_recommendation
WHERE recommended_order_qty < 0
   OR recommended_transfer_qty < 0;


-- =========================================================
-- 10) Replenishment action existence check
-- at least one action must be > 0
-- =========================================================
SELECT
    COUNT(*) AS invalid_action_rows
FROM analytics.fact_replenishment_recommendation
WHERE recommended_order_qty <= 0
  AND recommended_transfer_qty <= 0;


-- =========================================================
-- 11) Replenishment risk range check
-- =========================================================
SELECT
    COUNT(*) AS invalid_stockout_risk_rows
FROM analytics.fact_replenishment_recommendation
WHERE expected_stockout_risk < 0
   OR expected_stockout_risk > 1;


-- =========================================================
-- 12) Replenishment service level range check
-- =========================================================
SELECT
    COUNT(*) AS invalid_service_level_rows
FROM analytics.fact_replenishment_recommendation
WHERE expected_service_level < 0
   OR expected_service_level > 1;


-- =========================================================
-- 13) Replenishment location presence check
-- must have exactly one target location type
-- =========================================================
SELECT
    COUNT(*) AS invalid_target_location_rows
FROM analytics.fact_replenishment_recommendation
WHERE (target_store_id IS NULL AND target_warehouse_id IS NULL)
   OR (target_store_id IS NOT NULL AND target_warehouse_id IS NOT NULL);


-- =========================================================
-- 14) Supplier rule check
-- if recommended_order_qty > 0, supplier must exist
-- =========================================================
SELECT
    COUNT(*) AS invalid_supplier_rule_rows
FROM analytics.fact_replenishment_recommendation
WHERE recommended_order_qty > 0
  AND recommended_supplier_id IS NULL;


-- =========================================================
-- 15) Allowed priority values check
-- =========================================================
SELECT
    COUNT(*) AS invalid_priority_rows
FROM analytics.fact_replenishment_recommendation
WHERE LOWER(priority_level) NOT IN ('low', 'normal', 'high', 'critical');


-- =========================================================
-- 16) Allowed approval status values check
-- =========================================================
SELECT
    COUNT(*) AS invalid_approval_status_rows
FROM analytics.fact_replenishment_recommendation
WHERE LOWER(approval_status) NOT IN ('draft', 'pending', 'approved', 'rejected', 'executed');


-- =========================================================
-- 17) Duplicate forecast business key check
-- one row per run + target_date + product + location
-- =========================================================
SELECT
    COUNT(*) AS duplicate_business_key_groups
FROM (
    SELECT
        forecast_run_id,
        target_date_id,
        product_id,
        COALESCE(store_id, -1) AS store_key,
        COALESCE(warehouse_id, -1) AS warehouse_key,
        COUNT(*) AS row_count
    FROM analytics.fact_demand_forecast
    GROUP BY
        forecast_run_id,
        target_date_id,
        product_id,
        COALESCE(store_id, -1),
        COALESCE(warehouse_id, -1)
    HAVING COUNT(*) > 1
) AS duplicates;


-- =========================================================
-- 18) Duplicate replenishment business key check
-- one row per run + product + target location
-- =========================================================
SELECT
    COUNT(*) AS duplicate_business_key_groups
FROM (
    SELECT
        forecast_run_id,
        product_id,
        COALESCE(target_store_id, -1) AS store_key,
        COALESCE(target_warehouse_id, -1) AS warehouse_key,
        COUNT(*) AS row_count
    FROM analytics.fact_replenishment_recommendation
    GROUP BY
        forecast_run_id,
        product_id,
        COALESCE(target_store_id, -1),
        COALESCE(target_warehouse_id, -1)
    HAVING COUNT(*) > 1
) AS duplicates;


-- =========================================================
-- 19) Quick business profile — forecast by location type
-- =========================================================
SELECT
    CASE
        WHEN store_id IS NOT NULL THEN 'store_forecast'
        WHEN warehouse_id IS NOT NULL THEN 'warehouse_forecast'
        ELSE 'unknown'
    END AS forecast_scope,
    COUNT(*) AS row_count
FROM analytics.fact_demand_forecast
GROUP BY 1
ORDER BY 1;


-- =========================================================
-- 20) Quick business profile — replenishment priority mix
-- =========================================================
SELECT
    priority_level,
    COUNT(*) AS row_count
FROM analytics.fact_replenishment_recommendation
GROUP BY priority_level
ORDER BY row_count DESC, priority_level;