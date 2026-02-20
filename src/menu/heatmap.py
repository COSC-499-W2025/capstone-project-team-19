import os
import sys
import subprocess
from typing import Optional

from src.analysis.visualizations.activity_heatmap import write_project_activity_heatmap


def _open_image(path: str) -> None:
    try:
        if sys.platform.startswith("darwin"):
            subprocess.run(["open", path], check=False)
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception:
        pass


def view_activity_heatmap(conn, user_id: int) -> None:
    """
    CLI: pick a project -> generate cached activity heatmap PNG -> open it.
    """
    rows = conn.execute(
        """
        SELECT display_name, project_type
        FROM projects
        WHERE user_id = ?
        ORDER BY display_name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()

    if not rows:
        print("\nNo projects found.\n")
        return

    print("\nProjects:")
    for i, (name, ptype) in enumerate(rows, start=1):
        print(f"{i}. {name} ({ptype or 'unknown'})")

    choice = input("\nSelect a project number (or press Enter to cancel): ").strip()
    if not choice:
        return
    if not choice.isdigit() or not (1 <= int(choice) <= len(rows)):
        print("Invalid selection.\n")
        return

    project_name = rows[int(choice) - 1][0]

    mode = input("Heatmap mode: (d)iff per version or (s)napshot per version? [d]: ").strip().lower()
    mode = "snapshot" if mode == "s" else "diff"

    try:
        out_path = write_project_activity_heatmap(
            conn,
            user_id,
            project_name,
            mode=mode,          # "diff" recommended
            normalize=True,     # % per version column
        )
    except Exception as e:
        print(f"\nFailed to generate heatmap: {e}\n")
        return

    print(f"\nSaved heatmap to:\n  {out_path}\n")
    _open_image(out_path)