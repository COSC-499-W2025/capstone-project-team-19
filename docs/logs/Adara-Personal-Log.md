# Personal Log - Adara

## (Week 3) Monday 15th - Sunday 21st September

![Screenshot of tasks done from this sprint](./screenshots/Adara-Sept15-21.PNG)

Week recap: Collaborated with the team to brainstorm project concept, usage scenarios, and potential features based on project specification in Monday's class, converted discussion bullet points into list of functional and non functional requirements and printed them for Wednesday's class. Compared list with other groups on Wednesday and modified the final requirements list, created team Kanban board on Github.

## (Week 4) Monday 22nd - Sunday 28th September

![Screenshot of tasks done from this sprint](./screenshots/Adara-Sept22-28.PNG)

Week recap: Brainstormed the system architecture diagram with the team and shared it with other teams on Wednesday. Following that, I focused on expanding the CSV and GitHub functions of the diagram. For the CSV component, I broke down the function into smaller steps, identified the metrics we want to generate, and researched approaches for handling different scenarios (local vs. online files, availability of version history, and complexity of CSV content). 

For the GitHub component, I collaborated with Ammaar to research API endpoints and narrow down the most important repository metrics to include. I also explored different dashboard visualizations we’ll need for both CSV and GitHub data, aligning them with the metrics we identified. Along the way, I learned about Google Drive and OneDrive APIs to understand potential online file integrations.

I worked with Ivona to create the UML use case diagram, collaborated with Ammaar, Ivona, and Salma to draft the use case descriptions, and assisted Timmi and Salma in writing the Project Scope and Proposed Solution to ensure it captured all of our system’s key features. I also added several rows to the "Requirements, Testing, and Requirement Verification" section of the proposal.

## (Week 5) Monday 29th September - Sunday 5th October

![Screenshot of tasks done from this sprint](./screenshots/Adara-Sept22-28.PNG)

Week recap: Worked with team on Monday to create DFD level 0 and 1 in class, then finalized some data labeling before printing the DFD for Wednesday's class. Looked through some articles online about how to draw DFDs and what are the differences between the levels to refresh knowledge. Went around swapping and evaluating other team's DFDs with the team on Wednesday and shared my opinion on the findings.

## (Week 6) Monday 6th - Sunday 12th October

![Screenshot of tasks done from this sprint](./screenshots/Adara-Oct6-12.png)

Week recap: Discussed the final project requirements with team in class on wednesday. Then worked on modifying our System Architecture Diagram to better encapsulate all the project requirements; omitting some irrelevant modules, and adding new ones like offline processing modules for when external services are not accessible. Collaborated with Ammaar to make sure both the System Architecture Diagram and DFD Level 1 are aligned. Collaborated with Timmi in coding the requirement "Return error if uploaded file is in wrong format", expanding her work to include unsupported files (instead of just corrupted ones). Also logging failed uploads. Worked on the code/ script for dealing with duplicate files. Added unit tests for both of these features. Responded to feedback on PR by modifying code to consider all edge cases mentioned. Researched about MIME detectors and how to implement them. Reviewed PRs #36, #60, and #71.

## (Week 7) Monday 13th October - Sunday 19th October

![Screenshot of tasks done from this sprint](./screenshots/Adara-Oct13-19.png)

Week recap: Coordinated with team mainly over Discord. Reviewed Johanes’ and Ivona’s feature PRs, providing detailed feedback including suggestions to fix an error in Johanes’ code. Researched how to integrate an LLM into our project for advanced text analysis, focusing on finding the ideal parameters such as temperature and max tokens, and identifying the best free model option (ended up choosing llama 3.1 8b instant using groq). Implemented the LLM-based text analysis module (llm_analyze.py) which generates structured outputs like summaries, inferred skills, and success factors. Integrated it into main.py with proper consent handling. Added progress bar visualization, also researched and drafted unit tests for the LLM module using mocked API responses to ensure test reliability.

## (Week 7) Monday 13th October - Sunday 19th October

![Screenshot of tasks done from this sprint](./screenshots/Adara-Oct20-26.png)

Week recap: This week, I focused on expanding the LLM analysis pipeline to include code projects. I implemented the new code_llm_analyze.py module, which generates summaries based on README content, function headers, and comments passed through the same LLM as last week's. I also refactored helpers.py by moving extraction functions there and adding code specific extractions. I implemented a sanitizer to keep summaries first-person and consistent, removed the old 0/N tqdm prints, and fixed a bug where ZIPs with only files caused the program to stop. I also reviewed five PRs this week, doing additional research on POS tagging and Pygments to give feedback on improving topic modeling and language detection. Discussed with the team (through PR comments and Discord) about whether we should extract files from the database or local path, and if static dictionaries are still the best way to define supported file extensions.

For next week, I plan on further expanding the code llm analysis (individual) to include other metrics than just a summary. For reusability purposes I hope to coordinate with Salma on how to implement her collaborative code metric for this. I also would like to further the text file analysis to also evaluate files on a project level rather than single files as it is currently doing (e.g. analyzing outlines and drafts that makes up one project rather than analyzing each separately).

## (Week 9) Monday 27th October - Sunday 2nd November

![Screenshot of tasks done from this sprint](./screenshots/Adara-Oct27-Nov2.png)

Week recap: This week, I refactored both code_llm_analyze.py and text_llm_analyze.py to improve how project-level analyses are handled. For the text LLM module, I modified the logic so that it now performs analysis at the project folder level instead of analyzing each file individually. For the code LLM module, I reworked both code_llm_analyze.py and project_analysis.py. Initially, I reused Salma’s Git metrics function to display results at the individual code level. However, I later adopted Johanes’ implementation since it provides a more representative view of individual work patterns. Previously, LLM-based summaries were only generated for individual projects, and Git metrics were only available for collaborative ones. After the refactor, when users consent to LLM analysis, both individual and collaborative projects now produce three outputs: git metrics, project summary, and contribution summary.

Next week, I plan to clean up a few inconsistencies. For code_llm_analyze.py, I’ll handle cases where projects don’t have Git history and improve how it locates and reads README.md files for better context in summaries. For text_llm_analyze.py, I’ll fix the incorrect terminal output for project_name and refine how it prints analysis results to make them more consistent with the code LLM flow. Depending on the team's discussion on Monday I may also integrate csv file analysis or pull commit related code as extra input to generate the contribution summary.
