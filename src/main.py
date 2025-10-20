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

    # --- Returning user with full configuration ---
    elif prev_consent and prev_ext:
        print(f"\nWelcome back, {username}!")
        print(f"Your previous configuration: user consent = {prev_consent}, external service consent = {prev_ext}.")
        reuse = input("Would you like to continue with this configuration? (y/n): ").strip().lower()

        if reuse == "y":
            reused = True
            record_consent(conn, prev_consent, user_id=user_id)
            record_external_consent(conn, prev_ext, user_id=user_id)
        else:
            print("\nAlright, let’s review your consents again.\n")
            print(CONSENT_TEXT)
            status = get_user_consent()
            record_consent(conn, status, user_id=user_id)
            ext_status = get_external_consent()
            record_external_consent(conn, ext_status, user_id=user_id)

    # --- Brand new user ---
    else:
        print(f"\nNice to meet you, {username}!\n")
        print(CONSENT_TEXT)
        status = get_user_consent()
        record_consent(conn, status, user_id=user_id)
        ext_status = get_external_consent()
        record_external_consent(conn, ext_status, user_id=user_id)

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

    prompt_for_project_classifications(conn, user_id, zip_path, result)


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
