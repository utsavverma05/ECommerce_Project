"""
config.py -- Central configuration for the Flipkart NEEV Ops Case Study.
All paths, constants, and styling tokens in one place.
"""

import os
from pathlib import Path

# -- Project Root --------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent

# -- Paths ---------------------------------------------------------------------
DATA_RAW   = ROOT / "data" / "raw"
DB_PATH    = DATA_RAW / "ops_case_study.db"
OUTPUT_DIR = ROOT / "outputs"
CHART_DIR  = OUTPUT_DIR / "charts"

# -- Synthetic Data Settings ---------------------------------------------------
RANDOM_SEED    = 42
N_ORDERS       = 100_000
N_SELLERS      = 300
N_CUSTOMERS    = 90_000
N_PRODUCTS     = 500

# Analysis window — set to Olist's peak data period (most complete months).
# Change these if using a different date range.
ANALYSIS_START = "2017-09-01"    # Olist peak starts Sep 2017
ANALYSIS_END   = "2018-02-28"    # 6 months of dense data

# States used as fulfillment nodes (seller_state proxy)
SELLER_STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "CE", "PE"]

# High-RTO states (structural underservice -- baked into synthetic data)
HIGH_RTO_STATES = ["CE", "PE", "BA"]

# Underperforming nodes (bottom decile -- drive most degradation)
BAD_NODES = ["CE", "PE"]

# Product categories
CATEGORIES = [
    "electronics", "furniture", "fashion", "sports", "health_beauty",
    "toys", "books", "auto_parts", "home_appliances", "food_beverage",
    "office_supplies", "garden_tools", "musical_instruments", "pet_shop", "watches"
]

# -- Chart Styling -------------------------------------------------------------
PALETTE = {
    "primary":    "#2E86AB",   # blue
    "danger":     "#E84855",   # red
    "warning":    "#F4A261",   # amber
    "success":    "#2D9B72",   # green
    "dark":       "#1A1A2E",   # near-black
    "mid":        "#4A4E69",   # slate
    "light":      "#F2F2F2",   # off-white
    "accent":     "#9B5DE5",   # purple
}

FONT_FAMILY = "DejaVu Sans"   # available in all matplotlib installs

FIGURE_SIZE   = (12, 6)
DPI           = 150

# -- KPI Thresholds ------------------------------------------------------------
OTD_TARGET      = 0.85    # 85% on-time = healthy
RTO_MAX         = 0.05    # 5% RTO = acceptable ceiling
MAX_DELAY_DAYS  = 14      # cap for OHS normalisation
MAX_PROC_DAYS   = 7       # cap for OHS normalisation

# -- OHS Weights ---------------------------------------------------------------
OHS_WEIGHTS = {
    "otd":        0.40,
    "inv_rto":    0.25,
    "inv_delay":  0.20,
    "inv_proc":   0.15,
}
