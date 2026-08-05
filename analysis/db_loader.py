"""
db_loader.py
------------
Loads all raw CSVs into a local SQLite database and validates
key referential integrity constraints before analysis.

Works with BOTH:
  - Real Olist dataset (from Kaggle)
  - Synthetic data (from data/generate_synthetic_data.py)

Run:
    python analysis/db_loader.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import pandas as pd
from pathlib import Path
from analysis.config import DATA_RAW, DB_PATH, ANALYSIS_START, ANALYSIS_END

TABLES = {
    "orders":        "olist_orders_dataset.csv",
    "order_items":   "olist_order_items_dataset.csv",
    "products":      "olist_products_dataset.csv",
    "sellers":       "olist_sellers_dataset.csv",
    "customers":     "olist_customers_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
}

PARSE_DATES = {
    "orders": [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_reviews": ["review_creation_date"],
}


def load_all():
    print("=" * 57)
    print("  DB Loader -- Flipkart NEEV Case Study")
    print("=" * 57)

    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"  Removed old DB: {DB_PATH.name}")

    conn = sqlite3.connect(DB_PATH)

    for table, fname in TABLES.items():
        fpath = DATA_RAW / fname
        if not fpath.exists():
            print(f"\n  [!] Missing: {fname}")
            print(f"      Place real Olist CSVs in: {DATA_RAW}")
            print(f"      Or run: py data/generate_synthetic_data.py")
            conn.close()
            sys.exit(1)

        date_cols = PARSE_DATES.get(table, [])
        df = pd.read_csv(fpath, parse_dates=date_cols, low_memory=False)

        # --- Real Olist data: filter orders to analysis window ---------
        if table == "orders":
            before = len(df)
            df["order_purchase_timestamp"] = pd.to_datetime(
                df["order_purchase_timestamp"], errors="coerce")
            df = df[
                (df["order_purchase_timestamp"] >= ANALYSIS_START) &
                (df["order_purchase_timestamp"] <= ANALYSIS_END)
            ]
            print(f"  [INFO] orders filtered to {ANALYSIS_START} -> {ANALYSIS_END}: "
                  f"{before:,} -> {len(df):,} rows")

        # --- Strip whitespace from string columns ----------------------
        str_cols = df.select_dtypes(include="object").columns
        df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())

        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"  [OK]  {table:<20} {len(df):>8,} rows")

    _validate(conn)
    _print_summary(conn)
    conn.close()
    print(f"\n  [OK]  DB ready -> {DB_PATH}")
    print("=" * 57)
    return DB_PATH


def _validate(conn):
    checks = {
        "Null order_id in orders":
            "SELECT COUNT(*) FROM orders WHERE order_id IS NULL",
        "order_items without matching order":
            ("SELECT COUNT(*) FROM order_items oi "
             "LEFT JOIN orders o ON oi.order_id=o.order_id "
             "WHERE o.order_id IS NULL"),
        "order_items without matching seller":
            ("SELECT COUNT(*) FROM order_items oi "
             "LEFT JOIN sellers s ON oi.seller_id=s.seller_id "
             "WHERE s.seller_id IS NULL"),
        "Delivered but null delivery date":
            ("SELECT COUNT(*) FROM orders "
             "WHERE order_status='delivered' "
             "AND order_delivered_customer_date IS NULL"),
    }
    print("\n  Data Quality Checks:")
    all_ok = True
    for name, sql in checks.items():
        val = conn.execute(sql).fetchone()[0]
        flag = "[OK]" if val == 0 else "[!] "
        if val > 0:
            all_ok = False
        print(f"    {flag}  {name}: {val}")
    if all_ok:
        print("    All checks passed.")
    else:
        print("    [!] Some checks flagged — review above before interpreting results.")


def _print_summary(conn):
    """Quick snapshot of the loaded dataset."""
    total    = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    delivrd  = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status='delivered'").fetchone()[0]
    rto      = total - delivrd
    otd_row  = conn.execute(
        "SELECT ROUND(100.0*SUM(CASE WHEN order_delivered_customer_date "
        "<= order_estimated_delivery_date THEN 1 ELSE 0 END)/COUNT(*),1) "
        "FROM orders WHERE order_status='delivered' "
        "AND order_delivered_customer_date IS NOT NULL"
    ).fetchone()[0]
    reviews  = conn.execute("SELECT COUNT(*) FROM order_reviews").fetchone()[0]
    sellers  = conn.execute("SELECT COUNT(DISTINCT seller_id) FROM order_items").fetchone()[0]

    print(f"\n  Dataset Snapshot:")
    print(f"    Orders    : {total:,}  (delivered: {delivrd:,}, RTO/other: {rto:,})")
    print(f"    OTD Rate  : {otd_row}%")
    print(f"    Reviews   : {reviews:,}")
    print(f"    Sellers   : {sellers:,} unique")


def get_conn():
    """Return a live SQLite connection; auto-load if DB doesn't exist."""
    if not DB_PATH.exists():
        load_all()
    return sqlite3.connect(DB_PATH)


if __name__ == "__main__":
    load_all()
