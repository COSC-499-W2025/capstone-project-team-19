"""Tests for DELETE API endpoints for projects and resumes."""
import json
from src.db.project_summaries import save_project_summary, get_project_summary_by_name
from src.db.resumes import insert_resume_snapshot, list_resumes


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_project(conn, user_id, name, project_type="code", project_mode="individual"):
    """Create a test project and return its ID."""
    summary_json = json.dumps({
        "project_name": name,
        "project_type": project_type,
        "project_mode": project_mode,
        "languages": ["Python"],
        "summary_text": f"Test project: {name}",
        "metrics": {}
    })
    save_project_summary(conn, user_id, name, summary_json)
    conn.commit()
    project = get_project_summary_by_name(conn, user_id, name)
    return project["project_summary_id"]


def create_test_resume(conn, user_id, name):
    """Create a test resume and return its ID."""
    resume_json = json.dumps({
        "projects": [{"project_name": f"Project for {name}"}],
        "aggregated_skills": {}
    })
    resume_id = insert_resume_snapshot(conn, user_id, name, resume_json)
    conn.commit()
    return resume_id


def create_other_user(conn, user_id=2, username="other-user"):
    """Create another user for isolation tests."""
    conn.execute(
        "INSERT OR IGNORE INTO users(user_id, username, email) VALUES (?, ?, NULL)",
        (user_id, username)
    )
    conn.commit()


def assert_success_response(response, expected_status=200):
    """Assert response is successful with expected status code."""
    assert response.status_code == expected_status
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    return body


def assert_delete_single_success(response):
    """Assert single delete response is successful."""
    body = assert_success_response(response)
    assert body["data"] is None
    return body


def assert_delete_all_success(response, expected_count):
    """Assert delete all response is successful with expected count."""
    body = assert_success_response(response)
    assert body["data"]["deleted_count"] == expected_count
    return body


def assert_not_found(response):
    """Assert response is 404 not found."""
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def assert_unauthorized(response):
    """Assert response is 401 unauthorized."""
    assert response.status_code == 401


# ============================================================================
# DELETE /projects/{project_id} tests
# ============================================================================

def test_delete_project_requires_auth(client):
    """Test that DELETE /projects/{id} requires authentication."""
    res = client.delete("/projects/1")
    assert_unauthorized(res)


def test_delete_project_not_found_returns_404(client, auth_headers):
    """Test deleting a project that doesn't exist returns 404."""
    res = client.delete("/projects/999", headers=auth_headers)
    assert_not_found(res)


def test_delete_project_success(client, auth_headers, seed_conn):
    """Test successfully deleting a project."""
    project_id = create_test_project(seed_conn, 1, "TestProject")

    res = client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert_delete_single_success(res)

    # Verify it's gone
    assert get_project_summary_by_name(seed_conn, 1, "TestProject") is None


def test_delete_project_also_deletes_dedup_tables(client, auth_headers, seed_conn):
    """Test that deleting a project also removes data from projects/project_versions/version_files tables."""
    project_id = create_test_project(seed_conn, 1, "TestProjectDedup")

    # Also insert into deduplication tables (projects, project_versions, version_files)
    cur = seed_conn.execute(
        "INSERT INTO projects(user_id, display_name) VALUES (?, ?)",
        (1, "TestProjectDedup"),
    )
    project_key = cur.lastrowid
    cur = seed_conn.execute(
        "INSERT INTO project_versions(project_key, upload_id, fingerprint_strict, fingerprint_loose) "
        "VALUES (?, ?, ?, ?)",
        (project_key, None, "fp_strict_123", "fp_loose_123"),
    )
    version_key = cur.lastrowid
    seed_conn.execute(
        "INSERT INTO version_files(version_key, relpath, file_hash) VALUES (?, ?, ?)",
        (version_key, "src/main.py", "abc123hash"),
    )
    seed_conn.commit()

    # Verify dedup data exists before delete
    row = seed_conn.execute(
        "SELECT project_key FROM projects WHERE user_id = ? AND display_name = ?",
        (1, "TestProjectDedup"),
    ).fetchone()
    assert row is not None

    # Delete via API
    res = client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert_delete_single_success(res)

    # Verify project_summaries is gone
    assert get_project_summary_by_name(seed_conn, 1, "TestProjectDedup") is None

    # Verify projects table is also cleaned up
    row = seed_conn.execute(
        "SELECT project_key FROM projects WHERE user_id = ? AND display_name = ?",
        (1, "TestProjectDedup"),
    ).fetchone()
    assert row is None

    # Verify project_versions is also cleaned up
    row = seed_conn.execute(
        "SELECT version_key FROM project_versions WHERE project_key = ?",
        (project_key,),
    ).fetchone()
    assert row is None

    # Verify version_files is also cleaned up (via CASCADE)
    row = seed_conn.execute(
        "SELECT * FROM version_files WHERE version_key = ?",
        (version_key,),
    ).fetchone()
    assert row is None


def test_delete_project_cleans_up_rankings_and_thumbnails(client, auth_headers, seed_conn):
    """Test that deleting a project also removes project_rankings and project_thumbnails."""
    project_id = create_test_project(seed_conn, 1, "TestProjectRanked")

    # Insert into project_rankings and project_thumbnails
    seed_conn.execute(
        "INSERT INTO project_rankings(user_id, project_name, manual_rank) VALUES (?, ?, ?)",
        (1, "TestProjectRanked", 1),
    )
    seed_conn.execute(
        "INSERT INTO project_thumbnails(user_id, project_name, image_path, added_at, updated_at) "
        "VALUES (?, ?, ?, datetime('now'), datetime('now'))",
        (1, "TestProjectRanked", "/path/to/thumb.png"),
    )
    seed_conn.commit()

    # Verify data exists before delete
    assert seed_conn.execute(
        "SELECT 1 FROM project_rankings WHERE user_id = ? AND project_name = ?",
        (1, "TestProjectRanked"),
    ).fetchone() is not None
    assert seed_conn.execute(
        "SELECT 1 FROM project_thumbnails WHERE user_id = ? AND project_name = ?",
        (1, "TestProjectRanked"),
    ).fetchone() is not None

    # Delete via API
    res = client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert_delete_single_success(res)

    # Verify project_rankings is cleaned up
    assert seed_conn.execute(
        "SELECT 1 FROM project_rankings WHERE user_id = ? AND project_name = ?",
        (1, "TestProjectRanked"),
    ).fetchone() is None

    # Verify project_thumbnails is cleaned up
    assert seed_conn.execute(
        "SELECT 1 FROM project_thumbnails WHERE user_id = ? AND project_name = ?",
        (1, "TestProjectRanked"),
    ).fetchone() is None


def test_delete_all_projects_cleans_dedup_tables(client, auth_headers, seed_conn):
    """Test that delete all projects also cleans up deduplication tables."""
    # Create multiple projects with dedup data
    for i in range(2):
        name = f"BulkProject{i}"
        create_test_project(seed_conn, 1, name)
        cur = seed_conn.execute(
            "INSERT INTO projects(user_id, display_name) VALUES (?, ?)",
            (1, name),
        )
        pk = cur.lastrowid
        seed_conn.execute(
            "INSERT INTO project_versions(project_key, upload_id, fingerprint_strict, fingerprint_loose) "
            "VALUES (?, ?, ?, ?)",
            (pk, None, f"fp_strict_{i}", f"fp_loose_{i}"),
        )
    seed_conn.commit()

    # Verify dedup data exists
    count = seed_conn.execute(
        "SELECT COUNT(*) FROM projects WHERE user_id = ?", (1,)
    ).fetchone()[0]
    assert count == 2

    # Delete all via API
    res = client.delete("/projects", headers=auth_headers)
    assert_delete_all_success(res, expected_count=2)

    # Verify projects table is cleaned up for user 1
    count = seed_conn.execute(
        "SELECT COUNT(*) FROM projects WHERE user_id = ?", (1,)
    ).fetchone()[0]
    assert count == 0


def test_delete_all_projects_cleans_orphaned_dedup_data(client, auth_headers, seed_conn):
    """Test that delete all projects also cleans orphaned data in projects table.

    Orphaned data occurs when uploads start but analysis never completes,
    leaving data in projects/project_versions but not in project_summaries.
    """
    # Create a normal project (has both project_summaries and projects table entry)
    create_test_project(seed_conn, 1, "NormalProject")
    cur = seed_conn.execute(
        "INSERT INTO projects(user_id, display_name) VALUES (?, ?)",
        (1, "NormalProject"),
    )
    pk = cur.lastrowid
    seed_conn.execute(
        "INSERT INTO project_versions(project_key, upload_id, fingerprint_strict, fingerprint_loose) "
        "VALUES (?, ?, ?, ?)",
        (pk, None, "fp_normal", "fp_normal_loose"),
    )

    # Create orphaned project (only in projects table, no project_summaries)
    cur = seed_conn.execute(
        "INSERT INTO projects(user_id, display_name) VALUES (?, ?)",
        (1, "OrphanedProject"),
    )
    orphan_pk = cur.lastrowid
    seed_conn.execute(
        "INSERT INTO project_versions(project_key, upload_id, fingerprint_strict, fingerprint_loose) "
        "VALUES (?, ?, ?, ?)",
        (orphan_pk, None, "fp_orphan", "fp_orphan_loose"),
    )
    seed_conn.commit()

    # Verify: 1 in project_summaries, 2 in projects table
    summary_count = seed_conn.execute(
        "SELECT COUNT(*) FROM project_summaries WHERE user_id = ?", (1,)
    ).fetchone()[0]
    projects_count = seed_conn.execute(
        "SELECT COUNT(*) FROM projects WHERE user_id = ?", (1,)
    ).fetchone()[0]
    assert summary_count == 1
    assert projects_count == 2

    # Delete all via API - should clean up both normal and orphaned
    res = client.delete("/projects", headers=auth_headers)
    assert_delete_all_success(res, expected_count=2)  # Both should be counted

    # Verify both tables are cleaned up
    summary_count = seed_conn.execute(
        "SELECT COUNT(*) FROM project_summaries WHERE user_id = ?", (1,)
    ).fetchone()[0]
    projects_count = seed_conn.execute(
        "SELECT COUNT(*) FROM projects WHERE user_id = ?", (1,)
    ).fetchone()[0]
    assert summary_count == 0
    assert projects_count == 0


def test_delete_project_wrong_user(client, auth_headers, seed_conn):
    """Test that a user cannot delete another user's project."""
    create_other_user(seed_conn)
    project_id = create_test_project(seed_conn, 2, "OtherUserProject")

    # Try to delete with user 1's auth (should 404 since user 1 can't see it)
    res = client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert_not_found(res)

    # Verify project still exists for user 2
    assert get_project_summary_by_name(seed_conn, 2, "OtherUserProject") is not None


# ============================================================================
# DELETE /projects tests (delete all)
# ============================================================================

def test_delete_all_projects_requires_auth(client):
    """Test that DELETE /projects requires authentication."""
    res = client.delete("/projects")
    assert_unauthorized(res)


def test_delete_all_projects_empty_returns_zero(client, auth_headers):
    """Test deleting all projects when none exist returns count 0."""
    res = client.delete("/projects", headers=auth_headers)
    assert_delete_all_success(res, expected_count=0)


def test_delete_all_projects_success(client, auth_headers, seed_conn):
    """Test successfully deleting all projects."""
    # Create multiple projects
    for i in range(3):
        create_test_project(seed_conn, 1, f"Project{i}")

    # Verify they exist
    for i in range(3):
        assert get_project_summary_by_name(seed_conn, 1, f"Project{i}") is not None

    # Delete all
    res = client.delete("/projects", headers=auth_headers)
    assert_delete_all_success(res, expected_count=3)

    # Verify they're all gone
    for i in range(3):
        assert get_project_summary_by_name(seed_conn, 1, f"Project{i}") is None


def test_delete_all_projects_only_deletes_own_projects(client, auth_headers, seed_conn):
    """Test that delete all only deletes the authenticated user's projects."""
    # Create projects for both users
    create_test_project(seed_conn, 1, "User1Project")
    create_other_user(seed_conn)
    create_test_project(seed_conn, 2, "User2Project")

    # Delete all as user 1
    res = client.delete("/projects", headers=auth_headers)
    assert_delete_all_success(res, expected_count=1)

    # Verify user 1's project is gone
    assert get_project_summary_by_name(seed_conn, 1, "User1Project") is None

    # Verify user 2's project still exists
    assert get_project_summary_by_name(seed_conn, 2, "User2Project") is not None


# ============================================================================
# DELETE /resume/{resume_id} tests
# ============================================================================

def test_delete_resume_requires_auth(client):
    """Test that DELETE /resume/{id} requires authentication."""
    res = client.delete("/resume/1")
    assert_unauthorized(res)


def test_delete_resume_not_found_returns_404(client, auth_headers):
    """Test deleting a resume that doesn't exist returns 404."""
    res = client.delete("/resume/999", headers=auth_headers)
    assert_not_found(res)


def test_delete_resume_success(client, auth_headers, seed_conn):
    """Test successfully deleting a resume."""
    resume_id = create_test_resume(seed_conn, 1, "Test Resume")

    # Verify it exists
    assert any(r["id"] == resume_id for r in list_resumes(seed_conn, 1))

    # Delete it
    res = client.delete(f"/resume/{resume_id}", headers=auth_headers)
    assert_delete_single_success(res)

    # Verify it's gone
    assert not any(r["id"] == resume_id for r in list_resumes(seed_conn, 1))


def test_delete_resume_wrong_user(client, auth_headers, seed_conn):
    """Test that a user cannot delete another user's resume."""
    create_other_user(seed_conn)
    resume_id = create_test_resume(seed_conn, 2, "Other User Resume")

    # Try to delete with user 1's auth (should 404 since user 1 can't see it)
    res = client.delete(f"/resume/{resume_id}", headers=auth_headers)
    assert_not_found(res)

    # Verify user 2's resume still exists
    assert any(r["id"] == resume_id for r in list_resumes(seed_conn, 2))


# ============================================================================
# DELETE /resume tests (delete all)
# ============================================================================

def test_delete_all_resumes_requires_auth(client):
    """Test that DELETE /resume requires authentication."""
    res = client.delete("/resume")
    assert_unauthorized(res)


def test_delete_all_resumes_empty_returns_zero(client, auth_headers):
    """Test deleting all resumes when none exist returns count 0."""
    res = client.delete("/resume", headers=auth_headers)
    assert_delete_all_success(res, expected_count=0)


def test_delete_all_resumes_success(client, auth_headers, seed_conn):
    """Test successfully deleting all resumes."""
    # Create multiple resumes
    resume_ids = []
    for i in range(3):
        resume_id = create_test_resume(seed_conn, 1, f"Resume {i}")
        resume_ids.append(resume_id)

    # Verify they exist
    resumes_before = list_resumes(seed_conn, 1)
    assert len(resumes_before) == 3

    # Delete all
    res = client.delete("/resume", headers=auth_headers)
    assert_delete_all_success(res, expected_count=3)

    # Verify they're all gone
    assert len(list_resumes(seed_conn, 1)) == 0


def test_delete_all_resumes_only_deletes_own_resumes(client, auth_headers, seed_conn):
    """Test that delete all only deletes the authenticated user's resumes."""
    # Create resumes for both users
    create_test_resume(seed_conn, 1, "User 1 Resume")
    create_other_user(seed_conn)
    create_test_resume(seed_conn, 2, "User 2 Resume")

    # Delete all as user 1
    res = client.delete("/resume", headers=auth_headers)
    assert_delete_all_success(res, expected_count=1)

    # Verify user 1's resumes are gone
    assert len(list_resumes(seed_conn, 1)) == 0

    # Verify user 2's resume still exists
    assert len(list_resumes(seed_conn, 2)) == 1


