from parsing import parse_zip_file
from db import connect, init_schema
from consent import CONSENT_TEXT, get_user_consent, record_consent

def main():
    print("Welcome aboard! Let’s turn your work into cool insights.")

    # Should be called in main() not __main__ beacsue __main__ does not run during tests
    prompt_and_store()

def prompt_and_store():
    """Show consent text, get input, and store in DB."""
    conn = connect()
    init_schema(conn)

    print(CONSENT_TEXT)
    status = get_user_consent()
    record_consent(conn, status)
    print()
    print(f"Consent '{status}' recorded successfully.")

    zip_path = get_zip_path_from_user()
    print(f"Recieved path: {zip_path}")
    result = parse_zip_file(zip_path)
    if not result:
        print("No valid files were processed. Check logs for unsupported or corrupted files.")

def get_zip_path_from_user():
    path = input("Please enter the path to your ZIP file: ").strip()
    return path

if __name__ == "__main__":
    main()
