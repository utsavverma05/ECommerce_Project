-- ============================================================
-- 01_create_schema.sql
-- Core table definitions for SQLite.
-- (Informational — db_loader.py creates tables from CSVs.
--  Use this as reference / for PostgreSQL migration.)
-- ============================================================

CREATE TABLE IF NOT EXISTS orders (
    order_id                        TEXT PRIMARY KEY,
    customer_id                     TEXT NOT NULL,
    order_status                    TEXT,
    order_purchase_timestamp        TEXT,
    order_approved_at               TEXT,
    order_delivered_carrier_date    TEXT,
    order_delivered_customer_date   TEXT,
    order_estimated_delivery_date   TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id        TEXT,
    order_item_id   INTEGER,
    product_id      TEXT,
    seller_id       TEXT,
    price           REAL,
    freight_value   REAL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS products (
    product_id              TEXT PRIMARY KEY,
    product_category_name   TEXT,
    product_weight_g        INTEGER,
    product_length_cm       INTEGER,
    product_height_cm       INTEGER,
    product_width_cm        INTEGER
);

CREATE TABLE IF NOT EXISTS sellers (
    seller_id               TEXT PRIMARY KEY,
    seller_zip_code_prefix  TEXT,
    seller_city             TEXT,
    seller_state            TEXT
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id             TEXT PRIMARY KEY,
    customer_unique_id      TEXT,
    customer_zip_code_prefix TEXT,
    customer_city           TEXT,
    customer_state          TEXT
);

CREATE TABLE IF NOT EXISTS order_reviews (
    review_id           TEXT PRIMARY KEY,
    order_id            TEXT,
    review_score        INTEGER,
    review_creation_date TEXT
);

-- Indexes for join performance
CREATE INDEX IF NOT EXISTS idx_oi_order   ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_oi_seller  ON order_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_oi_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_rev_order  ON order_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_ord_status ON orders(order_status);
