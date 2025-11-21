import os
import pandas as pd
import numpy as np
from collections import defaultdict


# -------------------------------
# INTERNAL HELPERS
# -------------------------------

def group_csv_files(csv_files):
    """
    Group CSV files that share a similar prefix.
    e.g., data1.csv, data2.csv → one group
    """
    grouped = defaultdict(list)
    for f in csv_files:
        name = f["file_name"]
        prefix = ''.join([c for c in name if not c.isdigit()]).replace(".csv", "")
        prefix = prefix.rstrip("_- ")
        grouped[prefix or name].append(f)
    return grouped


def load_csv(path):
    """Safely load CSV file into pandas DataFrame. Returns None if load fails."""
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def analyze_single_csv(df):
    """
    Generate clean, non-printing metadata summary.
    (numeric statistics removed — per user instruction)
    """
    total_rows = len(df)
    missing_rows = df.isnull().any(axis=1).sum()
    missing_pct = (missing_rows / total_rows * 100) if total_rows > 0 else 0

    return {
        "row_count": total_rows,
        "col_count": len(df.columns),
        "headers": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_rows": missing_rows,
        "missing_pct": round(missing_pct, 2),
    }


# -------------------------------
# MAIN NON-PRINTING ENTRY POINT
# -------------------------------

def analyze_all_csv(csv_files, zip_path):
    """
    Clean, non-printing helper for text analysis.

    Returns:
    {
        "files": [ {csv metadata}, ... ],
        "growth_trend_present": bool,
        "growth_trends": { group_name: [(filename, row_count), ...] }
    }
    """
    if not csv_files:
        return {
            "files": [],
            "growth_trend_present": False,
            "growth_trends": {},
        }

    # Locate base path
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    grouped = group_csv_files(csv_files)

    all_summaries = []
    growth_trends = {}
    growth_trend_present = False

    for group_name, files in grouped.items():
        growth = []
        for f in sorted(files, key=lambda x: x["file_name"]):
            path = os.path.join(base_path, f["file_path"])
            df = load_csv(path)
            if df is None:
                continue

            summary = analyze_single_csv(df)

            all_summaries.append({
                "file_name": f["file_name"],
                "file_path": f["file_path"],
                **summary
            })

            growth.append((f["file_name"], summary["row_count"]))

        # detect growth trend per group
        if len(growth) > 1:
            growth_trends[group_name] = growth
            base_rows = growth[0][1]
            last_rows = growth[-1][1]
            if base_rows > 0 and last_rows > base_rows:
                growth_trend_present = True

    return {
        "files": all_summaries,
        "growth_trend_present": growth_trend_present,
        "growth_trends": growth_trends,
    }

