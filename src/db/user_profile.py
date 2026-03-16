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
            p.full_name,
            p.phone,
            p.linkedin,
            p.github,
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
            "full_name": None,
            "phone": None,
            "linkedin": None,
            "github": None,
            "location": None,
            "profile_text": None,
        }

    return {
        "user_id": row[0],
        "email": row[1],
        "full_name": row[2],
        "phone": row[3],
        "linkedin": row[4],
        "github": row[5],
        "location": row[6],
        "profile_text": row[7],
    }


def upsert_user_profile(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    email: Optional[str],
    full_name: Optional[str],
    phone: Optional[str],
    linkedin: Optional[str],
    github: Optional[str],
    location: Optional[str],
    profile_text: Optional[str],
) -> None:
    """
    Update users.email plus the per-user profile row.
    Blank strings are normalized to NULL.
    """
    clean_email = _clean_optional_text(email)
    clean_full_name = _clean_optional_text(full_name)
    clean_phone = _clean_optional_text(phone)
    clean_linkedin = _clean_optional_text(linkedin)
    clean_github = _clean_optional_text(github)
    clean_location = _clean_optional_text(location)
    clean_profile_text = _clean_optional_text(profile_text)

    # Enforce a maximum length for the profile paragraph so it fits well on a resume.
    # This is a backend guard; callers should provide shorter text rather than expecting truncation.
    if clean_profile_text is not None:
        MAX_PROFILE_CHARS = 900
        if len(clean_profile_text) > MAX_PROFILE_CHARS:
            raise ValueError(
                f"profile_text must be at most {MAX_PROFILE_CHARS} characters."
            )

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
        (user_id, full_name, phone, linkedin, github, location, profile_text, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET
            full_name = excluded.full_name,
            phone = excluded.phone,
            linkedin = excluded.linkedin,
            github = excluded.github,
            location = excluded.location,
            profile_text = excluded.profile_text,
            updated_at = datetime('now')
        """,
        (
            user_id,
            clean_full_name,
            clean_phone,
            clean_linkedin,
            clean_github,
            clean_location,
            clean_profile_text,
        ),
    )

    conn.commit()


def get_visible_profile_text(profile: Dict[str, Any]) -> Optional[str]:
    return _clean_optional_text(profile.get("profile_text"))


def get_contact_parts(profile: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Returns cleaned contact parts for rendering.
    """
    return {
        "phone": _clean_optional_text(profile.get("phone")),
        "email": _clean_optional_text(profile.get("email")),
        "linkedin": _clean_optional_text(profile.get("linkedin")),
        "github": _clean_optional_text(profile.get("github")),
        "location": _clean_optional_text(profile.get("location")),
    }


def get_resume_name(profile: Dict[str, Any], username: str) -> str:
    """
    Return the display name for resume export.
    Falls back to username if full_name is not set.
    """
    return _clean_optional_text(profile.get("full_name")) or username