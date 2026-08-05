# Data Directory

## Track A — Synthetic Data (Default)

Run the generator from the project root:

```bash
python data/generate_synthetic_data.py
```

This produces 6 CSVs in `data/raw/` that mirror the Olist schema exactly.
All downstream analysis works identically with synthetic or real data.

---

## Track B — Real Olist Data (Optional)

### Step 1: Get Kaggle API credentials
1. Go to [kaggle.com](https://www.kaggle.com) → Account → Create New API Token
2. Save `kaggle.json` to `~/.kaggle/kaggle.json`

### Step 2: Install Kaggle CLI
```bash
pip install kaggle
```

### Step 3: Download the dataset
```bash
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
```

### Step 4: Verify files
```
data/raw/
  olist_orders_dataset.csv
  olist_order_items_dataset.csv
  olist_products_dataset.csv
  olist_sellers_dataset.csv
  olist_customers_dataset.csv
  olist_order_reviews_dataset.csv
  olist_geolocation_dataset.csv     ← not used in this analysis
  product_category_name_translation.csv  ← optional, not required
```

### Step 5: Run the pipeline
```bash
python run_all.py --skip-data
```

> **Note**: Real Olist data covers 2016–2018. The config.py `ANALYSIS_START`
> and `ANALYSIS_END` will automatically filter to the 6-month window with
> the most complete data (~Sep 2017 – Feb 2018).
> Adjust `ANALYSIS_START` / `ANALYSIS_END` in `analysis/config.py` as needed.

---

## Data Quality Notes

| Issue | Magnitude | Treatment in Code |
|---|---|---|
| `order_delivered_customer_date` null | ~3% (real) / by design (synthetic) | Counted as RTO in all queries |
| Duplicate zip codes in geolocation | ~15% (real data) | Not used; seller_state used instead |
| Orders with no review | ~20% (real) | Excluded from CSAT analysis; volume noted |
| Sellers with <15 orders | Variable | Filtered out before decile analysis (min volume threshold) |
