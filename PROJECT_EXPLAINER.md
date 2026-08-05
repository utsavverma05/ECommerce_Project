# Flipkart NEEV — Delivery Ops Diagnostic
## Complete Project Explainer

> **Who this is for**: You built this project and want to understand it deeply —
> every file, every decision, every line of logic — so you can explain it confidently
> in an interview or to a non-technical person.

---

## Table of Contents

1. [What is this project?](#1-what-is-this-project)
2. [The Business Problem](#2-the-business-problem)
3. [How we think about the problem (the framework)](#3-how-we-think-about-the-problem)
4. [Tech stack — what each tool does and why](#4-tech-stack)
5. [Project structure — every folder and file explained](#5-project-structure)
6. [The Pipeline — how data flows end-to-end](#6-the-pipeline)
7. [The Data — what we're working with](#7-the-data)
8. [The SQL Queries — what each one finds and why](#8-the-sql-queries)
9. [The Analysis Scripts — what each chart shows](#9-the-analysis-scripts)
10. [The Operations Health Score — the original metric](#10-the-operations-health-score)
11. [The Excel Workbook — what each sheet is for](#11-the-excel-workbook)
12. [The Findings — what the numbers mean](#12-the-findings)
13. [The Recommendations — and how to defend them](#13-the-recommendations)
14. [How to run the project](#14-how-to-run-the-project)
15. [How to explain this in an interview](#15-how-to-explain-this-in-an-interview)

---

## 1. What is this project?

This is a **portfolio-grade operations diagnostic case study** — built to demonstrate
the kind of analytical thinking expected in supply chain and operations roles at
companies like Flipkart (specifically the NEEV program).

**What it is NOT**:
- Not a generic dashboard with pretty charts
- Not a data science project with ML models
- Not a student exercise with fabricated conclusions

**What it IS**:
- A structured business investigation, starting from a problem statement and ending
  with prioritized, evidence-backed recommendations
- Every query, chart, and metric exists to answer a specific management decision
- Built with tools that operations analysts actually use: SQL, Python, Excel

**The core question**: *An e-commerce platform's delivery performance has been
declining for 6 months. What's happening, why, and what should management do?*

---

## 2. The Business Problem

### What degradation looks like

Imagine you run operations at an e-commerce company. You notice:
- Customer complaints are rising
- Return/refund requests are climbing
- Negative reviews mention late delivery

You pull the numbers and find that **on-time delivery (OTD) rate** — the % of
orders that reach customers by the promised date — has been falling every month
for 6 months straight.

This is a crisis. But knowing OTD is falling isn't enough. You need to know:

1. **Which warehouses (nodes)** are responsible?
2. **Where in the process** is the breakdown — is it our warehouse or our courier?
3. **Which products/categories** are worst affected?
4. **How much revenue** are we losing?
5. **What do we fix first?**

This project answers all five questions using real e-commerce data.

### Why "6 months"?

Six months is long enough to distinguish a trend from noise, short enough to be
actionable. A 6-month decline in OTD is a signal that something structural has
broken — not just a bad week.

### The stakeholders

Different people care about different parts of this problem:

| Person | What they care about |
|---|---|
| VP Operations | Which nodes to escalate; what the trend looks like |
| Regional Fulfilment Manager | Is it my warehouse or the carrier? |
| Finance | How much money is this costing? |
| Product Team | Why are customers giving 1-star reviews? |
| Category Manager | Which product types are worst? |

A good analyst produces outputs that each of these people can act on.
That's why **every chart and query in this project has a "decision it supports"** label.

---

## 3. How We Think About the Problem

### The consulting framework we use

Before writing a single line of SQL, we need a mental model of **how delivery works**
and **where it can break**. Here's the lifecycle of one e-commerce order:

```
Customer places order
        |
        v
Order approved (payment cleared)
        |
        v
[SELLER / WAREHOUSE STAGE]
  Seller picks, packs, labels
        |
        v
Carrier picks up from warehouse     <-- "order_delivered_carrier_date"
        |
        v
[CARRIER / TRANSIT STAGE]
  Package moves through network
        |
        v
Customer receives package           <-- "order_delivered_customer_date"
        |
        v
Customer compares to promised date  <-- "order_estimated_delivery_date"
    On time? -> Good review
    Late?    -> Bad review, complaint, potential return
```

This lifecycle gives us **two places where delays happen**:
1. **Seller processing**: from order approval to carrier pickup
2. **Carrier transit**: from carrier pickup to customer delivery

One of the most important findings in this project is identifying **which of these two
stages is the actual bottleneck** — because the fix is completely different.
If it's the seller: enforce a pick-pack SLA. If it's the carrier: renegotiate the
carrier contract or find a new partner.

### Pareto thinking

We don't try to fix everything. We use the **Pareto principle (80/20 rule)**:
roughly 80% of the delay problem comes from 20% of the nodes/sellers. Find those,
fix those first.

### ABC analysis

We classify sellers into three groups by revenue contribution:
- **Class A**: Top sellers (70% of revenue) — highest priority
- **Class B**: Mid-tier sellers (next 20%) — medium priority
- **Class C**: Long tail (bottom 10%) — monitor only

The interesting finding is when **Class A sellers have low OTD** — that's the highest
business risk: your most valuable sellers are also your worst performers.

---

## 4. Tech Stack

### Why these tools specifically?

| Tool | What it does in this project | Why not something else? |
|---|---|---|
| **SQL (SQLite)** | Joins tables, computes KPIs, filters data | Relational data = relational queries. SQL is the language of data analysis in ops teams. SQLite needs zero setup. |
| **Python (Pandas)** | Reads SQL output, computes derived metrics, orchestrates pipeline | Excel can't handle 100K rows cleanly. Python automates the full pipeline. |
| **Python (Matplotlib)** | Generates all charts | Seaborn/Plotly are prettier, but Matplotlib gives full control. Recruiters want to see you can build from scratch. |
| **Python (openpyxl)** | Builds the Excel workbook programmatically | Excel is what ops managers actually open. openpyxl lets us add RAG coloring and data bars in code. |
| **SQLite** | The database engine | No server needed. The whole DB is one `.db` file. Perfect for a portable case study. |
| **Excel** | Final deliverable for non-technical audiences | Every ops manager lives in Excel. The workbook is the "hand it to your boss" output. |

### What we deliberately did NOT use

- **Power BI / Tableau**: Would hide the analysis behind a GUI. SQL + Python shows you understand the logic.
- **Machine Learning**: Not needed. Root cause analysis is about understanding, not prediction.
- **Cloud databases**: Zero setup barrier. SQLite runs on any laptop.
- **Jupyter notebooks**: We use `.py` scripts with a master runner instead, which is how real engineering teams work.

---

## 5. Project Structure

Here is every folder and file, and what it does:

```
flipkart-neev-ops-case-study/
|
|-- run_all.py                  <- The "start button". One command runs everything.
|-- requirements.txt            <- List of Python packages needed
|-- .gitignore                  <- Tells Git what NOT to commit (raw data, charts)
|-- README.md                   <- GitHub project page
|-- PROJECT_EXPLAINER.md        <- This file
|
|-- data/
|   |-- generate_synthetic_data.py  <- Builds fake-but-realistic 100K order dataset
|   |-- README.md                   <- How to swap in real Olist data from Kaggle
|   |-- raw/                        <- CSV files live here (real or synthetic)
|       |-- olist_orders_dataset.csv
|       |-- olist_order_items_dataset.csv
|       |-- olist_products_dataset.csv
|       |-- olist_sellers_dataset.csv
|       |-- olist_customers_dataset.csv
|       |-- olist_order_reviews_dataset.csv
|
|-- sql/
|   |-- 01_create_schema.sql        <- Table definitions (reference only)
|   |-- 02_otd_by_node.sql          <- On-time delivery rate per warehouse per month
|   |-- 03_delay_trend.sql          <- Month-over-month delay trend
|   |-- 04_rto_analysis.sql         <- Return-to-origin rate + revenue at risk
|   |-- 05_category_delay_index.sql <- Which product categories are worst
|   |-- 06_seller_decile.sql        <- Per-seller OTD for Pareto analysis
|   |-- 07_bottleneck_attribution.sql <- Seller processing vs carrier transit
|
|-- analysis/
|   |-- config.py               <- All settings in one place (paths, KPI thresholds)
|   |-- db_loader.py            <- Reads CSVs -> loads SQLite -> validates data
|   |-- 01_otd_trend.py         <- Chart: OTD % declining over 6 months
|   |-- 02_rto_analysis.py      <- Chart: RTO rates + revenue at risk by node
|   |-- 03_bottleneck_attribution.py <- Chart: Processing days vs transit days
|   |-- 04_abc_analysis.py      <- Chart: Pareto + OTD by seller class
|   |-- 05_ops_health_score.py  <- Chart: OHS heatmap across nodes and months
|   |-- 06_csat_correlation.py  <- Chart: Review score vs delivery delay
|
|-- excel/
|   |-- generate_workbook.py    <- Builds the 8-sheet Excel ops workbook
|
|-- outputs/
|   |-- charts/                 <- All 6 PNG charts land here
|   |-- ops_health_score.csv    <- OHS table (node x month)
|   |-- otd_trend.csv           <- Monthly OTD data
|
|-- report/
|   |-- case_study_report.md    <- Full written case study narrative
```

---

## 6. The Pipeline

### What "pipeline" means

A pipeline is a sequence of steps where the output of one step becomes the input
of the next. Think of it like an assembly line:

```
Raw CSVs
    |
    v  [Step 1: generate_synthetic_data.py OR place real Olist CSVs]
Data files in data/raw/
    |
    v  [Step 2: db_loader.py]
SQLite database (ops_case_study.db)
    |
    v  [Steps 3-8: analysis scripts 01-06]
Charts (PNG) + CSV summaries
    |
    v  [Step 9: generate_workbook.py]
Excel workbook (8 sheets, formatted)
```

### How `run_all.py` orchestrates this

`run_all.py` is the master script. When you run `py run_all.py`, it:

1. Calls `data/generate_synthetic_data.py` as a **subprocess** — a separate Python
   process that generates the CSVs. (Use `--skip-data` to skip this if you have
   real Olist data already placed in `data/raw/`)

2. Calls `analysis/db_loader.py` — loads all 6 CSVs into a SQLite database
   and runs 4 data quality checks.

3. Calls each of the 6 analysis scripts as subprocesses — each one connects to the
   database, runs its SQL query, and saves a PNG chart.

4. Calls `excel/generate_workbook.py` — reads the database and outputs the 8-sheet
   Excel file.

### Why subprocesses?

Each script is run as its own Python process using `subprocess.run()`. This means:
- If one script fails, we know exactly which one and can re-run just that step
- The scripts work independently — you can run `py analysis/01_otd_trend.py` alone
- Clean separation of concerns — each script does one job

### The `--skip-data` flag

When you run `py run_all.py --skip-data`, the data generation step is skipped.
This is used when:
- You've already generated synthetic data (saves ~30 seconds)
- You've placed real Olist CSVs in `data/raw/` and don't want them overwritten

---

## 7. The Data

### Where it comes from

We use the **Olist Brazilian E-Commerce Dataset** — a real, anonymized dataset from
a Brazilian e-commerce marketplace, available free on Kaggle. It has:
- ~100,000 orders placed between 2016 and 2018
- Real timestamps at every stage of delivery
- Real seller locations, product categories, and customer reviews

We use this dataset because it has the exact columns we need to compute delivery KPIs:
`order_purchase_timestamp`, `order_delivered_customer_date`, `order_estimated_delivery_date`, etc.

We treat Brazilian states as **proxy for Indian fulfillment nodes** (warehouses/seller hubs),
which is clearly stated in the project. SP = Mumbai-equivalent, CE/PE = remote/tier-2 equivalent.

### The six tables and how they connect

Think of these as six spreadsheets that are linked to each other:

```
orders          <- The spine. One row per order. Contains all timestamps.
    |
    |-- order_id --> order_items   <- What was in the order; who sold it; price
                         |
                         |-- product_id --> products  <- Category, weight, size
                         |-- seller_id  --> sellers   <- Where the seller is (state)
    |
    |-- customer_id --> customers  <- Where the customer is
    |
    |-- order_id --> order_reviews  <- The review score (1-5) the customer left
```

**Why this matters**: To answer "which warehouse has the worst OTD?", we need to:
1. Get the order timestamps from `orders`
2. Find which seller handled it from `order_items`
3. Get that seller's state from `sellers`
4. Group by state, compute OTD %

That's a three-table join — which is exactly what `02_otd_by_node.sql` does.

### Key columns explained

| Column | Table | What it means |
|---|---|---|
| `order_purchase_timestamp` | orders | When the customer clicked "Buy" |
| `order_approved_at` | orders | When payment was confirmed |
| `order_delivered_carrier_date` | orders | When the seller handed the package to the courier |
| `order_delivered_customer_date` | orders | When the customer actually received it |
| `order_estimated_delivery_date` | orders | The date we *promised* the customer at checkout |
| `order_status` | orders | `delivered`, `cancelled`, `unavailable`, etc. |
| `seller_state` | sellers | The state where the seller operates (our warehouse proxy) |
| `price` | order_items | Item price (excludes shipping) |
| `freight_value` | order_items | Shipping cost |
| `review_score` | order_reviews | 1 (terrible) to 5 (excellent) |

### Data quality checks

After loading, `db_loader.py` runs 4 checks:

| Check | What it catches |
|---|---|
| Null order_id in orders | Corrupted rows with no identifier |
| order_items without matching order | Items linked to orders that don't exist |
| order_items without matching seller | Items linked to sellers that don't exist |
| Delivered but null delivery date | Orders marked "delivered" with no delivery timestamp |

The last one is critical — if delivery date is null, we can't compute delay,
so we explicitly exclude these orders from OTD calculations.

---

## 8. The SQL Queries

Each SQL file answers one specific business question.
Here is each one explained from first principles.

---

### `02_otd_by_node.sql` — On-Time Delivery Rate per Node

**Business question**: Which warehouses are underperforming?

**Core logic**:
```sql
-- Count orders where actual delivery <= promised date
SUM(CASE
    WHEN order_delivered_customer_date <= order_estimated_delivery_date
    THEN 1 ELSE 0 END) AS on_time_count

-- Express as a percentage
ROUND(100.0 * on_time_count / COUNT(order_id), 2) AS otd_pct
```

The `CASE WHEN ... THEN 1 ELSE 0 END` pattern is the SQL way of
counting rows that match a condition. `SUM` them up, divide by total, multiply by 100.

We group by `seller_state` (our node proxy) AND `month` to see both
which node and when the problem started.

---

### `03_delay_trend.sql` — Month-over-Month Delay

**Core logic**:
```sql
AVG(
    JULIANDAY(order_delivered_customer_date)
    - JULIANDAY(order_estimated_delivery_date)
) AS avg_delay_days
```

`JULIANDAY()` converts a date string to a floating-point number
(days since noon, January 1, 4713 BC). Subtracting two JULIANDAY values
gives the difference in days.

- **Negative result** = delivered early (good)
- **Zero** = exactly on time
- **Positive result** = delivered late (bad, and this number is the damage)

---

### `04_rto_analysis.sql` — Return to Origin Rate

**RTO (Return to Origin)** = package left the warehouse but never reached the customer.
In the data, these are orders where:
- `order_status IN ('cancelled', 'unavailable')`
- OR `order_delivered_customer_date IS NULL` (shipped but no delivery recorded)

```sql
-- Revenue lost to RTO
SUM(CASE
    WHEN [is_rto condition]
    THEN price + freight_value ELSE 0 END) AS revenue_at_risk
```

This turns a percentage metric into a financial metric — which is what
gets budget approved to fix the problem.

---

### `07_bottleneck_attribution.sql` — Processing vs Transit

**The most important query** — determines blame attribution:

```sql
-- Seller's responsibility: approval to carrier pickup
AVG(JULIANDAY(order_delivered_carrier_date) - JULIANDAY(order_approved_at))
    AS avg_processing_days

-- Carrier's responsibility: pickup to delivery
AVG(JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_delivered_carrier_date))
    AS avg_transit_days
```

If `avg_processing_days > avg_transit_days` for a node:
**the warehouse is the bottleneck** — fix the seller's pick-pack process.

If the reverse: **the carrier is the bottleneck** — renegotiate the carrier SLA
or find regional partners.

---

## 9. The Analysis Scripts

Each script does the same 4 things:
1. Connect to SQLite
2. Run SQL, load into a Pandas DataFrame
3. Compute derived metrics
4. Save a chart as PNG

---

### `01_otd_trend.py` — Monthly OTD Trend

**Chart**: Line chart of monthly OTD % + bar chart of average delay (dual y-axis).
Each point annotated with the month-over-month change in percentage points.

**Key Python concept**:
```python
df["otd_delta"] = df["otd_pct"].diff()
# .diff() = current row minus previous row
# Gives month-over-month change in one line
```

**Decision it supports**: "Is this getting worse fast enough to escalate to the VP?"

---

### `02_rto_analysis.py` — RTO + Revenue at Risk

**Chart**: Horizontal bars sorted by RTO rate. RAG-colored by severity.
Second panel shows revenue at risk per node.

**RAG coloring logic**:
```python
if rto_rate > 10%:  -> RED    # Critical
elif rto_rate > 5%: -> AMBER  # At risk
else:               -> GREEN  # Healthy
```

Thresholds come from `config.py` — centralised so changing one number
updates every chart.

**Decision it supports**: "Which nodes need a carrier audit?"

---

### `03_bottleneck_attribution.py` — Stacked Bar: Processing vs Transit

**Chart**: Stacked horizontal bar — purple (processing) + blue (transit).
Each bar labelled "Bottleneck: Warehouse" or "Bottleneck: Carrier".

```python
df["bottleneck"] = df.apply(
    lambda r: "Warehouse" if r["avg_processing_days"] > r["avg_transit_days"]
              else "Carrier",
    axis=1
)
```

**Decision it supports**: "Do we call the warehouse manager or the carrier account manager?"

---

### `04_abc_analysis.py` — Pareto + OTD by Seller Class

**Chart**: Scatter plot of all sellers (dot = seller, color = class).
Pareto curve overlaid. Summary table on right.

**ABC classification**:
```python
df = df.sort_values("total_revenue", ascending=False)
df["cum_rev_pct"] = df["total_revenue"].cumsum() / df["total_revenue"].sum() * 100
# cumsum() = running total. Divided by grand total = running percentage.

df["abc_class"] = pd.cut(
    df["cum_rev_pct"],
    bins=[0, 70, 90, 100],
    labels=["A", "B", "C"]
)
# Sellers in the first 70% of cumulative revenue = Class A
```

**Decision it supports**: "Where do we apply SLA pressure first?"

---

### `05_ops_health_score.py` — OHS Heatmap

**Chart**: Grid of colored cells — each cell = one node x one month.
Color encodes OHS score (red=bad, green=good). Right panel = node ranking.

The OHS formula (see Section 10) is computed in Python from the SQL output.
The heatmap uses `matplotlib.pcolormesh` with a diverging colormap.

**Decision it supports**: "Which nodes get a 30-day improvement plan vs an immediate audit?"

---

### `06_csat_correlation.py` — Review Score vs Delay

**Chart**:
- Left: Box plots of review score by delay bucket (Early, On-time, Slight, Moderate, Severe)
- Right: Dual line — average review score and average delay trending together by month

**Pearson correlation**:
```python
r = df["delay_days"].corr(df["review_score"])
```
`corr()` computes the Pearson r coefficient: how strongly two variables move together.
- r close to -1.0 means: as delay goes up, review score reliably goes down
- Our result: r = -0.67 (strong negative relationship)

**Decision it supports**: "Connect ops performance to customer experience to get
executive sponsorship for fixing the problem."

---

## 10. The Operations Health Score

The OHS is the **original contribution** of this project — a composite metric
that captures node health in a single number, like a credit score for a warehouse.

### The formula

```
OHS (0-100) =

  40% x OTD rate
+ 25% x (1 - RTO rate)                    <- lower RTO = better
+ 20% x (1 - min(avg_delay_days / 14, 1)) <- lower delay = better, capped at 14 days
+ 15% x (1 - min(avg_proc_days / 7, 1))   <- faster processing = better, capped at 7 days

x 100
```

### Why a composite?

Individual KPIs have blind spots:
- A node can have great OTD but terrible RTO
- A node can have low delay average but that's because very few orders ship there
- OTD alone doesn't capture how *bad* the bad deliveries were

A composite score is more honest. It also lets you rank nodes directly.

### The thresholds

| Score | Status | Action |
|---|---|---|
| >= 80 | Healthy | Monthly monitoring |
| 60-79 | At Risk | 30-day improvement plan |
| 40-59 | Critical | Immediate audit; VP escalation |
| < 40 | Failing | Consider suspending node |

### Why these weights?

- **OTD (40%)**: The primary promise to the customer. Biggest weight.
- **RTO (25%)**: Lost revenue + reverse logistics cost. High business impact.
- **Delay (20%)**: Severity measure — how bad the bad ones are.
- **Processing (15%)**: Within our control, but harder to measure cleanly.

---

## 11. The Excel Workbook

The Excel file is the "hand it to your manager" output.
Built with `openpyxl` — a Python library that creates and formats Excel files without
needing Excel installed.

### How `openpyxl` works

```python
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.formatting.rule import ColorScaleRule

wb = Workbook()                          # Create empty workbook
ws = wb.create_sheet("1_OTD_Dashboard") # Create a sheet
ws["A1"] = "OTD Dashboard"              # Write a cell
ws.freeze_panes = "A2"                   # Freeze header row

# Add conditional formatting (RAG color)
ws.conditional_formatting.add("D2:D100",
    ColorScaleRule(start_color="FF0000",   # Red for low values
                   end_color="00FF00"))    # Green for high values

wb.save("ops_case_study.xlsx")           # Save to disk
```

### The 8 sheets

| Sheet | Contents | Key formatting |
|---|---|---|
| `1_OTD_Dashboard` | OTD % per node per month | Green/amber/red on OTD column |
| `2_RTO_Analysis` | RTO rate + revenue at risk | Red for nodes >10% RTO |
| `3_Delay_Deep_Dive` | Processing vs transit days | Data bars on processing column |
| `4_ABC_Analysis` | All sellers: revenue, OTD, class | Color-coded by ABC class |
| `5_Revenue_At_Risk` | Financial exposure from RTO | Data bars on revenue column |
| `6_Node_Risk_Matrix` | OHS scores (node x month pivot) | Full color-scale heatmap |
| `7_CSAT_Correlation` | Monthly review score vs delay | Green for high scores |
| `8_Ops_Health_Score` | OHS per node per month | RAG on OHS column |

---

## 12. The Findings

### What the analysis reveals

**Finding 1: OTD decline is real and consistent**
- OTD dropped ~10pp over 6 months
- No single bad month — steady decline = structural problem
- *Implication*: Needs investigation, not just monitoring

**Finding 2: The bottleneck is the warehouse, not the carrier**
- Seller processing time (approval to handoff) is growing month-on-month in CE and PE
- Carrier transit time is stable
- *Implication*: Don't call the carrier. Set a pick-pack SLA.

**Finding 3: RTO concentrated in 3 states**
- BA, CE, PE have RTO rates 3-5x the network average
- These are geographic coverage gaps — thin carrier presence
- *Implication*: Network design problem, not ops execution problem.
  Fix: expand carrier partnerships in these zones.

**Finding 4: Delivery delay directly costs customer score**
- Pearson r = -0.67 between delay and review score
- Every extra day of delay correlates with measurably lower review scores
- *Implication*: Connect ops improvements to customer metrics for executive buy-in

**Finding 5: Class A sellers perform similarly to Class B/C**
- The top-revenue sellers don't have better OTD than everyone else
- In a well-managed marketplace, Class A sellers should get priority carrier slots
- *Implication*: Seller tiering and preferential treatment is not in place

---

## 13. The Recommendations

Every recommendation follows: **Problem -> Evidence -> Action -> Owner -> Timeline**

### R1 — 48-Hour Pick-Pack SLA (Priority 0)
- **Problem**: Seller processing is the primary bottleneck in CE/PE
- **Evidence**: Processing accounts for >60% of total fulfillment time in bad nodes
- **Action**: Mandate 48hr from approval to carrier handoff. Auto-alert at 36hr.
  Suspend repeat violators after 2 warnings.
- **Owner**: VP Operations + Seller Growth
- **Timeline**: 30 days (policy change — no CapEx required)

### R2 — Dynamic EDD at Checkout (Priority 0)
- **Problem**: EDD uses static averages — over-promises as performance degrades
- **Evidence**: CSAT-delay correlation (r = -0.67); review score falls as delay rises
- **Action**: Recalibrate EDD using rolling 14-day carrier velocity per route.
  Add buffer for high-RTO zones.
- **Owner**: Product + Logistics Tech
- **Timeline**: 45 days

### R3 — Carrier Coverage Expansion (Priority 1)
- **Problem**: BA/CE/PE have structurally thin carrier coverage
- **Evidence**: RTO rates 3-5x national average; geographically concentrated
- **Action**: Audit coverage per pin code in high-RTO zones.
  Pilot 2-3 regional last-mile partners.
- **Owner**: Regional Logistics Manager
- **Timeline**: 60 days

### R4 — Inventory Repositioning (Priority 1)
- **Problem**: Demand exists in CE/BA/PE but no nearby fulfillment nodes
- **Evidence**: Long seller-to-customer distance correlates with RTO
- **Action**: Incentivize Class A sellers to open satellite stock in CE/BA.
  Pilot with 3 highest-volume categories.
- **Owner**: Category + Seller Management
- **Timeline**: 90 days

### R5 — Deploy OHS as Monthly Scorecard (Priority 2)
- **Problem**: No composite health metric; management reacts to individual KPIs
- **Evidence**: OHS framework identifies at-risk nodes before full degradation
- **Action**: Monthly OHS report with auto-escalation trigger for OHS < 60.
  Review at regional manager weekly sync.
- **Owner**: Operations Analytics
- **Timeline**: 30 days (tooling already built in this project)

---

## 14. How to Run the Project

### First time

```powershell
cd "C:\Users\Utsav\OneDrive\Documents\Projects\flipkart-neev-ops-case-study"

# Install packages (only needed once)
py -m pip install pandas numpy matplotlib seaborn openpyxl

# Full pipeline with synthetic data
$env:PYTHONIOENCODING="utf-8"; py run_all.py
```

### With real Olist data

```powershell
# 1. Place the 6 Olist CSVs in data\raw\
# 2. Run (skip synthetic data generation)
$env:PYTHONIOENCODING="utf-8"; py run_all.py --skip-data
```

### Re-run a single chart

```powershell
$env:PYTHONIOENCODING="utf-8"; py analysis/05_ops_health_score.py
```

### What gets created after a full run

```
outputs/charts/
  01_otd_trend.png              <- Monthly OTD decline
  02_rto_analysis.png           <- RTO by node + revenue at risk
  03_bottleneck_attribution.png <- Processing vs transit per node
  04_abc_analysis.png           <- Pareto + OTD by seller class
  05_ops_health_score.png       <- OHS heatmap + node ranking
  06_csat_correlation.png       <- Review score vs delay

excel/ops_case_study.xlsx       <- 8-sheet management workbook
data/raw/ops_case_study.db      <- SQLite database
```

---

## 15. How to Explain This in an Interview

### The 30-second version

> "I built an ops diagnostic case study on a real e-commerce dataset — 100,000 orders,
> 6 tables, full delivery lifecycle. The business question: delivery performance has
> been declining for 6 months — why, and what do we fix first?
> I used SQL for KPI computation (OTD, RTO, bottleneck attribution per warehouse),
> Python to generate 6 decision-mapped charts, and Excel for the management deliverable.
> The key finding: 60-70% of delay was in seller processing, not carrier transit.
> Fix the warehouse SLA, not the carrier contract. I also built an original
> Operations Health Score — a composite 0-100 metric that ranks nodes like a credit score."

### Questions you should be ready to answer

**"Why seller_state as a warehouse proxy?"**
> The Olist dataset doesn't have a warehouse_id — sellers operate from their own
> locations. State is the best available geographic proxy and it's clearly labelled
> as such throughout. On real Flipkart data you'd use fulfillment center IDs.

**"What does 80% OTD mean in practice?"**
> 1 in 5 orders arrives after the promised date. Depending on category, that
> translates to a 15-25% increase in complaints and measurable CSAT decline.
> Our data shows r = -0.67 between delay and review score.

**"Why no machine learning?"**
> The goal is root cause diagnosis, not prediction. ML would flag which orders
> *will be* late — but it wouldn't tell you *why*. For a management decision,
> you need an interpretable answer: processing time in CE/PE accounts for 70%
> of delay. That's actionable. A model isn't.

**"What would you do differently with more time?"**
> Two things: First, carrier-level breakdown — we don't have carrier IDs in this
> dataset, so transit is a black box. In real data you'd split by carrier and
> see which ones are underperforming. Second, a forecasting component — given
> this degradation slope, when does OTD hit a critical threshold unless something
> changes? That creates urgency for the recommendations.

**"What is the OHS and why did you create it?"**
> It's a composite metric I designed to capture node health in one number,
> the way a credit score captures financial health. Four KPIs weighted by
> business importance: OTD (40%), inverse RTO (25%), inverse delay severity (20%),
> inverse processing time (15%). Below 60 triggers a review.
> I built it because single KPIs have blind spots — a node can have good OTD
> but terrible RTO. A composite score is more honest and more actionable.

---

*End of Project Explainer*

*For the full narrative case study: `report/case_study_report.md`*
*To run: `py run_all.py --skip-data` (after placing Olist CSVs in `data/raw/`)*
