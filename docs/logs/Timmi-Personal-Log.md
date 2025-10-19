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

Week Recap: This week, I started by setting up the PR template and ensuring all assigned issues were in the Kanban board. Then, I fixed a Windows-specific bug where MIME detection was failing to recognize certain CSV files during pytest runs, which required additional research to resolve. I also connected the parsed files to the database so the files metadata is now stored in the database instead of only in the zip data file, although at the moment the parsed raw files are still stored in a folder.

My PR's:
- 74 (Pull request template)
- 77 (Windows test failure)
- 78 (Parsing to db)

Reviewed the following PR's:
- 75 (Store user config) - Salma