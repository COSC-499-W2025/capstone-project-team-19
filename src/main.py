from parsing import parse_zip_file
from db import connect, init_schema
from consent import CONSENT_TEXT, get_user_consent, record_consent

def main():
    print("Welcome aboard! Let’s turn your work into cool insights.")

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
    parse_zip_file(zip_path)

def get_zip_path_from_user():
    path = input("Please enter the path to your ZIP file: ").strip()
    return path

if __name__ == "__main__":
    main()
    prompt_and_store()
