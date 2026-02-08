import os
from src.utils.parsing import parse_zip_file, analyze_project_layout, ZIP_DATA_DIR
from src.utils.deduplication.integration import run_deduplication_for_projects, run_deduplication_for_projects_detailed
from src.db import (
    connect,
    init_schema,
    get_user_by_username,
    get_or_create_user,
    get_latest_consent,
    get_latest_external_consent,
    record_project_classifications,
    store_parsed_files,
)
from src.menu import (
    show_start_menu,
    view_old_project_summaries,
    view_resume_items,
    view_portfolio_items,
    view_project_feedback,
    delete_old_insights,
    project_list,
    view_chronological_skills,
    view_ranked_projects,
    manage_project_thumbnails,
    edit_project_dates_menu,
    manage_skill_highlighting,
)
from src.consent.consent import CONSENT_TEXT, get_user_consent, record_consent
from src.consent.external_consent import get_external_consent, record_external_consent
from src.project_analysis import detect_project_type, send_to_analysis
from src.utils.helpers import cleanup_extracted_zip
try:
    from src import constants
except ModuleNotFoundError:
    import constants

def main():
    print("Welcome aboard! Let's turn your work into cool insights.")

    # Should be called in main() not __main__ beacsue __main__ does not run during tests
    processed_zip_path = prompt_and_store()
    if processed_zip_path:
        cleanup_extracted_zip(processed_zip_path)


def prompt_and_store():
    """Main flow: identify user, check prior consents, reuse or re-prompt."""
    conn = connect()
    init_schema(conn)

    # defensive, but not technically necessary
    consent_status = None
    external_consent_status = None

    username = input("Enter your username: ").strip()
    existing_user = get_user_by_username(conn, username)

    if existing_user is None:
        # user does not exist
        user_id = get_or_create_user(conn, username)
        is_new_user = True
    else:
        user_id = existing_user[0]
        is_new_user = False

    while True:
        # Show main menu after username
        menu_choice = show_start_menu(username)

        # Handle menu choices
        if menu_choice == 2:
            view_old_project_summaries(conn, user_id, username)
        elif menu_choice == 3:
            view_resume_items(conn, user_id, username)
        elif menu_choice == 4:
            view_portfolio_items(conn, user_id, username)
        elif menu_choice == 5:
            view_project_feedback(conn, user_id, username)
        elif menu_choice == 6:
            delete_old_insights(conn, user_id, username)
        elif menu_choice == 7:
            view_ranked_projects(conn, user_id, username)
        elif menu_choice == 8:
            view_chronological_skills(conn, user_id, username)
        elif menu_choice == 9:
            edit_project_dates_menu(conn, user_id, username)
        elif menu_choice == 10:
            manage_project_thumbnails(conn, user_id, username)
        elif menu_choice == 11:
            project_list(conn, user_id, username)
        elif menu_choice == 12:
            manage_skill_highlighting(conn, user_id, username)
        elif menu_choice == 13:
            print("\nThank you for using the system. Goodbye!")
            return None
        elif menu_choice == 1:
            break

    stored_user_consent = get_latest_consent(conn, user_id)
    stored_external_consent = get_latest_external_consent(conn, user_id)

    if is_new_user:
        stored_user_consent = None
        stored_external_consent = None
        consent_status, external_consent_status = create_new_user(conn, username, user_id)

    else: 
        if stored_user_consent == "rejected":
            print(f"\nHeads up, {username}: you previously declined consent, so we can't reuse that configuration.")
            stored_user_consent = None
            stored_external_consent = None

        # Edge case 1: user exists but no consents yet
        if not stored_user_consent and not stored_external_consent:
            consent_status, external_consent_status = handle_existing_user_without_consents(conn, username, user_id)

        # Edge case 2: partial configuration 
        # The user will never make it this far if they decline user consent no matter what, only need to consider a declined external consent
        elif (stored_user_consent and not stored_external_consent):
            consent_status, external_consent_status = resolve_missing_external_consent(conn, username, user_id, stored_user_consent, stored_external_consent)

        # Returning user with full configuration
        elif stored_user_consent and stored_external_consent:
            consent_status, external_consent_status = confirm_or_update_consent(conn, username, user_id, stored_user_consent, stored_external_consent)        

    if consent_status is None:
        return None

    print("\nConsent recorded. Proceeding to file selection…\n")

    # Ask whether analysis output should be verbose
    while True:
        choice = input(
            "Verbose mode prints extra debug information and execution traces.\n"
            "If you prefer a cleaner view, normal mode shows only what you need.\n"
            "Enable verbose mode? (y/n): "
        ).strip().lower()

        if choice in ("y", "n"):
            print()
            constants.VERBOSE = (choice == "y")
            break

        print("Invalid choice – please enter y or n.")
        print()

    # Continue to file selection
    processed_zip_path = run_zip_ingestion_flow(conn, user_id, external_consent_status)
    return processed_zip_path
       

def create_new_user(conn, username, user_id):
    print(f"\nNice to meet you, {username}!\n")
    print(CONSENT_TEXT)
    
    consent_status = collect_user_consent(conn, user_id)
    if abort_on_declined_consent(consent_status):
        return None, None

    external_consent_status = get_external_consent()
    record_external_consent(conn, external_consent_status, user_id=user_id)

    return consent_status, external_consent_status

def handle_existing_user_without_consents(conn, username, user_id):
    print(f"\nWelcome back, {username}!")
    print("Looks like you've been here before, but we don't have your consent record yet.")
    print("Let's complete your setup.\n")
    print(CONSENT_TEXT)

    consent_status = collect_user_consent(conn, user_id)
    if abort_on_declined_consent(consent_status):
        return None, None
    
    external_consent_status = get_external_consent()
    record_external_consent(conn, external_consent_status, user_id=user_id)
    
    return consent_status, external_consent_status

def resolve_missing_external_consent(conn, username, user_id, consent_status, external_consent_status):
    print(f"\nWelcome back, {username}!")
    print("We found a partial configuration:")
    print(f"  • User consent = {consent_status or 'none'}")
    print(f"  • External service consent = {external_consent_status or 'none'}")
    print("Let's complete your setup.\n")

    external_consent_status = collect_external_consent(conn, user_id)

    return consent_status, external_consent_status

def confirm_or_update_consent(conn, username, user_id, consent_status, external_consent_status):
    print(f"\nWelcome back, {username}!")
    print(f"Your previous configuration: user consent = {consent_status}, external service consent = {external_consent_status}.")
    reuse = input("Would you like to continue with this configuration? (y/n): ").strip().lower()

    if reuse == "y":
        print("\nContinuing with your saved configuration…\n")
        record_consent(conn, consent_status, user_id=user_id)
        record_external_consent(conn, external_consent_status, user_id=user_id)
    else:
        print("\nAlright, let's review your consents again.\n")
        print(CONSENT_TEXT)

        consent_status = collect_user_consent(conn, user_id)
        
        if abort_on_declined_consent(consent_status):
            return None, None

        external_consent_status = get_external_consent()
        record_external_consent(conn, external_consent_status, user_id=user_id)

    return consent_status, external_consent_status

def abort_on_declined_consent(consent_status):
    if consent_status != "accepted":
        print("\nConsent declined. Exiting.")
        return True # tells caller to stop
    
    return False

def collect_user_consent(conn, user_id):
    consent_status = get_user_consent()
    record_consent(conn, consent_status, user_id)
    return consent_status

def collect_external_consent(conn, user_id):
    external_consent_status = get_external_consent()
    record_external_consent(conn, external_consent_status, user_id)
    return external_consent_status

def run_zip_ingestion_flow(conn, user_id, external_consent_status):
    unchecked_zip = True
    assignments = None
    processed_zip_path = None
    version_keys: dict[str, int] = {}

    while unchecked_zip:
        zip_path = get_zip_path_from_user()
        if not zip_path:
            print("No path entered. Exiting file selection.")
            break
        
        if constants.VERBOSE:
            print(f"\nReceived path: {zip_path}")

        result = parse_zip_file(zip_path, user_id=user_id, conn=conn, persist_to_db=False)
        if not result:
            print("\nNo valid files were processed. Check logs for unsupported or corrupted files.")
            continue
        processed_zip_path = zip_path

        # Run deduplication check
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        target_dir = os.path.join(ZIP_DATA_DIR, zip_name)
        layout = analyze_project_layout(result)
        skipped_projects, decisions = run_deduplication_for_projects_detailed(conn, user_id, target_dir, layout)
        # Filter out skipped projects from result
        if skipped_projects:
            result = [f for f in result if f.get("project_name") not in skipped_projects]

        # Apply dedup renames + attach version_key for storage
        name_map: dict[str, str] = {}
        version_keys = {}
        for orig_name, decision in (decisions or {}).items():
            final = decision.get("final_name")
            vk = decision.get("version_key")
            if final:
                name_map[orig_name] = final
                if isinstance(vk, int):
                    version_keys[final] = vk

        for f in result:
            orig = f.get("project_name")
            if orig in name_map:
                f["project_name"] = name_map[orig]
                f["version_key"] = version_keys.get(name_map[orig])

        # Persist files once (after dedup tagging)
        store_parsed_files(conn, result, user_id)

        assignments = prompt_for_project_classifications(conn, user_id, zip_path, result, project_name_map=name_map)
        try:
            detect_project_type(conn, user_id, assignments)
            # if zip file is valid (has folders)
            unchecked_zip = False
        except AttributeError:
            # if zip file is invalid
            print("\nInvalid ZIP file structure. Please make sure your ZIP file contains project folders where individual files are stored.")
            processed_zip_path = None
            assignments = None
            continue
        
    if assignments and processed_zip_path:
        send_to_analysis(
            conn,
            user_id,
            assignments,
            external_consent_status,
            processed_zip_path,
            version_keys=version_keys,
        )  # takes projects and sends them into the analysis flow
    else:
        if assignments:
            print("No valid project analysis to send.")
    return processed_zip_path
    

def get_zip_path_from_user():
    path = input("Please enter the path to your ZIP file: ").strip()
    return path


def prompt_for_project_classifications(conn, user_id: int, zip_path: str, files_info: list[dict], project_name_map: dict[str, str] | None = None) -> dict:
    """Ask the user to classify each detected project as individual or collaborative."""
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    layout = analyze_project_layout(files_info)
    root_name = layout["root_name"]
    auto_assignments = layout["auto_assignments"]
    pending_projects = layout["pending_projects"]
    stray_locations = layout["stray_locations"]

    if not auto_assignments and not pending_projects:
        print("No project folders detected to classify.")
        return {}

    
    if root_name:
        if constants.VERBOSE:
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
            print("\nLet's classify each remaining project individually.")
            for name in pending_projects:
                assignments[name] = ask_project_classification(name)

    # If dedup decided a folder name maps to an existing project name, persist using the final name.
    if project_name_map:
        assignments = {project_name_map.get(k, k): v for k, v in assignments.items()}

    record_project_classifications(conn, user_id, zip_path, zip_name, assignments)

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

