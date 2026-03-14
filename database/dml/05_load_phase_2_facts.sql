SET search_path TO analytics, public;

-- =========================================================
-- Phase 2.1C — Load Sales / Commercial Facts
-- EDIP / NorthStar Retail & Distribution
-- =========================================================

-- ---------------------------------------------------------
-- Optional performance cleanup
-- ---------------------------------------------------------
DROP INDEX IF EXISTS analytics.idx_fr_return_date_id;
DROP INDEX IF EXISTS analytics.idx_fr_sale_id;
DROP INDEX IF EXISTS analytics.idx_fr_order_id;
DROP INDEX IF EXISTS analytics.idx_fr_order_item_id;
DROP INDEX IF EXISTS analytics.idx_fr_customer_id;
DROP INDEX IF EXISTS analytics.idx_fr_product_id;
DROP INDEX IF EXISTS analytics.idx_fr_channel_id;
DROP INDEX IF EXISTS analytics.idx_fr_store_id;
DROP INDEX IF EXISTS analytics.idx_fr_warehouse_id;
DROP INDEX IF EXISTS analytics.idx_fr_region_id;
DROP INDEX IF EXISTS analytics.idx_fr_restockable_flag;
DROP INDEX IF EXISTS analytics.idx_fr_damaged_flag;

DROP INDEX IF EXISTS analytics.ux_fs_order_item;
DROP INDEX IF EXISTS analytics.idx_fs_sale_date_id;
DROP INDEX IF EXISTS analytics.idx_fs_order_id;
DROP INDEX IF EXISTS analytics.idx_fs_customer_id;
DROP INDEX IF EXISTS analytics.idx_fs_product_id;
DROP INDEX IF EXISTS analytics.idx_fs_channel_id;
DROP INDEX IF EXISTS analytics.idx_fs_store_id;
DROP INDEX IF EXISTS analytics.idx_fs_warehouse_id;
DROP INDEX IF EXISTS analytics.idx_fs_region_id;

DROP INDEX IF EXISTS analytics.ux_foi_order_line;
DROP INDEX IF EXISTS analytics.idx_foi_order_id;
DROP INDEX IF EXISTS analytics.idx_foi_order_date_id;
DROP INDEX IF EXISTS analytics.idx_foi_product_id;
DROP INDEX IF EXISTS analytics.idx_foi_customer_id;
DROP INDEX IF EXISTS analytics.idx_foi_channel_id;
DROP INDEX IF EXISTS analytics.idx_foi_store_id;
DROP INDEX IF EXISTS analytics.idx_foi_warehouse_id;
DROP INDEX IF EXISTS analytics.idx_foi_region_id;
DROP INDEX IF EXISTS analytics.idx_foi_stockout_flag;

DROP INDEX IF EXISTS analytics.idx_fo_order_date_id;
DROP INDEX IF EXISTS analytics.idx_fo_customer_id;
DROP INDEX IF EXISTS analytics.idx_fo_channel_id;
DROP INDEX IF EXISTS analytics.idx_fo_store_id;
DROP INDEX IF EXISTS analytics.idx_fo_region_id;
DROP INDEX IF EXISTS analytics.idx_fo_order_status;

-- ---------------------------------------------------------
-- Truncate in child-to-parent order
-- ---------------------------------------------------------
BEGIN;

TRUNCATE TABLE
    analytics.fact_returns,
    analytics.fact_sales,
    analytics.fact_order_items,
    analytics.fact_orders;

COMMIT;
-- ---------------------------------------------------------
-- Load fact_orders
-- ---------------------------------------------------------
\copy analytics.fact_orders (order_id, order_number, order_date_id, customer_id, channel_id, store_id, region_id, order_status, payment_status, fulfillment_type, item_count, total_units, gross_order_amount, discount_amount, shipping_fee, tax_amount, net_order_amount, currency_code, order_created_timestamp) FROM './data/synthetic/fact_orders.csv' WITH (FORMAT csv, HEADER true);

-- ---------------------------------------------------------
-- Load fact_order_items
-- ---------------------------------------------------------
\copy analytics.fact_order_items (order_item_id, order_id, order_line_number, order_date_id, customer_id, channel_id, store_id, warehouse_id, region_id, product_id, ordered_qty, allocated_qty, fulfilled_qty, cancelled_qty, unit_list_price, unit_selling_price, line_discount_amount, gross_line_amount, net_line_amount, stockout_flag, item_status, created_timestamp) FROM './data/synthetic/fact_order_items.csv' WITH (FORMAT csv, HEADER true);
-- ---------------------------------------------------------
-- Load fact_sales
-- ---------------------------------------------------------
\copy analytics.fact_sales (sale_id, sale_date_id, order_id, order_item_id, customer_id, channel_id, store_id, warehouse_id, region_id, product_id, units_sold, unit_list_price, unit_selling_price, gross_sales_amount, discount_amount, net_sales_amount, unit_cost, gross_margin_amount, fulfillment_type, sale_status, created_timestamp) FROM './data/synthetic/fact_sales.csv' WITH (FORMAT csv, HEADER true);

-- ---------------------------------------------------------
-- Load fact_returns
-- ---------------------------------------------------------
\copy analytics.fact_returns (return_id, return_date_id, sale_id, order_id, order_item_id, customer_id, channel_id, store_id, warehouse_id, region_id, product_id, returned_qty, return_reason, return_status, refund_amount, restockable_flag, damaged_flag, inventory_disposition, created_timestamp) FROM './data/synthetic/fact_returns.csv' WITH (FORMAT csv, HEADER true);

-- ---------------------------------------------------------
-- Recreate indexes
-- ---------------------------------------------------------

-- fact_orders
CREATE INDEX idx_fo_order_date_id
    ON analytics.fact_orders(order_date_id);

CREATE INDEX idx_fo_customer_id
    ON analytics.fact_orders(customer_id);

CREATE INDEX idx_fo_channel_id
    ON analytics.fact_orders(channel_id);

CREATE INDEX idx_fo_store_id
    ON analytics.fact_orders(store_id);

CREATE INDEX idx_fo_region_id
    ON analytics.fact_orders(region_id);

CREATE INDEX idx_fo_order_status
    ON analytics.fact_orders(order_status);

-- fact_order_items
CREATE UNIQUE INDEX ux_foi_order_line
    ON analytics.fact_order_items(order_id, order_line_number);

CREATE INDEX idx_foi_order_id
    ON analytics.fact_order_items(order_id);

CREATE INDEX idx_foi_order_date_id
    ON analytics.fact_order_items(order_date_id);

CREATE INDEX idx_foi_product_id
    ON analytics.fact_order_items(product_id);

CREATE INDEX idx_foi_customer_id
    ON analytics.fact_order_items(customer_id);

CREATE INDEX idx_foi_channel_id
    ON analytics.fact_order_items(channel_id);

CREATE INDEX idx_foi_store_id
    ON analytics.fact_order_items(store_id);

CREATE INDEX idx_foi_warehouse_id
    ON analytics.fact_order_items(warehouse_id);

CREATE INDEX idx_foi_region_id
    ON analytics.fact_order_items(region_id);

CREATE INDEX idx_foi_stockout_flag
    ON analytics.fact_order_items(stockout_flag);

-- fact_sales
CREATE UNIQUE INDEX ux_fs_order_item
    ON analytics.fact_sales(order_item_id);

CREATE INDEX idx_fs_sale_date_id
    ON analytics.fact_sales(sale_date_id);

CREATE INDEX idx_fs_order_id
    ON analytics.fact_sales(order_id);

CREATE INDEX idx_fs_customer_id
    ON analytics.fact_sales(customer_id);

CREATE INDEX idx_fs_product_id
    ON analytics.fact_sales(product_id);

CREATE INDEX idx_fs_channel_id
    ON analytics.fact_sales(channel_id);

CREATE INDEX idx_fs_store_id
    ON analytics.fact_sales(store_id);

CREATE INDEX idx_fs_warehouse_id
    ON analytics.fact_sales(warehouse_id);

CREATE INDEX idx_fs_region_id
    ON analytics.fact_sales(region_id);

-- fact_returns
CREATE INDEX idx_fr_return_date_id
    ON analytics.fact_returns(return_date_id);

CREATE INDEX idx_fr_sale_id
    ON analytics.fact_returns(sale_id);

CREATE INDEX idx_fr_order_id
    ON analytics.fact_returns(order_id);

CREATE INDEX idx_fr_order_item_id
    ON analytics.fact_returns(order_item_id);

CREATE INDEX idx_fr_customer_id
    ON analytics.fact_returns(customer_id);

CREATE INDEX idx_fr_product_id
    ON analytics.fact_returns(product_id);

CREATE INDEX idx_fr_channel_id
    ON analytics.fact_returns(channel_id);

CREATE INDEX idx_fr_store_id
    ON analytics.fact_returns(store_id);

CREATE INDEX idx_fr_warehouse_id
    ON analytics.fact_returns(warehouse_id);

CREATE INDEX idx_fr_region_id
    ON analytics.fact_returns(region_id);

CREATE INDEX idx_fr_restockable_flag
    ON analytics.fact_returns(restockable_flag);

CREATE INDEX idx_fr_damaged_flag
    ON analytics.fact_returns(damaged_flag);