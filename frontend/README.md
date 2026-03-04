# Frontend (React + Vite)

This folder contains the React frontend for the Capstone API.

## Prereqs
- Node.js + npm installed
- Backend API running locally (FastAPI)

## Setup

1) Create a local env file:

Create `frontend/.env.local` with:

```bash
VITE_API_BASE_URL=http://localhost:8000
````

2. Install and run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at `http://localhost:5173`.

## Backend requirement

The frontend expects the FastAPI backend to be running, otherwise API calls will fail.
Run:
```bash
uvicorn src.api.main:app --reload --env-file .env
```

Then confirm the backend is reachable:

* `GET http://localhost:8000/health` → `{"status":"ok"}`

## Common issues

* If you see CORS errors in the browser console, make sure the backend allows requests from `http://localhost:5173`.
* If `JWT_SECRET` is not set, login will fail.