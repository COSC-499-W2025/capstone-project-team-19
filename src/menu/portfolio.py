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
    format_duration,
    format_languages,
    format_frameworks,
    format_activity_line,
    format_skills_block,
    format_summary_block,
    resolve_portfolio_display_name,
)
from src.export.portfolio_docx import export_portfolio_to_docx

def view_portfolio_items(conn, user_id: int, username: str) -> None:
    """
    Display a ranked portfolio view for the user.
    """
    try:
        project_scores = collect_project_data(conn, user_id)

        if not project_scores:
            print(f"\n{'=' * 80}")
            print("No projects found. Please analyze some projects first.")
            print(f"{'=' * 80}\n")
            return

        print(f"\n{'=' * 80}")
        print(f"Portfolio view for {username}")
        print(f"{'=' * 80}\n")

        for rank, (project_name, score) in enumerate(project_scores, start=1):
            row = get_project_summary_row(conn, user_id, project_name)
            if row is None:
                continue

            summary = row["summary"]
            project_type = row.get("project_type") or summary.get("project_type") or "unknown"
            project_mode = row.get("project_mode") or summary.get("project_mode") or "individual"
            created_at = row.get("created_at") or ""

            display_name = resolve_portfolio_display_name(summary, project_name)
            print(f"[{rank}] {display_name} — Score {score:.3f}")
            print(f"  Type: {project_type} ({project_mode})")
            print(
                f"  {format_duration(project_type, project_mode, created_at, user_id, project_name, conn)}"
            )

            # Code: show languages + frameworks.
            if project_type == "code":
                print(f"  {format_languages(summary)}")
                print(f"  {format_frameworks(summary)}")

            # Activity (same for code/text)
            print(
                f"  {format_activity_line(project_type, project_mode, conn, user_id, project_name, summary)}"
            )

            # Skills block (bullets)
            for line in format_skills_block(summary):
                print(f"  {line}")

            # Summary block (LLM vs non-LLM)
            for line in format_summary_block(
                project_type, project_mode, summary, conn, user_id, project_name
            ):
                print(f"  {line}")

            print()  # blank line between projects

        print(f"{'=' * 80}\n")

        # --- Export prompt ---
        answer = input(
            "Do you want to export this portfolio to a Word document (.docx)? (y/n) "
        ).strip().lower()

        if answer == "y":
            out_file = export_portfolio_to_docx(conn, user_id, username, out_dir="./out")
            print(f"\nSaving portfolio to {out_file} ...")
            print("✓ Export complete.\n")
        else:
            print("\nReturning to main menu...\n")
            return

    except Exception as e:
        print(f"Error displaying portfolio items: {e}")
        print(f"{'=' * 80}\n")
