SET search_path TO analytics, public;

-- =========================================================
-- Phase 2.1A — Promotions + Price History Fact Tables
-- EDIP / NorthStar Retail & Distribution
-- =========================================================

-- ---------------------------------------------------------
-- 1) fact_promotions
-- Purpose:
--   Campaign / promotion windows that can later influence
--   sales demand, pricing, RAG memos, and executive reviews.
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.fact_promotions (
    promotion_id                 BIGINT PRIMARY KEY,
    promotion_code               VARCHAR(30) NOT NULL UNIQUE,
    promotion_name               VARCHAR(200) NOT NULL,
    campaign_type                VARCHAR(50) NOT NULL,
    promotion_status             VARCHAR(30) NOT NULL,
    product_id                   INTEGER NOT NULL,
    channel_id                   INTEGER NOT NULL,
    region_id                    INTEGER,
    start_date_id                INTEGER NOT NULL,
    end_date_id                  INTEGER NOT NULL,
    base_unit_price              DECIMAL(12,2) NOT NULL,
    promo_unit_price             DECIMAL(12,2) NOT NULL,
    discount_amount              DECIMAL(12,2) NOT NULL,
    discount_pct                 DECIMAL(6,2) NOT NULL,
    expected_uplift_pct          DECIMAL(6,2),
    actual_uplift_pct            DECIMAL(6,2),
    budget_amount                DECIMAL(14,2),
    promo_priority               VARCHAR(30) NOT NULL,
    stackable_flag               BOOLEAN NOT NULL DEFAULT FALSE,
    promo_reason                 VARCHAR(100),
    created_timestamp            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fact_promotions_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_fact_promotions_channel
        FOREIGN KEY (channel_id)
        REFERENCES analytics.dim_channel(channel_id),

    CONSTRAINT fk_fact_promotions_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id),

    CONSTRAINT fk_fact_promotions_start_date
        FOREIGN KEY (start_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fact_promotions_end_date
        FOREIGN KEY (end_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT chk_fact_promotions_date_window
        CHECK (end_date_id >= start_date_id),

    CONSTRAINT chk_fact_promotions_price_logic
        CHECK (
            base_unit_price > 0
            AND promo_unit_price > 0
            AND promo_unit_price <= base_unit_price
        ),

    CONSTRAINT chk_fact_promotions_discount_amount
        CHECK (discount_amount >= 0),

    CONSTRAINT chk_fact_promotions_discount_pct
        CHECK (discount_pct >= 0 AND discount_pct <= 100),

    CONSTRAINT chk_fact_promotions_uplift_pct
        CHECK (
            expected_uplift_pct IS NULL
            OR expected_uplift_pct >= 0
        ),

    CONSTRAINT chk_fact_promotions_actual_uplift_pct
        CHECK (
            actual_uplift_pct IS NULL
            OR actual_uplift_pct >= 0
        ),

    CONSTRAINT chk_fact_promotions_budget
        CHECK (budget_amount IS NULL OR budget_amount >= 0),

    CONSTRAINT chk_fact_promotions_status
        CHECK (
            LOWER(promotion_status) IN (
                'planned',
                'approved',
                'active',
                'completed',
                'cancelled'
            )
        ),

    CONSTRAINT chk_fact_promotions_priority
        CHECK (
            LOWER(promo_priority) IN (
                'high',
                'medium',
                'low'
            )
        )
);


-- ---------------------------------------------------------
-- 2) fact_price_history
-- Purpose:
--   Historical list/base/promo price windows for each
--   product-channel-region combination.
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.fact_price_history (
    price_history_id             BIGINT PRIMARY KEY,
    product_id                   INTEGER NOT NULL,
    channel_id                   INTEGER NOT NULL,
    region_id                    INTEGER,
    effective_start_date_id      INTEGER NOT NULL,
    effective_end_date_id        INTEGER NOT NULL,
    list_price                   DECIMAL(12,2) NOT NULL,
    selling_price                DECIMAL(12,2) NOT NULL,
    promo_price                  DECIMAL(12,2),
    markdown_pct                 DECIMAL(6,2) NOT NULL DEFAULT 0,
    price_change_reason          VARCHAR(100) NOT NULL,
    price_status                 VARCHAR(30) NOT NULL,
    is_promo_price_flag          BOOLEAN NOT NULL DEFAULT FALSE,
    source_promotion_id          BIGINT,
    created_timestamp            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fact_price_history_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_fact_price_history_channel
        FOREIGN KEY (channel_id)
        REFERENCES analytics.dim_channel(channel_id),

    CONSTRAINT fk_fact_price_history_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id),

    CONSTRAINT fk_fact_price_history_start_date
        FOREIGN KEY (effective_start_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fact_price_history_end_date
        FOREIGN KEY (effective_end_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fact_price_history_promotion
        FOREIGN KEY (source_promotion_id)
        REFERENCES analytics.fact_promotions(promotion_id),

    CONSTRAINT chk_fact_price_history_date_window
        CHECK (effective_end_date_id >= effective_start_date_id),

    CONSTRAINT chk_fact_price_history_list_price
        CHECK (list_price > 0),

    CONSTRAINT chk_fact_price_history_selling_price
        CHECK (selling_price > 0 AND selling_price <= list_price),

    CONSTRAINT chk_fact_price_history_promo_price
        CHECK (
            promo_price IS NULL
            OR (promo_price > 0 AND promo_price <= list_price)
        ),

    CONSTRAINT chk_fact_price_history_markdown_pct
        CHECK (markdown_pct >= 0 AND markdown_pct <= 100),

    CONSTRAINT chk_fact_price_history_status
        CHECK (
            LOWER(price_status) IN (
                'scheduled',
                'active',
                'expired'
            )
        )
);


-- ---------------------------------------------------------
-- 3) Helpful indexes
-- ---------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fp_product_id
    ON analytics.fact_promotions(product_id);

CREATE INDEX IF NOT EXISTS idx_fp_channel_id
    ON analytics.fact_promotions(channel_id);

CREATE INDEX IF NOT EXISTS idx_fp_region_id
    ON analytics.fact_promotions(region_id);

CREATE INDEX IF NOT EXISTS idx_fp_start_end_date
    ON analytics.fact_promotions(start_date_id, end_date_id);

CREATE INDEX IF NOT EXISTS idx_fp_status
    ON analytics.fact_promotions(promotion_status);

CREATE INDEX IF NOT EXISTS idx_fp_product_channel_region
    ON analytics.fact_promotions(product_id, channel_id, region_id);

CREATE INDEX IF NOT EXISTS idx_fph_product_id
    ON analytics.fact_price_history(product_id);

CREATE INDEX IF NOT EXISTS idx_fph_channel_id
    ON analytics.fact_price_history(channel_id);

CREATE INDEX IF NOT EXISTS idx_fph_region_id
    ON analytics.fact_price_history(region_id);

CREATE INDEX IF NOT EXISTS idx_fph_effective_dates
    ON analytics.fact_price_history(effective_start_date_id, effective_end_date_id);

CREATE INDEX IF NOT EXISTS idx_fph_product_channel_region
    ON analytics.fact_price_history(product_id, channel_id, region_id);

CREATE INDEX IF NOT EXISTS idx_fph_source_promotion_id
    ON analytics.fact_price_history(source_promotion_id);