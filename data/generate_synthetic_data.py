"""
generate_synthetic_data.py
------------------------------------------------------------------
Generates a realistic 100K-order synthetic dataset that mirrors the
Olist e-commerce schema. Bakes in a deliberate 6-month delivery
degradation signal so all downstream analysis produces meaningful,
defensible findings.

Degradation model:
  * Overall OTD starts at ~88% in Jan -> declines to ~72% by Jun
  * Two specific nodes (CE, PE) are the primary culprits
  * RTO is elevated in CE, PE, BA (structural underservice)
  * Seller processing time grows monotonically in bad nodes
  * Review score correlates inversely with delay (r approx -0.55)

Run:
    python data/generate_synthetic_data.py
Outputs:
    data/raw/olist_orders_dataset.csv
    data/raw/olist_order_items_dataset.csv
    data/raw/olist_products_dataset.csv
    data/raw/olist_sellers_dataset.csv
    data/raw/olist_customers_dataset.csv
    data/raw/olist_order_reviews_dataset.csv
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
from pathlib import Path
import uuid
from datetime import datetime, timedelta

# -- Config --------------------------------------------------------------------
from analysis.config import (
    DATA_RAW, RANDOM_SEED, N_ORDERS, N_SELLERS, N_CUSTOMERS,
    N_PRODUCTS, ANALYSIS_START, ANALYSIS_END,
    SELLER_STATES, HIGH_RTO_STATES, BAD_NODES, CATEGORIES
)

rng = np.random.default_rng(RANDOM_SEED)
DATA_RAW.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("  Synthetic Data Generator -- Flipkart NEEV Case Study")
print("=" * 60)

# -- Helper --------------------------------------------------------------------
def uid(n=1):
    return [uuid.uuid4().hex[:32] for _ in range(n)]

# -- 1. Sellers (Fulfillment Nodes) --------------------------------------------
print("[1/6] Generating sellers ...")

# Weight allocation: SP and RJ are dominant (like Mumbai/Delhi)
state_weights = [0.30, 0.20, 0.12, 0.08, 0.08, 0.07, 0.05, 0.04, 0.03, 0.03]
seller_states = rng.choice(SELLER_STATES, size=N_SELLERS, p=state_weights)

sellers = pd.DataFrame({
    "seller_id":              uid(N_SELLERS),
    "seller_zip_code_prefix": [str(rng.integers(10000, 99999)) for _ in range(N_SELLERS)],
    "seller_city":            rng.choice(
        ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Porto Alegre",
         "Curitiba", "Florianópolis", "Salvador", "Goiânia", "Fortaleza", "Recife"],
        size=N_SELLERS
    ),
    "seller_state": seller_states,
})
sellers.to_csv(DATA_RAW / "olist_sellers_dataset.csv", index=False)
print(f"   [OK] {len(sellers)} sellers across {len(SELLER_STATES)} states")

# -- 2. Products ---------------------------------------------------------------
print("[2/6] Generating products ...")

cat_weights = [0.15,0.12,0.12,0.09,0.09,0.08,0.07,0.06,0.05,0.04,0.04,0.03,0.03,0.02,0.01]
products = pd.DataFrame({
    "product_id":           uid(N_PRODUCTS),
    "product_category_name": rng.choice(CATEGORIES, size=N_PRODUCTS, p=cat_weights),
    "product_weight_g":      rng.integers(100, 20_000, size=N_PRODUCTS),
    "product_length_cm":     rng.integers(10, 100, size=N_PRODUCTS),
    "product_height_cm":     rng.integers(5, 50,  size=N_PRODUCTS),
    "product_width_cm":      rng.integers(10, 80,  size=N_PRODUCTS),
})
products.to_csv(DATA_RAW / "olist_products_dataset.csv", index=False)
print(f"   [OK] {len(products)} products across {len(CATEGORIES)} categories")

# -- 3. Customers --------------------------------------------------------------
print("[3/6] Generating customers ...")

# Customer states skew toward high-population / demand states
cust_states = ["SP","RJ","MG","RS","PR","SC","BA","GO","CE","PE",
               "AM","PA","ES","DF","MT","MS","RN","PB","AL","SE"]
cust_weights = [0.24,0.15,0.12,0.08,0.07,0.06,0.05,0.04,0.03,0.03,
                0.02,0.02,0.02,0.02,0.01,0.01,0.01,0.01,0.005,0.005]

customers = pd.DataFrame({
    "customer_id":              uid(N_CUSTOMERS),
    "customer_unique_id":       uid(N_CUSTOMERS),
    "customer_zip_code_prefix": [str(rng.integers(10000, 99999)) for _ in range(N_CUSTOMERS)],
    "customer_city":            rng.choice(
        ["São Paulo","Rio de Janeiro","Brasília","Fortaleza","Salvador",
         "Manaus","Curitiba","Recife","Porto Alegre","Belém"],
        size=N_CUSTOMERS
    ),
    "customer_state": rng.choice(cust_states, size=N_CUSTOMERS, p=cust_weights),
})
customers.to_csv(DATA_RAW / "olist_customers_dataset.csv", index=False)
print(f"   [OK] {len(customers)} customers")

# -- 4. Orders + degradation model ---------------------------------------------
print("[4/6] Generating orders with degradation baked in ...")

start_dt = pd.Timestamp(ANALYSIS_START)
end_dt   = pd.Timestamp(ANALYSIS_END)
date_range_days = (end_dt - start_dt).days

# Draw purchase timestamps -- higher volume in later months (growth)
raw_days = rng.exponential(scale=date_range_days * 0.6, size=N_ORDERS)
raw_days = np.clip(raw_days, 0, date_range_days)
purchase_ts = [start_dt + timedelta(days=float(d)) +
               timedelta(hours=int(rng.integers(8, 22))) for d in raw_days]

# Month index (0=Jan, 5=Jun) -- drives degradation
months = np.array([(t - start_dt).days / 30 for t in purchase_ts])  # 0-6

# Assign seller to each order
order_seller_idx = rng.integers(0, N_SELLERS, size=N_ORDERS)
order_sellers    = sellers.iloc[order_seller_idx]
order_states     = order_sellers["seller_state"].values

# -- Base processing days (warehouse -> carrier handoff) ------------------------
# Bad nodes start slow and get worse; good nodes stay stable
# KEY: processing is the PRIMARY bottleneck for bad nodes
base_proc = np.where(
    np.isin(order_states, BAD_NODES),
    3.5 + months * 0.65 + rng.exponential(1.2, N_ORDERS),   # worsening: ~4-8d by month 5
    1.0 + months * 0.08 + rng.exponential(0.6, N_ORDERS),   # stable:    ~1-2d
)
base_proc = np.clip(base_proc, 0.5, 14)

# -- Base transit days (carrier -> customer) ------------------------------------
# Carrier is FASTER than processing for most routes
same_state_mask = np.array([
    order_sellers.iloc[i]["seller_state"] == rng.choice(cust_states, p=cust_weights)
    for i in range(N_ORDERS)
])
base_transit = np.where(
    same_state_mask,
    rng.exponential(1.5, N_ORDERS),   # same state: ~1-2d
    rng.exponential(3.5, N_ORDERS),   # cross-state: ~3-5d
)
base_transit = np.clip(base_transit, 0.5, 15)

# -- Estimated delivery date (EDD) -- static, slightly OPTIMISTIC ---------------
# EDD is set close to base time; on-time orders (with negative delay_add) beat it,
# late orders miss it. Net: realistic avg delay of +0.5 to +2.5d growing over 6 months.
edd_offset = (base_proc + base_transit) * rng.uniform(0.98, 1.08, N_ORDERS)
edd_offset = np.clip(edd_offset, 3, 30)

# -- Actual delivery relative to EDD -------------------------------------------
# OTD probability degrades from 88% -> 72% over 6 months
otd_prob  = 0.88 - 0.027 * months        # linear degradation
# Bad nodes have lower baseline OTD
otd_prob  = np.where(np.isin(order_states, BAD_NODES), otd_prob - 0.18, otd_prob)
otd_prob  = np.clip(otd_prob, 0.30, 0.95)

on_time   = rng.random(N_ORDERS) < otd_prob
delay_add = np.where(on_time, rng.uniform(-1, 0, N_ORDERS),
                               rng.exponential(3.0, N_ORDERS))

total_days      = base_proc + base_transit + delay_add
total_days      = np.clip(total_days, 1, 40)

# -- RTO: elevated in high-RTO states ------------------------------------------
rto_prob  = np.where(np.isin(order_states, HIGH_RTO_STATES), 0.14, 0.03)
is_rto    = rng.random(N_ORDERS) < rto_prob

# -- Build timestamps ----------------------------------------------------------
approved_at          = [ts + timedelta(minutes=int(rng.integers(5, 60)))
                        for ts in purchase_ts]
carrier_date         = [approved_at[i] + timedelta(days=float(base_proc[i]))
                        for i in range(N_ORDERS)]
delivered_date       = [carrier_date[i] + timedelta(days=float(base_transit[i] + delay_add[i]))
                        for i in range(N_ORDERS)]
estimated_date       = [approved_at[i] + timedelta(days=float(edd_offset[i]))
                        for i in range(N_ORDERS)]

# Apply RTO: null out delivery date
delivered_date_final = [None if is_rto[i] else delivered_date[i] for i in range(N_ORDERS)]

# Order status
status = []
for i in range(N_ORDERS):
    if is_rto[i]:
        status.append(rng.choice(["cancelled", "unavailable"], p=[0.6, 0.4]))
    else:
        status.append("delivered")

order_ids   = uid(N_ORDERS)
customer_ids = rng.choice(customers["customer_id"].values, size=N_ORDERS)

orders = pd.DataFrame({
    "order_id":                          order_ids,
    "customer_id":                       customer_ids,
    "order_status":                      status,
    "order_purchase_timestamp":          purchase_ts,
    "order_approved_at":                 approved_at,
    "order_delivered_carrier_date":      carrier_date,
    "order_delivered_customer_date":     delivered_date_final,
    "order_estimated_delivery_date":     estimated_date,
})
orders.to_csv(DATA_RAW / "olist_orders_dataset.csv", index=False)

delivered_count = sum(1 for s in status if s == "delivered")
rto_count       = N_ORDERS - delivered_count
on_time_count   = sum(1 for i in range(N_ORDERS) if on_time[i] and not is_rto[i])
print(f"   [OK] {N_ORDERS:,} orders | {delivered_count:,} delivered | "
      f"{rto_count:,} RTO ({100*rto_count/N_ORDERS:.1f}%) | "
      f"overall OTD {100*on_time_count/delivered_count:.1f}%")

# -- 5. Order Items ------------------------------------------------------------
print("[5/6] Generating order items ...")

# ~70% single-item orders, ~30% multi-item
items_per_order = rng.choice([1, 2, 3], size=N_ORDERS, p=[0.70, 0.22, 0.08])

rows = []
for i, oid in enumerate(order_ids):
    n = items_per_order[i]
    seller = order_sellers.iloc[i]["seller_id"]
    for j in range(1, n + 1):
        prod    = rng.choice(products["product_id"].values)
        cat     = products.loc[products["product_id"] == prod, "product_category_name"].values[0]
        # Price varies by category
        base_price = {
            "electronics": 350, "furniture": 280, "fashion": 90,
            "sports": 120, "health_beauty": 65,
        }.get(cat, 100)
        price     = max(9.9, rng.normal(base_price, base_price * 0.4))
        freight   = max(5.0, rng.normal(18, 8))
        rows.append({
            "order_id":      oid,
            "order_item_id": j,
            "product_id":    prod,
            "seller_id":     seller,
            "price":         round(price, 2),
            "freight_value": round(freight, 2),
        })

order_items = pd.DataFrame(rows)
order_items.to_csv(DATA_RAW / "olist_order_items_dataset.csv", index=False)
print(f"   [OK] {len(order_items):,} order line items")

# -- 6. Reviews ----------------------------------------------------------------
print("[6/6] Generating reviews ...")

# Only delivered orders get reviews (+ some RTO complaints = 1 star)
review_rows = []
for i in range(N_ORDERS):
    if is_rto[i] and rng.random() < 0.4:        # RTO -> angry review
        score = rng.choice([1, 2], p=[0.85, 0.15])
    elif status[i] == "delivered":
        # Delay -> lower score (r approx -0.55)
        actual = (delivered_date[i] - estimated_date[i]).days if delivered_date_final[i] else 0
        if actual <= 0:                           # on time or early
            score = rng.choice([4, 5], p=[0.30, 0.70])
        elif actual <= 2:
            score = rng.choice([3, 4, 5], p=[0.20, 0.50, 0.30])
        elif actual <= 5:
            score = rng.choice([2, 3, 4], p=[0.35, 0.45, 0.20])
        else:
            score = rng.choice([1, 2, 3], p=[0.55, 0.30, 0.15])
    else:
        continue

    review_rows.append({
        "review_id":           uuid.uuid4().hex[:32],
        "order_id":            order_ids[i],
        "review_score":        score,
        "review_creation_date": (purchase_ts[i] +
                                  timedelta(days=float(total_days[i]) + rng.integers(1, 5))),
    })

reviews = pd.DataFrame(review_rows)
reviews.to_csv(DATA_RAW / "olist_order_reviews_dataset.csv", index=False)
print(f"   [OK] {len(reviews):,} reviews | avg score: {reviews['review_score'].mean():.2f}")

print()
print("=" * 60)
print("  [OK]  All CSVs written to data/raw/")
print("  Next: python analysis/db_loader.py")
print("=" * 60)
