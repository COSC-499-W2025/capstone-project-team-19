import json
import sqlite3
from datetime import datetime, UTC

import pytest

from src.db import init_schema, save_project_summary, list_resumes, get_resume_snapshot, insert_resume_snapshot
from src.menu.resume import menu as resume_menu
from src.menu.resume import flow as resume_flow
import src.menu.resume.helpers as helpers


def _make_summary(project_name: str, project_type: str = "code", project_mode: str = "individual") -> str:
    """Build a minimal ProjectSummary JSON string."""
    summary = {
        "project_name": project_name,
        "project_type": project_type,
        "project_mode": project_mode,
        "languages": [],
        "frameworks": [],
        "summary_text": None,
        "skills": [],
        "metrics": {},
        "contributions": {},
        "created_at": datetime.now(UTC).isoformat(),
        "project_id": None,
    }
    return json.dumps(summary)


def test_create_resume_uses_top_five(monkeypatch):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # Seed six project summaries
    names = [f"proj{i}" for i in range(6)]
    for name in names:
        save_project_summary(conn, user_id, name, _make_summary(name))

    # Rank projects with scores (proj0 highest, proj5 lowest)
    ranked = [(name, score) for score, name in enumerate(reversed(names), start=1)]
    ranked.sort(key=lambda x: x[1], reverse=True)

    def fake_collect_project_data(conn_arg, user_id_arg):
        assert conn_arg is conn
        assert user_id_arg == user_id
        return ranked

    # Always accept default resume name
    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr(resume_flow, "collect_project_data", fake_collect_project_data)

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    snapshots = list_resumes(conn, user_id)
    assert len(snapshots) == 1

    snap = get_resume_snapshot(conn, user_id, snapshots[0]["id"])
    assert snap is not None

    data = json.loads(snap["resume_json"])
    project_names = {p["project_name"] for p in data.get("projects", [])}

    # Expect only top 5 projects (exclude the lowest-ranked)
    expected_top = set(name for name, _ in ranked[:5])
    assert project_names == expected_top


def test_create_resume_no_summaries(monkeypatch):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # No summaries seeded
    monkeypatch.setattr("builtins.input", lambda _: "")

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    snapshots = list_resumes(conn, user_id)
    assert snapshots == []


def test_view_existing_resume_lists_and_renders(monkeypatch, capsys):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # Seed one summary and a resume snapshot
    save_project_summary(conn, user_id, "projA", _make_summary("projA"))
    snap_data = {"projects": [{"project_name": "projA"}], "aggregated_skills": {}}
    insert_resume_snapshot(conn, user_id, "MyResume", json.dumps(snap_data), "Rendered text")

    # Mock selection of first resume
    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    handled = resume_flow._handle_view_existing_resume(conn, user_id)

    captured = capsys.readouterr().out
    assert "MyResume" in captured
    assert "Rendered text" in captured
    assert handled is True


def test_view_existing_resume_no_resumes(capsys):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    handled = resume_flow._handle_view_existing_resume(conn, user_id)
    captured = capsys.readouterr().out
    assert "No saved resumes yet" in captured
    assert handled is False


def test_create_resume_with_fewer_than_five_projects(monkeypatch):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # Seed three project summaries
    for name in ["p1", "p2", "p3"]:
        save_project_summary(conn, user_id, name, _make_summary(name))

    # Mock ranking returning just these three
    def fake_collect_project_data(conn_arg, user_id_arg):
        return [("p1", 1.0), ("p2", 0.9), ("p3", 0.8)]

    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr(resume_flow, "collect_project_data", fake_collect_project_data)

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    snaps = list_resumes(conn, user_id)
    assert len(snaps) == 1
    data = json.loads(snaps[0]["name"] or "{}") if False else json.loads(get_resume_snapshot(conn, user_id, snaps[0]["id"])["resume_json"])
    projects = {p["project_name"] for p in data.get("projects", [])}
    assert projects == {"p1", "p2", "p3"}

def test_create_resume_with_manual_selection(monkeypatch):
    """Test selecting specific projects manually."""
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    names = [f"proj{i}" for i in range(6)]
    for name in names:
        save_project_summary(conn, user_id, name, _make_summary(name))

    ranked = [(name, 1.0 - i*0.1) for i, name in enumerate(names)]

    def fake_collect_project_data(conn_arg, user_id_arg):
        return ranked

    inputs = iter(["2,4,6", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(resume_flow, "collect_project_data", fake_collect_project_data)

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    snapshots = list_resumes(conn, user_id)
    assert len(snapshots) == 1

    snap = get_resume_snapshot(conn, user_id, snapshots[0]["id"])
    data = json.loads(snap["resume_json"])
    project_names = [p["project_name"] for p in data.get("projects", [])]

    assert project_names == ["proj1", "proj3", "proj5"]


def test_create_resume_limits_to_five_projects(monkeypatch, capsys):
    """Test that selecting more than 5 projects limits to 5."""
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    names = [f"proj{i}" for i in range(10)]
    for name in names:
        save_project_summary(conn, user_id, name, _make_summary(name))

    ranked = [(name, 1.0 - i*0.1) for i, name in enumerate(names)]

    def fake_collect_project_data(conn_arg, user_id_arg):
        return ranked

    inputs = iter(["1,2,3,4,5,6,7", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(resume_flow, "collect_project_data", fake_collect_project_data)

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    captured = capsys.readouterr().out
    assert "maximum is 5" in captured.lower() or "first 5" in captured.lower()

    snapshots = list_resumes(conn, user_id)
    assert len(snapshots) == 1

    snap = get_resume_snapshot(conn, user_id, snapshots[0]["id"])
    data = json.loads(snap["resume_json"])
    project_names = [p["project_name"] for p in data.get("projects", [])]

    assert len(project_names) == 5
    assert project_names == ["proj0", "proj1", "proj2", "proj3", "proj4"]


def test_create_resume_sorts_by_score(monkeypatch):
    """Test that projects are saved in score order (highest first)."""
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    names = ["projA", "projB", "projC", "projD"]
    for name in names:
        save_project_summary(conn, user_id, name, _make_summary(name))

    ranked = [("projB", 0.9), ("projD", 0.7), ("projA", 0.5), ("projC", 0.3)]

    def fake_collect_project_data(conn_arg, user_id_arg):
        return ranked

    inputs = iter(["4,1,2,3", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(resume_flow, "collect_project_data", fake_collect_project_data)

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    snapshots = list_resumes(conn, user_id)
    snap = get_resume_snapshot(conn, user_id, snapshots[0]["id"])
    data = json.loads(snap["resume_json"])
    project_names = [p["project_name"] for p in data.get("projects", [])]

    assert project_names == ["projB", "projD", "projA", "projC"]


def test_render_snapshot_text_activity_two_stages():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    from src.db import record_project_classification
    version_key = record_project_classification(
        conn,
        user_id,
        "fake.zip",
        "fake",
        "TextProj",
        "collaborative",
        project_type="text",
    )

    from src.db.text_activity import store_text_activity_contribution
    activity_data = {
        "timestamp_analysis": {"duration_days": 12},
        "summary": {
            "total_files": 2,
            "classified_files": 2,
            "activity_counts": {"Draft": 3, "Revision": 1},
        },
        "activity_classification": {},
        "timeline": [],
    }
    store_text_activity_contribution(conn, version_key, activity_data)

    from src.menu.resume.helpers import render_snapshot
    snapshot = {
        "projects": [
            {
                "project_name": "TextProj",
                "project_type": "text",
                "project_mode": "collaborative",
                "text_type": "Academic writing",
                "summary_text": "Example summary",
                "contribution_percent": 50.0,
                "classification_id": version_key,
                "languages": [],
                "frameworks": [],
                "skills": [],
            }
        ],
        "aggregated_skills": {},
    }

    rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
    lowered = rendered.lower()
    assert "balanced draft" in lowered
    assert "revision" in lowered

def test_render_snapshot_uses_manual_overrides():
    from src.menu.resume.helpers import render_snapshot

    snapshot = {
        "projects": [
            {
                "project_name": "proj1",
                "project_type": "code",
                "project_mode": "individual",
                "summary_text": "Default summary",
                "resume_display_name_override": "Custom Name",
                "resume_summary_override": "Custom summary",
                "resume_contributions_override": [
                    "Built the core workflow",
                    "Added tests and docs",
                ],
                "languages": [],
                "frameworks": [],
                "skills": [],
            }
        ],
        "aggregated_skills": {},
    }

    rendered = render_snapshot(None, None, snapshot, print_output=False)
    assert "- Custom Name" in rendered
    assert "Summary: Custom summary" in rendered
    assert "Built the core workflow" in rendered
    assert "Added tests and docs" in rendered


def test_manual_overrides_skip_resume_only(monkeypatch):
    from src.services.resume_overrides import apply_manual_overrides_to_resumes

    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    save_project_summary(
        conn,
        user_id,
        "projA",
        _make_summary("projA", project_type="code", project_mode="individual"),
    )

    monkeypatch.setattr(resume_flow, "collect_project_data", lambda c, u: [("projA", 1.0)])
    monkeypatch.setattr(
        helpers,
        "build_contribution_bullets",
        lambda c, u, p: ["Contributed X."],
    )
    monkeypatch.setattr("builtins.input", lambda _: "")

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    snap = get_resume_snapshot(conn, user_id, list_resumes(conn, user_id)[0]["id"])
    data = json.loads(snap["resume_json"])

    assert data["projects"][0]["contribution_bullets"] == ["Contributed X."]
    snap_a = {
        "projects": [
            {
                "project_name": "ProjX",
                "project_type": "code",
                "project_mode": "individual",
                "summary_text": "Original A",
                "resume_summary_override": "Resume-only A",
            }
        ],
        "aggregated_skills": {},
    }
    snap_b = {
        "projects": [
            {
                "project_name": "ProjX",
                "project_type": "code",
                "project_mode": "individual",
                "summary_text": "Original B",
            }
        ],
        "aggregated_skills": {},
    }

    insert_resume_snapshot(conn, user_id, "Resume A", json.dumps(snap_a), "rendered")
    insert_resume_snapshot(conn, user_id, "Resume B", json.dumps(snap_b), "rendered")

    overrides = {"summary_text": "Manual summary", "display_name": "Manual Name"}
    apply_manual_overrides_to_resumes(
        conn,
        user_id,
        "ProjX",
        overrides,
        {"summary_text", "display_name"},
    )

    resumes = list_resumes(conn, user_id)
    records = {r["name"]: get_resume_snapshot(conn, user_id, r["id"]) for r in resumes}

    snap_a_out = json.loads(records["Resume A"]["resume_json"])
    snap_b_out = json.loads(records["Resume B"]["resume_json"])

    proj_a = snap_a_out["projects"][0]
    proj_b = snap_b_out["projects"][0]

    assert "manual_summary_text" not in proj_a
    assert proj_a["manual_display_name"] == "Manual Name"
    assert proj_b["manual_summary_text"] == "Manual summary"
    assert proj_b["manual_display_name"] == "Manual Name"


def test_manual_overrides_force_resume_updates_resume_only():
    from src.services.resume_overrides import apply_manual_overrides_to_resumes

    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    snap_a = {
        "projects": [
            {
                "project_name": "ProjX",
                "project_type": "code",
                "project_mode": "individual",
                "summary_text": "Original A",
                "resume_summary_override": "Resume-only A",
                "resume_display_name_override": "Resume Name A",
            }
        ],
        "aggregated_skills": {},
    }
    snap_b = {
        "projects": [
            {
                "project_name": "ProjX",
                "project_type": "code",
                "project_mode": "individual",
                "summary_text": "Original B",
            }
        ],
        "aggregated_skills": {},
    }

    insert_resume_snapshot(conn, user_id, "Resume A", json.dumps(snap_a), "rendered")
    insert_resume_snapshot(conn, user_id, "Resume B", json.dumps(snap_b), "rendered")

    resumes = list_resumes(conn, user_id)
    resume_ids = {r["name"]: r["id"] for r in resumes}

    overrides = {"summary_text": "Manual summary", "display_name": "Manual Name"}
    apply_manual_overrides_to_resumes(
        conn,
        user_id,
        "ProjX",
        overrides,
        {"summary_text", "display_name"},
        force_resume_id=resume_ids["Resume A"],
    )

    records = {r["name"]: get_resume_snapshot(conn, user_id, r["id"]) for r in resumes}

    snap_a_out = json.loads(records["Resume A"]["resume_json"])
    snap_b_out = json.loads(records["Resume B"]["resume_json"])

    proj_a = snap_a_out["projects"][0]
    proj_b = snap_b_out["projects"][0]

    assert "resume_summary_override" not in proj_a
    assert "resume_display_name_override" not in proj_a
    assert proj_a["manual_summary_text"] == "Manual summary"
    assert proj_a["manual_display_name"] == "Manual Name"
    assert proj_b["manual_summary_text"] == "Manual summary"
    assert proj_b["manual_display_name"] == "Manual Name"

def test_create_resume_stores_contribution_bullets(monkeypatch):
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    save_project_summary(
        conn,
        user_id,
        "projA",
        _make_summary("projA", project_type="code", project_mode="individual"),
    )

    monkeypatch.setattr(resume_flow, "collect_project_data", lambda c, u: [("projA", 1.0)])
    monkeypatch.setattr(
        helpers,
        "build_contribution_bullets",
        lambda c, u, p: ["Contributed X."],
    )
    monkeypatch.setattr("builtins.input", lambda _: "")

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    snap = get_resume_snapshot(conn, user_id, list_resumes(conn, user_id)[0]["id"])
    data = json.loads(snap["resume_json"])

    assert data["projects"][0]["contribution_bullets"] == ["Contributed X."]


def test_create_resume_stores_key_role(monkeypatch):
    """Test that key_role from project summary is stored in resume snapshot."""
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # Create a summary with key_role in contributions
    summary_with_key_role = {
        "project_name": "projA",
        "project_type": "code",
        "project_mode": "individual",
        "languages": ["Python"],
        "frameworks": [],
        "summary_text": "A test project",
        "skills": [],
        "metrics": {},
        "contributions": {"key_role": "Backend Developer"},
        "created_at": datetime.now(UTC).isoformat(),
        "project_id": None,
    }

    save_project_summary(conn, user_id, "projA", json.dumps(summary_with_key_role))

    monkeypatch.setattr(resume_flow, "collect_project_data", lambda c, u: [("projA", 1.0)])
    monkeypatch.setattr(helpers, "build_contribution_bullets", lambda c, u, p: [])
    monkeypatch.setattr("builtins.input", lambda _: "")

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    snap = get_resume_snapshot(conn, user_id, list_resumes(conn, user_id)[0]["id"])
    data = json.loads(snap["resume_json"])

    assert data["projects"][0]["key_role"] == "Backend Developer"


def test_create_resume_without_key_role(monkeypatch):
    """Test that resume snapshot works without key_role in contributions."""
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    user_id = 1

    # Summary without key_role
    save_project_summary(
        conn,
        user_id,
        "projA",
        _make_summary("projA", project_type="code", project_mode="individual"),
    )

    monkeypatch.setattr(resume_flow, "collect_project_data", lambda c, u: [("projA", 1.0)])
    monkeypatch.setattr(helpers, "build_contribution_bullets", lambda c, u, p: [])
    monkeypatch.setattr("builtins.input", lambda _: "")

    resume_flow._handle_create_resume(conn, user_id, "TestUser")

    snap = get_resume_snapshot(conn, user_id, list_resumes(conn, user_id)[0]["id"])
    data = json.loads(snap["resume_json"])

    # key_role should not be present when not set in source
    assert "key_role" not in data["projects"][0]


class TestCollectSectionUpdatesContributionBullets:
    """Tests for add-on vs rewrite choice in _collect_section_updates."""

    def test_add_on_mode_appends_bullets(self, monkeypatch):
        """When user selects '1' (add on), new bullets are appended to existing."""
        # Use manual_contribution_bullets - this is what resolve_resume_contribution_bullets checks
        project_entry = {
            "manual_contribution_bullets": ["Existing bullet 1", "Existing bullet 2"]
        }
        # Simulate: select mode "1", enter "New bullet", then empty line to finish
        inputs = iter(["1", "New bullet", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"contribution_bullets"}, project_entry)

        assert updates["contribution_bullets"] == [
            "Existing bullet 1",
            "Existing bullet 2",
            "New bullet",
        ]

    def test_add_on_mode_no_new_bullets_returns_none(self, monkeypatch):
        """When user selects add-on but enters no bullets, returns None."""
        project_entry = {
            "manual_contribution_bullets": ["Existing bullet"]
        }
        # Simulate: select mode "1", then immediately empty line (no new bullets)
        inputs = iter(["1", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"contribution_bullets"}, project_entry)

        assert updates["contribution_bullets"] is None

    def test_rewrite_mode_replaces_bullets(self, monkeypatch):
        """When user selects '2' (rewrite), bullets are completely replaced."""
        project_entry = {
            "manual_contribution_bullets": ["Old bullet 1", "Old bullet 2"]
        }
        # Simulate: select mode "2", enter new bullets, then empty line
        inputs = iter(["2", "New bullet A", "New bullet B", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"contribution_bullets"}, project_entry)

        assert updates["contribution_bullets"] == ["New bullet A", "New bullet B"]

    def test_invalid_mode_defaults_to_rewrite(self, monkeypatch):
        """When user enters invalid mode, defaults to rewrite behavior."""
        project_entry = {
            "manual_contribution_bullets": ["Old bullet"]
        }
        # Simulate: invalid mode "3", enter new bullet, then empty line
        inputs = iter(["3", "Replacement bullet", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"contribution_bullets"}, project_entry)

        assert updates["contribution_bullets"] == ["Replacement bullet"]

    def test_no_existing_contributions_uses_original_flow(self, monkeypatch):
        """When no existing contributions, uses simple input flow (no mode prompt)."""
        project_entry = {}  # No contribution_bullets
        # Simulate: just enter bullets directly (no mode selection needed)
        inputs = iter(["First bullet", "Second bullet", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"contribution_bullets"}, project_entry)

        assert updates["contribution_bullets"] == ["First bullet", "Second bullet"]

    def test_no_project_entry_uses_original_flow(self, monkeypatch):
        """When project_entry is None, uses simple input flow."""
        # Simulate: just enter bullets directly
        inputs = iter(["Bullet one", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"contribution_bullets"}, None)

        assert updates["contribution_bullets"] == ["Bullet one"]

    def test_manual_override_bullets_used_for_existing(self, monkeypatch):
        """Test that manual_contribution_bullets are resolved as existing bullets."""
        project_entry = {
            "manual_contribution_bullets": ["Manual bullet 1", "Manual bullet 2"]
        }
        # Simulate: select mode "1" (add on), enter new bullet, finish
        inputs = iter(["1", "Added bullet", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"contribution_bullets"}, project_entry)

        assert updates["contribution_bullets"] == [
            "Manual bullet 1",
            "Manual bullet 2",
            "Added bullet",
        ]

    def test_resume_override_bullets_take_priority(self, monkeypatch):
        """Test that resume_contributions_override takes priority over contribution_bullets."""
        project_entry = {
            "contribution_bullets": ["Base bullet"],
            "resume_contributions_override": ["Override bullet 1", "Override bullet 2"]
        }
        # Simulate: select mode "1" (add on), enter new bullet, finish
        inputs = iter(["1", "New bullet", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"contribution_bullets"}, project_entry)

        # Should use resume_contributions_override as the base
        assert updates["contribution_bullets"] == [
            "Override bullet 1",
            "Override bullet 2",
            "New bullet",
        ]

    def test_base_contribution_bullets_used_as_fallback(self, monkeypatch):
        """Test that contribution_bullets (base field) is used when no overrides exist."""
        project_entry = {
            "contribution_bullets": ["Base bullet 1", "Base bullet 2"]
        }
        # Simulate: select mode "1" (add on), enter new bullet, finish
        inputs = iter(["1", "New bullet", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"contribution_bullets"}, project_entry)

        # New bullet should be appended to the end
        assert updates["contribution_bullets"] == [
            "Base bullet 1",
            "Base bullet 2",
            "New bullet",
        ]


class TestKeyRoleInResume:
    """Tests for key role display and editing in resume snapshots."""

    def test_resolve_resume_key_role_returns_base(self):
        """Test that resolve_resume_key_role returns base key_role."""
        entry = {"key_role": "Backend Developer"}
        assert helpers.resolve_resume_key_role(entry) == "Backend Developer"

    def test_resolve_resume_key_role_manual_overrides_base(self):
        """Test that manual_key_role takes priority over base key_role."""
        entry = {
            "key_role": "Backend Developer",
            "manual_key_role": "Senior Backend Developer",
        }
        assert helpers.resolve_resume_key_role(entry) == "Senior Backend Developer"

    def test_resolve_resume_key_role_resume_overrides_all(self):
        """Test that resume_key_role_override takes highest priority."""
        entry = {
            "key_role": "Backend Developer",
            "manual_key_role": "Senior Backend Developer",
            "resume_key_role_override": "Lead Backend Engineer",
        }
        assert helpers.resolve_resume_key_role(entry) == "Lead Backend Engineer"

    def test_resolve_resume_key_role_returns_none_when_empty(self):
        """Test that resolve_resume_key_role returns None when no role set."""
        entry = {}
        assert helpers.resolve_resume_key_role(entry) is None

    def test_build_resume_snapshot_includes_key_role(self):
        """Test that build_resume_snapshot extracts key_role from contributions."""
        from src.models.project_summary import ProjectSummary

        ps = ProjectSummary(
            project_name="TestProject",
            project_type="code",
            project_mode="individual",
        )
        ps.contributions["key_role"] = "Full Stack Developer"

        snapshot = helpers.build_resume_snapshot([ps])

        assert len(snapshot["projects"]) == 1
        assert snapshot["projects"][0]["key_role"] == "Full Stack Developer"

    def test_build_resume_snapshot_without_key_role(self):
        """Test that build_resume_snapshot works without key_role."""
        from src.models.project_summary import ProjectSummary

        ps = ProjectSummary(
            project_name="TestProject",
            project_type="code",
            project_mode="individual",
        )

        snapshot = helpers.build_resume_snapshot([ps])

        assert len(snapshot["projects"]) == 1
        assert "key_role" not in snapshot["projects"][0]

    def test_apply_resume_only_updates_sets_key_role_override(self):
        """Test that apply_resume_only_updates sets resume_key_role_override."""
        entry = {"key_role": "Developer"}
        helpers.apply_resume_only_updates(entry, {"key_role": "Senior Developer"})

        assert entry["resume_key_role_override"] == "Senior Developer"
        assert entry["key_role"] == "Developer"  # Base unchanged

    def test_apply_resume_only_updates_clears_key_role_override(self):
        """Test that apply_resume_only_updates clears resume_key_role_override when None."""
        entry = {"key_role": "Developer", "resume_key_role_override": "Senior Developer"}
        helpers.apply_resume_only_updates(entry, {"key_role": None})

        assert "resume_key_role_override" not in entry
        assert entry["key_role"] == "Developer"  # Base unchanged

    def test_resume_only_override_fields_includes_key_role(self):
        """Test that resume_only_override_fields tracks key_role."""
        entry = {"resume_key_role_override": "Lead Developer"}
        fields = helpers.resume_only_override_fields(entry)

        assert "key_role" in fields

    def test_apply_manual_overrides_sets_manual_key_role(self):
        """Test that apply_manual_overrides sets manual_key_role."""
        entry = {}
        helpers.apply_manual_overrides(entry, {"key_role": "Tech Lead"})

        assert entry["manual_key_role"] == "Tech Lead"

    def test_collect_section_updates_key_role(self, monkeypatch):
        """Test that _collect_section_updates handles key_role input."""
        project_entry = {"key_role": "Developer"}
        # Simulate: enter new key role
        inputs = iter(["Senior Developer"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"key_role"}, project_entry)

        assert updates["key_role"] == "Senior Developer"

    def test_collect_section_updates_key_role_clear(self, monkeypatch):
        """Test that _collect_section_updates clears key_role when blank."""
        project_entry = {"key_role": "Developer"}
        # Simulate: enter blank (clear)
        inputs = iter([""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        updates = resume_flow._collect_section_updates({"key_role"}, project_entry)

        assert updates["key_role"] is None

    def test_prompt_edit_sections_includes_key_role(self, monkeypatch):
        """Test that _prompt_edit_sections includes key_role as option 4."""
        # Simulate: select option "4" for key_role
        monkeypatch.setattr("builtins.input", lambda _: "4")

        sections = resume_flow._prompt_edit_sections()

        assert "key_role" in sections

    def test_prompt_edit_sections_multiple_including_key_role(self, monkeypatch):
        """Test selecting multiple sections including key_role."""
        # Simulate: select options "1,4" for summary_text and key_role
        monkeypatch.setattr("builtins.input", lambda _: "1,4")

        sections = resume_flow._prompt_edit_sections()

        assert "summary_text" in sections
        assert "key_role" in sections
