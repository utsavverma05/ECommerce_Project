# Flipkart NEEV — Delivery Ops Diagnostic Case Study

> **Portfolio-grade operations diagnostic.** Not a student dashboard — every query, chart, and metric maps to a real management decision.

---

## Problem Statement

An e-commerce platform's delivery performance has degraded over 6 months. OTD rate has declined, average delay has grown, and RTO rates are elevated in specific geographies — but the root cause is unknown and unquantified across the warehouse network.

**This case study answers:**
- Which fulfillment nodes are underperforming, and by how much?
- Is the bottleneck inside the warehouse (seller processing) or with the carrier (transit)?
- What is the financial exposure from undelivered/late orders?
- What should management do — in what order, and who owns it?

---

## Stack

| Tool | Use |
|---|---|
| Python (Pandas, Matplotlib, NumPy) | Data wrangling, analysis, visualization |
| SQLite (via sqlite3) | Relational querying across 6 tables |
| openpyxl | 8-sheet Excel workbook with RAG formatting |
| SQL | 7 decision-mapped queries |

*No Power BI. No ML. No cloud. Fully reproducible from a single `python run_all.py`.*

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-handle/flipkart-neev-ops-case-study.git
cd flipkart-neev-ops-case-study

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline
python run_all.py
```

This will:
- Generate 100K synthetic orders with realistic 6-month degradation
- Load into SQLite and validate integrity
- Produce 6 analysis charts in `outputs/charts/`
- Build the 8-sheet Excel workbook in `excel/`

**Runtime: ~45–90 seconds**

---

## Dataset

**Synthetic data** mirroring the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) schema (6 tables, 100K orders).

Degradation is deliberately baked in:
- OTD rate: 88% (Jan) → 72% (Jun)
- RTO elevated in states CE, PE, BA (>12%)
- Seller processing time growing in underperforming nodes
- Review scores declining in parallel (r ≈ −0.55 with delay)

> **To use real Olist data**: See `data/README.md` for Kaggle download instructions. All analysis scripts work unchanged.

---

## Project Structure

```
flipkart-neev-ops-case-study/
├── run_all.py                     ← One command to run everything
├── requirements.txt
├── data/
│   ├── generate_synthetic_data.py ← 100K orders with baked-in degradation
│   └── README.md                  ← How to use real Olist data
├── sql/
│   ├── 01_create_schema.sql       ← Schema reference
│   ├── 02_otd_by_node.sql         ← OTD rate per node per month
│   ├── 03_delay_trend.sql         ← MoM delay trend
│   ├── 04_rto_analysis.sql        ← RTO rate + revenue at risk
│   ├── 05_category_delay_index.sql← Volume-weighted category delay
│   ├── 06_seller_decile.sql       ← Per-seller OTD (for decile in Python)
│   └── 07_bottleneck_attribution.sql ← Processing vs transit split
├── analysis/
│   ├── config.py                  ← All constants, paths, palette, OHS weights
│   ├── db_loader.py               ← CSV → SQLite + integrity validation
│   ├── 01_otd_trend.py            → Chart: OTD% + delay MoM trend
│   ├── 02_rto_analysis.py         → Chart: RTO rate + revenue at risk
│   ├── 03_bottleneck_attribution.py → Chart: Processing vs transit split
│   ├── 04_abc_analysis.py         → Chart: ABC Pareto + OTD by class
│   ├── 05_ops_health_score.py     → Chart: OHS heatmap + node ranking
│   └── 06_csat_correlation.py     → Chart: Review score vs delay
├── excel/
│   └── generate_workbook.py       ← 8-sheet workbook (openpyxl)
└── outputs/
    ├── charts/                    ← 6 PNG chart outputs
    └── ops_health_score.csv       ← OHS per node per month
```

---

## Key Findings (from synthetic data run)

| Finding | Metric | Value |
|---|---|---|
| OTD degradation | Jan → Jun | ~88% → ~72% (−16pp) |
| Primary bottleneck | Processing vs transit | ~65–70% of delay from seller processing |
| Worst RTO nodes | CE, PE states | >12% RTO vs ~3% national avg |
| Revenue at risk | RTO orders | ~₹4–6M across 6 months |
| CSAT correlation | r(delay, score) | ≈ −0.55 |
| Class A sellers | Avg OTD | ~5pp below Class B/C |

---

## Operations Health Score (OHS)

$$OHS = 0.40 \cdot OTD + 0.25 \cdot (1 - RTO) + 0.20 \cdot \left(1 - \min\!\left(\frac{delay}{14}, 1\right)\right) + 0.15 \cdot \left(1 - \min\!\left(\frac{proc}{7}, 1\right)\right)$$

| Score | Status | Action |
|---|---|---|
| ≥80 | 🟢 Healthy | Monitor monthly |
| 60–79 | 🟡 At Risk | 30-day improvement plan |
| <60 | 🔴 Critical | Immediate audit |

---

## Recommendations

| Priority | Action | Owner | Timeline |
|---|---|---|---|
| P0 | Enforce 48-hr pick-pack SLA; auto-escalate beyond 72hr | VP Ops | 30 days |
| P0 | Implement dynamic EDD using rolling carrier velocity | Product + Logistics Tech | 45 days |
| P1 | Expand carrier coverage in high-RTO states (CE, PE, BA) | Regional Logistics | 60 days |
| P1 | Reposition Class A seller inventory to demand hotspots | Category + Seller Mgmt | 90 days |
| P2 | Deploy OHS as monthly ops scorecard with auto-trigger | Ops Analytics | 30 days |

---

## Chart Outputs

| # | Chart | Decision |
|---|---|---|
| 01 | OTD trend + avg delay MoM | Executive escalation trigger |
| 02 | RTO rate + revenue at risk by node | Last-mile partner audit |
| 03 | Processing vs transit split per node | Blame attribution |
| 04 | ABC Pareto + OTD by class | SLA enforcement priority |
| 05 | OHS heatmap + node ranking | Monthly ops scorecard |
| 06 | Review score vs delay (bucket + monthly) | CX cost of ops failure |

---

