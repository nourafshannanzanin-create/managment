# Workflow Hub Backend

Django backend for the existing `frontend/` UI with:

- MySQL persistence
- JWT authentication
- role-based access control
- local file uploads for requests, expenses, and approval documents
- automatic migration and demo seed support

## Stack

- Django 4.2
- PyMySQL
- PyJWT
- Passlib

## Local Setup

1. Create or start a MySQL database.
2. Copy `.env.example` to `.env`.
3. Update the `WORKFLOW_MYSQL_*` values if your local MySQL credentials differ.
4. Create a virtual environment and install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Run Backend

Use the Django command below from `backend/`:

```powershell
.\.venv\Scripts\python manage.py runworkflowserver 127.0.0.1:8000
```

This command applies migrations, seeds demo data if needed, and runs the API.

If you run plain `runserver`, the login/bootstrap flow can still auto-initialize the schema when `WORKFLOW_AUTO_INIT_DB=true`.

## Initial Login

- Email: `admin@karomand.local`
- Password: `AdminSecret!`

Other seeded users use:

- Password: `UserSecret123!`

## Docker MySQL

If Docker Desktop is running, you can start MySQL with:

```powershell
docker compose up -d
```

Then keep the default values from `.env.example`.
