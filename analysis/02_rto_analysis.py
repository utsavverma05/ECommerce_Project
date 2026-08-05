"""
02_rto_analysis.py
------------------
RTO rate by fulfillment node (seller_state) + revenue at risk.
Decision: Last-mile partner audit; which nodes to deprioritize / seek
          alternative carrier coverage.

Outputs:
  outputs/charts/02_rto_analysis.png
  outputs/rto_by_node.csv
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from analysis.config import PALETTE, CHART_DIR, OUTPUT_DIR, RTO_MAX, HIGH_RTO_STATES
from analysis.db_loader import get_conn

CHART_DIR.mkdir(parents=True, exist_ok=True)


def run():
    print("\n[02] RTO Analysis ...")
    conn = get_conn()

    sql = """
    SELECT
        s.seller_state                                          AS node,
        COUNT(DISTINCT o.order_id)                              AS total_orders,
        SUM(CASE
            WHEN o.order_status IN ('cancelled','unavailable')
              OR o.order_delivered_customer_date IS NULL
            THEN 1 ELSE 0 END)                                  AS rto_orders,
        ROUND(100.0 * SUM(CASE
            WHEN o.order_status IN ('cancelled','unavailable')
              OR o.order_delivered_customer_date IS NULL
            THEN 1 ELSE 0 END) / COUNT(DISTINCT o.order_id), 2) AS rto_rate_pct,
        ROUND(SUM(CASE
            WHEN o.order_status IN ('cancelled','unavailable')
              OR o.order_delivered_customer_date IS NULL
            THEN oi.price + oi.freight_value ELSE 0 END), 0)   AS revenue_at_risk
    FROM orders o
    JOIN order_items oi ON o.order_id  = oi.order_id
    JOIN sellers     s  ON oi.seller_id = s.seller_id
    GROUP BY 1
    ORDER BY rto_rate_pct DESC
    """
    df = pd.read_sql(sql, conn)
    conn.close()

    df.to_csv(OUTPUT_DIR / "rto_by_node.csv", index=False)

    # -- Color bars by severity -------------------------------------------------
    colors = []
    for _, row in df.iterrows():
        if row["rto_rate_pct"] >= RTO_MAX * 100 * 2:      # >10% -- critical
            colors.append(PALETTE["danger"])
        elif row["rto_rate_pct"] >= RTO_MAX * 100:         # >5% -- warning
            colors.append(PALETTE["warning"])
        else:
            colors.append(PALETTE["success"])

    # -- Plot -------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6),
                                   gridspec_kw={"width_ratios": [1.6, 1]})
    fig.patch.set_facecolor("#0F1117")
    for ax in (ax1, ax2):
        ax.set_facecolor("#0F1117")

    y = np.arange(len(df))

    # Left: RTO rate bar chart
    bars = ax1.barh(y, df["rto_rate_pct"], color=colors, edgecolor="#0F1117",
                    linewidth=0.5, height=0.6)
    ax1.axvline(RTO_MAX * 100, color="white", linestyle="--",
                linewidth=1.2, alpha=0.6)
    ax1.text(RTO_MAX * 100 + 0.15, len(df) - 0.5,
             f"Acceptable ceiling {RTO_MAX*100:.0f}%",
             color="white", fontsize=8, alpha=0.75)

    # Labels on bars
    for i, (bar, row) in enumerate(zip(bars, df.itertuples())):
        ax1.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                 f"{row.rto_rate_pct:.1f}%  ({row.rto_orders:,} orders)",
                 va="center", color="white", fontsize=8.5)

    ax1.set_yticks(y)
    ax1.set_yticklabels(df["node"], color="white", fontsize=11)
    ax1.set_xlabel("RTO Rate (%)", color="white", fontsize=10)
    ax1.tick_params(colors="white")
    ax1.set_title("RTO Rate by Fulfillment Node", color="white",
                  fontsize=12, fontweight="bold")
    ax1.set_xlim(0, df["rto_rate_pct"].max() * 1.35)

    # Right: Revenue at risk
    rev_k = df["revenue_at_risk"] / 1000
    bar2  = ax2.barh(y, rev_k,
                     color=[PALETTE["danger"] if n in HIGH_RTO_STATES
                            else PALETTE["mid"] for n in df["node"]],
                     height=0.6)
    for bar, val in zip(bar2, rev_k):
        ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                 f"Rs.{val:.0f}K", va="center", color="white", fontsize=8.5)

    ax2.set_yticks(y)
    ax2.set_yticklabels(df["node"], color="white", fontsize=11)
    ax2.set_xlabel("Revenue at Risk (Rs.K)", color="white", fontsize=10)
    ax2.tick_params(colors="white")
    ax2.set_title("Revenue at Risk per Node", color="white",
                  fontsize=12, fontweight="bold")

    # Legend
    legend_els = [
        mpatches.Patch(color=PALETTE["danger"],  label="Critical (>10%)"),
        mpatches.Patch(color=PALETTE["warning"], label="At Risk (5-10%)"),
        mpatches.Patch(color=PALETTE["success"], label="Healthy (<5%)"),
    ]
    ax1.legend(handles=legend_els, loc="lower right",
               facecolor="#1A1A2E", edgecolor="gray", labelcolor="white", fontsize=8)

    fig.suptitle("RTO Analysis -- Decision: Last-Mile Partner Audit",
                 color="white", fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    out = CHART_DIR / "02_rto_analysis.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()

    total_risk = df["revenue_at_risk"].sum()
    worst      = df.iloc[0]
    print(f"   Worst node: {worst['node']}  RTO {worst['rto_rate_pct']:.1f}%")
    print(f"   Total revenue at risk: Rs.{total_risk:,.0f}")
    print(f"   [OK] Chart -> {out.relative_to(out.parents[3])}")


if __name__ == "__main__":
    run()
