SET search_path TO analytics, public;

-- =========================================================
-- Phase 4.1B — Load Planner Overrides + Decision Logs
-- EDIP / NorthStar Retail & Distribution
-- File: 11_load_phase_4_planner_overrides_decision_logs.sql
-- =========================================================


-- =========================================================
-- 0) Safety cleanup before reload
-- =========================================================
TRUNCATE TABLE analytics.fact_decision_log, analytics.fact_planner_override;


-- =========================================================
-- 1) Temporary staging table for fact_planner_override
-- =========================================================
DROP TABLE IF EXISTS staging_fact_planner_override;

CREATE TEMP TABLE staging_fact_planner_override (
    planner_override_id            BIGINT,
    recommendation_id              BIGINT,
    forecast_run_id                BIGINT,
    override_date_id               INTEGER,
    product_id                     INTEGER,
    target_store_id                INTEGER,
    target_warehouse_id            INTEGER,
    original_order_qty             INTEGER,
    original_transfer_qty          INTEGER,
    overridden_order_qty           INTEGER,
    overridden_transfer_qty        INTEGER,
    override_type                  VARCHAR(30),
    override_reason_code           VARCHAR(100),
    planner_name                   VARCHAR(100),
    planner_role                   VARCHAR(50),
    approval_status                VARCHAR(30),
    impact_score                   DECIMAL(6,4),
    comment_text                   VARCHAR(500),
    created_timestamp              TIMESTAMP
);

\copy staging_fact_planner_override FROM './data/synthetic/fact_planner_override.csv' WITH (FORMAT csv, HEADER true);

INSERT INTO analytics.fact_planner_override (
    planner_override_id, 
    recommendation_id, 
    forecast_run_id, 
    override_date_id, 
    product_id, 
    target_store_id, 
    target_warehouse_id, 
    original_order_qty, 
    original_transfer_qty, 
    overridden_order_qty, 
    overridden_transfer_qty, 
    override_type, 
    override_reason_code, 
    planner_name, 
    planner_role, 
    approval_status, 
    impact_score, 
    comment_text, 
    created_timestamp)

SELECT 
    planner_override_id, 
    recommendation_id, 
    forecast_run_id, 
    override_date_id, 
    product_id, 
    NULLIF(target_store_id, 0), 
    NULLIF(target_warehouse_id, 0), 
    original_order_qty, 
    original_transfer_qty, 
    overridden_order_qty, 
    overridden_transfer_qty, 
    LOWER(override_type), 
    LOWER(override_reason_code), 
    planner_name, 
    LOWER(planner_role),
    LOWER(approval_status), 
    impact_score, 
    comment_text, 
    created_timestamp
FROM staging_fact_planner_override;


-- =========================================================
-- 2) Temporary staging table for fact_decision_log
-- =========================================================
DROP TABLE IF EXISTS staging_fact_decision_log;

CREATE TEMP TABLE staging_fact_decision_log (
    decision_log_id                BIGINT,
    decision_date_id               INTEGER,
    forecast_run_id                BIGINT,
    recommendation_id              BIGINT,
    planner_override_id            BIGINT,
    product_id                     INTEGER,
    region_id                      INTEGER,
    target_store_id                INTEGER,
    target_warehouse_id            INTEGER,
    decision_type                  VARCHAR(50),
    decision_status                VARCHAR(30),
    decision_source                VARCHAR(30),
    final_order_qty                INTEGER,
    final_transfer_qty             INTEGER,
    service_level_target           DECIMAL(6,4),
    expected_stockout_risk         DECIMAL(6,4),
    expected_service_level         DECIMAL(6,4),
    escalation_flag                BOOLEAN,
    exception_flag                 BOOLEAN,
    decision_reason_code           VARCHAR(100),
    decided_by                     VARCHAR(100),
    created_timestamp              TIMESTAMP
);

\copy staging_fact_decision_log FROM './data/synthetic/fact_decision_log.csv' WITH (FORMAT csv, HEADER true);

INSERT INTO analytics.fact_decision_log (
    decision_log_id, decision_date_id, 
    forecast_run_id, recommendation_id, 
    planner_override_id, product_id, 
    region_id, target_store_id, 
    target_warehouse_id, 
    decision_type, 
    decision_status, 
    decision_source, 
    final_order_qty, 
    final_transfer_qty, 
    service_level_target, 
    expected_stockout_risk, 
    expected_service_level, 
    escalation_flag, 
    exception_flag, 
    decision_reason_code, 
    decided_by, 
    created_timestamp)

SELECT 
    decision_log_id, 
    decision_date_id, 
    NULLIF(forecast_run_id, 0),
    NULLIF(recommendation_id, 0), 
    NULLIF(planner_override_id, 0), 
    product_id, region_id, 
    NULLIF(target_store_id, 0), 
    NULLIF(target_warehouse_id, 0), 
    LOWER(decision_type), 
    LOWER(decision_status), 
    LOWER(decision_source), 
    final_order_qty, 
    final_transfer_qty, 
    service_level_target, 
    expected_stockout_risk, 
    expected_service_level, 
    escalation_flag, 
    exception_flag, 
    LOWER(decision_reason_code), 
    decided_by, 
    created_timestamp
FROM staging_fact_decision_log;


-- =========================================================
-- 3) Quick load summary
-- =========================================================
SELECT 'fact_planner_override' AS table_name, COUNT(*) AS row_count
FROM analytics.fact_planner_override

UNION ALL

SELECT 'fact_decision_log' AS table_name, COUNT(*) AS row_count
FROM analytics.fact_decision_log
ORDER BY table_name;