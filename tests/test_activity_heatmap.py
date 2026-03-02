import sqlite3
from pathlib import Path

import numpy as np
import pytest

from src.analysis.visualizations.activity_heatmap import (
    build_project_activity_heatmap_matrix,
    render_heatmap_png,
)

# -------- fixtures --------

@pytest.fixture()
def conn():
    """
    Fresh in-memory DB per test.
    Loads the real schema from tables.sql.
    Nothing persists after the test.
    """
    c = sqlite3.connect(":memory:")

    schema_path = Path(__file__).resolve().parents[1] / "src" / "db" / "schema" / "tables.sql"
    c.executescript(schema_path.read_text(encoding="utf-8"))

    yield c
    c.close()


# -------- helpers (NO nested functions) --------

def index_of_label(labels: list[str], target: str) -> int:
    return labels.index(target)


def _insert_user(c: sqlite3.Connection, username: str = "testuser") -> int:
    c.execute(
        "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
        (username, "test@example.com", "x"),
    )
    (user_id,) = c.execute("SELECT last_insert_rowid()").fetchone()
    return int(user_id)


def _insert_project(c: sqlite3.Connection, user_id: int, name: str, project_type: str) -> int:
    c.execute(
        "INSERT INTO projects (user_id, display_name, classification, project_type) VALUES (?, ?, ?, ?)",
        (user_id, name, "individual", project_type),
    )
    (pk,) = c.execute("SELECT last_insert_rowid()").fetchone()
    return int(pk)


def _insert_version(c: sqlite3.Connection, project_key: int, fp: str) -> int:
    c.execute(
        "INSERT INTO project_versions (project_key, fingerprint_strict, created_at) VALUES (?, ?, ?)",
        (project_key, fp, "2026-02-20 00:00:00"),
    )
    (vk,) = c.execute("SELECT last_insert_rowid()").fetchone()
    return int(vk)


def _add_file(c: sqlite3.Connection, version_key: int, relpath: str, file_hash: str) -> None:
    c.execute(
        "INSERT INTO version_files (version_key, relpath, file_hash) VALUES (?, ?, ?)",
        (version_key, relpath, file_hash),
    )


# -------- tests --------

def test_heatmap_code_positive_diff_and_png(conn):
    """
    Code project happy path (diff, %):
    - v2 touched: src/app.py + src/utils.py => 100% Feature Coding
    - v3 touched: tests/test_app.py + docs/changelog.py => 50% Testing, 50% Documentation
    Also checks PNG renders.
    """
    user_id = _insert_user(conn, "code_user")
    project_name = "HeatmapTestCode"
    pk = _insert_project(conn, user_id, project_name, "code")

    v1 = _insert_version(conn, pk, "fp_v1")
    v2 = _insert_version(conn, pk, "fp_v2")
    v3 = _insert_version(conn, pk, "fp_v3")

    # v1 baseline
    _add_file(conn, v1, f"{project_name}/src/app.py", "A1")
    _add_file(conn, v1, f"{project_name}/tests/test_app.py", "T1")
    _add_file(conn, v1, f"{project_name}/docs/guide.py", "D1")  # docs/ => Documentation

    # v2: modify app, add utils
    _add_file(conn, v2, f"{project_name}/src/app.py", "A2")      # modified
    _add_file(conn, v2, f"{project_name}/src/utils.py", "U1")    # added
    _add_file(conn, v2, f"{project_name}/tests/test_app.py", "T1")
    _add_file(conn, v2, f"{project_name}/docs/guide.py", "D1")

    # v3: modify tests, add docs/changelog
    _add_file(conn, v3, f"{project_name}/src/app.py", "A2")
    _add_file(conn, v3, f"{project_name}/src/utils.py", "U1")
    _add_file(conn, v3, f"{project_name}/tests/test_app.py", "T2")          # modified
    _add_file(conn, v3, f"{project_name}/docs/guide.py", "D1")
    _add_file(conn, v3, f"{project_name}/docs/changelog.py", "D2")          # added

    mat, y_labels, x_labels, title = build_project_activity_heatmap_matrix(
        conn, user_id, project_name, mode="diff", normalize=True
    )

    assert x_labels == ["v1", "v2", "v3"]
    assert mat.shape[1] == 3

    i_feature = index_of_label(y_labels, "Feature Coding")
    i_testing = index_of_label(y_labels, "Testing")
    i_docs = index_of_label(y_labels, "Documentation")

    # v2 column (index 1)
    assert np.isclose(mat[i_feature, 1], 100.0, atol=1e-6)
    assert np.isclose(mat[i_testing, 1], 0.0, atol=1e-6)
    assert np.isclose(mat[i_docs, 1], 0.0, atol=1e-6)

    # v3 column (index 2)
    assert np.isclose(mat[i_testing, 2], 50.0, atol=1e-6)
    assert np.isclose(mat[i_docs, 2], 50.0, atol=1e-6)
    assert np.isclose(mat[i_feature, 2], 0.0, atol=1e-6)

    png = render_heatmap_png(mat, y_labels, x_labels, title)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 2000


def test_heatmap_text_positive_diff(conn):
    """
    Text project happy path (diff, %):
    - v2 touched: draft_v2.txt => 100% Revision
    - v3 touched: final_submission.txt => 100% Final
    """
    user_id = _insert_user(conn, "text_user")
    project_name = "HeatmapTestText"
    pk = _insert_project(conn, user_id, project_name, "text")

    v1 = _insert_version(conn, pk, "fp_v1")
    v2 = _insert_version(conn, pk, "fp_v2")
    v3 = _insert_version(conn, pk, "fp_v3")

    # v1 baseline
    _add_file(conn, v1, f"{project_name}/outline_plan.txt", "P1")     # Planning
    _add_file(conn, v1, f"{project_name}/research_notes.txt", "R1")   # Research
    _add_file(conn, v1, f"{project_name}/draft_v1.txt", "D1")         # Drafting

    # v2: add revision file only
    _add_file(conn, v2, f"{project_name}/outline_plan.txt", "P1")
    _add_file(conn, v2, f"{project_name}/research_notes.txt", "R1")
    _add_file(conn, v2, f"{project_name}/draft_v1.txt", "D1")
    _add_file(conn, v2, f"{project_name}/draft_v2.txt", "DV2")        # Revision

    # v3: add final file only
    _add_file(conn, v3, f"{project_name}/outline_plan.txt", "P1")
    _add_file(conn, v3, f"{project_name}/research_notes.txt", "R1")
    _add_file(conn, v3, f"{project_name}/draft_v1.txt", "D1")
    _add_file(conn, v3, f"{project_name}/draft_v2.txt", "DV2")
    _add_file(conn, v3, f"{project_name}/final_submission.txt", "F1") # Final

    mat, y_labels, x_labels, _title = build_project_activity_heatmap_matrix(
        conn, user_id, project_name, mode="diff", normalize=True
    )

    assert x_labels == ["v1", "v2", "v3"]

    i_revision = index_of_label(y_labels, "Revision")
    i_final = index_of_label(y_labels, "Final")

    assert np.isclose(mat[i_revision, 1], 100.0, atol=1e-6)  # v2
    assert np.isclose(mat[i_final, 2], 100.0, atol=1e-6)     # v3


def test_heatmap_negative_no_versions_raises(conn):
    user_id = _insert_user(conn, "novers_user")
    project_name = "HeatmapNoVersions"
    _insert_project(conn, user_id, project_name, "code")

    with pytest.raises(ValueError, match=r"no versions"):
        build_project_activity_heatmap_matrix(conn, user_id, project_name, mode="diff", normalize=True)