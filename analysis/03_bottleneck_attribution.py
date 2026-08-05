"""
03_bottleneck_attribution.py
----------------------------
Splits total fulfillment time into seller processing vs carrier transit,
per fulfillment node. Identifies whether the bottleneck is inside the
warehouse or with the carrier.

Decision: Where to invest first -- warehouse ops or carrier SLA enforcement.

Outputs:
  outputs/charts/03_bottleneck_attribution.png
  outputs/bottleneck_by_node.csv
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from analysis.config import PALETTE, CHART_DIR, OUTPUT_DIR
from analysis.db_loader import get_conn

CHART_DIR.mkdir(parents=True, exist_ok=True)


def run():
    print("\n[03] Bottleneck Attribution ...")
    conn = get_conn()

    sql = """
    SELECT
        s.seller_state                                          AS node,
        COUNT(DISTINCT o.order_id)                              AS orders,
        ROUND(AVG(
            JULIANDAY(o.order_delivered_carrier_date) -
            JULIANDAY(o.order_approved_at)
        ), 2)                                                   AS avg_processing_days,
        ROUND(AVG(
            JULIANDAY(o.order_delivered_customer_date) -
            JULIANDAY(o.order_delivered_carrier_date)
        ), 2)                                                   AS avg_transit_days,
        ROUND(AVG(
            JULIANDAY(o.order_delivered_customer_date) -
            JULIANDAY(o.order_approved_at)
        ), 2)                                                   AS avg_total_days
    FROM orders o
    JOIN order_items oi ON o.order_id  = oi.order_id
    JOIN sellers     s  ON oi.seller_id = s.seller_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_delivered_carrier_date  IS NOT NULL
      AND o.order_approved_at             IS NOT NULL
    GROUP BY 1
    ORDER BY avg_total_days DESC
    """
    df = pd.read_sql(sql, conn)
    conn.close()

    df["processing_pct"] = (df["avg_processing_days"] / df["avg_total_days"] * 100).round(1)
    df["bottleneck"]     = df.apply(
        lambda r: "Warehouse" if r["avg_processing_days"] > r["avg_transit_days"] else "Carrier",
        axis=1
    )
    df.to_csv(OUTPUT_DIR / "bottleneck_by_node.csv", index=False)

    # -- Plot -------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor("#0F1117")
    ax.set_facecolor("#0F1117")

    y = np.arange(len(df))
    h = 0.55

    b1 = ax.barh(y, df["avg_processing_days"], height=h,
                 color=PALETTE["accent"], label="Seller Processing (days)", alpha=0.9)
    b2 = ax.barh(y, df["avg_transit_days"], left=df["avg_processing_days"], height=h,
                 color=PALETTE["primary"], label="Carrier Transit (days)", alpha=0.9)

    # Bottleneck label + total
    for i, row in enumerate(df.itertuples()):
        color = PALETTE["accent"] if row.bottleneck == "Warehouse" else PALETTE["primary"]
        ax.text(row.avg_total_days + 0.15, i,
                f"Total: {row.avg_total_days:.1f}d  [{row.bottleneck} ^]",
                va="center", color=color, fontsize=8.5, fontweight="bold")

        # Processing % label inside bar
        if row.avg_processing_days > 0.8:
            ax.text(row.avg_processing_days / 2, i,
                    f"{row.avg_processing_days:.1f}d",
                    va="center", ha="center", color="white", fontsize=8)
        # Transit label inside bar
        if row.avg_transit_days > 1.0:
            ax.text(row.avg_processing_days + row.avg_transit_days / 2, i,
                    f"{row.avg_transit_days:.1f}d",
                    va="center", ha="center", color="white", fontsize=8)

    ax.set_yticks(y)
    ax.set_yticklabels(df["node"], color="white", fontsize=11)
    ax.set_xlabel("Days", color="white", fontsize=10)
    ax.tick_params(colors="white")
    ax.set_xlim(0, df["avg_total_days"].max() * 1.35)
    ax.set_title(
        "Bottleneck Attribution: Seller Processing vs Carrier Transit per Node\n"
        "Decision: Where to invest -- warehouse ops (purple) vs carrier SLA (blue)",
        color="white", fontsize=12, fontweight="bold"
    )
    ax.legend(facecolor="#1A1A2E", edgecolor="gray", labelcolor="white")

    plt.tight_layout()
    out = CHART_DIR / "03_bottleneck_attribution.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()

    # Summary stat: % of total delay from processing across all nodes
    overall_proc_pct = (df["avg_processing_days"] / df["avg_total_days"] * 100).mean()
    warehouse_nodes  = df[df["bottleneck"] == "Warehouse"]["node"].tolist()
    print(f"   Processing accounts for {overall_proc_pct:.0f}% of total fulfillment time (avg)")
    print(f"   Warehouse-bottlenecked nodes: {', '.join(warehouse_nodes)}")
    print(f"   [OK] Chart -> {out.relative_to(out.parents[3])}")


if __name__ == "__main__":
    run()
