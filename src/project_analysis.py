"""
Collaborative analysis module.
Handles project-type detection (code vs text) and routes collaborative projects
to the appropriate individual-contribution analyzers.

Individual projects - sent directly to analysis
Collaborative projects - processed to extract individual user contributions
"""
from src.language_detector import detect_languages
from src.framework_detector import detect_frameworks

import sqlite3
from src.alt_analyze import alternative_analysis
from src.text_llm_analyze import run_text_llm_analysis
from src.code_llm_analyze import run_code_llm_analysis
from src.code_non_llm_analysis import run_code_non_llm_analysis
from src.helpers import _fetch_files
from src.code_collaborative_analysis import analyze_code_project, print_code_portfolio_summary, set_manual_descs_store, prompt_collab_descriptions

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
            print("\n[INDIVIDUAL] No individual projects.")
            return False
        print("\n[INDIVIDUAL] Running individual projects...")
        for project_name, project_type in individual:
            print(f"  → {project_name} ({project_type})")
            run_individual_analysis(conn, user_id, project_name, project_type, current_ext_consent, zip_path)
        return True

    def run_collaborative_phase():
        if not collaborative:
            print("\n[COLLABORATIVE] No collaborative projects.")
            return False

        print("\n[COLLABORATIVE] Running collaborative projects...")

        # split: code first, then text
        code_collab = [(n, t) for (n, t) in collaborative if t == "code"]
        text_collab = [(n, t) for (n, t) in collaborative if t == "text"]

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
            get_individual_contributions(conn, user_id, project_name, project_type, current_ext_consent, zip_path)

        # print summary right after all CODE collab finished
        if code_collab:
            print_code_portfolio_summary()

        # 2) run all TEXT collab
        for project_name, project_type in text_collab:
            print(f"  → {project_name} ({project_type})")
            get_individual_contributions(conn, user_id, project_name, project_type, current_ext_consent, zip_path)

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



def get_individual_contributions(conn, user_id, project_name, project_type, current_ext_consent, zip_path):
    """
    Analyze collaborative projects to get specific user contributions in a collaborative project.
    The process used to get the individual contributions changes depending on the type of project (code/text).
    """

    print(f"[COLLABORATIVE] Preparing contribution analysis for '{project_name}' ({project_type})")

    if project_type == "text":
        analyze_text_contributions(conn, user_id, project_name, current_ext_consent)
    elif project_type == "code":
        analyze_code_contributions(conn, user_id, project_name, current_ext_consent, zip_path)
    else:
        print(f"[COLLABORATIVE] Unknown project type for '{project_name}', skipping.")


def run_individual_analysis(conn, user_id, project_name, project_type, current_ext_consent, zip_path):
    """
    Run full analysis on an individual project, depending on project_type.
    """
    
    if project_type == "text":
        run_text_analysis(conn, user_id, project_name, current_ext_consent, zip_path)
    elif project_type == "code":
        run_code_analysis(conn, user_id, project_name, current_ext_consent, zip_path)
    else:
        print(f"[INDIVIDUAL] Unknown project type for '{project_name}', skipping.")


def analyze_text_contributions(conn, user_id, project_name, current_ext_consent):
    """
    Analyze collaborative text projects by connecting to Google Drive.
    
    This function orchestrates the Google Drive setup and file linking process.
    The actual contribution analysis will be done in a later phase.
    Adding option for skipping connecting to Google Drive needs to be added later.
    """
    from src.google_drive_auth.text_project_setup import setup_text_project_drive_connection
    
    # Set up Google Drive connection and link files
    result = setup_text_project_drive_connection(conn, user_id, project_name)
    
    if not result['success']:
        # Setup failed - error messages already printed by setup function
        return
    
    # TODO: Future - perform actual contribution analysis here
    # For now, we just set up the connection and file mappings
    print("Note: Actual contribution analysis will be performed in a future update.")


def analyze_code_contributions(conn, user_id, project_name, current_ext_consent, zip_path):
    """Collaborative code analysis: Git data + LLM summary."""
    print(f"[COLLABORATIVE] Preparing contribution analysis for '{project_name}' (code)")

    analyze_code_project(conn, user_id, project_name, zip_path)
    

    if current_ext_consent == 'accepted':
        parsed_files = _fetch_files(conn, user_id, project_name, only_text=False)
        if parsed_files:
            print(f"\n[COLLABORATIVE-CODE] Running LLM-based summary for '{project_name}'...")
            run_code_llm_analysis(parsed_files, zip_path, project_name)
        else:
            print(f"[COLLABORATIVE-CODE] No code files found for '{project_name}'.")


def run_text_analysis(conn, user_id, project_name, current_ext_consent, zip_path):
    parsed_files = _fetch_files(conn, user_id, project_name, only_text=True)
    if not parsed_files:
        print(f"[INDIVIDUAL-TEXT] No text files found for '{project_name}'.")
        return
    analyze_files(conn, user_id, project_name, current_ext_consent, parsed_files, zip_path, only_text=True)


def run_code_analysis(conn, user_id, project_name, current_ext_consent, zip_path):
    """Runs full analysis on individual code projects (static metrics + Git + optional LLM)."""
    languages = detect_languages(conn, project_name)
    print(f"Languages detected in {project_name}: {languages}")

    frameworks = detect_frameworks(conn, project_name, user_id, zip_path)
    print(f"Frameworks detected in {project_name}: {frameworks}")

    parsed_files = _fetch_files(conn, user_id, project_name, only_text=False)
    if not parsed_files:
        print(f"[INDIVIDUAL-CODE] No code files found for '{project_name}'.")
        return

    # --- Run main code + Git analysis ---
    analyze_files(conn, user_id, project_name, current_ext_consent, parsed_files, zip_path, only_text=False)

    # --- Run LLM summary LAST, and only once ---
    if current_ext_consent == "accepted":
        print(f"\n[INDIVIDUAL-CODE] Running LLM-based summary for '{project_name}'...")
        run_code_llm_analysis(parsed_files, zip_path, project_name)
    else:
        print(f"[INDIVIDUAL-CODE] Skipping LLM summary (no external consent).")
    
        
# From LLMs and alternative analysis
def analyze_files(conn, user_id, project_name, external_consent, parsed_files, zip_path, only_text):
    if only_text:
        if external_consent=='accepted':
            run_text_llm_analysis(parsed_files, zip_path)
        else:
            alternative_analysis(parsed_files, zip_path, project_name)

    elif not only_text:
        # Run non-LLM code analysis (static + Git metrics)
        run_code_non_llm_analysis(conn, user_id, project_name, zip_path)
