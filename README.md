[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20544404&assignment_repo_type=AssignmentRepo)

# Capstone Project - Mining Digital Work Artifacts

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repo-url> capstone-project-team-19
cd capstone-project-team-19
```

### 2. Create and Activate a Virtual Environment

#### On Windows
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```
**Note for Windows:** If `pytest` returns an error, instead of `.\venv\Scripts\Activate.ps1`, try `source venv/bin/activate`.

#### On Mac/Linux
```bash
python -m venv venv
source venv/bin/activate
```

**Note for Mac users:** If you have multiple Python versions installed or `python` is not found, you may need to use `python3` instead:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip           # Upgrade pip to avoid weird dependency errors
pip install -r requirements.txt
```

### 4. Run Tests
```bash
pytest
```

If everything is set up correctly, you should see the tests pass.

## Work Breakdown Structure

Work breakdown structure will be updated based on [this google sheets](https://docs.google.com/spreadsheets/d/1yeHoVlBvooq_YpePy--oXryqxtmau8V4wUhEGfgpzfs/edit?usp=sharing) 

| No | Module/Functionality | Description | Member(s) | Time Estimation |
|----|----------------------|--------------|------------|------------------|
| **1** | **Project Requirements** |  |  |  |
| 1.1 | Project Requirements | Define project goal, do self research on gathering requirements | All members |  |
| 1.2 | System Architecture | Generate system architecture diagram, use case diagram, DFD based on the requirements | All members |  |
| 1.3 | Project Proposal | Generate project proposal based on requirements and system architecture | All members |  |
| 1.4 | Updated Project Plan | Update project plan based on evaluation, including system architecture diagram, DFD, and requirements | All members |  |
| 1.5 | Local Environment | Setup local environment based on project requirements | Timmi |  |
| **2** | **Backend** |  |  |  |
| 2.1 | External Service Consent Module |  | Salma |  |
| 2.1.1 | Ask for Consent Functionality | Ask user for consent of accessing data | Salma |  |
| 2.1.2 | Consent Store to Database Functionality | Store consent to database for future configuration | Salma |  |
| 2.2 | File Processing Module |  |  |  |
| 2.2.1 | ZIP Extraction Functionality | Parse a specified zipped folder containing nested folders and files |  |  |
| 2.2.2 | File Checking Functionality | Check whether file in the folder is according to accepted file format, return error if not |  |  |
| 2.2.3 | Storing to Database Functionality | Store file metadata in SQLite |  |  |
| 2.3 | Consent Module |  |  |  |
| 2.3.1 | Ask for Consent Functionality | Display permission text and risk |  |  |
| 2.3.2 | Consent Storage | Store consent in database for future configuration |  |  |
| 2.4 | Information Generator Module |  |  |  |
| 2.4.1 | Link to External Service Functionality | Use external service such as LLM to analyze files |  |  |
| 2.4.2 | Alternative Analysis Modules | Implement local analysis alternatives that produce the same metrics |  |  |
| 2.4.3 | Metadata Extraction Functionality | Extract key information for each project/file |  |  |
| 2.4.5 | Skill Extraction Functionality | Extract key skills demonstrated in project |  |  |
| 2.4.6 | Project Identification Functionality | Distinguish individual/collaborative projects, extrapolate individual contributions, extract metrics, identify programming language and framework |  |  |
| 2.4.7 | Project Information Storage Functionality | Store identification result in database |  |  |
| 2.5 | Project Ranking Module |  |  |  |
| 2.5.1 | Project Ranking Functionality | Rank importance of each project based on user's contributions |  |  |
| 2.5.2 | Project Summarizing Functionality | Summarize top-ranked projects |  |  |
| 2.5.3 | Chronological List Functionality | Produce chronological list of projects and skills exercised |  |  |
| **3** | **Frontend** |  |  |  |
| 3.1 | Consent and Permission Display | Display user consent and permission interface |  |  |
| 3.2 | File Upload Visual | Create file upload interface |  |  |
| 3.3 | File Analyzation Tracking Visual | Display the ongoing process of analyzing |  |  |
| 3.4.| Output | Display result in form of dashboard, charts, and summary | | |
| **4** | **Testing and Verification** |  |  |  |
| 4.1 | Unit Testing | Perform unit tests for all modules |  |  |
| 4.2 | Integration Testing | Perform integration testing between modules |  |  |
| **5** | **Documentation & Report** |  |  |  |
| 5.1 | Milestone 1 Documentation | Prepare milestone 1 documentation |  |  |
