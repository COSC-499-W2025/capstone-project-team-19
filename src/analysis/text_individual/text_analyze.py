import os
import textwrap
from typing import List, Dict
from src.utils.helpers import extract_text_file
from .csv_analyze import analyze_all_csv
from .llm_summary import generate_text_llm_summary
from .alt_summary import prompt_manual_summary
from src.analysis.skills.flows.text_skill_extraction import extract_text_skills
from src.analysis.activity_type.text.activity_type import print_activity, get_activity_contribution_data
from src.db import get_files_with_timestamps, store_text_activity_contribution, get_classification_id
try:
    from src import constants
except ModuleNotFoundError:
    import constants

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
    raw_text_files = [
        f for f in parsed_files
        if f.get("file_type") == "text"
        and not f.get("file_name", "").lower().endswith(".csv")
    ]

    # Decide mode: individual (normal) vs collaborative (suppress_print=True)
    is_collab_mode = bool(suppress_print)

    text_files: List[dict] = []
    for f in raw_text_files:
        norm_path = f.get("file_path", "")
        norm_path = norm_path.replace("\\", "/")

        has_individual = "/individual/" in norm_path or norm_path.startswith("individual/")
        has_collab = "/collaborative/" in norm_path or norm_path.startswith("collaborative/")

        # INDIVIDUAL phase: prefer files under individual/, otherwise use neutral ones
        if not is_collab_mode:
            if has_individual:
                text_files.append(f)
            elif not has_individual and not has_collab:
                text_files.append(f)

        # COLLABORATIVE phase: prefer files under collaborative/, otherwise use neutral ones
        else:
            if has_collab:
                text_files.append(f)
            elif not has_individual and not has_collab:
                text_files.append(f)

    if not text_files and not suppress_print:
        print("No non-CSV text files found to analyze.")
        return []

    # Compute CSV metadata ONCE for the entire project
    csv_metadata = analyze_all_csv(parsed_files, zip_path) or {}

    # Base path to extracted zip
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    # Debug block
    if not suppress_print:
        if constants.VERBOSE:
            print("\n" + "=" * 80)
            print(f"[debug] text project={project_name}")
            print(f"[debug] zip_path arg={zip_path}")
            print(f"[debug] ZIP_DATA_DIR={ZIP_DATA_DIR}")
            print(f"[debug] zip_name={zip_name}")
            print(f"[debug] base_path={base_path}")
            print(f"[debug] base_path exists? {os.path.exists(base_path)}")
            print("=" * 80)

    if not suppress_print:
        if constants.VERBOSE:
            print(f"\nAnalyzing {len(text_files)} text file(s)...\n")

    # Group text files by project folder (collapse individual/collaborative)
    projects: Dict[str, List[dict]] = {}
    for f in text_files:
        path_norm = f["file_path"].replace("\\", "/")
        parts = path_norm.split("/")

        # e.g. "paper_name/individual/paper/file.pdf" → "paper"
        #      "paper_name/collaborative/paper/file.pdf" → "paper"
        #      "paper/file.pdf" → "paper"
        if len(parts) >= 3 and parts[1] in {"individual", "collaborative"}:
            folder = parts[2]
        elif len(parts) >= 1:
            folder = parts[0]
        else:
            continue

        if not suppress_print:
            if constants.VERBOSE:
                print(f"[debug] text file → project: {path_norm}  → {folder}")

        projects.setdefault(folder, []).append(f)

    # Use the passed project_name parameter if available, otherwise use folder names
    # When called from analyze_files, project_name is already set correctly
    for folder_name, files in projects.items():
        # Use the passed project_name parameter to ensure database consistency
        current_project_name = project_name if project_name else folder_name
        if not suppress_print:
            print(f"\n→ {current_project_name}")
        files_sorted = sorted(files, key=lambda x: x["file_name"])

        # --- Select main file ---
        main_file = _select_main_file(files_sorted, base_path)

        # --- Activity type analysis (only for individual mode) ---
        if not suppress_print:
            all_project_files=get_files_with_timestamps(conn,user_id, current_project_name)
        # Store activity type data to database (only if conn is available)
            if conn is not None:
                classification_id=get_classification_id(conn, user_id, current_project_name)
                activity_data=get_activity_contribution_data(all_project_files, main_file_name=main_file['file_name'])
                if classification_id and activity_data:
                    store_text_activity_contribution(conn, classification_id, activity_data)
            print_activity(all_project_files,current_project_name,main_file_name=main_file['file_name'])

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
        csv_files_list = csv_metadata.get("files", []) if isinstance(csv_metadata, dict) else []
        csv_supporting = _csv_files_for_project(folder_name, csv_files_list)

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
            project_name=current_project_name,
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
            "skills": list(skill_result.get("buckets", {}).keys()),
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
