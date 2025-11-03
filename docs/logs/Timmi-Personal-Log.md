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

![Screenshot of this week's peer evaluation]()

Week Recap: This week I worked on implementing the GitHub OAuth to further the collaboration analysis. Although no metrics have been pulled from GitHub yet, I worked on setting up the authentication flow through GitHub. If the user agrees, they can connect their project to a GitHub repository, which will allow us to analyze more individual contributions to a collaborative project. I included various tests, and ensured any tokens were securely stored in the local database.

Next week, I plan to extend the individual contributions to a collaboratvie project by actually requesting and recieving dating via the GitHub API once the user has linked a project to its GitHub repository. I also began refactoring the main flow (specifically the file `main.py`), but because of how messy the file is it is taking me longer than expected. Thus, I will continue my refactoring and hope to have this PR done early next week.

Last week, I had planned on extending the duplication techniques, but the team discussed this and realized any further duplication checks are not a requirement until Milestone 2. Saving this for the next milestone will allow us to focus more on the Milestone 1 requirements.