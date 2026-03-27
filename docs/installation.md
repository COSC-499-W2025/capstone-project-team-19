# Installation

This guide explains how to set up and run the system locally for development and testing.

## Backend Setup

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

### 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then generate and set a `JWT_SECRET` (required for running the API):

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste the output into your `.env` as the value for `JWT_SECRET`. All other variables in `.env` are for optional integrations and can be left as-is. See [Environment Variables and OAuth Setup](#environment-variables-and-oauth-setup) for details.

### 5. Run the backend

This project can be run in **one of two modes** - choose the one that fits your needs:

#### Option 1: API Mode (For Frontend Integration)

Runs the system as a web service using FastAPI. Use this mode when you want to connect a frontend application or make HTTP requests to the API.

```bash
# Ensure you are in the main directory
cd capstone-project-team-19

# Start the API server
uvicorn src.api.main:app --reload
```

> **Note:** If you are getting an error regarding `JWT_SECRET` missing from the .env file but it exists, try running `uvicorn src.api.main:app --reload --env-file .env` instead.

The API will be available at `http://localhost:8000`. You can:
    - View interactive API documentation at `http://localhost:8000/docs`
    - View alternative API docs at `http://localhost:8000/redoc`
    - Read the full endpoint reference in [API.md](./API.md)
    - Make HTTP requests to the API endpoints from your frontend or API client
    - For upload `/run` readiness rules, refer to [Analysis Ready Matrix](./run_analysis_readiness_matrix.txt)

You can also check the API is running correctly:
    - `http://localhost:8000/health` (returns `{"status": "ok"}`)

> **Note:** The API server runs independently - you do not need to run the CLI application.

#### Option 2: CLI Mode (For Direct Use)

Runs the system as a command-line interface. Use this mode for direct interaction via terminal prompts.

```bash
# Ensure you are in the main directory
cd capstone-project-team-19

# Start the CLI application
python -m src.main
```

> **Note:** The CLI runs independently - you do not need to run the API server. Both modes use the same underlying code and database.

### 6. Run Tests
Ensure you are in the main directory `/capstone-project-team-19`.

```bash
pytest tests
```

This runs the automated unit and integration test suite for the backend. If everything is set up correctly, you should see the tests pass.

## Frontend Setup
The frontend is located in the `frontend/` directory.

[Frontend README](../frontend/README.md)

Quick start:

```bash
cd frontend
npm install
npm run dev
```