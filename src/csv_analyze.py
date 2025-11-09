import os
import pandas as pd
import numpy as np
import textwrap
import json
from collections import defaultdict
from dotenv import load_dotenv
from groq import Groq
from src.helpers import _fetch_files
import sqlite3
from src.db import connect

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def run_csv_analysis(parsed_files, zip_path, conn, user_id, llm_consent="rejected"):
    csv_files = [
        f for f in parsed_files
        if f.get("file_name", "").lower().endswith(".csv")
    ]
    if not csv_files:
        print("No CSV files found for analysis.")
        return

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    print(f"\n{'='*80}")
    print(f"CSV ANALYSIS — {len(csv_files)} dataset(s) found in project")
    print(f"{'='*80}\n")

    # Group by prefix to detect similar dataset groups
    grouped = group_csv_files(csv_files)

    for group_name, files in grouped.items():
        print(f"\nDataset group: {group_name} ({len(files)} file{'s' if len(files) > 1 else ''})")
        print("-" * 80)

        growth_trend = []
        for f in sorted(files, key=lambda x: x["file_name"]):
            path = os.path.join(base_path, f["file_path"])
            df = load_csv(path)
            if df is None:
                print(f"Could not read {f['file_name']}. Skipping.")
                continue

            summary = analyze_single_csv(df)
            summary_text = generate_dataset_summary(df, f["file_name"], llm_consent)

            # store growth info
            growth_trend.append((f["file_name"], summary["row_count"]))

            print_dataset_summary(f["file_name"], summary, summary_text)

        # print growth trend for grouped datasets
        if len(growth_trend) > 1:
            print_growth_trend(growth_trend)

    print(f"\n{'='*80}")
    print("CSV analysis completed successfully.")
    print(f"{'='*80}\n")


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
    """Generate non-LLM numeric and structural summary."""
    summary = {
        "row_count": len(df),
        "col_count": len(df.columns),
        "headers": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "numeric_stats": {},
    }

    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        if len(series) > 0:
            summary["numeric_stats"][col] = {
                "min": round(series.min(), 3),
                "max": round(series.max(), 3),
                "mean": round(series.mean(), 3),
            }

    return summary


def generate_dataset_summary(df, filename, llm_consent):
    """
    Summarize the dataset's contents either manually or via LLM.
    """
    if llm_consent != "accepted":
        print(f"\nLLM consent not granted. Please describe '{filename}' manually.")
        return input("Enter a short summary of this dataset: ").strip()

    # Limit for safe LLM context size
    preview = df.head(5).to_dict(orient="records")
    columns = list(df.columns)

    prompt = (
        f"You are analyzing a CSV dataset named '{filename}'.\n"
        f"Columns: {columns}\n"
        f"Sample rows:\n{json.dumps(preview, indent=2)}\n\n"
        "Provide a concise 2–3 sentence summary describing what this dataset represents, "
        "what kind of information it stores, and its potential purpose or topic."
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a data analyst who summarizes datasets clearly and concisely."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=150,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating dataset summary via LLM: {e}")
        return "[Summary unavailable due to API error]"


def print_dataset_summary(filename, summary, summary_text):
    print(f"\nFile: {filename}")
    print(f"Rows: {summary['row_count']:,} | Columns: {summary['col_count']}")
    print(f"Headers: {', '.join(summary['headers'])}")
    print(f"Data Types: {json.dumps(summary['dtypes'], indent=2)}")

    if summary["numeric_stats"]:
        print("\nNumeric Columns Summary:")
        for col, stats in summary["numeric_stats"].items():
            print(f"  - {col}: min={stats['min']}, max={stats['max']}, mean={stats['mean']}")
    else:
        print("\n(No numeric columns detected.)")

    print("\nSummary of Content:")
    wrapped = textwrap.fill(summary_text or "[No summary provided]", width=80, subsequent_indent="  ")
    print(f"  {wrapped}\n" + "-" * 80)


def print_growth_trend(growth_trend):
    """Display dataset size progression for grouped files."""
    print("\nGrowth Over Time:")
    base = growth_trend[0][1]
    for fname, rows in growth_trend:
        change = ((rows - base) / base * 100) if base else 0
        print(f"  - {fname}: {rows} rows ({change:+.1f}% vs. first)")
    total_growth = ((growth_trend[-1][1] - growth_trend[0][1]) / growth_trend[0][1]) * 100 if len(growth_trend) > 1 else 0
    print(f"Total Growth: {total_growth:+.1f}%\n" + "-" * 80)

if __name__ == "__main__":
    print("\nStandalone CSV Analysis Mode")
    conn = connect()
    user_id = int(input("Enter user_id: ").strip() or "1")
    project_name = input("Enter project_name: ").strip()
    llm_consent = input("Allow LLM summary? (y/n): ").strip().lower()
    llm_consent = "accepted" if llm_consent in {"y", "yes"} else "rejected"

    parsed_files = _fetch_files(conn, user_id, project_name, only_text=True)
    if not parsed_files:
        print("No CSV files found for this project.")
    else:
        zip_path = input("Enter zip path used during upload: ").strip()
        run_csv_analysis(parsed_files, zip_path, conn, user_id, llm_consent)
