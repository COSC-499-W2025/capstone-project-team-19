import textwrap
from typing import List, Dict, Any, Optional


NO_FEEDBACK_MSG = (
    "No feedback found for this project yet. "
)

_ACRONYMS = {"ci", "api", "db", "ui", "ml", "ai", "sql", "jwt"}

def _format_category(name: str) -> str:
    """
    Format DB category keys into user-friendly headings.
    Examples:
      "object_oriented_programming" -> "Object Oriented Programming"
      "ci_workflows" -> "CI Workflows"
      "" -> "General"
    """
    if not name or not name.strip():
        return "General"

    cleaned = name.strip().replace("_", " ").replace("-", " ")
    cleaned = " ".join(cleaned.split())  # collapse extra whitespace

    words = []
    for w in cleaned.split(" "):
        wl = w.lower()
        if wl in _ACRONYMS:
            words.append(w.upper())
        else:
            # capitalize first letter, keep rest lowercase
            words.append(w.capitalize())

    return " ".join(words)

# --------------------------------------------------------------------
# DB helpers (inline so this script works even if you don't have these yet)
# --------------------------------------------------------------------

def get_projects_list_for_feedback(conn, user_id: int) -> List[Dict[str, Any]]:
    """
    Reuses project_summaries if you want, but this works standalone by reading project_summaries table.
    If your project list is sourced elsewhere, swap this query.
    """
    rows = conn.execute(
        """
        SELECT
            project_name,
            project_type,
            project_mode,
            created_at
        FROM project_summaries
        WHERE user_id = ?
        ORDER BY datetime(created_at) DESC
        """,
        (user_id,),
    ).fetchall()

    return [
        {
            "project_name": r[0],
            "project_type": r[1],
            "project_mode": r[2],
            "created_at": r[3],
        }
        for r in rows
    ]


def get_project_feedback_suggestions(conn, user_id: int, project_name: str) -> List[Dict[str, Any]]:
    """
    Pull all feedback rows for a given project.
    We print only 'suggestion', grouped by skill_name.
    """
    try:
        rows = conn.execute(
            """
            SELECT
                COALESCE(skill_name, '') AS skill_name,
                COALESCE(suggestion, '') AS suggestion
            FROM project_feedback
            WHERE user_id = ?
              AND project_name = ?
            ORDER BY skill_name COLLATE NOCASE, suggestion COLLATE NOCASE
            """,
            (user_id, project_name),
        ).fetchall()

        return [{"skill_name": r[0] or "", "suggestion": r[1] or ""} for r in rows]

    except Exception:
        # Minimal fallback: only suggestion
        rows = conn.execute(
            """
            SELECT COALESCE(suggestion, '') AS suggestion
            FROM project_feedback
            WHERE user_id = ?
              AND project_name = ?
            """,
            (user_id, project_name),
        ).fetchall()

        return [{"skill_name": "", "suggestion": r[0] or ""} for r in rows]


# --------------------------------------------------------------------
# Menu item
# --------------------------------------------------------------------

def view_project_feedback(conn, user_id: int, username: str):
    """
    Display feedback suggestions for previously analyzed projects.
    Mirrors view_old_project_summaries UX.
    """
    while True:
        print("\n" + "=" * 60)
        print("VIEW FEEDBACK")
        print("=" * 60)

        projects = get_projects_list_for_feedback(conn, user_id)

        if not projects:
            print(f"\nNo projects found for {username}.")
            print("You haven't analyzed any projects yet.")
            input("\nPress Enter to return to main menu...")
            return None

        print(f"\n{username}'s Projects List:\n")
        for idx, p in enumerate(projects, start=1):
            project_type = p.get("project_type") or "unknown"
            project_mode = p.get("project_mode") or "unknown"
            created_at = p.get("created_at")
            print(f"{idx}. {p['project_name']} ({project_mode} {project_type} Project, Analyzed: {created_at})")

        if len(projects) == 1:
            display_project_feedback(conn, user_id, projects[0]["project_name"])
            input("\nPress Enter to return to main menu...")
            return None

        print("\n" + "-" * 60)
        choice = input(
            f"\nEnter the number (1-{len(projects)}) to view feedback, or 'q' to quit: "
        ).strip().lower()

        if choice == "q":
            print("\nReturning to main menu...")
            return None

        try:
            idx = int(choice)
            if 1 <= idx <= len(projects):
                selected_project = projects[idx - 1]
                display_project_feedback(conn, user_id, selected_project["project_name"])

                print("\n" + "-" * 60)
                continue_choice = input("\nView feedback for another project? (y/n): ").strip().lower()
                if continue_choice not in {"y", "yes"}:
                    print("\nReturning to main menu...")
                    return None
            else:
                print(f"Please enter a number between 1 and {len(projects)}.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")


def display_project_feedback(conn, user_id: int, project_name: str):
    """
    Display all feedback suggestions for a specific project.
    """
    rows = get_project_feedback_suggestions(conn, user_id, project_name)

    print("\n" + "=" * 60)
    print(f"PROJECT FEEDBACK: {project_name}")
    print("=" * 60)

    if not rows:
        print("\n" + NO_FEEDBACK_MSG)
        return

    # Grouping is only by skill_name now
    has_grouping = any((r.get("skill_name") or "").strip() for r in rows)

    print("\n" + "-" * 60)
    print("SUGGESTIONS:")
    print("-" * 60)

    if not has_grouping:
        for r in rows:
            suggestion = (r.get("suggestion") or "").strip()
            if not suggestion:
                continue
            print(textwrap.fill(f"• {suggestion}", width=80, subsequent_indent="  "))
        return

    current_group = None
    for r in rows:
        skill_name = (r.get("skill_name") or "").strip()
        suggestion = (r.get("suggestion") or "").strip()
        if not suggestion:
            continue

        group_header = _format_category(skill_name)

        if group_header != current_group:
            current_group = group_header
            print(f"\n{current_group}:")

        print(textwrap.fill(f"• {suggestion}", width=80, subsequent_indent="  "))