SET search_path TO analytics, public;

-- =========================================================
-- Phase 3.1A — Forecast + Replenishment Fact Tables
-- EDIP / NorthStar Retail & Distribution
-- File: 09_phase_3_forecast_replenishment.sql
-- =========================================================


-- =========================================================
-- 1) fact_demand_forecast
-- Purpose:
--   Forecast output by SKU-location-target date.
--   One row = one forecasted SKU-location-target-date record
--   generated from one forecast run.
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_demand_forecast (
    forecast_id                    BIGINT PRIMARY KEY,
    forecast_run_id                BIGINT NOT NULL,
    forecast_date_id               INTEGER NOT NULL,
    target_date_id                 INTEGER NOT NULL,

    product_id                     INTEGER NOT NULL,
    store_id                       INTEGER,
    warehouse_id                   INTEGER,
    region_id                      INTEGER NOT NULL,

    forecast_units                 DECIMAL(14,2) NOT NULL,
    forecast_lower_bound           DECIMAL(14,2) NOT NULL,
    forecast_upper_bound           DECIMAL(14,2) NOT NULL,

    model_name                     VARCHAR(100) NOT NULL,
    model_version                  VARCHAR(50) NOT NULL,
    confidence_score               DECIMAL(6,4) NOT NULL,

    created_timestamp              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fdf_forecast_date
        FOREIGN KEY (forecast_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fdf_target_date
        FOREIGN KEY (target_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fdf_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_fdf_store
        FOREIGN KEY (store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_fdf_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT fk_fdf_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id),

    CONSTRAINT chk_fdf_date_window
        CHECK (target_date_id >= forecast_date_id),

    CONSTRAINT chk_fdf_forecast_units_nonnegative
        CHECK (forecast_units >= 0),

    CONSTRAINT chk_fdf_lower_bound_nonnegative
        CHECK (forecast_lower_bound >= 0),

    CONSTRAINT chk_fdf_upper_bound_nonnegative
        CHECK (forecast_upper_bound >= 0),

    CONSTRAINT chk_fdf_interval_logic
        CHECK (
            forecast_lower_bound <= forecast_units
            AND forecast_units <= forecast_upper_bound
        ),

    CONSTRAINT chk_fdf_confidence_score
        CHECK (confidence_score >= 0 AND confidence_score <= 1),

    CONSTRAINT chk_fdf_location_presence
        CHECK (
            store_id IS NOT NULL
            OR warehouse_id IS NOT NULL
        ),

    CONSTRAINT chk_fdf_single_location_type
        CHECK (
            NOT (store_id IS NOT NULL AND warehouse_id IS NOT NULL)
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fdf_run_target_scope
    ON analytics.fact_demand_forecast (
        forecast_run_id,
        target_date_id,
        product_id,
        COALESCE(store_id, -1),
        COALESCE(warehouse_id, -1)
    );

CREATE INDEX IF NOT EXISTS idx_fdf_forecast_run_id
    ON analytics.fact_demand_forecast(forecast_run_id);

CREATE INDEX IF NOT EXISTS idx_fdf_forecast_date_id
    ON analytics.fact_demand_forecast(forecast_date_id);

CREATE INDEX IF NOT EXISTS idx_fdf_target_date_id
    ON analytics.fact_demand_forecast(target_date_id);

CREATE INDEX IF NOT EXISTS idx_fdf_product_id
    ON analytics.fact_demand_forecast(product_id);

CREATE INDEX IF NOT EXISTS idx_fdf_store_id
    ON analytics.fact_demand_forecast(store_id);

CREATE INDEX IF NOT EXISTS idx_fdf_warehouse_id
    ON analytics.fact_demand_forecast(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fdf_region_id
    ON analytics.fact_demand_forecast(region_id);


-- =========================================================
-- 2) fact_replenishment_recommendation
-- Purpose:
--   Prescriptive action output from forecast + inventory logic.
--   One row = one recommendation for one SKU-location scope.
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_replenishment_recommendation (
    recommendation_id              BIGINT PRIMARY KEY,
    forecast_run_id                BIGINT NOT NULL,
    recommendation_date_id         INTEGER NOT NULL,

    product_id                     INTEGER NOT NULL,
    target_store_id                INTEGER,
    target_warehouse_id            INTEGER,

    recommended_order_qty          INTEGER NOT NULL DEFAULT 0,
    recommended_transfer_qty       INTEGER NOT NULL DEFAULT 0,

    priority_level                 VARCHAR(20) NOT NULL,
    reason_code                    VARCHAR(100) NOT NULL,

    expected_stockout_risk         DECIMAL(6,4) NOT NULL,
    expected_service_level         DECIMAL(6,4) NOT NULL,

    recommended_supplier_id        INTEGER,
    approval_status                VARCHAR(30) NOT NULL,

    created_timestamp              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_frr_recommendation_date
        FOREIGN KEY (recommendation_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_frr_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_frr_target_store
        FOREIGN KEY (target_store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_frr_target_warehouse
        FOREIGN KEY (target_warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT fk_frr_supplier
        FOREIGN KEY (recommended_supplier_id)
        REFERENCES analytics.dim_supplier(supplier_id),

    CONSTRAINT chk_frr_qty_nonnegative
        CHECK (
            recommended_order_qty >= 0
            AND recommended_transfer_qty >= 0
        ),

    CONSTRAINT chk_frr_some_action_exists
        CHECK (
            recommended_order_qty > 0
            OR recommended_transfer_qty > 0
        ),

    CONSTRAINT chk_frr_priority_level
        CHECK (
            LOWER(priority_level) IN (
                'low',
                'normal',
                'high',
                'critical'
            )
        ),

    CONSTRAINT chk_frr_stockout_risk
        CHECK (
            expected_stockout_risk >= 0
            AND expected_stockout_risk <= 1
        ),

    CONSTRAINT chk_frr_service_level
        CHECK (
            expected_service_level >= 0
            AND expected_service_level <= 1
        ),

    CONSTRAINT chk_frr_approval_status
        CHECK (
            LOWER(approval_status) IN (
                'draft',
                'pending',
                'approved',
                'rejected',
                'executed'
            )
        ),

    CONSTRAINT chk_frr_location_presence
        CHECK (
            target_store_id IS NOT NULL
            OR target_warehouse_id IS NOT NULL
        ),

    CONSTRAINT chk_frr_single_location_type
        CHECK (
            NOT (target_store_id IS NOT NULL AND target_warehouse_id IS NOT NULL)
        ),

    CONSTRAINT chk_frr_supplier_needed_for_order
        CHECK (
            recommended_order_qty = 0
            OR recommended_supplier_id IS NOT NULL
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_frr_run_scope
    ON analytics.fact_replenishment_recommendation (
        forecast_run_id,
        product_id,
        COALESCE(target_store_id, -1),
        COALESCE(target_warehouse_id, -1)
    );

CREATE INDEX IF NOT EXISTS idx_frr_forecast_run_id
    ON analytics.fact_replenishment_recommendation(forecast_run_id);

CREATE INDEX IF NOT EXISTS idx_frr_recommendation_date_id
    ON analytics.fact_replenishment_recommendation(recommendation_date_id);

CREATE INDEX IF NOT EXISTS idx_frr_product_id
    ON analytics.fact_replenishment_recommendation(product_id);

CREATE INDEX IF NOT EXISTS idx_frr_target_store_id
    ON analytics.fact_replenishment_recommendation(target_store_id);

CREATE INDEX IF NOT EXISTS idx_frr_target_warehouse_id
    ON analytics.fact_replenishment_recommendation(target_warehouse_id);

CREATE INDEX IF NOT EXISTS idx_frr_supplier_id
    ON analytics.fact_replenishment_recommendation(recommended_supplier_id);

CREATE INDEX IF NOT EXISTS idx_frr_priority_level
    ON analytics.fact_replenishment_recommendation(priority_level);

CREATE INDEX IF NOT EXISTS idx_frr_approval_status
    ON analytics.fact_replenishment_recommendation(approval_status);