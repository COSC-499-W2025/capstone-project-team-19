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
3. [PrivacyConsent](#privacyconsent)
4. [Skills](#skills)
5. [Resume](#resume)
6. [Portfolio](#portfolio)
7. [Path Variables](#path-variables)  
8. [DTO References](#dto-references)  
9. [Best Practices](#best-practices)  
10. [Error Codes](#error-codes)  
11. [Example Error Response](#example-error-response)  

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

## **PrivacyConsent**

**Base URL:** `/privacy-consent`

Handles user consent for internal processing and external integrations.

### **Endpoints**



---

## **Skills**

**Base URL:** `/skills`

Exposes extracted skills and timelines.

### **Endpoints**
- **Get Skills**
    - **Endpoint**: `GET /skills`
    - **Description**: Returns a chronological list of all skills extracted from the user's projects, including skill level, score, and associated project information.
    - **Headers**: 
        - `X-User-Id` (integer, required): Current user identifier
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
    - **Headers**: 
        - `X-User-Id` (integer, required): Current user identifier
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
    - **Endpoint**: `GET /resume/{resumeId}`
    - **Description**: Returns detailed information for a specific résumé snapshot, including all projects, aggregated skills, and rendered text.
    - **Path Parameters**:
        - `{resumeId}` (integer, required): The ID of the résumé snapshot
    - **Headers**: 
        - `X-User-Id` (integer, required): Current user identifier
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
