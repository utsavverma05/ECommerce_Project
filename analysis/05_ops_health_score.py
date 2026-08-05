
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from analysis.config import (
    PALETTE, CHART_DIR, OUTPUT_DIR,
    OHS_WEIGHTS, MAX_DELAY_DAYS, MAX_PROC_DAYS
)
from analysis.db_loader import get_conn

CHART_DIR.mkdir(parents=True, exist_ok=True)


def compute_ohs(otd, rto, delay, proc):
    inv_rto   = 1 - np.clip(rto, 0, 1)
    inv_delay = 1 - np.clip(delay / MAX_DELAY_DAYS, 0, 1)
    inv_proc  = 1 - np.clip(proc  / MAX_PROC_DAYS,  0, 1)
    score = (OHS_WEIGHTS["otd"]       * np.clip(otd, 0, 1)
           + OHS_WEIGHTS["inv_rto"]   * inv_rto
           + OHS_WEIGHTS["inv_delay"] * inv_delay
           + OHS_WEIGHTS["inv_proc"]  * inv_proc)
    return np.round(score * 100, 1)


def run():
    print("\n[05] Operations Health Score ...")
    conn = get_conn()

    sql = """
    SELECT
        s.seller_state                                          AS node,
        STRFTIME('%Y-%m', o.order_purchase_timestamp)           AS month,
        COUNT(DISTINCT o.order_id)                              AS total_orders,
        ROUND(AVG(CASE
            WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
            THEN 1.0 ELSE 0.0 END), 4)                         AS otd_rate,
        ROUND(AVG(CASE
            WHEN o.order_status IN ('cancelled','unavailable')
              OR o.order_delivered_customer_date IS NULL
            THEN 1.0 ELSE 0.0 END), 4)                         AS rto_rate,
        ROUND(AVG(CASE
            WHEN o.order_delivered_customer_date IS NOT NULL
            THEN MAX(0, JULIANDAY(o.order_delivered_customer_date)
                      - JULIANDAY(o.order_estimated_delivery_date))
            ELSE 0 END), 4)                                     AS avg_delay_days,
        ROUND(AVG(CASE
            WHEN o.order_delivered_carrier_date IS NOT NULL
              AND o.order_approved_at IS NOT NULL
            THEN JULIANDAY(o.order_delivered_carrier_date)
                 - JULIANDAY(o.order_approved_at)
            ELSE NULL END), 4)                                  AS avg_proc_days
    FROM orders o
    JOIN order_items oi ON o.order_id  = oi.order_id
    JOIN sellers     s  ON oi.seller_id = s.seller_id
    GROUP BY 1, 2
    ORDER BY 1, 2
    """
    df = pd.read_sql(sql, conn)
    conn.close()

    df["ohs"] = compute_ohs(
        df["otd_rate"], df["rto_rate"],
        df["avg_delay_days"], df["avg_proc_days"].fillna(df["avg_proc_days"].median())
    )
    df["status"] = pd.cut(df["ohs"], bins=[0, 60, 80, 100],
                          labels=["Critical", "At Risk", "Healthy"],
                          include_lowest=True)
    df.to_csv(OUTPUT_DIR / "ops_health_score.csv", index=False)

    # -- Pivot to heatmap matrix ------------------------------------------------
    pivot = df.pivot_table(index="node", columns="month", values="ohs", aggfunc="mean")
    pivot = pivot.sort_values(pivot.columns[-1])   # sort by latest month OHS

    # -- Plot -------------------------------------------------------------------
    fig, (ax_heat, ax_bar) = plt.subplots(1, 2, figsize=(16, 6),
                                           gridspec_kw={"width_ratios": [2.2, 1]})
    fig.patch.set_facecolor("#0F1117")
    for ax in (ax_heat, ax_bar):
        ax.set_facecolor("#0F1117")

    # Custom colormap: red -> amber -> green
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "ohs_cmap",
        [(0, "#E84855"), (0.6, "#F4A261"), (1.0, "#2D9B72")]
    )

    im = ax_heat.imshow(pivot.values, cmap=cmap, vmin=40, vmax=100, aspect="auto")

    month_labels = [m[5:] for m in pivot.columns]
    month_map    = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun"}
    month_labels = [month_map.get(m, m) for m in month_labels]

    ax_heat.set_xticks(np.arange(len(pivot.columns)))
    ax_heat.set_xticklabels(month_labels, color="white", fontsize=10)
    ax_heat.set_yticks(np.arange(len(pivot.index)))
    ax_heat.set_yticklabels(pivot.index, color="white", fontsize=10)
    ax_heat.tick_params(colors="white")

    # Annotate cells
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                text_color = "white" if val < 70 else "#0F1117"
                ax_heat.text(j, i, f"{val:.0f}", ha="center", va="center",
                             color=text_color, fontsize=9, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax_heat, shrink=0.85)
    cbar.set_label("OHS Score", color="white", fontsize=9)
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

    ax_heat.set_title("Operations Health Score -- Node x Month Heatmap\n"
                      "Decision: Trigger SLA review for nodes scoring <60",
                      color="white", fontsize=11, fontweight="bold")

    # -- Right: Final month ranking bar ----------------------------------------
    latest  = pivot.iloc[:, -1].sort_values()
    bar_clr = ["#E84855" if v < 60 else "#F4A261" if v < 80 else "#2D9B72"
               for v in latest]

    y = np.arange(len(latest))
    ax_bar.barh(y, latest.values, color=bar_clr, height=0.6)
    ax_bar.axvline(80, color=PALETTE["success"], linestyle="--", linewidth=1.2, alpha=0.7)
    ax_bar.axvline(60, color=PALETTE["danger"],  linestyle="--", linewidth=1.2, alpha=0.7)

    for i, (node, val) in enumerate(latest.items()):
        ax_bar.text(val + 0.5, i, f"{val:.0f}", va="center",
                    color="white", fontsize=9, fontweight="bold")

    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels(latest.index, color="white", fontsize=10)
    ax_bar.set_xlabel("OHS Score (latest month)", color="white", fontsize=9)
    ax_bar.tick_params(colors="white")
    ax_bar.set_xlim(0, 110)
    ax_bar.set_title("Latest Month Ranking", color="white",
                     fontsize=11, fontweight="bold")

    plt.tight_layout()
    out = CHART_DIR / "05_ops_health_score.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()

    latest_df = df[df["month"] == df["month"].max()].sort_values("ohs")
    critical  = latest_df[latest_df["status"] == "Critical"]["node"].tolist()
    print(f"   Critical nodes (latest month): {', '.join(critical) if critical else 'None'}")
    print(f"   OHS range: {df['ohs'].min():.1f} - {df['ohs'].max():.1f}")
    print(f"   [OK] Chart -> {out.relative_to(out.parents[3])}")


if __name__ == "__main__":
    run()
