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
