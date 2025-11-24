# Personal Log - Salma

## (Week 3) Monday 15th - Sunday 21st September

![Screenshot of week 3 peer eval](./screenshots/Salma-Sept15-21.png)

Week recap:

- Discussed the initial project details with the team and brainstormed functional and non-functional requirements.
- Met with other groups to compare requirements, took notes, and revised the list based on feedback and online team discussions.
- Reviewed and approved some pull requests on GitHub.

## (Week 4) Monday 22nd - Sunday 28th September

![Screenshot of week 4 peer eval](./screenshots/Salma-Sept22-28.PNG)

Week recap:

- Met with the team on Monday to discuss and draft the initial architecture diagram. Took notes, compared with another team on Wednesday, and revised the diagram.
- Created a shared Figma file for design collaboration and architecture diagram development.
- Researched the audio function and integrated it into both the architecture diagram and dashboard visualization. The accompanying document outlines the workflow, including audio input, preprocessing, transcription, speaker diarization, and categorization into work or non-work artifacts with summary metrics.
- Worked on the proposed solution and use cases for the project proposal.

## (Week 5) Monday 29th September - Sunday 5th October

![Screenshot of week 5 peer eval](./screenshots/Salma-Sept29-Oct5.PNG)

Week recap:

- Built the Data Flow Diagram (DFD) with the team on Monday.
- Met with another team on Wednesday to compare diagrams and took notes.
- Researched the differences between DFD Level 0 and Level 1.
- Prepared a Figma file and reusable diagram template to make teamwork easier.

## (Week 6) Monday 6th October - Sunday 12th October

![Screenshot of week 6 peer eval](./screenshots/Salma-Oct6-12.png)

Week Recap:

- Reviewed the professor’s requirements and discussed them with the team during Wednesday’s class.
- Worked on the consent feature: drafted the consent text, implemented logic to store consent responses in the SQLite database, and wrote tests to ensure both accepted and rejected responses are stored correctly.
- Made several adjustments based on feedback e.g. incorporated Ammaar’s suggestion to add the .db file to .gitignore and ensured test data doesn’t pollute the actual user consent database.
- Provided comments and suggestions on pull requests, such as the file output placement in Timmi’s ZIP parsing PR. Also reviewed other PRs, including DFD Level 1 (Ammaar) and WBS (Johanes).

## (Week 7) Monday 13th October - Sunday 19th October

![Screenshot of week 7 peer eval](./screenshots/Salma-Oct13-19.png)

Week recap:

- Worked on implementing user configuration based on username or user_id for future uses. This feature allows users to save and modify their user consent and LLM consent settings. It also handles edge cases, such as when a user is logged in but has not yet set their configuration, or when only a partial configuration is provided. Additionally, I created a local database view (latest_user_consent) for quick lookups of usernames and their most recent consent settings.
- Provided comments and suggestions on multiple PRs. For example, I reviewed Timmi’s PR and suggested storing file metadata based on username or user_id. I also reviewed Johanes’ PR and provided some suggestions for next steps.

## (Week 8) Monday 20th October - Sunday 26th October

![Screenshot of week 7 peer eval](./screenshots/Salma-Oct20-26.PNG)

Week Recap:

- Continued Timmi’s PR to fix the send_to_analysis flow for correctly directing individual and collaborative work. Made adjustments based on feedback, such as adding missing arguments and implementing a loop system for user prompts.
- Reviewed several PRs and provided feedback e.g., Ammaar’s PR on consent flow logic, Timmi’s PR on redirecting individual vs. collaborative work, and Adara’s PR on using bullet points instead of paragraphs in resumes.
- Worked on code collaborative analysis to detect .git folders and generate metrics like the number of commits and overall summary per project.

Next steps: continue developing the code collaborative analysis for global summaries from all projects (possibly using LLMs), refactor the code, and move on to non-code collaborative analysis.

## (Week 9) Monday 27th October - Sunday 2nd November

![Screenshot of week 9 peer eval](./screenshots/Salma-Oct27-Nov2.PNG)

Week Recap:

- Refactored code_collaborative_analysis.py to reuse language and framework detection functionality, separate core logic from helpers, and integrate project classifications (classification = collaborative, type = code).
- Reviewed and provided feedback on some PRs (e.g. Ammaar’s and Johanes’s) to make the language/framework detection and metrics output more user-friendly.
- Worked on generating summaries for all code-collaborative projects using Git metrics and user input (without LLM).

Next Steps: improve the non-LLM summary generation for code-collaborative analysis based on feedback from Johanes and Timmi e.g. use NLTK for stopword removal and provide a user input template. If time allows, I also plan to store the metrics into the DB.

## (Week 10) Monday November 3 - Sunday November 9

![Screenshot of week 10 peer eval](./screenshots/Salma-Nov3-Nov9.PNG)

Week recap:

- Improved the summary of non-llm code collaborative analysis:

  - Provided a template to the user with clear instructions and an example input (e.g., “please include what the project does, your technical focus, your contribution,” etc.). Shortened and reformatted the template into bullet points based on Timmi’s feedback.
  - Fixed a related bug: only asks for user input if the user rejects LLM consent, and the question is moved earlier (before any analysis) to avoid redundant prompts per project.
  - Enhanced the stopwords filter for keyword extraction from all user inputs using NLTK.

- Reviewed and provided some feedback on some PRs, for example:
  - Reviewed Timmi’s PR on GitHub metrics to suggest handling runtime errors (e.g., empty repos, missing GitHub client ID) gracefully by printing error messages and continuing the program instead of stopping.
  - Suggested renaming Ammaar’s non-LLM metrics table to non_llm_text for consistency with Johanes’ llm_text table.

Next week: I plan to store non-LLM code collaborative metrics (was unsure about the DB refactoring but now resolved). If time allows, I also plan to refactor the repo structure to include subfolders such as e.g., consent/, common/, text_individual_analysis/, etc.

## (Week 11) Monday November 17 - Sunday November 23

![Screenshot of week 11 peer eval](./screenshots/Salma-Nov17-Nov23.PNG)

I postponed storing the non-LLM collaborative code metrics because a few milestone-1 tasks became higher priority. Here’s what I completed over the past weeks:

- PR #206 (Repo restructuring during reading week)

  - Refactored the src/ directory into clearer subfolders for better organization and maintainability.
  - Updated all related imports and path references across scripts and tests.
  - Applied Timmi’s suggestion to rename common/ to utils/ to follow industry standard.

- PR #233 (Code activity-type detection basic logic pipeline)

  - Implemented build_activity_summary() to aggregate activity counts from files and PRs, including percentage breakdowns.
  - Added a standardized formatter for both individual and collaborative analysis flows.
  - Created test_code_activity_type.py to validate path shortening, formatter output, and aggregation logic.
  - Activity detection uses keyword matching on filenames and PR text (e.g., test/spec → Testing, readme/md → Documentation, refactor/fix/bug/docs in PRs → corresponding category). Anything else defaults to Feature Coding.

- PR #238 (Improvements for PR #233)

  - Integrated user-associated files into the collaborative analysis logic.
  - Incorporated teammate feedback: removed duplicate imports (Ammaar), excluded dependency files by reusing the list from the non-LLM analysis (Johanes), and moved SQL-related queries into src/db (Ivona).
  - Updated the console output to a cleaner table format.
  - Store data in code_activity_metrics.
  - Updated and expanded tests to cover all edge cases.

- Reviewed and provided feedback on several PRs, including:
  - Johanes’ PR on text activity detection, suggesting that SQL-related queries be moved into src/db.
  - Timmi’s PR on the GitHub analysis function, recommending a quick word/topic-diversity check to ensure comments are actually meaningful.
  - Ammaar’s PR on collaborative code-skill detection, suggesting a clearer table name change from user_file_contributions to user_code_contributions.

Next Week: I plan to re-run main to identify and fix remaining issues/possible edge cases (e.g., the text-individual flow) to finish Milestone 1. I’ll also discuss with the team whether the terminal-output reformatting task can be split into smaller subtasks. If still needed, I’ll also store the non-LLM collaborative code metrics.
