"""
Project Ranking — Required Database Inputs

To compute a meaningful “importance score” for each project, the ranking
module must retrieve metrics from multiple database tables. These signals
describe project size, difficulty, user contribution, recency, skills, and
overall project scope. All data listed below is already stored in the system.

Required data sources:

1. Project Summary (project_summaries.summary_json)
   - languages: list of languages used
   - frameworks: list of detected frameworks
   - skills: extracted skill list
   - metrics: code/text/git analysis metrics (LoC, complexity, readability, etc.)
   - contributions: collaborative contribution details (git or Drive)
   - errors: analysis errors to penalize messy projects
   - created_at: when the summary was generated

2. Files Table (files)
   - file count per project
   - total file size (size_bytes)
   - number of code vs. text files (extension, file_type)
   - earliest and latest file timestamps (created, modified)

3. Code Contribution Tables
   - user_code_contributions:
       lines_changed, commits_count per file
   - code_activity_metrics:
       distribution of debugging, testing, refactoring, documentation,
       and feature coding events
   - project_repos:
       repo linkage (to determine if GitHub metrics exist)

4. GitHub Metrics (if code project has linked repo)
   - github_repo_metrics:
       total_commits, commit_days, first_commit_date, last_commit_date
       total_additions/deletions, contribution_percent, PR/issue counts
   - github_commit_timestamps:
       raw commit timeline for computing duration and recency
   - github_pull_requests, github_pr_reviews, github_pr_review_comments
       quality and depth of collaboration signals
   - github_issues and github_issue_comments:
       issue tracking involvement

5. Text Contribution Metrics (text collaboration only)
   - text_contribution_summary:
       user_revision_count, total_word_count, total_revision_count
   - text_contribution_revisions:
       timestamped revision activity for recency and depth scoring

6. Text Analysis Tables (text project difficulty / size)
   - non_llm_text:
       doc_count, total_words, reading_level_avg, summary quality metrics
   - llm_text:
       readability scores, lexical diversity, word/sentence counts

7. Skill Records (project_skills)
   - skill_name, level (“beginner/intermediate/advanced”), numeric score
   - evidence_json showing why the skill applies
   - used for computing skill depth and evidence strength

Summary:
The ranking module pulls project-level summaries plus supporting metrics from
files, GitHub, text analysis tables, skill tables, and contribution tables.
These values are combined into a unified importance score reflecting size,
complexity, contribution, skill depth, recency, and project duration.

"""

from src.db import get_project_summaries


# TODO: call all project summaries (maybe only certain metrics??)

"""
get_project_summaries
get_file_metrics
get_github_repo_metrics
get_commit_timestamps
get_text_non_llm_metrics
get_text_contribution_summary
get_project_skills
get_code_activity_metrics
"""

# TODO: calculate the most important ones

# TODO: print the projects