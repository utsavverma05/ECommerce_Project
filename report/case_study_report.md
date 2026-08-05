# Delivery Operations Diagnostic — Case Study Report

**Client**: E-Commerce Platform (Synthetic Data — Olist Schema Proxy)
**Analyst**: [Your Name] | **Period**: January 2017 – June 2017
**Stack**: Python (Pandas, Matplotlib), SQL (SQLite), Excel (openpyxl)

---

## Executive Summary

An e-commerce platform's delivery performance degraded materially over 6 months.
On-time delivery (OTD) rate fell from **~88% to ~72% (-16pp)**. Average delivery
delay grew by ~2.3 days. Return-to-origin (RTO) rates exceeded 12% in 3 states.
Customer review scores declined in parallel (r = −0.55 with delay).

Root cause: **Seller processing time** (order approval → carrier handoff) grew
monotonically in 2 specific fulfillment nodes, accounting for ~65–70% of total
fulfillment time. The carrier (transit) component was stable. This is a
**warehouse-side operations failure**, not a carrier capacity problem.

**5 prioritized recommendations** are costed, owned, and timeline-bound.

---

## 1. Problem Decomposition

### 1.1 KPI Scorecard — 6-Month Summary

| KPI | Jan | Jun | Change | Status |
|---|---|---|---|---|
| OTD Rate | ~88% | ~72% | −16pp | 🔴 Critical |
| Avg Delivery Delay | ~0.8d | ~3.1d | +2.3d | 🔴 Critical |
| RTO Rate (network avg) | ~4% | ~7% | +3pp | 🟡 At Risk |
| Avg Review Score | ~4.2 | ~3.5 | −0.7 pts | 🟡 At Risk |
| Seller Processing Time | ~1.5d | ~3.4d | +1.9d | 🔴 Critical |
| Carrier Transit Time | ~5.1d | ~5.4d | +0.3d | 🟢 Stable |

### 1.2 Geographic Concentration

RTO is structurally concentrated:

| State | RTO Rate | vs. Network Avg | Characterization |
|---|---|---|---|
| CE | ~14% | +10pp | Structurally underserved |
| PE | ~13% | +9pp | Thin carrier coverage |
| BA | ~11% | +7pp | Long-haul, low density |
| SP | ~3% | Baseline | Healthy |

### 1.3 Bottleneck Attribution

Across all nodes, the fulfillment time breakdown (averaged):
- **Seller Processing**: ~65–70% of total time
- **Carrier Transit**: ~30–35% of total time

**Bottom 2 decile sellers** (by OTD): processing time 4.5–6d vs. 1.5–2d for top decile.
These sellers serve <25% of volume but generate ~55–60% of delayed orders.

---

## 2. Root Cause Analysis

### RCA 1 — OTD Declining MoM (Primary Issue)

| Level | Finding |
|---|---|
| Why 1 | OTD is declining — more orders delivered past EDD |
| Why 2 | Total fulfillment time has grown by 2.3 days over 6 months |
| Why 3 | Seller processing (approval → carrier handoff) drives ~70% of increase |
| Why 4 | Bottom-20% sellers take 5–7 days to hand off vs. 1.5–2 days for top sellers |
| Why 5 | No enforced pick-pack SLA; carrier pickup windows not monitored |
| **Root Cause** | Absence of seller-side processing SLA enforcement + no carrier pickup accountability |

### RCA 2 — RTO Concentrated in 3 States

| Level | Finding |
|---|---|
| Why 1 | High % of orders in CE/PE/BA not reaching customers |
| Why 2 | Last-mile delivery failure rate structurally elevated in these states |
| Why 3 | Low delivery density → uneconomic for major carriers to maintain coverage |
| Why 4 | All inventory concentrated in SP/RJ nodes; orders are long-haul |
| Why 5 | No inventory positioning policy by demand geography |
| **Root Cause** | Node-demand geographic mismatch + absent carrier coverage in low-density zones |

### RCA 3 — CSAT Declining with OTD

| Level | Finding |
|---|---|
| Why 1 | Average review score declining (4.2 → 3.5 over 6 months) |
| Why 2 | Strong correlation between delay and score (r = −0.55) |
| Why 3 | EDD shown at checkout is being broken — expectation set, then missed |
| Why 4 | EDD based on static historical averages, not live carrier performance |
| **Root Cause** | Static EDD systematically over-promises; disappointment amplified relative to actual delay |

---

## 3. Pareto: Which Problems Matter Most

| Problem | Orders Impacted | Revenue at Risk | OTD Impact |
|---|---|---|---|
| Seller processing bottleneck (bad nodes) | ~55–60% of delays | High (A-class sellers involved) | −10 to −14pp |
| Geographic RTO (CE, PE, BA) | ~12–14% of orders in those states | ~₹4–6M over 6 months | −2 to −3pp on network |
| EDD over-promise | All orders — amplifies CSAT damage | CSAT-driven churn (indirect) | Perception issue |

**The processing bottleneck is the dominant lever.** Fix this first.

---

## 4. Recommendations

### R1 — Enforce 48-Hour Seller Pick-Pack SLA [P0]
- **Problem**: Bottom-20% sellers take 4–7 days to hand off to carriers.
- **Evidence**: Processing days account for ~70% of total delay; bottom decile drives 55% of delayed orders.
- **Action**: Mandate 48hr SLA for all sellers. Auto-alert at 36hr. Suspend repeat violators after 2 warnings in 30 days.
- **Owner**: VP Operations + Seller Growth
- **Timeline**: 30 days (policy + tooling)
- **Expected impact**: OTD +8–12pp if bottom-20% sellers brought to median processing time.

### R2 — Dynamic EDD Recalibration [P0]
- **Problem**: EDD shown at checkout uses static averages; creates expectation gaps when performance degrades.
- **Evidence**: r = −0.55 (delay vs review score). Rising 1-star reviews during delay spikes.
- **Action**: Recalibrate EDD using rolling 14-day carrier velocity per route. Add 1.5× buffer for CE/PE/BA routes.
- **Owner**: Product (EDD model) + Logistics Tech
- **Timeline**: 45 days
- **Expected impact**: CSAT avg +0.3–0.5 pts; 1-star rate −25–35%.

### R3 — Carrier Coverage Expansion in High-RTO States [P1]
- **Problem**: CE/PE/BA have >11% RTO vs ~3% national average.
- **Evidence**: RTO concentrated in structurally thin-coverage zones; long-haul from SP/RJ.
- **Action**: Audit delivery capability per pin code in top-5 high-RTO states. Pilot 2–3 hyperlocal last-mile partners. Renegotiate carrier SLAs with coverage commitment.
- **Owner**: Regional Logistics Manager
- **Timeline**: 60 days
- **Expected impact**: RTO in affected states −5–8pp.

### R4 — Reposition Inventory to Match Demand Geography [P1]
- **Problem**: High demand in CE/PE/BA but no nearby fulfillment nodes.
- **Evidence**: Long seller→customer distance correlates with high RTO and delay.
- **Action**: Work with top-20 Class A sellers to open satellite inventory in CE and BA. Offer storage incentives. Pilot with 3 highest-volume categories in those states.
- **Owner**: Category + Seller Management
- **Timeline**: 90 days
- **Expected impact**: Cross-region delivery time −1.5 days avg; RTO −3–5pp in pilot zones.

### R5 — Deploy Ops Health Score as Monthly Scorecard [P2]
- **Problem**: No composite metric exists; management reacts to individual KPI alerts rather than predicting node failure.
- **Evidence**: OHS framework (Section 7 of case study) not currently operationalized anywhere.
- **Action**: Compute OHS per node per month. Automate RAG report. Auto-trigger SLA review for OHS <60. Dashboard review at regional manager weekly sync.
- **Owner**: Operations Analytics
- **Timeline**: 30 days (tooling already built)
- **Expected impact**: Earlier detection of degradation; prevents full performance cliff.

---

## 5. Implementation Sequencing

```
Month 1:   R1 (SLA policy) + R5 (OHS dashboard)   ← Quick wins, no CapEx
Month 1.5: R2 (Dynamic EDD)                         ← Protect CSAT now
Month 2:   R3 (Carrier audit + negotiation)          ← Field work
Month 3:   R4 (Inventory repositioning pilot)        ← Structural fix
```

---

## 6. Expected Outcomes (6-Month Horizon)

| Metric | Baseline (Jun) | Target (Dec) |
|---|---|---|
| OTD Rate | ~72% | ≥84% |
| Avg Delay | ~3.1 days | ≤1.2 days |
| Network RTO Rate | ~7% | ≤4% |
| Avg Review Score | ~3.5 | ≥4.0 |
| Seller Processing Time | ~3.4 days | ≤2.0 days |

---

## 7. Methodology Note

All analysis uses synthetic data generated to mirror the Olist Brazilian E-Commerce
dataset schema (100,000 orders, 6 tables). Degradation signals are deliberately
encoded into the generator. The same pipeline runs identically on real Olist data
(see `data/README.md`). No results are fabricated or extrapolated from real company data.

---

*Report generated by: `run_all.py` — Flipkart NEEV Ops Case Study v1.0*
