SET search_path TO analytics, public;

-- =========================================================
-- Phase 2.1A — Sales / Commercial Fact Tables
-- EDIP / NorthStar Retail & Distribution
-- =========================================================


-- =========================================================
-- 1) fact_orders
-- One row = one customer order header
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_orders (
    order_id                     BIGINT PRIMARY KEY,
    order_number                 VARCHAR(30) NOT NULL UNIQUE,
    order_date_id                INTEGER NOT NULL,

    customer_id                  BIGINT NOT NULL,
    channel_id                   INTEGER NOT NULL,
    store_id                     INTEGER,
    region_id                    INTEGER NOT NULL,

    order_status                 VARCHAR(30) NOT NULL,
    payment_status               VARCHAR(30) NOT NULL,
    fulfillment_type             VARCHAR(30) NOT NULL,

    item_count                   INTEGER NOT NULL,
    total_units                  INTEGER NOT NULL,

    gross_order_amount           DECIMAL(14,2) NOT NULL,
    discount_amount              DECIMAL(14,2) NOT NULL DEFAULT 0,
    shipping_fee                 DECIMAL(14,2) NOT NULL DEFAULT 0,
    tax_amount                   DECIMAL(14,2) NOT NULL DEFAULT 0,
    net_order_amount             DECIMAL(14,2) NOT NULL,

    currency_code                VARCHAR(10) NOT NULL DEFAULT 'USD',
    order_created_timestamp      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fo_order_date
        FOREIGN KEY (order_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fo_customer
        FOREIGN KEY (customer_id)
        REFERENCES analytics.dim_customer(customer_id),

    CONSTRAINT fk_fo_channel
        FOREIGN KEY (channel_id)
        REFERENCES analytics.dim_channel(channel_id),

    CONSTRAINT fk_fo_store
        FOREIGN KEY (store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_fo_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id),

    CONSTRAINT chk_fo_order_status
        CHECK (order_status IN (
            'created',
            'confirmed',
            'partially_fulfilled',
            'completed',
            'cancelled'
        )),

    CONSTRAINT chk_fo_payment_status
        CHECK (payment_status IN (
            'pending',
            'paid',
            'partially_refunded',
            'refunded',
            'failed'
        )),

    CONSTRAINT chk_fo_fulfillment_type
        CHECK (fulfillment_type IN (
            'in_store',
            'ship_from_store',
            'ship_from_warehouse',
            'click_and_collect'
        )),

    CONSTRAINT chk_fo_item_count_nonnegative
        CHECK (item_count >= 0),

    CONSTRAINT chk_fo_total_units_nonnegative
        CHECK (total_units >= 0),

    CONSTRAINT chk_fo_amounts_nonnegative
        CHECK (
            gross_order_amount >= 0
            AND discount_amount >= 0
            AND shipping_fee >= 0
            AND tax_amount >= 0
            AND net_order_amount >= 0
        ),

    CONSTRAINT chk_fo_net_amount_logic
        CHECK (
            net_order_amount = ROUND(
                gross_order_amount - discount_amount + shipping_fee + tax_amount,
                2
            )
        ),

    CONSTRAINT chk_fo_store_channel_logic
        CHECK (
            (store_id IS NOT NULL AND fulfillment_type IN ('in_store', 'ship_from_store', 'click_and_collect'))
            OR
            (store_id IS NULL AND fulfillment_type = 'ship_from_warehouse')
        )
);

CREATE INDEX IF NOT EXISTS idx_fo_order_date_id
    ON analytics.fact_orders(order_date_id);

CREATE INDEX IF NOT EXISTS idx_fo_customer_id
    ON analytics.fact_orders(customer_id);

CREATE INDEX IF NOT EXISTS idx_fo_channel_id
    ON analytics.fact_orders(channel_id);

CREATE INDEX IF NOT EXISTS idx_fo_store_id
    ON analytics.fact_orders(store_id);

CREATE INDEX IF NOT EXISTS idx_fo_region_id
    ON analytics.fact_orders(region_id);

CREATE INDEX IF NOT EXISTS idx_fo_order_status
    ON analytics.fact_orders(order_status);


-- =========================================================
-- 2) fact_order_items
-- One row = one order line
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_order_items (
    order_item_id                 BIGINT PRIMARY KEY,
    order_id                      BIGINT NOT NULL,
    order_line_number             INTEGER NOT NULL,

    order_date_id                 INTEGER NOT NULL,
    customer_id                   BIGINT NOT NULL,
    channel_id                    INTEGER NOT NULL,
    store_id                      INTEGER,
    warehouse_id                  INTEGER,
    region_id                     INTEGER NOT NULL,

    product_id                    INTEGER NOT NULL,

    ordered_qty                   INTEGER NOT NULL,
    allocated_qty                 INTEGER NOT NULL DEFAULT 0,
    fulfilled_qty                 INTEGER NOT NULL DEFAULT 0,
    cancelled_qty                 INTEGER NOT NULL DEFAULT 0,

    unit_list_price               DECIMAL(12,2) NOT NULL,
    unit_selling_price            DECIMAL(12,2) NOT NULL,
    line_discount_amount          DECIMAL(14,2) NOT NULL DEFAULT 0,
    gross_line_amount             DECIMAL(14,2) NOT NULL,
    net_line_amount               DECIMAL(14,2) NOT NULL,

    stockout_flag                 BOOLEAN NOT NULL DEFAULT FALSE,
    item_status                   VARCHAR(30) NOT NULL,

    created_timestamp             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_foi_order
        FOREIGN KEY (order_id)
        REFERENCES analytics.fact_orders(order_id),

    CONSTRAINT fk_foi_order_date
        FOREIGN KEY (order_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_foi_customer
        FOREIGN KEY (customer_id)
        REFERENCES analytics.dim_customer(customer_id),

    CONSTRAINT fk_foi_channel
        FOREIGN KEY (channel_id)
        REFERENCES analytics.dim_channel(channel_id),

    CONSTRAINT fk_foi_store
        FOREIGN KEY (store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_foi_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT fk_foi_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id),

    CONSTRAINT fk_foi_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT chk_foi_line_number_positive
        CHECK (order_line_number > 0),

    CONSTRAINT chk_foi_qty_nonnegative
        CHECK (
            ordered_qty >= 0
            AND allocated_qty >= 0
            AND fulfilled_qty >= 0
            AND cancelled_qty >= 0
        ),

    CONSTRAINT chk_foi_qty_balance
        CHECK (
            allocated_qty <= ordered_qty
            AND fulfilled_qty <= allocated_qty
            AND fulfilled_qty + cancelled_qty <= ordered_qty
        ),

    CONSTRAINT chk_foi_price_logic
        CHECK (
            unit_list_price >= 0
            AND unit_selling_price >= 0
            AND unit_selling_price <= unit_list_price
        ),

    CONSTRAINT chk_foi_amount_logic
        CHECK (
            gross_line_amount = ROUND(ordered_qty * unit_list_price, 2)
            AND net_line_amount = ROUND((fulfilled_qty * unit_selling_price) - line_discount_amount, 2)
            AND line_discount_amount >= 0
            AND net_line_amount >= 0
        ),

    CONSTRAINT chk_foi_item_status
        CHECK (item_status IN (
            'created',
            'allocated',
            'fulfilled',
            'partially_fulfilled',
            'cancelled',
            'stockout'
        )),

    CONSTRAINT chk_foi_location_logic
        CHECK (
            (store_id IS NOT NULL AND warehouse_id IS NULL)
            OR
            (store_id IS NULL AND warehouse_id IS NOT NULL)
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_foi_order_line
    ON analytics.fact_order_items(order_id, order_line_number);

CREATE INDEX IF NOT EXISTS idx_foi_order_id
    ON analytics.fact_order_items(order_id);

CREATE INDEX IF NOT EXISTS idx_foi_order_date_id
    ON analytics.fact_order_items(order_date_id);

CREATE INDEX IF NOT EXISTS idx_foi_product_id
    ON analytics.fact_order_items(product_id);

CREATE INDEX IF NOT EXISTS idx_foi_customer_id
    ON analytics.fact_order_items(customer_id);

CREATE INDEX IF NOT EXISTS idx_foi_channel_id
    ON analytics.fact_order_items(channel_id);

CREATE INDEX IF NOT EXISTS idx_foi_store_id
    ON analytics.fact_order_items(store_id);

CREATE INDEX IF NOT EXISTS idx_foi_warehouse_id
    ON analytics.fact_order_items(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_foi_region_id
    ON analytics.fact_order_items(region_id);

CREATE INDEX IF NOT EXISTS idx_foi_stockout_flag
    ON analytics.fact_order_items(stockout_flag);


-- =========================================================
-- 3) fact_sales
-- One row = one realized sale / fulfilled order line outcome
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_sales (
    sale_id                       BIGINT PRIMARY KEY,
    sale_date_id                  INTEGER NOT NULL,

    order_id                      BIGINT NOT NULL,
    order_item_id                 BIGINT NOT NULL,

    customer_id                   BIGINT NOT NULL,
    channel_id                    INTEGER NOT NULL,
    store_id                      INTEGER,
    warehouse_id                  INTEGER,
    region_id                     INTEGER NOT NULL,
    product_id                    INTEGER NOT NULL,

    units_sold                    INTEGER NOT NULL,

    unit_list_price               DECIMAL(12,2) NOT NULL,
    unit_selling_price            DECIMAL(12,2) NOT NULL,
    gross_sales_amount            DECIMAL(14,2) NOT NULL,
    discount_amount               DECIMAL(14,2) NOT NULL DEFAULT 0,
    net_sales_amount              DECIMAL(14,2) NOT NULL,

    unit_cost                     DECIMAL(12,2) NOT NULL,
    gross_margin_amount           DECIMAL(14,2) NOT NULL,

    fulfillment_type              VARCHAR(30) NOT NULL,
    sale_status                   VARCHAR(30) NOT NULL DEFAULT 'completed',

    created_timestamp             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fs_sale_date
        FOREIGN KEY (sale_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fs_order
        FOREIGN KEY (order_id)
        REFERENCES analytics.fact_orders(order_id),

    CONSTRAINT fk_fs_order_item
        FOREIGN KEY (order_item_id)
        REFERENCES analytics.fact_order_items(order_item_id),

    CONSTRAINT fk_fs_customer
        FOREIGN KEY (customer_id)
        REFERENCES analytics.dim_customer(customer_id),

    CONSTRAINT fk_fs_channel
        FOREIGN KEY (channel_id)
        REFERENCES analytics.dim_channel(channel_id),

    CONSTRAINT fk_fs_store
        FOREIGN KEY (store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_fs_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT fk_fs_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id),

    CONSTRAINT fk_fs_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT chk_fs_units_positive
        CHECK (units_sold > 0),

    CONSTRAINT chk_fs_price_logic
        CHECK (
            unit_list_price >= 0
            AND unit_selling_price >= 0
            AND unit_selling_price <= unit_list_price
            AND unit_cost >= 0
        ),

    CONSTRAINT chk_fs_amount_logic
        CHECK (
            gross_sales_amount = ROUND(units_sold * unit_list_price, 2)
            AND net_sales_amount = ROUND((units_sold * unit_selling_price) - discount_amount, 2)
            AND gross_margin_amount = ROUND(net_sales_amount - (units_sold * unit_cost), 2)
            AND discount_amount >= 0
        ),

    CONSTRAINT chk_fs_fulfillment_type
        CHECK (fulfillment_type IN (
            'in_store',
            'ship_from_store',
            'ship_from_warehouse',
            'click_and_collect'
        )),

    CONSTRAINT chk_fs_sale_status
        CHECK (sale_status IN ('completed', 'returned_partially', 'returned_fully')),

    CONSTRAINT chk_fs_location_logic
        CHECK (
            (store_id IS NOT NULL AND warehouse_id IS NULL)
            OR
            (store_id IS NULL AND warehouse_id IS NOT NULL)
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fs_order_item
    ON analytics.fact_sales(order_item_id);

CREATE INDEX IF NOT EXISTS idx_fs_sale_date_id
    ON analytics.fact_sales(sale_date_id);

CREATE INDEX IF NOT EXISTS idx_fs_order_id
    ON analytics.fact_sales(order_id);

CREATE INDEX IF NOT EXISTS idx_fs_customer_id
    ON analytics.fact_sales(customer_id);

CREATE INDEX IF NOT EXISTS idx_fs_product_id
    ON analytics.fact_sales(product_id);

CREATE INDEX IF NOT EXISTS idx_fs_channel_id
    ON analytics.fact_sales(channel_id);

CREATE INDEX IF NOT EXISTS idx_fs_store_id
    ON analytics.fact_sales(store_id);

CREATE INDEX IF NOT EXISTS idx_fs_warehouse_id
    ON analytics.fact_sales(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fs_region_id
    ON analytics.fact_sales(region_id);


-- =========================================================
-- 4) fact_returns
-- One row = one return line against a realized sale
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_returns (
    return_id                     BIGINT PRIMARY KEY,
    return_date_id                INTEGER NOT NULL,

    sale_id                       BIGINT NOT NULL,
    order_id                      BIGINT NOT NULL,
    order_item_id                 BIGINT NOT NULL,

    customer_id                   BIGINT NOT NULL,
    channel_id                    INTEGER NOT NULL,
    store_id                      INTEGER,
    warehouse_id                  INTEGER,
    region_id                     INTEGER NOT NULL,
    product_id                    INTEGER NOT NULL,

    returned_qty                  INTEGER NOT NULL,
    return_reason                 VARCHAR(50) NOT NULL,
    return_status                 VARCHAR(30) NOT NULL,

    refund_amount                 DECIMAL(14,2) NOT NULL,
    restockable_flag              BOOLEAN NOT NULL DEFAULT FALSE,
    damaged_flag                  BOOLEAN NOT NULL DEFAULT FALSE,
    inventory_disposition         VARCHAR(30) NOT NULL,

    created_timestamp             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fr_return_date
        FOREIGN KEY (return_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fr_sale
        FOREIGN KEY (sale_id)
        REFERENCES analytics.fact_sales(sale_id),

    CONSTRAINT fk_fr_order
        FOREIGN KEY (order_id)
        REFERENCES analytics.fact_orders(order_id),

    CONSTRAINT fk_fr_order_item
        FOREIGN KEY (order_item_id)
        REFERENCES analytics.fact_order_items(order_item_id),

    CONSTRAINT fk_fr_customer
        FOREIGN KEY (customer_id)
        REFERENCES analytics.dim_customer(customer_id),

    CONSTRAINT fk_fr_channel
        FOREIGN KEY (channel_id)
        REFERENCES analytics.dim_channel(channel_id),

    CONSTRAINT fk_fr_store
        FOREIGN KEY (store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_fr_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT fk_fr_region
        FOREIGN KEY (region_id)
        REFERENCES analytics.dim_region(region_id),

    CONSTRAINT fk_fr_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT chk_fr_returned_qty_positive
        CHECK (returned_qty > 0),

    CONSTRAINT chk_fr_refund_nonnegative
        CHECK (refund_amount >= 0),

    CONSTRAINT chk_fr_reason
        CHECK (return_reason IN (
            'damaged',
            'wrong_item',
            'customer_remorse',
            'quality_issue',
            'late_delivery',
            'other'
        )),

    CONSTRAINT chk_fr_status
        CHECK (return_status IN (
            'requested',
            'approved',
            'received',
            'refunded',
            'rejected'
        )),

    CONSTRAINT chk_fr_inventory_disposition
        CHECK (inventory_disposition IN (
            'restock',
            'damaged',
            'scrap',
            'vendor_return'
        )),

    CONSTRAINT chk_fr_flag_logic
        CHECK (
            NOT (restockable_flag = TRUE AND damaged_flag = TRUE)
        ),

    CONSTRAINT chk_fr_disposition_logic
        CHECK (
            (restockable_flag = TRUE AND damaged_flag = FALSE AND inventory_disposition = 'restock')
            OR
            (damaged_flag = TRUE AND restockable_flag = FALSE AND inventory_disposition IN ('damaged', 'scrap', 'vendor_return'))
            OR
            (restockable_flag = FALSE AND damaged_flag = FALSE AND inventory_disposition IN ('vendor_return', 'scrap'))
        ),

    CONSTRAINT chk_fr_location_logic
        CHECK (
            (store_id IS NOT NULL AND warehouse_id IS NULL)
            OR
            (store_id IS NULL AND warehouse_id IS NOT NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_fr_return_date_id
    ON analytics.fact_returns(return_date_id);

CREATE INDEX IF NOT EXISTS idx_fr_sale_id
    ON analytics.fact_returns(sale_id);

CREATE INDEX IF NOT EXISTS idx_fr_order_id
    ON analytics.fact_returns(order_id);

CREATE INDEX IF NOT EXISTS idx_fr_order_item_id
    ON analytics.fact_returns(order_item_id);

CREATE INDEX IF NOT EXISTS idx_fr_customer_id
    ON analytics.fact_returns(customer_id);

CREATE INDEX IF NOT EXISTS idx_fr_product_id
    ON analytics.fact_returns(product_id);

CREATE INDEX IF NOT EXISTS idx_fr_channel_id
    ON analytics.fact_returns(channel_id);

CREATE INDEX IF NOT EXISTS idx_fr_store_id
    ON analytics.fact_returns(store_id);

CREATE INDEX IF NOT EXISTS idx_fr_warehouse_id
    ON analytics.fact_returns(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fr_region_id
    ON analytics.fact_returns(region_id);

CREATE INDEX IF NOT EXISTS idx_fr_restockable_flag
    ON analytics.fact_returns(restockable_flag);

CREATE INDEX IF NOT EXISTS idx_fr_damaged_flag
    ON analytics.fact_returns(damaged_flag);