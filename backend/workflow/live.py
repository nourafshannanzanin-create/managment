from __future__ import annotations

import json
import logging
import os
import queue
import threading
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import timedelta

from django.db import close_old_connections, connection, transaction
from django.db.models import Q
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone

from workflow.models import LiveOutbox, User
from workflow.security import decode_token


HEARTBEAT_SECONDS = 25
MAX_QUEUE_SIZE = 100
MAX_REPLAY_EVENTS = int(os.getenv("WORKFLOW_LIVE_MAX_REPLAY_EVENTS", "500"))
MAX_REPLAY_AGE_HOURS = int(os.getenv("WORKFLOW_LIVE_MAX_REPLAY_AGE_HOURS", "72"))
LIVE_MAX_SUBSCRIBERS = int(os.getenv("WORKFLOW_LIVE_MAX_SUBSCRIBERS", "200"))
LIVE_REDIS_CHANNEL = os.getenv("WORKFLOW_LIVE_REDIS_CHANNEL", "workflow:live:events")

logger = logging.getLogger(__name__)

_subscribers: set["_LiveSubscriber"] = set()
_subscribers_lock = threading.Lock()
_redis_listener_started = False
_redis_listener_lock = threading.Lock()


def _env_enabled(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _replay_enabled() -> bool:
    return all(
        _env_enabled(name)
        for name in (
            "WORKFLOW_LIVE_OUTBOX_ENABLED",
            "WORKFLOW_LIVE_REPLAY_ENABLED",
            "WORKFLOW_LIVE_V2_ENABLED",
        )
    )


@dataclass(frozen=True)
class _LiveSubscriber:
    queue: queue.Queue[dict]
    user_id: int
    organization_id: int | None
    is_hq: bool


def _encode(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _is_hq_user(user: User) -> bool:
    platform_role = getattr(user, "platform_role", "") or ""
    return bool(platform_role.startswith("hq_"))


def _user_organization_id(user: User) -> int | None:
    membership = getattr(user, "organization_membership", None)
    return getattr(membership, "organization_id", None)


def _can_receive_event(subscriber: _LiveSubscriber, event: dict) -> bool:
    data = event.get("data") or {}
    if not data:
        # An unscoped event must never be exposed to a tenant user.
        return subscriber.is_hq
    if subscriber.is_hq:
        return True

    user_ids = data.get("user_ids")
    if isinstance(user_ids, list) and subscriber.user_id in {int(item) for item in user_ids if str(item).isdigit()}:
        return True

    user_id = data.get("user_id")
    if user_id is not None and str(user_id) == str(subscriber.user_id):
        return True

    organization_id = data.get("organization_id")
    if organization_id is not None:
        return str(organization_id) == str(subscriber.organization_id or "")

    return False


def _target_subscribers(event: dict) -> list[_LiveSubscriber]:
    data = event.get("data") or {}
    if not data:
        with _subscribers_lock:
            return list(_subscribers)

    targets: list[_LiveSubscriber] = []
    user_ids = {int(item) for item in (data.get("user_ids") or []) if str(item).isdigit()}
    user_id = data.get("user_id")
    organization_id = data.get("organization_id")

    with _subscribers_lock:
        for subscriber in _subscribers:
            if subscriber.is_hq:
                targets.append(subscriber)
                continue
            if user_ids and subscriber.user_id in user_ids:
                targets.append(subscriber)
                continue
            if user_id is not None and str(user_id) == str(subscriber.user_id):
                targets.append(subscriber)
                continue
            if organization_id is not None and str(organization_id) == str(subscriber.organization_id or ""):
                targets.append(subscriber)
                continue
    return targets


def _deliver_local(event: dict) -> None:
    for subscriber in _target_subscribers(event):
        try:
            subscriber.queue.put_nowait(event)
        except queue.Full:
            pass


def _redis_client():
    url = os.getenv("WORKFLOW_REDIS_URL", "").strip()
    if not url:
        return None
    try:
        import redis

        return redis.Redis.from_url(
            url,
            decode_responses=True,
            socket_keepalive=True,
            health_check_interval=30,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    except Exception:
        return None


def _redis_publish(event: dict) -> None:
    client = _redis_client()
    if client is None:
        return
    try:
        client.publish(LIVE_REDIS_CHANNEL, _encode(event))
    except Exception:
        logger.debug("live redis publish failed", exc_info=True)


def _ensure_redis_listener() -> None:
    global _redis_listener_started
    with _redis_listener_lock:
        if _redis_listener_started:
            return
        if _redis_client() is None:
            return
        _redis_listener_started = True

    def _loop() -> None:
        while True:
            try:
                client = _redis_client()
                if client is None:
                    raise RuntimeError("Redis client unavailable")
                # `listen()` converts an idle channel into a socket timeout
                # when finite request timeouts are enabled. Polling keeps an
                # idle channel quiet and reconnects only after real failures.
                with client.pubsub(ignore_subscribe_messages=True) as pubsub:
                    pubsub.subscribe(LIVE_REDIS_CHANNEL)
                    while True:
                        message = pubsub.get_message(timeout=1.0)
                        if not message or message.get("type") != "message":
                            continue
                        raw = message.get("data")
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8", errors="ignore")
                        if not raw:
                            continue
                        try:
                            event = json.loads(raw)
                        except (TypeError, ValueError):
                            continue
                        # Avoid double-delivery when publisher is this same process:
                        # publishers already delivered locally; only apply remote events.
                        if event.get("_origin") == os.getpid():
                            continue
                        _deliver_local(event)
            except Exception:
                logger.debug("live redis listener restarting", exc_info=True)
                threading.Event().wait(2)

    thread = threading.Thread(target=_loop, name="workflow-live-redis", daemon=True)
    thread.start()


def _event_from_outbox(row: LiveOutbox) -> dict:
    return {
        # `id` preserves compatibility with current clients; `event_id` is
        # explicit for new consumers and is a monotonic reconnect cursor.
        "id": str(row.id),
        "event_id": str(row.id),
        "type": row.event_type,
        "event_type": row.event_type,
        "entity": row.entity_type,
        "entity_id": row.entity_id,
        "action": row.action,
        "tenant_id": str(row.tenant_id) if row.tenant_id is not None else None,
        "actor_user_id": str(row.actor_user_id) if row.actor_user_id is not None else None,
        "version": row.version or row.created_at.isoformat(),
        "occurred_at": row.created_at.isoformat(),
        "data": row.payload or {},
        "_origin": os.getpid(),
    }


def _publish_outbox_row(row_id: int) -> None:
    # The callback runs after commit.  A missing row is harmless (for example
    # after controlled retention cleanup) because DB reconciliation remains
    # the source of truth.
    row = LiveOutbox.objects.filter(pk=row_id).first()
    if row is None:
        return
    event = _event_from_outbox(row)
    _deliver_local(event)
    # Strip origin for wire format consumers; redis listener filters on it.
    _redis_publish(event)


def _publish_legacy_event(event_type: str, payload: dict) -> None:
    """Safe dark-deploy fallback while the additive outbox table is absent."""
    event = {
        "id": uuid.uuid4().hex,
        "event_id": None,
        "type": event_type,
        "event_type": event_type,
        "data": payload,
        "occurred_at": timezone.now().isoformat(),
        "_origin": os.getpid(),
    }
    _deliver_local(event)
    _redis_publish(event)


def record_live_event(
    event_type: str,
    data: dict | None = None,
    *,
    tenant_id: int | None = None,
    entity_type: str = "entity",
    entity_id: str | int = "",
    action: str = "updated",
    actor_user_id: int | None = None,
    version: str = "",
) -> LiveOutbox | None:
    """Persist an invalidation in the mutation transaction and publish on commit."""
    if not _env_enabled("WORKFLOW_LIVE_OUTBOX_ENABLED"):
        # Do not touch the new table before its migration has been explicitly
        # applied. The legacy event remains an invalidation signal only.
        transaction.on_commit(lambda: _publish_legacy_event(event_type, data or {}))
        return None
    if not connection.in_atomic_block:
        raise RuntimeError("LiveOutbox must be written inside the business transaction.")
    row = LiveOutbox.objects.create(
        tenant_id=tenant_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        actor_user_id=actor_user_id,
        version=version,
        payload=data or {},
    )
    transaction.on_commit(lambda row_id=row.id: _publish_outbox_row(row_id))
    return row


def publish_live_event(event_type: str, data: dict | None = None) -> LiveOutbox | None:
    """Compatibility API for callers outside model signals.

    New code should pass explicit scope through ``record_live_event``.
    """
    payload = data or {}
    return record_live_event(
        event_type,
        payload,
        tenant_id=payload.get("organization_id"),
        entity_type=event_type.split(".", 1)[0],
        entity_id=payload.get("code") or payload.get("id") or "",
        action="created" if event_type.endswith(".created") else "updated",
        actor_user_id=payload.get("user_id") or payload.get("actor_user_id"),
    )


def _subscribe(user: User) -> _LiveSubscriber | None:
    with _subscribers_lock:
        if len(_subscribers) >= LIVE_MAX_SUBSCRIBERS:
            return None
        subscriber = _LiveSubscriber(
            queue=queue.Queue(maxsize=MAX_QUEUE_SIZE),
            user_id=user.id,
            organization_id=_user_organization_id(user),
            is_hq=_is_hq_user(user),
        )
        _subscribers.add(subscriber)
        return subscriber


def _unsubscribe(subscriber: _LiveSubscriber) -> None:
    with _subscribers_lock:
        _subscribers.discard(subscriber)


def _authenticate_live_user(request):
    token = (request.GET.get("token") or "").strip()
    if not token:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        return None
    return (
        User.objects.select_related("organization_membership__organization")
        .filter(pk=user_id, is_active=True)
        .first()
    )


def _parse_cursor(raw: str | None) -> int | None:
    try:
        value = int(str(raw or "").strip())
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def _replay_events(subscriber: _LiveSubscriber, last_event_id: int | None) -> Iterator[dict]:
    if last_event_id is None or not _replay_enabled():
        return
    if subscriber.is_hq:
        scoped = LiveOutbox.objects.all()
    elif subscriber.organization_id is not None:
        scoped = LiveOutbox.objects.filter(tenant_id=subscriber.organization_id)
    else:
        scoped = LiveOutbox.objects.filter(Q(actor_user_id=subscriber.user_id) | Q(tenant_id__isnull=True))

    newest = scoped.order_by("-id").only("id").first()
    oldest = scoped.order_by("id").only("id", "created_at").first()
    stale_cursor = bool(
        oldest
        and last_event_id < oldest.id - 1
        and oldest.created_at < timezone.now() - timedelta(hours=MAX_REPLAY_AGE_HOURS)
    )
    invalid_cursor = bool(newest and last_event_id > newest.id)
    if stale_cursor or invalid_cursor:
        reason = "cursor_expired" if stale_cursor else "cursor_invalid"
        yield {
            "id": str(newest.id if newest else last_event_id),
            "event_id": str(newest.id if newest else last_event_id),
            "type": "system.full_resync_required",
            "event_type": "system.full_resync_required",
            "data": {"reason": reason},
            "_origin": os.getpid(),
        }
        return

    candidates = list(scoped.filter(pk__gt=last_event_id).order_by("id")[: MAX_REPLAY_EVENTS + 1])
    if len(candidates) > MAX_REPLAY_EVENTS:
        yield {
            "id": str(candidates[-1].id),
            "event_id": str(candidates[-1].id),
            "type": "system.full_resync_required",
            "event_type": "system.full_resync_required",
            "data": {"reason": "replay_limit"},
            "_origin": os.getpid(),
        }
        return
    for row in candidates:
        event = _event_from_outbox(row)
        if _can_receive_event(subscriber, event):
            yield event


def _sse_frame(event: dict) -> str:
    wire = {key: value for key, value in event.items() if key != "_origin"}
    return f"id: {wire['id']}\nevent: {wire.get('type', 'message')}\ndata: {_encode(wire)}\n\n"


def _event_stream(user: User, last_event_id: int | None) -> Iterator[str]:
    # Register after stream starts so rejected connections do not consume slots.
    close_old_connections()
    subscriber = _subscribe(user)
    if subscriber is None:
        yield f"data: {_encode({'type': 'live.rejected', 'data': {'reason': 'capacity'}})}\n\n"
        return

    _ensure_redis_listener()
    try:
        # Drop request-scoped DB connection for the long-lived stream.
        connection.close()
        yield "retry: 5000\n\n"
        yield f"data: {_encode({'type': 'live.connected', 'data': {}})}\n\n"
        for event in _replay_events(subscriber, last_event_id):
            yield _sse_frame(event)
        while True:
            try:
                event = subscriber.queue.get(timeout=HEARTBEAT_SECONDS)
            except queue.Empty:
                yield f": heartbeat {timezone.now().isoformat()}\n\n"
                continue
            if not _can_receive_event(subscriber, event):
                continue
            yield _sse_frame(event)
    finally:
        _unsubscribe(subscriber)
        close_old_connections()


def live_events_view(request):
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed."}, status=405)
    user = _authenticate_live_user(request)
    if user is None:
        return JsonResponse({"detail": "توکن نامعتبر است."}, status=401)

    cursor = _parse_cursor(request.headers.get("Last-Event-ID"))
    if cursor is None:
        # EventSource cannot set custom headers on a fresh connection.  The
        # client also carries its per-tab cursor as a query parameter for a
        # close/reopen caused by visibility changes or a soft reload.
        cursor = _parse_cursor(request.GET.get("last_event_id"))
    response = StreamingHttpResponse(
        _event_stream(user, cursor),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
