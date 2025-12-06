from src.utils.language_detector import detect_languages
from src.utils.framework_detector import detect_frameworks

import sqlite3
import json

# TEXT ANALYSIS imports
from src.analysis.text_individual.text_analyze import run_text_pipeline
from src.analysis.text_individual.csv_analyze import analyze_all_csv
from src.db import get_classification_id, get_text_activity_contribution
from src.analysis.text_collaborative.text_collab_analysis import analyze_collaborative_text_project
from src.integrations.google_drive.google_drive_auth.text_project_setup import setup_text_project_drive_connection

# CODE ANALYSIS imports
from src.analysis.code_individual.code_llm_analyze import run_code_llm_analysis
from src.analysis.code_individual.code_non_llm_analysis import run_code_non_llm_analysis, prompt_manual_code_project_summary
from src.utils.helpers import _fetch_files
from src.analysis.code_collaborative.code_collaborative_analysis import analyze_code_project, print_code_portfolio_summary
from src.integrations.google_drive.process_project_files import process_project_files
from src.db.project_summaries import save_project_summary
from src.db.skills import get_project_skills
from src.db import get_text_non_llm_metrics, get_classification_id
from src.db.code_metrics import (
    insert_code_complexity_metrics,
    update_code_complexity_metrics,
    code_complexity_metrics_exists,
)
from src.db.code_metrics_helpers import extract_complexity_metrics
import json
from src.analysis.code_collaborative.code_collaborative_analysis import analyze_code_project, print_code_portfolio_summary, set_manual_descs_store, prompt_collab_descriptions
from src.models.project_summary import ProjectSummary
from src.analysis.skills.flows.skill_extraction import extract_skills
from src.analysis.activity_type.code.summary import build_activity_summary
from src.analysis.activity_type.code.formatter import format_activity_summary
from src.db import store_code_activity_metrics
from src.db import get_metrics_id, insert_code_collaborative_summary
import src.constants as constants


def detect_project_type(conn: sqlite3.Connection, user_id: int, assignments: dict[str, str]) -> None:
    """
    Determine if each project is code or text by examining files from the 'files' table
    Updates the project_classifications table with the detected type.

    The function:
        1. Reads all files for the given user from the 'files' table
        2. Counts how many files of type 'code' or 'text' belong to each project
        3. Assigns a project type automatically if unambiguous
        4. If a project contains both code and text files, the user is prompted to decide
        5. Updates the 'project_classifications' table accordingly

    Notes:
        - Projects with no recognizable files (neither code nor text) are skipped and left with a NULL `project_type`
        - Mixed projects require user input to classify manually
    """

    # Grabs file project_name and file_type from 'files' table and creates a list
    files = conn.execute("""
        SELECT project_name, file_type
        FROM files
        WHERE user_id = ? AND project_name IS NOT NULL
    """, (user_id,)).fetchall()

    project_counts = {}

    # counts how many code files vs text files there are in a project
    for project_name, file_type in files:
        if project_name not in project_counts:
            project_counts[project_name] = {"code": 0, "text": 0}
        if file_type in {"code", "text"}:
            project_counts[project_name][file_type] += 1

    # Decides which project is which type based on project_counts values
    for project_name, classification in assignments.items():
        counts = project_counts.get(project_name, {"code": 0, "text": 0})

        if counts["code"] > 0 and counts["text"] == 0:
            project_type = "code"
        elif counts["text"] > 0 and counts["code"] == 0:
            project_type = "text"
        elif counts["code"] == 0 and counts["text"] == 0: # likely will not happen, rare case (still important to check)
            # No recognizable files at all
            print(f"No valid files found for project '{project_name}'. Project type left as NULL.")
            project_type = None
        else:
            # project type can not be decided, mixed files
            # prompt user to state whether a project is code or text
            print(f"\nThe project '{project_name}' contains both code and text files.")
            while True:
                choice = input("Type 'c' if it's mainly a CODE project, or 't' if it's mainly a TEXT project: ").strip().lower()
                if choice in {"c", "code"}:
                    project_type = "code"
                    break
                elif choice in {"t", "text"}:
                    project_type = "text"
                    break
                else:
                    print("Please enter 'c' or 't'.")

        # skip update if the project type is still unknown
        if project_type is None:
            print(f"Detected UNKNOWN project type for: {project_name} (skipping update)")
            continue  # skip database update if project is unknown
        
        if constants.VERBOSE:
            print(f"Detected {project_type.upper()} project: {project_name}")

        # Save detected project type into the database
        conn.execute("""
            UPDATE project_classifications
            SET project_type = ? 
            WHERE user_id = ? AND project_name = ?
        """, (project_type, user_id, project_name))

    conn.commit()

def send_to_analysis(conn, user_id, assignments, current_ext_consent, zip_path):
    """
    Routes each project to the appropriate analysis flow based on its classification and type.
    Collaborative projects trigger contribution analysis.
    Individual projects go directly into standard analysis.

    Notes:
        - Skips projects that do not have a project_type or classification (this should rarely, if ever, happen)
        - Calls downstream analysis functions for each project depending on its type

    Always offer INDIVIDUAL first, then (optionally) COLLABORATIVE.
    Flow:
      1) "Run individual analysis now?"  -> if yes, run all individual projects
      2) "Run collaborative analysis now?" -> if yes, run all collaborative projects
      3) otherwise exit

    After each phase (or set of prompts), ask:
    "Do you want to exit analysis now? (y/n)"
    If user answers 'n'/'no', automatically run the remaining (unrun) phase(s),
    starting with INDIVIDUAL if still pending.
    """

    # Partition projects and attach their detected types
    individual = []
    collaborative = []

    for project_name, classification in assignments.items():
        row = conn.execute(
            """
            SELECT project_type
            FROM project_classifications
            WHERE user_id = ? AND project_name = ?
            """,
            (user_id, project_name),
        ).fetchone()

        if not row or not row[0]:
            print(f"Skipping '{project_name}': project_type missing or NULL.")
            continue

        project_type = row[0]
        if classification == "individual":
            individual.append((project_name, project_type))
        elif classification == "collaborative":
            collaborative.append((project_name, project_type))
        else:
            print(f"Unknown classification '{classification}' for '{project_name}', skipping.")

    if not individual and not collaborative:
        print("No projects to analyze.")
        return

    def run_individual_phase():
        if not individual:
            if constants.VERBOSE:
                print("\n[INDIVIDUAL] No individual projects.")
            return False
        if constants.VERBOSE:
            print("\n[INDIVIDUAL] Running individual projects...")
        for project_name, project_type in individual:
            print(f"  → {project_name} ({project_type})")
            summary = ProjectSummary(
                project_name=project_name,
                project_type=project_type,
                project_mode="individual"
            )
            run_individual_analysis(conn, user_id, project_name, project_type, current_ext_consent, zip_path, summary)
            _load_skills_into_summary(conn, user_id, project_name, summary)
            _load_text_metrics_into_summary(conn, user_id, project_name, summary)
            if project_type == "text":
                _load_text_activity_type_into_summary(conn, user_id, project_name, summary, is_collaborative=False)
            json_data = json.dumps(summary.__dict__, default=str)
            save_project_summary(conn, user_id, project_name, json_data)
        return True

    def run_collaborative_phase():
        if not collaborative:
            print("\n[COLLABORATIVE] No collaborative projects.")
            return False
        if constants.VERBOSE:
            print("\n[COLLABORATIVE] Running collaborative projects...")

        # split: code first, then text
        code_collab = [(n, t) for (n, t) in collaborative if t == "code"]
        text_collab = [(n, t) for (n, t) in collaborative if t == "text"]
        
        # capture manual PROJECT summaries for collab code when LLM is disabled
        manual_project_summaries: dict[str, str] = {}
        if code_collab and current_ext_consent != "accepted":
            for name, _ptype in code_collab:
                manual_project_summaries[name] = prompt_manual_code_project_summary(name)


        # ask once for user descriptions for CODE collab projects (non-LLM path)
        if code_collab:
            # prompt_collab_descriptions expects list[(project_name, something)];
            # it only uses the project_name, so second value can be anything.
            projects_for_desc = [(name, "") for (name, _ptype) in code_collab]
            project_descs = prompt_collab_descriptions(projects_for_desc, current_ext_consent)
            set_manual_descs_store(project_descs)
        else:
            # no code collab → clear any previous state
            set_manual_descs_store({})

                # 1) run all CODE collab
        for project_name, project_type in code_collab:
            print(f"  → {project_name} ({project_type})")
            summary = ProjectSummary(
                project_name=project_name,
                project_type=project_type,
                project_mode="collaborative"
            )

            # For non-LLM collab code, attach the PROJECT summary collected earlier
            if current_ext_consent != "accepted":
                proj_summary = manual_project_summaries.get(project_name)
                if proj_summary:
                    summary.summary_text = proj_summary

            get_individual_contributions(
                conn,
                user_id,
                project_name,
                project_type,
                current_ext_consent,
                zip_path,
                summary,
            )
            _load_skills_into_summary(conn, user_id, project_name, summary)
            _load_text_metrics_into_summary(conn, user_id, project_name, summary)
            if project_type == "text":
                _load_text_activity_type_into_summary(
                    conn,
                    user_id,
                    project_name,
                    summary,
                    is_collaborative=True,
                )
            json_data = json.dumps(summary.__dict__, default=str)
            save_project_summary(conn, user_id, project_name, json_data)


        # print summary right after all CODE collab finished
        if code_collab:
            print_code_portfolio_summary()

        # 2) run all TEXT collab
        for project_name, project_type in text_collab:
            print(f"  → {project_name} ({project_type})")
            summary = ProjectSummary(
                project_name=project_name,
                project_type=project_type,
                project_mode="collaborative"
            )
            get_individual_contributions(conn, user_id, project_name, project_type, current_ext_consent, zip_path, summary)
            _load_skills_into_summary(conn, user_id, project_name, summary)
            _load_text_metrics_into_summary(conn, user_id, project_name, summary)
            if project_type == "text":
                _load_text_activity_type_into_summary(conn, user_id, project_name, summary, is_collaborative=True)
            json_data = json.dumps(summary.__dict__, default=str)
            save_project_summary(conn, user_id, project_name, json_data)

        return True

    # Track pending phases
    pending_individual = bool(individual)
    pending_collab = bool(collaborative)

    # ---- Initial prompts (individual first) ----
    if pending_individual:
        ans_ind = input("\nRun INDIVIDUAL analysis now? (y/n): ").strip().lower()
        if ans_ind in {"", "y", "yes"}:
            if run_individual_phase():
                pending_individual = False

    if pending_collab:
        ans_collab = input("\nRun COLLABORATIVE analysis now? (y/n): ").strip().lower()
        if ans_collab in {"y", "yes"}:
            if run_collaborative_phase():
                pending_collab = False

    # If nothing left, we're done
    if not (pending_individual or pending_collab):
        print("\nAll requested analyses completed.")
        # _run_skill_extraction_for_all(conn, user_id, assignments)
        # commented out skill extraction after all analyses, to avoid double extraction for text files
        return

    # ---- Exit loop: if user chooses not to exit, run whatever is still pending ----
    while pending_individual or pending_collab:
        # Craft hint about what will run next if they choose NOT to exit
        next_to_run = "INDIVIDUAL" if pending_individual else "COLLABORATIVE"
        ans_exit = input(
            f"\nDo you want to exit analysis now? (y/n)\n"
            f"If you answer 'n'/'no', the {next_to_run} analysis will be run next: "
        ).strip().lower()

        if ans_exit in {"y", "yes"}:
            print("Exiting analysis.")
            return

        # User chose to continue: run the next pending phase (individual gets priority)
        if pending_individual:
            if run_individual_phase():
                pending_individual = False
        elif pending_collab:
            if run_collaborative_phase():
                pending_collab = False

    print("\nAll requested analyses completed.")
    # _run_skill_extraction_for_all(conn, user_id, assignments)
    # commented out skill extraction after all analyses, to avoid double extraction for text files



def get_individual_contributions(conn, user_id, project_name, project_type, current_ext_consent, zip_path, summary=None):
    """
    Analyze collaborative projects to get specific user contributions in a collaborative project.
    The process used to get the individual contributions changes depending on the type of project (code/text).
    """
    if constants.VERBOSE:
        print(f"[COLLABORATIVE] Preparing contribution analysis for '{project_name}' ({project_type})")

    if project_type == "text":
        analyze_text_contributions(conn, user_id, project_name, current_ext_consent, summary, zip_path)
    elif project_type == "code":
        analyze_code_contributions(conn, user_id, project_name, current_ext_consent, zip_path, summary)
    else:
        print(f"[COLLABORATIVE] Unknown project type for '{project_name}', skipping.")


def run_individual_analysis(conn, user_id, project_name, project_type, current_ext_consent, zip_path, summary=None):
    """
    Run full analysis on an individual project, depending on project_type.
    """
    
    if project_type == "text":
        run_text_analysis(conn, user_id, project_name, current_ext_consent, zip_path, summary)
    elif project_type == "code":
        run_code_analysis(conn, user_id, project_name, current_ext_consent, zip_path, summary)
    else:
        print(f"[INDIVIDUAL] Unknown project type for '{project_name}', skipping.")


def analyze_text_contributions(conn, user_id, project_name, current_ext_consent, summary, zip_path):
    """
    Analyze collaborative text projects with optional Google Drive connection.
    If Google Drive is skipped or fails → fallback to collaborative manual text flow.
    """

    print(f"[COLLABORATIVE] Preparing TEXT contribution analysis for '{project_name}'")

    # ------------------------------
    # ALWAYS FETCH PARSED FILES HERE
    # ------------------------------
    parsed_files = _fetch_files(conn, user_id, project_name, only_text=True)

    if not parsed_files:
        print(f"[TEXT-COLLAB] No text files found for '{project_name}'. Cannot analyze.")
        return

    while True:
        choice = input(
            "\nThis project is TEXT-based.\n"
            "Do you want to connect Google Drive to analyze revision history? (y/n): "
        ).strip().lower()

        print()

        if choice in {"y", "yes"}:
            use_drive = True
            break
        elif choice in {"n", "no"}:
            use_drive = False
            break
        else:
            print("Please enter 'y' or 'n'.")

    # Manual contribution mode
    if not use_drive:
        if constants.VERBOSE:
            print("[TEXT-COLLAB] Google Drive connection skipped. Using manual contribution mode.")
        analyze_collaborative_text_project(
            conn=conn,
            user_id=user_id,
            project_name=project_name,
            parsed_files=parsed_files,
            zip_path=zip_path,
            external_consent=current_ext_consent,
            summary_obj=summary
        )
        return

    # Drive attempt
    result = setup_text_project_drive_connection(conn, user_id, project_name)

    if not result['success']:
        print("\n[TEXT-COLLAB] Google Drive connection failed → falling back to manual mode.\n")
        analyze_collaborative_text_project(
            conn, user_id, project_name, parsed_files, None, current_ext_consent, summary
        )
        return

    creds = result.get("creds")
    drive_service = result.get("drive_service")
    docs_service = result.get("docs_service")

    if not drive_service or not docs_service:
        print("\n[TEXT-COLLAB] Google Drive connected but incomplete services → fallback to manual.\n")
        analyze_collaborative_text_project(
            conn, user_id, project_name, parsed_files, None, current_ext_consent, summary
        )
        return

    # ------------------------------
    # DRIVE MODE
    # ------------------------------

    user_email = result.get("user_email")

    if constants.VERBOSE:
        print("\n[TEXT-COLLAB] Starting Google Drive revision analysis...")

    drive_result = process_project_files(
        conn=conn,
        creds=creds,
        drive_service=drive_service,
        docs_service=docs_service,
        user_id=user_id,
        project_name=project_name,
        user_email=user_email
    )

    if summary and drive_result:
        summary.contributions["google_drive"] = drive_result

    print("[TEXT-COLLAB] Google Drive contribution analysis complete.")
    
   


def analyze_code_contributions(conn, user_id, project_name, current_ext_consent, zip_path, summary):
    """Collaborative code analysis: Git data + LLM summary."""
    if constants.VERBOSE:
        print(f"[COLLABORATIVE] Preparing contribution analysis for '{project_name}' (code)")

    metrics = analyze_code_project(conn, user_id, project_name, zip_path, summary)

    # activity-type summary for collaborative code
    activity_summary = build_activity_summary(conn, user_id=user_id, project_name=project_name)
    if constants.VERBOSE:
        print("\n[COLLABORATIVE-CODE] Activity type summary:")
    print(format_activity_summary(activity_summary))
    print()
    store_code_activity_metrics(conn, user_id, activity_summary)
    
    if summary:
        summary.contributions["github_contribution_metrics_generated"] = bool(metrics)
        summary.contributions["activity_type"] = activity_summary.per_activity

    # Extract skills for collaborative code projects
    extract_skills(conn, user_id, project_name)

    if current_ext_consent == 'accepted':
        parsed_files = _fetch_files(conn, user_id, project_name, only_text=False)
        if parsed_files:
            print(f"\n[COLLABORATIVE-CODE] Running LLM-based summary for '{project_name}'...")
            llm_results = run_code_llm_analysis(parsed_files, zip_path, project_name)

            if llm_results:
                # update ProjectSummary object as before
                if summary:
                    summary.summary_text = llm_results.get("project_summary")
                    summary.contributions["llm_contribution_summary"] = llm_results.get("contribution_summary")

                # also store in code_collaborative_summary table
                metrics_id = get_metrics_id(conn, user_id, project_name)
                if metrics_id:
                    combined_text = (
                        f"Project Summary:\n{llm_results.get('project_summary','')}\n\n"
                        f"Contribution Summary:\n{llm_results.get('contribution_summary','')}"
                    ).strip()

                    if combined_text:
                        insert_code_collaborative_summary(
                            conn,
                            metrics_id=metrics_id,
                            user_id=user_id,
                            project_name=project_name,
                            summary_type="llm",
                            content=combined_text,
                        )

    else:
        if constants.VERBOSE:
            print(f"[COLLABORATIVE-CODE] Skipping LLM summary (no external consent).")

        # capture manual project summary for collab code
        if summary is not None and not getattr(summary, "summary_text", None):
            summary.summary_text = prompt_manual_code_project_summary(project_name)


def run_text_analysis(conn, user_id, project_name, current_ext_consent, zip_path, summary):
    parsed_files = _fetch_files(conn, user_id, project_name, only_text=True)
    if not parsed_files:
        print(f"[INDIVIDUAL-TEXT] No text files found for '{project_name}'.")
        return
    analyze_files(conn, user_id, project_name, current_ext_consent, parsed_files, zip_path, only_text=True, summary=summary)


def run_code_analysis(conn, user_id, project_name, current_ext_consent, zip_path, summary):
    """Runs full analysis on individual code projects (static metrics + Git + optional LLM)."""
    languages = detect_languages(conn, project_name)
    print(f"Languages detected in {project_name}: {languages}")

    frameworks = detect_frameworks(conn, project_name, user_id, zip_path)
    print(f"Frameworks detected in {project_name}: {frameworks}")

    if summary:
        summary.languages = languages or []
        summary.frameworks = frameworks or []

    parsed_files = _fetch_files(conn, user_id, project_name, only_text=False)
    if not parsed_files:
        print(f"[INDIVIDUAL-CODE] No code files found for '{project_name}'.")
        return

    # --- Run main code + Git analysis ---
    analyze_files(conn, user_id, project_name, current_ext_consent, parsed_files, zip_path, only_text=False)

    # --- Activity-type summary (individual) ---
    activity_summary = build_activity_summary(conn, user_id=user_id, project_name=project_name)
    print()  # spacing
    print(format_activity_summary(activity_summary))
    print()
    store_code_activity_metrics(conn, user_id, activity_summary)

    if summary is not None:
        # store raw counts so you can reuse later in UI / JSON
        summary.metrics["activity_type"] = activity_summary.per_activity

    # Extract skills for code projects
    extract_skills(conn, user_id, project_name)

    # --- Run LLM summary LAST, and only once ---
    if current_ext_consent == "accepted":
        print(f"\n[INDIVIDUAL-CODE] Running LLM-based summary for '{project_name}'...")
        llm_results = run_code_llm_analysis(parsed_files, zip_path, project_name)
        if summary and llm_results:
            summary.summary_text = llm_results.get("project_summary")
            summary.contributions["llm_contribution_summary"] = llm_results.get("contribution_summary")
    else:
        if constants.VERBOSE:
            print(f"[INDIVIDUAL-CODE] Skipping LLM summary (no external consent).")
        
        # capture manual project summary
        if summary is not None and not getattr(summary, "summary_text", None):
            summary.summary_text = prompt_manual_code_project_summary(project_name)
    
        
def analyze_files(conn, user_id, project_name, external_consent, parsed_files, zip_path, only_text, summary=None):
    classification_id = get_classification_id(conn, user_id, project_name)

    if only_text:
        # ------------------------------
        # 1. Detect CSV files
        # ------------------------------
        csv_files = [
            f for f in parsed_files
            if f.get("file_name", "").lower().endswith(".csv")
        ]

        # All files are CSV -> unsupported
        if csv_files and len(csv_files) == len(parsed_files):
            print(f"\n[INDIVIDUAL-TEXT] '{project_name}' contains only CSV files.")
            print("Our system currently only supports CSV files as supporting files of text-based projects.\n")
            return

        # ------------------------------
        # 2. Load CSV metadata (not printed)
        # ------------------------------
        csv_metadata = analyze_all_csv(csv_files, zip_path) if csv_files else None

        # ------------------------------
        # 3. Call NEW TEXT PIPELINE
        # ------------------------------
        text_results = run_text_pipeline(
            parsed_files=parsed_files,
            zip_path=zip_path,
            conn=conn,
            user_id=user_id,
            project_name=project_name,
            consent=external_consent,
            csv_metadata=csv_metadata
        )
        
        # ------------------------------
        # 4. Integrate with ProjectSummary
        # ------------------------------
        if summary and text_results:
            summary.summary_text = text_results.get("project_summary")
            summary.skills = text_results.get("skills", [])


    else:
        # --- Run non-LLM code analysis (static + Git metrics) ---
        classification_id=get_classification_id(conn, user_id, project_name)
        code_analysis_result = run_code_non_llm_analysis(conn, user_id, project_name, zip_path)
        if code_analysis_result and classification_id:
            complexity_data = code_analysis_result.get('complexity_data')
            if complexity_data and complexity_data.get('summary'):
                metrics = extract_complexity_metrics(complexity_data['summary'])
                update = code_complexity_metrics_exists(conn, classification_id)
                if update:
                    update_code_complexity_metrics(conn, classification_id, *metrics)
                else:
                    insert_code_complexity_metrics(conn, classification_id, *metrics)

def _run_skill_extraction_for_all(conn, user_id, assignments):
    for project_name in assignments.keys():
        extract_skills(conn, user_id, project_name)


def _load_skills_into_summary(conn, user_id, project_name, summary):
    """
    Load skills from project_skills table and populate ProjectSummary.
    Stores both skill names (for backward compatibility) and detailed skill data in metrics.
    """
    if not summary:
        return
    
    rows = get_project_skills(conn, user_id, project_name)
    if rows:
        skills = []
        for skill_name, level, score, evidence_json in rows:
            # Only store skill name, level, and score - evidence is in project_skills table
            skills.append({
                "skill_name": skill_name,
                "level": level,
                "score": score
            })
        summary.skills = [s["skill_name"] for s in skills]
        summary.metrics["skills_detailed"] = skills


def _load_text_metrics_into_summary(conn, user_id, project_name, summary):
    """
    Load text metrics from database and populate ProjectSummary.metrics["text"].
    Loads both LLM and non-LLM text metrics.
    """
    if not summary or summary.project_type != "text":
        return
    
    classification_id = get_classification_id(conn, user_id, project_name)
    if not classification_id:
        return
    
    text_metrics = {}
    
    # Load non-LLM metrics
    non_llm = get_text_non_llm_metrics(conn, classification_id)
    if non_llm:
        text_metrics["non_llm"] = {
            "doc_count": non_llm.get("doc_count"),
            "total_words": non_llm.get("total_words"),
            "reading_level_avg": non_llm.get("reading_level_avg"),
            "reading_level_label": non_llm.get("reading_level_label"),
            "keywords": non_llm.get("keywords", [])
        }
    
    if text_metrics:
        summary.metrics["text"] = text_metrics


def _load_text_activity_type_into_summary(conn, user_id, project_name, summary, is_collaborative=False):
    """
    Load text activity type data from database and populate ProjectSummary.
    Transforms text activity data format to match code activity format for consistency.
    
    For individual projects: adds to summary.metrics["activity_type"]
    For collaborative projects: adds to summary.contributions["activity_type"]
    """
    if not summary:
        return
    
    classification_id = get_classification_id(conn, user_id, project_name)
    if not classification_id:
        return
    
    activity_data = get_text_activity_contribution(conn, classification_id)
    if not activity_data:
        return
    
    # Transform text activity data to match code format
    # Code format: {activity_name: {"count": int, "top_file": Optional[str]}}
    activity_classification = activity_data.get('activity_classification', {})
    activity_counts = activity_data.get('summary', {}).get('activity_counts', {})
    
    per_activity = {}
    for activity_name, count in activity_counts.items():
        # Get top file for this activity (first file in classification list, if any)
        top_file = None
        files_list = activity_classification.get(activity_name, [])
        if files_list:
            top_file = files_list[0]  # Use first file as top_file
        
        per_activity[activity_name] = {
            "count": count,
            "top_file": top_file
        }
    
    if per_activity:
        if is_collaborative:
            summary.contributions["activity_type"] = per_activity
        else:
            summary.metrics["activity_type"] = per_activity
