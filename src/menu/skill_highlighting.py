"""
src/menu/skill_highlighting.py

Menu for managing skill highlighting preferences.
"""

from typing import List, Dict, Any
from src.services.skill_preferences_service import (
    get_available_skills_with_status,
    update_skill_preferences,
    reset_skill_preferences,
)


def manage_skill_highlighting(conn, user_id: int, username: str) -> None:
    """
    Interactive menu for managing which skills to highlight in portfolio/resume.
    """
    while True:
        print("\n" + "=" * 60)
        print("SKILL HIGHLIGHTING")
        print("=" * 60)
        print("\nChoose which skills to feature in your portfolio and resume.")
        print("\n1. View current skill preferences")
        print("2. Toggle skill highlighting")
        print("3. Set skill display order")
        print("4. Reset to defaults")
        print("5. Back to main menu")

        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            _view_skill_preferences(conn, user_id)
        elif choice == "2":
            _toggle_skill_highlighting(conn, user_id)
        elif choice == "3":
            _set_skill_order(conn, user_id)
        elif choice == "4":
            _reset_preferences(conn, user_id)
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


def _view_skill_preferences(conn, user_id: int) -> None:
    """Display current skill preferences."""
    skills = get_available_skills_with_status(conn, user_id, context="global")

    if not skills:
        print("\nNo skills found. Upload and analyze projects first.")
        return

    print("\n" + "-" * 70)
    print("YOUR SKILLS")
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
    print("(Highlighted skills appear in your portfolio and resume)")


def _toggle_skill_highlighting(conn, user_id: int) -> None:
    """Toggle highlighting for individual skills."""
    skills = get_available_skills_with_status(conn, user_id, context="global")

    if not skills:
        print("\nNo skills found. Upload and analyze projects first.")
        return

    # Display skills with numbers
    print("\n" + "-" * 60)
    print("TOGGLE SKILL HIGHLIGHTING")
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
    # This ensures un-toggled skills are also tracked in the database
    toggled_count = 0
    updates: List[Dict[str, Any]] = []

    for idx, skill in enumerate(skills, 1):
        if idx in indices:
            # Toggle this skill
            updates.append({
                "skill_name": skill["skill_name"],
                "is_highlighted": not skill["is_highlighted"],
                "display_order": skill.get("display_order"),
            })
            toggled_count += 1
        else:
            # Keep this skill's current status (ensure it's in DB)
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
        update_skill_preferences(conn, user_id, updates, context="global")
        print(f"\nToggled {toggled_count} skill(s).")
        _view_skill_preferences(conn, user_id)


def _set_skill_order(conn, user_id: int) -> None:
    """Set display order for highlighted skills."""
    skills = get_available_skills_with_status(conn, user_id, context="global")
    highlighted = [s for s in skills if s["is_highlighted"]]

    if not highlighted:
        print("\nNo highlighted skills. Toggle some skills first.")
        return

    print("\n" + "-" * 60)
    print("SET SKILL DISPLAY ORDER")
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

    # Update display order
    updates: List[Dict[str, Any]] = []
    for display_order, idx in enumerate(new_order, 1):
        skill = highlighted[idx - 1]
        updates.append({
            "skill_name": skill["skill_name"],
            "is_highlighted": True,
            "display_order": display_order,
        })

    if updates:
        update_skill_preferences(conn, user_id, updates, context="global")
        print(f"\nUpdated display order for {len(updates)} skill(s).")
        _view_skill_preferences(conn, user_id)


def _reset_preferences(conn, user_id: int) -> None:
    """Reset all skill preferences to defaults."""
    confirm = input("\nReset all skill preferences to defaults? (y/n): ").strip().lower()

    if confirm == "y":
        count = reset_skill_preferences(conn, user_id, context="global")
        print(f"\nReset {count} preference(s). All skills will now be shown by default.")
    else:
        print("\nReset cancelled.")
