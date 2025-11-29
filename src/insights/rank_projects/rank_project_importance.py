import json

from src.db import get_all_user_project_summaries, connect
from src.models.project_summary import ProjectSummary

def collect_project_data(conn, user_id):
    rows = get_all_user_project_summaries(conn, user_id)

    for row in rows:
        project_name = row["project_name"]
        project_type = row["project_type"]
        project_mode = row["project_mode"]

        summary_dict = json.loads(row["summary_json"])
        project_summary = ProjectSummary.from_dict(summary_dict)

        print("\nproject_name:", project_name)
        print("\nproject_type:", project_type)
        print("\nproject_mode:", project_mode)
        print("\nproject_summary:", project_summary)
        print()

        if project_type == "text":
            score_text_project(project_summary)
        else: # project will be code
            score_code_project(project_summary)


def score_text_project(summary):
    is_collaborative = (summary.project_mode == "collaborative")


    pass

def score_code_project(summary):
    is_collaborative = (summary.project_mode == "collaborative")

    pass

if __name__ == "__main__":
    conn = connect()
    user_id = 1
    collect_project_data(conn, user_id)
    conn.close()
