#!/usr/bin/env bash
# Controlled production dark deploy for the realtime/idempotency release.
# It intentionally leaves all new runtime features disabled.

set -Eeuo pipefail

project_dir="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$project_dir"

test -f .env.production
test -f backend/workflow/migrations/0037_idempotency_record.py
grep -q 'WORKFLOW_LIVE_OUTBOX_ENABLED' backend/docker-compose.yml

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="$project_dir/backups"
mkdir -p "$backup_dir"
cp -p .env.production "$backup_dir/.env.production.before-dark-deploy.$stamp"

set_env() {
  local name="$1"
  local value="$2"
  if grep -q "^${name}=" .env.production; then
    sed -i "s|^${name}=.*|${name}=${value}|" .env.production
  else
    printf '\n%s=%s\n' "$name" "$value" >> .env.production
  fi
}

# Dark deploy: new tables may not exist yet, so code must keep old paths.
set_env WORKFLOW_RUN_MIGRATIONS false
set_env WORKFLOW_LIVE_OUTBOX_ENABLED false
set_env WORKFLOW_IDEMPOTENCY_ENABLED false
set_env WORKFLOW_IDEMPOTENCY_ENFORCE false

docker compose --env-file .env.production config --quiet

backup_file="$backup_dir/mysql-before-realtime-dark-deploy-$stamp.sql.gz"
docker compose --env-file .env.production exec -T db sh -ec \
  'exec mysqldump --single-transaction --routines --events --triggers -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' \
  | gzip -c > "$backup_file"
test -s "$backup_file"
gzip -t "$backup_file"
sha256sum "$backup_file"

docker compose --env-file .env.production build backend frontend

plan_file="$backup_dir/migrate-plan-$stamp.txt"
docker compose --env-file .env.production run --rm --no-deps --entrypoint python backend \
  manage.py showmigrations workflow
docker compose --env-file .env.production run --rm --no-deps --entrypoint python backend \
  manage.py migrate --plan | tee "$plan_file"

unexpected="$(
  grep -E '^[[:space:]]*workflow\.' "$plan_file" \
    | grep -Ev '^[[:space:]]*workflow\.(0036_live_outbox|0037_idempotency_record)$' \
    || true
)"

if [ -n "$unexpected" ]; then
  printf 'STOP: unapproved migrations detected:\n%s\n' "$unexpected"
  exit 1
fi

docker compose --env-file .env.production run --rm --no-deps --entrypoint python backend \
  manage.py check

# New containers start with feature flags off. Migration is then explicit.
docker compose --env-file .env.production up -d --no-deps backend frontend gateway-nginx
sleep 10

docker compose --env-file .env.production run --rm --no-deps --entrypoint python backend \
  manage.py migrate --noinput
docker compose --env-file .env.production restart backend
sleep 10

docker compose --env-file .env.production ps
curl -fsS http://127.0.0.1:18090/api/v1/health
docker compose --env-file .env.production logs --tail=150 backend

printf '\nSUCCESS: dark deploy complete; outbox and idempotency remain disabled.\nBackup: %s\nPlan: %s\n' \
  "$backup_file" "$plan_file"
