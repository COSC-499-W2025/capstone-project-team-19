"""
Tests for skill timeline service: diminishing returns and cumulative scoring.
"""

import pytest
from datetime import datetime
import src.db as db
from src.services.skills_service import _diminishing_return, get_skill_timeline_data


@pytest.fixture
def test_db():
    conn = db.connect(":memory:")
    db.init_schema(conn)
    yield conn
    conn.close()


def _user(conn):
    return db.get_or_create_user(conn, "testuser")


def _project(conn, uid, name, ptype="code", when=None):
    return db.record_project_classification(
        conn, user_id=uid, zip_path="/t.zip", zip_name="t",
        project_name=name, classification="individual",
        project_type=ptype, when=when or datetime.now().isoformat(),
    )


def _skill(conn, uid, project, skill, level, score):
    pk = db.get_project_key(conn, uid, project)
    conn.execute(
        "INSERT INTO project_skills (user_id,project_key,skill_name,level,score,evidence_json) "
        "VALUES (?,?,?,?,?,'[]')", (uid, int(pk), skill, level, score))
    conn.commit()


def _text_dates(conn, vk, start, end):
    conn.execute(
        "INSERT INTO text_activity_contribution "
        "(version_key,start_date,end_date,duration_days,total_files,classified_files,"
        "activity_classification_json,timeline_json,activity_counts_json) "
        "VALUES (?,?,?,1,1,1,'{}','[]','{}')", (vk, start, end))
    conn.commit()


# -- Diminishing return unit tests --

class TestDiminishingReturn:
    def test_first_score(self):
        assert _diminishing_return(0.0, 0.3) == pytest.approx(0.3)

    def test_two_scores(self):
        assert _diminishing_return(0.3, 0.4) == pytest.approx(0.58)

    def test_three_incremental(self):
        s = _diminishing_return(_diminishing_return(0.0, 0.3), 0.4)
        s = _diminishing_return(s, 0.25)
        assert s == pytest.approx(0.685)

    def test_max_score_reaches_one(self):
        assert _diminishing_return(0.5, 1.0) == pytest.approx(1.0)

    def test_zero_new_unchanged(self):
        assert _diminishing_return(0.5, 0.0) == pytest.approx(0.5)

    def test_never_exceeds_one(self):
        s = 0.0
        for _ in range(20):
            s = _diminishing_return(s, 0.3)
        assert s <= 1.0

    def test_order_independent(self):
        a = _diminishing_return(_diminishing_return(0.0, 0.3), 0.5)
        b = _diminishing_return(_diminishing_return(0.0, 0.5), 0.3)
        assert a == pytest.approx(b)


# -- Timeline integration tests --

class TestTimelineData:
    def test_empty(self, test_db):
        uid = _user(test_db)
        r = get_skill_timeline_data(test_db, uid)
        assert r["dated"] == [] and r["undated"] == [] and r["current_totals"] == {}
        assert r["summary"]["total_skills"] == 0

    def test_single_dated(self, test_db):
        uid = _user(test_db)
        vk = _project(test_db, uid, "Essay", "text")
        _text_dates(test_db, vk, "2024-06-01", "2024-06-15")
        _skill(test_db, uid, "Essay", "writing", "Advanced", 0.8)

        r = get_skill_timeline_data(test_db, uid)
        assert len(r["dated"]) == 1
        assert r["dated"][0]["cumulative_skills"]["writing"]["cumulative_score"] == pytest.approx(0.8)
        assert r["undated"] == []

    def test_cumulative_across_dates(self, test_db):
        uid = _user(test_db)
        vk1 = _project(test_db, uid, "P1", "text")
        _text_dates(test_db, vk1, "2024-01-01", "2024-01-10")
        _skill(test_db, uid, "P1", "research", "Beginner", 0.3)

        vk2 = _project(test_db, uid, "P2", "text")
        _text_dates(test_db, vk2, "2024-02-01", "2024-02-15")
        _skill(test_db, uid, "P2", "research", "Intermediate", 0.4)

        r = get_skill_timeline_data(test_db, uid)
        assert r["dated"][0]["cumulative_skills"]["research"]["cumulative_score"] == pytest.approx(0.3)
        # 1-(0.7)(0.6) = 0.58
        assert r["dated"][1]["cumulative_skills"]["research"]["cumulative_score"] == pytest.approx(0.58)
        assert r["dated"][1]["cumulative_skills"]["research"]["projects"] == ["P1", "P2"]

    def test_cumulative_carries_all_skills(self, test_db):
        uid = _user(test_db)
        vk1 = _project(test_db, uid, "P1", "text")
        _text_dates(test_db, vk1, "2024-01-01", "2024-01-05")
        _skill(test_db, uid, "P1", "skill_a", "Beginner", 0.3)

        vk2 = _project(test_db, uid, "P2", "text")
        _text_dates(test_db, vk2, "2024-02-01", "2024-02-10")
        _skill(test_db, uid, "P2", "skill_b", "Beginner", 0.5)

        r = get_skill_timeline_data(test_db, uid)
        d2 = r["dated"][1]["cumulative_skills"]
        assert "skill a" in d2 and "skill b" in d2

    def test_undated_folds_into_current_totals(self, test_db):
        uid = _user(test_db)
        vk = _project(test_db, uid, "Dated", "text")
        _text_dates(test_db, vk, "2024-01-01", "2024-01-15")
        _skill(test_db, uid, "Dated", "writing", "Intermediate", 0.4)

        _project(test_db, uid, "Undated", "code")
        _skill(test_db, uid, "Undated", "writing", "Beginner", 0.3)

        r = get_skill_timeline_data(test_db, uid)
        assert r["dated"][0]["cumulative_skills"]["writing"]["cumulative_score"] == pytest.approx(0.4)
        # current: 1-(0.6)(0.7) = 0.58
        assert r["current_totals"]["writing"]["cumulative_score"] == pytest.approx(0.58)
        assert r["current_totals"]["writing"]["projects"] == ["Dated", "Undated"]

    def test_undated_only_skill(self, test_db):
        uid = _user(test_db)
        _project(test_db, uid, "Code", "code")
        _skill(test_db, uid, "Code", "python", "Advanced", 0.7)

        r = get_skill_timeline_data(test_db, uid)
        assert r["dated"] == []
        assert r["current_totals"]["python"]["cumulative_score"] == pytest.approx(0.7)

    def test_summary(self, test_db):
        uid = _user(test_db)
        vk1 = _project(test_db, uid, "P1", "text")
        _text_dates(test_db, vk1, "2024-01-01", "2024-01-10")
        _skill(test_db, uid, "P1", "skill_a", "Beginner", 0.3)

        vk2 = _project(test_db, uid, "P2", "text")
        _text_dates(test_db, vk2, "2024-03-01", "2024-03-20")
        _skill(test_db, uid, "P2", "skill_b", "Beginner", 0.5)

        _project(test_db, uid, "P3", "code")
        _skill(test_db, uid, "P3", "skill_c", "Advanced", 0.9)

        r = get_skill_timeline_data(test_db, uid)
        s = r["summary"]
        assert s["total_skills"] == 3
        assert s["total_projects"] == 3
        assert s["date_range"]["earliest"] == "2024-01-10"
        assert s["date_range"]["latest"] == "2024-03-20"

    def test_many_low_scores_converge(self, test_db):
        uid = _user(test_db)
        for i in range(5):
            vk = _project(test_db, uid, f"P{i}", "text")
            _text_dates(test_db, vk, "2024-01-01", f"2024-0{i+1}-15")
            _skill(test_db, uid, f"P{i}", "research", "Beginner", 0.25)

        r = get_skill_timeline_data(test_db, uid)
        # 1-(0.75)^5 ≈ 0.7627
        final = r["dated"][-1]["cumulative_skills"]["research"]
        assert final["cumulative_score"] == pytest.approx(0.7627, abs=0.001)
        assert len(final["projects"]) == 5
