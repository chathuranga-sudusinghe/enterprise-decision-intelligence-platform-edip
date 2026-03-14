SET search_path TO analytics, public;

-- =========================================================
-- Phase 4.1C — Planner Overrides + Decision Logs Validation
-- EDIP / NorthStar Retail & Distribution
-- File: 12_phase_4_planner_overrides_decision_logs_validation.sql
-- =========================================================


-- =========================================================
-- 1) Row count check
-- =========================================================
SELECT 'fact_planner_override' AS check_name, COUNT(*) AS row_count
FROM analytics.fact_planner_override

UNION ALL

SELECT 'fact_decision_log' AS check_name, COUNT(*) AS row_count
FROM analytics.fact_decision_log;


-- =========================================================
-- 2) Required NULL check — planner override
-- =========================================================
SELECT
    COUNT(*) AS invalid_required_null_rows
FROM analytics.fact_planner_override
WHERE planner_override_id IS NULL
   OR recommendation_id IS NULL
   OR forecast_run_id IS NULL
   OR override_date_id IS NULL
   OR product_id IS NULL
   OR original_order_qty IS NULL
   OR original_transfer_qty IS NULL
   OR overridden_order_qty IS NULL
   OR overridden_transfer_qty IS NULL
   OR override_type IS NULL
   OR override_reason_code IS NULL
   OR planner_name IS NULL
   OR planner_role IS NULL
   OR approval_status IS NULL
   OR impact_score IS NULL
   OR created_timestamp IS NULL;


-- =========================================================
-- 3) Required NULL check — decision log
-- =========================================================
SELECT
    COUNT(*) AS invalid_required_null_rows
FROM analytics.fact_decision_log
WHERE decision_log_id IS NULL
   OR decision_date_id IS NULL
   OR product_id IS NULL
   OR region_id IS NULL
   OR decision_type IS NULL
   OR decision_status IS NULL
   OR decision_source IS NULL
   OR final_order_qty IS NULL
   OR final_transfer_qty IS NULL
   OR decision_reason_code IS NULL
   OR decided_by IS NULL
   OR created_timestamp IS NULL;


-- =========================================================
-- 4) Planner override non-negative quantity check
-- =========================================================
SELECT
    COUNT(*) AS invalid_negative_override_qty_rows
FROM analytics.fact_planner_override
WHERE original_order_qty < 0
   OR original_transfer_qty < 0
   OR overridden_order_qty < 0
   OR overridden_transfer_qty < 0;


-- =========================================================
-- 5) Planner override location presence check
-- must have exactly one location type
-- =========================================================
SELECT
    COUNT(*) AS invalid_override_location_rows
FROM analytics.fact_planner_override
WHERE (target_store_id IS NULL AND target_warehouse_id IS NULL)
   OR (target_store_id IS NOT NULL AND target_warehouse_id IS NOT NULL);


-- =========================================================
-- 6) Planner override type allowed values check
-- =========================================================
SELECT
    COUNT(*) AS invalid_override_type_rows
FROM analytics.fact_planner_override
WHERE LOWER(override_type) NOT IN (
    'increase_order',
    'decrease_order',
    'increase_transfer',
    'decrease_transfer',
    'cancel_recommendation',
    'approve_as_is',
    'reroute_transfer'
);


-- =========================================================
-- 7) Planner override approval status allowed values check
-- =========================================================
SELECT
    COUNT(*) AS invalid_override_approval_status_rows
FROM analytics.fact_planner_override
WHERE LOWER(approval_status) NOT IN (
    'draft',
    'pending',
    'approved',
    'rejected',
    'executed'
);


-- =========================================================
-- 8) Planner override impact score range check
-- =========================================================
SELECT
    COUNT(*) AS invalid_impact_score_rows
FROM analytics.fact_planner_override
WHERE impact_score < 0
   OR impact_score > 1;


-- =========================================================
-- 9) Planner override final action rule check
-- =========================================================
SELECT
    COUNT(*) AS invalid_override_final_action_rows
FROM analytics.fact_planner_override
WHERE NOT (
    overridden_order_qty > 0
    OR overridden_transfer_qty > 0
    OR LOWER(override_type) = 'cancel_recommendation'
);


-- =========================================================
-- 10) Decision log non-negative quantity check
-- =========================================================
SELECT
    COUNT(*) AS invalid_negative_final_qty_rows
FROM analytics.fact_decision_log
WHERE final_order_qty < 0
   OR final_transfer_qty < 0;


-- =========================================================
-- 11) Decision log location logic check
-- cannot have both store and warehouse
-- =========================================================
SELECT
    COUNT(*) AS invalid_decision_location_rows
FROM analytics.fact_decision_log
WHERE target_store_id IS NOT NULL
  AND target_warehouse_id IS NOT NULL;


-- =========================================================
-- 12) Decision type allowed values check
-- =========================================================
SELECT
    COUNT(*) AS invalid_decision_type_rows
FROM analytics.fact_decision_log
WHERE LOWER(decision_type) NOT IN (
    'replenishment_approved',
    'replenishment_overridden',
    'replenishment_rejected',
    'transfer_rerouted',
    'expedite_order',
    'exception_escalated'
);


-- =========================================================
-- 13) Decision status allowed values check
-- =========================================================
SELECT
    COUNT(*) AS invalid_decision_status_rows
FROM analytics.fact_decision_log
WHERE LOWER(decision_status) NOT IN (
    'draft',
    'pending',
    'approved',
    'rejected',
    'executed',
    'escalated'
);


-- =========================================================
-- 14) Decision source allowed values check
-- =========================================================
SELECT
    COUNT(*) AS invalid_decision_source_rows
FROM analytics.fact_decision_log
WHERE LOWER(decision_source) NOT IN (
    'system',
    'planner',
    'manager',
    'hybrid'
);


-- =========================================================
-- 15) Decision score range checks
-- =========================================================
SELECT
    COUNT(*) AS invalid_decision_score_rows
FROM analytics.fact_decision_log
WHERE (service_level_target IS NOT NULL AND (service_level_target < 0 OR service_level_target > 1))
   OR (expected_stockout_risk IS NOT NULL AND (expected_stockout_risk < 0 OR expected_stockout_risk > 1))
   OR (expected_service_level IS NOT NULL AND (expected_service_level < 0 OR expected_service_level > 1));


-- =========================================================
-- 16) Decision anchor integrity check
-- must have recommendation or planner override anchor
-- =========================================================
SELECT
    COUNT(*) AS invalid_decision_anchor_rows
FROM analytics.fact_decision_log
WHERE recommendation_id IS NULL
  AND planner_override_id IS NULL;


-- =========================================================
-- 17) Decision final action rule check
-- =========================================================
SELECT
    COUNT(*) AS invalid_decision_final_action_rows
FROM analytics.fact_decision_log
WHERE NOT (
    final_order_qty > 0
    OR final_transfer_qty > 0
    OR LOWER(decision_status) IN ('rejected', 'escalated')
);


-- =========================================================
-- 18) Duplicate planner override recommendation check
-- one override per recommendation
-- =========================================================
SELECT
    COUNT(*) AS duplicate_override_groups
FROM (
    SELECT
        recommendation_id,
        COUNT(*) AS row_count
    FROM analytics.fact_planner_override
    GROUP BY recommendation_id
    HAVING COUNT(*) > 1
) AS duplicates;


-- =========================================================
-- 19) Duplicate decision event check
-- =========================================================
SELECT
    COUNT(*) AS duplicate_decision_event_groups
FROM (
    SELECT
        decision_date_id,
        COALESCE(recommendation_id, -1) AS recommendation_key,
        COALESCE(planner_override_id, -1) AS override_key,
        decision_type,
        COUNT(*) AS row_count
    FROM analytics.fact_decision_log
    GROUP BY
        decision_date_id,
        COALESCE(recommendation_id, -1),
        COALESCE(planner_override_id, -1),
        decision_type
    HAVING COUNT(*) > 1
) AS duplicates;


-- =========================================================
-- 20) Profile — override type distribution
-- =========================================================
SELECT
    override_type,
    COUNT(*) AS row_count
FROM analytics.fact_planner_override
GROUP BY override_type
ORDER BY row_count DESC, override_type;


-- =========================================================
-- 21) Profile — decision status distribution
-- =========================================================
SELECT
    decision_status,
    COUNT(*) AS row_count
FROM analytics.fact_decision_log
GROUP BY decision_status
ORDER BY row_count DESC, decision_status;


-- =========================================================
-- 22) Profile — decision source distribution
-- =========================================================
SELECT
    decision_source,
    COUNT(*) AS row_count
FROM analytics.fact_decision_log
GROUP BY decision_source
ORDER BY row_count DESC, decision_source;