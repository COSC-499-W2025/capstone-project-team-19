# Testing

## Test Strategy

We use automated tests for the backend and frontend, plus **manual runs** through the CLI when we want to walk through a full upload with real ZIP files.

- **Backend - `pytest`**: Python tests live in `tests/`. Most files test one piece of the pipeline (parsing, analysis, storage, etc.). The `tests/api/` folder tests HTTP routes so the API matches what the app expects.

- **Frontend - Vitest**: React components and pages are tested in `frontend/` with Vitest and React Testing Library. These run in a simulated browser (jsdom), not a real Chrome window.

- **Manual - CLI**: We run `python -m src.main` with sample ZIPs from [Test Data](#test-data) and follow the steps in [Manual Test Scenarios](#manual-test-scenarios). That checks things like project classification, versions, and the text menus (summaries, resume, portfolio) in a realistic way.

## Running Tests

### Backend
Ensure you are in the main directory `/capstone-project-team-19`.

```bash
pytest tests
```

This runs the automated unit and integration test suite for the backend. If everything is set up correctly, you should see the tests pass.

### Frontend

Run the frontend tests from the `/frontend` directory.

```bash
cd frontend
npm install
npm run test:run
```

More information can be found [here](../frontend/README.md).

## Test Data

Test data is located in the `test-data/` directory and includes:

- **Versioned project data**: Used to test deduplication and version tracking
- **Multi-project dataset**: Includes individual and collaborative, code and text projects

These datasets are used in manual CLI testing to validate system behavior across different scenarios.

## Manual Testing (CLI)

### Preparing Input Data (ZIP Upload)

This section describes how to structure input data for testing the system using the CLI.

To keep analysis simple, please structure the folder you zip and upload like this:

1. Place everything inside a single top-level directory (your "root" folder). The ZIP should contain only this folder at its highest level.
2. Inside the root folder you may optionally create subfolders named `individual/` and `collaborative/`.
   - If you create these folders, add each project as a subfolder beneath the appropriate one. Every subfolder under `individual/` is treated as an individual project; every subfolder under `collaborative/` is treated as a collaborative project.
3. If you do **not** create `individual/` or `collaborative/`, simply keep each project as a child folder directly under the root. The CLI will then ask you to classify each project one-by-one.
   - Any loose files left directly in the root (not inside a project folder) are ignored during analysis, so be sure to nest everything you want processed inside a project directory.

Example structures:

```
my-workspace/
├── individual/
│   ├── blog-site/
│   └── data-journal/
└── collaborative/
    ├── hackathon-app/
    └── research-tool/
```

or, if you prefer to classify through the prompts:

```
my-workspace/
├── blog-site/
├── data-journal/
├── hackathon-app/
└── research-tool/
```

After arranging your files, zip the root folder (e.g., zip `my-workspace/` into `my-workspace.zip`) and provide that ZIP file path to the CLI when prompted.

> **Note:**
> Do not change the name of the ZIP folder, it should match the root folder exactly.
> Local .git analysis will not work if the folder names do not match.

### Preparing a Local `.git` Repository for Collaborative Analysis

1. **Find your repo**

   - Use a collaborative repo (with multiple authors).

2. **Clone locally**

   - Run:
     ```bash
     git clone <repo-url>
     ```
   - Use **Terminal (macOS)** or **Command Prompt/PowerShell (Windows)**.
     > Don’t download the ZIP — it won’t include `.git` history.

3. **Place the repo**

   - Put the cloned folder either in:
     ```
     root/collaborative/
     ```
     or directly in the **root** (without `collaborative/`).

4. **Zip the folder**
   - From the **root**, compress it into a `.zip`.

### Versioning and Deduplication

The system supports multiple versions of the same project (e.g., re-uploads). When you upload a ZIP:

- **Re-upload of identical content** – Automatically skipped (no duplicate analysis).
- **Re-upload with changes** – You can choose: **skip**, **new project** (treat as separate), or **new version** (add as a new run of the same project).
- Each version gets a `version_key`; files and metrics are stored per version.
- In the API, use `project_key` and `version_key` from `state.dedup_project_keys` and `state.dedup_version_keys` when working with upload flow.

## Manual Test Scenarios
### Versioned Project (Two Snapshots of the Same Project)

These two zips represent the same collaborative code project at different points in time. Upload v1 first, then v2 to test versioning and deduplication.

**v1: Early snapshot** (`test-data/code_collab_proj_v1.zip`):
A Flask-based task management API with basic models, routes, and one test file (8 files total).

```
v1_root/
└── code_collab_proj/
    ├── app/
    │   ├── __init__.py
    │   ├── models.py          # Task, User, Project models
    │   ├── task_service.py    # Basic CRUD service
    │   └── routes.py          # REST endpoints
    ├── test/
    │   ├── __init__.py
    │   └── test_models.py
    ├── doc/
    │   └── README.md
    └── requirements.txt
```

**v2: Later snapshot** (`test-data/code_collab_proj_v2.zip`):
The same project with expanded models, a new comment system, utility helpers, and additional tests (12 files total).

```
v2_root/
└── code_collab_proj/
    ├── app/
    │   ├── __init__.py
    │   ├── models.py            # Expanded: Comment, Priority enum added
    │   ├── task_service.py      # Enhanced: filtering, sorting, statistics
    │   ├── comment_service.py   # NEW: comment threading system
    │   ├── utils.py             # NEW: date/slug/pagination helpers
    │   └── routes.py            # Expanded: comment + stats endpoints
    ├── test/
    │   ├── __init__.py
    │   ├── test_models.py       # Expanded: comment + priority tests
    │   ├── test_task_service.py # NEW: service layer tests
    │   └── test_utils.py        # NEW: utility function tests
    ├── doc/
    │   └── README.md            # Updated with new endpoints
    └── requirements.txt
```

**How to test versioning:**

1. Run `python -m src.main`
2. Enter a username (e.g. `test_user`)
3. Choose option `1` (Analyze new project)
4. Accept consent (`y`), decline external services (`n`), decline verbose (`n`)
5. Enter path: `test-data/code_collab_proj_v1.zip`
6. Classify as collaborative (`c`), code project (`c`)
7. When prompted, use these suggested answers:
   - **Project summary:** `A Flask task management API with CRUD operations`
   - **Your contribution:** `Built the task service layer and REST API routes`
   - **Enhance with GitHub data:** `n`
   - **Your role:** `Backend Developer`
8. After v1 completes, choose option `1` again and upload `test-data/code_collab_proj_v2.zip`
9. The system will detect it as a version of the same project — choose `v` (new version)
10. Answer the same prompts with updated descriptions:
    - **Project summary:** `A Flask task management API with comments and enhanced filtering`
    - **Your contribution:** `Added the comment system and utility helpers`
    - **Enhance with GitHub data:** `n`
    - **Your role:** `Backend Developer`

### Multi-Project Upload (Individual + Collaborative, Code + Text)

A single zip containing four projects covering all combinations of project type and mode (`test-data/multi_project_test_data.zip`).

```
multi_root/
├── code_indiv_proj/        # Individual code project
│   ├── src/
│   │   ├── calculator.py   # Scientific calculator module
│   │   ├── converter.py    # Unit converter module
│   │   └── __init__.py
│   ├── test/
│   │   ├── test_calculator.py
│   │   ├── test_converter.py
│   │   └── __init__.py
│   ├── doc/
│   │   └── README.md
│   └── requirements.txt
│
├── code_collab_proj/       # Collaborative code project
│   ├── app/
│   │   ├── models.py           # Inventory data models
│   │   ├── inventory_service.py # Business logic
│   │   ├── routes.py           # Flask API endpoints
│   │   └── __init__.py
│   ├── test/
│   │   ├── test_inventory.py
│   │   └── __init__.py
│   ├── doc/
│   │   └── README.md
│   └── requirements.txt
│
├── text_indiv_proj/        # Individual text project
│   ├── research_paper.txt  # Main document (remote work study)
│   ├── notes.txt           # Supporting notes
│   └── survey_results.csv  # Survey data
│
└── text_collab_proj/       # Collaborative text project
    ├── project_proposal.txt
    ├── design_document.txt # Main document
    ├── meeting_minutes.txt
    └── task_tracking.csv
```

**How to test multi-project upload:**

1. Run `python -m src.main`
2. Enter a username (e.g. `multi_test_user`)
3. Choose option `1` (Analyze new project)
4. Accept consent (`y`), decline external services (`n`), decline verbose (`n`)
5. Enter path: `test-data/multi_project_test_data.zip`
6. The system may detect similarity between code projects — choose `n` (new project)
7. Classify as mixed (`m`), then for each project:
   - `code_collab_proj` → `c` (collaborative)
   - `code_indiv_proj` → `i` (individual)
   - `text_collab_proj` → `c` (collaborative)
   - `text_indiv_proj` → `i` (individual)
8. When asked about project type for code projects (they contain both code and text files), choose `c` (code)

**Individual projects run first.** Use these suggested answers:

| Prompt | Suggested answer |
|--------|-----------------|
| Connect to GitHub? | `n` |
| Project summary (code_indiv_proj) | `A Python utility library with calculator and unit converter` |
| Your work on code_indiv_proj | `Built the calculator and converter modules with full test coverage` |
| Your role on code_indiv_proj | `Developer` |
| Main file selection (text_indiv_proj) | Press Enter (auto-selects largest) |
| Summary for text file | `A research paper on remote work and developer productivity` |
| Your work on text_indiv_proj | `Wrote the research paper and collected survey data` |
| Your role on text_indiv_proj | `Lead Author` |

**Collaborative projects run second.** Use these suggested answers:

| Prompt | Suggested answer |
|--------|-----------------|
| Project summary (code_collab_proj) | `An inventory management REST API built with Flask` |
| Your contribution to code_collab_proj | `Implemented the inventory service layer and API routes` |
| Enhance with GitHub data? | `n` |
| Your role on code_collab_proj | `Backend Developer` |
| Connect Google Drive? (text_collab_proj) | `n` |
| Main file selection | Press Enter (auto-selects largest) |
| Summary for text file | Press Enter (skip) |
| Sections you worked on | `1` |
| Your contribution to text_collab_proj | `Wrote the technical design document and task tracking` |
| Supporting TEXT files | `1` |
| CSV files | `1` |
| Contribution types (comma-separated) | `1,3` (Writing, Research) |
| Your role on text_collab_proj | `Project Manager` |

After all analyses complete, the system returns to the main menu. You can then:
- **Option 2**: View project summaries for all 4 projects
- **Option 3**: Create a resume (aggregates top projects)
- **Option 4**: View portfolio (ranked project cards)
- **Option 7**: View all projects ranked by importance

These test scenarios demonstrate that the system correctly handles individual and collaborative projects, versioning, and diverse input structures.