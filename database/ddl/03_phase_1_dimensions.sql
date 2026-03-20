-- ============================================
-- EDIP / NorthStar Retail & Distribution
-- Phase 1.1A : Core Dimension Schema
-- File: 03_phase_1_dimensions.sql
-- Target Schema: analytics
-- ============================================

SET search_path TO analytics;

-- ============================================
-- 1) dim_calendar
-- Shared enterprise calendar dimension
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_calendar (
    date_id         INTEGER PRIMARY KEY,              -- YYYYMMDD
    full_date       DATE NOT NULL UNIQUE,
    day_of_week     VARCHAR(10) NOT NULL,
    week_of_year    INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      VARCHAR(15) NOT NULL,
    quarter         INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    is_weekend      BOOLEAN NOT NULL,
    is_month_end    BOOLEAN NOT NULL,
    season_name     VARCHAR(20) NOT NULL,
    holiday_flag    BOOLEAN NOT NULL
);

-- ============================================
-- 2) dim_region
-- Business geography for reporting and planning
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_region (
    region_id           INTEGER PRIMARY KEY,
    region_code         VARCHAR(20) NOT NULL UNIQUE,
    region_name         VARCHAR(100) NOT NULL,
    country_name        VARCHAR(100) NOT NULL,
    market_type         VARCHAR(50) NOT NULL,
    climate_zone        VARCHAR(50),
    demand_volatility   VARCHAR(20),
    active_flag         BOOLEAN NOT NULL
);

-- ============================================
-- 3) dim_store
-- Physical retail network
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_store (
    store_id                 INTEGER PRIMARY KEY,
    store_code               VARCHAR(20) NOT NULL UNIQUE,
    store_name               VARCHAR(150) NOT NULL,
    region_id                INTEGER NOT NULL,
    store_type               VARCHAR(50) NOT NULL,
    city                     VARCHAR(100) NOT NULL,
    opening_date             DATE NOT NULL,
    store_status             VARCHAR(30) NOT NULL,
    floor_area_sqft          INTEGER,
    daily_capacity_units     INTEGER,
    manager_name             VARCHAR(100),
    CONSTRAINT fk_dim_store_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id)
);

-- ============================================
-- 4) dim_warehouse
-- Warehouse network
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_warehouse (
    warehouse_id               INTEGER PRIMARY KEY,
    warehouse_code             VARCHAR(20) NOT NULL UNIQUE,
    warehouse_name             VARCHAR(150) NOT NULL,
    region_id                  INTEGER NOT NULL,
    city                       VARCHAR(100) NOT NULL,
    warehouse_type             VARCHAR(50) NOT NULL,
    storage_capacity_units     INTEGER NOT NULL,
    operating_status           VARCHAR(30) NOT NULL,
    manager_name               VARCHAR(100),
    CONSTRAINT fk_dim_warehouse_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id)
);

-- ============================================
-- 5) dim_channel
-- Sales channel definition
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_channel (
    channel_id        INTEGER PRIMARY KEY,
    channel_code      VARCHAR(20) NOT NULL UNIQUE,
    channel_name      VARCHAR(100) NOT NULL,
    channel_group     VARCHAR(50) NOT NULL,
    is_online_flag    BOOLEAN NOT NULL
);

-- ============================================
-- 6) dim_supplier
-- Supplier master
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_supplier (
    supplier_id           INTEGER PRIMARY KEY,
    supplier_code         VARCHAR(20) NOT NULL UNIQUE,
    supplier_name         VARCHAR(150) NOT NULL,
    supplier_tier         VARCHAR(30) NOT NULL,
    region_served         VARCHAR(100) NOT NULL,
    lead_time_days_avg    INTEGER NOT NULL,
    on_time_rate          DECIMAL(5,2) NOT NULL,
    quality_score         DECIMAL(5,2) NOT NULL,
    contract_start_date   DATE NOT NULL,
    contract_end_date     DATE,
    active_flag           BOOLEAN NOT NULL
);

-- ============================================
-- 7) dim_product
-- Product master
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_product (
    product_id               INTEGER PRIMARY KEY,
    sku_code                 VARCHAR(30) NOT NULL UNIQUE,
    product_name             VARCHAR(200) NOT NULL,
    category                 VARCHAR(100) NOT NULL,
    subcategory              VARCHAR(100) NOT NULL,
    brand                    VARCHAR(100) NOT NULL,
    unit_cost                DECIMAL(12,2) NOT NULL,
    list_price               DECIMAL(12,2) NOT NULL,
    supplier_id              INTEGER NOT NULL,
    shelf_life_days          INTEGER,
    reorder_point_default    INTEGER NOT NULL,
    safety_stock_default     INTEGER NOT NULL,
    launch_date              DATE NOT NULL,
    active_flag              BOOLEAN NOT NULL,
    CONSTRAINT fk_dim_product_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES analytics.dim_supplier(supplier_id),
    CONSTRAINT chk_dim_product_price_positive
        CHECK (unit_cost >= 0 AND list_price >= 0),
    CONSTRAINT chk_dim_product_price_logic
        CHECK (list_price >= unit_cost),
    CONSTRAINT chk_dim_product_stock_logic
        CHECK (reorder_point_default >= 0 AND safety_stock_default >= 0)
);

-- ============================================
-- 8) dim_customer
-- Customer master
-- ============================================
CREATE TABLE IF NOT EXISTS analytics.dim_customer (
    customer_id               BIGINT PRIMARY KEY,
    customer_code             VARCHAR(30) NOT NULL UNIQUE,
    customer_segment          VARCHAR(50) NOT NULL,
    region_id                 INTEGER NOT NULL,
    signup_date               DATE NOT NULL,
    loyalty_tier              VARCHAR(30),
    preferred_channel_id      INTEGER NOT NULL,
    lifetime_value_band       VARCHAR(30) NOT NULL,
    active_flag               BOOLEAN NOT NULL,
    CONSTRAINT fk_dim_customer_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id),
    CONSTRAINT fk_dim_customer_channel
        FOREIGN KEY (preferred_channel_id)
        REFERENCES analytics.dim_channel(channel_id)
);

-- ============================================
-- Helpful indexes for future joins
-- ============================================
CREATE INDEX IF NOT EXISTS idx_dim_store_region_id
    ON analytics.dim_store(region_id);

CREATE INDEX IF NOT EXISTS idx_dim_warehouse_region_id
    ON analytics.dim_warehouse(region_id);

CREATE INDEX IF NOT EXISTS idx_dim_product_supplier_id
    ON analytics.dim_product(supplier_id);

CREATE INDEX IF NOT EXISTS idx_dim_customer_region_id
    ON analytics.dim_customer(region_id);

CREATE INDEX IF NOT EXISTS idx_dim_customer_preferred_channel_id
    ON analytics.dim_customer(preferred_channel_id);