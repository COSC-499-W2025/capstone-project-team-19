"""
src/menu/skill_highlighting.py

Menu for managing skill highlighting preferences.
Supports per-project, per-resume, per-portfolio, and global contexts.
"""

from typing import List, Dict, Any, Optional, Literal

from src.services.skill_preferences_service import (
    get_available_skills_with_status,
    update_skill_preferences,
    reset_skill_preferences,
)


def manage_skill_highlighting(
    conn,
    user_id: int,
    username: str,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    context_name: Optional[str] = None,
    project_key: Optional[int] = None,
) -> None:
    """
    Interactive menu for managing which skills to highlight.

    Args:
        conn: Database connection
        user_id: User ID
        username: Username for display
        context: "global", "portfolio", or "resume"
        context_id: Resume ID when context is "resume", None otherwise
        context_name: Name of resume/portfolio for display
        project_key: Project key to scope skills to a specific project
    """
    context_label = _get_context_label(context, context_name)
    back_label = "Back" if context != "global" else "Back to main menu"

    while True:
        print("\n" + "=" * 60)
        print(f"SKILL HIGHLIGHTING - {context_label}")
        print("=" * 60)
        print(f"\nChoose which skills to feature in {context_label.lower()}.")
        print("\n1. View current skill preferences")
        print("2. Toggle skill highlighting")
        print("3. Set skill display order")
        print("4. Reset to defaults")
        print(f"5. {back_label}")

        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            _view_skill_preferences(conn, user_id, context, context_id, context_label, project_key)
        elif choice == "2":
            _toggle_skill_highlighting(conn, user_id, context, context_id, context_label, project_key)
        elif choice == "3":
            _set_skill_order(conn, user_id, context, context_id, context_label, project_key)
        elif choice == "4":
            _reset_preferences(conn, user_id, context, context_id, context_label, project_key)
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


def _get_context_label(
    context: Literal["global", "portfolio", "resume"],
    context_name: Optional[str] = None,
) -> str:
    """Get display label for the current context."""
    if context_name:
        return context_name
    elif context == "resume":
        return "This Resume"
    elif context == "portfolio":
        return "Portfolio"
    else:
        return "Global (All Resumes & Portfolio)"


def _view_skill_preferences(
    conn,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    context_label: str = "Global",
    project_key: Optional[int] = None,
) -> None:
    """Display current skill preferences."""
    skills = get_available_skills_with_status(conn, user_id, context, context_id, project_key)

    if not skills:
        print("\nNo skills found. Upload and analyze projects first.")
        return

    print("\n" + "-" * 70)
    print(f"YOUR SKILLS ({context_label})")
    print("-" * 70)
    print(f"{'#':<4} {'Skill':<30} {'Status':<12} {'Order':<8} {'Projects':<10} {'Score':<8}")
    print("-" * 70)

    for i, skill in enumerate(skills, 1):
        name = skill["skill_name"].replace("_", " ").title()
        status = "Highlighted" if skill["is_highlighted"] else "Hidden"
        order = skill.get("display_order")
        order_str = str(order) if order is not None else "-"

        print(f"{i:<4} {name:<30} {status:<12} {order_str:<8} {skill['project_count']:<10} {skill['max_score']:.2f}")

    print("-" * 70)

    highlighted_count = sum(1 for s in skills if s["is_highlighted"])
    print(f"\nHighlighted: {highlighted_count}/{len(skills)} skills")

    if context == "global":
        print("(These preferences apply to all resumes and portfolio unless overridden)")
    elif context == "resume":
        print("(These preferences apply only to this project in this resume)")
    elif context == "portfolio":
        print("(These preferences apply only to this project in the portfolio)")


def _toggle_skill_highlighting(
    conn,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    context_label: str = "Global",
    project_key: Optional[int] = None,
) -> None:
    """Toggle highlighting for individual skills."""
    skills = get_available_skills_with_status(conn, user_id, context, context_id, project_key)

    if not skills:
        print("\nNo skills found. Upload and analyze projects first.")
        return

    # Display skills with numbers
    print("\n" + "-" * 60)
    print(f"TOGGLE SKILL HIGHLIGHTING ({context_label})")
    print("-" * 60)

    for i, skill in enumerate(skills, 1):
        name = skill["skill_name"].replace("_", " ").title()
        status = "[X]" if skill["is_highlighted"] else "[ ]"
        print(f"{i}. {status} {name}")

    print("\nEnter skill numbers to toggle (comma-separated), or 'q' to go back:")
    print("Example: 1,3,5 to toggle skills 1, 3, and 5")

    user_input = input("\nSkills to toggle: ").strip().lower()

    if user_input == "q" or not user_input:
        return

    try:
        indices = [int(x.strip()) for x in user_input.split(",")]
    except ValueError:
        print("Invalid input. Please enter numbers separated by commas.")
        return

    # Toggle the selected skills and save ALL skills' status
    toggled_count = 0
    updates: List[Dict[str, Any]] = []

    for idx, skill in enumerate(skills, 1):
        if idx in indices:
            updates.append({
                "skill_name": skill["skill_name"],
                "is_highlighted": not skill["is_highlighted"],
                "display_order": skill.get("display_order"),
            })
            toggled_count += 1
        else:
            updates.append({
                "skill_name": skill["skill_name"],
                "is_highlighted": skill["is_highlighted"],
                "display_order": skill.get("display_order"),
            })

    # Validate indices
    invalid_indices = [idx for idx in indices if idx < 1 or idx > len(skills)]
    for idx in invalid_indices:
        print(f"Skipping invalid index: {idx}")

    if updates:
        update_skill_preferences(conn, user_id, updates, context, context_id, project_key)
        print(f"\nToggled {toggled_count} skill(s).")
        _view_skill_preferences(conn, user_id, context, context_id, context_label, project_key)


def _set_skill_order(
    conn,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    context_label: str = "Global",
    project_key: Optional[int] = None,
) -> None:
    """Set display order for highlighted skills."""
    skills = get_available_skills_with_status(conn, user_id, context, context_id, project_key)
    highlighted = [s for s in skills if s["is_highlighted"]]

    if not highlighted:
        print("\nNo highlighted skills. Toggle some skills first.")
        return

    print("\n" + "-" * 60)
    print(f"SET SKILL DISPLAY ORDER ({context_label})")
    print("-" * 60)
    print("\nCurrent highlighted skills:")

    for i, skill in enumerate(highlighted, 1):
        name = skill["skill_name"].replace("_", " ").title()
        order = skill.get("display_order")
        order_str = f" (order: {order})" if order is not None else ""
        print(f"{i}. {name}{order_str}")

    print("\nEnter the new order as a comma-separated list of skill numbers.")
    print("Example: 3,1,2 puts skill 3 first, then 1, then 2")
    print("Or press Enter to keep current order.")

    user_input = input("\nNew order: ").strip()

    if not user_input:
        return

    try:
        new_order = [int(x.strip()) for x in user_input.split(",")]
    except ValueError:
        print("Invalid input. Please enter numbers separated by commas.")
        return

    # Validate indices
    if not all(1 <= idx <= len(highlighted) for idx in new_order):
        print("Invalid skill numbers. Please use numbers from the list above.")
        return

    # Normalize: place selected skills first, then append remaining in current order.
    selected_indices = []
    seen = set()
    for idx in new_order:
        if idx in seen:
            continue
        seen.add(idx)
        selected_indices.append(idx)

    ordered_skills: List[Dict[str, Any]] = []
    for idx in selected_indices:
        ordered_skills.append(highlighted[idx - 1])
    for idx, skill in enumerate(highlighted, 1):
        if idx not in seen:
            ordered_skills.append(skill)
    updates: List[Dict[str, Any]] = []
    for display_order, skill in enumerate(ordered_skills, 1):
        updates.append({
            "skill_name": skill["skill_name"],
            "is_highlighted": True,
            "display_order": display_order,
        })

    if updates:
        update_skill_preferences(conn, user_id, updates, context, context_id, project_key)
        print(f"\nUpdated display order for {len(updates)} skill(s).")
        _view_skill_preferences(conn, user_id, context, context_id, context_label, project_key)


def _reset_preferences(
    conn,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    context_label: str = "Global",
    project_key: Optional[int] = None,
) -> None:
    """Reset skill preferences to defaults for this context."""
    if context == "global":
        confirm_msg = "\nReset all skill preferences to defaults? (y/n): "
        success_msg = "\nReset {count} preference(s). All skills will now be shown by default."
    else:
        confirm_msg = f"\nReset skill preferences for {context_label} to use global defaults? (y/n): "
        success_msg = f"\nReset {{count}} preference(s). {context_label} will now use global preferences."

    confirm = input(confirm_msg).strip().lower()

    if confirm == "y":
        count = reset_skill_preferences(conn, user_id, context, context_id, project_key)
        print(success_msg.format(count=count))
    else:
        print("\nReset cancelled.")
