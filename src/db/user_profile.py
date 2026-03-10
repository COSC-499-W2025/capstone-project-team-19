"""
src/db/user_profile.py

Helpers for storing and retrieving standalone user profile information.
Email is stored on users.email.
Other profile fields live in user_profiles.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, Optional


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def get_user_profile(conn: sqlite3.Connection, user_id: int) -> Dict[str, Any]:
    """
    Return the current profile data for a user.
    Email comes from users.email.
    """
    row = conn.execute(
        """
        SELECT
            u.user_id,
            u.email,
            p.phone,
            p.linkedin,
            p.location,
            p.profile_text
        FROM users u
        LEFT JOIN user_profiles p
            ON u.user_id = p.user_id
        WHERE u.user_id = ?
        """,
        (user_id,),
    ).fetchone()

    if not row:
        return {
            "user_id": user_id,
            "email": None,
            "phone": None,
            "linkedin": None,
            "location": None,
            "profile_text": None,
        }

    return {
        "user_id": row[0],
        "email": row[1],
        "phone": row[2],
        "linkedin": row[3],
        "location": row[4],
        "profile_text": row[5],
    }


def upsert_user_profile(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    email: Optional[str],
    phone: Optional[str],
    linkedin: Optional[str],
    location: Optional[str],
    profile_text: Optional[str],
) -> None:
    """
    Update users.email plus the per-user profile row.
    Blank strings are normalized to NULL.
    """
    clean_email = _clean_optional_text(email)
    clean_phone = _clean_optional_text(phone)
    clean_linkedin = _clean_optional_text(linkedin)
    clean_location = _clean_optional_text(location)
    clean_profile_text = _clean_optional_text(profile_text)

    conn.execute(
        """
        UPDATE users
        SET email = ?
        WHERE user_id = ?
        """,
        (clean_email, user_id),
    )

    conn.execute(
        """
        INSERT INTO user_profiles
        (user_id, phone, linkedin, location, profile_text, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET
            phone = excluded.phone,
            linkedin = excluded.linkedin,
            location = excluded.location,
            profile_text = excluded.profile_text,
            updated_at = datetime('now')
        """,
        (user_id, clean_phone, clean_linkedin, clean_location, clean_profile_text),
    )

    conn.commit()


def build_contact_line(profile: Dict[str, Any]) -> Optional[str]:
    """
    Build a single contact line from the populated fields only.
    Returns None if all contact fields are empty.
    """
    parts = []
    for key in ("phone", "email", "linkedin", "location"):
        value = _clean_optional_text(profile.get(key))
        if value:
            parts.append(value)

    if not parts:
        return None

    return " | ".join(parts)


def get_visible_profile_text(profile: Dict[str, Any]) -> Optional[str]:
    """
    Return the profile paragraph if populated, otherwise None.
    """
    return _clean_optional_text(profile.get("profile_text"))