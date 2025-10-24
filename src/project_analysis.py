"""
Collaborative analysis module.
Handles project-type detection (code vs text) and routes collaborative projects
to the appropriate individual-contribution analyzers.

Individual projects - sent directly to analysis
Collaborative projects - processed to extract individual user contributions
"""

import sqlite3
from alt_analyze import calculate_document_metrics, calculate_project_metrics
from llm_analyze import run_llm_analysis

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

def send_to_analysis(conn, user_id, assignments, current_ext_consent):
    """
    Routes each project to the appropriate analysis flow based on its classification and type.
    Collaborative projects trigger contribution analysis.
    Individual projects go directly into standard analysis.

    Notes:
        - Skips projects that do not have a project_type or classification (this should rarely, if ever, happen)
        - Calls downstream analysis functions for each project depending on its type
    """

    for project_name, classification in assignments.items():
        types = conn.execute("""
            SELECT project_type
            FROM project_classifications
            WHERE user_id = ? AND project_name = ?
        """, (user_id, project_name)).fetchone()


        if not types:
            print(f"Skipping {project_name}: project_type not found.")
            continue

        project_type = types[0]

        if not project_type:
            print(f"Skipping '{project_name}': project_type is NULL.")
            continue

        if classification == "collaborative":
            print(f"Running collaborative flow for {project_name} ({project_type})")
            get_individual_contributions(conn, user_id, project_name, project_type, current_ext_consent)

        elif classification == "individual": # individual
            print(f"Running individual flow for {project_name} ({project_type})")
            run_individual_analysis(conn, user_id, project_name, project_type, current_ext_consent)

        else:
            print(f"Unknown classification '{classification} for project '{project_name}'. Skipping.")


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


def run_individual_analysis(conn, user_id, project_name, project_type, current_ext_consent):
    """
    Run full analysis on an individual project, depending on project_type.
    """
    
    if project_type == "text":
        run_text_analysis(conn, user_id, project_name, current_ext_consent)
    elif project_type == "code":
        run_code_analysis(conn, user_id, project_name, current_ext_consent)
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


def run_text_analysis(conn, user_id, project_name, current_ext_consent):
    """
    Placeholder for individual text project analysis.

    """
    pass


def run_code_analysis(conn, user_id, project_name, current_ext_consent):
    """
    Placeholder for individual code project analysis.
    """
    pass



# From LLMs and alternative analysis

def analyze_files(conn, user_id, external_consent, parsed_files, zip_path):
    if external_consent=='accepted':
        llm_analysis(parsed_files, zip_path)
    else:
        alternative_analysis(parsed_files, zip_path)
        
def llm_analysis(parsed_files, zip_path):
    run_llm_analysis(parsed_files, zip_path)

def alternative_analysis(parsed_files, zip_path):
    if not isinstance(parsed_files, list):
        return

    text_files=[f for f in parsed_files if f.get('file_type')=='text']

    if not text_files:
        print("No text files found to analyze.")
        return

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ZIP_DATA_DIR = os.path.join(REPO_ROOT, "zip_data")
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(ZIP_DATA_DIR, zip_name)

    print(f"\n{'='*80}")
    print(f"Analyzing {len(text_files)} file(s)...")
    print(f"{'='*80}\n")

    # Calculate metrics for each document
    all_document_metrics = []
    for file_info in text_files:
        file_path = os.path.join(base_path, file_info['file_path'])
        filename = file_info['file_name']

        print(f"Processing: {filename}")
        doc_metrics = calculate_document_metrics(file_path)

        if doc_metrics.get('processed'):
            # Add filename for reference
            doc_metrics['filename'] = filename
            all_document_metrics.append(doc_metrics)
            display_individual_results(filename, doc_metrics)
        else:
            print(f"Failed to process: {doc_metrics.get('error', 'Unknown error')}\n")

    # Display project-wide summary
    if all_document_metrics:
        print(f"\n{'='*80}")
        print("PROJECT SUMMARY - Aggregated Metrics Across All Files")
        print(f"{'='*80}\n")
        display_project_summary(calculate_project_metrics(all_document_metrics))
    else:
        print("\nNo files were successfully processed.")

def display_individual_results(filename: str, doc_metrics: dict):
    """Display analysis results for an individual file."""
    linguistic = doc_metrics['linguistic_metrics']
    topics = doc_metrics['topics']
    keywords = doc_metrics['keywords']

    print(f"  Linguistic & Readability:")
    print(f"    Word Count: {linguistic['word_count']}, Sentences: {linguistic['sentence_count']}")
    print(f"    Reading Level: {linguistic['reading_level']} (Grade {linguistic['flesch_kincaid_grade']})")
    print(f"    Lexical Diversity: {linguistic['lexical_diversity']}")

    print(f"  Top Keywords: ", end="")
    if keywords:
        keyword_str = ', '.join([word for word, _score in keywords[:5]])
        print(keyword_str)
    else:
        print("None")

    print(f"  Topics: ", end="")
    if topics:
        topic_labels = [topic['label'] for topic in topics[:2]]
        print(', '.join(topic_labels))
    else:
        print("None")
    print()

def display_project_summary(project_metrics: dict):
    """Display aggregated project-wide metrics."""
    if not project_metrics or 'error' in project_metrics:
        print("Unable to generate project summary.")
        return

    summary = project_metrics['summary']
    print(f"Total Documents Analyzed:     {summary['total_documents']}")
    print(f"Total Words:                  {summary['total_words']:,}")
    print(f"Average Reading Level:        {summary['reading_level_label']} (Grade {summary['reading_level_average']})")

    print(f"\nTop Keywords Across All Documents:")
    print("-" * 50)
    keywords = project_metrics.get('keywords', [])
    if keywords:
        for i, kw in enumerate(keywords[:15], 1):
            print(f"{i:2d}. {kw['word']:30s} (score: {kw['score']:.3f})")
    else:
        print("No keywords found")

    print(f"\n{'='*80}\n")

