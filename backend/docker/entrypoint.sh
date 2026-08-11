#!/bin/sh
set -eu

DB_HOST="${WORKFLOW_MYSQL_HOST:-db}"
DB_PORT="${WORKFLOW_MYSQL_PORT:-3306}"
DB_NAME="${WORKFLOW_MYSQL_DATABASE:-workflow_hub}"
DB_USER="${WORKFLOW_MYSQL_USER:-workflow_user}"
WAIT_TIMEOUT="${WORKFLOW_DB_WAIT_TIMEOUT:-60}"

echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT}/${DB_NAME} as ${DB_USER}..."
python - <<'PY'
import os
import time

import pymysql

host = os.environ.get("WORKFLOW_MYSQL_HOST", "db")
port = int(os.environ.get("WORKFLOW_MYSQL_PORT", "3306"))
database = os.environ.get("WORKFLOW_MYSQL_DATABASE", "workflow_hub")
user = os.environ.get("WORKFLOW_MYSQL_USER", "workflow_user")
password = os.environ.get("WORKFLOW_MYSQL_PASSWORD", "workflow_password")
timeout = int(os.environ.get("WORKFLOW_DB_WAIT_TIMEOUT", "60"))
deadline = time.time() + timeout
last_error = None

while time.time() < deadline:
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=3,
            write_timeout=3,
            read_timeout=3,
            charset="utf8mb4",
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        connection.close()
        print("MySQL connection is ready.")
        break
    except Exception as exc:
        last_error = exc
        time.sleep(2)
else:
    raise SystemExit(
        f"Database {host}:{port}/{database} did not become ready for user {user} "
        f"within {timeout} seconds. Last error: {last_error!r}"
    )
PY

echo "Running prepareworkflow..."
python manage.py prepareworkflow
echo "Starting application: $*"

exec "$@"
