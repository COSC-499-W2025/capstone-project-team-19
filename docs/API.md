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
7. [Privacy Consent](#privacyconsent)
8. [Skills](#skills)
9. [Resume](#resume)
10. [Portfolio](#portfolio)
11. [Portfolio Settings](#portfolio-settings)
12. [Public Portfolio](#public-portfolio)
13. [Activity Heatmap](#activity-heatmap)
14. [User Profile](#user-profile)
15. [Path Variables](#path-variables)
16. [DTO References](#dto-references)
17. [Best Practices](#best-practices)
18. [Error Codes](#error-codes)
19. [Example Error Response](#example-error-response)

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
  - **Endpoint**: `GET /`
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
  - **Endpoint**: `GET /{project_id}`
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
    - **Endpoint**: `GET /ranking`
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

  - **Get Top Projects**
    - **Endpoint**: `GET /top`
    - **Description**: Returns the top N projects in ranked order, with summary snippets and version counts. Useful for dashboards and "top projects" displays.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Query Parameters**:
      - `limit` (integer, optional): Number of top projects to return. Defaults to `3`. Must be ≥ 1.
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response DTO**: `TopProjectsDTO`
    - **Response Body**:
      ```json
      {
        "success": true,
        "data": {
          "topProjects": [
            {
              "projectId": "9",
              "title": "My Project",
              "rankScore": 0.732,
              "summarySnippet": "A full-stack task manager with React and Spring Boot...",
              "versionCount": 3
            }
          ]
        },
        "error": null
      }
      ```

  - **Get Project Evolution**
    - **Endpoint**: `GET /{project_id}/evolution`
    - **Description**: Returns version-by-version evolution for a project: summaries, file-level diffs, skill progression, languages, frameworks, and metrics. Projects with multiple uploads (versions) will show how the project evolved over time.
    - **Path Parameters**:
      - `{project_id}` (integer, required): The `project_summary_id` of the project
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Response Status**: `200 OK` on success, `404 Not Found` if project doesn't exist or belong to user
    - **Response DTO**: `ProjectEvolutionDTO`
    - **Response Body**:
      ```json
      {
        "success": true,
        "data": {
          "projectId": "3",
          "title": "code_collab_proj",
          "versions": [
            {
              "versionId": "1",
              "date": "2026-02-18",
              "summary": "Task Manager",
              "diff": null,
              "skills": ["architecture_and_design"],
              "skillsDetail": [{"skill_name": "architecture_and_design", "level": "Intermediate", "score": 0.33}],
              "skillProgression": null,
              "languages": ["Java", "JSON", "YAML"],
              "frameworks": ["Spring", "Spring Boot"],
              "avgComplexity": null,
              "totalFiles": 86
            },
            {
              "versionId": "2",
              "date": "2026-02-18",
              "summary": "task manager",
              "diff": {
                "linesAdded": null,
                "linesModified": null,
                "linesRemoved": null,
                "files": {
                  "filesAdded": ["new-file.java"],
                  "filesModified": ["modified-file.py"],
                  "filesRemoved": ["removed-file.c"],
                  "unchangedCount": 28
                }
              },
              "skills": ["testing_and_ci"],
              "skillsDetail": [{"skill_name": "testing_and_ci", "level": "Beginner", "score": 0.25}],
              "skillProgression": {
                "newSkills": [{"skill_name": "testing_and_ci", "level": "Beginner", "score": 0.25, "prev_score": null}],
                "improvedSkills": [],
                "declinedSkills": [],
                "removedSkills": [{"skill_name": "architecture_and_design", "level": "Intermediate", "score": 0.33, "prev_score": 0.33}]
              },
              "languages": ["Java", "JavaScript", "TypeScript"],
              "frameworks": ["React", "Spring Boot"],
              "avgComplexity": null,
              "totalFiles": 206
            }
          ]
        },
        "error": null
      }
      ```
    - **Notes**:
      - First version has `diff: null` and `skillProgression: null` (nothing to compare)
      - `diff` for later versions includes file-level changes (added/modified/removed) and optionally `linesAdded`, `linesRemoved` when available
      - `skillProgression` shows new, improved, declined, and removed skills between consecutive versions
      - `avgComplexity` is `null` for collaborative code projects; only individual code projects have complexity metrics

  - **Replace Entire Ranking Order**
    - **Endpoint**: `PUT /ranking`
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
    - **Endpoint**: `PATCH /{project_id}/ranking`
    - **Description**: Sets or clears the manual rank for one project.
    - **Path Parameters**:
      - `{project_id}` (integer, required): The `project_summary_id` of the project to update
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request DTO**: `PatchProjectRankingRequestDTO`
    - **Request Body**:
      - Set manual rank:
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
    - **Endpoint**: `POST /ranking/reset`
    - **Description**: Clears all manual ranking overrides for the user (reverts to pure computed ranking).
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response DTO**: `ProjectRankingDTO`

- **Project Dates**
    - **Description**: View and manage **manual date overrides** for projects.
        - If a project has manual dates, the API will report `source: "MANUAL"` and return those dates.
        - If a project has no manual dates, the API will report `source: "AUTO"` and return the best available automatic date (if any).
        - Manual dates affect any features that depend on project chronology (e.g., chronological skills, portfolio ordering).

    - **List Project Dates**
        - **Endpoint**: `GET /dates`
        - **Description**: Returns all projects with their effective dates and whether they come from manual overrides or automatic computation.
        - **Auth**: `Authorization: Bearer <access_token>`
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
        - **Endpoint**: `PATCH /{project_id}/dates`
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
        - **Endpoint**: `DELETE /{project_id}/dates`
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
        - **Endpoint**: `POST /dates/reset`
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
    - **Endpoint**: `DELETE /{project_id}`
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
        DELETE /9

        # Delete project and update resumes
        DELETE /9?refresh_resumes=true
        ```
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
    - **Endpoint**: `DELETE /`
    - **Description**: Permanently deletes all projects belonging to the current user.
    - **Query Parameters**:
        - `refresh_resumes` (boolean, optional): If `true`, also removes deleted projects from any résumé snapshots. Résumés that become empty are deleted. Defaults to `false`.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Example Requests**:
        ```bash
        # Delete all projects (default, resumes unchanged)
        DELETE /

        # Delete all projects and update resumes
        DELETE /?refresh_resumes=true
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
        - **Endpoint**: `POST /{project_id}/thumbnail`
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
        - **Endpoint**: `GET /{project_id}/thumbnail`
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
        - **Endpoint**: `DELETE /{project_id}/thumbnail`
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

1. **Start upload**: `POST /`
   - parses ZIP and computes layout
   - runs dedup:
     - exact duplicates are automatically skipped
     - “ask” cases are stored for UI resolution
     - “new_version” suggestions may be recorded
2. **Poll/resume**: `GET /{upload_id}`
3. **Resolve dedup (optional)**: `POST /{upload_id}/dedup/resolve`
4. **Submit classifications**: `POST /{upload_id}/classifications`
5. **Resolve mixed project types (optional)**: `POST /{upload_id}/project-types`
6. **Select collaborative text contribution sections (optional, text-collab only)**:
   - `GET /{upload_id}/projects/{project_key}/text/sections`
   - `POST /{upload_id}/projects/{project_key}/text/contributions`
7. **Provide summary metadata before run (when needed)**:
   - `POST /{upload_id}/projects/{project_key}/key-role`
8. **Run analysis (readiness + execution)**:
   - `POST /{upload_id}/run`
   - Use `mode=check` for readiness-only, or `mode=run` to execute after readiness passes.
   - For full readiness matrix details (blockers/warnings by scope and project type), refer to `docs/run_analysis_readiness_matrix.txt`.

Use `project_key` from `state.dedup_project_keys` (keyed by project name) for each project.

---

### **Endpoints**

- **Start Upload**
  - **Endpoint**: `POST /`
  - **Description**: Upload a ZIP file, save it to disk, parse the ZIP, and compute the project layout to determine the next wizard step. The server creates an `upload_id` and stores wizard state in the database.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Request Body**: `multipart/form-data`
    - `file` (file, required): ZIP file
  - **Response Status**: `200 OK`

- **Get Upload Status (Resume / Poll)**
    - **Endpoint**: `GET /{upload_id}`
    - **Description**: Returns the current upload wizard state for the given `upload_id`. Use this to resume a wizard flow or refresh the UI.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Path Params**:
        - `{upload_id}` (integer, required): The ID of the upload session
    - **Response Status**: `200 OK` on success, `404 Not Found` if upload doesn't exist or belong to user
    - **Response Body**:
        ```json
        {
            "success": true,
            "data": {
                "upload_id": 5,
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
            },
            "error": null
        }
        ```

- **Resolve Dedup (Optional, New)**
  - **Endpoint**: `POST /{upload_id}/dedup/resolve`
  - **Description**: Resolves dedup “ask” cases that were captured during upload parsing. This step happens before classifications and project types.
  - **Headers**:
    - `Authorization`: Bearer <token>
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
  - **Endpoint**: `POST /{upload_id}/classifications`
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
  - **Endpoint**: `POST /{upload_id}/project-types`
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

- **Run Analysis**
  - **Endpoint**: `POST /{upload_id}/run`
  - **Description**: Supports readiness check and execution for the requested scope (`all`, `individual`, or `collaborative`).
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Path Params**:
    - `{upload_id}` (integer, required)
  - **Request Body**:
    ```json
    {
      "scope": "all",
      "force_rerun": false,
      "mode": "run"
    }
    ```
  - **Response Status**:
    - `200 OK` for `mode="check"` (returns `ready`, `warnings`, `errors`; no execution)
    - `200 OK` for `mode="run"` if readiness passes
    - `409 Conflict` if upload state is incomplete or scope is already completed without force rerun
    - `422 Unprocessable Entity` for invalid scope/mode
    - `404 Not Found` if upload does not exist or does not belong to the user
    - `500 Internal Server Error` if runtime execution fails after readiness passes
  - **Readiness Matrix Reference**:
    - Full matrix documentation is maintained in `docs/run_analysis_readiness_matrix.txt`.

- **List Main File Sections (Collaborative Text Contribution)**
    - **Endpoint**: `GET /{upload_id}/projects/{project_key}/text/sections`
    - **Description**: Returns numbered sections derived from the **selected main text file** for the project (from `uploads.state.file_roles`). Intended for selecting which parts of the document the user contributed to.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Path Params**:
        - `{upload_id}` (integer, required): The upload session ID
        - `{project_key}` (integer, required): The project key from `state.dedup_project_keys`
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
    - **Endpoint**: `POST /{upload_id}/projects/{project_key}/text/contributions`
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
    - **Endpoint**: `POST /{upload_id}/projects/{project_key}/supporting-text-files`
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
    - **Endpoint**: `POST /{upload_id}/projects/{project_key}/supporting-csv-files`
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

- **Set Project Key Role**
  - **Endpoint**: `POST /{upload_id}/projects/{project_key}/key-role`
  - **Description**: Stores the user-provided role/title for the project in the upload wizard state.
    - Writes to: `uploads.state.contributions[project_name].key_role`
    - Value is whitespace-normalized before storing
    - Blank input is allowed and clears the stored role (stored as empty string)
  - **Auth**: `Authorization: Bearer <access_token>`
  - **Path Params**:
    - `{upload_id}` (integer, required)
    - `{project_key}` (integer, required): From `state.dedup_project_keys`
  - **Valid Upload Status**:
    - `needs_file_roles`
    - `needs_summaries`
    - `analyzing`
    - `done`
  - **Request Body**:
    ```json
    {
      "key_role": "Backend Developer"
    }
    ```
    - Clear role:
    ```json
    {
      "key_role": "   "
    }
    ```
  - **Response Status**: `200 OK`
  - **Response DTO**: `UploadDTO`
  - **Error Responses**:
    - `404 Not Found` if upload does not exist/belong to user, or project is not part of this upload
    - `409 Conflict` if upload status is not valid for this action
    - `422 Unprocessable Entity` if `key_role` is invalid (e.g., wrong type or exceeds max length)

- **Manual Project Summary**
  - **Endpoint**: `POST /{upload_id}/projects/{project_name}/manual-project-summary`
  - **Description**: Stores a user-provided manual project summary for this upload session.
    - Writes to: `uploads.state.manual_project_summaries[project_name]`
  - **Auth**: `Authorization: Bearer <access_token>`
  - **Path Params**:
    - `{upload_id}` (integer, required): The upload session ID
    - `{project_name}` (string, required): The project name
  - **Request DTO**: `ManualProjectSummaryRequestDTO`
  - **Request Body**:
    ```json
    {
      "summary_text": "Built a pipeline to ..., improved ..., shipped ..."
    }
    ```
  - **Response Status**: `200 OK`
  - **Response DTO**: `UploadDTO`
  - **Error Responses**:
    - `404 Not Found` if upload or project is not found / does not belong to user
    - `409 Conflict` if upload is not in a summary-allowed status (must be `needs_summaries`, or if enabled: `analyzing`/`done`)

- **Manual Contribution Summary**
  - **Endpoint**: `POST /{upload_id}/projects/{project_name}/manual-contribution-summary`
  - **Description**: Stores a user-provided manual contribution summary for this upload session.
    - Writes to: `uploads.state.contributions[project_name].manual_contribution_summary`
  - **Auth**: `Authorization: Bearer <access_token>`
  - **Path Params**:
    - `{upload_id}` (integer, required): The upload session ID
    - `{project_name}` (string, required): The project name
  - **Request DTO**: `ManualContributionSummaryRequestDTO`
  - **Request Body**:
    ```json
    {
      "manual_contribution_summary": "I implemented ..., fixed ..., added tests ..., or keep it empty if you'd like"
    }
    ```
  - **Response Status**: `200 OK`
  - **Response DTO**: `UploadDTO`
  - **Error Responses**:
    - `404 Not Found` if upload or project is not found / does not belong to user
    - `409 Conflict` if upload is not in a summary-allowed status (must be `needs_summaries`, or if enabled: `analyzing`/`done`)


## **GitHub Integration**

**Base URL:** `/projects/upload/{upload_id}/projects/{project}/github` and `/auth`

Handles GitHub OAuth authentication and repository linking for projects during the upload wizard flow.

### **Endpoints**

- **Start GitHub Connection**
  - **Endpoint**: `POST /start`
  - **Description**: Initiates GitHub OAuth connection flow for a project. If `connect_now` is `true` and user is not already connected, returns an authorization URL. If a stored token exists, it is validated first; if validation fails (expired or revoked), the token is cleared and an auth URL is returned so the user can re-authorize. If `connect_now` is `false`, records that GitHub connection was skipped.
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
        "auth_url": "https://github.com/login/oauth/authorize?client_id=...&state=..."
      },
      "error": null
    }
    ```
    if user is already connected or connect_now is false, auth_url will be null

- **GitHub OAuth Callback**
  - **Endpoint**: `GET /github/callback`
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
  - **Endpoint**: `GET /repos`
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
  - **Endpoint**: `POST /link`
  - **Description**: Links a GitHub repository to the project. The repository must be accessible by the authenticated user.
  - **Path Parameters**:
    - `{upload_id}` (integer, required): The upload session ID
    - `{project}` (string, required): The project name
  - **Headers**:
    - `Authorization` (string, required): Bearer token. Format: `Bearer <your-jwt-token>`
  - **Request Body**:
    ```json
    {
    "repo_full_name": "owner/repo-name"
    }
    ```
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
    - **Endpoint**: `POST /start`
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
    - **Endpoint**: `GET /google/callback`
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
    - **Endpoint**: `GET /files`
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
    - **Endpoint**: `POST /link`
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
  - **Endpoint**: `GET /{upload_id}/projects/{project_key}/files`
  - **Description**: Returns all parsed files for a project within an upload, plus convenience buckets for `text_files` and `csv_files`. Clients should use the returned `relpath` values for subsequent file-role selection calls. Use `project_key` from `state.dedup_project_keys`.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
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
  - **Endpoint**: `POST /{upload_id}/projects/{project_key}/main-file`
  - **Description**: Stores the client-selected main file for a project (by `relpath`) in `uploads.state.file_roles`. The relpath must match one of the parsed files for that project. Use `project_key` from `state.dedup_project_keys`.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
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
  - **Endpoint**: `POST /internal`
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
  - **Endpoint**: `POST /external`
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
  - **Endpoint**: `GET /status`
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
  - **Endpoint**: `GET /`
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
            "project_name": "MyProject",
            "actual_activity_date": "2024-01-15",
            "recorded_at": "2024-01-20"
          }
        ]
      },
      "error": null
    }
    ```

- **Get Skill Timeline**
  - **Endpoint**: `GET /timeline`
  - **Description**: Returns a chronological skill evolution timeline with cumulative scores computed using diminishing returns. Skills are grouped by date, and undated skills are listed separately. A `current_totals` section folds undated skills into the final cumulative score.
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK`
  - **Response Body**: Uses `SkillTimelineDTO`
    ```json
    {
      "success": true,
      "data": {
        "dated": [
          {
            "date": "2024-01-15",
            "events": [
              {
                "skill_name": "Python",
                "level": "Intermediate",
                "score": 0.3,
                "project_name": "ProjectA"
              }
            ],
            "cumulative_skills": {
              "Python": {
                "cumulative_score": 0.3,
                "projects": ["ProjectA"]
              }
            }
          },
          {
            "date": "2024-03-20",
            "events": [
              {
                "skill_name": "Python",
                "level": "Advanced",
                "score": 0.4,
                "project_name": "ProjectB"
              }
            ],
            "cumulative_skills": {
              "Python": {
                "cumulative_score": 0.58,
                "projects": ["ProjectA", "ProjectB"]
              }
            }
          }
        ],
        "undated": [
          {
            "skill_name": "Docker",
            "level": "Beginner",
            "score": 0.25,
            "project_name": "ProjectC"
          }
        ],
        "current_totals": {
          "Python": {
            "cumulative_score": 0.58,
            "projects": ["ProjectA", "ProjectB"]
          },
          "Docker": {
            "cumulative_score": 0.25,
            "projects": ["ProjectC"]
          }
        },
        "summary": {
          "total_skills": 2,
          "total_projects": 3,
          "date_range": {
            "earliest": "2024-01-15",
            "latest": "2024-03-20"
          },
          "skill_names": ["Docker", "Python"]
        }
      },
      "error": null
    }
    ```
  - **Cumulative Score Formula**: Uses diminishing returns — `1 - (1 - current) × (1 - new_score)`. Each new project fills a fraction of the remaining gap to 1.0, so scores always increase but never exceed 1.0. This rewards breadth (practicing a skill across many projects) without rapid saturation.

---

## **Resume**

**Base URL:** `/resume`

Manages résumé-specific representations of projects.

### **Endpoints**

- **List Resumes**
  - **Endpoint**: `GET /`
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
  - **Endpoint**: `GET /{resume_id}`
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

- **Get Resume Skills**
  - **Endpoint**: `GET /{resume_id}/skills`
  - **Description**: Returns all skills present in a specific résumé snapshot, along with their current preference status (highlighted or hidden). Only skills that actually appear in this résumé are returned — not every skill the user has ever recorded. Skill preferences fall back to global preferences if no resume-level preferences are set.
  - **Path Parameters**:
    - `{resume_id}` (integer, required): The ID of the résumé snapshot
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK` or `404 Not Found`
  - **Response Body**: Uses `ResumeSkillListDTO` containing a list of `ResumeSkillStatusDTO` objects
    ```json
    {
      "success": true,
      "data": {
        "skills": [
          {
            "skill_name": "clarity",
            "display_name": "Clear communication",
            "is_highlighted": true,
            "display_order": null
          },
          {
            "skill_name": "architecture_and_design",
            "display_name": "Architecture & design",
            "is_highlighted": false,
            "display_order": null
          }
        ]
      },
      "error": null
    }
    ```
  - **Fields**:
    - `skill_name` (string): Raw skill key used when saving preferences (e.g. `"clarity"`, `"architecture_and_design"`)
    - `display_name` (string): Human-readable label shown in the UI and exported PDF/DOCX
    - `is_highlighted` (boolean): Whether the skill is currently shown on this résumé
    - `display_order` (integer or null): Explicit ordering position; `null` means default order
  - **Error Responses**:
    - `401 Unauthorized`: Missing or invalid Bearer token
    - `404 Not Found`: Resume not found

- **Generate Resume**
  - **Endpoint**: `POST /generate`
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
  - **Endpoint**: `POST /{resume_id}/edit`
  - **Description**: Edits a résumé snapshot. Can rename the résumé, edit project details, update resume-level skill highlighting preferences, or any combination. Project editing is optional - you can rename a résumé without editing any project.
  - **Path Parameters**:
    - `{resume_id}` (integer, required): The `id` from `resume_snapshots` table. Get this from `GET /` list.
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
      "contribution_edit_mode": "replace",
      "key_role": "Backend Developer"
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
    - `key_role` (string, optional): The user's key role for the project (e.g. "Backend Developer", "Team Lead"). Follows the same `scope` rules as other fields.
    - `skill_preferences` (array, optional): Resume-level skill highlighting preferences. Each entry uses `SkillPreferenceDTO`:
      - `skill_name` (string, required): Raw skill key — use values from `GET /{resume_id}/skills`
      - `is_highlighted` (boolean, optional, default `true`): Whether to show this skill on the résumé
      - `display_order` (integer, optional): Explicit sort position (lower = higher priority)
    - `skill_preferences_reset` (boolean, optional): If `true`, clears all resume-level skill preferences and reverts to global defaults. Cannot be combined with `skill_preferences`.

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
    - **Example: Update skill preferences for this résumé**:
        ```json
        {
            "skill_preferences": [
                { "skill_name": "clarity", "is_highlighted": true },
                { "skill_name": "architecture_and_design", "is_highlighted": false },
                { "skill_name": "testing_and_ci", "is_highlighted": true, "display_order": 1 }
            ]
        }
        ```
    - **Example: Reset skill preferences to defaults**:
        ```json
        {
            "skill_preferences_reset": true
        }
        ```

---

## **User Profile**

**Base URL:** `/profile`

Manages standalone user profile information used for resume and portfolio exports. This includes full name, email, phone, LinkedIn URL, GitHub URL, location, and a short profile paragraph.

All endpoints require authentication (`Authorization: Bearer <access_token>`).

### **Endpoints**

- **Get Current User Profile**
  - **Endpoint**: `GET /`
  - **Description**: Returns the authenticated user's current profile information. If the user has not saved a profile yet, all fields (except `user_id`) will be `null`.
  - **Auth**: Bearer token required
  - **Request Body**: None
  - **Response Status**: `200 OK`
  - **Response Body**: Uses `UserProfileDTO`
    ```json
    {
      "success": true,
      "data": {
        "user_id": 1,
        "email": "user@example.com",
        "full_name": "Alice Example",
        "phone": "123-456-7890",
        "linkedin": "https://linkedin.com/in/alice",
        "github": "https://github.com/alice",
        "location": "Kelowna, BC",
        "profile_text": "Software and data student building practical tools."
      },
      "error": null
    }
    ```
  - **Error Responses**:
    - `401 Unauthorized`: Missing or invalid Bearer token

- **Update Current User Profile**
  - **Endpoint**: `PUT /`
  - **Description**: Creates or updates the authenticated user's profile information. All fields are optional; only provided fields are changed. Blank strings are normalized to `null`, which clears those fields.
  - **Auth**: Bearer token required
  - **Request Body**: Uses `UserProfileUpdateDTO`
    ```json
    {
      "email": "user@example.com",
      "full_name": "Alice Example",
      "phone": "123-456-7890",
      "linkedin": "https://linkedin.com/in/alice",
      "github": "https://github.com/alice",
      "location": "Kelowna, BC",
      "profile_text": "Software and data student building practical tools."
    }
    ```
    - `email` (string, optional): Contact email address. Also updates `users.email`.
    - `full_name` (string, optional): Full name used for resume/portfolio exports.
    - `phone` (string, optional): Phone number to show in contact details.
    - `linkedin` (string, optional): LinkedIn profile URL.
    - `github` (string, optional): GitHub profile URL.
    - `location` (string, optional): Location line (e.g., `"Kelowna, BC"`).
    - `profile_text` (string, optional): Short profile paragraph. If empty/blank, the profile section is hidden in exports.
  - **Response Status**: `200 OK`
  - **Response Body**: Uses `UserProfileDTO` with the updated profile
    ```json
    {
      "success": true,
      "data": {
        "user_id": 1,
        "email": "user@example.com",
        "full_name": "Alice Example",
        "phone": "123-456-7890",
        "linkedin": "https://linkedin.com/in/alice",
        "github": "https://github.com/alice",
        "location": "Kelowna, BC",
        "profile_text": "Software and data student building practical tools."
      },
      "error": null
    }
    ```
  - **Error Responses**:
    - `401 Unauthorized`: Missing or invalid Bearer token
    
- **List Education Entries**
  - **Endpoint**: `GET /education`
  - **Description**: Returns all education entries for the authenticated user (e.g., degrees, diplomas). Results are ordered by `display_order` and `entry_id`.
  - **Auth**: Bearer token required
  - **Request Body**: None
  - **Response Status**: `200 OK`
  - **Response Body**: Uses `UserEducationListDTO`
    ```json
    {
      "success": true,
      "data": {
        "entries": [
          {
            "entry_id": 1,
            "entry_type": "education",
            "title": "BSc in Computer Science",
            "organization": "UBCO",
            "date_text": "2022 - 2026",
            "description": "Major in data science.",
            "display_order": 1,
            "created_at": "2025-01-15T10:00:00",
            "updated_at": "2025-01-15T10:00:00"
          }
        ]
      },
      "error": null
    }
    ```
  - **Error Responses**:
    - `401 Unauthorized`: Missing or invalid Bearer token

- **Replace Education Entries**
  - **Endpoint**: `PUT /education`
  - **Description**: Replaces all of the user's education entries with the provided list. This is a full replace operation: existing `"education"` entries are deleted and re-inserted in the order provided.
  - **Auth**: Bearer token required
  - **Request Body**: Uses `UserEducationEntriesUpdateDTO`
    ```json
    {
      "entries": [
        {
          "title": "BSc in Computer Science",
          "organization": "UBCO",
          "date_text": "2022 - 2026",
          "description": "Major in data science."
        },
        {
          "title": "MSc in Computer Science",
          "organization": "UBCO",
          "date_text": "2026 - 2028",
          "description": "Graduate program."
        }
      ]
    }
    ```
    - `title` (string, required): Degree or program name
    - `organization` (string, optional): Institution name
    - `date_text` (string, optional): Free-form date range (e.g., `"2022 - 2026"`)
    - `description` (string, optional): Short description or notes
  - **Response Status**: `200 OK` on success, `400 Bad Request` on validation error
  - **Response Body**: Uses `UserEducationListDTO` with the updated entries
  - **Error Responses**:
    - `400 Bad Request`: Validation error (for example, missing `title`)
    - `401 Unauthorized`: Missing or invalid Bearer token

- **List Certification Entries**
  - **Endpoint**: `GET /certifications`
  - **Description**: Returns all certificate-style entries for the authenticated user (e.g., professional certifications). Results are ordered by `display_order` and `entry_id`.
  - **Auth**: Bearer token required
  - **Request Body**: None
  - **Response Status**: `200 OK`
  - **Response Body**: Uses `UserEducationListDTO`
    ```json
    {
      "success": true,
      "data": {
        "entries": [
          {
            "entry_id": 2,
            "entry_type": "certificate",
            "title": "AWS Cloud Practitioner",
            "organization": "Amazon Web Services",
            "date_text": "2025",
            "description": "Foundational cloud certification.",
            "display_order": 1,
            "created_at": "2025-01-15T10:05:00",
            "updated_at": "2025-01-15T10:05:00"
          }
        ]
      },
      "error": null
    }
    ```
  - **Error Responses**:
    - `401 Unauthorized`: Missing or invalid Bearer token

- **Replace Certification Entries**
  - **Endpoint**: `PUT /certifications`
  - **Description**: Replaces all of the user's certification entries with the provided list. Existing `"certificate"` entries are deleted and re-inserted in the order provided.
  - **Auth**: Bearer token required
  - **Request Body**: Uses `UserEducationEntriesUpdateDTO`
    ```json
    {
      "entries": [
        {
          "title": "AWS Cloud Practitioner",
          "organization": "Amazon Web Services",
          "date_text": "2025",
          "description": "Foundational cloud certification."
        }
      ]
    }
    ```
    - `title` (string, required): Certificate name
    - `organization` (string, optional): Issuing organization
    - `date_text` (string, optional): Free-form date text (e.g., `"2025"`)
    - `description` (string, optional): Short description or notes
  - **Response Status**: `200 OK` on success, `400 Bad Request` on validation error
  - **Response Body**: Uses `UserEducationListDTO` with the updated entries
  - **Error Responses**:
    - `400 Bad Request`: Validation error (for example, missing `title` or invalid entry type)
    - `401 Unauthorized`: Missing or invalid Bearer token

- **List Experience Entries**
  - **Endpoint**: `GET /experience`
  - **Description**: Returns all work experience entries for the authenticated user (e.g., jobs, internships). Results are ordered by `display_order` and `entry_id`.
  - **Auth**: Bearer token required
  - **Request Body**: None
  - **Response Status**: `200 OK`
  - **Response Body**: Uses `UserExperienceListDTO`
    ```json
    {
      "success": true,
      "data": {
        "entries": [
          {
            "entry_id": 1,
            "role": "Full Stack Engineer",
            "company": "Company ABC",
            "date_text": "Sep 2025 - Dec 2025",
            "description": "Worked on backend and frontend features.",
            "display_order": 1,
            "created_at": "2025-01-15T10:00:00",
            "updated_at": "2025-01-15T10:00:00"
          }
        ]
      },
      "error": null
    }
    ```
  - **Error Responses**:
    - `401 Unauthorized`: Missing or invalid Bearer token

- **Replace Experience Entries**
  - **Endpoint**: `PUT /experience`
  - **Description**: Replaces all of the user's work experience entries with the provided list. Existing experience entries are deleted and re-inserted in the order provided.
  - **Auth**: Bearer token required
  - **Request Body**: Uses `UserExperienceEntriesUpdateDTO`
    ```json
    {
      "entries": [
        {
          "role": "Full Stack Engineer",
          "company": "Company ABC",
          "date_text": "Sep 2025 - Dec 2025",
          "description": "Worked on backend and frontend features."
        },
        {
          "role": "Data Science Intern",
          "company": "PETRONAS",
          "date_text": "May 2025 - Aug 2025",
          "description": "Built analytics workflows and dashboards."
        }
      ]
    }
    ```
    - `role` (string, required): Job title or role name
    - `company` (string, optional): Company or organization name
    - `date_text` (string, optional): Free-form date text (e.g., `"Sep 2025 - Dec 2025"`)
    - `description` (string, optional): Short description of responsibilities or impact
  - **Response Status**: `200 OK` on success, `400 Bad Request` on validation error
  - **Response Body**: Uses `UserExperienceListDTO` with the updated entries
  - **Error Responses**:
    - `400 Bad Request`: Validation error (for example, missing `role`)
    - `401 Unauthorized`: Missing or invalid Bearer token
  - **Error Responses**:
    - `401 Unauthorized`: Missing or invalid Bearer token
    - `404 Not Found`: `"Resume not found"` or `"Project not found in resume"` (distinct messages)
    - `422 Unprocessable Entity`: Missing `project_name` query parameter

- **Add Project to Resume**
  - **Endpoint**: `POST /{resume_id}/projects`
  - **Description**: Adds a project to an existing résumé snapshot. The project must exist (from `project_summaries`) and must not already be in the résumé.
  - **Path Parameters**:
    - `{resume_id}` (integer, required): The ID of the résumé snapshot
  - **Request Body**: `AddProjectRequestDTO`
    - `project_summary_id` (integer, required): The `project_summary_id` from `project_summaries` (get from `GET /projects/ranking`)
  - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
  - **Response Status**: `200 OK` on success
  - **Response Body**: `ResumeDetailDTO` with the updated résumé including the new project
  - **Error Responses**:
    - `400 Bad Request`: Project not found or already in resume
    - `401 Unauthorized`: Missing or invalid Bearer token
    - `404 Not Found`: Resume not found

- **Export Resume to DOCX**
    - **Endpoint**: `GET /{resume_id}/export/docx`
    - **Description**: Exports a résumé snapshot to a Word document (.docx) file.
    - **Path Parameters**:
        - `{resume_id}` (integer, required): The ID of the résumé snapshot to export. Get this from `GET /`.
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
    - **Endpoint**: `GET /{resume_id}/export/pdf`
    - **Description**: Exports a résumé snapshot to a PDF document.
    - **Path Parameters**:
        - `{resume_id}` (integer, required): The ID of the résumé snapshot to export. Get this from `GET /`.
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

- **Get Portfolio Overview**
    - **Endpoint**: `GET /`
    - **Description**: Returns the user's portfolio as a ranked list of projects, suitable for display in a UI. This is a read-only view; it does not create or persist any portfolio snapshot.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response Body**: Uses `PortfolioDTO`
        ```json
        {
          "success": true,
          "data": {
            "items": [
              {
                "rank": 1,
                "project_name": "MyProject",
                "display_name": "My Project",
                "score": 0.875,
                "project_type": "code",
                "project_mode": "individual",
                "start_date": "2024-01-15",
                "end_date": "2024-06-30",
                "languages": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "React"],
                "summary_text": "A web application for...",
                "skills": ["Backend Development", "API Design"],
                "text_type": null,
                "contribution_percent": null,
                "activities": [
                  { "name": "feature_coding", "percent": 85.0 },
                  { "name": "testing", "percent": 15.0 }
                ]
              }
            ]
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token
        - `404 Not Found`: User not found

- **Generate Portfolio**
    - **Endpoint**: `POST /generate`
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
    - **Endpoint**: `POST /edit`
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
    - **Endpoint**: `GET /export/docx`
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
    - **Endpoint**: `GET /export/pdf`
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

## **Portfolio Settings**

**Base URL:** `/portfolio-settings`

Manages authenticated user portfolio visibility settings. Controls whether the portfolio is public, which resume is shown, and per-project public/private toggles.

All endpoints require authentication (`Authorization: Bearer <access_token>`).

### **Endpoints**

- **Get Portfolio Settings**
    - **Endpoint**: `GET /`
    - **Description**: Returns the authenticated user's current portfolio settings.
    - **Auth**: Bearer token required
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "portfolio_public": false,
            "active_resume_id": null
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token

- **Update Portfolio Settings**
    - **Endpoint**: `PUT /`
    - **Description**: Updates portfolio visibility and/or active resume. All fields are optional — only provided fields are changed.
    - **Auth**: Bearer token required
    - **Request Body**:
        ```json
        {
          "portfolio_public": true,
          "active_resume_id": 5,
          "clear_active_resume": false
        }
        ```
        - `portfolio_public` (boolean, optional): Set to `true` to make the portfolio publicly accessible, `false` to make it private.
        - `active_resume_id` (integer, optional): ID of the resume to pin as the active public resume.
        - `clear_active_resume` (boolean, optional): Set to `true` to remove the active resume selection.
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "portfolio_public": true,
            "active_resume_id": 5
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token

- **Toggle Project Visibility**
    - **Endpoint**: `PATCH /projects/{project_summary_id}/visibility`
    - **Description**: Sets the `is_public` flag on a specific project. Public projects appear on the user's public portfolio page; private projects are hidden from all public views.
    - **Auth**: Bearer token required
    - **Path Variables**:
        - `project_summary_id` (integer): ID of the project summary to update
    - **Request Body**:
        ```json
        {
          "is_public": true
        }
        ```
        - `is_public` (boolean, required): `true` to make the project public, `false` to make it private.
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "project_summary_id": 42,
            "is_public": true
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `401 Unauthorized`: Missing or invalid Bearer token
        - `404 Not Found`: Project not found or belongs to another user

---

## **Public Portfolio**

**Base URL:** `/public/{username}`

Read-only, unauthenticated endpoints for viewing a user's public portfolio. All endpoints return `404` if the portfolio is private or the username does not exist — intentionally the same response to avoid confirming whether a username exists.

**No authentication required.**

### **Endpoints**

- **List Public Projects**
    - **Endpoint**: `GET /projects`
    - **Description**: Returns all projects the user has marked as public (`is_public = true`). Strips internal fields such as metrics, contributions, and `project_key`.
    - **Auth**: None
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "projects": [
              {
                "project_summary_id": 42,
                "project_name": "My App",
                "project_type": "code",
                "project_mode": "individual",
                "created_at": "2024-03-01T10:00:00"
              }
            ]
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `404 Not Found`: Portfolio is private or username does not exist

- **Get Public Project Detail**
    - **Endpoint**: `GET /projects/{project_id}`
    - **Description**: Returns detail for a single public project. Returns `404` if the project is private or belongs to another user.
    - **Auth**: None
    - **Path Variables**:
        - `project_id` (integer): `project_summary_id` of the project
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "project_summary_id": 42,
            "project_name": "My App",
            "project_type": "code",
            "project_mode": "individual",
            "created_at": "2024-03-01T10:00:00",
            "summary_text": "A web app built with FastAPI.",
            "languages": ["Python"],
            "frameworks": ["FastAPI"],
            "skills": ["Backend Development"]
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `404 Not Found`: Portfolio is private, project is private, or not found

- **Get Public Project Thumbnail**
    - **Endpoint**: `GET /projects/{project_id}/thumbnail`
    - **Description**: Returns the thumbnail image for a public project as a PNG file. Returns `404` if the project is private or has no thumbnail.
    - **Auth**: None
    - **Response Status**: `200 OK`
    - **Response**: Binary PNG image (`image/png`)
    - **Error Responses**:
        - `404 Not Found`: Portfolio/project is private, thumbnail does not exist, or username not found

- **Get Public Project Ranking**
    - **Endpoint**: `GET /ranking`
    - **Description**: Returns a ranked list of the user's public projects. Score and internal ranking fields are stripped.
    - **Auth**: None
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "rankings": [
              {
                "rank": 1,
                "project_summary_id": 42,
                "project_name": "My App"
              }
            ]
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `404 Not Found`: Portfolio is private or username does not exist

- **List Public Resumes**
    - **Endpoint**: `GET /resumes`
    - **Description**: Returns all resume snapshots belonging to the user whose portfolio is public.
    - **Auth**: None
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "resumes": [
              {
                "id": 5,
                "name": "Software Engineer Resume",
                "created_at": "2024-03-01T10:00:00"
              }
            ]
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `404 Not Found`: Portfolio is private or username does not exist

- **Get Public Resume Detail**
    - **Endpoint**: `GET /resumes/{resume_id}`
    - **Description**: Returns the full detail of a specific resume. Sensitive internal fields (`contribution_percent`, `activities`) are stripped from project entries.
    - **Auth**: None
    - **Path Variables**:
        - `resume_id` (integer): ID of the resume snapshot
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "id": 5,
            "name": "Software Engineer Resume",
            "created_at": "2024-03-01T10:00:00",
            "projects": [
              {
                "project_name": "My App",
                "project_type": "code",
                "project_mode": "individual",
                "languages": ["Python"],
                "frameworks": ["FastAPI"],
                "summary_text": "A web app.",
                "skills": ["Backend Development"],
                "key_role": "Lead Developer",
                "contribution_bullets": ["Built the REST API"],
                "start_date": "2024-01-01",
                "end_date": "2024-06-30"
              }
            ],
            "aggregated_skills": {
              "languages": ["Python"],
              "frameworks": ["FastAPI"],
              "technical_skills": ["Backend Development"],
              "writing_skills": []
            },
            "rendered_text": "Resume — Software Engineer Resume\n..."
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `404 Not Found`: Portfolio is private, resume not found, or username does not exist

- **Get Public Skills**
    - **Endpoint**: `GET /skills`
    - **Description**: Returns skills extracted from the user's public projects only. Internal fields (score, dates) are stripped.
    - **Auth**: None
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "skills": [
              {
                "skill_name": "Backend Development",
                "level": "advanced",
                "project_name": "My App"
              }
            ]
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `404 Not Found`: Portfolio is private or username does not exist

- **Get Public Skills Timeline**
    - **Endpoint**: `GET /skills/timeline`
    - **Description**: Returns the skill timeline data for the user's portfolio. Same structure as the authenticated skills timeline.
    - **Auth**: None
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
          "success": true,
          "data": {
            "dated": [...],
            "undated": [...],
            "current_totals": {...},
            "summary": {...}
          },
          "error": null
        }
        ```
    - **Error Responses**:
        - `404 Not Found`: Portfolio is private or username does not exist

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

## **Activity Heatmap**
Displays a heatmap of **activity type vs version** for a project.

- **Notes**
  - `mode=diff` (default): each version column shows **only files changed in that version** (added + modified vs previous version).
  - `mode=snapshot`: each version column shows **all files present in that version**.
  - If `normalize=true`, values are **percent per version column**:
    - `% = (files in that activity) / (total files counted for that version) * 100`
    - Each version column sums to ~100% (unless that version has 0 eligible files).


### **Endpoints**
- **Get Activity Heatmap Info**
    - **Endpoint**: `GET /projects/{project_name}/activity-heatmap`
    - **Description**: Generates (or reuses cached) heatmap and returns metadata + a `png_url` to fetch the image.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Path Parameters**:
      - `{project_name}` (string, required): Project display name
    - **Query Parameters**:
      - `mode` (string, optional): `"diff"` or `"snapshot"`. Defaults to `"diff"`.
      - `normalize` (boolean, optional): Defaults to `true` (percent). If `false`, values are raw counts.
      - `include_unclassified_text` (boolean, optional): Defaults to `true` (text projects only).
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response DTO**: `ActivityHeatmapInfoDTO`
    - **Response Body**:
      ```json
      {
        "success": true,
        "data": {
          "project_name": "My Project",
          "mode": "diff",
          "normalize": true,
          "include_unclassified_text": true,
          "png_url": "/projects/My Project/activity-heatmap.png?mode=diff&normalize=true&include_unclassified_text=true"
        },
        "error": null
      }
      ```
    - **Error Responses**:
      - `401 Unauthorized` if missing/invalid/expired token
      - `404 Not Found` if project doesn't exist or doesn't belong to user
      - `400 Bad Request` if project has no versions

- **Get Activity Heatmap PNG**
    - **Endpoint**: `GET /projects/{project_name}/activity-heatmap.png`
    - **Description**: Returns the heatmap image as a PNG (`image/png`). Uses cached artifact when available.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Path Parameters**:
      - `{project_name}` (string, required): Project display name 
    - **Query Parameters**:
      - `mode` (string, optional): `"diff"` or `"snapshot"`. Defaults to `"diff"`.
      - `normalize` (boolean, optional): Defaults to `true`.
      - `include_unclassified_text` (boolean, optional): Defaults to `true` (text projects only).
    - **Request Body**: None
    - **Response Status**: `200 OK`
    - **Response**: Binary image download with MIME type `image/png`
    - **Response Headers**:
      - `Content-Type: image/png`
    - **Error Responses**:
      - `401 Unauthorized` if missing/invalid/expired token
      - `404 Not Found` if project doesn't exist or doesn't belong to user
      - `400 Bad Request` if project has no versions

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

- **TopProjectItemDTO** (used by `GET /projects/top`)
  - `projectId` (string, required): The `project_summary_id` as string
  - `title` (string, required): Project display name
  - `rankScore` (float, required): Computed importance score
  - `summarySnippet` (string, optional): Truncated summary (≈120 chars), or `null`
  - `versionCount` (int, default 0): Number of versions (upload snapshots) for this project

- **TopProjectsDTO**
  - `topProjects` (List[TopProjectItemDTO], required)

- **ProjectEvolutionDTO** (used by `GET /projects/{project_id}/evolution`)
  - `projectId` (string, required): The `project_summary_id` as string
  - `title` (string, required): Project display name
  - `versions` (List[EvolutionVersionDTO], required): Versions ordered oldest first

- **EvolutionVersionDTO**
  - `versionId` (string, required)
  - `date` (string, required): Activity or creation date (YYYY-MM-DD)
  - `summary` (string, required): Version summary text
  - `diff` (VersionDiffDTO, optional): Changes since previous version; `null` for first version
  - `skills` (List[string]): Skill names for this version
  - `skillsDetail` (List[object]): Skill objects with `skill_name`, `level`, `score`
  - `skillProgression` (SkillProgressionDTO, optional): New/improved/declined/removed skills vs previous version; `null` for first version
  - `languages` (List[string]): Languages detected
  - `frameworks` (List[string]): Frameworks detected
  - `avgComplexity` (float, optional): Average cyclomatic complexity; `null` for collaborative code
  - `totalFiles` (int, optional): File count for this version

- **VersionDiffDTO**
  - `linesAdded` (int, optional): Lines added since previous version; `null` when unavailable
  - `linesModified` (int, optional): Lines modified; `null` when unavailable
  - `linesRemoved` (int, optional): Lines removed since previous version; `null` when unavailable
  - `files` (FileDiffDTO, optional): File-level changes

- **FileDiffDTO**
  - `filesAdded` (List[string]): Paths of newly added files
  - `filesModified` (List[string]): Paths of modified files
  - `filesRemoved` (List[string]): Paths of removed files
  - `unchangedCount` (int): Count of unchanged files

- **SkillProgressionDTO**
  - `newSkills` (List[SkillChangeDTO]): Skills that appeared in this version
  - `improvedSkills` (List[SkillChangeDTO]): Skills with increased score
  - `declinedSkills` (List[SkillChangeDTO]): Skills with decreased score
  - `removedSkills` (List[SkillChangeDTO]): Skills that disappeared since previous version

- **SkillChangeDTO**
  - `skill_name` (string, required)
  - `level` (string, required)
  - `score` (float, required)
  - `prev_score` (float, optional): Previous version's score; `null` for new skills

### **Upload Wizard DTOs (Projects Upload)**

- **UploadDTO**
  - `upload_id` (int, required)
  - `status` (string, required)  
    Allowed values:
    - `"started"`
    - `"needs_dedup"`
    - `"parsed"`
    - `"needs_classification"`
    - `"needs_project_types"`
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

- **ManualProjectSummaryRequestDTO**
  - `summary_text` (string, required): User-provided manual project summary text

- **ManualContributionSummaryRequestDTO**
  - `manual_contribution_summary` (string, required): User-provided manual contribution summary text (what you did)

- **KeyRoleRequestDTO**
  - `key_role` (string, required): project role/title
  - Notes:
    - whitespace is normalized before storing
    - max length: `120`
    - blank input is allowed and treated as clear (`""`)


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

- **AddProjectRequestDTO**
  - `project_summary_id` (integer, required): `project_summary_id` from `project_summaries` (get from `GET /projects/ranking`)

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

- **PortfolioItemDTO**
    - `rank` (int, required): 1-based rank of the project within the portfolio
    - `project_name` (string, required): Internal project name
    - `display_name` (string, required): Human-friendly project title
    - `score` (float, required): Importance ranking score
    - `project_type` (string, optional): `"code"` or `"text"` (or `null` if unknown)
    - `project_mode` (string, optional): `"individual"` or `"collaborative"` (or `null` if unknown)
    - `start_date` (string, optional): ISO 8601 date string (YYYY-MM-DD)
    - `end_date` (string, optional): ISO 8601 date string (YYYY-MM-DD)
    - `languages` (List[string], optional): Languages associated with the project
    - `frameworks` (List[string], optional): Frameworks or libraries used
    - `summary_text` (string, optional): Short description of the project
    - `skills` (List[string], optional): High-level skills highlighted for this project
    - `text_type` (string, optional): For text projects, a label such as `"Academic writing"`
    - `contribution_percent` (float, optional): User's estimated contribution percentage (text projects)
    - `activities` (List[dict], optional): Activity breakdown entries (e.g. `{ "name": "feature_coding", "percent": 85.0 }`)

- **PortfolioDTO**
    - `items` (List[PortfolioItemDTO], required): Ranked list of portfolio items for the current user

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

### **User Profile DTOs**

- **UserProfileDTO**
  - `user_id` (int, required): Authenticated user's ID
  - `email` (string, optional): Contact email address (also stored on `users.email`)
  - `full_name` (string, optional): Full name used for resume/portfolio exports
  - `phone` (string, optional): Phone number shown in contact details
  - `linkedin` (string, optional): LinkedIn profile URL
  - `github` (string, optional): GitHub profile URL
  - `location` (string, optional): Location line (e.g. `"Kelowna, BC"`)
  - `profile_text` (string, optional): Short profile paragraph (max 600 characters)

- **UserProfileUpdateDTO**
  - `email` (string, optional): New email; blank or whitespace-only strings clear the email
  - `full_name` (string, optional): New full name; blank or whitespace-only strings clear the name
  - `phone` (string, optional): New phone; blank or whitespace-only strings clear the phone
  - `linkedin` (string, optional): New LinkedIn URL; blank or whitespace-only strings clear the URL
  - `github` (string, optional): New GitHub URL; blank or whitespace-only strings clear the URL
  - `location` (string, optional): New location; blank or whitespace-only strings clear the location
  - `profile_text` (string, optional): New profile paragraph; blank/whitespace-only strings clear the profile section
  
- **UserEducationEntryDTO**
  - `entry_id` (int, required): Unique identifier for the education/certification entry
  - `entry_type` (string, required): Either `"education"` or `"certificate"`
  - `title` (string, required): Degree, program, or certificate name
  - `organization` (string, optional): Institution or issuing organization
  - `date_text` (string, optional): Free-form date string (e.g. `"2022 - 2026"` or `"2025"`)
  - `description` (string, optional): Short description or notes
  - `display_order` (int, required): Order in which entries should appear on the resume
  - `created_at` (string, optional): ISO timestamp when the entry was created
  - `updated_at` (string, optional): ISO timestamp when the entry was last updated

- **UserEducationListDTO**
  - `entries` (List[UserEducationEntryDTO], required): Ordered list of education or certification entries

- **UserEducationEntryInputDTO**
  - `title` (string, required): Degree, program, or certificate name
  - `organization` (string, optional): Institution or issuing organization
  - `date_text` (string, optional): Free-form date string to show on the resume
  - `description` (string, optional): Short description or notes

- **UserEducationEntriesUpdateDTO**
  - `entries` (List[UserEducationEntryInputDTO], required): New list of entries to replace existing ones

- **UserExperienceEntryDTO**
  - `entry_id` (int, required): Unique identifier for the experience entry
  - `role` (string, required): Job title or role name
  - `company` (string, optional): Company or organization name
  - `date_text` (string, optional): Free-form date string (e.g. `"Sep 2025 - Dec 2025"`)
  - `description` (string, optional): Short description or notes
  - `display_order` (int, required): Order in which entries should appear on the resume
  - `created_at` (string, optional): ISO timestamp when the entry was created
  - `updated_at` (string, optional): ISO timestamp when the entry was last updated

- **UserExperienceListDTO**
  - `entries` (List[UserExperienceEntryDTO], required): Ordered list of experience entries

- **UserExperienceEntryInputDTO**
  - `role` (string, required): Job title or role name
  - `company` (string, optional): Company or organization name
  - `date_text` (string, optional): Free-form date text shown on the resume
  - `description` (string, optional): Short description or notes

- **UserExperienceEntriesUpdateDTO**
  - `entries` (List[UserExperienceEntryInputDTO], required): New list of entries to replace existing ones

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


### **Activity Heatmap DTOs**

- **ActivityHeatmapInfoDTO** (used by `GET /projects/{project_name}/activity-heatmap`)
  - `project_name` (string, required)
  - `mode` (string, required): `"diff"` or `"snapshot"`
  - `normalize` (boolean, required): `true` = percent per version column, `false` = raw counts
  - `include_unclassified_text` (boolean, required): text projects only
  - `png_url` (string, required): relative URL to fetch the PNG
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
