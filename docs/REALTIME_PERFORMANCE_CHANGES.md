# Realtime & Performance Changes

## P0 completed in code

- Kept one ref-counted SSE connection per tab and extended it to retain the latest cursor in `sessionStorage` across a controlled close/reopen.
- Supports named SSE frames without breaking existing `message` consumers.
- Removed mutation/detail/background states from the application-wide blocking overlay; modal and row-level states remain local.
- Kept Nginx SSE buffering disabled on the SSE route only.
- Set conservative, environment-configured gthread defaults and added Gunicorn request recycling.
- Added Docker JSON log rotation for every compose service.

## P1 completed in code

- Added a durable `LiveOutbox` written inside the same transaction as a model mutation.
- Moved live fanout to `transaction.on_commit`; rollback no longer produces a browser event.
- Added standard envelope fields (`event_id`, entity, action, tenant, version, occurred_at) while retaining legacy `id`, `type`, and `data` fields.
- Added tenant-scoped replay through `Last-Event-ID` or the controlled reconnect cursor. Replay overflow sends `system.full_resync_required`, which triggers silent reconciliation.
- Added authenticated unsafe-request idempotency storage and replay. The frontend sends `Idempotency-Key`; recording and enforcement are independently feature-flagged until staging soak proves all clients are compatible.

## Operations

- Inspect retention first: `python manage.py prune_live_outbox --dry-run --retention-hours 72`
- Prune only by scheduled job after staging validation: `python manage.py prune_live_outbox --retention-hours 72`
- New migrations: `0036_live_outbox`, `0037_idempotency_record`.

## Rollback

- Disable `WORKFLOW_LIVE_OUTBOX_ENABLED`, `WORKFLOW_IDEMPOTENCY_ENABLED`, and `WORKFLOW_IDEMPOTENCY_ENFORCE`; do not delete idempotency or outbox data during rollback.
- Deploy the previous image only after confirming it tolerates the additive tables. Redis/SSE can be disabled independently; the DB remains authoritative.
