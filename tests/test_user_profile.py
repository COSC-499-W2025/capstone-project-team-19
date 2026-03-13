import sqlite3

from src.db import init_schema, get_or_create_user
from src.db.user_profile import (
    get_user_profile,
    upsert_user_profile,
    get_contact_parts,
    get_visible_profile_text,
    get_resume_name,
)


def make_conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn


def test_get_user_profile_defaults_for_new_user():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    profile = get_user_profile(conn, user_id)

    assert profile["user_id"] == user_id
    assert profile["email"] is None
    assert profile["full_name"] is None
    assert profile["phone"] is None
    assert profile["linkedin"] is None
    assert profile["github"] is None
    assert profile["location"] is None
    assert profile["profile_text"] is None


def test_upsert_user_profile_inserts_profile_and_updates_users_email():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    upsert_user_profile(
        conn,
        user_id,
        email="alice@example.com",
        full_name="Alice Tan",
        phone="1234567890",
        linkedin="https://linkedin.com/in/alice",
        github="https://github.com/alice",
        location="Kelowna, BC",
        profile_text="Software and data student building practical tools.",
    )

    profile = get_user_profile(conn, user_id)
    assert profile["email"] == "alice@example.com"
    assert profile["full_name"] == "Alice Tan"
    assert profile["phone"] == "1234567890"
    assert profile["linkedin"] == "https://linkedin.com/in/alice"
    assert profile["github"] == "https://github.com/alice"
    assert profile["location"] == "Kelowna, BC"
    assert profile["profile_text"] == "Software and data student building practical tools."

    row = conn.execute(
        "SELECT email FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    assert row[0] == "alice@example.com"


def test_upsert_user_profile_updates_existing_values():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    upsert_user_profile(
        conn,
        user_id,
        email="alice@example.com",
        full_name="Alice Tan",
        phone="123",
        linkedin="https://linkedin.com/in/alice",
        github="https://github.com/alice",
        location="Kelowna",
        profile_text="First version.",
    )

    upsert_user_profile(
        conn,
        user_id,
        email="newalice@example.com",
        full_name="Alice Wong",
        phone="999",
        linkedin="https://linkedin.com/in/newalice",
        github=None,
        location="Vancouver",
        profile_text="Updated paragraph.",
    )

    profile = get_user_profile(conn, user_id)
    assert profile["email"] == "newalice@example.com"
    assert profile["full_name"] == "Alice Wong"
    assert profile["phone"] == "999"
    assert profile["linkedin"] == "https://linkedin.com/in/newalice"
    assert profile["github"] is None
    assert profile["location"] == "Vancouver"
    assert profile["profile_text"] == "Updated paragraph."


def test_upsert_user_profile_can_clear_all_fields():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    upsert_user_profile(
        conn,
        user_id,
        email="alice@example.com",
        full_name="Alice Tan",
        phone="123",
        linkedin="https://linkedin.com/in/alice",
        github="https://github.com/alice",
        location="Kelowna",
        profile_text="Hello",
    )

    upsert_user_profile(
        conn,
        user_id,
        email=None,
        full_name=None,
        phone=None,
        linkedin=None,
        github=None,
        location=None,
        profile_text=None,
    )

    profile = get_user_profile(conn, user_id)
    assert profile["email"] is None
    assert profile["full_name"] is None
    assert profile["phone"] is None
    assert profile["linkedin"] is None
    assert profile["github"] is None
    assert profile["location"] is None
    assert profile["profile_text"] is None


def test_upsert_user_profile_normalizes_blank_strings_to_none():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    upsert_user_profile(
        conn,
        user_id,
        email="   ",
        full_name="   ",
        phone="",
        linkedin="   ",
        github="",
        location="   ",
        profile_text="",
    )

    profile = get_user_profile(conn, user_id)
    assert profile["email"] is None
    assert profile["full_name"] is None
    assert profile["phone"] is None
    assert profile["linkedin"] is None
    assert profile["github"] is None
    assert profile["location"] is None
    assert profile["profile_text"] is None


def test_get_contact_parts_returns_only_cleaned_values():
    profile = {
        "email": " alice@example.com ",
        "phone": None,
        "linkedin": " https://linkedin.com/in/alice ",
        "github": "   ",
        "location": " Kelowna, BC ",
    }

    parts = get_contact_parts(profile)

    assert parts == {
        "phone": None,
        "email": "alice@example.com",
        "linkedin": "https://linkedin.com/in/alice",
        "github": None,
        "location": "Kelowna, BC",
    }


def test_get_visible_profile_text_returns_none_when_empty():
    assert get_visible_profile_text({"profile_text": None}) is None
    assert get_visible_profile_text({"profile_text": ""}) is None
    assert get_visible_profile_text({"profile_text": "   "}) is None
    assert get_visible_profile_text({"profile_text": "Hello"}) == "Hello"


def test_get_resume_name_prefers_full_name_and_falls_back_to_username():
    assert get_resume_name({"full_name": "Alice Tan"}, "alice123") == "Alice Tan"
    assert get_resume_name({"full_name": ""}, "alice123") == "alice123"
    assert get_resume_name({"full_name": None}, "alice123") == "alice123"