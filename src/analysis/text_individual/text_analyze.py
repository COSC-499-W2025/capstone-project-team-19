# src/analysis/text_individual/text_analyze.py

import os
import textwrap
from typing import List, Dict

from src.utils.helpers import extract_text_file
from .csv_analyze import analyze_all_csv
from .llm_summary import generate_text_llm_summary
from .alt_summary import prompt_manual_summary
from src.analysis.skills.flows.text_skill_extraction import extract_text_skills


def run_text_pipeline(
    parsed_files: List[dict],
    zip_path: str,
    conn,
    user_id: int,
    project_name,
    consent: str = "rejected",
    csv_metadata=None,
    suppress_print=False
):
    """
    Text project analysis with:
      - main vs supporting text file detection
      - supporting CSV metadata via analyze_all_csv
      - summary (LLM or manual)
      - skill detection (later)
    Prints ONLY summary + list of skills.

    No linguistic metrics, no readability, no numeric CSV stats.
    """

    if not isinstance(parsed_files, list):
        return []

    # Normalize paths
    for f in parsed_files:
        if "file_path" in f and isinstance(f["file_path"], str):
            f["file_path"] = os.path.normpath(f["file_path"])

    # Extract NON-CSV text files
    text_files = [
        f for f in parsed_files
        if f.get("file_type") == "text"
        and not f.get("file_name", "").lower().endswith(".csv")
    ]

    if not text_files and not suppress_print:
        print("No non-CSV text files found to analyze.")
        return []

    # Compute CSV metadata ONCE for the entire project
    csv_metadata = analyze_all_csv(parsed_files, zip_path)
    
    # ================================
    # DEBUG: PRINT CSV METADATA
    # ================================
    import pprint
    pp = pprint.PrettyPrinter(indent=2, width=120)

    if not suppress_print:
        print("\n[DEBUG] FULL CSV METADATA (raw analyze_all_csv output):")
        if not csv_metadata:
            print("  → None (no CSVs detected).")
        else:
            pp.pprint(csv_metadata)
        print("[END DEBUG]")

    # ================================

    # Base path to extracted zip
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    if not suppress_print:
        print(f"\n{'=' * 80}")
        print(f"Analyzing {len(text_files)} text file(s)...")
        print(f"{'=' * 80}\n")

    # Group text files by top folder (project name)
    projects: Dict[str, List[dict]] = {}
    for f in text_files:
        folder = f["file_path"].replace("\\", "/").split("/")[0]
        projects.setdefault(folder, []).append(f)

    for project_name, files in projects.items():
        if not suppress_print:
            print(f"\n→ {project_name}")
        files_sorted = sorted(files, key=lambda x: x["file_name"])

        # --- Select main file ---
        main_file = _select_main_file(files_sorted, base_path)

        # --- Load main file content ---
        main_path = os.path.join(base_path, main_file["file_path"])
        main_text = extract_text_file(main_path, conn, user_id)
        if not main_text and not suppress_print:
            print("Could not extract text. Skipping.\n")
            continue

        # --- Supporting text files ---
        supporting_files = [f for f in files_sorted if f != main_file]
        supporting_texts = _load_supporting_texts(
            supporting_files, base_path, conn, user_id
        )

        if not suppress_print:
            print(f"Found {len(supporting_texts)} supporting text file(s).")
            if supporting_texts:
                print("Supporting text files:")
                for s in supporting_texts:
                    print(f"  • {s['filename']}")

        # --- Supporting CSV files (based on folder) ---
        csv_supporting = _csv_files_for_project(project_name, csv_metadata["files"])
        if csv_supporting and not suppress_print:
            print("Detected CSV supporting files:")
            for c in csv_supporting:
                print(f"  • {c['file_name']}")

        # --- Summary ---
        if consent == "accepted":
            summary = generate_text_llm_summary(main_text)
        else:
            summary = prompt_manual_summary(main_file["file_name"])
            
        # === COLLABORATIVE MODE: skip printing + skip skill detectors ===
        if suppress_print:
            return {
                "project_summary": summary,
                "csv_metadata": csv_metadata,
                "main_file": main_file["file_name"]
            }


        # --- Skill detection ---
        skill_result = extract_text_skills(
            main_text=main_text,
            supporting_texts=supporting_texts,
            csv_metadata=csv_metadata,
            project_name=project_name,
            user_id=user_id,
            conn=conn,
        )

        # --- Final output: ONLY summary and skills ---
        if not suppress_print:
            print("\nSummary:")
            print(textwrap.fill(summary, width=80, subsequent_indent="  "))

            print("\nSkill Scores:")
            print("-" * 60)

            for bucket_name, data in skill_result["buckets"].items():
                print(f"{bucket_name:20s}  score={data['score']:.2f}   ({data['description']})")

            print("-" * 60)
            print(f"OVERALL PROJECT SCORE: {skill_result['overall_score']:.2f}")
            print("-" * 60)
        
        # ----------------------------------------------------------
        # RETURN structured results for project_analysis integration
        # ----------------------------------------------------------
        return {
            "project_summary": summary,
            "skills": skill_result.get("skills", []),
            "buckets": skill_result.get("buckets", {}),
            "overall_score": skill_result.get("overall_score"),
            "main_file": main_file["file_name"],
        }


# ----------------- Helpers -----------------

def _select_main_file(files_sorted, base_path):
    """Prompt user or auto-select main text file."""
    if len(files_sorted) == 1:
        main = files_sorted[0]
        print(f"Only one text file detected: {main['file_name']}")
        return main

    print("\nSelect the MAIN (final) file for this project:")
    for idx, f in enumerate(files_sorted, start=1):
        print(f"  {idx}. {f['file_name']}")

    choice = input(
        "Enter number of main file (or press Enter to auto-select largest): "
    ).strip()

    if choice.isdigit() and 1 <= int(choice) <= len(files_sorted):
        return files_sorted[int(choice) - 1]

    # fallback: largest file on disk
    return max(
        files_sorted,
        key=lambda f: os.path.getsize(os.path.join(base_path, f["file_path"])),
    )


def _load_supporting_texts(files, base_path, conn, user_id):
    supporting = []
    for f in files:
        path = os.path.join(base_path, f["file_path"])
        content = extract_text_file(path, conn, user_id)
        if content:
            supporting.append({"filename": f["file_name"], "text": content})
    return supporting


def _csv_files_for_project(project_name, csv_summaries):
    """Return CSVs whose top folder == project_name."""
    matches = []
    for entry in csv_summaries:
        top = entry.get("file_path", "").replace("\\", "/").split("/")[0]
        if top == project_name:
            matches.append(entry)
    return matches
