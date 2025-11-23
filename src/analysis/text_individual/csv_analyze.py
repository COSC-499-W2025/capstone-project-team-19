import os
import pandas as pd
import numpy as np
from collections import defaultdict

# NOTE: All LLM + printing helpers kept only for standalone CLI usage, not pipeline.


def group_csv_files(csv_files):
    """
    Group CSV files that share a similar prefix.
    e.g., data_collection1.csv, data_collection2.csv → one group
    """
    grouped = defaultdict(list)
    for f in csv_files:
        name = f["file_name"]
        prefix = ''.join([c for c in name if not c.isdigit()]).replace(".csv", "")
        prefix = prefix.rstrip("_- ")
        grouped[prefix or name].append(f)
    return grouped


def load_csv(path):
    """Safely load CSV file into pandas DataFrame."""
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None


def analyze_single_csv(df):
    """
    Generate non-LLM structural summary for a single CSV.
    NO numeric stats (min/max/mean) – only shape + missingness + headers + dtypes.
    """
    total_rows = len(df)
    missing_rows = df.isnull().any(axis=1).sum()
    missing_pct = (missing_rows / total_rows * 100) if total_rows > 0 else 0

    summary = {
        "row_count": total_rows,
        "col_count": len(df.columns),
        "headers": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_rows": missing_rows,
        "missing_pct": round(missing_pct, 2),
    }
    return summary


def analyze_all_csv(parsed_files, zip_path):
    """
    Non-printing helper used by the text analysis pipeline.

    Given ALL parsed_files, filter out CSVs, load them, and return metadata.

    Returns:
    {
        "files": [
            {
              "file_name": str,
              "file_path": str,
              "row_count": int,
              "col_count": int,
              "headers": [...],
              "dtypes": {...},
              "missing_rows": int,
              "missing_pct": float,
            },
            ...
        ],
        "growth_trend_present": bool,   # True if any grouped dataset grows over time
        "growth_trends": {             # For debugging / detector evidence
            group_name: [(filename, row_count), ...],
            ...
        },
    }
    """
    # Filter CSVs only
    csv_files = [
        f for f in parsed_files
        if f.get("file_name", "").lower().endswith(".csv")
    ]

    if not csv_files:
        return {
            "files": [],
            "growth_trend_present": False,
            "growth_trends": {},
        }

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    grouped = group_csv_files(csv_files)

    all_file_summaries = []
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
            all_file_summaries.append({
                "file_name": f["file_name"],
                "file_path": f["file_path"],
                **summary,
            })

            growth.append((f["file_name"], summary["row_count"]))

        if len(growth) > 1:
            growth_trends[group_name] = growth
            base_rows = growth[0][1]
            last_rows = growth[-1][1]
            if base_rows > 0 and last_rows > base_rows:
                growth_trend_present = True

    return {
        "files": all_file_summaries,
        "growth_trend_present": growth_trend_present,
        "growth_trends": growth_trends,
    }


