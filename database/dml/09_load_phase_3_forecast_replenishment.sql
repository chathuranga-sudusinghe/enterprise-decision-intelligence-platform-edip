SET search_path TO analytics, public;

-- =========================================================
-- Phase 3.1B — Load Forecast + Replenishment CSV Files
-- EDIP / NorthStar Retail & Distribution
-- File: 09_load_phase_3_forecast_replenishment.sql
-- =========================================================


-- =========================================================
-- 0) Safety cleanup before reload
-- =========================================================
TRUNCATE TABLE analytics.fact_replenishment_recommendation RESTART IDENTITY;
TRUNCATE TABLE analytics.fact_demand_forecast RESTART IDENTITY;


-- =========================================================
-- 1) Temporary staging table for fact_demand_forecast
-- =========================================================
DROP TABLE IF EXISTS staging_fact_demand_forecast;

CREATE TEMP TABLE staging_fact_demand_forecast (
    forecast_id                    BIGINT,
    forecast_run_id                BIGINT,
    forecast_date_id               INTEGER,
    target_date_id                 INTEGER,
    product_id                     INTEGER,
    store_id                       INTEGER,
    warehouse_id                   INTEGER,
    region_id                      INTEGER,
    forecast_units                 DECIMAL(14,2),
    forecast_lower_bound           DECIMAL(14,2),
    forecast_upper_bound           DECIMAL(14,2),
    model_name                     VARCHAR(100),
    model_version                  VARCHAR(50),
    confidence_score               DECIMAL(6,4),
    created_timestamp              TIMESTAMP
);


-- =========================================================
-- 2) Load CSV into forecast staging
-- =========================================================
\copy staging_fact_demand_forecast FROM './data/synthetic/fact_demand_forecast.csv' WITH (FORMAT csv, HEADER true);

-- =========================================================
-- 3) Insert forecast data into final table
-- =========================================================
INSERT INTO analytics.fact_demand_forecast (
    forecast_id,
    forecast_run_id,
    forecast_date_id,
    target_date_id,
    product_id,
    store_id,
    warehouse_id,
    region_id,
    forecast_units,
    forecast_lower_bound,
    forecast_upper_bound,
    model_name,
    model_version,
    confidence_score,
    created_timestamp
)
SELECT
    forecast_id,
    forecast_run_id,
    forecast_date_id,
    target_date_id,
    product_id,
    NULLIF(store_id, 0),
    NULLIF(warehouse_id, 0),
    region_id,
    forecast_units,
    forecast_lower_bound,
    forecast_upper_bound,
    model_name,
    model_version,
    confidence_score,
    created_timestamp
FROM staging_fact_demand_forecast;


-- =========================================================
-- 4) Temporary staging table for fact_replenishment_recommendation
-- =========================================================
DROP TABLE IF EXISTS staging_fact_replenishment_recommendation;

CREATE TEMP TABLE staging_fact_replenishment_recommendation (
    recommendation_id              BIGINT,
    forecast_run_id                BIGINT,
    recommendation_date_id         INTEGER,
    product_id                     INTEGER,
    target_store_id                INTEGER,
    target_warehouse_id            INTEGER,
    recommended_order_qty          INTEGER,
    recommended_transfer_qty       INTEGER,
    priority_level                 VARCHAR(20),
    reason_code                    VARCHAR(100),
    expected_stockout_risk         DECIMAL(6,4),
    expected_service_level         DECIMAL(6,4),
    recommended_supplier_id        INTEGER,
    approval_status                VARCHAR(30),
    created_timestamp              TIMESTAMP
);


-- =========================================================
-- 5) Load CSV into replenishment staging
-- =========================================================
\copy staging_fact_replenishment_recommendation FROM './data/synthetic/fact_replenishment_recommendation.csv' WITH (FORMAT csv, HEADER true);


-- =========================================================
-- 6) Insert replenishment data into final table
-- =========================================================
INSERT INTO analytics.fact_replenishment_recommendation (
    recommendation_id,
    forecast_run_id,
    recommendation_date_id,
    product_id,
    target_store_id,
    target_warehouse_id,
    recommended_order_qty,
    recommended_transfer_qty,
    priority_level,
    reason_code,
    expected_stockout_risk,
    expected_service_level,
    recommended_supplier_id,
    approval_status,
    created_timestamp
)
SELECT
    recommendation_id,
    forecast_run_id,
    recommendation_date_id,
    product_id,
    NULLIF(target_store_id, 0),
    NULLIF(target_warehouse_id, 0),
    recommended_order_qty,
    recommended_transfer_qty,
    LOWER(priority_level),
    LOWER(reason_code),
    expected_stockout_risk,
    expected_service_level,
    NULLIF(recommended_supplier_id, 0),
    LOWER(approval_status),
    created_timestamp
FROM staging_fact_replenishment_recommendation;


-- =========================================================
-- 7) Quick load summary
-- =========================================================
SELECT 'fact_demand_forecast' AS table_name, COUNT(*) AS row_count
FROM analytics.fact_demand_forecast

UNION ALL

SELECT 'fact_replenishment_recommendation' AS table_name, COUNT(*) AS row_count
FROM analytics.fact_replenishment_recommendation
ORDER BY table_name;