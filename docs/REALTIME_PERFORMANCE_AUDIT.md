# Realtime & Performance Audit

Date: 2026-08-25

## Baseline findings

- The application already used a ref-counted physical `EventSource`, so concurrent route consumers do not create more than one SSE connection per tab.
- The frontend fetch wrapper already applies a finite timeout and abort signal. Direct page-level fetches remain a follow-up audit item before enabling strict idempotency.
- Nginx disables buffering only for `/api/v1/live/events`; its read timeout is safely above the 25-second heartbeat.
- The backend previously emitted from Django `post_save` immediately. A transaction rollback could therefore reach the browser, and Redis Pub/Sub loss had no durable replay source.
- Docker logging rotation and Gunicorn request recycling were missing from the compose/configuration path.

## Current safety status

- Source of truth: MySQL. Redis/SSE are invalidation transport only.
- Live outbox: implemented by migrations `0036_live_outbox` and `0037_idempotency_record`; not yet applied to a non-test database.
- Production state: **not changed**. No migration, data mutation, deployment, or ASGI cutover was executed.

## Required staging measurements

Record p50/p95/p99 latency, query counts for hot GETs, active SSE connections, RSS, CPU, MySQL connection count, Redis errors, reconnect rate, and Docker log growth before/after the staged migration.

## Known rollout gates

1. MariaDB strict mode warning must be resolved or explicitly accepted by the DBA.
2. MariaDB does not enforce the conditional active-task-timer unique constraint; the existing transaction lock remains required.
3. WSGI SSE is a P0 bridge only. ASGI requires the separate staging/canary process in the playbook.
