"""
Collaborative analysis module.
Handles project-type detection (code vs text) and routes collaborative projects
to the appropriate individual-contribution analyzers.

Individual projects - sent directly to analysis
Collaborative projects - processed to extract individual user contributions
"""

import sqlite3
from alt_analyze import alternative_analysis
from llm_analyze import run_llm_analysis
from helpers import _fetch_files

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
    """

    # Collect projects + types
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
            print(f"Skipping '{project_name}': project_type missing.")
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

    # Helper runners
    def run_individual_phase():
        if not individual:
            print("\n[INDIVIDUAL] No individual projects.")
            return
        print("\n[INDIVIDUAL] Running individual projects...")
        for project_name, project_type in individual:
            print(f"  → {project_name} ({project_type})")
            run_individual_analysis(conn, user_id, project_name, project_type, current_ext_consent, zip_path)

    def run_collaborative_phase():
        if not collaborative:
            print("\n[COLLABORATIVE] No collaborative projects.")
            return
        print("\n[COLLABORATIVE] Running collaborative projects...")
        for project_name, project_type in collaborative:
            print(f"  → {project_name} ({project_type})")
            get_individual_contributions(conn, user_id, project_name, project_type, current_ext_consent)

    # Prompt 1: INDIVIDUAL first (default yes)
    ans_ind = input("\nDo you want to run the INDIVIDUAL analysis now? (Y/n): ").strip().lower()
    if ans_ind in {"", "y", "yes"}:
        run_individual_phase()

    # Prompt 2: COLLABORATIVE next (default no if user typed explicit 'n' on first, still ask)
    ans_collab = input("\nDo you want to run the COLLABORATIVE analysis now? (y/N): ").strip().lower()
    if ans_collab in {"y", "yes"}:
        run_collaborative_phase()
    else:
        print("Exiting without running collaborative analysis.")


def get_individual_contributions(conn, user_id, project_name, project_type, current_ext_consent):
    """
    Analyze collaborative projects to get specific user contributions in a collaborative project.
    The process used to get the individual contributions changes depending on the type of project (code/text).
    """

    print(f"[COLLABORATIVE] Preparing contribution analysis for '{project_name}' ({project_type})")

    if project_type == "text":
        analyze_text_contributions(conn, user_id, project_name, current_ext_consent)
    elif project_type == "code":
        analyze_code_contributions(conn, user_id, project_name, current_ext_consent)
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
    Placeholder for future collaborative text contribution analysis.

    This function should figure out which parts of a textual collaborative project were done by the user.
    Various analysis techniques will probably need to be used, and if necessary the user can be prompted to specify which parts they did.
    """
    pass


def analyze_code_contributions(conn, user_id, project_name, current_ext_consent):
    """
    Placeholder for future collaborative code contribution analysis.

    This function should figure out which parts of a coding collaborative project were done by the user.
    Check for a .git folder (which should have commits), or connect to git using OAuth, etc. 
    User can also be prompted, or key words can be used.
    """
    pass


def run_text_analysis(conn, user_id, project_name, current_ext_consent, zip_path):
    """
    Placeholder for individual text project analysis.
    Individual TEXT project → pull files from DB and analyze.

    """

    parsed_files = _fetch_files(conn, user_id, project_name, only_text=True)
    if not parsed_files:
        print(f"[INDIVIDUAL-TEXT] No text files found for '{project_name}'.")
        return
    analyze_files(conn, user_id, current_ext_consent, parsed_files, zip_path)

    pass


def run_code_analysis(conn, user_id, project_name, current_ext_consent):
    """
    Placeholder for individual code project analysis.
    """
    pass



# From LLMs and alternative analysis

def analyze_files(conn, user_id, external_consent, parsed_files, zip_path):
    if external_consent=='accepted':
        run_llm_analysis(parsed_files, zip_path)
    else:
        alternative_analysis(parsed_files, zip_path)
  