from __future__ import annotations

from pathlib import Path
import os

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import (
    upsert_project_thumbnail,
    get_project_thumbnail_path,
    delete_project_thumbnail,
)
from src.utils.image_utils import validate_image_path, save_standardized_thumbnail


def _select_project_from_ranked_list(conn, user_id: int) -> str | None:
    project_scores = collect_project_data(conn, user_id)
    if not project_scores:
        print("\nNo projects found. Analyze some projects first.\n")
        return None

    print("\nSelect a project:")
    for i, (project_name, score) in enumerate(project_scores, start=1):
        print(f"{i}. {project_name} (Score {score:.3f})")

    while True:
        choice = input("\nEnter project number (or 'b' to go back): ").strip().lower()
        if choice == "b":
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(project_scores):
                return project_scores[idx - 1][0]
        print("Invalid selection. Try again.")


def _show_image(image_path: str) -> None:
    img = mpimg.imread(image_path)
    plt.figure()
    plt.imshow(img)
    plt.axis("off")
    plt.title(Path(image_path).name)
    plt.show()


def manage_project_thumbnails(conn, user_id: int, username: str) -> None:
    images_dir = Path("./images")

    while True:
        print("\n" + "=" * 80)
        print("Project Thumbnails")
        print("=" * 80)
        print("1. Add thumbnail to a project")
        print("2. Replace / edit project thumbnail")
        print("3. View project thumbnail")
        print("4. Remove project thumbnail")
        print("5. Back to main menu")

        action = input("\nSelect an option (1-5): ").strip()

        if action == "5":
            print("\nReturning to main menu...\n")
            return

        if action not in {"1", "2", "3", "4"}:
            print("Invalid choice. Please enter 1-5.")
            continue

        if action == "1":  # Add
            project_name = _select_project_from_ranked_list(conn, user_id)
        else:  # Replace / View / Remove
            project_name = _select_project_with_thumbnail(conn, user_id)

        if project_name is None:
            continue

        existing = get_project_thumbnail_path(conn, user_id, project_name)

        if action == "1":
            print(
                "Note: Images are automatically resized to a maximum of 800×800 px "
                "for best compatibility in exports."
            )

            raw_path = input("Enter image path: ").strip()
            try:
                src = validate_image_path(raw_path)
                dst = save_standardized_thumbnail(src, images_dir, user_id, project_name)
                upsert_project_thumbnail(conn, user_id, project_name, str(dst))
                print(f"\n✓ Thumbnail added for '{project_name}' -> {dst}\n")
            except Exception as e:
                print(f"\nFailed to add thumbnail: {e}\n")

        elif action == "2":
            raw_path = input("Enter new image path: ").strip()
            try:
                src = validate_image_path(raw_path)
                dst = save_standardized_thumbnail(src, images_dir, user_id, project_name)
                upsert_project_thumbnail(conn, user_id, project_name, str(dst))
                print(f"\n✓ Thumbnail updated for '{project_name}' -> {dst}\n")
            except Exception as e:
                print(f"\nFailed to update thumbnail: {e}\n")

        elif action == "3":
            if not existing or not Path(existing).exists():
                print(f"\nNo thumbnail found for '{project_name}'.\n")
                continue
            try:
                _show_image(existing)
            except Exception as e:
                print(f"\nFailed to display image: {e}\n")

        elif action == "4":
            if not existing:
                print(f"\nNo thumbnail to remove for '{project_name}'.\n")
                continue
            confirm = input(f"Remove thumbnail for '{project_name}'? (y/n): ").strip().lower()
            if confirm != "y":
                print("\nCancelled.\n")
                continue

            ok = delete_project_thumbnail(conn, user_id, project_name)
            if ok:
                # optional: delete managed file if it's in ./images
                try:
                    p = Path(existing)
                    if p.exists() and p.parent.resolve() == images_dir.resolve():
                        os.remove(p)
                except Exception:
                    pass
                print(f"\n✓ Thumbnail removed for '{project_name}'.\n")
            else:
                print("\nNothing removed.\n")

def _select_project_with_thumbnail(conn, user_id: int) -> str | None:
    projects = []
    project_scores = collect_project_data(conn, user_id)

    for name, _ in project_scores:
        if get_project_thumbnail_path(conn, user_id, name):
            projects.append(name)

    if not projects:
        print("\nNo projects with thumbnails yet.\n")
        return None

    print("\nSelect a project:")
    for i, name in enumerate(projects, start=1):
        print(f"{i}. {name}")

    while True:
        choice = input("\nEnter project number (or 'b' to go back): ").strip().lower()
        if choice == "b":
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(projects):
                return projects[idx - 1]
        print("Invalid selection. Try again.")
