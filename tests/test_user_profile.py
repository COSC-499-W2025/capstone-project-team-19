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


def test_upsert_user_profile_round_trip():
    """
    Covers insert + update + clear in one test.
    """
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    # insert
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

    # update
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

    # clear
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


def test_profile_helpers():
    parts = get_contact_parts(
        {
            "email": " alice@example.com ",
            "phone": None,
            "linkedin": " https://linkedin.com/in/alice ",
            "github": "   ",
            "location": " Kelowna, BC ",
        }
    )

    assert parts == {
        "phone": None,
        "email": "alice@example.com",
        "linkedin": "https://linkedin.com/in/alice",
        "github": None,
        "location": "Kelowna, BC",
    }

    assert get_visible_profile_text({"profile_text": None}) is None
    assert get_visible_profile_text({"profile_text": ""}) is None
    assert get_visible_profile_text({"profile_text": "   "}) is None
    assert get_visible_profile_text({"profile_text": "Hello"}) == "Hello"

    assert get_resume_name({"full_name": "Alice Tan"}, "alice123") == "Alice Tan"
    assert get_resume_name({"full_name": ""}, "alice123") == "alice123"
    assert get_resume_name({"full_name": None}, "alice123") == "alice123"