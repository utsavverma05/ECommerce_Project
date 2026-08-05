"""
01_otd_trend.py
---------------
Monthly OTD rate + average delay trend.
Decision: Executive escalation trigger -- is degradation accelerating?

Outputs:
  outputs/charts/01_otd_trend.png
  outputs/otd_trend.csv
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patches as mpatches
import numpy as np

from analysis.config import PALETTE, CHART_DIR, OUTPUT_DIR, OTD_TARGET
from analysis.db_loader import get_conn

CHART_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run():
    print("\n[01] OTD Trend Analysis ...")
    conn = get_conn()

    sql = """
    SELECT
        STRFTIME('%Y-%m', order_purchase_timestamp)   AS month,
        COUNT(order_id)                                AS orders,
        ROUND(AVG(
            JULIANDAY(order_delivered_customer_date) -
            JULIANDAY(order_estimated_delivery_date)
        ), 3)                                          AS avg_delay_days,
        ROUND(100.0 * SUM(CASE
            WHEN order_delivered_customer_date <= order_estimated_delivery_date
            THEN 1 ELSE 0 END) / COUNT(order_id), 3)  AS otd_pct
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """
    df = pd.read_sql(sql, conn)
    conn.close()

    df["month_label"] = df["month"].str[5:]   # e.g. "01" -> "Jan"
    month_map = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun"}
    df["month_label"] = df["month"].str[5:].map(month_map).fillna(df["month"].str[5:])

    # -- MoM delta --------------------------------------------------------------
    df["otd_delta"] = df["otd_pct"].diff()
    df["delay_delta"] = df["avg_delay_days"].diff()

    # Save CSV
    df.to_csv(OUTPUT_DIR / "otd_trend.csv", index=False)

    # -- Plot -------------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(13, 6))
    ax2 = ax1.twinx()
    fig.patch.set_facecolor("#0F1117")
    ax1.set_facecolor("#0F1117")

    x = np.arange(len(df))
    bar_width = 0.5

    # Bars = avg delay days
    bars = ax2.bar(x, df["avg_delay_days"], width=bar_width,
                   color=PALETTE["danger"], alpha=0.25, label="Avg Delay (days)")

    # Line = OTD%
    ax1.plot(x, df["otd_pct"], color=PALETTE["primary"],
             linewidth=2.8, marker="o", markersize=8, zorder=5, label="OTD Rate (%)")

    # Target line
    ax1.axhline(OTD_TARGET * 100, color=PALETTE["success"],
                linestyle="--", linewidth=1.5, alpha=0.7, zorder=4)
    ax1.text(len(df) - 0.5, OTD_TARGET * 100 + 0.4,
             f"Target {OTD_TARGET*100:.0f}%", color=PALETTE["success"],
             fontsize=9, ha="right")

    # Annotate each OTD point
    for i, row in df.iterrows():
        delta_str = ""
        if pd.notna(row["otd_delta"]):
            sign  = "^" if row["otd_delta"] > 0 else "v"
            color = PALETTE["success"] if row["otd_delta"] > 0 else PALETTE["danger"]
            delta_str = f"\n{sign}{abs(row['otd_delta']):.1f}pp"
        ax1.annotate(f"{row['otd_pct']:.1f}%{delta_str}",
                     (i, row["otd_pct"]),
                     textcoords="offset points", xytext=(0, 14),
                     ha="center", fontsize=8.5,
                     color=color if delta_str else PALETTE["primary"])

    ax1.set_xticks(x)
    ax1.set_xticklabels(df["month_label"], color="white", fontsize=11)
    ax1.set_ylabel("On-Time Delivery Rate (%)", color=PALETTE["primary"], fontsize=11)
    ax2.set_ylabel("Avg Delay (days)", color=PALETTE["danger"], fontsize=11)
    ax1.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.1f%%"))
    ax1.tick_params(axis="y", colors=PALETTE["primary"])
    ax2.tick_params(axis="y", colors=PALETTE["danger"])
    ax1.tick_params(axis="x", colors="white")
    ax1.set_ylim(60, 100)

    ax1.set_title("Monthly OTD Rate & Average Delivery Delay\n"
                  "Decision: Escalation trigger -- degradation accelerating from Jan->Jun",
                  color="white", fontsize=13, fontweight="bold", pad=15)

    patch1 = mpatches.Patch(color=PALETTE["primary"], label="OTD Rate (%)")
    patch2 = mpatches.Patch(color=PALETTE["danger"],  alpha=0.5, label="Avg Delay (days)")
    ax1.legend(handles=[patch1, patch2], loc="lower left",
               facecolor="#1A1A2E", edgecolor="gray", labelcolor="white")

    plt.tight_layout()
    out = CHART_DIR / "01_otd_trend.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()

    # -- Print summary ----------------------------------------------------------
    first, last = df.iloc[0], df.iloc[-1]
    print(f"   OTD Jan: {first['otd_pct']:.1f}%  ->  Jun: {last['otd_pct']:.1f}%  "
          f"({last['otd_pct']-first['otd_pct']:+.1f}pp)")
    print(f"   Avg delay Jan: {first['avg_delay_days']:.2f}d  ->  Jun: {last['avg_delay_days']:.2f}d")
    print(f"   [OK] Chart -> {out.relative_to(out.parents[3])}")


if __name__ == "__main__":
    run()
