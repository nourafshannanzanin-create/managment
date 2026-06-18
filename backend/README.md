# Workflow Hub Backend

FastAPI backend for the existing `frontend/` UI with:

- MySQL persistence
- JWT authentication
- role-based access control
- local file uploads for request attachments
- seeded demo data for dashboard, requests, expenses, approvals, reports, users, and settings

## Stack

- FastAPI
- SQLAlchemy 2
- PyMySQL
- Uvicorn

## Local Setup

1. Create or start a MySQL database.
2. Copy `.env.example` to `.env`.
3. Update the `WORKFLOW_MYSQL_*` values if your local MySQL credentials differ.
4. Create a virtual environment and install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

5. Start the API:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If `WORKFLOW_AUTO_INIT_DB=true`, the app will create tables and seed demo data on startup.

## Demo Login

- Email: `admin@workflow.local`
- Password: `Admin123!`

## Docker MySQL

If Docker Desktop is running, you can start MySQL with:

```powershell
docker compose up -d
```

Then keep the default values from `.env.example`.
