# Personal Log - Ammaar

## (Week 3) Monday 15th - Sunday 21st September

![Screenshot of work done this sprint from peer eval](./screenshots/Ammaar-Sept-15-21.png)

Week recap: Worked with the team on creating a list of functional and non-functional requirements. On Wednesday, during class we met with other teams and compared requirements.

## (Week 4) Monday 22nd - Sunday 28th September

![Screenshot of work done this sprint from peer eval](./screenshots/Ammaar-Sept22-28.png)

Week recap: This week I focused on API research and authentication architecture. I did a deep dive into GitHub's authentication options, comparing GitHub Apps versus GitHub OAuth and mapping how each approach aligns with our required REST API calls. I also researched the Google Drive API authentication flow and identified the specific endpoints we'll need.

Building on Adara's comprehensive GitHub endpoint research, I expanded our system architecture diagram to incorporate GitHub processes. I also expanded the architecture around the code/script function and added to the dashboard visualization components for both local code analysis and GitHub-specific analysis features.

On the documentation side, I updated and revised our use case descriptions based on the UML case diagram that Ivona and Adara created. I also assisted Johanes with updating the file function in the system architecture when he encountered access issues with the Figma file.

Finally, I converted our project proposal from Word format to Markdown as required for submission.

## (Week 5) Monday 29th September - Sunday 5th October

![Screenshot of work done this sprint from peer eval](./screenshots/Ammaar-Sept29-Oct5.png)

Week recap: On Monday, our team worked together to create the DFD Level 0 and Level 1 diagrams. We finalized the main processes, data flows, and external entities, making sure the diagrams aligned with our functional requirements and system architecture.

On Wednesday, we joined the in-class activity where we rotated between different teams to compare DFDs. This gave us useful insights into how other groups represented their processes, especially around metrics extraction, artifact databases, and error handling. The comparison helped us refine our understanding of what details our diagrams capture well and what areas might need more specificity.

## (Week 6) Monday 6th October - Sunday 12th October

![Screenshot of work done this sprint from peer eval](./screenshots/Ammaar-Oct6-12.png)

Week recap: This week we kicked off implementation and started coding! I had the chance to collaborate with Adara on refining our DFD and system architecture diagram. After reviewing the professor's updated requirements, I made some adjustments to the level 1 data flow diagram, and Adara helped ensure everything stayed in sync between our diagrams.

I also had the chance to collaborate with the team through several PR reviews:

1. Timmi's environment setup PR was solid - I added a quick note in the readme for Mac users since I'd run into that issue myself.

2. Salma's consent feature was well-structured - I suggested a couple of small tweaks to make sure it behaves exactly as we want, and she quickly addressed them.

3. Timmi's parsing PR was great - I noticed one test failing (probably from the main merge) and discovered something interesting about the file paths when running commands from different directories.

4. Johannes' WBS was well-organized - I did some reading on WBS best practices and shared a few ideas on how we might expand it to cover more of our requirements comprehensively.

## (Week 7) Monday 13th October - Sunday 19th October

![Screenshot of work done this sprint from peer eval](./screenshots/Ammaar-Oct13-19.png)

Week recap: Focused on the project classification flow. I extended the backend to persist project tags, updated the CLI to auto-detect `individual/` and `collaborative/` folder structures, and added Markdown support in the parser so doc-heavy projects are recognized. I also updated the README with ZIP-prep instructions. Wrapped up with a dedicated test suite covering the new layout analyzer and confirmed the existing consent/user configuration tests still pass.

As for PR reviews, I reviewed Timmi’s parsing to DB PR to make sure the new schema changes fit smoothly with the parsing flow. I also reviewed Johanes' PR on alternate analysis methods and provided some feedback.

## (Week 8) Monday 20th October - Sunday 26th October

![Screenshot of work done this sprint from peer eval](./screenshots/Ammaar-Oct20-26.png)

Week recap: I merged the Store Raw Project Info PR (#117) so every parsed file now gets saved with its project name. That change means downstream analysis can group artifacts without re-checking folder paths. I linked the parser straight into the `projects` table and updated the schema. I also worked on the “reject consent first” bug (#116). I wrote a regression test, and confirmed the UI flow is accurate to the logic we intended.

Next week’s focus: implement the cleanup that deletes `zip_data/` right after parsing and analysis (this was agreed upon by the team).

## (Week 9) Monday 27th October - Sunday 2nd November

![Screenshot of work done this sprint from peer eval](./screenshots/Ammaar-Oct27-Nov2.png)

Week recap: This week I worked on two features and reviewed two PRs. I also updated the team log with everyone's contributions.

For my first PR (#140), I added cleanup functionality to delete the `zip_data/` folder after parsing is done. Timmi suggested moving the cleanup call from `prompt_and_store()` to `main()` to keep responsibilities separate, which made sense. I refactored it and added unit tests. 

For my second PR (#142), I replaced our hard-coded language detection with Pygments so we can now recognize way more file types: Rust, Go, Kotlin, TypeScript, Swift, and others. This really broadens what our system can analyze for building portfolios and resumes later on.

On the PR review side, I reviewed Timmi's GitHub OAuth PR (#152). Found a few issues during testing. Timmi fixed everything quickly and got it working smoothly.

I also reviewed Adara's text analysis refactoring PR (#160). I noticed analysis only worked for PDFs initially and project names weren't displaying correctly. She fixed both issues, added markdown support, and synced with the main branch. Everything passed after her changes.

Next week's focus: I'll be working on updating the database schema and connecting the Google Drive API.

## (Week 10) Monday 3rd November - Sunday 9th November

![Screenshot of work done this sprint from peer eval](./screenshots/Ammaar-Nov3-Nov9.png)

Week recap: This week I worked on two feature PRs and reviewed three PRs from teammates.

For my first feature PR (#182), I expanded our framework detection from 14 frameworks to over 100, covering Python web frameworks (Django, Flask, FastAPI, Tornado), JavaScript/TypeScript frameworks (React, Vue, Next.js), mobile frameworks (React Native, Expo), CSS frameworks (Material-UI, Sass), build tools (Vite, Webpack), ORMs (Prisma), and state management libraries (Redux, Zustand). I also refactored the test file by creating a `_test_framework_detection()` helper function to cut down on boilerplate, which made the tests way cleaner.

For my second feature PR (#193), I added storage for offline text analysis metrics so we can reuse results later. I created a new `text_offline_metrics` table linked to `project_classifications`, added DB helper functions (`get_classification_id` and `store_text_offline_metrics`), and modified `alternative_analysis()` to return its summary so it can be persisted. I also added comprehensive unit tests covering upsert functionality, field preservation during partial updates, and edge cases like missing payloads. Timmi requested additional test coverage for edge cases, so I added tests to ensure existing fields aren't overwritten during updates and that empty/missing fields are handled gracefully.

For PR reviews, I reviewed Salma's collaborative summary improvements (#184). She fixed a bug where manual project descriptions were being requested even when users accepted LLM consent, added a helpful template for user input, and filtered out filler words using NLTK for better keyword extraction. After Timmi's feedback about the template being too text-heavy, she shortened it into a cleaner bullet list. Everything looked good after her changes.

I also reviewed Adara's CSV support PR (#179). She added CSV file handling to the text LLM analysis pipeline with metadata extraction. I noticed there were no unit tests for the new `extractfromcsv()` function and no integration tests showing how CSV metadata flows through the LLM pipeline, so I requested test coverage for these scenarios. Timmi and Ivona found additional issues with file extension validation duplication and errors when CSV was the only file type. Adara added the test cases I requested, refactored to fetch extensions from the database instead of the file path, and created a separate `csv_analyze.py` module to handle CSV files independently. Still waiting for her final updates to approve.

Finally, I reviewed Timmi's GitHub metrics PR (#185). She integrated GitHub OAuth, repo linking, and metrics collection (commits, PRs, issues). The architecture was solid with clear separation between API calls, storage, and orchestration. All tests passed and the GitHub integration worked smoothly when I tested it locally.

Next week's focus: I'll continue working on the database schema updates.
