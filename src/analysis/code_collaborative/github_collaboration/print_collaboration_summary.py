def print_collaboration_summary(profile: dict):
    print("\n==============================")
    print(" Collaboration Skill Summary")
    print("==============================\n")

    levels = profile.get("skill_levels", {})
    skills = profile.get("skills", {})
    norm = profile.get("normalized", {})

    print(f"Review Quality:        {levels.get('review_quality', 'N/A')}")
    print(f"Participation:         {levels.get('participation', 'N/A')}")
    print(f"Consistency:           {levels.get('consistency', 'N/A')}")
    print(f"Leadership:            {levels.get('leadership', 'N/A')}")
    print()

    print("Normalized Contribution:")
    print(f" - Commits:            {norm.get('commit_share', 0):.2f}")
    print(f" - PRs:                {norm.get('pr_share', 0):.2f}")
    print(f" - Issues:             {norm.get('issue_share', 0):.2f}")
    print(f" - Reviews:            {norm.get('review_share', 0):.2f}")
    print()

    print(f"Overall Activity Score: {norm.get('total_behavior_score', 0):.2f}")
    print(f"Dominant Activity:      {norm.get('dominant_activity', 'N/A')}")
    print()
