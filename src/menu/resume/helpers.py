"""
src/menu/resume/helpers.py

Helper functions for building and rendering resume snapshots.
"""
import json
from typing import List, Dict, Any

from src.models.project_summary import ProjectSummary
from typing import Any, Dict, List

from src.db.code_activity import get_code_activity_percents, get_normalized_code_metrics


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
    lines = [f"\n- {p.get('project_name', 'Unnamed project')}"]

    langs = p.get("languages") or []
    fws = p.get("frameworks") or []
    if langs:
        lines.append(f"  Languages: {', '.join(sorted(set(langs)))}")
    if fws:
        lines.append(f"  Frameworks: {', '.join(sorted(set(fws)))}")

    if p.get("project_type") == "text":
        lines.append(f"  Type: {p.get('text_type', 'Text')}")
    if p.get("summary_text"):
        lines.append(f"  Summary: {p['summary_text']}")

    # Contributions
    if p.get("project_type") == "code":
        project_name = p.get("project_name") or ""
        is_collab = bool(p.get("is_collaborative") or p.get("project_mode") == "collaborative")

        activity_label = {
            "feature_coding": "feature implementation",
            "refactoring": "refactoring",
            "debugging": "debugging",
            "testing": "testing",
            "documentation": "documentation",
        }

        lines.append("  Contributions:")

        if conn and user_id is not None and project_name:
            metrics = get_normalized_code_metrics(conn, user_id, project_name, is_collab)
            activities = get_code_activity_percents(conn, user_id, project_name, source="combined")

            if metrics:
                total_commits = int(metrics["total_commits"])
                your_commits = int(metrics["your_commits"])
                loc_added = int(metrics["loc_added"])
                loc_deleted = int(metrics["loc_deleted"])
                loc_net = int(metrics["loc_net"])

                share = (your_commits / total_commits * 100.0) if total_commits > 0 else 0.0

                # Top 3 activities for the “across workflows” phrase
                top_acts = [(k, v) for k, v in sorted(activities.items(), key=lambda kv: kv[1], reverse=True) if v > 0.0][:3]
                workflows = ", ".join(activity_label.get(k, k.replace("_", " ")) for k, _ in top_acts) if top_acts else "core development"

                # Template-style bullets
                if is_collab:
                    lines.append(
                        f"    • Contributed {share:.1f}% of total repository commits ({your_commits} commits) "
                        f"across {workflows} workflows."
                    )
                else:
                    lines.append(
                        f"    • Delivered {your_commits} commits across {workflows} workflows in an individual codebase."
                    )

                lines.append(
                    f"    • Delivered a net code contribution of {loc_net:+d} lines, adding {loc_added} and deleting {loc_deleted}, "
                    f"demonstrating an emphasis on maintainability and code quality."
                )

                feat = float(activities.get("feature_coding") or 0.0)
                refac = float(activities.get("refactoring") or 0.0)
                debug = float(activities.get("debugging") or 0.0)
                test = float(activities.get("testing") or 0.0)
                doc = float(activities.get("documentation") or 0.0)

                if feat > 0.0:
                    lines.append(
                        f"    • Focused {feat:.1f}% of development effort on feature implementation, translating requirements into production-ready code."
                    )
                if refac > 0.0:
                    lines.append(
                        f"    • Allocated {refac:.1f}% of contributions to refactoring, improving readability, modularity, and long-term maintainability."
                    )
                if debug > 0.0:
                    lines.append(
                        f"    • Dedicated {debug:.1f}% of activity to debugging, identifying root causes and resolving runtime and logic issues."
                    )
                if (test + doc) > 0.0:
                    lines.append(
                        f"    • Contributed to testing and documentation ({(test + doc):.1f}% combined), supporting code reliability and team onboarding."
                    )
            else:
                lines.append("    • (no metrics found in code_collaborative_metrics / git_individual_metrics)")
        else:
            lines.append("    • (missing conn/user_id/project_name; cannot load metrics)")

    elif p.get("project_type") == "text":
        pct = p.get("contribution_percent")
        if isinstance(pct, (int, float)):
            lines.append(f"  Contribution: {pct:.1f}% of document")

    # Skills
    skills = p.get("skills") or []
    if skills:
        lines.append("  Skills:")
        lines.append("    • " + ", ".join(skills))


    return lines



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
