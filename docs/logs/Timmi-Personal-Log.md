# Personal Log - Timmi

## (Week 3) Monday 15th - Sunday 21st September

![Screenshot of this week's peer eval](./screenshots/Timmi%20Sept15-21.PNG)

Week Recap: Worked with the team to build the functional and non-functional requirements. Conversed with other teams on Wednesday, Sept. 17th, about both ours and their project requirements, we compared ideas and gained feedback on how to clean up our project requirements. Performed personal research, and conversed with my team, on the project specifications, specifically data storage.

## (Week 4) Monday 22nd - Sunday 28th September

![Screenshot of this week's peer eval](./screenshots/Timmi-Sept22-28.PNG)

Worked with the team to build the architecture diagram and put together the project proposal. On Wednesday, we conversed with other teams about their architecture diagrams, then regrouped and talked about what we liked, what we didn't, and what we wanted to add/expand on.

I was assigned to write the *Project Scope and Usage Scenario* and the *Proposed Solution* (with Salma) in the project proposal. Additionally, the team split up research tasks on the different file type functions.

I took on the Image function, Video function, and getting data from online sources (Google Drive) with Ammaar, and thus spent a few hours researching how we would analyze those file types. I then added the processes to the Architecture Diagram.

I also helped with the *Tech Stack* and the *Requirements, Testing, and Requirement Verification* sections in the project proposal, as well as expanded on the dashboard visualization in the architecture diagram.

## (Week 5) Monday 29th September - Sunday 5th October

![Screenshot of this week's peer eval](./screenshots/Timmi-Sept29-Oct5.png)

Week Recap: On Monday the team began working on the DFD, both Level 0 and Level 1. We researched DFD's to ensure we were putting the correct elements in our diagram, as they are specific to the level of the DFD. On Wednesday, we conversed with other teams, exchanging diagrams. We asked questions about their diagrams to learn their process and plans, and they asked about ours. 

## (Week 6) Monday 6th October - Sunday 12th October

![Screenshot of this week's peer eval](./screenshots/Timmi-Oct6-Oct12.png)

Week Recap: Spent time inputting each requirement as in issue. We did not have a meeting this week, so each team member self-assigned a task to themselves. I took on setting up the local environment and implementing the requirement "parsing zip files". I researched how to parse a file in python, and also general python set up for the system. Additionally, I wrote the tests for the parsing files requirement.

My PR's: 
- Local environment setup
- Parsing files

Reviewed the following PR's:
- User consent feature (Salma)
- Add updated system architecture diagram and description (Adara)
- Wbs (Johanes)

## (Week 7) Monday October 13 - Sunday October 17 

![Screenshot of this week's peer evaluation](./screenshots/Timmi-Oct13-Oct19.PNG) 

Week Recap: This week, I started by setting up the PR template and ensuring all assigned issues were in the Kanban board. Then, I fixed a Windows-specific bug where MIME detection was failing to recognize certain CSV files during pytest runs, which required additional research to resolve. I also connected the parsed ZIP files to the database so the files metadata is now stored in the database. The files themselves remain stored locally on the user’s machine rather than within the database, which is something the team plans to discuss further in our next meeting. 

My PR's:
- 74 (Pull request template)
- 77 (Windows test failure)
- 78 (Parsing to db)

Reviewed the following PR's:
- 75 (Store user config) - Salma

## (Week 8) Monday October 20 - Sunday October 26

![Screenshot of this week's peer evaluation](./screenshots/Timmi-Oct20-Oct26.PNG)

Week Recap: This week, I started by removing and refactoring the `zip_data` folder so that raw files would no longer be saved in the directory or the database. This change was discussed with the team on Wednesday, October 22. However, when my PR was reviewed, there was some confusion because parts of the existing analysis code still relied on those raw files being saved. There was a misunderstanding about which files were stored where, and after further discussion on Discord, we decided that the `zip_data` folder would only be removed after the parsing and analysis are complete. I then closed my PR without merging and created an issue to implement this change in the future.

After that, I began implementing the flow for parsing and analysis by adding a `project_type` attribute to the `project_classifications` table to indicate whether each project was code or text. I also added modular routing for collaborative versus individual projects. Collaborative projects now trigger contribution analysis to determine which parts the user worked on, while individual projects go straight to file analysis. All relevant tests have been implemented.

Additionally, Ivona and I discussed the need for further duplication checks when uploading a ZIP file. I then implemented code to check if the ZIP file had already been uploaded, and if so it prompts the user to choose what they would like to do (reuse the old analaysis or replace the files with the new ones). Further duplication checks will need to be implemented.

Next week, I plan to continue with the analysis of the files and continue to implement duplication checks, as there is one case that is still getting through despite being a duplicate.

My PR's:
- 104 (Refactor/remove zip data saving) - closed, unmerged
- 118 (Project type classification)
- 127 (Fix/duplicate zip path)

## (Week 9) Monday October 27 - Sunday November 2

![Screenshot of this week's peer evaluation](./screenshots/Timmi-Oct27-Nov2.PNG)

Week Recap: This week I worked on implementing the GitHub OAuth to further the collaboration analysis. Although no metrics have been pulled from GitHub yet, I worked on setting up the authentication flow through GitHub. If the user agrees, they can connect their project to a GitHub repository, which will allow us to analyze more individual contributions to a collaborative project. I included multiple tests and ensured the GitHub tokens were securely stored in the local database.

Next week, I plan to extend the individual contributions to a collaborative project by actually requesting and recieving dating via the GitHub API. This function will only run if the user has given permission to connect to GitHub, as was implemented last week. I also began refactoring the main flow (specifically the file `main.py`), but because of how messy the file is it is taking me longer than expected. Thus, I will continue my refactoring and hope to have this PR done early next week.

Last week, I had planned on extending the duplication techniques, but the team discussed this and realized any further duplication checks are not a requirement until Milestone 2. Saving this for the next milestone will allow us to focus more on the Milestone 1 requirements.

## (Week 10) Monday November 17 - Sunday November 23

![Screenshot of this week's peer evaluation](./screenshots/Timmi-Nov17-Nov23.PNG)

Week Recap: This week I focused heavily on completing core components of the system that were necessary for meeting the milestone requirements. I implemented the full GitHub integration flow, expanded and finalized the pipelines, and contributed major restructuring across the project. I also resolved several GitHub conflicts that emerged due to delayed PR reviews, which required me to manually migrate work into new branches.

A large portion of my time was also spent determining our remaining tasks for the milestone. Because consistent communication was difficult, I created detailed documents outlining the project structure and the outstanding work needed, which helped the team get clarity on what still had to be completed. These documents are all on Google Docs, and thus are not included in the repository.

In addition to this, I continued cleaning up the codebase by organizing modules, improving flow consistency, and preparing for the next phase of development.

Technical Breakdown:
- #208 (Refactor/db module split) - Refactored the whole `db.py` file. Separated the schema from the helper functions, then further split the helper functions into files based on which table the functions were accessing.
- #209 (GitHub metrics db storage) - Normalized the `github_repo_metrics` table, so instead of storing a JSON text the table has proper metric columns. I updated all areas of the code to account for this change (storing/parsing functions, updating integration flow, and fixing tests)
- #212 (Skill detection flow) - Implemented the full skill detection pipeline. Previously, all the analyses were spread out among the system, printing and storing different types of metrics, and not technically detecting the skills the user shows in their projects. This pipeline takes the analyses already implemented and sends the data into a skill detector flow, where the project is parsed via several detector functions (the functions themselves were not implemented in this PR, only the flow was). 
- #213 (GitHub analysis functions) - Implemented the initial modules used to determine the user's collaboration skills in a coding project. The functions themselves were not fully implemented here, only the flow and supporting classes. 
- #221 (Integration for project summaries) - Implemented the Project Summaries flow. As the analyses are run, the project summary is filled in, so later the system can print and store the project summaries instead of all the various types of anlyses we previously had implemented. This will make the final milestone requirements much easier to implement (retrieval and parsing).
- #225 (GitHub analysis final implementation) - Completely finished the full GitHub collaboration analysis. My previous GitHub PRs were partial, and more focused on flow, but this one fully fleshed out any missing sections and conencted all the components. When the user connects to GitHub, their collaboration skills are now detected and stored in the database. Detecting these skills will help the user understand their contribution patterns (team dynamics, workload, etc.).

Additionally, I reviewed as many PRs as my time schedule allowed.

Next Week:
- Refactor the project summary so that the system prints results stored in the project summary database rather than using the current flow. 
- Separate the printing of resume items and portfolio items to make the output clearer and more aligned with the user experience we intend.
- Clarify (and possibly implement) the things Salma mentioned in PR #225 (GitHub API not returning ALL comments on a PR, only some, and ensuring all comments are being stored)

I also plan to refactor the print statements throughout the codebase. Right now the system prints too much during a run, so my goal is to reduce unnecessary output and ensure that only the final project summaries are displayed to the user.