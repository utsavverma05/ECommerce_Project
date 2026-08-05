"""
06_csat_correlation.py
-----------------------
Quantifies the relationship between delivery delay and customer review score.
Also plots month-over-month average review score alongside OTD to show
aligned degradation -- strengthening the business case for remediation.

Decision: Quantify CX cost of delivery failure; build the executive case
          that operational metrics and customer satisfaction move together.

Outputs:
  outputs/charts/06_csat_correlation.png
  outputs/csat_delay_data.csv
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

from analysis.config import PALETTE, CHART_DIR, OUTPUT_DIR
from analysis.db_loader import get_conn

CHART_DIR.mkdir(parents=True, exist_ok=True)


def run():
    print("\n[06] CSAT Correlation ...")
    conn = get_conn()

    sql = """
    SELECT
        o.order_id,
        r.review_score,
        JULIANDAY(o.order_delivered_customer_date) -
        JULIANDAY(o.order_estimated_delivery_date)     AS delay_days,
        STRFTIME('%Y-%m', o.order_purchase_timestamp)  AS month
    FROM orders o
    JOIN order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND r.review_score IS NOT NULL
    """
    df = pd.read_sql(sql, conn)
    conn.close()

    df = df.dropna(subset=["delay_days", "review_score"])
    df.to_csv(OUTPUT_DIR / "csat_delay_data.csv", index=False)

    # Correlation coefficient
    corr = df["delay_days"].corr(df["review_score"])

    # Bin delay for box plot clarity
    df["delay_bin"] = pd.cut(
        df["delay_days"],
        bins=[-30, -3, 0, 2, 5, 10, 30],
        labels=["Early\n(>3d)", "On Time\n(0-3d)", "Slight\n(0-2d)",
                "Moderate\n(2-5d)", "Severe\n(5-10d)", "Critical\n(>10d)"]
    )

    # Monthly aggregation
    monthly = df.groupby("month").agg(
        avg_score=("review_score", "mean"),
        avg_delay=("delay_days",   "mean"),
        count    =("order_id",     "count"),
    ).reset_index()
    month_map = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun"}
    monthly["label"] = monthly["month"].str[5:].map(month_map).fillna(monthly["month"].str[5:])

    # -- Plot -------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.patch.set_facecolor("#0F1117")
    for ax in (ax1, ax2):
        ax.set_facecolor("#0F1117")

    # -- Left: box plot by delay bucket ----------------------------------------
    order_cats = ["Early\n(>3d)", "On Time\n(0-3d)", "Slight\n(0-2d)",
                  "Moderate\n(2-5d)", "Severe\n(5-10d)", "Critical\n(>10d)"]
    box_data   = [df[df["delay_bin"] == cat]["review_score"].dropna().values
                  for cat in order_cats]

    bp = ax1.boxplot(
        box_data, tick_labels=order_cats, patch_artist=True,
        medianprops=dict(color="white", linewidth=2),
        whiskerprops=dict(color="gray"), capprops=dict(color="gray"),
        flierprops=dict(marker="o", color=PALETTE["danger"], alpha=0.2, markersize=2)
    )

    colors_box = [PALETTE["success"], PALETTE["success"], PALETTE["warning"],
                  PALETTE["warning"], PALETTE["danger"], PALETTE["danger"]]
    for patch, color in zip(bp["boxes"], colors_box):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax1.set_ylabel("Review Score (1-5)", color="white", fontsize=10)
    ax1.set_xlabel("Delivery Delay Bucket", color="white", fontsize=10)
    ax1.tick_params(colors="white")
    ax1.set_ylim(0.5, 5.5)
    ax1.set_title(f"Review Score by Delay Bucket\nPearson r = {corr:.2f}  "
                  f"(delivery delay <-> customer score)",
                  color="white", fontsize=11, fontweight="bold")
    ax1.axhline(3, color="gray", linestyle="--", alpha=0.4)
    ax1.text(0.02, 3.1, "Neutral score (3)", color="gray",
             transform=ax1.get_yaxis_transform(), fontsize=8, alpha=0.7)

    # -- Right: dual line -- avg score + avg delay by month ---------------------
    x = np.arange(len(monthly))

    ax2r = ax2.twinx()
    ax2r.set_facecolor("#0F1117")

    ax2.plot(x, monthly["avg_score"], color=PALETTE["success"],
             linewidth=2.5, marker="o", markersize=8, label="Avg Review Score")
    ax2r.plot(x, monthly["avg_delay"], color=PALETTE["danger"],
              linewidth=2.5, marker="s", markersize=7, linestyle="--", label="Avg Delay (days)")

    # Annotations
    for i, row in monthly.iterrows():
        ax2.annotate(f"{row['avg_score']:.2f}",
                     (i, row["avg_score"]), textcoords="offset points",
                     xytext=(0, 10), ha="center", color=PALETTE["success"], fontsize=8.5)
        ax2r.annotate(f"{row['avg_delay']:.1f}d",
                      (i, row["avg_delay"]), textcoords="offset points",
                      xytext=(0, -16), ha="center", color=PALETTE["danger"], fontsize=8.5)

    ax2.set_xticks(x)
    ax2.set_xticklabels(monthly["label"], color="white", fontsize=10)
    ax2.set_ylabel("Avg Review Score", color=PALETTE["success"], fontsize=10)
    ax2r.set_ylabel("Avg Delay (days)", color=PALETTE["danger"], fontsize=10)
    ax2.tick_params(axis="y", colors=PALETTE["success"])
    ax2r.tick_params(axis="y", colors=PALETTE["danger"])
    ax2.tick_params(axis="x", colors="white")

    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2r.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2,
               facecolor="#1A1A2E", edgecolor="gray", labelcolor="white", fontsize=8)

    ax2.set_title("CSAT vs Delivery Delay -- Monthly Trend\n"
                  "As delay rises, review scores fall in parallel",
                  color="white", fontsize=11, fontweight="bold")

    plt.tight_layout()
    out = CHART_DIR / "06_csat_correlation.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()

    print(f"   Pearson r (delay vs score): {corr:.3f}")
    print(f"   Avg score: Jan {monthly.iloc[0]['avg_score']:.2f}  ->  "
          f"Jun {monthly.iloc[-1]['avg_score']:.2f}")
    print(f"   [OK] Chart -> {out.relative_to(out.parents[3])}")


if __name__ == "__main__":
    run()
