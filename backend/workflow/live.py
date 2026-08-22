from __future__ import annotations

import json
import queue
import threading
import uuid
from collections.abc import Iterator
from dataclasses import dataclass

from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone

from workflow.models import User
from workflow.security import decode_token


HEARTBEAT_SECONDS = 25
MAX_QUEUE_SIZE = 100

_subscribers: set["_LiveSubscriber"] = set()
_subscribers_lock = threading.Lock()


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
        return True
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


def publish_live_event(event_type: str, data: dict | None = None) -> None:
    event = {
        "id": uuid.uuid4().hex,
        "type": event_type,
        "data": data or {},
        "created_at": timezone.now().isoformat(),
    }
    for subscriber in _target_subscribers(event):
        try:
            subscriber.queue.put_nowait(event)
        except queue.Full:
            pass


def _subscribe(user: User) -> _LiveSubscriber:
    subscriber = _LiveSubscriber(
        queue=queue.Queue(maxsize=MAX_QUEUE_SIZE),
        user_id=user.id,
        organization_id=_user_organization_id(user),
        is_hq=_is_hq_user(user),
    )
    with _subscribers_lock:
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


def _event_stream(user: User) -> Iterator[str]:
    subscriber = _subscribe(user)
    try:
        yield "retry: 5000\n\n"
        yield f"data: {_encode({'type': 'live.connected', 'data': {}})}\n\n"
        while True:
            try:
                event = subscriber.queue.get(timeout=HEARTBEAT_SECONDS)
            except queue.Empty:
                yield f": heartbeat {timezone.now().isoformat()}\n\n"
                continue
            if not _can_receive_event(subscriber, event):
                continue
            yield f"id: {event['id']}\ndata: {_encode(event)}\n\n"
    finally:
        _unsubscribe(subscriber)


def live_events_view(request):
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed."}, status=405)
    user = _authenticate_live_user(request)
    if user is None:
        return JsonResponse({"detail": "توکن نامعتبر است."}, status=401)

    response = StreamingHttpResponse(_event_stream(user), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
