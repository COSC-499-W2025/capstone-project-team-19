import sqlite3
import pytest
import db


@pytest.fixture
def conn(shared_db):
    c = db.connect()
    user_id = db.get_or_create_user(c, "evol-test-user")
    return c, user_id


def _create_project_with_two_versions(conn, user_id, project_name="TestProj"):
    """Helper: create a project with two versions and return (project_key, vk1, vk2)."""
    from src.db.deduplication import insert_project, insert_project_version, insert_version_files

    pk = insert_project(conn, user_id, project_name)
    conn.commit()
    vk1 = insert_project_version(conn, pk, upload_id=1, fingerprint_strict="fp1", fingerprint_loose="fl1")
    conn.commit()
    vk2 = insert_project_version(conn, pk, upload_id=2, fingerprint_strict="fp2", fingerprint_loose="fl2")
    conn.commit()
    return pk, vk1, vk2


# ---------------------------------------------------------------------------
# get_file_diff_between_versions
# ---------------------------------------------------------------------------

class TestFileDiff:
    def test_added_files(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version, insert_version_files
        from src.db.version_evolution import get_file_diff_between_versions

        pk = insert_project(c, uid, "FileDiffProj")
        c.commit()
        vk1 = insert_project_version(c, pk, upload_id=1, fingerprint_strict="a1", fingerprint_loose="a1")
        insert_version_files(c, vk1, [("src/main.py", "hash_a")])
        c.commit()

        vk2 = insert_project_version(c, pk, upload_id=2, fingerprint_strict="a2", fingerprint_loose="a2")
        insert_version_files(c, vk2, [("src/main.py", "hash_a"), ("src/util.py", "hash_b")])
        c.commit()

        diff = get_file_diff_between_versions(c, vk1, vk2)
        assert diff["added"] == ["src/util.py"]
        assert diff["modified"] == []
        assert diff["removed"] == []
        assert diff["unchanged_count"] == 1

    def test_removed_files(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version, insert_version_files
        from src.db.version_evolution import get_file_diff_between_versions

        pk = insert_project(c, uid, "RemovedProj")
        c.commit()
        vk1 = insert_project_version(c, pk, upload_id=1, fingerprint_strict="r1", fingerprint_loose="r1")
        insert_version_files(c, vk1, [("a.py", "h1"), ("b.py", "h2")])
        c.commit()

        vk2 = insert_project_version(c, pk, upload_id=2, fingerprint_strict="r2", fingerprint_loose="r2")
        insert_version_files(c, vk2, [("a.py", "h1")])
        c.commit()

        diff = get_file_diff_between_versions(c, vk1, vk2)
        assert diff["added"] == []
        assert diff["removed"] == ["b.py"]
        assert diff["unchanged_count"] == 1

    def test_modified_files(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version, insert_version_files
        from src.db.version_evolution import get_file_diff_between_versions

        pk = insert_project(c, uid, "ModifiedProj")
        c.commit()
        vk1 = insert_project_version(c, pk, upload_id=1, fingerprint_strict="m1", fingerprint_loose="m1")
        insert_version_files(c, vk1, [("app.py", "old_hash")])
        c.commit()

        vk2 = insert_project_version(c, pk, upload_id=2, fingerprint_strict="m2", fingerprint_loose="m2")
        insert_version_files(c, vk2, [("app.py", "new_hash")])
        c.commit()

        diff = get_file_diff_between_versions(c, vk1, vk2)
        assert diff["modified"] == ["app.py"]
        assert diff["added"] == []
        assert diff["removed"] == []
        assert diff["unchanged_count"] == 0

    def test_mixed_changes(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version, insert_version_files
        from src.db.version_evolution import get_file_diff_between_versions

        pk = insert_project(c, uid, "MixedProj")
        c.commit()
        vk1 = insert_project_version(c, pk, upload_id=1, fingerprint_strict="x1", fingerprint_loose="x1")
        insert_version_files(c, vk1, [
            ("keep.py", "same"),
            ("change.py", "old"),
            ("delete.py", "gone"),
        ])
        c.commit()

        vk2 = insert_project_version(c, pk, upload_id=2, fingerprint_strict="x2", fingerprint_loose="x2")
        insert_version_files(c, vk2, [
            ("keep.py", "same"),
            ("change.py", "new"),
            ("added.py", "fresh"),
        ])
        c.commit()

        diff = get_file_diff_between_versions(c, vk1, vk2)
        assert diff["added"] == ["added.py"]
        assert diff["modified"] == ["change.py"]
        assert diff["removed"] == ["delete.py"]
        assert diff["unchanged_count"] == 1

    def test_empty_versions(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version
        from src.db.version_evolution import get_file_diff_between_versions

        pk = insert_project(c, uid, "EmptyProj")
        c.commit()
        vk1 = insert_project_version(c, pk, upload_id=1, fingerprint_strict="e1", fingerprint_loose="e1")
        c.commit()
        vk2 = insert_project_version(c, pk, upload_id=2, fingerprint_strict="e2", fingerprint_loose="e2")
        c.commit()

        diff = get_file_diff_between_versions(c, vk1, vk2)
        assert diff["added"] == []
        assert diff["modified"] == []
        assert diff["removed"] == []
        assert diff["unchanged_count"] == 0


# ---------------------------------------------------------------------------
# get_skill_diff_between_versions
# ---------------------------------------------------------------------------

class TestSkillDiff:
    def _insert_skills(self, c, vk, skills):
        """skills: list of (name, level, score)"""
        c.executemany(
            "INSERT OR REPLACE INTO version_skills (version_key, skill_name, level, score) VALUES (?, ?, ?, ?)",
            [(vk, name, level, score) for name, level, score in skills],
        )
        c.commit()

    def test_new_skills(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version
        from src.db.version_evolution import get_skill_diff_between_versions

        pk = insert_project(c, uid, "SkillNewProj")
        c.commit()
        vk1 = insert_project_version(c, pk, upload_id=1, fingerprint_strict="sn1", fingerprint_loose="sn1")
        c.commit()
        vk2 = insert_project_version(c, pk, upload_id=2, fingerprint_strict="sn2", fingerprint_loose="sn2")
        c.commit()

        self._insert_skills(c, vk1, [("Python", "intermediate", 0.6)])
        self._insert_skills(c, vk2, [("Python", "intermediate", 0.6), ("Testing", "beginner", 0.3)])

        diff = get_skill_diff_between_versions(c, vk1, vk2)
        assert len(diff["new"]) == 1
        assert diff["new"][0]["skill_name"] == "Testing"
        assert diff["removed"] == []
        assert diff["improved"] == []

    def test_removed_skills(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version
        from src.db.version_evolution import get_skill_diff_between_versions

        pk = insert_project(c, uid, "SkillRmProj")
        c.commit()
        vk1 = insert_project_version(c, pk, upload_id=1, fingerprint_strict="sr1", fingerprint_loose="sr1")
        c.commit()
        vk2 = insert_project_version(c, pk, upload_id=2, fingerprint_strict="sr2", fingerprint_loose="sr2")
        c.commit()

        self._insert_skills(c, vk1, [("Python", "advanced", 0.9), ("OOP", "intermediate", 0.5)])
        self._insert_skills(c, vk2, [("Python", "advanced", 0.9)])

        diff = get_skill_diff_between_versions(c, vk1, vk2)
        assert len(diff["removed"]) == 1
        assert diff["removed"][0]["skill_name"] == "OOP"
        assert diff["new"] == []

    def test_improved_and_declined(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version
        from src.db.version_evolution import get_skill_diff_between_versions

        pk = insert_project(c, uid, "SkillChgProj")
        c.commit()
        vk1 = insert_project_version(c, pk, upload_id=1, fingerprint_strict="sc1", fingerprint_loose="sc1")
        c.commit()
        vk2 = insert_project_version(c, pk, upload_id=2, fingerprint_strict="sc2", fingerprint_loose="sc2")
        c.commit()

        self._insert_skills(c, vk1, [("Python", "intermediate", 0.5), ("Docs", "advanced", 0.8)])
        self._insert_skills(c, vk2, [("Python", "advanced", 0.9), ("Docs", "intermediate", 0.4)])

        diff = get_skill_diff_between_versions(c, vk1, vk2)
        assert len(diff["improved"]) == 1
        assert diff["improved"][0]["skill_name"] == "Python"
        assert diff["improved"][0]["prev_score"] == 0.5
        assert diff["improved"][0]["score"] == 0.9

        assert len(diff["declined"]) == 1
        assert diff["declined"][0]["skill_name"] == "Docs"

    def test_no_changes(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version
        from src.db.version_evolution import get_skill_diff_between_versions

        pk = insert_project(c, uid, "SkillSameProj")
        c.commit()
        vk1 = insert_project_version(c, pk, upload_id=1, fingerprint_strict="ss1", fingerprint_loose="ss1")
        c.commit()
        vk2 = insert_project_version(c, pk, upload_id=2, fingerprint_strict="ss2", fingerprint_loose="ss2")
        c.commit()

        self._insert_skills(c, vk1, [("Python", "advanced", 0.9)])
        self._insert_skills(c, vk2, [("Python", "advanced", 0.9)])

        diff = get_skill_diff_between_versions(c, vk1, vk2)
        assert diff["new"] == []
        assert diff["removed"] == []
        assert diff["improved"] == []
        assert diff["declined"] == []


# ---------------------------------------------------------------------------
# Enriched version summary round-trip
# ---------------------------------------------------------------------------

class TestEnrichedVersionSummary:
    def test_languages_and_frameworks_round_trip(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version
        from src.db.version_evolution import insert_version_summary, get_version_summary

        pk = insert_project(c, uid, "EnrichedProj")
        c.commit()
        vk = insert_project_version(c, pk, upload_id=1, fingerprint_strict="en1", fingerprint_loose="en1")
        c.commit()

        insert_version_summary(
            c, vk,
            summary_text="Added REST API",
            languages=["Python", "JavaScript"],
            frameworks=["FastAPI", "React"],
            avg_complexity=3.2,
            total_files=15,
        )

        vs = get_version_summary(c, vk)
        assert vs is not None
        assert vs["languages"] == ["Python", "JavaScript"]
        assert vs["frameworks"] == ["FastAPI", "React"]
        assert vs["avg_complexity"] == pytest.approx(3.2)
        assert vs["total_files"] == 15

    def test_null_enriched_fields(self, conn):
        c, uid = conn
        from src.db.deduplication import insert_project, insert_project_version
        from src.db.version_evolution import insert_version_summary, get_version_summary

        pk = insert_project(c, uid, "NullEnrichedProj")
        c.commit()
        vk = insert_project_version(c, pk, upload_id=1, fingerprint_strict="ne1", fingerprint_loose="ne1")
        c.commit()

        insert_version_summary(c, vk, summary_text="Minimal")

        vs = get_version_summary(c, vk)
        assert vs["languages"] == []
        assert vs["frameworks"] == []
        assert vs["avg_complexity"] is None
        assert vs["total_files"] is None
