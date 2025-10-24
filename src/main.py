import os

from parsing import parse_zip_file, analyze_project_layout
from db import (
    connect,
    init_schema,
    get_or_create_user,
    get_latest_consent,
    get_latest_external_consent,
    record_project_classifications,
)
from consent import CONSENT_TEXT, get_user_consent, record_consent
from external_consent import get_external_consent, record_external_consent
from alt_analyze import calculate_document_metrics, calculate_project_metrics
from llm_analyze import run_llm_analysis
from project_analysis import detect_project_type, send_to_analysis
import os

def main():
    print("Welcome aboard! Let’s turn your work into cool insights.")

    # Should be called in main() not __main__ beacsue __main__ does not run during tests
    prompt_and_store()

def prompt_and_store():
    """Main flow: identify user, check prior consents, reuse or re-prompt."""
    conn = connect()
    init_schema(conn)

    username = input("Enter your username: ").strip()
    user_id = get_or_create_user(conn, username)

    prev_consent = get_latest_consent(conn, user_id)
    prev_ext = get_latest_external_consent(conn, user_id)

    reused = False  # track reuse
    current_ext_consent=None 

    # Edge case 1: user exists but no consents yet
    if not prev_consent and not prev_ext:
        print(f"\nWelcome back, {username}!")
        print("Looks like you’ve been here before, but we don’t have your consent record yet.")
        print("Let’s complete your setup.\n")
        print(CONSENT_TEXT)
        status = get_user_consent()
        record_consent(conn, status, user_id=user_id)
        ext_status = get_external_consent()
        record_external_consent(conn, ext_status, user_id=user_id)
        current_ext_consent=ext_status

    # Edge case 2: partial configuration (only one consent found)
    elif (prev_consent and not prev_ext) or (not prev_consent and prev_ext):
        print(f"\nWelcome back, {username}!")
        print("We found a partial configuration:")
        print(f"  • User consent = {prev_consent or 'none'}")
        print(f"  • External service consent = {prev_ext or 'none'}")
        print("Let’s complete your setup.\n")

        # Only ask for the missing one
        if not prev_consent:
            print(CONSENT_TEXT)
            status = get_user_consent()
            record_consent(conn, status, user_id=user_id)
        # Although this is not necessary because you have to answer user consent before going to external consent
        if not prev_ext:
            ext_status = get_external_consent()
            record_external_consent(conn, ext_status, user_id=user_id)
            current_ext_consent=ext_status
        else:
            current_ext_consent=prev_ext

    # --- Returning user with full configuration ---
    elif prev_consent and prev_ext:
        print(f"\nWelcome back, {username}!")
        print(f"Your previous configuration: user consent = {prev_consent}, external service consent = {prev_ext}.")
        reuse = input("Would you like to continue with this configuration? (y/n): ").strip().lower()

        if reuse == "y":
            reused = True
            record_consent(conn, prev_consent, user_id=user_id)
            record_external_consent(conn, prev_ext, user_id=user_id)
            current_ext_consent=prev_ext
        else:
            print("\nAlright, let’s review your consents again.\n")
            print(CONSENT_TEXT)
            status = get_user_consent()
            record_consent(conn, status, user_id=user_id)
            ext_status = get_external_consent()
            record_external_consent(conn, ext_status, user_id=user_id)
            current_ext_consent = ext_status

    # --- Brand new user ---
    else:
        print(f"\nNice to meet you, {username}!\n")
        print(CONSENT_TEXT)
        status = get_user_consent()
        record_consent(conn, status, user_id=user_id)
        ext_status = get_external_consent()
        record_external_consent(conn, ext_status, user_id=user_id)
        current_ext_consent=ext_status

    # Only show message if not reusing previous config
    if not reused:
        print("\nConsent recorded. Proceeding to file selection…\n")
    else:
        print("\nContinuing with your saved configuration…\n")

    # Continue to file selection
    zip_path = get_zip_path_from_user()
    print(f"Recieved path: {zip_path}")
    result = parse_zip_file(zip_path, user_id=user_id, conn=conn)
    if not result:
        print("No valid files were processed. Check logs for unsupported or corrupted files.")
        return

    assignments = prompt_for_project_classifications(conn, user_id, zip_path, result)
    detect_project_type(conn, user_id, assignments)
    analyze_files(conn, user_id, current_ext_consent, result, zip_path)
    send_to_analysis(conn, user_id, assignments, current_ext_consent)

    
    
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


def get_zip_path_from_user():
    path = input("Please enter the path to your ZIP file: ").strip()
    return path


def prompt_for_project_classifications(conn, user_id: int, zip_path: str, files_info: list[dict]) -> None:
    """Ask the user to classify each detected project as individual or collaborative."""
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    layout = analyze_project_layout(files_info)
    root_name = layout["root_name"]
    auto_assignments = layout["auto_assignments"]
    pending_projects = layout["pending_projects"]
    stray_locations = layout["stray_locations"]

    if not auto_assignments and not pending_projects:
        print("No project folders detected to classify.")
        return

    if root_name:
        print(f"\nUsing '{root_name}' as the root folder for this upload.")

    if auto_assignments:
        print("\nAutomatically classified projects based on folder placement:")
        for name, label in sorted(auto_assignments.items()):
            print(f"  • {name}: {label}")

    assignments = dict(auto_assignments)

    if pending_projects:
        print("\nProjects still needing classification:")
        for name in pending_projects:
            print(f"  • {name}")

        scope = ask_overall_scope()
        if scope in {"individual", "collaborative"}:
            for name in pending_projects:
                assignments[name] = scope
        else:
            print("\nLet’s classify each remaining project individually.")
            for name in pending_projects:
                assignments[name] = ask_project_classification(name)

    record_project_classifications(conn, user_id, zip_name, assignments)

    print("\nProject classifications saved:")
    for name, classification in sorted(assignments.items()):
        print(f"  • {name}: {classification}")

    if stray_locations:
        print("\nSkipped items (no project folder detected):")
        for name in stray_locations:
            print(f"  • {name}")

    return assignments


def ask_overall_scope() -> str:
    """Prompt for a bulk classification decision for the remaining projects."""
    prompt = (
        "\nFor the projects listed above, are they all individual, all collaborative, or a mix?\n"
        "Type 'i' for individual, 'c' for collaborative, or 'm' for mixed: "
    )
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"i", "individual"}:
            return "individual"
        if answer in {"c", "collaborative"}:
            return "collaborative"
        if answer in {"m", "mixed", "b", "both"}:
            return "mixed"
        print("Please respond with 'i' (individual), 'c' (collaborative), or 'm' (mixed).")


def ask_project_classification(project_name: str) -> str:
    """Prompt the user to classify a single project as individual or collaborative."""
    prompt = f"  - Is '{project_name}' individual or collaborative? (i/c): "
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"i", "individual"}:
            return "individual"
        if answer in {"c", "collaborative"}:
            return "collaborative"
        print("Please respond with 'i' for individual or 'c' for collaborative.")

if __name__ == "__main__":
    main()
