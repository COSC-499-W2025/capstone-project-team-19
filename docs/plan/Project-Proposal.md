# Features Proposal for Mining Digital Work Artifacts

**Course:** COSC 499 - Capstone Project  
**Instructor:** Bowen Hui  
**Date:** September 28, 2025  
**Team Number:** 19

**Team Members**
- Timmi Draper — 19696624
- Ammaar Khan — 92804954
- Adara Putri — 49733405
- Ivona Nicetin — 87205910
- Salma Vikha Ainindita — 74417296
- Johanes Panjaitan — 39809579

## Project Scope and Usage Scenario

This system is designed to automatically generate portfolios based on selected projects. A user uploads their projects and the system organizes and builds metrics based on the file type and content. Users can upload local files or connect their online accounts (Google Drive, GitHub, OneDrive) via OAuth to select projects stored in the cloud. The data metrics are displayed in a dashboard that users can export as a PDF, DOCX, or CSV file. The system also stores past dashboards, enabling users to compare previous metrics with newly generated ones over time. For example, a newly graduated student who wants to showcase their projects can upload their files, wait for the system to process the data, and receive a visual dashboard of their work to export in various formats for easy sharing.

## Proposed Solution

Our proposed solution is a desktop application that automatically generates portfolios from user-uploaded projects. The system includes six core functions—Text (DOCX and PDF), Video, Image, Audio, CSV, Code (script), GitHub—each designed to handle a specific file type. The system supports integration with online platforms through OAuth, allowing users to securely fetch and analyze files from Google Drive and GitHub in addition to local uploads. These functions extract structured insights such as document topics, coding activity, project timelines, patterns of media usage, and version history. The extracted information is aggregated into metrics, stored securely in a database, and presented through an interactive dashboard. Historical dashboards are versioned and stored, allowing users to revisit and compare older dashboards against the latest ones for a longitudinal view of progress and project growth. Users can export their results into different formats (e.g., PDF, DOCX, or CSV), making it simple to showcase their projects to employers or collaborators.

The solution is unique in its ability to unify diverse work artifacts into one coherent narrative of professional and creative growth. This helps graduating students and early professionals save time, strengthen their portfolios, and gain a competitive advantage in the job market. The tool emphasizes privacy-first design: all processing runs locally, so large or sensitive files never leave the user’s machine unless they explicitly share or export them. In addition, the app includes a clear consent flow that disables the ability to upload projects unless the user has agreed to have their files or folders processed. The system’s capabilities let users showcase everything they have built, turning various projects into a clean, understandable portfolio.

## Use Cases

### Use Case 1: Create Account and Login

- **Primary Actor:** User
- **Description:** Access the app with a personal profile so runs, settings, and exports persist.
- **Precondition:** App installed; network available if using cloud signup (local profiles work offline).
- **Postcondition:** Authenticated session established, user profile loaded.
- **Main Scenario:**
  1. Open the app and choose to create an account or log in.
  2. Enter email and password.
  3. For the first time, complete a minimal profile.
  4. The system stores credentials or a local token and opens the home page.
- **Extensions:**
  - 2a. Invalid details -> system prompts correction.
  - 2b. Forgot password -> reset via email.

### Use Case 2: Consent to File Processing

- **Primary Actor:** User
- **Description:** Provide informed consent before any files are analyzed and indicate which files or folders to include.
- **Precondition:** User is authenticated and on the file upload page.
- **Postcondition:** Consent decision stored with timestamp and policy version.
- **Main Scenario:**
  1. App displays a short consent screen that explains what is processed locally and what is optional.
  2. User accepts and chooses defaults for include/exclude rules.
  3. System records consent and policy version in the profile.
- **Extensions:**
  - 1a. User declines consent -> process canceled.
  - 1b. User revokes consent -> cached data cleared, analysis disabled until re-accepted.

### Use Case 3: Upload Work Artifacts

- **Primary Actor:** User
- **Description:** Provide source materials for analysis from local files or cloud accounts (Google Drive, GitHub).
- **Precondition:** User has granted consent.
- **Postcondition:** Source set created with file inventory, initial metadata, and (for cloud files) verified OAuth authentication.
- **Main Scenario:**
  1. Click New Project -> choose Select folder, Upload zip, or Import from Cloud.
  2. If cloud files are selected, the system initiates OAuth flow with the chosen provider and requests access.
  3. User selects files from local or cloud sources.
  4. System categorizes files into supported types (e.g., PDF, DOCX, etc.).
  5. System checks file size, format validity, and compatibility.
- **Extensions:**
  - 3a. Unsupported or corrupted files are flagged with an error message.
  - 3b. Very large sets -> show estimated time and allow cancel.
  - 3c. OAuth authentication fails -> show error and prompt user to retry or choose local files.

### Use Case 4: View Portfolio Dashboard

- **Primary Actor:** User
- **Description:** Explore results of the latest analysis in one place.
- **Precondition:** At least one analysis run exists for the project.
- **Postcondition:** View state and filters are saved with the project.
- **Main Scenario:**
  1. Open project -> dashboard loads latest run.
  2. Use filters to adjust date range, artifact types, or languages.
  3. Inspect charts, tables, and graphs (e.g., contribution frequency, lines changed, content summary).
- **Extensions:**
  - 1a. No runs yet -> show empty state with run analysis call to action.
  - 1b. Large dataset -> enable virtualized tables and pagination.

### Use Case 5: Export Portfolio

- **Primary Actor:** User
- **Description:** Export current dashboard data to CSV, PDF, or DOCX.
- **Precondition:** A dashboard view is available.
- **Postcondition:** Export file saved to selected path; audit entry recorded.
- **Main Scenario:**
  1. Click "Export."
  2. Choose format.
  3. Confirm; system generates file and shows success toast.
- **Extensions:**
  - 2a. Insufficient disk space or permission denied -> show error banner with retry.
  - 3a. Long export -> show progress indicator and cancel option.

### Use Case 6: View Historical Dashboards

- **Primary Actor:** User
- **Description:** Open results from a previous analysis run.
- **Precondition:** Project has at least one prior run.
- **Postcondition:** Historical run loaded; selection remembered.
- **Main Scenario:**
  1. Go to history.
  2. Browse runs by date.
  3. Select a run to load its dashboard view.
- **Extensions:**
  - 2a. No history -> explain how to create new runs.

### Use Case 7: Compare Dashboards

- **Primary Actor:** User
- **Description:** See differences between two runs side by side.
- **Precondition:** At least two previous runs exist.
- **Postcondition:** Comparison view configured and available for export.
- **Main Scenario:**
  1. From history choose compare.
  2. Select baseline run and target run.
  3. System shows side-by-side metrics, deltas, and highlights.
  4. User toggles view by artifact type, language, or file path.
- **Extensions:**
  - 1a. No history -> explain how to create new runs.

## Requirements, Testing, Requirement Verification

### Tech Stack

- **Frontend (UI)**
  - React (runs inside Electron)
- **Backend (Logic)**
  - Electron using Node.js
  - Python
  - SQLite (storing data locally)
  - OAuth (allows authentication for external providers such as GitHub and Google Drive)
- **Processing Data**
  - `FFmpeg` – splitting audio/video, frame extraction
  - `PySceneDetect` – scene detection
  - `OpenCV` – image preprocessing and metric extraction
  - `Ultralytics YOLO` – object detection
  - `CLIP` – scene/environment detection
  - Microsoft Graph API – version history and metadata extraction for Excel files
  - Google Sheets/Drive API – version history and metadata extraction for Google files
  - GitHub REST API – data extraction from GitHub repositories
  - `pandas` – metrics calculation
  - Google API – Google Drive file extraction
  - `pypdf` / `PyMuPDF` – extraction of PDF text and images
  - `doc2txt` – extraction of text and images from DOC files
  - `zipfile`, `xml.etree.ElementTree`, `openpyxl` – extraction of charts from DOC files then writing data into Excel files
- **Data Visualization**
  - `matplotlib`
  - `seaborn`
- **Testing Tools**
  - Jest (UI)
  - PyTest (Python scripts)
  - Test Driven Development (TDD) with GitHub (CI/CD)
  - Manual usability testing

### Languages

- JavaScript
- Python
- HTML/CSS
- SQL

### Requirement Verification

| Requirement | Description | Test Cases | Owner | H/M/E |
| --- | --- | --- | --- | --- |
| Account Creation | Users must be able to create a new account with required details (username, password, email). | - Create valid account (success)<br>- Duplicate username (error)<br>- Weak password (error)<br>- Duplicate email (error) | Ammaar | M |
| User Login | Existing users must be able to log in with valid credentials. Invalid credentials must be handled gracefully. | - Valid login (success, dashboard shown)<br>- Wrong password (error)<br>- Empty fields (error) | Johanes | E |
| Forgot Password | Users can reset their password securely via email. | - Invalid username (error)<br>- Request password reset (success, email sent)<br>- Reset password page (success)<br>- Invalid email (error)<br>- Reset link used twice (error) | Ammaar | M |
| Consent Agreement | Users must review and agree to consent terms before uploading files. | - Consent given (success, uploading files enabled)<br>- Consent declined (error, uploading disabled)<br>- Consent not asked (error, uploading disabled) | Salma | E |
| File Selection | Users select file(s) for system processing; invalid file types are rejected. | - Upload valid file(s) (success)<br>- Upload invalid file(s) (error) | Timmi | M |
| File Categorization | System categorizes files into supported types (PDF, DOCX, CSV) and checks compatibility. | - All supported file types recognized correctly (success)<br>- Unsupported file types flagged (error)<br>- Corrupted files (error) | Timmi | H |
| Version History Retrieval | System retrieves file version history via API (Google Drive, GitHub) or local snapshots. | - Google Drive version history via API (success)<br>- GitHub commit history via API (success)<br>- Local snapshot diffs detected (success)<br>- No history available (error handled) | Adara | H |
| Data Summarization | System generates summaries of file content (images, words, columns, rows, headers, descriptions) using an LLM API. | - Error state handled<br>- Small CSV summarized correctly<br>- Large file summarized within time limits<br>- Unsupported file (error handled)<br>- API key missing (error handled) | Salma | M |
| Dashboard Visualization | System generates visualizations of project growth over time and metadata summaries. | - Heatmap generated correctly from version history<br>- Pie chart shows correct contribution breakdown<br>- Stacked bar graph shows correct distribution of languages used in code<br>- Card view displays correct metadata<br>- No data (error handled gracefully) | Adara | M |
| Dashboard History & Comparison | The system stores past metrics (not full dashboards). Selecting an old dashboard re-renders it via the visualization module and allows export. | - Generate dashboard (metrics stored successfully)<br>- Select old dashboard (visualization re-renders correctly)<br>- Export old dashboard as PDF (success)<br>- Export old dashboard as DOCX (success)<br>- Export old dashboard as CSV (success)<br>- Attempt to load history with no stored metrics (error handled gracefully) | Ivona | H |
| OAuth Authentication | Users authenticate Google Drive/GitHub accounts for secure API access. | - Compare old vs. new metrics side-by-side (success)<br>- User login via Google OAuth (success)<br>- User login via GitHub OAuth (success)<br>- Consent screen scopes match required permissions<br>- Expired token refresh (success)<br>- Denied permissions (error handled) | Johanes | H |
