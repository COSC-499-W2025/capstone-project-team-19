"""
src/menu/profile.py
Menu for editing user profile information used in resume export.
"""

from __future__ import annotations

from src.db.user_profile import get_user_profile, upsert_user_profile


def _display_value(value: str | None) -> str:
    return value if value else "(not set)"


def _prompt_field(label: str, current: str | None) -> str | None:
    """
    Enter -> keep existing value
    '-'   -> clear/delete value
    text  -> update value
    """
    suffix = f" [{current}]" if current else ""
    raw = input(f"{label}{suffix}: ").strip()

    if raw == "":
        return current
    if raw == "-":
        return None
    return raw


def edit_user_profile(conn, user_id: int, username: str) -> None:
    """
    Edit standalone user profile fields used by resume export.
    """
    current = get_user_profile(conn, user_id)

    print(f"\nProfile settings for {username}:")
    print(f"Email: {_display_value(current.get('email'))}")
    print(f"Phone: {_display_value(current.get('phone'))}")
    print(f"LinkedIn: {_display_value(current.get('linkedin'))}")
    print(f"Location: {_display_value(current.get('location'))}")
    print(f"Profile paragraph: {_display_value(current.get('profile_text'))}")

    print("\nPress Enter to keep the current value.")
    print("Type '-' to clear/delete a value.\n")

    email = _prompt_field("Email", current.get("email"))
    phone = _prompt_field("Phone", current.get("phone"))
    linkedin = _prompt_field("LinkedIn", current.get("linkedin"))
    location = _prompt_field("Location", current.get("location"))
    profile_text = _prompt_field("Profile paragraph", current.get("profile_text"))

    upsert_user_profile(
        conn,
        user_id,
        email=email,
        phone=phone,
        linkedin=linkedin,
        location=location,
        profile_text=profile_text,
    )

    print("\nProfile saved.")