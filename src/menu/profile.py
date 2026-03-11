"""
src/menu/profile.py

Standalone profile menu/handler.
Profile editing stays separate from resume editing because the frontend
will eventually expose profile and resume on different pages.
"""

from __future__ import annotations

from src.db.user_profile import get_user_profile, upsert_user_profile
from src.db.user_education import (
    list_user_education_entries,
    add_user_education_entry,
    delete_user_education_entry,
)
from src.db.user_experience import (
    list_user_experience_entries,
    add_user_experience_entry,
    delete_user_experience_entry,
)


def _display_value(value: str | None) -> str:
    return value if value else "(not set)"


def _prompt_field(label: str, current: str | None) -> str | None:
    suffix = f" [{current}]" if current else ""
    raw = input(f"{label}{suffix}: ").strip()

    if raw == "":
        return current
    if raw == "-":
        return None
    return raw


def _edit_basic_profile(conn, user_id: int, username: str) -> None:
    current = get_user_profile(conn, user_id)
    display_name = current.get("full_name") or username

    print(f"\nProfile settings for {display_name}:")
    print(f"Full name: {_display_value(current.get('full_name'))}")
    print(f"Email: {_display_value(current.get('email'))}")
    print(f"Phone: {_display_value(current.get('phone'))}")
    print(f"LinkedIn: {_display_value(current.get('linkedin'))}")
    print(f"GitHub: {_display_value(current.get('github'))}")
    print(f"Location: {_display_value(current.get('location'))}")
    print(f"Profile paragraph: {_display_value(current.get('profile_text'))}")

    print("\nPress Enter to keep the current value.")
    print("Type '-' to clear/delete a value.\n")

    full_name = _prompt_field("Full name", current.get("full_name"))
    email = _prompt_field("Email", current.get("email"))
    phone = _prompt_field("Phone", current.get("phone"))
    linkedin = _prompt_field("LinkedIn URL", current.get("linkedin"))
    github = _prompt_field("GitHub URL", current.get("github"))
    location = _prompt_field("Location", current.get("location"))
    profile_text = _prompt_field("Profile paragraph", current.get("profile_text"))

    upsert_user_profile(
        conn,
        user_id,
        email=email,
        full_name=full_name,
        phone=phone,
        linkedin=linkedin,
        github=github,
        location=location,
        profile_text=profile_text,
    )

    print("\nProfile saved.")


def _list_education_entries(conn, user_id: int) -> list[dict]:
    entries = list_user_education_entries(conn, user_id)

    if not entries:
        print("\nNo education or certificate entries saved yet.")
        return []

    print("\nEducation & Certificates:")
    for idx, entry in enumerate(entries, start=1):
        entry_type = "Education" if entry["entry_type"] == "education" else "Certificate"
        title = entry["title"]
        organization = entry.get("organization") or ""
        date_text = entry.get("date_text") or ""
        details = " | ".join(part for part in [organization, date_text] if part)
        if details:
            print(f"{idx}. [{entry_type}] {title} — {details}")
        else:
            print(f"{idx}. [{entry_type}] {title}")

        if entry.get("description"):
            print(f"   {entry['description']}")

    return entries


def _add_education_entry(conn, user_id: int) -> None:
    print("\nAdd entry type:")
    print("1. Education")
    print("2. Certificate")
    entry_type_choice = input("Select an option (1-2): ").strip()

    if entry_type_choice == "1":
        entry_type = "education"
    elif entry_type_choice == "2":
        entry_type = "certificate"
    else:
        print("Invalid selection.")
        return

    title = input("Title (required): ").strip()
    if not title:
        print("Title is required.")
        return

    organization = input("School / issuer / organization (optional): ").strip() or None
    date_text = input("Date text (optional, e.g. '2022 - 2026' or 'May 2025'): ").strip() or None
    description = input("Description (optional): ").strip() or None

    entry_id = add_user_education_entry(
        conn,
        user_id,
        entry_type=entry_type,
        title=title,
        organization=organization,
        date_text=date_text,
        description=description,
    )

    print(f"\nSaved entry #{entry_id}.")


def _delete_education_entry(conn, user_id: int) -> None:
    entries = _list_education_entries(conn, user_id)
    if not entries:
        return

    choice = input("Select an entry to delete (number) or press Enter to cancel: ").strip()
    if not choice:
        print("Cancelled.")
        return
    if not choice.isdigit():
        print("Invalid selection.")
        return

    idx = int(choice)
    if idx < 1 or idx > len(entries):
        print("Invalid selection.")
        return

    entry = entries[idx - 1]
    confirm = input(f"Delete '{entry['title']}'? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    deleted = delete_user_education_entry(conn, user_id, entry["entry_id"])
    if deleted:
        print("Entry deleted.")
    else:
        print("Unable to delete the selected entry.")


def _list_experience_entries(conn, user_id: int) -> list[dict]:
    entries = list_user_experience_entries(conn, user_id)

    if not entries:
        print("\nNo experience entries saved yet.")
        return []

    print("\nExperience:")
    for idx, entry in enumerate(entries, start=1):
        role = entry["role"]
        company = entry.get("company") or ""
        date_text = entry.get("date_text") or ""
        details = " | ".join(part for part in [company, date_text] if part)
        if details:
            print(f"{idx}. {role} — {details}")
        else:
            print(f"{idx}. {role}")

        if entry.get("description"):
            print(f"   {entry['description']}")

    return entries


def _add_experience_entry(conn, user_id: int) -> None:
    role = input("Role (required): ").strip()
    if not role:
        print("Role is required.")
        return

    company = input("Company (optional): ").strip() or None
    date_text = input("Date text (optional, e.g. 'May 2024 - Aug 2024'): ").strip() or None
    description = input("Job description (optional): ").strip() or None

    entry_id = add_user_experience_entry(
        conn,
        user_id,
        role=role,
        company=company,
        date_text=date_text,
        description=description,
    )

    print(f"\nSaved experience entry #{entry_id}.")


def _delete_experience_entry(conn, user_id: int) -> None:
    entries = _list_experience_entries(conn, user_id)
    if not entries:
        return

    choice = input("Select an experience entry to delete (number) or press Enter to cancel: ").strip()
    if not choice:
        print("Cancelled.")
        return
    if not choice.isdigit():
        print("Invalid selection.")
        return

    idx = int(choice)
    if idx < 1 or idx > len(entries):
        print("Invalid selection.")
        return

    entry = entries[idx - 1]
    confirm = input(f"Delete '{entry['role']}'? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    deleted = delete_user_experience_entry(conn, user_id, entry["entry_id"])
    if deleted:
        print("Entry deleted.")
    else:
        print("Unable to delete the selected entry.")


def edit_user_profile(conn, user_id: int, username: str) -> None:
    while True:
        print(f"\nProfile options for {username}:")
        print("1. Edit basic profile")
        print("2. View education / certificate entries")
        print("3. Add education / certificate entry")
        print("4. Delete education / certificate entry")
        print("5. View experience entries")
        print("6. Add experience entry")
        print("7. Delete experience entry")
        print("8. Back to main menu")

        choice = input("Select an option (1-8): ").strip()

        if choice == "1":
            _edit_basic_profile(conn, user_id, username)
        elif choice == "2":
            _list_education_entries(conn, user_id)
        elif choice == "3":
            _add_education_entry(conn, user_id)
        elif choice == "4":
            _delete_education_entry(conn, user_id)
        elif choice == "5":
            _list_experience_entries(conn, user_id)
        elif choice == "6":
            _add_experience_entry(conn, user_id)
        elif choice == "7":
            _delete_experience_entry(conn, user_id)
        elif choice == "8":
            return
        else:
            print("Invalid choice.")