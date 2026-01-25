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
4. [Uploads Wizard](#uploads-wizard)
5. [Privacy Consent](#privacyconsent)
6. [Skills](#skills)
7. [Resume](#resume)
8. [Portfolio](#portfolio)
9. [Path Variables](#path-variables)  
10. [DTO References](#dto-references)  
11. [Best Practices](#best-practices)  
12. [Error Codes](#error-codes)  
13. [Example Error Response](#example-error-response)  

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
        {"status":"ok"}
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

---

## **Uploads Wizard**

**Base URL:** `/projects/upload`

Uploads are tracked as a resumable multi-step “wizard” using an `uploads` table. Each upload has:
- an `upload_id`
- a `status` indicating the current step
- a `state` JSON blob storing wizard context (parsed layout, user selections, etc.)

### **Upload Status Values**

`uploads.status` is one of:

- `started` – upload session created
- `needs_classification` – user must classify projects (individual vs collaborative)
- `parsed` – classifications submitted (temporary state in current implementation)
- `needs_file_roles` – user must select file roles (e.g., main text file) and related inputs
- `needs_summaries` – user must provide manual summaries (when applicable)
- `analyzing` – analysis running
- `done` – analysis completed
- `failed` – upload failed (error stored in `state.error`)

### **Wizard Flow**

A typical flow for the first four endpoints:

1. **Start upload**: `POST /projects/upload`  
2. **Poll/resume**: `GET /projects/upload/{upload_id}`  
3. **Submit classifications**: `POST /projects/upload/{upload_id}/classifications`  
4. **Resolve mixed project types (optional)**: `POST /projects/upload/{upload_id}/project-types`  

---

### **Endpoints**

- **Start Upload**
    - **Endpoint**: `POST /projects/upload`
    - **Description**: Upload a ZIP file, save it to disk, parse the ZIP, and compute the project layout to determine the next wizard step. The server creates an `upload_id` and stores wizard state in the database.
    - **Auth: Bearer** means this header is required: `Authorization: Bearer <access_token>`
    - **Request Body**: `multipart/form-data`
        - `file` (file, required): ZIP file
    - **Response Status**: `200 OK`
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

- **Get Upload Status (Resume / Poll)**
    - **Endpoint**: `GET /projects/upload/{upload_id}`
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
    - **Response Status**: `200 OK`
    - **Response Body**:
        ```json
        {
            "success": true,
            "data": {
                "upload_id": 1,
                "status": "parsed",
                "zip_name": "text_projects.zip",
                "state": {
                    "message": "zip saved",
                    "classifications": {
                        "Project A": "individual",
                        "Project B": "collaborative"
                    }
                }
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
    - **Request Body**:
        ```json
        {
            "project_types": {
                "PlantGrowthStudy": "text"
            }
        }
        ```
    - **Response Status**: `200 OK`
    - **Notes**:
        - Returns `422 Unprocessable Entity` if the request includes unknown project names (not present in `layout.auto_assignments` or `layout.pending_projects`).
        - Returns `422 Unprocessable Entity` if project type values are not `code` or `text`.


---


## **Privacy Consent**

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
                        "project_name":"MyProjet",
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
    ```json
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
        
        



---

## **Portfolio**

**Base URL:** `/portfolio`

Manages portfolio showcase configuration.

### **Endpoints**



---

## **Path Variables**

- `{project_id}` (integer, required): The ID of a project (project_summary_id)  
- `{resume_id}` (integer, required): The ID of a résumé snapshot  
- `{upload_id}` (integer, required): The ID of an upload session  
- `{portfolio_id}` (integer, required): The ID of a portfolio (reserved for future use)  

---

## **DTO References**

DTOs (Data Transfer Objects) are defined using Pydantic models in `src/api/schemas/`.

Every endpoint must:
- Accept a DTO for its request body (when applicable)
- Return a DTO in its response body
- Reference the DTO it uses in this document

Example:
- **ProjectListItemDTO**
    - `project_summary_id` (int, required)
    - `project_name` (string, required)
    - `project_type` (string, optional)
    - `project_mode` (string, optional)
    - `created_at` (string, optional)

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


- **SkillEventDTO**
    - `skill_name` (string, required)
    - `level` (string, required)
    - `score` (float, required)
    - `project_name` (string, required)
    - `actual_activity_date` (string, optional)
    - `recorded_at` (string, optional)

- **SkillsListDTO**
    - `skills` (List[SkillEventDTO], required)

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
- **ProjectDetailDTO** (used by `GET /projects/{project_id}`)
    - `project_summary_id` (int, required)
    - `project_name` (string, required)
    - `project_type` (string, optional)
    - `project_mode` (string, optional)
    - `created_at` (string, optional)
    - `summary_text` (string, optional)
    - `languages` (array of strings, optional)
    - `frameworks` (array of strings, optional)
    - `skills` (array of strings, optional)
    - `metrics` (object, optional)
    - `contributions` (object, optional)

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

| Code | Description                              |
|------|------------------------------------------|
| 200  | OK – Request succeeded                   |
| 201  | Created – Resource successfully created  |
| 204  | No Content – Resource deleted            |
| 400  | Bad Request – Invalid input              |
| 401  | Unauthorized – Missing/invalid/expired token |
| 404  | Not Found – Resource not found           |
| 409  | Conflict – Duplicate or invalid state    |
| 422  | Unprocessable Entity – Validation error  |
| 500  | Internal Server Error – Unexpected error |

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
