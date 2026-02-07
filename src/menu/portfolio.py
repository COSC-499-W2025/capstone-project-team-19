"""
Menu option for viewing portfolio items.
- Ordered by existing project importance scores
- One compact "card" per project
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import get_project_summary_row
from src.insights.portfolio import (
    format_languages,
    format_frameworks,
    format_summary_block,
    resolve_portfolio_contribution_bullets,
    resolve_portfolio_display_name,
    resolve_portfolio_summary_text,
)
from src.export.portfolio_docx import export_portfolio_to_docx
from src.services.portfolio_service import (
    build_portfolio_data,
    update_portfolio_overrides,
    clear_portfolio_overrides_for_fields,
)
from src.services import resume_overrides
from src.export.portfolio_pdf import export_portfolio_to_pdf
_PLACEHOLDER_CONTRIB = "[No manual contribution summary provided]"

def _strip_placeholder_contrib(bullets: list[str]) -> list[str]:
    """Remove empty strings and the placeholder contribution text."""
    out = []
    for b in bullets or []:
        t = (b or "").strip()
        if not t:
            continue
        if t == _PLACEHOLDER_CONTRIB:
            continue
        out.append(t)
    return out

def view_portfolio_menu(conn, user_id: int, username: str) -> None:
    """
    Portfolio submenu with options to view, edit, and export.
    """
    while True:
        print("\nPortfolio options:")
        print("")
        print("1. View portfolio")
        print("2. Edit wording")
        print("3. Export to Word (.docx)")
        print("4. Export to PDF (.pdf)")
        print("5. Back to main menu")
        choice = input("Select an option (1-5): ").strip()

        if choice == "1":
            _display_portfolio(conn, user_id, username)
            print("")
            continue
        elif choice == "2":
            handled = _handle_edit_portfolio_wording(conn, user_id, username)
            if handled:
                print("")
                continue
        elif choice == "3":
            handled = _handle_export_portfolio(conn, user_id, username)
            if handled:
                print("")
                continue
        elif choice == "4":
            handled = _handle_export_portfolio_pdf(conn, user_id, username)
            if handled:
                print("")
                continue
        elif choice == "5":
            print("")
            return
        else:
            print("Invalid choice, please enter 1, 2, 3, 4, or 5.")


# Keep old function name as alias for backwards compatibility
def view_portfolio_items(conn, user_id: int, username: str) -> None:
    """
    Backwards-compatible alias for view_portfolio_menu.
    """
    view_portfolio_menu(conn, user_id, username)


def _display_portfolio(conn, user_id: int, username: str) -> bool:
    """
    Display the ranked portfolio view (no prompts).
    Returns True if portfolio was displayed, False if no projects.
    """
    try:
        projects = build_portfolio_data(conn, user_id)

        if not projects:
            print(f"\n{'=' * 80}")
            print("No projects found. Please analyze some projects first.")
            print(f"{'=' * 80}\n")
            return False

        print(f"\n{'=' * 80}")
        print(f"Portfolio view for {username}")
        print(f"{'=' * 80}\n")

        for rank, project in enumerate(projects, start=1):
            project_name = project["project_name"]
            project_type = project["project_type"]
            project_mode = project["project_mode"]

            row = get_project_summary_row(conn, user_id, project_name)
            summary = (row["summary"] or {}) if row else {}

            print(f"[{rank}] {project['display_name']} — Score {project['score']:.3f}")
            print(f"  Type: {project_type} ({project_mode})")
            print(f"  {project['duration']}")

            if project_type == "code":
                print(f"  {format_languages(summary)}")
                print(f"  {format_frameworks(summary)}")

            print(f"  {project['activity']}")

            # Skills block (bullets)
            if project["skills"]:
                print("  Skills:")
                for skill in project["skills"]:
                    print(f"    - {skill}")
            else:
                print("  Skills: N/A")

            # Summary block (LLM vs non-LLM)
            for line in format_summary_block(
                project_type, project_mode, summary, conn, user_id, project_name
            ):
                print(f"  {line}")

            print()  # blank line between projects

        print(f"{'=' * 80}\n")
        return True

    except Exception as e:
        print(f"Error displaying portfolio items: {e}")
        print(f"{'=' * 80}\n")
        return False


def _handle_export_portfolio(conn, user_id: int, username: str) -> bool:
    """
    Export the portfolio to a Word document.
    """
    project_scores = collect_project_data(conn, user_id)
    if not project_scores:
        print("No projects found. Please analyze some projects first.")
        return False

    out_file = export_portfolio_to_docx(conn, user_id, username, out_dir="./out")
    print(f"\nSaving portfolio to {out_file} ...")
    print("Export complete.\n")
    return True


def _prompt_edit_sections() -> set[str]:
    print("\nWhat would you like to edit?")
    print("1. Summary text")
    print("2. Contribution bullets")
    print("3. Display name")
    raw = input("Select one or more (e.g., 1,3) or press Enter to cancel: ").strip()
    if not raw:
        return set()
    selected: set[str] = set()
    for token in raw.replace(" ", "").split(","):
        if token == "1":
            selected.add("summary_text")
        elif token == "2":
            selected.add("contribution_bullets")
        elif token == "3":
            selected.add("display_name")
    return selected


def _collect_section_updates(
    sections: set[str],
    project_entry: dict,
    conn,
    user_id: int,
) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if "display_name" in sections:
        display_name = input("New display name (leave blank to clear): ").strip()
        updates["display_name"] = display_name or None
    if "summary_text" in sections:
        summary_text = input("New summary text (leave blank to clear): ").strip()
        updates["summary_text"] = summary_text or None
    if "contribution_bullets" in sections:
        current_bullets = resolve_portfolio_contribution_bullets(
            project_entry.get("summary") or {},
            project_entry.get("project_type") or "unknown",
            project_entry.get("project_mode") or "individual",
            conn,
            user_id,
            project_entry.get("project_name") or "",
        ) or []

        # If “current” is just the placeholder, treat as empty
        cleaned_current = _strip_placeholder_contrib(current_bullets)

        if cleaned_current:
            print("\nCurrent contributions:")
            for bullet in cleaned_current:
                print(f"  - {bullet}")

            print("\nHow would you like to edit?")
            print("1. Add on to existing contributions")
            print("2. Completely rewrite")
            mode = input("Select (1-2): ").strip()

            if mode == "1":
                print("\nEnter additional contribution bullets (one per line). Press Enter on a blank line to finish.")
                new_bullets: list[str] = []
                while True:
                    line = input("> ").strip()
                    if not line:
                        break
                    new_bullets.append(line)

                if new_bullets:
                    # append onto real bullets (placeholder already removed)
                    updates["contribution_bullets"] = cleaned_current + new_bullets
            else:
                print("\nEnter contribution bullets (one per line). Press Enter on a blank line to finish.")
                bullets: list[str] = []
                while True:
                    line = input("> ").strip()
                    if not line:
                        break
                    bullets.append(line)
                updates["contribution_bullets"] = bullets or None

        else:
            # No real contributions yet (or only placeholder) → behave like empty
            print("Enter contribution bullets (one per line). Press Enter on a blank line to finish.")
            bullets: list[str] = []
            while True:
                line = input("> ").strip()
                if not line:
                    break
                bullets.append(line)
            updates["contribution_bullets"] = bullets or None

    return updates


def _handle_edit_portfolio_wording(conn, user_id: int, username: str) -> bool:
    project_scores = collect_project_data(conn, user_id)
    if not project_scores:
        print("No projects found. Please analyze some projects first.")
        return False

    portfolio_entries: list[dict[str, Any]] = []
    print("\nProjects in this portfolio:")
    for project_name, score in project_scores:
        row = get_project_summary_row(conn, user_id, project_name)
        if row is None:
            continue
        summary = row.get("summary") or {}
        display = resolve_portfolio_display_name(summary, project_name)
        summary_text = resolve_portfolio_summary_text(summary) or ""
        preview = (summary_text[:60] + "...") if summary_text and len(summary_text) > 60 else summary_text
        suffix = f" — {preview}" if preview else ""
        portfolio_entries.append(
            {
                "project_name": project_name,
                "project_type": row.get("project_type") or summary.get("project_type"),
                "project_mode": row.get("project_mode") or summary.get("project_mode"),
                "summary": summary,
            }
        )
        print(f"{len(portfolio_entries)}. {display}{suffix}")

    if not portfolio_entries:
        print("No portfolio entries found to edit.")
        return False

    proj_choice = input("Select a project to edit (number) or press Enter to cancel: ").strip()
    if not proj_choice.isdigit():
        print("Cancelled.")
        return False

    idx = int(proj_choice)
    if idx < 1 or idx > len(portfolio_entries):
        print("Invalid selection.")
        return False

    project_entry = portfolio_entries[idx - 1]
    project_name = project_entry.get("project_name") or ""
    if not project_name:
        print("Selected project is missing a project name.")
        return False

    print("\nApply changes to:")
    print("1. This portfolio only")
    print("2. All resumes & portfolio")
    scope_choice = input("Select scope (1-2): ").strip()
    if scope_choice not in {"1", "2"}:
        print("Cancelled.")
        return False

    sections = _prompt_edit_sections()
    if not sections:
        print("Cancelled.")
        return False

    updates = _collect_section_updates(sections, project_entry, conn, user_id)
    if not updates:
        print("No updates provided.")
        return False

    if scope_choice == "1":
        overrides = update_portfolio_overrides(conn, user_id, project_name, updates)
        if overrides is None:
            print("Unable to update portfolio overrides.")
            return False
        print("[Portfolio] Updated wording for this portfolio.")
        return True

    manual_overrides = resume_overrides.update_project_manual_overrides(conn, user_id, project_name, updates)
    if manual_overrides is None:
        print("Unable to update project summary for global overrides.")
        return False

    # Clear portfolio-specific overrides for fields being updated globally,
    # so the global manual_overrides take effect (they have lower priority).
    clear_portfolio_overrides_for_fields(conn, user_id, project_name, set(updates.keys()))

    resume_overrides.apply_manual_overrides_to_resumes(
        conn,
        user_id,
        project_name,
        manual_overrides,
        set(updates.keys()),
        log_summary=True,
    )
    print("[Portfolio] Updated wording across resumes and portfolio.")
    return True

def _handle_export_portfolio_pdf(conn, user_id: int, username: str) -> bool:
    """
    Export the portfolio to a PDF document.
    """
    project_scores = collect_project_data(conn, user_id)
    if not project_scores:
        print("No projects found. Please analyze some projects first.")
        return False

    out_file = export_portfolio_to_pdf(conn, user_id, username, out_dir="./out")
    print(f"\nSaving portfolio to {out_file} ...")
    print("Export complete.\n")
    return True

_PLACEHOLDER_CONTRIB = "[No manual contribution summary provided]"

def _strip_placeholder_contrib(bullets: list[str]) -> list[str]:
    out = []
    for b in bullets or []:
        t = (b or "").strip()
        if not t:
            continue
        if t == _PLACEHOLDER_CONTRIB:
            continue
        out.append(t)
    return out
