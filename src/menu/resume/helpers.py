"""
src/menu/resume/helpers.py

Helper functions for building and rendering resume snapshots.
"""
import json
from typing import List, Dict, Any
from src.models.project_summary import ProjectSummary
from typing import Any, Dict, List
from src.db.code_activity import get_code_activity_percents, get_normalized_code_metrics
from src.db import get_classification_id
from src.db.text_activity import get_text_activity_contribution


def _clean_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _clean_bullets(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    cleaned: List[str] = []
    for item in values:
        text = str(item).strip()
        if not text:
            continue
        if text.startswith(("-", "•")):
            text = text.lstrip("-•").strip()
        if text:
            cleaned.append(text)
    return cleaned


def resolve_resume_display_name(entry: Dict[str, Any]) -> str:
    resume_name = _clean_str(entry.get("resume_display_name_override"))
    if resume_name:
        return resume_name
    manual_name = _clean_str(entry.get("manual_display_name"))
    if manual_name:
        return manual_name
    return entry.get("project_name") or "Unnamed project"


def resolve_resume_summary_text(entry: Dict[str, Any]) -> str | None:
    summary_override = _clean_str(entry.get("resume_summary_override"))
    if summary_override:
        return summary_override
    manual_summary = _clean_str(entry.get("manual_summary_text"))
    if manual_summary:
        return manual_summary
    return _clean_str(entry.get("summary_text"))


def resolve_resume_contribution_bullets(entry: Dict[str, Any]) -> List[str]:
    resume_bullets = _clean_bullets(entry.get("resume_contributions_override"))
    if resume_bullets:
        return resume_bullets
    manual_bullets = _clean_bullets(entry.get("manual_contribution_bullets"))
    if manual_bullets:
        return manual_bullets
    return []


def resume_only_override_fields(entry: Dict[str, Any]) -> set[str]:
    fields: set[str] = set()
    if _clean_str(entry.get("resume_display_name_override")):
        fields.add("display_name")
    if _clean_str(entry.get("resume_summary_override")):
        fields.add("summary_text")
    if _clean_bullets(entry.get("resume_contributions_override")):
        fields.add("contribution_bullets")
    return fields


def has_resume_only_overrides(entry: Dict[str, Any], fields: set[str] | None = None) -> bool:
    overrides = resume_only_override_fields(entry)
    if not overrides:
        return False
    if fields is None:
        return True
    return bool(overrides & fields)


def apply_resume_only_updates(entry: dict, updates: dict[str, Any]) -> None:
    # Apply resume-only overrides to a single snapshot entry.
    if "display_name" in updates:
        if updates["display_name"]:
            entry["resume_display_name_override"] = updates["display_name"]
        else:
            entry.pop("resume_display_name_override", None)
    if "summary_text" in updates:
        if updates["summary_text"]:
            entry["resume_summary_override"] = updates["summary_text"]
        else:
            entry.pop("resume_summary_override", None)
    if "contribution_bullets" in updates:
        if updates["contribution_bullets"]:
            entry["resume_contributions_override"] = updates["contribution_bullets"]
        else:
            entry.pop("resume_contributions_override", None)


def apply_manual_overrides(entry: Dict[str, Any], overrides: Dict[str, Any]) -> None:
    if not isinstance(overrides, dict):
        return
    display_name = _clean_str(overrides.get("display_name"))
    if display_name:
        entry["manual_display_name"] = display_name
    summary_text = _clean_str(overrides.get("summary_text"))
    if summary_text:
        entry["manual_summary_text"] = summary_text
    bullets = _clean_bullets(overrides.get("contribution_bullets"))
    if bullets:
        entry["manual_contribution_bullets"] = bullets



def load_project_summaries(conn, user_id: int, get_all_user_project_summaries) -> List[ProjectSummary]:
    """Fetch and deserialize all saved project summaries for the user."""
    rows = get_all_user_project_summaries(conn, user_id)
    projects: List[ProjectSummary] = []

    for row in rows:
        try:
            summary_dict = json.loads(row["summary_json"])
            projects.append(ProjectSummary.from_dict(summary_dict))
        except Exception:
            # Skip malformed entries to avoid breaking the resume flow.
            continue

    return projects


def build_resume_snapshot(summaries: List[ProjectSummary]) -> Dict[str, Any]:
    """Build a structured snapshot of resume data from project summaries."""
    projects = []
    for ps in summaries:
        entry: Dict[str, Any] = {
            "project_name": ps.project_name,
            "project_type": ps.project_type,
            "project_mode": ps.project_mode,
            "languages": ps.languages or [],
            "frameworks": ps.frameworks or [],
            "summary_text": ps.summary_text,
            "skills": _extract_skills(ps, map_labels=True),
        }
        if ps.manual_overrides:
            apply_manual_overrides(entry, ps.manual_overrides)

        if ps.project_type == "text":
            entry["text_type"] = "Academic writing"
            if ps.project_mode == "collaborative":
                text_collab = ps.contributions.get("text_collab")
                if isinstance(text_collab, dict):
                    pct = text_collab.get("percent_of_document")
                    if isinstance(pct, (int, float)):
                        entry["contribution_percent"] = pct
                    collab_skills = text_collab.get("skills")
                    if isinstance(collab_skills, list) and collab_skills:
                        entry["skills"] = collab_skills
        else:  # code
            entry["activities"] = _extract_activity(ps)

        projects.append(entry)

    agg = _aggregate_skills(summaries)
    return {"projects": projects, "aggregated_skills": agg}


def render_snapshot(
    conn,
    user_id: int,
    snapshot: Dict[str, Any],
    print_output: bool = True,
) -> str:
    """Render a snapshot to text; optionally print to console."""
    lines: List[str] = []

    projects = snapshot.get("projects", [])
    # Group by type/mode
    groups = {
        ("code", "individual"): "=== Code Projects (Individual) ===",
        ("code", "collaborative"): "=== Code Projects (Collaborative) ===",
        ("text", "individual"): "=== Text Projects (Individual) ===",
        ("text", "collaborative"): "=== Text Projects (Collaborative) ===",
    }

    for (ptype, pmode), header in groups.items():
        group_entries = [p for p in projects if p.get("project_type") == ptype and p.get("project_mode") == pmode]
        if not group_entries:
            continue
        lines.append("")
        lines.append(header)
        for p in group_entries:
            lines.extend(_render_project_block(conn, user_id, p))

    agg = snapshot.get("aggregated_skills", {})
    skills_lines = []
    if agg.get("languages"):
        skills_lines.append(f"Languages: {', '.join(sorted(set(agg['languages'])))}")
    if agg.get("frameworks"):
        skills_lines.append(f"Frameworks: {', '.join(sorted(set(agg['frameworks'])))}")
    if agg.get("technical_skills"):
        skills_lines.append(f"Technical skills: {', '.join(sorted(set(agg['technical_skills'])))}")
    if agg.get("writing_skills"):
        skills_lines.append(f"Writing skills: {', '.join(sorted(set(agg['writing_skills'])))}")

    if skills_lines:
        lines.append("")
        lines.append("=== Skills Summary ===")
        lines.extend(skills_lines)

    rendered = "\n".join(lines).strip() + "\n"
    if print_output:
        print("\n" + rendered)
    return rendered


def _render_project_block(conn, user_id: int, p: Dict[str, Any]) -> List[str]:
    lines = [f"\n- {resolve_resume_display_name(p)}"]

    langs = p.get("languages") or []
    fws = p.get("frameworks") or []
    if langs:
        lines.append(f"  Languages: {', '.join(sorted(set(langs)))}")
    if fws:
        lines.append(f"  Frameworks: {', '.join(sorted(set(fws)))}")

    if p.get("project_type") == "text":
        lines.append(f"  Type: {p.get('text_type', 'Text')}")
    summary_text = resolve_resume_summary_text(p)
    if summary_text:
        lines.append(f"  Summary: {summary_text}")

    # Contributions (single source of truth = stored bullets, else compute)
    lines.append("  Contributions:")
    # Contributions
    custom_bullets = resolve_resume_contribution_bullets(p)
    if custom_bullets:
        lines.append("  Contributions:")
        for bullet in custom_bullets:
            lines.append(f"    • {bullet}")
    elif p.get("project_type") == "code":
        project_name = p.get("project_name") or ""
        is_collab = bool(p.get("is_collaborative") or p.get("project_mode") == "collaborative")

    bullets = p.get("contribution_bullets")
    if not isinstance(bullets, list) or not bullets:
        if conn and user_id is not None:
            bullets = build_contribution_bullets(conn, user_id, p)
        else:
            bullets = []

    if bullets:
        for b in bullets:
            lines.append(f"    • {str(b).strip()}")
    else:
        lines.append("    • (no contribution bullets available)")

    # Skills
    skills = p.get("skills") or []
    if skills:
        lines.append("  Skills:")
        lines.append("    • " + ", ".join(skills))

    return lines


def build_contribution_bullets(
    conn,
    user_id: int,
    project: Dict[str, Any],
) -> List[str]:
    """
    Build contribution bullet strings for a single project.
    Unlike _render_project_block (which renders the full CLI project section),
    this returns only the contribution bullet texts for storing/exporting.
    """
    if not conn or user_id is None:
        return []

    ptype = project.get("project_type")
    project_name = project.get("project_name") or ""
    if not project_name:
        return []

    bullets: List[str] = []

    # ---------------------------
    # CODE PROJECTS
    # ---------------------------
    if ptype == "code":
        is_collab = bool(project.get("is_collaborative") or project.get("project_mode") == "collaborative")

        metrics = get_normalized_code_metrics(conn, user_id, project_name, is_collab)
        activities = get_code_activity_percents(conn, user_id, project_name, source="combined") or {}

        if not metrics:
            return ["(no metrics found in code_collaborative_metrics / git_individual_metrics)"]

        # Guard against missing keys
        total_commits = int(metrics.get("total_commits") or 0)
        your_commits = int(metrics.get("your_commits") or 0)
        loc_added = int(metrics.get("loc_added") or 0)
        loc_deleted = int(metrics.get("loc_deleted") or 0)
        loc_net = int(metrics.get("loc_net") or 0)

        share = (your_commits / total_commits * 100.0) if total_commits > 0 else 0.0

        activity_label = {
            "feature_coding": "feature implementation",
            "refactoring": "refactoring",
            "debugging": "debugging",
            "testing": "testing",
            "documentation": "documentation",
        }

        # Top 3 non-zero activities
        ranked = sorted(
            ((k, float(v or 0.0)) for k, v in activities.items()),
            key=lambda kv: kv[1],
            reverse=True,
        )
        top_acts = [(k, v) for k, v in ranked if v > 0.0][:3]
        workflows = ", ".join(activity_label.get(k, k.replace("_", " ")) for k, _ in top_acts) if top_acts else "core development"

        if is_collab:
            bullets.append(
                f"Contributed {share:.1f}% of total repository commits ({your_commits} commits) across {workflows} workflows."
            )
        else:
            bullets.append(
                f"Delivered {your_commits} commits across {workflows} workflows in an individual codebase."
            )

        bullets.append(
            f"Delivered a net code contribution of {loc_net:+d} lines, adding {loc_added} and deleting {loc_deleted}, "
            f"demonstrating an emphasis on maintainability and code quality."
        )

        feat = float(activities.get("feature_coding") or 0.0)
        refac = float(activities.get("refactoring") or 0.0)
        debug = float(activities.get("debugging") or 0.0)
        test = float(activities.get("testing") or 0.0)
        doc = float(activities.get("documentation") or 0.0)

        if feat > 0.0:
            bullets.append(
                f"Focused {feat:.1f}% of development effort on feature implementation, translating requirements into production-ready code."
            )
        if refac > 0.0:
            bullets.append(
                f"Allocated {refac:.1f}% of contributions to refactoring, improving readability, modularity, and long-term maintainability."
            )
        if debug > 0.0:
            bullets.append(
                f"Dedicated {debug:.1f}% of activity to debugging, identifying root causes and resolving runtime and logic issues."
            )
        if (test + doc) > 0.0:
            bullets.append(
                f"Contributed to testing and documentation ({(test + doc):.1f}% combined), supporting code reliability and team onboarding."
            )

        return bullets

    # ---------------------------
    # TEXT PROJECTS
    # ---------------------------
    if ptype == "text":
        pct = project.get("contribution_percent")

        if isinstance(pct, (int, float)):
            bullets.append(f"Contributed to {pct:.1f}% of the project deliverables.")

        classification_id = project.get("classification_id") or get_classification_id(conn, user_id, project_name)
        row = get_text_activity_contribution(conn, classification_id) if classification_id else None

        if not row:
            if not bullets:
                bullets.append("(no activity breakdown found in text_activity_contribution)")
            return bullets

        summary = row.get("summary", {}) or {}
        counts = summary.get("activity_counts", {}) or {}
        duration_days = (row.get("timestamp_analysis", {}) or {}).get("duration_days")

        if isinstance(duration_days, int) and duration_days > 0:
            bullets.append(f"Worked across a {duration_days}-day timeline.")

        total_events = sum(int(v or 0) for v in counts.values())
        if total_events > 0:
            ranked = sorted(counts.items(), key=lambda kv: int(kv[1] or 0), reverse=True)
            top = [(k, int(v or 0)) for k, v in ranked if int(v or 0) > 0][:3]

            if len(top) >= 2:
                (a1, c1), (a2, c2) = top[0], top[1]
                p1 = c1 / total_events * 100.0
                p2 = c2 / total_events * 100.0

                if len(top) >= 3:
                    a3, c3 = top[2]
                    p3 = c3 / total_events * 100.0
                    bullets.append(
                        f"Balanced {str(a1).lower()} ({p1:.1f}%) with {str(a2).lower()} ({p2:.1f}%), and {str(a3).lower()} ({p3:.1f}%), "
                        f"supporting both content development and iterative improvement."
                    )
                else:
                    bullets.append(
                        f"Balanced {str(a1).lower()} ({p1:.1f}%) with {str(a2).lower()} ({p2:.1f}%), supporting both content development and iterative improvement."
                    )

            for stage in ("Revision", "Final"):
                if int(counts.get(stage, 0) or 0) > 0:
                    bullets.append(
                        f"Contributed to {stage.lower()}-stage work, strengthening clarity, structure, and polish."
                    )
                    break

        if not bullets:
            bullets.append("(no activity breakdown found in text_activity_contribution)")
        return bullets

    return []

def _extract_activity(ps: ProjectSummary) -> List[Dict[str, Any]]:
    activity = None
    if ps.project_mode == "collaborative":
        activity = ps.contributions.get("activity_type")
    activity = activity or ps.metrics.get("activity_type")
    if not isinstance(activity, dict):
        return []

    items = []
    for k, v in activity.items():
        top_file = v.get("top_file") or v.get("top_file_overall")
        items.append({"name": k, "top_file": top_file})
    return items


def _extract_skills(ps: ProjectSummary, map_labels: bool = False) -> List[str]:
    skills = ps.metrics.get("skills_detailed")
    tech_skill_map = {
        "architecture_and_design": "Architecture & design",
        "data_structures": "Data structures",
        "frontend_skills": "Frontend development",
        "object_oriented_programming": "Object-oriented programming",
        "security_and_error_handling": "Security & error handling",
        "testing_and_ci": "Testing & CI",
        "algorithms": "Algorithms",
        "backend_development": "Backend development",
        "clean_code_and_quality": "Clean code & quality",
        "devops_and_ci_cd": "DevOps & CI/CD",
    }
    writing_skill_map = {
        "clarity": "Clear communication",
        "structure": "Structured writing",
        "vocabulary": "Strong vocabulary",
        "argumentation": "Analytical writing",
        "depth": "Critical thinking",
        "process": "Revision & editing",
        "planning": "Planning & organization",
        "research": "Research integration",
        "data_collection": "Data collection",
        "data_analysis": "Data analysis",
    }
    if isinstance(skills, list):
        names = [s.get("skill_name") for s in skills if isinstance(s, dict) and s.get("skill_name")]
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for n in names:
            if n not in seen:
                seen.add(n)
                if map_labels:
                    mapped = writing_skill_map.get(n) or tech_skill_map.get(n) or n
                    unique.append(mapped)
                else:
                    unique.append(n)
        return unique
    return []


def _aggregate_skills(summaries: List[ProjectSummary]) -> Dict[str, List[str]]:
    langs = set()
    frameworks = set()
    tech_skills = set()
    writing_skills = set()

    tech_skill_map = {
        "architecture_and_design": "Architecture & design",
        "data_structures": "Data structures",
        "frontend_skills": "Frontend development",
        "object_oriented_programming": "Object-oriented programming",
        "security_and_error_handling": "Security & error handling",
        "testing_and_ci": "Testing & CI",
        "algorithms": "Algorithms",
        "backend_development": "Backend development",
        "clean_code_and_quality": "Clean code & quality",
        "devops_and_ci_cd": "DevOps & CI/CD",
    }

    writing_skill_map = {
        "clarity": "Clear communication",
        "structure": "Structured writing",
        "vocabulary": "Strong vocabulary",
        "argumentation": "Analytical writing",
        "depth": "Critical thinking",
        "process": "Revision & editing",
        "planning": "Planning & organization",
        "research": "Research integration",
        "data_collection": "Data collection",
        "data_analysis": "Data analysis",
    }

    for ps in summaries:
        langs.update(ps.languages or [])
        frameworks.update(ps.frameworks or [])
        skills = _extract_skills(ps)
        for s in skills:
            if s in writing_skill_map:
                writing_skills.add(writing_skill_map[s])
            else:
                tech_skills.add(tech_skill_map.get(s, s))

    return {
        "languages": sorted(langs),
        "frameworks": sorted(frameworks),
        "technical_skills": sorted(tech_skills),
        "writing_skills": sorted(writing_skills),
    }

def enrich_snapshot_with_contributions(conn, user_id: int, snapshot: Dict[str, Any]) -> Dict[str, Any]:
    projects = snapshot.get("projects") or []
    for p in projects:
        if conn and user_id is not None:
            p["contribution_bullets"] = build_contribution_bullets(conn, user_id, p)
        else:
            p["contribution_bullets"] = []
    return snapshot