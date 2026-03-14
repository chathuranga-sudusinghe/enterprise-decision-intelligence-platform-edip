SET search_path TO analytics, public;

-- =========================================================
-- Phase 2.1D — Promotions + Price History Validation Checks
-- EDIP / NorthStar Retail & Distribution
-- File: 08_phase_2_promotions_price_history_validation.sql
-- =========================================================


-- =========================================================
-- 1) Row count checks
-- =========================================================
SELECT 'fact_promotions' AS table_name, COUNT(*) AS row_count
FROM analytics.fact_promotions
UNION ALL
SELECT 'fact_price_history', COUNT(*)
FROM analytics.fact_price_history
ORDER BY table_name;


-- =========================================================
-- 2) Null checks for key required columns
-- =========================================================
SELECT
    COUNT(*) AS null_promotion_id_rows
FROM analytics.fact_promotions
WHERE promotion_id IS NULL;

SELECT
    COUNT(*) AS null_promotion_code_rows
FROM analytics.fact_promotions
WHERE promotion_code IS NULL;

SELECT
    COUNT(*) AS null_product_id_rows
FROM analytics.fact_promotions
WHERE product_id IS NULL;

SELECT
    COUNT(*) AS null_channel_id_rows
FROM analytics.fact_promotions
WHERE channel_id IS NULL;

SELECT
    COUNT(*) AS null_start_date_id_rows
FROM analytics.fact_promotions
WHERE start_date_id IS NULL;

SELECT
    COUNT(*) AS null_end_date_id_rows
FROM analytics.fact_promotions
WHERE end_date_id IS NULL;

SELECT
    COUNT(*) AS null_base_unit_price_rows
FROM analytics.fact_promotions
WHERE base_unit_price IS NULL;

SELECT
    COUNT(*) AS null_promo_unit_price_rows
FROM analytics.fact_promotions
WHERE promo_unit_price IS NULL;

SELECT
    COUNT(*) AS null_price_history_id_rows
FROM analytics.fact_price_history
WHERE price_history_id IS NULL;

SELECT
    COUNT(*) AS null_product_id_rows
FROM analytics.fact_price_history
WHERE product_id IS NULL;

SELECT
    COUNT(*) AS null_channel_id_rows
FROM analytics.fact_price_history
WHERE channel_id IS NULL;

SELECT
    COUNT(*) AS null_effective_start_date_id_rows
FROM analytics.fact_price_history
WHERE effective_start_date_id IS NULL;

SELECT
    COUNT(*) AS null_effective_end_date_id_rows
FROM analytics.fact_price_history
WHERE effective_end_date_id IS NULL;

SELECT
    COUNT(*) AS null_list_price_rows
FROM analytics.fact_price_history
WHERE list_price IS NULL;

SELECT
    COUNT(*) AS null_selling_price_rows
FROM analytics.fact_price_history
WHERE selling_price IS NULL;

SELECT
    COUNT(*) AS null_price_status_rows
FROM analytics.fact_price_history
WHERE price_status IS NULL;


-- =========================================================
-- 3) Duplicate key checks
-- =========================================================
SELECT
    promotion_id,
    COUNT(*) AS duplicate_count
FROM analytics.fact_promotions
GROUP BY promotion_id
HAVING COUNT(*) > 1;

SELECT
    promotion_code,
    COUNT(*) AS duplicate_count
FROM analytics.fact_promotions
GROUP BY promotion_code
HAVING COUNT(*) > 1;

SELECT
    price_history_id,
    COUNT(*) AS duplicate_count
FROM analytics.fact_price_history
GROUP BY price_history_id
HAVING COUNT(*) > 1;


-- =========================================================
-- 4) Foreign key consistency checks
-- =========================================================
SELECT
    COUNT(*) AS missing_product_fk_rows
FROM analytics.fact_promotions fp
LEFT JOIN analytics.dim_product dp
    ON fp.product_id = dp.product_id
WHERE dp.product_id IS NULL;

SELECT
    COUNT(*) AS missing_channel_fk_rows
FROM analytics.fact_promotions fp
LEFT JOIN analytics.dim_channel dc
    ON fp.channel_id = dc.channel_id
WHERE dc.channel_id IS NULL;

SELECT
    COUNT(*) AS missing_region_fk_rows
FROM analytics.fact_promotions fp
LEFT JOIN analytics.dim_region dr
    ON fp.region_id = dr.region_id
WHERE fp.region_id IS NOT NULL
  AND dr.region_id IS NULL;

SELECT
    COUNT(*) AS missing_start_date_fk_rows
FROM analytics.fact_promotions fp
LEFT JOIN analytics.dim_calendar cal
    ON fp.start_date_id = cal.date_id
WHERE cal.date_id IS NULL;

SELECT
    COUNT(*) AS missing_end_date_fk_rows
FROM analytics.fact_promotions fp
LEFT JOIN analytics.dim_calendar cal
    ON fp.end_date_id = cal.date_id
WHERE cal.date_id IS NULL;

SELECT
    COUNT(*) AS missing_product_fk_rows
FROM analytics.fact_price_history fph
LEFT JOIN analytics.dim_product dp
    ON fph.product_id = dp.product_id
WHERE dp.product_id IS NULL;

SELECT
    COUNT(*) AS missing_channel_fk_rows
FROM analytics.fact_price_history fph
LEFT JOIN analytics.dim_channel dc
    ON fph.channel_id = dc.channel_id
WHERE dc.channel_id IS NULL;

SELECT
    COUNT(*) AS missing_region_fk_rows
FROM analytics.fact_price_history fph
LEFT JOIN analytics.dim_region dr
    ON fph.region_id = dr.region_id
WHERE fph.region_id IS NOT NULL
  AND dr.region_id IS NULL;

SELECT
    COUNT(*) AS missing_start_date_fk_rows
FROM analytics.fact_price_history fph
LEFT JOIN analytics.dim_calendar cal
    ON fph.effective_start_date_id = cal.date_id
WHERE cal.date_id IS NULL;

SELECT
    COUNT(*) AS missing_end_date_fk_rows
FROM analytics.fact_price_history fph
LEFT JOIN analytics.dim_calendar cal
    ON fph.effective_end_date_id = cal.date_id
WHERE cal.date_id IS NULL;


-- =========================================================
-- 5) Promotion business rule checks
-- =========================================================
SELECT
    COUNT(*) AS invalid_promotion_date_windows
FROM analytics.fact_promotions
WHERE end_date_id < start_date_id;

SELECT
    COUNT(*) AS invalid_promotion_price_logic_rows
FROM analytics.fact_promotions
WHERE base_unit_price <= 0
   OR promo_unit_price <= 0
   OR promo_unit_price > base_unit_price;

SELECT
    COUNT(*) AS invalid_discount_amount_rows
FROM analytics.fact_promotions
WHERE discount_amount < 0;

SELECT
    COUNT(*) AS invalid_discount_pct_rows
FROM analytics.fact_promotions
WHERE discount_pct < 0
   OR discount_pct > 100;

SELECT
    COUNT(*) AS invalid_budget_rows
FROM analytics.fact_promotions
WHERE budget_amount IS NOT NULL
  AND budget_amount < 0;

SELECT
    COUNT(*) AS invalid_status_rows
FROM analytics.fact_promotions
WHERE LOWER(promotion_status) NOT IN (
    'planned',
    'approved',
    'active',
    'completed',
    'cancelled'
);

SELECT
    COUNT(*) AS invalid_priority_rows
FROM analytics.fact_promotions
WHERE LOWER(promo_priority) NOT IN (
    'high',
    'medium',
    'low'
);

SELECT
    COUNT(*) AS incorrect_discount_math_rows
FROM analytics.fact_promotions
WHERE ABS((base_unit_price - promo_unit_price) - discount_amount) > 0.02;


-- =========================================================
-- 6) Price history business rule checks
-- =========================================================
SELECT
    COUNT(*) AS invalid_price_history_date_windows
FROM analytics.fact_price_history
WHERE effective_end_date_id < effective_start_date_id;

SELECT
    COUNT(*) AS invalid_list_price_rows
FROM analytics.fact_price_history
WHERE list_price <= 0;

SELECT
    COUNT(*) AS invalid_selling_price_rows
FROM analytics.fact_price_history
WHERE selling_price <= 0
   OR selling_price > list_price;

SELECT
    COUNT(*) AS invalid_promo_price_rows
FROM analytics.fact_price_history
WHERE promo_price IS NOT NULL
  AND (
      promo_price <= 0
      OR promo_price > list_price
  );

SELECT
    COUNT(*) AS invalid_markdown_pct_rows
FROM analytics.fact_price_history
WHERE markdown_pct < 0
   OR markdown_pct > 100;

SELECT
    COUNT(*) AS invalid_price_status_rows
FROM analytics.fact_price_history
WHERE LOWER(price_status) NOT IN (
    'scheduled',
    'active',
    'expired'
);

SELECT
    COUNT(*) AS bad_promo_flag_without_source_rows
FROM analytics.fact_price_history
WHERE is_promo_price_flag = TRUE
  AND source_promotion_id IS NULL;

SELECT
    COUNT(*) AS bad_nonpromo_with_source_rows
FROM analytics.fact_price_history
WHERE is_promo_price_flag = FALSE
  AND source_promotion_id IS NOT NULL;


-- =========================================================
-- 7) Promotion linkage checks
-- =========================================================
SELECT
    COUNT(*) AS missing_source_promotion_fk_rows
FROM analytics.fact_price_history fph
LEFT JOIN analytics.fact_promotions fp
    ON fph.source_promotion_id = fp.promotion_id
WHERE fph.source_promotion_id IS NOT NULL
  AND fp.promotion_id IS NULL;

SELECT
    COUNT(*) AS promo_scope_mismatch_rows
FROM analytics.fact_price_history fph
JOIN analytics.fact_promotions fp
    ON fph.source_promotion_id = fp.promotion_id
WHERE fph.is_promo_price_flag = TRUE
  AND (
      fph.product_id <> fp.product_id
      OR fph.channel_id <> fp.channel_id
      OR COALESCE(fph.region_id, -1) <> COALESCE(fp.region_id, -1)
  );

SELECT
    COUNT(*) AS promo_price_mismatch_rows
FROM analytics.fact_price_history fph
JOIN analytics.fact_promotions fp
    ON fph.source_promotion_id = fp.promotion_id
WHERE fph.is_promo_price_flag = TRUE
  AND ABS(fph.selling_price - fp.promo_unit_price) > 0.02;

SELECT
    COUNT(*) AS promo_window_outside_source_rows
FROM analytics.fact_price_history fph
JOIN analytics.fact_promotions fp
    ON fph.source_promotion_id = fp.promotion_id
WHERE fph.is_promo_price_flag = TRUE
  AND (
      fph.effective_start_date_id < fp.start_date_id
      OR fph.effective_end_date_id > fp.end_date_id
  );


-- =========================================================
-- 8) Overlap checks — fact_promotions
-- =========================================================
WITH ordered_promotions AS (
    SELECT
        promotion_id,
        product_id,
        channel_id,
        region_id,
        start_date_id,
        end_date_id,
        LAG(end_date_id) OVER (
            PARTITION BY product_id, channel_id, region_id
            ORDER BY start_date_id, promotion_id
        ) AS previous_end_date_id
    FROM analytics.fact_promotions
)
SELECT
    promotion_id,
    product_id,
    channel_id,
    region_id,
    start_date_id,
    end_date_id,
    previous_end_date_id
FROM ordered_promotions
WHERE previous_end_date_id IS NOT NULL
  AND start_date_id <= previous_end_date_id
ORDER BY product_id, channel_id, region_id, start_date_id, promotion_id;


-- =========================================================
-- 9) Overlap checks — fact_price_history
-- =========================================================
WITH ordered_price_history AS (
    SELECT
        price_history_id,
        product_id,
        channel_id,
        region_id,
        effective_start_date_id,
        effective_end_date_id,
        LAG(effective_end_date_id) OVER (
            PARTITION BY product_id, channel_id, region_id
            ORDER BY effective_start_date_id, price_history_id
        ) AS previous_end_date_id
    FROM analytics.fact_price_history
)
SELECT
    price_history_id,
    product_id,
    channel_id,
    region_id,
    effective_start_date_id,
    effective_end_date_id,
    previous_end_date_id
FROM ordered_price_history
WHERE previous_end_date_id IS NOT NULL
  AND effective_start_date_id <= previous_end_date_id
ORDER BY product_id, channel_id, region_id, effective_start_date_id, price_history_id;


-- =========================================================
-- 10) Coverage / summary checks
-- =========================================================
SELECT
    promotion_status,
    COUNT(*) AS promotion_count
FROM analytics.fact_promotions
GROUP BY promotion_status
ORDER BY promotion_status;

SELECT
    campaign_type,
    COUNT(*) AS promotion_count
FROM analytics.fact_promotions
GROUP BY campaign_type
ORDER BY promotion_count DESC, campaign_type;

SELECT
    promo_priority,
    COUNT(*) AS promotion_count
FROM analytics.fact_promotions
GROUP BY promo_priority
ORDER BY promo_priority;

SELECT
    price_status,
    COUNT(*) AS row_count
FROM analytics.fact_price_history
GROUP BY price_status
ORDER BY price_status;

SELECT
    is_promo_price_flag,
    COUNT(*) AS row_count
FROM analytics.fact_price_history
GROUP BY is_promo_price_flag
ORDER BY is_promo_price_flag;


-- =========================================================
-- 11) Final validation summary
-- All values should ideally be zero.
-- =========================================================
WITH validation_summary AS (
    SELECT 'invalid_promotion_date_windows' AS check_name, COUNT(*) AS issue_count
    FROM analytics.fact_promotions
    WHERE end_date_id < start_date_id

    UNION ALL

    SELECT 'invalid_promotion_price_logic_rows', COUNT(*)
    FROM analytics.fact_promotions
    WHERE base_unit_price <= 0
       OR promo_unit_price <= 0
       OR promo_unit_price > base_unit_price

    UNION ALL

    SELECT 'invalid_discount_pct_rows', COUNT(*)
    FROM analytics.fact_promotions
    WHERE discount_pct < 0
       OR discount_pct > 100

    UNION ALL

    SELECT 'invalid_price_history_date_windows', COUNT(*)
    FROM analytics.fact_price_history
    WHERE effective_end_date_id < effective_start_date_id

    UNION ALL

    SELECT 'invalid_selling_price_rows', COUNT(*)
    FROM analytics.fact_price_history
    WHERE selling_price <= 0
       OR selling_price > list_price

    UNION ALL

    SELECT 'invalid_promo_price_rows', COUNT(*)
    FROM analytics.fact_price_history
    WHERE promo_price IS NOT NULL
      AND (
          promo_price <= 0
          OR promo_price > list_price
      )

    UNION ALL

    SELECT 'invalid_markdown_pct_rows', COUNT(*)
    FROM analytics.fact_price_history
    WHERE markdown_pct < 0
       OR markdown_pct > 100

    UNION ALL

    SELECT 'bad_promo_flag_without_source_rows', COUNT(*)
    FROM analytics.fact_price_history
    WHERE is_promo_price_flag = TRUE
      AND source_promotion_id IS NULL

    UNION ALL

    SELECT 'bad_nonpromo_with_source_rows', COUNT(*)
    FROM analytics.fact_price_history
    WHERE is_promo_price_flag = FALSE
      AND source_promotion_id IS NOT NULL

    UNION ALL

    SELECT 'missing_source_promotion_fk_rows', COUNT(*)
    FROM analytics.fact_price_history fph
    LEFT JOIN analytics.fact_promotions fp
        ON fph.source_promotion_id = fp.promotion_id
    WHERE fph.source_promotion_id IS NOT NULL
      AND fp.promotion_id IS NULL
)
SELECT *
FROM validation_summary
ORDER BY check_name;