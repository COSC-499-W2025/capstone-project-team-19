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
```

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

## Testing

The frontend uses **Vitest** and **React Testing Library** for tests. Use Node `22.x` (recommended) for frontend tests.
`vitest`/`jsdom` do not work reliably on Node `21.x` and can fail with `ERR_REQUIRE_ESM`.

**Run tests once:**
```bash
cd frontend
npm install
npm run test:run
```

**Run tests in watch mode** (re-runs on file changes):
```bash
cd frontend
npm run test
```

Tests are co-located with the code they test (e.g. `src/api/__tests__/client.test.ts` next to `client.ts`). Vitest discovers all `*.test.ts` and `*.test.tsx` files automatically. The test environment uses jsdom to simulate a browser for component tests.
