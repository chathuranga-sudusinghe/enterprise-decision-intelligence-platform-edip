-- ============================================
-- EDIP / NorthStar Retail & Distribution
-- Phase 1.3 : Load synthetic dimension CSVs
-- File: 01_load_phase_1_dimensions.sql
-- Target Schema: analytics
-- ============================================

SET search_path TO analytics;

-- --------------------------------------------
-- 1) clear old rows before reloading -- TRUNCATE TABLE: clean old data
-- --------------------------------------------
TRUNCATE TABLE   
    analytics.dim_customer,
    analytics.dim_product,
    analytics.dim_store,
    analytics.dim_warehouse,
    analytics.dim_supplier,
    analytics.dim_channel,
    analytics.dim_region,
    analytics.dim_calendar;

-- --------------------------------------------
-- 2) Load parent dimensions first
-- --------------------------------------------
\copy analytics.dim_calendar (date_id, full_date, day_of_week, week_of_year, month, month_name, quarter, year, is_weekend, is_month_end, season_name, holiday_flag) FROM './data/synthetic/dim_calendar.csv' DELIMITER ',' CSV HEADER;

\copy analytics.dim_region (region_id, region_code, region_name, country_name, market_type, climate_zone, demand_volatility, active_flag) FROM './data/synthetic/dim_region.csv' DELIMITER ',' CSV HEADER;

\copy analytics.dim_channel (channel_id, channel_code, channel_name, channel_group, is_online_flag) FROM './data/synthetic/dim_channel.csv' DELIMITER ',' CSV HEADER;

\copy analytics.dim_supplier (supplier_id, supplier_code, supplier_name, supplier_tier, region_served, lead_time_days_avg, on_time_rate, quality_score, contract_start_date, contract_end_date, active_flag) FROM './data/synthetic/dim_supplier.csv' DELIMITER ',' CSV HEADER;


-- --------------------------------------------
-- 3) Load dependent dimensions
-- --------------------------------------------
\copy analytics.dim_store (store_id, store_code, store_name, region_id, store_type, city, opening_date, store_status, floor_area_sqft, daily_capacity_units, manager_name) FROM './data/synthetic/dim_store.csv' DELIMITER ',' CSV HEADER;

\copy analytics.dim_warehouse (warehouse_id, warehouse_code, warehouse_name, region_id, city, warehouse_type, storage_capacity_units, operating_status, manager_name) FROM './data/synthetic/dim_warehouse.csv' DELIMITER ',' CSV HEADER;

\copy analytics.dim_product (product_id, sku_code, product_name, category, subcategory, brand, unit_cost, list_price, supplier_id, shelf_life_days, reorder_point_default, safety_stock_default, launch_date, active_flag) FROM './data/synthetic/dim_product.csv' DELIMITER ',' CSV HEADER;

\copy analytics.dim_customer (customer_id, customer_code, customer_segment, region_id, signup_date, loyalty_tier, preferred_channel_id, lifetime_value_band, active_flag) FROM './data/synthetic/dim_customer.csv' DELIMITER ',' CSV HEADER;
