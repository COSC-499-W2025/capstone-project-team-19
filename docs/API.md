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
2. [Projects](#projects)
3. [Uploads Wizard](#uploads-wizard)
4. [Privacy Consent](#privacyconsent)
5. [Skills](#skills)
6. [Resume](#resume)
7. [Portfolio](#portfolio)
8. [Path Variables](#path-variables)  
9. [DTO References](#dto-references)  
10. [Best Practices](#best-practices)  
11. [Error Codes](#error-codes)  
12. [Example Error Response](#example-error-response)  

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

## **Projects**

**Base URL:** `/projects`

Handles project ingestion, analysis, classification, and metadata updates.

### **Endpoints**

- **List Projects**
    - **Endpoint**: `GET /projects`
    - **Description**: Returns a list of all projects belonging to the current user.
    - **Headers**: 
        - `X-User-Id` (integer, required): Current user identifier
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
    - **Headers**:
        - `X-User-Id` (integer, required)
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
    - **Headers**:
        - `X-User-Id` (integer, required)
    - **Path Params**:
        - `upload_id` (integer, required)
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

- **Submit Project Classifications**
    - **Endpoint**: `POST /projects/upload/{upload_id}/classifications`
    - **Description**: Submit the user’s classification choices for projects detected within the uploaded ZIP. This replaces the CLI prompt where users classify each project as `individual` or `collaborative`.
    - **Headers**:
        - `X-User-Id` (integer, required)
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
    - **Headers**:
        - `X-User-Id` (integer, required)
    - **Path Params**:
        - `upload_id` (integer, required)
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



---

## **Skills**

**Base URL:** `/skills`

Exposes extracted skills and timelines.

### **Endpoints**



---

## **Resume**

**Base URL:** `/resume`

Manages résumé-specific representations of projects.

### **Endpoints**



---

## **Portfolio**

**Base URL:** `/portfolio`

Manages portfolio showcase configuration.

### **Endpoints**



---

## **Path Variables**

- `{id}` (integer, required): Generic resource identifier  
- `{projectId}` (integer, required): The ID of a project  
- `{resumeId}` (integer, required): The ID of a résumé  
- `{portfolioId}` (integer, required): The ID of a portfolio  

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
