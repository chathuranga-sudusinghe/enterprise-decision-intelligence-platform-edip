SET search_path TO analytics, public;

-- =========================================================
-- Phase 1.5A — Procurement / Inventory Fact Tables
-- EDIP / NorthStar Retail & Distribution
-- =========================================================

-- =========================================================
-- 1) fact_purchase_orders
-- Supplier purchase order header/line grain
-- One row = one PO line
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_purchase_orders (
    po_line_id                    BIGINT PRIMARY KEY,
    purchase_order_id             BIGINT NOT NULL,
    po_number                     VARCHAR(30) NOT NULL,
    po_date_id                    INTEGER NOT NULL,
    expected_receipt_date_id      INTEGER NOT NULL,

    supplier_id                   INTEGER NOT NULL,
    warehouse_id                  INTEGER NOT NULL,
    product_id                    INTEGER NOT NULL,

    ordered_qty                   INTEGER NOT NULL,
    unit_cost                     DECIMAL(12,2) NOT NULL,
    line_amount                   DECIMAL(14,2) NOT NULL,

    currency_code                 VARCHAR(10) NOT NULL DEFAULT 'USD',
    order_status                  VARCHAR(30) NOT NULL,
    priority_level                VARCHAR(20) NOT NULL,
    buyer_name                    VARCHAR(100),
    contract_reference            VARCHAR(50),
    created_timestamp             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fpo_po_date
        FOREIGN KEY (po_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fpo_expected_receipt_date
        FOREIGN KEY (expected_receipt_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fpo_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES analytics.dim_supplier(supplier_id),

    CONSTRAINT fk_fpo_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT fk_fpo_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT chk_fpo_qty_positive
        CHECK (ordered_qty > 0),

    CONSTRAINT chk_fpo_unit_cost_positive
        CHECK (unit_cost > 0),

    CONSTRAINT chk_fpo_line_amount_nonnegative
        CHECK (line_amount >= 0),

    CONSTRAINT chk_fpo_status
        CHECK (order_status IN ('draft', 'approved', 'sent', 'partially_received', 'received', 'cancelled')),

    CONSTRAINT chk_fpo_priority
        CHECK (priority_level IN ('low', 'normal', 'high', 'critical'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_purchase_orders_po_number_line
    ON analytics.fact_purchase_orders(po_number, product_id, warehouse_id, po_date_id);

CREATE INDEX IF NOT EXISTS idx_fpo_supplier_id
    ON analytics.fact_purchase_orders(supplier_id);

CREATE INDEX IF NOT EXISTS idx_fpo_warehouse_id
    ON analytics.fact_purchase_orders(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fpo_product_id
    ON analytics.fact_purchase_orders(product_id);

CREATE INDEX IF NOT EXISTS idx_fpo_po_date_id
    ON analytics.fact_purchase_orders(po_date_id);

CREATE INDEX IF NOT EXISTS idx_fpo_expected_receipt_date_id
    ON analytics.fact_purchase_orders(expected_receipt_date_id);


-- =========================================================
-- 2) fact_inbound_shipments
-- Actual inbound shipment / receipt fact
-- One row = one inbound shipment line for a PO/product
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_inbound_shipments (
    inbound_shipment_line_id       BIGINT PRIMARY KEY,
    inbound_shipment_id            BIGINT NOT NULL,
    shipment_number                VARCHAR(30) NOT NULL,

    purchase_order_id              BIGINT NOT NULL,
    po_line_id                     BIGINT NOT NULL,

    supplier_id                    INTEGER NOT NULL,
    warehouse_id                   INTEGER NOT NULL,
    product_id                     INTEGER NOT NULL,

    shipped_date_id                INTEGER,
    expected_arrival_date_id       INTEGER NOT NULL,
    actual_arrival_date_id         INTEGER,
    received_date_id               INTEGER,

    shipped_qty                    INTEGER NOT NULL,
    received_qty                   INTEGER NOT NULL,
    rejected_qty                   INTEGER NOT NULL DEFAULT 0,
    damaged_qty                    INTEGER NOT NULL DEFAULT 0,

    shipment_status                VARCHAR(30) NOT NULL,
    delay_days                     INTEGER NOT NULL DEFAULT 0,
    carrier_name                   VARCHAR(100),
    transport_mode                 VARCHAR(30),
    qc_pass_flag                   BOOLEAN NOT NULL DEFAULT TRUE,
    created_timestamp              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fis_purchase_order_line
        FOREIGN KEY (po_line_id)
        REFERENCES analytics.fact_purchase_orders(po_line_id),

    CONSTRAINT fk_fis_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES analytics.dim_supplier(supplier_id),

    CONSTRAINT fk_fis_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT fk_fis_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_fis_shipped_date
        FOREIGN KEY (shipped_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fis_expected_arrival_date
        FOREIGN KEY (expected_arrival_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fis_actual_arrival_date
        FOREIGN KEY (actual_arrival_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fis_received_date
        FOREIGN KEY (received_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT chk_fis_shipped_qty_nonnegative
        CHECK (shipped_qty >= 0),

    CONSTRAINT chk_fis_received_qty_nonnegative
        CHECK (received_qty >= 0),

    CONSTRAINT chk_fis_rejected_qty_nonnegative
        CHECK (rejected_qty >= 0),

    CONSTRAINT chk_fis_damaged_qty_nonnegative
        CHECK (damaged_qty >= 0),

    CONSTRAINT chk_fis_delay_days_nonnegative
        CHECK (delay_days >= 0),

    CONSTRAINT chk_fis_status
        CHECK (shipment_status IN ('in_transit', 'delayed', 'partially_received', 'received', 'rejected')),

    CONSTRAINT chk_fis_qty_balance
        CHECK (received_qty + rejected_qty <= shipped_qty)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_inbound_shipments_shipment_line
    ON analytics.fact_inbound_shipments(shipment_number, product_id, warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fis_po_line_id
    ON analytics.fact_inbound_shipments(po_line_id);

CREATE INDEX IF NOT EXISTS idx_fis_supplier_id
    ON analytics.fact_inbound_shipments(supplier_id);

CREATE INDEX IF NOT EXISTS idx_fis_warehouse_id
    ON analytics.fact_inbound_shipments(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fis_product_id
    ON analytics.fact_inbound_shipments(product_id);

CREATE INDEX IF NOT EXISTS idx_fis_expected_arrival_date_id
    ON analytics.fact_inbound_shipments(expected_arrival_date_id);

CREATE INDEX IF NOT EXISTS idx_fis_received_date_id
    ON analytics.fact_inbound_shipments(received_date_id);


-- =========================================================
-- 3) fact_inventory_snapshot
-- Daily inventory balance fact
-- One row = one product-location-date snapshot
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_inventory_snapshot (
    inventory_snapshot_id          BIGINT PRIMARY KEY,
    snapshot_date_id               INTEGER NOT NULL,

    product_id                     INTEGER NOT NULL,
    location_type                  VARCHAR(20) NOT NULL,
    store_id                       INTEGER,
    warehouse_id                   INTEGER,

    on_hand_qty                    INTEGER NOT NULL,
    reserved_qty                   INTEGER NOT NULL DEFAULT 0,
    available_qty                  INTEGER NOT NULL,
    in_transit_qty                 INTEGER NOT NULL DEFAULT 0,
    damaged_qty                    INTEGER NOT NULL DEFAULT 0,
    reorder_point_qty              INTEGER NOT NULL,
    safety_stock_qty               INTEGER NOT NULL,

    inventory_status               VARCHAR(30) NOT NULL,
    stockout_flag                  BOOLEAN NOT NULL DEFAULT FALSE,
    days_of_cover_estimate         DECIMAL(10,2),
    created_timestamp              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_finv_snapshot_date
        FOREIGN KEY (snapshot_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_finv_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_finv_store
        FOREIGN KEY (store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_finv_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT chk_finv_location_type
        CHECK (location_type IN ('store', 'warehouse')),

    CONSTRAINT chk_finv_location_exclusive
        CHECK (
            (location_type = 'store' AND store_id IS NOT NULL AND warehouse_id IS NULL)
            OR
            (location_type = 'warehouse' AND warehouse_id IS NOT NULL AND store_id IS NULL)
        ),

    CONSTRAINT chk_finv_on_hand_nonnegative
        CHECK (on_hand_qty >= 0),

    CONSTRAINT chk_finv_reserved_nonnegative
        CHECK (reserved_qty >= 0),

    CONSTRAINT chk_finv_available_nonnegative
        CHECK (available_qty >= 0),

    CONSTRAINT chk_finv_in_transit_nonnegative
        CHECK (in_transit_qty >= 0),

    CONSTRAINT chk_finv_damaged_nonnegative
        CHECK (damaged_qty >= 0),

    CONSTRAINT chk_finv_reorder_nonnegative
        CHECK (reorder_point_qty >= 0),

    CONSTRAINT chk_finv_safety_nonnegative
        CHECK (safety_stock_qty >= 0),

    CONSTRAINT chk_finv_status
        CHECK (inventory_status IN ('healthy', 'low_stock', 'stockout', 'overstock', 'inactive')),

    CONSTRAINT chk_finv_available_logic
        CHECK (available_qty <= on_hand_qty)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_inventory_snapshot_grain
    ON analytics.fact_inventory_snapshot(
        snapshot_date_id,
        product_id,
        location_type,
        COALESCE(store_id, -1),
        COALESCE(warehouse_id, -1)
    );

CREATE INDEX IF NOT EXISTS idx_finv_snapshot_date_id
    ON analytics.fact_inventory_snapshot(snapshot_date_id);

CREATE INDEX IF NOT EXISTS idx_finv_product_id
    ON analytics.fact_inventory_snapshot(product_id);

CREATE INDEX IF NOT EXISTS idx_finv_store_id
    ON analytics.fact_inventory_snapshot(store_id);

CREATE INDEX IF NOT EXISTS idx_finv_warehouse_id
    ON analytics.fact_inventory_snapshot(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_finv_stockout_flag
    ON analytics.fact_inventory_snapshot(stockout_flag);


-- =========================================================
-- 4) fact_stock_movements
-- Inventory movement ledger
-- One row = one stock movement event
-- =========================================================
CREATE TABLE IF NOT EXISTS analytics.fact_stock_movements (
    stock_movement_id              BIGINT PRIMARY KEY,
    movement_date_id               INTEGER NOT NULL,

    product_id                     INTEGER NOT NULL,
    location_type                  VARCHAR(20) NOT NULL,
    store_id                       INTEGER,
    warehouse_id                   INTEGER,

    movement_type                  VARCHAR(30) NOT NULL,
    movement_reason                VARCHAR(50) NOT NULL,
    quantity_change                INTEGER NOT NULL,

    reference_type                 VARCHAR(30),
    reference_id                   BIGINT,
    source_location_type           VARCHAR(20),
    source_store_id                INTEGER,
    source_warehouse_id            INTEGER,
    target_location_type           VARCHAR(20),
    target_store_id                INTEGER,
    target_warehouse_id            INTEGER,

    unit_cost                      DECIMAL(12,2),
    created_timestamp              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fsm_movement_date
        FOREIGN KEY (movement_date_id)
        REFERENCES analytics.dim_calendar(date_id),

    CONSTRAINT fk_fsm_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_fsm_store
        FOREIGN KEY (store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_fsm_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT fk_fsm_source_store
        FOREIGN KEY (source_store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_fsm_source_warehouse
        FOREIGN KEY (source_warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT fk_fsm_target_store
        FOREIGN KEY (target_store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_fsm_target_warehouse
        FOREIGN KEY (target_warehouse_id)
        REFERENCES analytics.dim_warehouse(warehouse_id),

    CONSTRAINT chk_fsm_location_type
        CHECK (location_type IN ('store', 'warehouse')),

    CONSTRAINT chk_fsm_location_exclusive
        CHECK (
            (location_type = 'store' AND store_id IS NOT NULL AND warehouse_id IS NULL)
            OR
            (location_type = 'warehouse' AND warehouse_id IS NOT NULL AND store_id IS NULL)
        ),

    CONSTRAINT chk_fsm_source_location_type
        CHECK (source_location_type IS NULL OR source_location_type IN ('store', 'warehouse')),

    CONSTRAINT chk_fsm_target_location_type
        CHECK (target_location_type IS NULL OR target_location_type IN ('store', 'warehouse')),

    CONSTRAINT chk_fsm_movement_type
        CHECK (movement_type IN (
            'receipt',
            'issue',
            'transfer_in',
            'transfer_out',
            'return_in',
            'return_out',
            'adjustment',
            'damage',
            'cycle_count'
        )),

    CONSTRAINT chk_fsm_quantity_not_zero
        CHECK (quantity_change <> 0)
);

CREATE INDEX IF NOT EXISTS idx_fsm_movement_date_id
    ON analytics.fact_stock_movements(movement_date_id);

CREATE INDEX IF NOT EXISTS idx_fsm_product_id
    ON analytics.fact_stock_movements(product_id);

CREATE INDEX IF NOT EXISTS idx_fsm_store_id
    ON analytics.fact_stock_movements(store_id);

CREATE INDEX IF NOT EXISTS idx_fsm_warehouse_id
    ON analytics.fact_stock_movements(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fsm_reference
    ON analytics.fact_stock_movements(reference_type, reference_id);

CREATE INDEX IF NOT EXISTS idx_fsm_movement_type
    ON analytics.fact_stock_movements(movement_type);