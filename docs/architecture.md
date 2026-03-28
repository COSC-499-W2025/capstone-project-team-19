# System Architecture

![System Architecture Diagram 1](docs/plan/Milestone%202%20System%20Architecture%20Diagram_1.png)

![System Architecture Diagram 2](docs/plan/Milestone%202%20System%20Architecture%20Diagram_2.png)


The System Architecture Diagram outlines the complete pipeline from user data consent through metrics generation and outputs. 
The flow starts when the user login, and choose one of the 11 menu:

- View old project summaries

   List user's past projects that has been analyzed before, and ask user to choose which project summaries the user would like to view.

- View all projects ranked

   Ranking the project based on skills score, collaboration score, activity diversity, and metrics obtained from the analysis.

- View resume items

   Create a frozen resume snapshot or view an existing one. Retrieves data from project_summaries table, rank projects, and includes only the top five project. Show languages and frameworks (for code), summary, contributions, and skills. It also shows skills summary at the bottom of the resume.

   This menu also allows user to export their resume snapshot into DOCX/PDF. 

   User can edit wordings of their resume which is done per project. They can edit contribution summary, project summary, display name, or key role, which can be applied either for a certain resume or globally.

   User can also choose whether to show some of their skills or not in a resume.

- View chronological skills

   Shows skill timeline, what skills obtained, skill level, from what project, and score in a chronological list.

- View project feedback

   Shows improvement suggestions per skill, grouped by skill name.

- Edit project dates

   Lets users manually adjust project start/end dates. Will affect skill timeline, and chronological skills.

- Manage project thumbnails

   Upload or edit project thumbnail images, which will be shown in the portfolio

- View portfolio items

   Display each project with its title, importance score, project type, mode, duration, activity breakdown, skills, and summary. It retrieves data from the project_summaries table.

   User will be able to export their portfolio to PDF/DOCX.

   This menu also allows user to edit their portfolio which will be done per project. They can choose to show some skills, edit summary text, contribution bullets, or display name.

- View all projects

   List all projects chronologically from newest to oldest, and show the date of the project.

- Delete old insight

   Give options for user to delete resume, delete projects, refresh resume based on projects list after deleted, or keep the resume unchanged.

- Analyze new project

   The flow will continue to consent manager, where user will be asked for consent to analyze their files and external services. If consent is granted, the system will parse and inspect the uploaded archive, and files will be sent to analysis layer, then deleted after the analysis done.

   The file type detector and project structure classifier will determine the path of the analysis whether it goes to code/text analysis and individual/collaborative analysis. 

   Before analysis, uploaded ZIP is hashed to detect if it's a re-upload or a new version

   Re-uploads are stored as new versions under the same project, not as duplicates
   
   For all analysis, will go through the Non-LLM analysis first, then if LLM access is granted, summarization of project will be done by LLM, if not, user will be asked to enter their own summary.


   There are four path of analysis:

   - For individual code project, language, framework, complexity, git commits, author, and history will be analyzed. If .git does not exist, it will ask for github integration. If integration not granted, git analysis will be skipped.

   - Individual Text Analysis will go through linguistic and readability analysis, CSV analysis, and activity type detection.

   - Collaborative code project analysis will detect for .git file. If it exist, it will be used to filter user's files, and analyze contribution metrics. Github integration will be asked for despite the existence of .git files. If the user choose to integrate their github account, PRs, Issues, and Commits data will be fetched, and user's individual contribution will be analyzed. The github data will also be used to detect the collaborative skills.

      However, if user chose not to integrate their github data, and if .git does not exist, user will be asked to enter their contribution summary. This summary will be used to detect their contribution by matching filenames, file paths and file content. 

      Code files will go through the language & framework detection and activity type detection.

   - Collaborative text project will ask the user to give access to their google drive. The Google API pipeline will extract contribution by fetching the comments, replies, questions in the document. It will be used to calculate collaborative skill.

      However, if user does not give access to google, user will be asked which files and which part of main file did the user work on. Individual contribution files will be passed to the individual text pipeline and contribution will be calculated.

   All files (and contributed files for collaborative project) will be passed to the skill bucket analysis layer, where existence check of each criteria of each skills will be done. Each skills will have score and will be given level based on it's score.

   Skill bucket itself has the feedback, so when one skill does not hit some criteria, it will give the feedback for that certain criteria. After skill extraction, unmet criteria automatically generate improvement suggestions stored in project_feedback table.

   All of the analysis result has their own tables, and overall project summaries result will be stored to the project_summaries table.

   Activity type analysis has two path:
   - Code Activity, pattern match will be done on filename and PR Title/Body (if github integrated), then stored to database that lists activity type proportion, activity types list and files list for each activity type.

   - Text activity, pattern match will be done on filename. Timestamp will be parsed that will be used to list activity type evolution (created, modified, type listed chronologically)

   After analysis, project is automatically scored and ranked

   Uploaded/extracted files will be deleted after analysis completes.

## Level 1 Data Flow Diagram

![DFD Level 1](docs/plan/DFD_L1_Milestone1.png)

The Level 1 DFD illustrates the complete lifecycle of a project analysis request, beginning with the user selecting an action in the menu and ending with the generation of summaries, skills, and portfolio outputs. When the user initiates a new analysis, the system first manages consent by collecting permissions for local analysis, GitHub integration, Google Drive access, and optional LLM summarization. These selections are stored in the consent and configuration data store so that future analyses remain consistent with the user's preferences.

After the user uploads a zipped project folder, the system validates the archive, extracts its contents, and records file metadata. If the project has been uploaded before, the versioning and deduplication stage detects duplicates and lets the user skip, create a new project, or add a new version. The classification stage then determines project boundaries, identifies file types, and separates individual from collaborative projects. Once classified, projects are sent to the non-LLM analysis pipeline, which performs linguistic metrics, CSV inspection, readability analysis, language and framework detection, Git commit inspection, and contribution inference depending on the project type and available integrations. All extracted metrics and contribution data are written to the analysis results store.

The skill bucket analysis process then evaluates the available evidence, including text and code metrics, contributions, structural features, and activity traces, to produce skill scores and levels. When a skill detector finds no evidence for a criterion, the feedback system generates actionable improvement suggestions for the user. Activity type detection supplements these results by categorizing user behavior over time, such as coding, testing, documentation, or textual revision patterns.

If LLM access is granted, a summarization process enhances the project record with natural language summaries and extracts a key role (e.g., "Backend Developer") from the user's contribution description. Otherwise, the system prompts the user to provide a manual summary and key role. These finalized summaries, along with all metrics, skill outputs, and contribution descriptions, are stored as complete project records.

Because all menu operations draw from the same analysis results store, the user can view ranked projects, retrieve chronological skill timelines, build and edit resumes, view and edit portfolio cards, review skill feedback, manage project thumbnails, edit project dates, export resumes and portfolios to DOCX or PDF, or revisit past analyses without re-running computation. The system is also accessible via a FastAPI layer with JWT authentication, which mirrors CLI functionality through REST endpoints. The DFD illustrates which components interact with external services, which rely on stored data, and where new analysis paths, such as additional detectors or classifiers, can be integrated into the pipeline.