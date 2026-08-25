# Production Rollout Checklist

## P0 — staging first

- [ ] Set `WORKFLOW_RUN_MIGRATIONS=false`, `WORKFLOW_LIVE_OUTBOX_ENABLED=false`, and `WORKFLOW_IDEMPOTENCY_ENABLED=false` for the initial Dark Deploy.
- [ ] Record image tag, DB backup verification, p95/p99, query count, RSS, MySQL connections, SSE connections, and log usage.
- [ ] Build frontend and run focused backend tests.
- [ ] Confirm exactly one physical SSE socket per tab after 20 route transitions.
- [ ] Confirm a background event does not show the full-screen overlay.
- [ ] Confirm Nginx config and Docker compose config render successfully.
- [ ] Calculate `workers × threads` against the DB connection ceiling; do not use defaults as a capacity calculation.

## P1 — migration and soak

- [ ] Apply additive migrations on staging: `python manage.py migrate`.
- [ ] Run the migration plan against the actual production database and stop if it contains unapproved operations.
- [ ] Verify event is absent after a rolled-back transaction and present only after commit.
- [ ] Disconnect client B, mutate in client A, reconnect B, and verify catch-up without reload.
- [ ] Verify tenant A never receives tenant B event or replay.
- [ ] Test duplicate request/payment/task action with the same `Idempotency-Key`; it must replay one response.
- [ ] Enable `WORKFLOW_LIVE_OUTBOX_ENABLED=true` only for a limited-tenant canary after migration.
- [ ] Then enable `WORKFLOW_IDEMPOTENCY_ENABLED=true` with `WORKFLOW_IDEMPOTENCY_ENFORCE=false` to observe compatible callers; enforce only after the canary.
- [ ] Run 24-hour soak: RSS, request rate while idle, DB connections, event lag, reconnect rate, and log disk usage must remain flat.

## P2

- [ ] Use `EXPLAIN` and query-budget tests before adding indexes.
- [ ] Confirm hot GET routes perform no writes.
- [ ] Schedule outbox pruning with 72-hour retention after a successful replay soak.

## P3 — separately authorized ASGI canary

- [ ] Audit middleware and third-party dependencies for async safety.
- [ ] Stage ASGI with production-like SSE load; then canary a small traffic slice.
- [ ] Keep the WSGI image/configuration as rollback target.
- [ ] Do not cut over whole production directly and do not roll back database data.
