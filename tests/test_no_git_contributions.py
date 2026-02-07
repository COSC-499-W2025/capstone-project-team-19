import os

from src.analysis.code_collaborative.no_git_contributions import (
    rank_files_by_description,
    store_contributions_without_git,
)
from src.db import init_schema
from src.db.projects import get_project_key


def test_rank_files_by_description_uses_name_and_path(tmp_path):
    files = [
        {"file_name": "auth_service.py", "file_path": "proj/auth_service.py"},
        {"file_name": "utils.js", "file_path": "proj/frontend/utils.js"},
        {"file_name": "README.md", "file_path": "proj/README.md"},
    ]

    ranked = rank_files_by_description("auth API login", files, base_dir=None, top_n=3)

    assert ranked[0] == "proj/auth_service.py"
    assert ranked == ["proj/auth_service.py"]


def test_rank_files_by_description_uses_content_slice(tmp_path):
    base_dir = tmp_path / "zip_data"
    base_dir.mkdir()
    file_rel = "proj/data_pipeline.py"
    file_abs = base_dir / file_rel
    file_abs.parent.mkdir(parents=True, exist_ok=True)
    file_abs.write_text("def process_data():\n    # handles ETL pipeline\n    pass\n")

    files = [{"file_name": "data_pipeline.py", "file_path": file_rel}]

    ranked = rank_files_by_description("ETL pipeline work", files, base_dir=str(base_dir), top_n=3)
    assert ranked == [file_rel]


def test_store_contributions_without_git_falls_back_to_all(tmp_sqlite_conn):
    init_schema(tmp_sqlite_conn)
    # Insert minimal files rows
    tmp_sqlite_conn.execute(
        """
        INSERT INTO files (user_id, file_name, file_type, file_path, project_name)
        VALUES (1, 'a.py', 'code', 'proj/a.py', 'demo'),
               (1, 'b.py', 'code', 'proj/b.py', 'demo')
        """
    )
    tmp_sqlite_conn.commit()

    # Empty desc => no keyword hits => fallback to all code files
    store_contributions_without_git(tmp_sqlite_conn, user_id=1, project_name="demo", desc="", debug=False)

    pk = get_project_key(tmp_sqlite_conn, 1, "demo")
    assert pk is not None
    rows = tmp_sqlite_conn.execute(
        "SELECT file_path FROM user_code_contributions WHERE user_id=? AND project_key=? ORDER BY file_path",
        (1, pk),
    ).fetchall()
    assert [r[0] for r in rows] == ["proj/a.py", "proj/b.py"]


def test_rank_files_path_hit_only(tmp_path):
    files = [
        {"file_name": "index.js", "file_path": "proj/auth/index.js"},
        {"file_name": "main.py", "file_path": "proj/core/main.py"},
    ]
    ranked = rank_files_by_description("auth routing", files, base_dir=None, top_n=2)
    assert ranked == ["proj/auth/index.js"]


def test_rank_files_content_beyond_limit(tmp_path):
    base_dir = tmp_path / "zip_data"
    base_dir.mkdir()
    file_rel = "proj/long_file.py"
    file_abs = base_dir / file_rel
    file_abs.parent.mkdir(parents=True, exist_ok=True)

    # Put the keyword only after 10KB so the 10KB slice should miss it
    prefix = "x" * 10000
    file_abs.write_text(prefix + " auth_token_handler")

    files = [{"file_name": "long_file.py", "file_path": file_rel}]

    ranked = rank_files_by_description("auth token", files, base_dir=str(base_dir), top_n=3)
    assert ranked == []  # content slice should not reach the keyword
