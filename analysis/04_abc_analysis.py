"""
04_abc_analysis.py
------------------
ABC Pareto analysis: sellers classified by cumulative revenue share.
Cross-tabulated with OTD rate to surface the risk quadrant:
  High revenue (Class A) + Low OTD = highest business risk.

Decision: Priority SLA enforcement -- which sellers need immediate
          intervention vs ongoing monitoring.

Outputs:
  outputs/charts/04_abc_analysis.png
  outputs/abc_seller_classification.csv
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
    print("\n[04] ABC Analysis ...")
    conn = get_conn()

    # Use a subquery to compute per-order on-time flag FIRST,
    # then aggregate to seller — avoids double-counting from multi-item orders.
    sql = """
    WITH order_otd AS (
        SELECT
            oi.seller_id,
            s.seller_state,
            o.order_id,
            SUM(oi.price + oi.freight_value)                     AS order_value,
            CASE
                WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
                THEN 1 ELSE 0 END                                AS is_on_time
        FROM orders o
        JOIN order_items oi ON o.order_id  = oi.order_id
        JOIN sellers     s  ON oi.seller_id = s.seller_id
        WHERE o.order_status = 'delivered'
          AND o.order_delivered_customer_date IS NOT NULL
        GROUP BY oi.seller_id, s.seller_state, o.order_id,
                 o.order_delivered_customer_date, o.order_estimated_delivery_date
    )
    SELECT
        seller_id,
        seller_state,
        COUNT(order_id)                               AS total_orders,
        ROUND(SUM(order_value), 2)                    AS total_revenue,
        ROUND(100.0 * SUM(is_on_time) / COUNT(order_id), 2) AS otd_pct
    FROM order_otd
    GROUP BY seller_id, seller_state
    HAVING COUNT(order_id) >= 15
    ORDER BY total_revenue DESC
    """
    df = pd.read_sql(sql, conn)
    conn.close()

    # ABC classification by cumulative revenue
    df = df.sort_values("total_revenue", ascending=False).reset_index(drop=True)
    df["cum_rev_pct"] = df["total_revenue"].cumsum() / df["total_revenue"].sum() * 100
    df["abc_class"]   = pd.cut(
        df["cum_rev_pct"],
        bins=[0, 70, 90, 100],
        labels=["A", "B", "C"],
        include_lowest=True
    )

    # Decile by OTD
    df["otd_decile"] = pd.qcut(df["otd_pct"], q=10, labels=False, duplicates="drop") + 1

    df.to_csv(OUTPUT_DIR / "abc_seller_classification.csv", index=False)

    # -- Summary table for right panel -----------------------------------------
    summary = df.groupby("abc_class", observed=True).agg(
        sellers     =("seller_id",     "count"),
        avg_otd     =("otd_pct",       "mean"),
        total_rev   =("total_revenue", "sum"),
        total_orders=("total_orders",  "sum"),
    ).reset_index()
    summary["rev_share"] = summary["total_rev"] / summary["total_rev"].sum() * 100

    # -- Plot -------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6),
                                   gridspec_kw={"width_ratios": [2.2, 1]})
    fig.patch.set_facecolor("#0F1117")
    for ax in (ax1, ax2):
        ax.set_facecolor("#0F1117")

    # -- Left: Pareto + OTD scatter ---------------------------------------------
    abc_colors = {"A": PALETTE["danger"], "B": PALETTE["warning"], "C": PALETTE["success"]}
    scatter_colors = [abc_colors[c] for c in df["abc_class"].astype(str)]

    x = np.arange(len(df))
    ax1.scatter(x, df["otd_pct"], c=scatter_colors, s=30, alpha=0.75, zorder=3)

    # Cumulative revenue line on twin axis
    ax1b = ax1.twinx()
    ax1b.set_facecolor("#0F1117")
    ax1b.plot(x, df["cum_rev_pct"], color="white", linewidth=1.8,
              linestyle="--", alpha=0.6, label="Cumulative Revenue %")
    ax1b.axhline(70, color=PALETTE["danger"],  linestyle=":", alpha=0.5)
    ax1b.axhline(90, color=PALETTE["warning"], linestyle=":", alpha=0.5)
    ax1b.text(len(df) * 0.02, 71, "A/B split (70%)",
              color=PALETTE["danger"], fontsize=7.5, alpha=0.8)
    ax1b.text(len(df) * 0.02, 91, "B/C split (90%)",
              color=PALETTE["warning"], fontsize=7.5, alpha=0.8)
    ax1b.set_ylabel("Cumulative Revenue (%)", color="white", fontsize=9)
    ax1b.tick_params(colors="white")
    ax1b.set_ylim(0, 105)

    ax1.set_ylabel("OTD Rate (%)", color="white", fontsize=10)
    ax1.set_xlabel("Sellers (sorted by revenue, high -> low)", color="white", fontsize=9)
    ax1.tick_params(colors="white")
    ax1.set_ylim(30, 105)
    ax1.set_title("ABC Pareto: Seller OTD by Revenue Class",
                  color="white", fontsize=12, fontweight="bold")

    patches = [mpatches.Patch(color=v, label=f"Class {k}") for k, v in abc_colors.items()]
    ax1.legend(handles=patches, facecolor="#1A1A2E", edgecolor="gray",
               labelcolor="white", loc="lower right")

    # -- Right: Summary table ---------------------------------------------------
    ax2.axis("off")
    col_labels = ["Class", "Sellers", "Rev Share", "Avg OTD%", "Action"]
    actions    = {
        "A": "[P0] Enforce SLA now",
        "B": "[P1] 30-day plan",
        "C": "[P2] Monitor quarterly",
    }
    table_data = [
        [row["abc_class"],
         f"{int(row['sellers']):,}",
         f"{row['rev_share']:.1f}%",
         f"{row['avg_otd']:.1f}%",
         actions[str(row["abc_class"])]]
        for _, row in summary.iterrows()
    ]

    tbl = ax2.table(
        cellText=table_data, colLabels=col_labels,
        cellLoc="center", loc="center",
        bbox=[0, 0.25, 1, 0.65]
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_facecolor("#1A1A2E" if r > 0 else "#2E86AB")
        cell.set_text_props(color="white")
        cell.set_edgecolor("#0F1117")

    ax2.set_title("ABC Summary + Recommended Action",
                  color="white", fontsize=11, fontweight="bold", pad=10)

    plt.tight_layout()
    out = CHART_DIR / "04_abc_analysis.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()

    for _, row in summary.iterrows():
        print(f"   Class {row['abc_class']}: {int(row['sellers'])} sellers | "
              f"rev share {row['rev_share']:.1f}% | avg OTD {row['avg_otd']:.1f}%")
    print(f"   [OK] Chart -> {out.relative_to(out.parents[3])}")


if __name__ == "__main__":
    run()
