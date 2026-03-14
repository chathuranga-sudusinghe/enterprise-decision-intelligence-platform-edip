SET search_path TO analytics, public;

-- =========================================================
-- Phase 4.1A — Planner Overrides + Decision Logs Fact Tables
-- EDIP / NorthStar Retail & Distribution
-- File: 08_phase_4_planner_overrides_decision_logs.sql
-- =========================================================


-- =========================================================
-- 1) fact_planner_override
-- Purpose:
--   Human planner override of a system-generated
--   replenishment recommendation.
--   One row = one override action on one recommendation.
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_planner_override (
    planner_override_id              BIGINT PRIMARY KEY,
    recommendation_id                BIGINT NOT NULL,
    forecast_run_id                  BIGINT NOT NULL,
    override_date_id                 INTEGER NOT NULL,

    product_id                       INTEGER NOT NULL,
    target_store_id                  INTEGER,
    target_warehouse_id              INTEGER,

    original_order_qty               INTEGER NOT NULL DEFAULT 0,
    original_transfer_qty            INTEGER NOT NULL DEFAULT 0,
    overridden_order_qty             INTEGER NOT NULL DEFAULT 0,
    overridden_transfer_qty          INTEGER NOT NULL DEFAULT 0,

    override_type                    VARCHAR(30) NOT NULL,
    override_reason_code             VARCHAR(100) NOT NULL,
    planner_name                     VARCHAR(100) NOT NULL,
    planner_role                     VARCHAR(50) NOT NULL,

    approval_status                  VARCHAR(30) NOT NULL,
    impact_score                     DECIMAL(6,4) NOT NULL,
    comment_text                     VARCHAR(500),

    created_timestamp                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fpo_override_recommendation
        FOREIGN KEY (recommendation_id)
        REFERENCES analytics.fact_replenishment_recommendation(recommendation_id),

    CONSTRAINT fk_fpo_override_date
        FOREIGN KEY (override_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fpo_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_fpo_target_store
        FOREIGN KEY (target_store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_fpo_target_warehouse
        FOREIGN KEY (target_warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT chk_fpo_original_qty_nonnegative
        CHECK (
            original_order_qty >= 0
            AND original_transfer_qty >= 0
        ),

    CONSTRAINT chk_fpo_override_qty_nonnegative
        CHECK (
            overridden_order_qty >= 0
            AND overridden_transfer_qty >= 0
        ),

    CONSTRAINT chk_fpo_location_presence
        CHECK (
            target_store_id IS NOT NULL
            OR target_warehouse_id IS NOT NULL
        ),

    CONSTRAINT chk_fpo_single_location_type
        CHECK (
            NOT (target_store_id IS NOT NULL AND target_warehouse_id IS NOT NULL)
        ),

    CONSTRAINT chk_fpo_override_type
        CHECK (
            LOWER(override_type) IN (
                'increase_order',
                'decrease_order',
                'increase_transfer',
                'decrease_transfer',
                'cancel_recommendation',
                'approve_as_is',
                'reroute_transfer'
            )
        ),

    CONSTRAINT chk_fpo_approval_status
        CHECK (
            LOWER(approval_status) IN (
                'draft',
                'pending',
                'approved',
                'rejected',
                'executed'
            )
        ),

    CONSTRAINT chk_fpo_impact_score
        CHECK (impact_score >= 0 AND impact_score <= 1),

    CONSTRAINT chk_fpo_some_final_action
        CHECK (
            overridden_order_qty > 0
            OR overridden_transfer_qty > 0
            OR LOWER(override_type) = 'cancel_recommendation'
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fpo_recommendation_override
    ON analytics.fact_planner_override(recommendation_id);

CREATE INDEX IF NOT EXISTS idx_fpo_forecast_run_id
    ON analytics.fact_planner_override(forecast_run_id);

CREATE INDEX IF NOT EXISTS idx_fpo_override_date_id
    ON analytics.fact_planner_override(override_date_id);

CREATE INDEX IF NOT EXISTS idx_fpo_product_id
    ON analytics.fact_planner_override(product_id);

CREATE INDEX IF NOT EXISTS idx_fpo_target_store_id
    ON analytics.fact_planner_override(target_store_id);

CREATE INDEX IF NOT EXISTS idx_fpo_target_warehouse_id
    ON analytics.fact_planner_override(target_warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fpo_override_type
    ON analytics.fact_planner_override(override_type);

CREATE INDEX IF NOT EXISTS idx_fpo_approval_status
    ON analytics.fact_planner_override(approval_status);


-- =========================================================
-- 2) fact_decision_log
-- Purpose:
--   Final decision-history record for major planning /
--   replenishment actions and exceptions.
--   One row = one decision event.
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_decision_log (
    decision_log_id                  BIGINT PRIMARY KEY,
    decision_date_id                 INTEGER NOT NULL,
    forecast_run_id                  BIGINT,

    recommendation_id                BIGINT,
    planner_override_id              BIGINT,

    product_id                       INTEGER,
    region_id                        INTEGER,
    target_store_id                  INTEGER,
    target_warehouse_id              INTEGER,

    decision_type                    VARCHAR(50) NOT NULL,
    decision_status                  VARCHAR(30) NOT NULL,
    decision_source                  VARCHAR(30) NOT NULL,

    final_order_qty                  INTEGER NOT NULL DEFAULT 0,
    final_transfer_qty               INTEGER NOT NULL DEFAULT 0,

    service_level_target             DECIMAL(6,4),
    expected_stockout_risk           DECIMAL(6,4),
    expected_service_level           DECIMAL(6,4),

    escalation_flag                  BOOLEAN NOT NULL DEFAULT FALSE,
    exception_flag                   BOOLEAN NOT NULL DEFAULT FALSE,
    decision_reason_code             VARCHAR(100) NOT NULL,
    decided_by                       VARCHAR(100) NOT NULL,

    created_timestamp                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fdl_decision_date
        FOREIGN KEY (decision_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fdl_recommendation
        FOREIGN KEY (recommendation_id)
        REFERENCES analytics.fact_replenishment_recommendation(recommendation_id),

    CONSTRAINT fk_fdl_planner_override
        FOREIGN KEY (planner_override_id)
        REFERENCES analytics.fact_planner_override(planner_override_id),

    CONSTRAINT fk_fdl_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_fdl_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id),

    CONSTRAINT fk_fdl_target_store
        FOREIGN KEY (target_store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_fdl_target_warehouse
        FOREIGN KEY (target_warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT chk_fdl_final_qty_nonnegative
        CHECK (
            final_order_qty >= 0
            AND final_transfer_qty >= 0
        ),

    CONSTRAINT chk_fdl_decision_type
        CHECK (
            LOWER(decision_type) IN (
                'replenishment_approved',
                'replenishment_overridden',
                'replenishment_rejected',
                'transfer_rerouted',
                'expedite_order',
                'exception_escalated'
            )
        ),

    CONSTRAINT chk_fdl_decision_status
        CHECK (
            LOWER(decision_status) IN (
                'draft',
                'pending',
                'approved',
                'rejected',
                'executed',
                'escalated'
            )
        ),

    CONSTRAINT chk_fdl_decision_source
        CHECK (
            LOWER(decision_source) IN (
                'system',
                'planner',
                'manager',
                'hybrid'
            )
        ),

    CONSTRAINT chk_fdl_service_level_target
        CHECK (
            service_level_target IS NULL
            OR (service_level_target >= 0 AND service_level_target <= 1)
        ),

    CONSTRAINT chk_fdl_stockout_risk
        CHECK (
            expected_stockout_risk IS NULL
            OR (expected_stockout_risk >= 0 AND expected_stockout_risk <= 1)
        ),

    CONSTRAINT chk_fdl_service_level
        CHECK (
            expected_service_level IS NULL
            OR (expected_service_level >= 0 AND expected_service_level <= 1)
        ),

    CONSTRAINT chk_fdl_single_location_type
        CHECK (
            NOT (target_store_id IS NOT NULL AND target_warehouse_id IS NOT NULL)
        ),

    CONSTRAINT chk_fdl_decision_anchor
        CHECK (
            recommendation_id IS NOT NULL
            OR planner_override_id IS NOT NULL
        ),

    CONSTRAINT chk_fdl_some_final_action
        CHECK (
            final_order_qty > 0
            OR final_transfer_qty > 0
            OR LOWER(decision_status) IN ('rejected', 'escalated')
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fdl_decision_event
    ON analytics.fact_decision_log (
        decision_date_id,
        COALESCE(recommendation_id, -1),
        COALESCE(planner_override_id, -1),
        decision_type
    );

CREATE INDEX IF NOT EXISTS idx_fdl_forecast_run_id
    ON analytics.fact_decision_log(forecast_run_id);

CREATE INDEX IF NOT EXISTS idx_fdl_decision_date_id
    ON analytics.fact_decision_log(decision_date_id);

CREATE INDEX IF NOT EXISTS idx_fdl_recommendation_id
    ON analytics.fact_decision_log(recommendation_id);

CREATE INDEX IF NOT EXISTS idx_fdl_planner_override_id
    ON analytics.fact_decision_log(planner_override_id);

CREATE INDEX IF NOT EXISTS idx_fdl_product_id
    ON analytics.fact_decision_log(product_id);

CREATE INDEX IF NOT EXISTS idx_fdl_region_id
    ON analytics.fact_decision_log(region_id);

CREATE INDEX IF NOT EXISTS idx_fdl_target_store_id
    ON analytics.fact_decision_log(target_store_id);

CREATE INDEX IF NOT EXISTS idx_fdl_target_warehouse_id
    ON analytics.fact_decision_log(target_warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fdl_decision_type
    ON analytics.fact_decision_log(decision_type);

CREATE INDEX IF NOT EXISTS idx_fdl_decision_status
    ON analytics.fact_decision_log(decision_status);

CREATE INDEX IF NOT EXISTS idx_fdl_decision_source
    ON analytics.fact_decision_log(decision_source);