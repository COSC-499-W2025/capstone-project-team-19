import sqlite3

from src.db import init_schema, get_or_create_user
from src.db.user_education import (
    list_user_education_entries,
    add_user_education_entry,
    delete_user_education_entry,
)


def make_conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn


def test_list_user_education_entries_empty_for_new_user():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    entries = list_user_education_entries(conn, user_id)

    assert entries == []


def test_add_user_education_entry_saves_education_entry():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    entry_id = add_user_education_entry(
        conn,
        user_id,
        entry_type="education",
        title="BSc in Computer Science",
        organization="UBCO",
        date_text="2022 - 2026",
        description="Major in data science.",
    )

    entries = list_user_education_entries(conn, user_id)

    assert len(entries) == 1
    assert entries[0]["entry_id"] == entry_id
    assert entries[0]["entry_type"] == "education"
    assert entries[0]["title"] == "BSc in Computer Science"
    assert entries[0]["organization"] == "UBCO"
    assert entries[0]["date_text"] == "2022 - 2026"
    assert entries[0]["description"] == "Major in data science."
    assert entries[0]["display_order"] == 1


def test_add_user_education_entry_saves_certificate_and_increments_order():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    add_user_education_entry(
        conn,
        user_id,
        entry_type="education",
        title="BSc in Computer Science",
        organization="UBCO",
        date_text="2022 - 2026",
        description="Major in data science.",
    )

    cert_id = add_user_education_entry(
        conn,
        user_id,
        entry_type="certificate",
        title="AWS Cloud Practitioner",
        organization="Amazon Web Services",
        date_text="2025",
        description="Foundational cloud certification.",
    )

    entries = list_user_education_entries(conn, user_id)

    assert len(entries) == 2
    assert entries[1]["entry_id"] == cert_id
    assert entries[1]["entry_type"] == "certificate"
    assert entries[1]["title"] == "AWS Cloud Practitioner"
    assert entries[1]["organization"] == "Amazon Web Services"
    assert entries[1]["date_text"] == "2025"
    assert entries[1]["description"] == "Foundational cloud certification."
    assert entries[1]["display_order"] == 2


def test_add_user_education_entry_rejects_invalid_type():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    try:
        add_user_education_entry(
            conn,
            user_id,
            entry_type="award",
            title="Some Award",
        )
        assert False, "Expected ValueError for invalid entry type"
    except ValueError as exc:
        assert "entry_type" in str(exc)


def test_add_user_education_entry_requires_title():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    try:
        add_user_education_entry(
            conn,
            user_id,
            entry_type="education",
            title="",
        )
        assert False, "Expected ValueError for missing title"
    except ValueError as exc:
        assert "title" in str(exc).lower()


def test_delete_user_education_entry_removes_entry():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    entry_id = add_user_education_entry(
        conn,
        user_id,
        entry_type="certificate",
        title="AWS Cloud Practitioner",
        organization="Amazon Web Services",
        date_text="2025",
        description="Foundational cloud certification.",
    )

    deleted = delete_user_education_entry(conn, user_id, entry_id)
    entries = list_user_education_entries(conn, user_id)

    assert deleted is True
    assert entries == []


def test_delete_user_education_entry_returns_false_for_missing_entry():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    deleted = delete_user_education_entry(conn, user_id, 9999)

    assert deleted is False