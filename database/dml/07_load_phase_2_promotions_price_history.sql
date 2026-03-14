SET search_path TO analytics, public;

-- =========================================================
-- Phase 2.1C — Load Promotions + Price History CSVs
-- EDIP / NorthStar Retail & Distribution
-- File: 07_load_phase_2_promotions_price_history.sql
-- =========================================================

-- ---------------------------------------------------------
-- 1) Load order
-- Load child table last because fact_price_history references
-- fact_promotions via source_promotion_id
-- ---------------------------------------------------------

TRUNCATE TABLE
    analytics.fact_price_history,
    analytics.fact_promotions;

-- ---------------------------------------------------------
-- 2) Load fact_promotions
-- ---------------------------------------------------------
\copy analytics.fact_promotions (promotion_id, promotion_code, promotion_name, campaign_type, promotion_status, product_id, channel_id, region_id, start_date_id, end_date_id, base_unit_price, promo_unit_price, discount_amount, discount_pct, expected_uplift_pct, actual_uplift_pct, budget_amount, promo_priority, stackable_flag, promo_reason) FROM './data/synthetic/fact_promotions.csv'DELIMITER ',' CSV HEADER;

-- ---------------------------------------------------------
-- 3) Load fact_price_history
-- ---------------------------------------------------------
\copy analytics.fact_price_history (price_history_id, product_id, channel_id, region_id, effective_start_date_id, effective_end_date_id, list_price, selling_price, promo_price, markdown_pct, price_change_reason, price_status, is_promo_price_flag, source_promotion_id) FROM './data/synthetic/fact_price_history.csv' DELIMITER ','CSV HEADER;

-- ---------------------------------------------------------
-- 4) Quick row-count check
-- ---------------------------------------------------------
SELECT 'fact_promotions' AS table_name, COUNT(*) AS row_count
FROM analytics.fact_promotions
UNION ALL
SELECT 'fact_price_history', COUNT(*)
FROM analytics.fact_price_history
ORDER BY table_name;