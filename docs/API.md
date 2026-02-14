# Capstone Portfolio & Résumé API

This document provides an overview of the API endpoints available in the system. Each section corresponds to a grouping and details the available routes, methods, parameters, and expected responses.

---

## Introduction

Welcome to the **Capstone Portfolio & Résumé API**. This API exposes the project’s analysis and data pipeline as a service. This API is designed to be RESTful, using standard HTTP methods and response codes.

A REST API allows different systems to communicate over HTTP using standard methods such as `GET`, `POST`, `PUT`, and `DELETE`. Each request interacts with the system’s resources, such as “projects”, “skills”, “résumés”, and “portfolios”.

---

## Base URL

When running the API locally using FastAPI’s default configuration, all requests should be made to:

http://localhost:8000

(Note: This may change in deployment or custom configurations.)

---

## Table of Contents

1. [Health](#health)
2. [Authentication](#authentication)
3. [Projects](#projects)
4. [GitHub Integration](#github-integration)
5. [Google Drive Integration](#google-drive-integration)
6. [Uploads Wizard](#uploads-wizard)
6. [Privacy Consent](#privacyconsent)
7. [Skills](#skills)
8. [Resume](#resume)
9. [Portfolio](#portfolio)
10. [Path Variables](#path-variables)
11. [DTO References](#dto-references)
12. [Best Practices](#best-practices)
13. [Error Codes](#error-codes)
14. [Example Error Response](#example-error-response)

---

## **Health**

**Base URL:** `/`

Basic health checkpoint to verify the service is up and responding.

### **Endpoints**

- **Health**
  - **Endpoint**: `GET /health`
  - **Description**: Returns the status of the service.
  - **Response Status**: `200 OK`
  - **Response Body**:
    ```json
    { "status": "ok" }
    ```

---

## **Authentication** (Required)

This API uses **Bearer token authentication**.

### Rule

All endpoints require an access token **except**:

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`

### How to authenticate

1. Register (once): `POST /auth/register`
2. Login: `POST /auth/login` then receive `access_token`
3. Send the token on every request:

**Header**

- `Authorization: Bearer <access_token>`

### Example

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/projects
```

### Error Responses

- `401 Unauthorized` - missing/invalid/expired token

**Base URL:** `/auth`

Handles authentication and security for the endpoints.

### **Endpoints**

- **Register**
  - **Endpoint**: `POST /register`
  - **Description**: Uploads username and password to database. Checks if the username already exists in the database.
  - **Headers**: None.
  - **Response Status**: `201 Created` on success, `400 Bad Request` if username already taken
  - **Request Body**:

  ```json
  {
    "username": "John Doe",
    "password": "securepassword123"
  }
  ```

  - **Response Body**:

  ```json
  {
    "user_id": 1,
    "username": "John Doe"
  }
  ```

- **Login**
  - **Endpoint**: `POST /login`
  - **Description**: Takes in a username and password, checks that the username exists and the password is correct. Returns an authorization (bearer) token that expires after 60 minutes.
  - **Headers**: None.
  - **Response Status**: `200 OK` on success, `401 Unauthorized` if credentials are invalid
  - **Request Body**:

  ```json
  {
    "username": "John Doe",
    "password": "securepassword"
  }
  ```

  - **Response Body**:

  ```json
  {
    "access_token": "token",
    "token_type": "bearer"
  }
  ```

---

## **Projects**

**Base URL:** `/projects`

Handles project ingestion, analysis, classification, and metadata updates.

### **Endpoints**

- **List Projects**
  - **Endpoint**: `GET /projects`
  - **Description**: Returns a list of all projects belonging to the current user.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK`
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "projects": [
          {
            "project_summary_id": 9,
            "project_name": "Project Name herere",
            "project_type": "text",
            "project_mode": "individual",
            "created_at": "2026-01-12 01:51:24"
          }
        ]
      },
      "error": null
    }
    ```
- **GET Project by ID**
  - **Endpoint**: `GET /projects/{project_id}`
  - **Description**: Returns detailed information for a specific project, including full analysis data (languages, frameworks, skills, metrics, contributions).
  - **Path Parameters**:
    - `{project_id}` (integer, required): The project_summary_id of the project to retrieve
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK` on success, `404 Not Found` if project doesn't exist or belong to user
  - **Response DTO**: `ProjectDetailDTO`
  - **Response Body**:
    ```json
            {
        "success": true,
        "data": {
            "project_summary_id": 9,
            "project_name": "My Project",
            "project_type": "code",
            "project_mode": "individual",
            "created_at": "2026-01-12 01:51:24",
            "summary_text": "A web application built with Python and Flask",
            "languages": ["Python", "JavaScript"],
            "frameworks": ["Flask", "React"],
            "skills": ["Backend Development", "Frontend Development"],
            "metrics": {
                "git": {...},
                "code_complexity": {...}
            },
            "contributions": {...}
        },
        "error": null
    }
    ```

- **Project Ranking**
  - **Description**: Returns/updates the ranked list of projects (with computed scores) and supports manual ranking overrides.
  - **Ranking Behavior**:
    - Projects with a `manual_rank` are shown first, sorted by `manual_rank` ascending (1 = highest priority)
    - Remaining projects are sorted by computed `score` descending

  - **Get Project Ranking**
    - **Endpoint**: `GET /projects/ranking`
    - **Description**: Returns all projects in ranked order with computed `score` and (optional) `manual_rank`.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response DTO**: `ProjectRankingDTO`
    - **Response Body**:
      ```json
      {
        "success": true,
        "data": {
          "rankings": [
            {
              "rank": 1,
              "project_summary_id": 9,
              "project_name": "My Project",
              "score": 0.732,
              "manual_rank": 1
            },
            {
              "rank": 2,
              "project_summary_id": 10,
              "project_name": "Another Project",
              "score": 0.701,
              "manual_rank": null
            }
          ]
        },
        "error": null
      }
      ```

  - **Replace Entire Ranking Order**
    - **Endpoint**: `PUT /projects/ranking`
    - **Description**: Replaces the entire manual ranking order. The request must include **every** project for the user (no extras, no missing). The list order becomes `manual_rank = 1..N`.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request DTO**: `ReplaceProjectRankingRequestDTO`
    - **Request Body**:
      ```json
      {
        "project_ids": [10, 9, 12]
      }
      ```
    - **Response Status**: `200 OK`
    - **Response DTO**: `ProjectRankingDTO`
    - **Error Responses**:
      - `400 Bad Request` if `project_ids` contains duplicates OR does not include every project_summary_id for the user
      - `404 Not Found` if any `project_id` does not exist / does not belong to the user

  - **Patch One Project's Manual Rank**
    - **Endpoint**: `PATCH /projects/{project_id}/ranking`
    - **Description**: Sets or clears the manual rank for one project.
    - **Path Parameters**:
      - `{project_id}` (integer, required): The `project_summary_id` of the project to update
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request DTO**: `PatchProjectRankingRequestDTO`
    - **Request Body**:
      - Set manual rank:
- **Project Dates**
    - **Description**: View and manage **manual date overrides** for projects.
        - If a project has manual dates, the API will report `source: "MANUAL"` and return those dates.
        - If a project has no manual dates, the API will report `source: "AUTO"` and return the best available automatic date (if any).
        - Manual dates affect any features that depend on project chronology (e.g., chronological skills, portfolio ordering).

    - **List Project Dates**
        - **Endpoint**: `GET /projects/dates`
        - **Description**: Returns all projects with their effective dates and whether they come from manual overrides or automatic computation.
        - **Auth**:`Authorization: Bearer <access_token>`
        - **Request Body**: None
        - **Response Status**: `200 OK`
        - **Response Body**:
            ```json
            {
                "success": true,
                "data": {
                    "projects": [
                    {
                        "project_summary_id": 9,
                        "project_name": "My Project",
                        "start_date": "2024-01-01",
                        "end_date": "2024-12-31",
                        "source": "MANUAL",
                        "manual_start_date": "2024-01-01",
                        "manual_end_date": "2024-12-31"
                    },
                    {
                        "project_summary_id": 10,
                        "project_name": "Another Project",
                        "start_date": "2025-02-10",
                        "end_date": "2025-03-05",
                        "source": "AUTO",
                        "manual_start_date": null,
                        "manual_end_date": null
                    }
                    ]
                },
                "error": null
            }
            ```

    - **Set / Patch Manual Project Dates**
        - **Endpoint**: `PATCH /projects/{project_id}/dates`
        - **Description**: Sets or clears the manual start/end dates for a single project.
        - **Path Parameters**:
            - `{project_id}` (integer, required): The `project_summary_id` of the project to update
        - **Auth** : `Authorization: Bearer <access_token>`
        - **Request Body**:
            - Set both:
                ```json
                { "start_date": "2024-01-01", "end_date": "2024-12-31" }
                ```
            - Set one side only (leave the other unchanged by omitting it):
                ```json
                { "start_date": "2024-01-01" }
                ```
            - Clear one side only (send `null`):
                ```json
                { "end_date": null }
                ```
        - **Notes**:
            - At least one of `start_date` or `end_date` must be present (sending `{}` returns `422 Unprocessable Entity`)
            - Date format must be `YYYY-MM-DD`
            - Dates cannot be in the future
            - If both are present, `start_date` must be <= `end_date`
        - **Response Status**: `200 OK`
        - **Response Body**:
            ```json
            {
              "success": true,
              "data": {
                    "project_summary_id": 9,
                    "project_name": "My Project",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "source": "MANUAL",
                    "manual_start_date": "2024-01-01",
                    "manual_end_date": "2024-12-31"
              },
              "error": null
            }
            ```
        - **Error Responses**:
            - `400 Bad Request` if date format is invalid, date is in the future, or start_date > end_date
            - `404 Not Found` if the project does not exist / does not belong to the user

    - **Clear Manual Dates for One Project (Revert to Automatic)**
        - **Endpoint**: `DELETE /projects/{project_id}/dates`
        - **Description**: Clears manual date overrides for a project (sets them back to automatic behavior).
        - **Path Parameters**:
            - `{project_id}` (integer, required): The `project_summary_id` of the project to clear
        - **Auth**: `Authorization: Bearer <access_token>`
        - **Request Body**: None
        - **Response Status**: `200 OK`
        - **Response Body**:
            ```json
            {
                "success": true,
                "data": {
                    "project_summary_id": 9,
                    "project_name": "My Project",
                    "start_date": "2025-02-10",
                    "end_date": "2025-03-05",
                    "source": "AUTO",
                    "manual_start_date": null,
                    "manual_end_date": null
                },
                "error": null
            }
            ```
        - **Error Responses**:
            - `404 Not Found` if the project does not exist / does not belong to the user

    - **Reset All Project Dates to Automatic**
        - **Endpoint**: `POST /projects/dates/reset`
        - **Description**: Clears all manual date overrides for the current user.
        - **Auth**: `Authorization: Bearer <access_token>`
        - **Request Body**: None
        - **Response Status**: `200 OK`
        - **Response Body**:
            ```json
            {
                "success": true,
                "data": {
                    "cleared_count": 2
                },
                "error": null
            }
            ```

- **Delete Project by ID**
    - **Endpoint**: `DELETE /projects/{project_id}`
    - **Description**: Permanently deletes a specific project and all its associated data (skills, metrics, files, etc.).
    - **Path Parameters**:
        - `{project_id}` (integer, required): The project_summary_id of the project to delete
    - **Query Parameters**:
        - `refresh_resumes` (boolean, optional): If `true`, also removes the deleted project from any résumé snapshots. Résumés that become empty are deleted. Defaults to `false`.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Example Requests**:
        ```bash
        # Delete project (default, resumes unchanged)
        DELETE /projects/9

        # Delete project and update resumes
        DELETE /projects/9?refresh_resumes=true
        ```
    - **Response Status**: `200 OK` on success, `404 Not Found` if project doesn't exist or belong to user
    - **Response Body**:
        ```json
        { "rank": 1 }
        ```
      - Clear manual rank (revert to auto ranking for that project):
        ```json
        { "rank": null }
        ```
      - Note: `rank` is required (sending `{}` will return `422 Unprocessable Entity`)
    - **Response Status**: `200 OK`
    - **Response DTO**: `ProjectRankingDTO`
    - **Error Responses**:
      - `400 Bad Request` if `rank` is less than 1, or greater than the user's project count
      - `404 Not Found` if the project does not exist / does not belong to the user

  - **Reset Ranking to Automatic**
    - **Endpoint**: `POST /projects/ranking/reset`
    - **Description**: Clears all manual ranking overrides for the user (reverts to pure computed ranking).
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response DTO**: `ProjectRankingDTO`

- **Delete Project by ID**
  - **Endpoint**: `DELETE /projects/{project_id}`
  - **Description**: Permanently deletes a specific project and all its associated data (skills, metrics, files, etc.).
  - **Path Parameters**:
    - `{project_id}` (integer, required): The project_summary_id of the project to delete
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK` on success, `404 Not Found` if project doesn't exist or belong to user
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": null,
      "error": null
    }
    ```

- **Delete All Projects**
    - **Endpoint**: `DELETE /projects`
    - **Description**: Permanently deletes all projects belonging to the current user.
    - **Query Parameters**:
        - `refresh_resumes` (boolean, optional): If `true`, also removes deleted projects from any résumé snapshots. Résumés that become empty are deleted. Defaults to `false`.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Example Requests**:
        ```bash
        # Delete all projects (default, resumes unchanged)
        DELETE /projects

        # Delete all projects and update resumes
        DELETE /projects?refresh_resumes=true
        ```
    - **Response Status**: `200 OK`
    - **Response DTO**: `DeleteResultDTO`
    - **Response Body**:
        ```json
        {
            "success": true,
            "data": {
                "deleted_count": 3
            },
            "error": null
        }
        ```

- **Retrieve Project Feedback**
    - **Endpoint**: `GET /{project_id}/feedback`
    - **Description**: Returns all feedback for one project.
    - **Auth**: `Authorization: Bearer <access_token>`
    - **Response Status**: `200 OK`
    - **Response DTO**: `ProjectFeedbackDTO`
    - **Request Body**: None.
    - **Response Body**:
        ```json
        {
            "success": true,
            "data": {
                "project_id": 9,
                "project_name": "My Project",
                "feedback": [
                    {
                        "feedback_id": 1,
                        "project_type": "code",
                        "skill_name": "code_quality",
                        "file_name": "main.py",
                        "criterion_key": "complexity",
                        "criterion_label": "Code Complexity",
                        "expected": "Cyclomatic complexity < 10",
                        "observed": {"max_complexity": 12},
                        "suggestion": "Refactor main() to reduce nested conditions",
                        "generated_at": "2026-01-12 02:15:30"
                    },
                    {
                        "feedback_id": 2,
                        "project_type": "code",
                        "skill_name": "documentation",
                        "file_name": "utils.py",
                        "criterion_key": "docstrings",
                        "criterion_label": "Function Documentation",
                        "expected": "All public functions documented",
                        "observed": {"coverage": 0.75},
                        "suggestion": "Add docstrings to helper_validate() and helper_process()",
                        "generated_at": "2026-01-12 02:15:30"
                    }
                ]
            },
            "error": null
        }
        ```

- **Project Thumbnails**
    - **Description**: Upload, view, and delete thumbnail images for projects. Thumbnails are standardized to PNG format and resized to a maximum of 800x800 px.

    - **Upload Thumbnail**
        - **Endpoint**: `POST /projects/{project_id}/thumbnail`
        - **Description**: Upload or replace a project's thumbnail image. If a thumbnail already exists for the project, it is overwritten (no separate edit/replace endpoint needed). Accepts PNG, JPG, JPEG, and WEBP formats. Images are automatically converted to PNG and resized if larger than 800x800 px.
        - **Path Parameters**:
            - `{project_id}` (integer, required): The `project_summary_id` of the project
        - **Auth**: `Authorization: Bearer <access_token>`
        - **Request Body**: `multipart/form-data`
            - `file` (file, required): Image file (PNG, JPG, JPEG, or WEBP)
        - **Response Status**: `200 OK`
        - **Response DTO**: `ThumbnailUploadDTO`
        - **Response Body**:
            ```json
            {
                "success": true,
                "data": {
                    "project_id": 9,
                    "project_name": "My Project",
                    "message": "Thumbnail uploaded successfully"
                },
                "error": null
            }
            ```
        - **Error Responses**:
            - `401 Unauthorized`: Missing or invalid Bearer token
            - `404 Not Found`: Project not found or doesn't belong to user
            - `422 Unprocessable Entity`: Invalid image file (unsupported format or corrupt image)

    - **Get Thumbnail**
        - **Endpoint**: `GET /projects/{project_id}/thumbnail`
        - **Description**: Download the thumbnail image for a project. Returns the image as a PNG file.
        - **Path Parameters**:
            - `{project_id}` (integer, required): The `project_summary_id` of the project
        - **Auth**: `Authorization: Bearer <access_token>`
        - **Response Status**: `200 OK`
        - **Response**: Binary image download with MIME type `image/png`
        - **Response Headers**:
            - `Content-Type: image/png`
        - **Error Responses**:
            - `401 Unauthorized`: Missing or invalid Bearer token
            - `404 Not Found`: Project not found, or thumbnail not found

    - **Delete Thumbnail**
        - **Endpoint**: `DELETE /projects/{project_id}/thumbnail`
        - **Description**: Remove a project's thumbnail image. Deletes both the database record and the image file on disk.
        - **Path Parameters**:
            - `{project_id}` (integer, required): The `project_summary_id` of the project
        - **Auth**: `Authorization: Bearer <access_token>`
        - **Request Body**: None
        - **Response Status**: `200 OK`
        - **Response Body**:
            ```json
            {
                "success": true,
                "data": null,
                "error": null
            }
            ```
        - **Error Responses**:
            - `401 Unauthorized`: Missing or invalid Bearer token
            - `404 Not Found`: Project not found, or thumbnail not found

---

## **Uploads Wizard**

**Base URL:** `/projects/upload`

Uploads are tracked as a resumable multi-step “wizard” using an `uploads` table. Each upload has:

- an `upload_id`
- a `status` indicating the current step
- a `state` JSON blob storing wizard context (parsed layout, user selections, dedup context, etc.)

### **Upload Status Values**

`uploads.status` is one of:

- `started` – upload session created
- `needs_dedup` – user must resolve dedup “ask” cases (new in dedup refactor)
- `needs_classification` – user must classify projects (individual vs collaborative)
- `parsed` – classifications submitted (temporary state in current implementation)
- `needs_project_types` – user must resolve code vs text for any mixed/unknown projects
- `needs_file_roles` – user must select file roles (e.g., main text file) and related inputs
- `needs_summaries` – user must provide manual summaries (when applicable)
- `analyzing` – analysis running
- `done` – analysis completed
- `failed` – upload failed (error stored in `state.error`)

### **Wizard Flow**

A typical flow for the first six endpoints:

1. **Start upload**: `POST /projects/upload`
   - parses ZIP and computes layout
   - runs dedup:
     - exact duplicates are automatically skipped
     - “ask” cases are stored for UI resolution
     - “new_version” suggestions may be recorded
2. **Poll/resume**: `GET /projects/upload/{upload_id}`
3. **Resolve dedup (optional)**: `POST /projects/upload/{upload_id}/dedup/resolve`
4. **Submit classifications**: `POST /projects/upload/{upload_id}/classifications`
5. **Resolve mixed project types (optional)**: `POST /projects/upload/{upload_id}/project-types`
6. **Select collaborative text contribution sections (optional, text-collab only)**:
   - `GET /projects/upload/{upload_id}/projects/{project_key}/text/sections`
   - `POST /projects/upload/{upload_id}/projects/{project_key}/text/contributions`

Use `project_key` from `state.dedup_project_keys` (keyed by project name) for each project.

---

### **Endpoints**

- **Start Upload**
  - **Endpoint**: `POST /projects/upload`
  - **Description**: Upload a ZIP file, save it to disk, parse the ZIP, and compute the project layout to determine the next wizard step. The server creates an `upload_id` and stores wizard state in the database.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Request Body**: `multipart/form-data`
    - `file` (file, required): ZIP file
  - **Response Status**: `200 OK`

- **Get Upload Status (Resume / Poll)**
    - **Endpoint**: `GET /projects/upload/{upload_id}`
    - **Description**: Returns the current upload wizard state for the given `upload_id`. Use this to resume a wizard flow or refresh the UI.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Path Params**:
        - `{upload_id}` (integer, required): The ID of the upload session
    - **Response Status**: `200 OK` on success, `404 Not Found` if upload doesn't exist or belong to user
    -                 "upload_id": 5,
                "status": "needs_classification",
                "zip_name": "text_projects.zip",
                "state": {
                    "zip_name": "text_projects.zip",
                    "zip_path": "/.../src/analysis/zip_data/_uploads/5_text_projects.zip",
                    "layout": {
                        "root_name": "text_projects",
                        "auto_assignments": {},
                        "pending_projects": [
                            "PlantGrowthStudy"
                        ],
                        "stray_locations": []
                    },
                    "files_info_count": 8
                }
        ```

- **Resolve Dedup (Optional, New)**
  - **Endpoint**: `POST /projects/upload/{upload_id}/dedup/resolve`
  - **Description**: Resolves dedup “ask” cases that were captured during upload parsing. This step happens before classifications and project types.
  - **Headers**:
    - `Authentication`: Bearer <token>
  - **Path Params**:
    - `upload_id` (integer, required)
  - **Request Body**:
    ```json
    {
      "decisions": {
        "PlantGrowthStudy": "new_version"
      }
    }
    ```
  - **Allowed decision values**:
    - `skip` – discard this project from the upload
    - `new_project` – force register this as a new project snapshot
    - `new_version` – force register this as a new version of the best matched existing project
  - **Response Status**: `200 OK`
  - **Response Notes**:
    - Returns `409 Conflict` if upload status is not `needs_dedup`.
    - Returns `422 Unprocessable Entity` if decisions are missing or contain unknown projects.
    - On success, `state.dedup_asks` is cleared and `state.dedup_resolved` is stored.

- **Submit Project Classifications**
  - **Endpoint**: `POST /projects/upload/{upload_id}/classifications`
  - **Description**: Submit the user’s classification choices for projects detected within the uploaded ZIP. This replaces the CLI prompt where users classify each project as `individual` or `collaborative`.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Path Params**:
    - `upload_id` (integer, required)
  - **Request Body**:
    ```json
    {
        "assignments": {
            "Project A": "individual",
            "Project B": "collaborative"
        }
    }
    ```

- **Submit Project Types (Code vs Text) (Optional)**
  - **Endpoint**: `POST /projects/upload/{upload_id}/project-types`
  - **Description**: Submit user selections for project type (`code` vs `text`) when a detected project contains both code and text artifacts and requires a choice. The request must use project names exactly as reported in `state.layout.auto_assignments` and `state.layout.pending_projects`.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Path Params**:
    - `{upload_id}` (integer, required): The ID of the upload session

- **Git Identities (Local Git)**
  - **Description**: Replaces the CLI prompt that asks users to pick their git identity from a local `.git` history.
    - **Notes**:
      - `project_key` is the value from `projects.project_key`.
      - GET returns empty `options` for individual code projects (no collaborator list).
      - POST is allowed only for collaborative code projects.
      - Selection matching uses email or name, so aliases may map to multiple indices.
    - **List Git Identities**
        - **Endpoint**: `GET /{upload_id}/projects/{project_key}/git/identities`
      - **Description**: Returns a ranked list of identities found in the local git history for this project, plus `selected_indices` based on the user’s saved identities.
      - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
        - **Path Params**:
            - `{upload_id}` (integer, required): The upload session ID
            - `{project_key}` (integer, required): The project key
      - **Error Responses**:
        - `401 Unauthorized` if missing or invalid Bearer token
        - `404 Not Found` if the project does not belong to this upload
        - `404 Not Found` if no local Git repo is found for the project
        - `409 Conflict` if the project is not a code project
      - **Response Status**: `200 OK`
      - **Response Body**:
      ```json
      {
        "success": true,
        "data": {
          "options": [
            {
              "index": 1,
              "name": "Test User",
              "email": "test1@example.com",
              "commit_count": 36
            },
            {
              "index": 2,
              "name": "Test User 2",
              "email": "test2@example.com",
              "commit_count": 11
            }
          ],
          "selected_indices": [1]
        },
        "error": null
      }
      ```
    - **Save Git Identity Selection**
        - **Endpoint**: `POST /{upload_id}/projects/{project_key}/git/identities`
      - **Description**: Saves the user’s selected git identities (by index) and optional extra commit emails for future runs.
      - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
        - **Path Params**:
            - `{upload_id}` (integer, required): The upload session ID
            - `{project_key}` (integer, required): The project key
      - **Request Body**:
        ```json
        {
          "selected_indices": [1, 3],
          "extra_emails": ["test.extra@example.com"]
        }
        ```
      - **Error Responses**:
        - `401 Unauthorized` if missing or invalid Bearer token
        - `404 Not Found` if the project does not belong to this upload
        - `404 Not Found` if no local Git repo is found for the project
        - `404 Not Found` if no git identities are found for the project
        - `409 Conflict` if the project is not a code project
        - `409 Conflict` if the project is not collaborative
        - `422 Unprocessable Entity` if any selected index is out of range
      - **Response Status**: `200 OK`
      - **Response Body**:
        ```json
        {
        "success": true,
        "data": {
        "options": [
        {
        "index": 1,
        "name": "Test User",
        "email": "test1@example.com",
        "commit_count": 36
        }
        ],
        "selected_indices": [1]
        },
        "error": null
        }
      ```

- **Submit Project Types (Code vs Text) (Optional)**
    - **Endpoint**: `POST /projects/upload/{upload_id}/project-types`
    - **Description**: Submit user selections for project type (`code` vs `text`) when a detected project contains both code and text artifacts and requires a choice. The request must use project names exactly as reported in `state.layout.auto_assignments` and `state.layout.pending_projects`.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Path Params**:
        - `{upload_id}` (integer, required): The ID of the upload session

- **List Main File Sections (Collaborative Text Contribution)**
    - **Endpoint**: `GET /projects/upload/{upload_id}/projects/{project_key}/text/sections`
    - **Description**: Returns numbered sections derived from the **selected main text file** for the project (from `uploads.state.file_roles`). Intended for selecting which parts of the document the user contributed to.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Path Params**:
        - `{upload_id}` (integer, required): The upload session ID
        - `{project_key}` (integer, required): The project key from `state.dedup_project_keys`
    - **Query Params**:
        - `max_section_chars` (integer, optional): Truncates each section’s `content` to this many characters.
    - **Response Status**: `200 OK`
    - **Response DTO**: `MainFileSectionsDTO`
    - **Response Body**:
        ```json
        {
            "success": true,
            "data": {
                "project_name": "MockProject",
                "main_file": "mock_projects/MockProject/main_report.txt",
                "sections": [
                    {
                        "id": 1,
                        "title": "Introduction",
                        "preview": "This report describes…",
                        "content": "This report describes…",
                        "is_truncated": false
                    }
                ]
            },
            "error": null
        }
        ```
    - **Error Responses**:
        - `409 Conflict` if the main file is not selected yet for this project
        - `404 Not Found` if the main file is missing on disk
        - `422 Unprocessable Entity` if the main file cannot be extracted or is empty

- **Set Main File Contributed Sections (Collaborative Text Contribution)**
    - **Endpoint**: `POST /projects/upload/{upload_id}/projects/{project_key}/text/contributions`
    - **Description**: Persists the section IDs the user contributed to into `uploads.state.contributions`. IDs are validated against the server-derived section list and stored de-duplicated + sorted.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Path Params**:
        - `{upload_id}` (integer, required): The upload session ID
        - `{project_key}` (integer, required): The project key from `state.dedup_project_keys`
    - **Request DTO**: `SetMainFileSectionsRequestDTO`
    - **Request Body**:
        ```json
        {
            "selected_section_ids": [1, 3, 5]
        }
        ```
    - **Response Status**: `200 OK`
    - **Response DTO**: `UploadDTO`
    - **Error Responses**:
        - `422 Unprocessable Entity` if any section IDs are out of range
        - `409 Conflict` if the main file is not selected yet for this project

- **Set Supporting Text Files (Collaborative Text Contribution)**
    - **Endpoint**: `POST /projects/upload/{upload_id}/projects/{project_key}/supporting-text-files`
    - **Description**: Stores which **supporting TEXT files** the user contributed to (excluding the selected main file, and excluding `.csv` files).
        - Writes to: `uploads.state.contributions` (keyed by project name)
        - Values are stored **deduplicated + sorted**
    - **Auth**: `Authorization: Bearer <access_token>`
    - **Path Params**:
        - `{upload_id}` (integer, required)
        - `{project_key}` (integer, required): From `state.dedup_project_keys`
    - **Request Body**:
        ```json
        {
        "relpaths": [
            "text_projects_og/PlantGrowthStudy/reading_notes.txt",
            "text_projects_og/PlantGrowthStudy/second_draft.docx"
        ]
        }
        ```
    - **Response Status**: `200 OK`
    - **Response DTO**: `UploadDTO`
    - **Error Responses**:

    - `409 Conflict` if upload is not in a file-picking step (e.g. not `needs_file_roles` / `needs_summaries`), or if main file is not selected yet (service guard)
    - `422 Unprocessable Entity` if any relpath is unsafe (e.g. contains `..`) or if the list includes the main file or any `.csv`
    - `404 Not Found` if any relpath does not exist for this project/upload


- **Set Supporting CSV Files (Collaborative Text Contribution)**
    - **Endpoint**: `POST /projects/upload/{upload_id}/projects/{project_key}/supporting-csv-files`
    - **Description**: Stores which **CSV files** the user contributed to.
        - Writes to: `uploads.state.contributions` (keyed by project name)
        - Values are stored **deduplicated + sorted**
    - **Auth**: `Authorization: Bearer <access_token>`
    - **Path Params**:
        - `{upload_id}` (integer, required)
        - `{project_key}` (integer, required): From `state.dedup_project_keys`
    - **Request Body**:
        ```json
        {
        "relpaths": [
            "text_projects_og/PlantGrowthStudy/plant_growth_data.csv",
            "text_projects_og/PlantGrowthStudy/plant_growth_data2.csv"
        ]
        }
        ```
    - **Response Status**: `200 OK`
    - **Response DTO**: `UploadDTO`
    - **Error Responses**:
        - `409 Conflict` if upload is not in a file-picking step (e.g. not `needs_file_roles` / `needs_summaries`)
        - `422 Unprocessable Entity` if any relpath is unsafe, or if any relpath is not a `.csv`
        - `404 Not Found` if any relpath does not exist for this project/upload
---

## **GitHub Integration**

**Base URL:** `/projects/upload/{upload_id}/projects/{project}/github` and `/auth`

Handles GitHub OAuth authentication and repository linking for projects during the upload wizard flow.

### **Endpoints**

- **Start GitHub Connection**
  - **Endpoint**: `POST /projects/upload/{upload_id}/projects/{project}/github/start`
  - **Description**: Initiates GitHub OAuth connection flow for a project. If `connect_now` is `true` and user is not already connected, returns an authorization URL. If `connect_now` is `false`, records that GitHub connection was skipped.
  - **Path Parameters**:
    - `{upload_id}` (integer, required): The upload session ID
    - `{project}` (string, required): The project name
  - **Headers**:
    - `Authorization` (string, required): Bearer token. Format: `Bearer <your-jwt-token>`
  - **Request Body**:
    {
    "connect_now": true
    }
  - **Response Status**: `200 OK` on success, `404 Not Found` if upload doesn't exist or belong to user
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "auth_url": "https://github.com/login/oauth/authorize?client_id=...&state=..."
      },
      "error": null
    }
    ```
    if user is already connected or connect_now is false, auth_url will be null

- **GitHub OAuth Callback**
  - **Endpoint**: `GET /auth/github/callback`
  - **Description**: Handles the OAuth callback from GitHub after user authorizes the application. Exchanges the authorization code for an access token and saves it. No authentication required - this is a public callback endpoint.
  - **Query Parameters**:
    - `code` (string, required): Authorization code from GitHub
    - `state` (string, optional): OAuth state parameter for security
  - **Response Status**: `200 OK` on success, `400 Bad Request` if code exchange fails or state is invalid
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "GitHub connected successfully",
      "data": {
        "success": true,
        "user_id": 1,
        "upload_id": 1,
        "project_name": "MyProject"
      }
    }
    ```

- **List GitHub Repositories**
  - **Endpoint**: `GET /projects/upload/{upload_id}/projects/{project}/github/repos`
  - **Description**: Returns a list of the user's GitHub repositories that can be linked to the project. Requires GitHub to be connected first.
  - **Path Parameters**:
    - `{upload_id}` (integer, required): The upload session ID
    - `{project}` (string, required): The project name
  - **Headers**:
    - `Authorization` (string, required): Bearer token. Format: `Bearer <your-jwt-token>`
  - **Response Status**: `200 OK` on success, `401 Unauthorized` if GitHub is not connected, `404 Not Found` if upload doesn't exist
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "repos": [
          {
            "full_name": "owner/repo1"
          },
          {
            "full_name": "owner/repo2"
          }
        ]
      },
      "error": null
    }
    ```

- **Link GitHub Repository**
  - **Endpoint**: `POST /projects/upload/{upload_id}/projects/{project}/github/link`
  - **Description**: Links a GitHub repository to the project. The repository must be accessible by the authenticated user.
  - **Path Parameters**:
    - `{upload_id}` (integer, required): The upload session ID
    - `{project}` (string, required): The project name
  - **Headers**:
    - `Authorization` (string, required): Bearer token. Format: `Bearer <your-jwt-token>`
  - **Request Body**:
    {
    "repo_full_name": "owner/repo-name"
    }
  - **Response Status**: `200 OK` on success, `400 Bad Request` if GitHub is not connected or repo format is invalid, `404 Not Found` if upload doesn't exist
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "success": true,
        "repo_full_name": "owner/repo-name"
      },
      "error": null
    }
    ```

---

## Google Drive Integration

**Base URL:** `/projects/upload/{upload_id}/projects/{project}/drive` and `/auth`

Handles Google Drive OAuth authentication and file linking for projects during the upload wizard flow. Mirrors the GitHub integration pattern.

### **Endpoints**
- **Start Google Drive Connection**
    - **Endpoint**: `POST /projects/upload/{upload_id}/projects/{project}/drive/start`
    - **Description**: Initiates Google Drive OAuth connection flow for a project. If `connect_now` is `true` and user is not already connected, returns a Google authorization URL. If `connect_now` is `false`, records that Google Drive connection was skipped.
    - **Path Parameters**:
        - `{upload_id}` (integer, required): The upload session ID
        - `{project}` (string, required): The project name
    - **Headers**: 
        - `Authorization` (string, required): Bearer token. Format: `Bearer <your-jwt-token>`
    - **Request Body**:
        ```json
        {
            "connect_now": true
        }
        ```
    - **Response Status**: `200 OK` on success, `404 Not Found` if upload doesn't exist or belong to user
    - **Response Body**:
        ```json
        {
            "success": true,
            "data": {
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&state=..."
            },
            "error": null
        }
        ```
        If user is already connected or `connect_now` is `false`, `auth_url` will be `null`.

- **Google Drive OAuth Callback**
    - **Endpoint**: `GET /auth/google/callback`
    - **Description**: Handles the OAuth callback from Google after user authorizes the application. Exchanges the authorization code for access and refresh tokens and saves them. No authentication required — this is a public callback endpoint.
    - **Query Parameters**:
        - `code` (string, required): Authorization code from Google
        - `state` (string, optional): OAuth state parameter for security
    - **Response Status**: `200 OK` on success, `400 Bad Request` if code exchange fails or state is invalid
    - **Response Body**:
        ```json
        {
            "success": true,
            "message": "Google Drive connected successfully",
            "data": {
                "success": true,
                "user_id": 1,
                "upload_id": 1,
                "project_name": "MyProject"
            }
        }
        ```

- **List Google Drive Files**
    - **Endpoint**: `GET /projects/upload/{upload_id}/projects/{project}/drive/files`
    - **Description**: Returns a list of the user's Google Drive files (filtered to supported types) that can be linked to the project. Requires Google Drive to be connected first.
    - **Path Parameters**:
        - `{upload_id}` (integer, required): The upload session ID
        - `{project}` (string, required): The project name
    - **Headers**: 
        - `Authorization` (string, required): Bearer token. Format: `Bearer <your-jwt-token>`
    - **Response Status**: `200 OK` on success, `401 Unauthorized` if Google Drive is not connected, `404 Not Found` if upload doesn't exist
    - **Response Body**:
        ```json
        {
            "success": true,
            "data": {
                "files": [
                    {
                        "id": "1aBcDeFgHiJkLmNoPqRsT",
                        "name": "Project Report.docx",
                        "mime_type": "application/vnd.google-apps.document"
                    },
                    {
                        "id": "2uVwXyZaBcDeFgHiJkLm",
                        "name": "Data.csv",
                        "mime_type": "text/plain"
                    }
                ]
            },
            "error": null
        }
        ```

- **Link Google Drive Files**
    - **Endpoint**: `POST /projects/upload/{upload_id}/projects/{project}/drive/link`
    - **Description**: Links one or more Google Drive files to the project's local files. Each link maps a local file name (from the uploaded ZIP) to a Google Drive file. Requires Google Drive to be connected.
    - **Path Parameters**:
        - `{upload_id}` (integer, required): The upload session ID
        - `{project}` (string, required): The project name
    - **Headers**: 
        - `Authorization` (string, required): Bearer token. Format: `Bearer <your-jwt-token>`
    - **Request Body**:
        ```json
        {
            "links": [
                {
                    "local_file_name": "report.docx",
                    "drive_file_id": "1aBcDeFgHiJkLmNoPqRsT",
                    "drive_file_name": "Project Report.docx",
                    "mime_type": "application/vnd.google-apps.document"
                },
                {
                    "local_file_name": "data.csv",
                    "drive_file_id": "2uVwXyZaBcDeFgHiJkLm",
                    "drive_file_name": "Data.csv",
                    "mime_type": "text/plain"
                }
            ]
        }
        ```
    - **Response Status**: `200 OK` on success, `400 Bad Request` if Google Drive is not connected, `404 Not Found` if upload doesn't exist
    - **Response Body**:
        ```json
        {
            "success": true,
            "data": {
                "success": true,
                "project_name": "MyProject",
                "files_linked": 2
            },
            "error": null
        }
        ```

---

- **List Project Files**
  - **Endpoint**: `GET /projects/upload/{upload_id}/projects/{project_key}/files`
  - **Description**: Returns all parsed files for a project within an upload, plus convenience buckets for `text_files` and `csv_files`. Clients should use the returned `relpath` values for subsequent file-role selection calls. Use `project_key` from `state.dedup_project_keys`.
  - **Headers**:
    - `X-User-Id` (integer, required)
  - **Path Params**:
    - `upload_id` (integer, required)
    - `project_key` (integer, required): From `state.dedup_project_keys`
  - **Valid Upload Status**:
    - `needs_file_roles`
    - `needs_summaries`
  - **Response Status**: `200 OK`
  - **Response DTO**: `UploadProjectFilesDTO`
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "project_name": "ProjectA",
        "all_files": [
          {
            "relpath": "text_projects/ProjectA/readme.txt",
            "file_name": "readme.txt",
            "file_type": "text",
            "extension": ".txt",
            "size_bytes": 123
          }
        ],
        "text_files": [
          {
            "relpath": "text_projects/ProjectA/readme.txt",
            "file_name": "readme.txt",
            "file_type": "text",
            "extension": ".txt",
            "size_bytes": 123
          }
        ],
        "csv_files": []
      },
      "error": null
    }
    ```
  - **Notes**:
    - Returns `409 Conflict` if the upload is not in `needs_file_roles` or `needs_summaries`.
    - Returns `404 Not Found` if the project is not part of this upload (not present in the upload’s layout).

- **Set Project Main File**
  - **Endpoint**: `POST /projects/upload/{upload_id}/projects/{project_key}/main-file`
  - **Description**: Stores the client-selected main file for a project (by `relpath`) in `uploads.state.file_roles`. The relpath must match one of the parsed files for that project. Use `project_key` from `state.dedup_project_keys`.
  - **Headers**:
    - `X-User-Id` (integer, required)
  - **Path Params**:
    - `upload_id` (integer, required)
    - `project_key` (integer, required): From `state.dedup_project_keys`
  - **Valid Upload Status**:
    - `needs_file_roles`
  - **Request DTO**: `MainFileRequestDTO`
  - **Request Body**:
    ```json
    {
      "relpath": "text_projects/ProjectA/readme.txt"
    }
    ```
  - **Response Status**: `200 OK`
  - **Response DTO**: `UploadDTO`
  - **Response Body (state excerpt)**:
    ```json
    {
      "success": true,
      "data": {
        "upload_id": 5,
        "status": "needs_file_roles",
        "zip_name": "text_projects.zip",
        "state": {
          "file_roles": {
            "ProjectA": {
              "main_file": "text_projects/ProjectA/readme.txt"
            }
          }
        }
      },
      "error": null
    }
    ```
  - **Notes**:
    - Returns `409 Conflict` if the upload is not in `needs_file_roles`.
    - Returns `422 Unprocessable Entity` if `relpath` is invalid (absolute path, contains `..`, etc.).
    - Returns `404 Not Found` if the relpath is not found for that project.

---

## **PrivacyConsent**

**Base URL:** `/privacy-consent`

Handles user consent for internal processing and external integrations.

### **Endpoints**

- **Record Internal Processing Consent**
  - **Endpoint**: `POST /privacy-consent/internal`
  - **Description**: Records the user's consent for internal data processing
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Request Body**:
    ```json
    {
      "status": "accepted"
    }
    ```
  - **Response Status**: `201 Created`
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "consent_id": 1,
        "user_id": 1,
        "status": "accepted",
        "timestamp": "2026-01-17T12:34:56.789012"
      },
      "error": null
    }
    ```

- **Record External Integration Consent**
  - **Endpoint**: `POST /privacy-consent/external`
  - **Description**: Records the user's consent for external service integrations
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Request Body**:
    ```json
    {
      "status": "rejected"
    }
    ```
  - **Response Status**: `201 Created`
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "consent_id": 2,
        "user_id": 1,
        "status": "rejected",
        "timestamp": "2026-01-17T12:35:00.123456"
      },
      "error": null
    }
    ```

- **Get Consent Status**
  - **Endpoint**: `GET /privacy-consent/status`
  - **Description**: Retrieves the current consent status for the authenticated user (returns the most recent consent for each type)
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK`
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "user_id": 1,
        "internal_consent": "accepted",
        "external_consent": "rejected"
      },
      "error": null
    }
    ```

---

## **Skills**

**Base URL:** `/skills`

Exposes extracted skills and timelines.

### **Endpoints**

- **Get Skills**
  - **Endpoint**: `GET /skills`
  - **Description**: Returns a chronological list of all skills extracted from the user's projects, including skill level, score, and associated project information.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK`
  - **Response Body**: Uses `SkillsListDTO` containing a list of `SkillEventDTO` objects
    ```json
    {
      "success": true,
      "data": {
        "skills": [
          {
            "skill_name": "Python",
            "level": "Advanced",
            "score": 0.9,
            "project_name": "MyProjet",
            "actual_activity_date": "2024-01-15",
            "recorded_at": "2024-01-20"
          }
        ]
      },
      "error": null
    }
    ```

---

## **Resume**

**Base URL:** `/resume`

Manages résumé-specific representations of projects.

### **Endpoints**

- **List Resumes**
  - **Endpoint**: `GET /resume`
  - **Description**: Returns a list of all résumé snapshots belonging to the current user.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK`
  - **Response Body**: Uses `ResumeListDTO` containing a list of `ResumeListItemDTO` objects
    ```json
    {
      "success": true,
      "data": {
        "resumes": [
          {
            "id": 1,
            "name": "Resume 2024-01-12",
            "created_at": "2024-01-12 10:30:00"
          }
        ]
      },
      "error": null
    }
    ```

- **Get Resume by ID**
  - **Endpoint**: `GET /resume/{resume_id}`
  - **Description**: Returns detailed information for a specific résumé snapshot, including all projects, aggregated skills, and rendered text.
  - **Path Parameters**:
    - `{resume_id}` (integer, required): The ID of the résumé snapshot
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK` or `404 Not Found`
  - **Response Body**: Uses `ResumeDetailDTO`

  ````json
      {
          "success": true,
          "data": {
              "id": 1,
              "name": "Resume 2024-01-12",
              "created_at": "2024-01-12 10:30:00",
              "projects": [
                  {
                      "project_name": "MyProject",
                      "project_type": "code",
                      "project_mode": "individual",
                      "languages": ["Python", "JavaScript"],
                      "frameworks": ["React", "FastAPI"],
                      "summary_text": "A web application...",
                      "skills": ["Backend Development", "Frontend Development"],
                      "text_type": null,
                      "contribution_percent": null,
                      "activities": []
                  }
              ],
              "aggregated_skills": {
                  "languages": ["Python", "JavaScript"],
                  "frameworks": ["React", "FastAPI"],
                  "technical_skills": ["Backend Development", "Frontend Development"],
                  "writing_skills": []
              },
              "rendered_text": "Resume text here..."
          },
          "error": null
      }
      ```

  ````

- **Generate Resume**
  - **Endpoint**: `POST /resume/generate`
  - **Description**: Creates a new résumé snapshot from the user's projects. If `project_ids` is not provided, automatically selects the top 5 ranked projects. Builds the snapshot, enriches with contribution bullets and dates, and renders the text.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Request Body**: Uses `ResumeGenerateRequestDTO`

    ```json
    {
      "name": "My Resume",
      "project_ids": [1, 3, 5]
    }
    ```

    - `name` (string, required): Name for the résumé snapshot
    - `project_ids` (array of integers, optional): List of `project_summary_id` values from the `project_summaries` table. Get these IDs from `GET /projects`. If omitted (no project_ids, just name), uses top 5 ranked projects.

  - **Response Status**: `201 Created` or `400 Bad Request`
  - **Response Body**: Uses `ResumeDetailDTO`
    ```json
    {
        "success": true,
        "data": {
            "id": 2,
            "name": "My Resume",
            "created_at": "2024-01-15 14:30:00",
            "projects": [...],
            "aggregated_skills": {...},
            "rendered_text": "..."
        },
        "error": null
    }
    ```
  - **Error Responses**:
    - `400 Bad Request`: No valid projects found for the given IDs
    - `401 Unauthorized`: Missing Authentication header
    - `404 Not Found`: User not found

- **Edit Resume**
  - **Endpoint**: `POST /resume/{resume_id}/edit`
  - **Description**: Edits a résumé snapshot. Can rename the résumé, edit project details, update resume-level skill highlighting preferences, or any combination. Project editing is optional - you can rename a résumé or update resume-level skill preferences without editing any project.
  - **Path Parameters**:
    - `{resume_id}` (integer, required): The `id` from `resume_snapshots` table. Get this from `GET /resume` list.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Request Body**: Uses `ResumeEditRequestDTO`

    ```json
    {
      "name": "Updated Resume Name",
      "project_summary_id": 123,
      "scope": "resume_only",
      "display_name": "Custom Project Name",
      "summary_text": "Updated project summary...",
      "contribution_bullets": [
        "Built feature X",
        "Improved performance by 50%"
      ],
      "contribution_edit_mode": "replace"
    }
    ```

    - `name` (string, optional): New name for the résumé (rename)
    - `project_name` (string, optional): The text name of the project to edit. If omitted, only résumé-level updates are applied (e.g., rename and/or skill preferences).
    - `project_summary_id` (integer, optional): Required when editing project fields. Get this from `GET /resume/{resume_id}` response (`projects[].project_summary_id`). If omitted, only the résumé name is updated.
    - `scope` (string, optional): Required when editing a project. Either `"resume_only"` or `"global"`. Defaults to `"resume_only"` if not specified.
      - `resume_only`: Changes apply only to this résumé (stored as `resume_*_override` fields)
      - `global`: Changes apply to all résumés and update `project_summaries.manual_overrides`
    - `display_name` (string, optional): Custom display name for the project
    - `summary_text` (string, optional): Updated summary text
    - `contribution_bullets` (array of strings, optional): Custom contribution bullet points
    - `contribution_edit_mode` (string, optional): How to apply contribution bullets. Defaults to `"replace"`.
      - `"replace"`: Replace all existing bullets with the provided list
      - `"append"`: Keep existing bullets and add the provided bullets to the end
    - `skill_preferences` (array, optional): Resume-level skill highlighting preferences. Each entry uses `SkillPreferenceDTO`.
    - `skill_preferences_reset` (boolean, optional): If true, clears all resume-level skill preferences (reverts to defaults).

  - **Response Status**: `200 OK` or `404 Not Found`
  - **Response Body**: Uses `ResumeDetailDTO`
    ```json
    {
        "success": true,
        "data": {
            "id": 1,
            "name": "Updated Resume Name",
            "project_name": "MyProject",
            "scope": "resume_only",
            "display_name": "Custom Project Name",
            "summary_text": "Updated project summary...",
            "contribution_bullets": [
                "Built feature X",
                "Improved performance by 50%"
            ],
            "contribution_edit_mode": "replace",
            "key_role": "Backend Developer"
        }
        ```
        - `name` (string, optional): New name for the résumé (rename)
        - `project_name` (string, optional): The text name of the project to edit. If omitted, only résumé-level updates are applied (e.g., rename and/or skill preferences).
        - `project_summary_id` (integer, optional): Required when editing project fields. Get from `GET /resume/{resume_id}` response. If omitted, only name is updated.
        - `scope` (string, optional): Required when editing a project. Either `"resume_only"` or `"global"`. Defaults to `"resume_only"` if not specified.
            - `resume_only`: Changes apply only to this résumé (stored as `resume_*_override` fields)
            - `global`: Changes apply to all résumés and update `project_summaries.manual_overrides`
        - `display_name` (string, optional): Custom display name for the project
        - `summary_text` (string, optional): Updated summary text
        - `contribution_bullets` (array of strings, optional): Custom contribution bullet points
        - `contribution_edit_mode` (string, optional): How to apply contribution bullets. Defaults to `"replace"`.
            - `"replace"`: Replace all existing bullets with the provided list
            - `"append"`: Keep existing bullets and add the provided bullets to the end
        - `key_role` (string, optional): The user's key role for the project (e.g. "Backend Developer", "Team Lead"). Follows the same `scope` rules as other fields.
        - `skill_preferences` (array, optional): Resume-level skill highlighting preferences. Each entry uses `SkillPreferenceDTO`.
        - `skill_preferences_reset` (boolean, optional): If true, clears all resume-level skill preferences (reverts to defaults).
    - **Response Status**: `200 OK` or `404 Not Found`
    - **Response Body**: Uses `ResumeDetailDTO`
        ```json
        {
            "success": true,
            "data": {
                "id": 1,
                "name": "Updated Resume Name",
                "created_at": "2024-01-12 10:30:00",
                "projects": [...],
                "aggregated_skills": {...},
                "rendered_text": "..."
            },
            "error": null
        }
        ```
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token
        - `404 Not Found`: Resume or project not found
    - **Example: Rename résumé only (no project editing)**:
        ```json
        {
            "name": "My Updated Resume"
        }
        ```
    - **Example: Append new bullets to existing**:
        ```json
        {
            "project_summary_id": 123,
            "scope": "resume_only",
            "contribution_bullets": ["Added new feature Y"],
            "contribution_edit_mode": "append"
        }
        ```

- **Delete Resume by ID**
  - **Endpoint**: `DELETE /resume/{resume_id}`
  - **Description**: Permanently deletes a specific résumé snapshot.
  - **Path Parameters**:
    - `{resume_id}` (integer, required): The ID of the résumé snapshot to delete
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK` on success, `404 Not Found` if résumé doesn't exist or belong to user
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": null,
      "error": null
    }
    ```

- **Delete All Resumes**
  - **Endpoint**: `DELETE /resume`
  - **Description**: Permanently deletes all résumé snapshots belonging to the current user.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK`
  - **Response DTO**: `DeleteResultDTO`
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "deleted_count": 2
      },
      "error": null
    }
    ```

- **Remove Project from Resume**
  - **Endpoint**: `DELETE /resume/{resume_id}/projects?project_name=<name>`
  - **Description**: Removes a single project from a résumé snapshot. Recomputes aggregated skills from the remaining projects. If no projects remain after removal, the résumé is deleted entirely.
  - **Path Parameters**:
    - `{resume_id}` (integer, required): The ID of the résumé snapshot
  - **Query Parameters**:
    - `project_name` (string, required): The name of the project to remove
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK` on success, `404 Not Found` if résumé doesn't exist or project isn't in the résumé
  - **Response Body** (project removed, résumé still has other projects):
    ```json
    {
      "success": true,
      "data": {
        "id": 1,
        "name": "My Resume",
        "projects": [...],
        "aggregated_skills": {...},
        "rendered_text": "..."
      },
      "error": null
    }
    ```
  - **Response Body** (last project removed, résumé deleted):
    ```json
    {
      "success": true,
      "data": null,
      "error": null
    }
    ```
  - **Error Responses**:
    - `401 Unauthorized`: Missing or invalid Bearer token
    - `404 Not Found`: `"Resume not found"` or `"Project not found in resume"` (distinct messages)
    - `422 Unprocessable Entity`: Missing `project_name` query parameter

- **Export Resume to DOCX**
    - **Endpoint**: `GET /resume/{resume_id}/export/docx`
    - **Description**: Exports a résumé snapshot to a Word document (.docx) file.
    - **Path Parameters**:
        - `{resume_id}` (integer, required): The ID of the résumé snapshot to export. Get this from `GET /resume`.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response**: Binary file download with MIME type `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
    - **Response Headers**:
        - `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`
        - `Content-Disposition: attachment; filename="resume_username_2025-01-15_14-30-00.docx"`
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token
        - `404 Not Found`: Resume not found or doesn't belong to user

- **Export Resume to PDF**
    - **Endpoint**: `GET /resume/{resume_id}/export/pdf`
    - **Description**: Exports a résumé snapshot to a PDF document.
    - **Path Parameters**:
        - `{resume_id}` (integer, required): The ID of the résumé snapshot to export. Get this from `GET /resume`.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response**: Binary file download with MIME type `application/pdf`
    - **Response Headers**:
        - `Content-Type: application/pdf`
        - `Content-Disposition: attachment; filename="resume_username_2025-01-15_14-30-00.pdf"`
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token
        - `404 Not Found`: Resume not found or doesn't belong to user

---

## **Portfolio**

**Base URL:** `/portfolio`

Manages portfolio showcase configuration. Portfolios are generated live from all of the user's analyzed projects, ranked by importance score. No data is persisted — the portfolio reflects the current state of project summaries and overrides.

### **Endpoints**

- **Generate Portfolio**
    - **Endpoint**: `POST /portfolio/generate`
    - **Description**: Generates a portfolio view from all of the user's analyzed projects, ranked by importance. Returns structured project data and a rendered plain-text version. The portfolio is not persisted — it is built on demand from existing project summaries.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: Uses `PortfolioGenerateRequestDTO`
        ```json
        {
            "name": "My Portfolio"
        }
        ```
        - `name` (string, required): Label for the portfolio (used in rendered text header)
    - **Response Status**: `200 OK` or `400 Bad Request`
    - **Response Body**: Uses `PortfolioDetailDTO`
        ```json
        {
            "success": true,
            "data": {
                "projects": [
                    {
                        "project_name": "MyProject",
                        "display_name": "My Project",
                        "project_type": "code",
                        "project_mode": "collaborative",
                        "score": 0.875,
                        "duration": "Duration: 2024-01-15 – 2024-06-30",
                        "languages": ["Python", "JavaScript"],
                        "frameworks": ["FastAPI", "React"],
                        "activity": "Activity: feature_coding 85%, testing 15%",
                        "skills": ["Backend Development", "API Design"],
                        "summary_text": "A web application for...",
                        "contribution_bullets": ["Built the REST API layer"]
                    }
                ],
                "rendered_text": "Portfolio — My Portfolio\n..."
            },
            "error": null
        }
        ```
    - **Error Responses**:
        - `400 Bad Request`: No projects found for this user
        - `401 Unauthorized`: Missing or invalid Bearer token

- **Edit Portfolio**
    - **Endpoint**: `POST /portfolio/edit`
    - **Description**: Edits portfolio wording or skill highlighting for a specific project. Changes can be scoped to the portfolio only or applied globally (affecting all resumes and the portfolio). Edits are stored as overrides in `project_summaries.summary_json` and skill preferences are stored per project — no portfolio snapshot table is needed. Returns the updated portfolio view.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: Uses `PortfolioEditRequestDTO`
        ```json
        {
            "project_summary_id": 123,
            "scope": "portfolio_only",
            "display_name": "Custom Project Name",
            "summary_text": "Updated summary...",
            "contribution_bullets": ["Built feature X", "Improved performance by 50%"]
        }
        ```
        - `project_summary_id` (integer, required): The `project_summary_id` from the portfolio generate response (`projects[].project_summary_id`)
        - `scope` (string, optional): Either `"portfolio_only"` (default) or `"global"`
            - `portfolio_only`: Changes apply only to the portfolio view (stored as `portfolio_overrides`)
            - `global`: Changes apply to all resumes and the portfolio (stored as `manual_overrides` in `project_summaries`, fanned out to all `resume_snapshots`)
        - `display_name` (string, optional): Custom display name for the project
        - `summary_text` (string, optional): Updated summary text
        - `contribution_bullets` (array of strings, optional): Custom contribution bullet points
        - `skill_preferences` (array, optional): Per-project skill highlighting preferences. Each entry uses `SkillPreferenceDTO`.
        - `skill_preferences_reset` (boolean, optional): If true, clears skill preferences for the specified project.
    - **Response Status**: `200 OK` or `404 Not Found`
    - **Response Body**: Uses `PortfolioDetailDTO` (returns the full updated portfolio)
        ```json
        {
            "success": true,
            "data": {
                "projects": [...],
                "rendered_text": "..."
            },
            "error": null
        }
        ```
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token
        - `404 Not Found`: Project not found

- **Export Portfolio to DOCX**
    - **Endpoint**: `GET /portfolio/export/docx`
    - **Description**: Exports the user's portfolio to a Word document (.docx) file. Includes all ranked projects with their metadata, summaries, and contribution bullets.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response**: Binary file download with MIME type `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
    - **Response Headers**:
        - `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`
        - `Content-Disposition: attachment; filename="portfolio_username_2025-01-15_14-30-00.docx"`
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token
        - `404 Not Found`: No projects found for this user

- **Export Portfolio to PDF**
    - **Endpoint**: `GET /portfolio/export/pdf`
    - **Description**: Exports the user's portfolio to a PDF document. Includes all ranked projects with their metadata, summaries, and contribution bullets.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response**: Binary file download with MIME type `application/pdf`
    - **Response Headers**:
        - `Content-Type: application/pdf`
        - `Content-Disposition: attachment; filename="portfolio_username_2025-01-15_14-30-00.pdf"`
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token
        - `404 Not Found`: No projects found for this user

---

### Path Variables

- `{project_id}` (integer): Maps to `project_summary_id` from the `project_summaries` table
- `{project_key}` (integer): Maps to `project_key` from the `projects` table (used in upload flow)
- `{resume_id}` (integer): Maps to `id` from the `resume_snapshots` table
- `{upload_id}` (integer): Maps to `upload_id` from the `uploads` table
- `{portfolio_id}` (integer): Reserved for future use

### Important: Identifier Sources

The API uses different identifiers depending on the resource. Here's where each identifier comes from:

| API Parameter                | Database Table      | Database Column      | Description                        |
| ---------------------------- | ------------------- | -------------------- | ---------------------------------- |
| `project_id` / `project_ids` | `project_summaries` | `project_summary_id` | Unique ID for a project summary    |
| `project_summary_id`         | `project_summaries` | `project_summary_id` | Same as above; preferred for edits |
| `project_key`                | `projects`          | `project_key`        | Internal project key; used in upload paths |
| `version_key`                | `project_versions`  | `version_key`        | Identifies a specific analysis run/version |
| `project_name`               | `projects`          | `display_name`       | Display name; for UI only, not for lookups |
| `resume_id`                  | `resume_snapshots`  | `id`                 | Unique ID for a saved résumé       |
| `upload_id`                  | `uploads`           | `upload_id`          | Unique ID for an upload session    |
| `user_id`                    | `users`             | `user_id`            | Unique ID for a user               |

**Note:** Projects and versions are identified by stable keys:

- `project_summary_id` (integer) - Preferred for resume/portfolio edits
- `project_key` (integer) - Used in upload flow paths (from `state.dedup_project_keys`)
- `version_key` (integer) - Per-version metrics; from `state.dedup_version_keys`
- `project_name` (text) - Display purposes only; avoid for API lookups

### Versioning

Projects can have multiple versions (re-uploads). Each version gets a `version_key`. Upload state exposes:

- `state.dedup_project_keys` – maps `project_name` → `project_key`
- `state.dedup_version_keys` – maps `project_name` → `version_key`

Use `project_key` in upload paths; the server resolves it to the project for that upload.

### How to Get Project IDs

To get `project_summary_id` values for use in endpoints like `POST /resume/generate`:

1. Call `GET /projects` to list all projects
2. Each project in the response includes `project_summary_id`
3. Use these IDs in the `project_ids` array

---

## **DTO References**

DTOs (Data Transfer Objects) are defined using Pydantic models in `src/api/schemas/`.

Every endpoint must:

- Accept a DTO for its request body (when applicable)
- Return a DTO in its response body
- Reference the DTO it uses in this document

Example:

- **ProjectListItemDTO**
  - `project_summary_id` (int, required) – preferred for edits
  - `project_key` (int, optional) – internal key
  - `project_name` (string, required) – display only
  - `project_type` (string, optional)
  - `project_mode` (string, optional)
  - `created_at` (string, optional)

### **Projects DTOs**

- **ProjectListDTO** (used by `GET /projects`)
  - `projects` (List[ProjectListItemDTO], required)

- **ProjectDetailDTO** (used by `GET /projects/{project_id}`)
  - `project_summary_id` (int, required) – preferred for edits
  - `project_key` (int, optional) – internal key
  - `project_name` (string, required) – display only
  - `project_type` (string, optional)
  - `project_mode` (string, optional)
  - `created_at` (string, optional)
  - `summary_text` (string, optional)
  - `languages` (array of strings, optional)
  - `frameworks` (array of strings, optional)
  - `skills` (array of strings, optional)
  - `metrics` (object, optional)
  - `contributions` (object, optional)

### **Project Ranking DTOs**

- **ProjectRankingItemDTO** (used by `GET /projects/ranking`)
  - `rank` (int, required): The 1-based position in the returned ranking list
  - `project_summary_id` (int, required)
  - `project_name` (string, required)
  - `score` (float, required)
  - `manual_rank` (int, optional): The stored manual rank override (if set)

- **ProjectRankingDTO**
  - `rankings` (List[ProjectRankingItemDTO], required)

- **ReplaceProjectRankingRequestDTO** (used by `PUT /projects/ranking`)
  - `project_ids` (List[int], required): Must include every `project_summary_id` for the user exactly once

- **PatchProjectRankingRequestDTO** (used by `PATCH /projects/{project_id}/ranking`)
  - `rank` (int, optional): Set a manual rank. Use `null` to clear manual rank.

### **Upload Wizard DTOs (Projects Upload)**

- **UploadDTO**
  - `upload_id` (int, required)
  - `status` (string, required)  
    Allowed values:
    - `"started"`
    - `"parsed"`
    - `"needs_classification"`
    - `"needs_file_roles"`
    - `"needs_summaries"`
    - `"analyzing"`
    - `"done"`
    - `"failed"`
  - `zip_name` (string, optional)
  - `state` (object, optional)

- **ClassificationsRequest**
  - `assignments` (object, required)  
    Shape: `{ "<project_name>": "<classification>" }`  
    Allowed values:
    - `"individual"`
    - `"collaborative"`

- **ProjectTypesRequest**
  - `project_types` (object, required)  
    Shape: `{ "<project_name>": "<project_type>" }`  
    Allowed values:
    - `"text"`
    - `"code"`

- **DedupResolveRequestDTO**
  - `decisions` (object, required)  
    Allowed values: `"skip"`, `"new_project"`, `"new_version"`

- **MainFileSectionDTO**
    - `id` (int, required): 1-based section identifier
    - `title` (string, required): Display title derived from header or preview
    - `preview` (string, optional): Short snippet for scanning
    - `content` (string, optional): Section text (may be truncated)
    - `is_truncated` (boolean, required): True if `content` was truncated

- **MainFileSectionsDTO**
    - `project_name` (string, required)
    - `main_file` (string, required): The selected main file relpath for the project
    - `sections` (List[MainFileSectionDTO], required)

- **SetMainFileSectionsRequestDTO**
    - `selected_section_ids` (List[int], required): IDs from `MainFileSectionsDTO.sections[*].id`

- **SupportingFilesRequest**
    - `relpaths` (List[string], required): relpaths returned by `GET .../files`


### **Skills DTOs**

- **SkillEventDTO**
  - `skill_name` (string, required)
  - `level` (string, required)
  - `score` (float, required)
  - `project_name` (string, required)
  - `actual_activity_date` (string, optional)
  - `recorded_at` (string, optional)

- **SkillsListDTO**
  - `skills` (List[SkillEventDTO], required)

- **SkillPreferenceDTO**
  - `skill_name` (string, required)
  - `is_highlighted` (boolean, optional): Defaults to true
  - `display_order` (int, optional): Lower values show first

### **Resume DTOs**

- **ResumeListItemDTO**
  - `id` (int, required)
  - `name` (string, required)
  - `created_at` (string, optional)

- **ResumeListDTO**
  - `resumes` (List[ResumeListItemDTO], required)

- **ResumeProjectDTO**
  - `project_name` (string, required)
  - `project_type` (string, optional)
  - `project_mode` (string, optional)
  - `languages` (List[string], optional)
  - `frameworks` (List[string], optional)
  - `summary_text` (string, optional)
  - `skills` (List[string], optional)
  - `text_type` (string, optional)
  - `contribution_percent` (float, optional)
  - `activities` (List[Dict], optional)

- **AggregatedSkillsDTO**
  - `languages` (List[string], optional)
  - `frameworks` (List[string], optional)
  - `technical_skills` (List[string], optional)
  - `writing_skills` (List[string], optional)

- **ResumeDetailDTO**
  - `id` (int, required)
  - `name` (string, required)
  - `created_at` (string, optional)
  - `projects` (List[ResumeProjectDTO], optional)
  - `aggregated_skills` (AggregatedSkillsDTO, optional)
  - `rendered_text` (string, optional)

- **ResumeGenerateRequestDTO**
  - `name` (string, required): Name for the new résumé snapshot
  - `project_ids` (List[int], optional): List of `project_summary_id` values from `project_summaries` table. Get these from `GET /projects`. If omitted, uses top 5 ranked projects.

- **ResumeEditRequestDTO**
    - `name` (string, optional): New name for the résumé
    - `project_name` (string, optional): Text name of the project to edit. If omitted, only résumé-level updates are applied.
    - `project_summary_id` (integer, optional): Required when editing project fields. Get from `GET /resume/{resume_id}` response. If omitted, only name is updated.
    - `scope` (string, optional): `"resume_only"` (default) or `"global"`. Required when editing a project.
    - `display_name` (string, optional): Custom display name for the project
    - `summary_text` (string, optional): Updated summary text
    - `contribution_bullets` (List[string], optional): Custom contribution bullet points
    - `contribution_edit_mode` (string, optional): `"replace"` (default) or `"append"`
    - `key_role` (string, optional): The user's key role for the project (e.g. "Backend Developer", "Team Lead")
    - `skill_preferences` (List[SkillPreferenceDTO], optional): Resume-level skill highlighting preferences
    - `skill_preferences_reset` (boolean, optional): Clear all resume-level preferences (revert to defaults)

- **PortfolioGenerateRequestDTO**
    - `name` (string, required): Label for the portfolio

- **PortfolioEditRequestDTO**
    - `project_summary_id` (integer, required): Use from portfolio generate response
    - `scope` (string, optional): `"portfolio_only"` (default) or `"global"`
    - `display_name` (string, optional): Custom display name for the project
    - `summary_text` (string, optional): Updated summary text
    - `contribution_bullets` (List[string], optional): Custom contribution bullet points
    - `skill_preferences` (List[SkillPreferenceDTO], optional): Per-project skill highlighting preferences
    - `skill_preferences_reset` (boolean, optional): Clear preferences for the specified project

- **PortfolioProjectDTO**
    - `project_name` (string, required)
    - `display_name` (string, required)
    - `project_type` (string, optional)
    - `project_mode` (string, optional)
    - `score` (float, required): Importance ranking score
    - `duration` (string, optional): Formatted duration string (e.g. "Duration: 2024-01-15 – 2024-06-30")
    - `languages` (List[string], optional): Top 3 languages (code projects only)
    - `frameworks` (List[string], optional): Frameworks used (code projects only)
    - `activity` (string, optional): Formatted activity line (e.g. "Activity: feature_coding 85%, testing 15%")
    - `skills` (List[string], optional): Top 4 skills
    - `summary_text` (string, optional): Project summary text
    - `contribution_bullets` (List[string], optional): Contribution bullet points

- **PortfolioDetailDTO**
    - `projects` (List[PortfolioProjectDTO], optional)
    - `rendered_text` (string, optional): Plain-text formatted portfolio

- **PortfolioGenerateRequestDTO**
    - `name` (string, required): Label for the portfolio

- **PortfolioEditRequestDTO**
    - `project_summary_id` (integer, required): Use from portfolio generate response
    - `scope` (string, optional): `"portfolio_only"` (default) or `"global"`
    - `display_name` (string, optional): Custom display name for the project
    - `summary_text` (string, optional): Updated summary text
    - `contribution_bullets` (List[string], optional): Custom contribution bullet points

- **PortfolioProjectDTO**
    - `project_name` (string, required)
    - `display_name` (string, required)
    - `project_type` (string, optional)
    - `project_mode` (string, optional)
    - `score` (float, required): Importance ranking score
    - `duration` (string, optional): Formatted duration string (e.g. "Duration: 2024-01-15 – 2024-06-30")
    - `languages` (List[string], optional): Top 3 languages (code projects only)
    - `frameworks` (List[string], optional): Frameworks used (code projects only)
    - `activity` (string, optional): Formatted activity line (e.g. "Activity: feature_coding 85%, testing 15%")
    - `skills` (List[string], optional): Top 4 skills
    - `summary_text` (string, optional): Project summary text
    - `contribution_bullets` (List[string], optional): Contribution bullet points

- **PortfolioDetailDTO**
    - `projects` (List[PortfolioProjectDTO], optional)
    - `rendered_text` (string, optional): Plain-text formatted portfolio

- **ConsentRequestDTO**
  - `status` (string, required): Must be either "accepted" or "rejected"

- **ConsentResponseDTO**
  - `consent_id` (int, required): Unique identifier for the consent record
  - `user_id` (int, required): User who gave the consent
  - `status` (string, required): "accepted" or "rejected"
  - `timestamp` (string, required): ISO 8601 timestamp of when consent was recorded

- **ConsentStatusDTO**
  - `user_id` (int, required): User identifier
  - `internal_consent` (string, optional): Latest internal consent status, or null if not set
  - `external_consent` (string, optional): Latest external consent status, or null if not set

### **GitHub Integration DTOs**

- **GitHubStartRequest**
  - `connect_now` (boolean, required)

- **GitHubStartResponse**
  - `auth_url` (string, optional)

- **GitHubRepoDTO**
  - `full_name` (string, required)

- **GitHubReposResponse**
  - `repos` (List[GitHubRepoDTO], required)

- **GitHubLinkRequest**
  - `repo_full_name` (string, required)

### **Google Drive Integration DTOs**

- **DriveStartRequest**
    - `connect_now` (boolean, required)

- **DriveStartResponse**
    - `auth_url` (string, optional)

- **DriveFileDTO**
    - `id` (string, required): Google Drive file ID
    - `name` (string, required): File name in Google Drive
    - `mime_type` (string, required): MIME type of the file

- **DriveFilesResponse**
    - `files` (List[DriveFileDTO], required)

- **DriveLinkItem**
    - `local_file_name` (string, required): File name from the uploaded ZIP
    - `drive_file_id` (string, required): Google Drive file ID to link to
    - `drive_file_name` (string, required): File name in Google Drive
    - `mime_type` (string, required): MIME type of the Drive file

- **DriveLinkRequest**
    - `links` (List[DriveLinkItem], required)

- **ThumbnailUploadDTO** (used by `POST /projects/{project_id}/thumbnail`)
    - `project_id` (int, required): The project_summary_id
    - `project_name` (string, required): Display name of the project
    - `message` (string, required): Status message (e.g. "Thumbnail uploaded successfully")

- **DeleteResultDTO** (used by `DELETE /projects` and `DELETE /resume`)
  - `deleted_count` (int, required): Number of items deleted

---

## **Best Practices**

- Use correct HTTP methods:
  - `GET` – Retrieve data
  - `POST` – Create resources
  - `PUT` – Replace or fully update resources
  - `PATCH` – Partially update resources
  - `DELETE` – Delete resources

---

## **Error Codes**

| Code | Description                                  |
| ---- | -------------------------------------------- |
| 200  | OK – Request succeeded                       |
| 201  | Created – Resource successfully created      |
| 204  | No Content – Resource deleted                |
| 400  | Bad Request – Invalid input                  |
| 401  | Unauthorized – Missing/invalid/expired token |
| 404  | Not Found – Resource not found               |
| 409  | Conflict – Duplicate or invalid state        |
| 422  | Unprocessable Entity – Validation error      |
| 500  | Internal Server Error – Unexpected error     |

---

## **Example Error Response**

```json
{
  "success": false,
  "data": null,
  "error": {
    "message": "Resource not found",
    "code": 404
  }
}
```
