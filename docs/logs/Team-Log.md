# Team Log

## (Week 3) Monday 15th - Sunday 21st September

Week recap: The team discussed and worked on creating a list of functional and non-functional requirements. On Wednesday, during class we met with other teams and compared requirements.

Discussion went well with other teams, we found out that there are some features that our team has, while other's not, and vice versa.

Such as other team has trend analysis and onboarding tutorial while our team does not
Our team has a feature where we ask for user's permission, while other team does not.

### Additional Context

| Team    | Highlights                                                                                                                                                                                                                                                                                    |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Team 20 | **Functional:** More detailed file classification (e.g., programming language and type).<br>**Functional:** Analysis runs only on new files to avoid redundancy.<br>**Security:** Omits user permission requests before accessing local files.                                                |
| Team 17 | **Functional:** Adds trend analysis visualizations and file previews for user approval.<br>**Non-functional:** Groups requirements under performance, scalability, reliability, security, maintainability, and privacy.<br>**New:** Includes an onboarding/tutorial experience at app launch. |
| Team 3  | **Functional:** Generates resume bullet points and provides a timeline visualization.<br>**Non-functional:** Favors a modular codebase design.<br>**Use Case:** Extends the system to HR platforms and hiring managers.                                                                       |

Plan for the next cycle: Discussing about team's project proposal and architecture diagram that will be submitted next week

## (Week 4) Monday 22nd - Sunday 28th September

### Week recap:

The team worked on building the architecture diagram and writing the project proposal. On Wednesday, we conversed with other teams about their architecture diagrams, then regrouped to discuss what we liked, didn't like, and what we wanted to add/expand on in our own diagram. We also finally decided to work on native app instead of web app considering the challenges of learning new things that might be useful for us in the future.

For the project proposal, we divided writing responsibilities among the team. We also split up research tasks for the different file type functions. Team members researched approaches for text (PDF, DOCX), images, videos, audio, csv, and code analysis as well as retrieving data from online sources (Google Drive and Github). We integrated our research into the architecture diagram, and the dashboard visualization was expanded to include them.

### Burnup chart

![Burnup chart for Sept 22-28](screenshots/Burnup-Sept22-28.png)

### Github usernames

| GitHub Username | Student Name          |
| --------------- | --------------------- |
| `AdaraPutri`    | Adara Putri           |
| `ammaarkhan`    | Ammaar Khan           |
| `ivonanicetin`  | Ivona Nicetin         |
| `johaneshp`     | Johanes Hamonangan    |
| `salmavkh`      | Salma Vikha Ainindita |
| `taoTimTim`     | Timmi Draper          |

### Table view of completed tasks by username

| GitHub Username | Screenshot                                                                  |
| --------------- | --------------------------------------------------------------------------- |
| `AdaraPutri`    | ![Completed tasks for Adara](screenshots/Completed-Adara-Sept22-28.png)     |
| `ammaarkhan`    | ![Completed tasks for Ammaar](screenshots/Completed-Ammaar-Sept22-28.png)   |
| `ivonanicetin`  | ![Completed tasks for Ivona](screenshots/Completed-Ivona-Sept22-28.png)     |
| `johaneshp`     | ![Completed tasks for Johanes](screenshots/Completed-Johanes-Sept22-28.png) |
| `salmavkh`      | ![Completed tasks for Salma](screenshots/Completed-Salma-Sept22-28.png)     |
| `taoTimTim`     | ![Completed tasks for Timmi](screenshots/Completed-Timmi-Sept22-28.png)     |

### Table view of in progress tasks by username

Not applicable – no tasks in progress.

### Additional context

#### Differences/Similarities with Other Teams' Architecture Diagrams

| Team    | Takeaways                                                                                                                                                                                                                                                              |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Team 14 | Included a portfolio builder that we decided to skip.<br>Connected with GitHub, which inspired us to add that feature.<br>Plans to leave room for a future web frontend rather than staying app-only.<br>Stored both raw and processed data (we don't store raw data). |
| Team 15 | Avoids using a database, keeping everything local.<br>Does not support music, audio, or video files (we plan to include them).<br>Has post-processing in between ML and metrics steps to tidy up the data.                                                             |
| Team 18 | Also uses Electron to support cross-platform desktop development.                                                                                                                                                                                                      |

Plan for next cycle: Build the Data Flow Diagram (DFD) that must be submitted next week

## (Week 5) Monday 29th - Sunday 5th October

### Week recap:

The team focused on building the Data Flow Diagram (DFD). On Monday, we collaborated to draft Level 0 and Level 1, aligning on system boundaries, external entities, and the major data stores and flows. We looked at examples and articles online to understand the difference between a Level 0 and Level 1 diagram and consulted the professor on our DFD Level 1 draft in class. The feedback was to break down the different metric functions like we did in the System Architecture diagram and to include separate arrows from the "Categorize File" process to each functions. On Wednesday, we went around in class comparing DFDs with other teams, then regrouped to discuss what we liked, didn't like, and what we wanted to refine or add to our diagrams.

### Burnup chart

![Burnup chart for Sept 29-Oct 5](screenshots/Burnup-Sept29-Oct5.png)

### Github usernames

| GitHub Username | Student Name          |
| --------------- | --------------------- |
| `AdaraPutri`    | Adara Putri           |
| `ammaarkhan`    | Ammaar Khan           |
| `ivonanicetin`  | Ivona Nicetin         |
| `johaneshp`     | Johanes Hamonangan    |
| `salmavkh`      | Salma Vikha Ainindita |
| `taoTimTim`     | Timmi Draper          |

### Table view of completed tasks by username

| GitHub Username | Screenshot                                                                    |
| --------------- | ----------------------------------------------------------------------------- |
| `AdaraPutri`    | ![Completed tasks for Adara](screenshots/Completed-Adara-Sept29-Oct5.png)     |
| `ammaarkhan`    | ![Completed tasks for Ammaar](screenshots/Completed-Ammaar-Sept29-Oct5.png)   |
| `ivonanicetin`  | ![Completed tasks for Ivona](screenshots/Completed-Ivona-Sept29-Oct5.png)     |
| `johaneshp`     | ![Completed tasks for Johanes](screenshots/Completed-Johanes-Sept29-Oct5.png) |
| `salmavkh`      | ![Completed tasks for Salma](screenshots/Completed-Salma-Sept29-Oct5.png)     |
| `taoTimTim`     | ![Completed tasks for Timmi](screenshots/Completed-Timmi-Sept29-Oct5.png)     |

### Table view of in progress tasks by username

Not applicable – no tasks in progress.

### Additional context

#### Differences/Similarities with Other Teams' DFD Diagrams

| Team    | Takeaways                                                                                                                                                                                                                                                                   |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Team 11 | Focuses on scanning file metadata rather than calculating metrics.<br>Lacks a dedicated metrics module and renders the dashboard as static HTML.<br>We still need clarity on how their data extraction supports the insights they expect to present.                        |
| Team 17 | Level 0 and Level 1 structures align closely with ours.<br>Introduces error logging and an artifact database, though the data ingestion flow remains unclear.<br>Aims to output a portfolio experience instead of a dashboard; users can opt out of saving to the database. |
| Team 15 | Restricts processing to text files only, applying an ML model for every document.<br>Does not handle images or video sources.<br>Open questions on what metrics they intend to surface from the ML pipeline.                                                                |

## (Week 6) Monday 6th - Sunday 12th October

### Week recap:

This week, the team focused on moving from design to implementation, refining both the System Architecture Diagram and DFD Level 1 to reflect all updated project requirements and new modules like offline processing. The team also began coding key system features: setting up the local environment, implementing ZIP file parsing, and enhancing it with error handling for unsupported and duplicate files, MIME validation, and detailed logging. Unit tests were added to ensure these features work as intended. Additionally, the team worked on creating and testing the consent form for external service usage, ensuring responses are correctly stored in the database. Everyone reviewed and refined multiple PRs, aligning coding progress with the finalized system design.

### Burnup chart

![Burnup chart for Oct 6 - 12](screenshots/Burnup-Oct6-12.png)

### Github usernames

| GitHub Username | Student Name          |
| --------------- | --------------------- |
| `AdaraPutri`    | Adara Putri           |
| `ammaarkhan`    | Ammaar Khan           |
| `ivonanicetin`  | Ivona Nicetin         |
| `johaneshp`     | Johanes Hamonangan    |
| `salmavkh`      | Salma Vikha Ainindita |
| `taoTimTim`     | Timmi Draper          |

### Table view of completed tasks by username

| GitHub Username | Screenshot                                                                |
| --------------- | ------------------------------------------------------------------------- |
| `AdaraPutri`    | ![Completed tasks for Adara](screenshots/Completed-Adara-Oct6-12.png)     |
| `ammaarkhan`    | ![Completed tasks for Ammaar](screenshots/Completed-Ammaar-Oct6-12.png)   |
| `ivonanicetin`  | ![Completed tasks for Ivona](screenshots/Completed-Ivona-Oct6-12.png)     |
| `johaneshp`     | ![Completed tasks for Johanes](screenshots/Completed-Johanes-Oct6-12.png) |
| `salmavkh`      | ![Completed tasks for Salma](screenshots/Completed-Salma-Oct6-12.png)     |
| `taoTimTim`     | ![Completed tasks for Timmi](screenshots/Completed-Timmi-Oct6-12.png)     |

### Table view of in progress tasks by username

Not applicable – no tasks in progress.

## (Week 7) Monday 13th - Sunday 19th October

### Week recap:

This week, the team continued implementation work for Milestone 1, completing several major system features. Timmi added the Pull Request template, fixed a Windows-specific MIME-type detection bug to ensure consistent file recognition across platforms, and completed the integration of ZIP file parsing with metadata storage in the local SQLite database. Salma implemented user-configuration storage, enabling persistent saving of user consent preferences (accepted and rejected for both LLM usage and file parsing). Ivona completed the feature for detecting and identifying the programming language and framework used in uploaded coding projects. Ammaar developed the feature that distinguishes individual projects from collaborative ones, allowing the system to identify when files belong to shared repositories versus solo workspaces for more accurate contribution tracking. Johanes implemented the alternative analysis feature, ensuring that when user data cannot be sent to an external service, the system automatically performs a local analysis to maintain functionality and data privacy. Adara implemented the advanced text function, which analyzes text files using LLM and prints the metrics found to the user.

### Burnup chart

![Burnup chart for Oct 13 - 19](screenshots/week7-burnupchart.png)

### Github usernames

| GitHub Username | Student Name          |
| --------------- | --------------------- |
| `AdaraPutri`    | Adara Putri           |
| `ammaarkhan`    | Ammaar Khan           |
| `ivonanicetin`  | Ivona Nicetin         |
| `johaneshp`     | Johanes Hamonangan    |
| `salmavkh`      | Salma Vikha Ainindita |
| `taoTimTim`     | Timmi Draper          |

### Table view of completed tasks by username

| GitHub Username | Screenshot                                                                    |
| --------------- | ----------------------------------------------------------------------------- |
| `AdaraPutri`    | ![Completed tasks for Adara](screenshots/Completed-Adara-Oct13-Oct19.png)     |
| `ammaarkhan`    | ![Completed tasks for Ammaar](screenshots/Completed-Ammaar-Oct13-Oct19.png)   |
| `ivonanicetin`  | ![Completed tasks for Ivona](screenshots/Completed-Ivona-Oct13-Oct19.png)     |
| `johaneshp`     | ![Completed tasks for Johanes](screenshots/Completed-Johanes-Oct13-Oct19.png) |
| `salmavkh`      | ![Completed tasks for Salma](screenshots/Completed-Salma-Oct13-Oct19.png)     |
| `taoTimTim`     | ![Completed tasks for Timmi](screenshots/Completed-Timmi-Oct13-Oct19.png)     |

### Table view of in progress tasks by username

Not applicable – no tasks in progress.

## (Week 8) Monday 20th - Sunday 26th October

### Week recap:

This week, the team focused on improving the analysis pipeline, database consistency, and overall user experience. Ammaar implemented a fix ensuring that the program exits cleanly when a user declines consent, and updated the parsing process so that each file now stores its associated project name, making downstream grouping and analysis more reliable. Timmi developed the project-type classification feature, enabling automatic detection of whether a project is code- or text-based and routing it accordingly. She also added a safeguard to prevent duplicate ZIP uploads from being reprocessed in the database. Salma refined the send_to_analysis flow by adding user prompts between individual and collaborative analysis phases, reorganizing functions for clarity, and ensuring a smoother, more modular pipeline. Johanes improved the alternative analysis logic by refining keyword filters, applying POS tagging, and enhancing topic extraction to ensure that only meaningful terms are analyzed during local runs. Ivona refactored the language detection module to align with the new database schema, ensuring accurate identification of languages used in code projects, and added features to detect frameworks of a coding project by identifying the configuration/dependency files in a given project. Adara fixed an issue where ZIP uploads containing only files (and no folders) caused the program to stop, and added an LLM-based code analysis feature that generates resume-style summaries for entire code project by extracting README content, function definitions, and comments across each folder.

Plan for next week:
Next week, the team plans to continue to implement the milestone 1 requirements.
Adara plans to keep implementing the code and text file analysis.
Ammaar will implement deleting the `zip_data` folder after parsing.
Ivona plans to implement better language/framework detection to include more languages and frameworks.
Timmi plans to cotinue implementing more file analysis and to add more duplications checks.
Johanes plans to continue implementing analysis of code.
Salma plans to continue developing the code collaborative analysis for global summaries from all projects (possibly using LLMs), refactor the code, and move on to non-code collaborative analysis.

We're going to meet virtually on Monday to discuss further about our plans.

### Burnup chart

![Burnup chart for Oct 20 - 26](screenshots/week8-burnupchart.png)

### Github usernames

| GitHub Username | Student Name          |
| --------------- | --------------------- |
| `AdaraPutri`    | Adara Putri           |
| `ammaarkhan`    | Ammaar Khan           |
| `ivonanicetin`  | Ivona Nicetin         |
| `johaneshp`     | Johanes Hamonangan    |
| `salmavkh`      | Salma Vikha Ainindita |
| `taoTimTim`     | Timmi Draper          |

### Table view of completed tasks by username

| GitHub Username | Screenshot                                                                    |
| --------------- | ----------------------------------------------------------------------------- |
| `AdaraPutri`    | ![Completed tasks for Adara](screenshots/Completed-Adara-Oct20-Oct26.png)     |
| `ammaarkhan`    | ![Completed tasks for Ammaar](screenshots/Completed-Ammaar-Oct20-Oct26.png)   |
| `ivonanicetin`  | ![Completed tasks for Ivona](screenshots/Completed-Ivona-Oct20-Oct26.png)     |
| `johaneshp`     | ![Completed tasks for Johanes](screenshots/Completed-Johanes-Oct20-Oct26.png) |
| `salmavkh`      | ![Completed tasks for Salma](screenshots/Completed-Salma-Oct20-Oct26.png)     |
| `taoTimTim`     | ![Completed tasks for Timmi](screenshots/Completed-Timmi-Oct20-Oct26.png)     |

### Table view of in progress tasks by username

| GitHub Username | Screenshot                                                                   |
| --------------- | ---------------------------------------------------------------------------- |
| `ivonanicetin`  | ![In-Progress Task for Ivona](screenshots/In-Progress-Ivona-Oct20-Oct26.png) |

## (Week 9) Monday 27th October – Sunday 2nd November

### Week recap

The team focused on improving project-level analysis and expanding what data we can work with. Adara refactored both text and code LLM pipelines so each project now produces git-aware metrics, project summaries, and contribution highlights, all organized by project folder. Ammaar added cleanup functionality to delete the extracted ZIP workspace after processing and switched our language detector to Pygments, which lets us support way more programming languages. Ivona set up the Google Drive OAuth flow so users can authorize and pull their cloud documents directly into our analysis pipeline. Johanes built the first version of individual code metrics that work outside the LLM path, giving us consistent baselines even when users don't consent to LLM usage. Salma streamlined the collaborative code analyzer by reusing our language and framework detectors and improving the non-LLM summaries we generate from git history. Timmi implemented the GitHub OAuth handshake so collaborative projects can connect to repositories for better contribution breakdowns later on.

### Plan for the next cycle

- Adara will improve the code LLM flow by handling repos without git data and better README ingestion, plus align text output formatting with the code analyzer.
- Ammaar will start updating the database schema to store metrics and help with the external API data analysis.
- Ivona will keep expanding framework detection coverage and look into contribution metrics from the newly fetched Drive files.
- Johanes will save the new project metrics into the database so they can power future dashboards.
- Salma will iterate on the non-LLM collaborative summaries by adding NLP cleanup and storage based on team feedback.
- Timmi will use the new OAuth flow to pull contribution data from GitHub and continue refactoring the main CLI flow.

### Burnup chart

![Burnup chart for Oct 27 - Nov 2](screenshots/week9-burnupchart.png)

### Github usernames

| GitHub Username | Student Name          |
| --------------- | --------------------- |
| `AdaraPutri`    | Adara Putri           |
| `ammaarkhan`    | Ammaar Khan           |
| `ivonanicetin`  | Ivona Nicetin         |
| `johaneshp`     | Johanes Hamonangan    |
| `salmavkh`      | Salma Vikha Ainindita |
| `taoTimTim`     | Timmi Draper          |

### Table view of completed tasks by username

| GitHub Username | Screenshot                                                                   |
| --------------- | ---------------------------------------------------------------------------- |
| `AdaraPutri`    | ![Completed tasks for Adara](screenshots/Completed-Adara-Oct27-Nov2.png)     |
| `ammaarkhan`    | ![Completed tasks for Ammaar](screenshots/Completed-Ammaar-Oct27-Nov2.png)   |
| `ivonanicetin`  | ![Completed tasks for Ivona](screenshots/Completed-Ivona-Oct27-Nov2.png)     |
| `johaneshp`     | ![Completed tasks for Johanes](screenshots/Completed-Johanes-Oct27-Nov2.png) |
| `salmavkh`      | ![Completed tasks for Salma](screenshots/Completed-Salma-Oct27-Nov2.png)     |
| `taoTimTim`     | ![Completed tasks for Timmi](screenshots/Completed-Timmi-Oct27-Nov2.png)     |

### Table view of in progress tasks by username

| GitHub Username | Screenshot                                                                   |
| --------------- | ---------------------------------------------------------------------------- |
| `ivonanicetin`  | ![In-progress tasks for Ivona](screenshots/In-Progress-Ivona-Oct27-Nov2.png) |
| `taoTimTim`     | ![In-progress tasks for Timmi](screenshots/In-Progress-Timmi-Oct27-Nov2.png) |

## (Week 10) Monday November 3 - Sunday November 9

### Week recap

This week, the team focused on improving how different parts of the system work together and ensuring the analysis pipeline runs smoothly across all file types. We added support for CSV files, linked Google Drive and GitHub data more effectively, and made sure results from both LLM and non-LLM analyses are stored consistently in the database. The main workflow was cleaned up to reduce repetition and make the overall process easier to follow, while user prompts and summaries were refined to produce clearer and more useful outputs. Through code reviews, shared testing, and close collaboration, the team resolved several integration issues and strengthened the overall reliability and flow of the project.

### Plan for the next cycle

The team will focus on linking related modules and improving data connections across the system. The CSV analysis will be connected to text outputs to make dataset results more complete and readable, while CSV metadata extraction will be expanded to support Google Sheets through the Google Drive API. The team will continue improving collaboration analysis by refining Google Drive and GitHub integrations, adding more API calls, and fixing remaining bugs. More tables and metrics will be added to the database (e.g., non-LLM code collaborative results) to make analysis outputs easier to track and reuse. Work will also continue on refining the database structure, cleaning up code, and organizing the repo structure into subfolders and helper files for better readability and maintenance.

### Burnup chart

![Burnup chart for Nov 3 - Nov 9](screenshots/week10-burnupchart.png)

### Github usernames

| GitHub Username | Student Name          |
| --------------- | --------------------- |
| `AdaraPutri`    | Adara Putri           |
| `ammaarkhan`    | Ammaar Khan           |
| `ivonanicetin`  | Ivona Nicetin         |
| `johaneshp`     | Johanes Hamonangan    |
| `salmavkh`      | Salma Vikha Ainindita |
| `taoTimTim`     | Timmi Draper          |

### Table view of completed tasks by username

| GitHub Username | Screenshot                                                                  |
| --------------- | --------------------------------------------------------------------------- |
| `AdaraPutri`    | ![Completed tasks for Adara](screenshots/Completed-Adara-Nov3-Nov9.png)     |
| `ammaarkhan`    | ![Completed tasks for Ammaar](screenshots/Completed-Ammaar-Nov3-Nov9.png)   |
| `ivonanicetin`  | ![Completed tasks for Ivona](screenshots/Completed-Ivona-Nov3-Nov9.png)     |
| `johaneshp`     | ![Completed tasks for Johanes](screenshots/Completed-Johanes-Nov3-Nov9.png) |
| `salmavkh`      | ![Completed tasks for Salma](screenshots/Completed-Salma-Nov3-Nov9.png)     |
| `taoTimTim`     | ![Completed tasks for Timmi](screenshots/Completed-Timmi-Nov3-Nov9.png)     |

### Table view of in progress tasks by username

| GitHub Username | Screenshot                                                                  |
| --------------- | --------------------------------------------------------------------------- |
| `ivonanicetin`  | ![In-progress tasks for Ivona](screenshots/In-Progress-Ivona-Nov3-Nov9.png) |
| `taoTimTim`     | ![In-progress tasks for Timmi](screenshots/In-Progress-Timmi-Nov3-Nov9.png) |
| `salmavkh`      | ![In-progress tasks for Timmi](screenshots/In-Progress-Salma-Nov3-Nov9.png) |

## (Week 12) Monday November 17 - Sunday November 23

### Week recap

This week, the team focused on completing the remaining core requirements for Milestone 1, with a stronger emphasis on generating skill oriented outputs for the portfolio and resume. This work was complemented by refactoring pipelines and the database, implementing new features, and carrying out targeted feature optimizations. We implemented text and code activity type detection using filenames for both domains and PR keyword signals for code, and ensured all results are persisted in the database. We also refactored the overall repository structure by introducing clearer subfolders and reorganizing the database layer by splitting db.py into a schema module and table specific query modules. In parallel, we continued implementing storage for key analysis outputs including activity types, skill extraction results, contribution data, and project summaries so the entire analysis pipeline now persists consistently across the system. Collaborative workflows were strengthened by improving file contribution tracking, optimizing Google Drive integration, and enhancing text and code detectors. Overall, this week concentrated on solidifying core infrastructure while expanding functionality to support more accurate and scalable project analysis.

### Plan for the next cycle

Next week, the team will complete the remaining Milestone 1 requirements. The team will focus on finishing the integration between pipelines and database storage, refining project summary retrieval, reducing unnecessary print output, and completing collaborative text-analysis features such as Google Drive metrics and contribution scoring. We also plan to refine the start-menu interface, improve the clarity of resume and portfolio outputs, and address remaining GitHub API edge cases. Continuous PR review and cleanup will support final stabilization for the upcoming milestone.

### Burnup chart

![Burnup chart for Nov 17 - Nov 23](screenshots/week12-burnupchart.png)

### Github usernames

| GitHub Username | Student Name          |
| --------------- | --------------------- |
| `AdaraPutri`    | Adara Putri           |
| `ammaarkhan`    | Ammaar Khan           |
| `ivonanicetin`  | Ivona Nicetin         |
| `johaneshp`     | Johanes Hamonangan    |
| `salmavkh`      | Salma Vikha Ainindita |
| `taoTimTim`     | Timmi Draper          |

### Table view of completed tasks by username

| GitHub Username | Screenshot                                                                    |
| --------------- | ----------------------------------------------------------------------------- |
| `AdaraPutri`    | ![Completed tasks for Adara](screenshots/Completed-Adara-Nov17-Nov23.png)     |
| `ammaarkhan`    | ![Completed tasks for Ammaar](screenshots/Completed-Ammaar-Nov17-Nov23.png)   |
| `ivonanicetin`  | ![Completed tasks for Ivona](screenshots/Completed-Ivona-Nov17-Nov23.png)     |
| `johaneshp`     | ![Completed tasks for Johanes](screenshots/Completed-Johanes-Nov17-Nov23.png) |
| `salmavkh`      | ![Completed tasks for Salma](screenshots/Completed-Salma-Nov17-Nov23.png)     |
| `taoTimTim`     | ![Completed tasks for Timmi](screenshots/Completed-Timmi-Nov17-Nov23.png)     |


## (Week 13) Monday November 24 - Sunday November 30

### Week recap
This week, the team focused on refactoring and fixing issues, and updated the start menu. Starting from modifying the menu, to give user options such as, retrieve portfolio, retrieve resume, delete insights, etc. Once all skills and metrics produced, project_summaries table started to be filled with necessary information obtained from analysis worked on the previous weeks. Project_summaries table is used in the retrieval of informations such as portfolio and resume, skills list in chronological order, deletion of projects and resume, producing chronological list of project, project ranking. The issues that are fixed and refactored such as file path handling which is now using the project_name from database, file text sections extractions, adding prompt for user's summary in non llm analysis, framework detection path issue, optimization of google drive analysis and word counting fix. Overall, this week concentrated on using all the project_summaries table information to create the portfolio and resume, fulfilling the milestone requirements, and fixing issues that existed from previous weeks. 

### Plan for the next cycle

we'll do optimization needed to improve the performance, and any changes needed for the deliverables of milestone 1. We'll start working on the presentation, updating readme, and demo video. Starting to plan for milestone 2, and any further plans will be discussed after the presentation.

### Burnup chart

![Burnup chart for Nov 24 - Nov 30](screenshots/week13-burnupchart.png)

### Github usernames

| GitHub Username | Student Name          |
| --------------- | --------------------- |
| `AdaraPutri`    | Adara Putri           |
| `ammaarkhan`    | Ammaar Khan           |
| `ivonanicetin`  | Ivona Nicetin         |
| `johaneshp`     | Johanes Hamonangan    |
| `salmavkh`      | Salma Vikha Ainindita |
| `taoTimTim`     | Timmi Draper          |

### Table view of completed tasks by username

| GitHub Username | Screenshot                                                                    |
| --------------- | ----------------------------------------------------------------------------- |
| `AdaraPutri`    | ![Completed tasks for Adara](screenshots/Completed-Adara-Nov24-Nov30.png)     |
| `ammaarkhan`    | ![Completed tasks for Ammaar](screenshots/Completed-Ammaar-Nov24-Nov30.png)   |
| `ivonanicetin`  | ![Completed tasks for Ivona](screenshots/Completed-Ivona-Nov24-Nov30.png)     |
| `johaneshp`     | ![Completed tasks for Johanes](screenshots/Completed-Johanes-Nov24-Nov30.png) |
| `salmavkh`      | ![Completed tasks for Salma](screenshots/Completed-Salma-Nov24-Nov30.png)     |
| `taoTimTim`     | ![Completed tasks for Timmi](screenshots/Completed-Timmi-Nov24-Nov30.png)     |