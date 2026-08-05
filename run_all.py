"""
run_all.py
----------
Master runner -- executes the full case study pipeline end-to-end.

Steps:
  1. Generate synthetic data (if not already present)
  2. Load data into SQLite
  3. Run all 6 analysis scripts -> 6 charts
  4. Build Excel workbook (8 sheets)

Usage:
  python run_all.py
  python run_all.py --skip-data     # if CSVs already exist
  python run_all.py --skip-excel    # skip workbook build
"""

import sys
import time
import argparse
import subprocess
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from analysis.config import DATA_RAW, OUTPUT_DIR, CHART_DIR


def banner(step, total, msg):
    filled  = "#" * step
    empty   = "." * (total - step)
    print(f"\n  [{step}/{total}] [{filled}{empty}]  {msg}")


def sep(char="=", width=60):
    print(char * width)


def main():
    parser = argparse.ArgumentParser(description="Flipkart NEEV Case Study -- Full Pipeline")
    parser.add_argument("--skip-data",  action="store_true", help="Skip synthetic data generation")
    parser.add_argument("--skip-excel", action="store_true", help="Skip Excel workbook generation")
    args = parser.parse_args()

    total = 9
    t0    = time.time()

    print()
    sep()
    print("  Flipkart NEEV Ops Case Study -- Full Pipeline Runner")
    sep()

    # Step 1: Generate data
    banner(1, total, "Synthetic Data Generation")
    csv_check = DATA_RAW / "olist_orders_dataset.csv"
    if args.skip_data and csv_check.exists():
        print("  Skipped (--skip-data flag; CSVs exist)")
    else:
        env = {**__import__("os").environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [sys.executable, str(ROOT / "data" / "generate_synthetic_data.py")],
            env=env
        )
        if result.returncode != 0:
            print("  [FAIL] Data generation failed.")
            sys.exit(1)

    # Step 2: Load to SQLite
    banner(2, total, "Loading CSVs -> SQLite")
    from analysis.db_loader import load_all
    load_all()

    # Steps 3-8: Analysis scripts
    analysis_scripts = [
        (3, "OTD Trend",              "analysis/01_otd_trend.py"),
        (4, "RTO Analysis",           "analysis/02_rto_analysis.py"),
        (5, "Bottleneck Attribution", "analysis/03_bottleneck_attribution.py"),
        (6, "ABC Analysis",           "analysis/04_abc_analysis.py"),
        (7, "Ops Health Score",       "analysis/05_ops_health_score.py"),
        (8, "CSAT Correlation",       "analysis/06_csat_correlation.py"),
    ]

    env = {**__import__("os").environ, "PYTHONIOENCODING": "utf-8"}

    for step_n, label, script_rel in analysis_scripts:
        banner(step_n, total, label)
        script_file = ROOT / script_rel
        result = subprocess.run([sys.executable, str(script_file)], env=env)
        if result.returncode != 0:
            print(f"  [FAIL] {label} failed.")
            sys.exit(1)

    # Step 9: Excel workbook
    banner(9, total, "Excel Workbook")
    if args.skip_excel:
        print("  Skipped (--skip-excel flag)")
    else:
        result = subprocess.run(
            [sys.executable, str(ROOT / "excel" / "generate_workbook.py")],
            env=env
        )
        if result.returncode != 0:
            print("  [FAIL] Excel build failed.")
            sys.exit(1)

    # Summary
    elapsed = time.time() - t0
    charts  = sorted(CHART_DIR.glob("*.png"))

    print()
    sep()
    print("  [OK] Pipeline Complete!")
    sep("-")
    print(f"  Charts generated : {len(charts)} PNG files")
    print(f"  Excel workbook   : excel/ops_case_study.xlsx")
    print(f"  OHS data         : outputs/ops_health_score.csv")
    print(f"  Total runtime    : {elapsed:.1f}s")
    sep()
    print()
    print("  Charts:")
    for c in charts:
        print(f"    {c.name}")


if __name__ == "__main__":
    main()
