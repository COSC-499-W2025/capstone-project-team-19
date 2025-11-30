from datetime import datetime
from src.db import get_skill_events

def get_skill_timeline(conn, user_id):
    rows = get_skill_events(conn, user_id)

    dated = []
    undated = []

    for row in rows:
        # SQLite returns tuples: skill_name, level, score, project_name, actual_activity_date, recorded_at
        skill_name = row[0]
        level = row[1]
        score = row[2]
        project_name = row[3]
        actual_activity_date = row[4]  # end_date or last_commit_date, can be NULL
        
        # Replace underscores with spaces in skill names for better readability
        formatted_skill_name = skill_name.replace("_", " ")
        
        event = {
            "skill_name": formatted_skill_name,
            "level": level,
            "score": score,
            "project_name": project_name,
            "date": actual_activity_date
        }

        # Only use actual activity dates for "dated" list
        # If no actual activity date exists, put in "undated"
        if actual_activity_date is None:
            undated.append(event)
        else:
            dated.append(event)

    dated.sort(key = lambda e: e["date"])

    return dated, undated

def print_skill_timeline(dated, undated):
    # Line width: 4 (indent) + 65 (skill info) + 2 (" [") + ~30 (project name) + 1 ("]") = ~102
    # Use 105 to extend just past the edge
    line_width = 100
    
    print("\n" + "=" * line_width)
    print("SKILL TIMELINE (Chronological List)")
    print("=" * line_width)

    if not dated and not undated:
        print("\nNo skill data available.\n")
        print("=" * line_width)
        return

    print("DATED SKILL EVENTS")
    print("-" * line_width)

    if dated:
        current_date = None

        for e in dated:
            # convert iso date string to datetime objct
            try:
                date_time = datetime.fromisoformat(e["date"])
                date_str = date_time.strftime("%B %d, %Y")
            except:
                date_str = e["date"]

            if date_str != current_date:
                print(f"\n{date_str}:")
                current_date = date_str

            # Format with fixed width for skill + level/score so project names align
            # Format score to 2 decimal places
            score_str = f"{e['score']:.2f}".rstrip('0').rstrip('.')  # Remove trailing zeros
            skill_info = f"{e['skill_name']} ({e['level']}, score={score_str})"
            print(f"  - {skill_info:65s} [{e['project_name']}]")
        
        print()  # Empty line after last dated event

    else:
        print("\nNo dated skill events available.\n")

    # Only show undated section if there are undated skills
    if undated:
        print("\n" + "=" * line_width)
        print("UNDATED SKILL EVENTS (No Activity Metadata)")
        print("-" * line_width)
        
        for e in undated:
            # Format with fixed width for skill + level/score so project names align
            # Format score to 2 decimal places
            score_str = f"{e['score']:.2f}".rstrip('0').rstrip('.')  # Remove trailing zeros
            skill_info = f"{e['skill_name']} ({e['level']}, score={score_str})"
            print(f"  - {skill_info:65s} [{e['project_name']}]")
        
        print()  # Empty line after last undated event

    print("=" * line_width + "\n")