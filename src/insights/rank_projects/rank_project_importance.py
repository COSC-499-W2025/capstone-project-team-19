import json

from src.db import get_all_user_project_summaries, connect

def collect_project_data(conn, user_id):
    summaries = get_all_user_project_summaries(conn, user_id)

    for summary in summaries:
        project_name = summary["project_name"]
        project_type = summary["project_type"]
        project_mode = summary["project_mode"]

        summary_json = json.loads(summary["summary_json"])

        print("\nproject_name:", project_name)
        print("\nproject_type:", project_type)
        print("\nproject_mode:", project_mode)
        print("\nsummary_json:", summary_json)
        print()
        print()

        if project_type == "text":
            score_text_project(summary_json)
        else: # project will be code
            score_code_project(summary_json)


def score_text_project(project_mode, summary):
    is_collaborative = (project_mode == "collaborative")

    pass

def score_code_project(project_mode, summary):
    is_collaborative = (project_mode == "collaborative")

    pass

if __name__ == "__main__":
    conn = connect()
    user_id = 1
    collect_project_data(conn, user_id)
    conn.close()
