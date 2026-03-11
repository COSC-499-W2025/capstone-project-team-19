import sqlite3

from src.db import init_schema, get_or_create_user
from src.db.user_experience import (
    list_user_experience_entries,
    add_user_experience_entry,
    delete_user_experience_entry,
)


def make_conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn


def test_list_user_experience_entries_empty_for_new_user():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    entries = list_user_experience_entries(conn, user_id)

    assert entries == []


def test_user_experience_round_trip():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    entry_id = add_user_experience_entry(
        conn,
        user_id,
        role="Data Science Intern",
        company="PETRONAS",
        date_text="May 2025 - Aug 2025",
        description="Built analytics workflows and dashboards.",
    )

    entries = list_user_experience_entries(conn, user_id)

    assert len(entries) == 1
    assert entries[0]["entry_id"] == entry_id
    assert entries[0]["role"] == "Data Science Intern"
    assert entries[0]["company"] == "PETRONAS"

    assert delete_user_experience_entry(conn, user_id, entry_id) is True
    assert list_user_experience_entries(conn, user_id) == []