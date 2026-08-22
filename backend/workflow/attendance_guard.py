from __future__ import annotations

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from workflow.models import AttendanceEvent, Organization, User


class AttendanceTransitionError(ValueError):
    pass


def latest_attendance_event_for_update(organization: Organization, user: User) -> AttendanceEvent | None:
    return (
        AttendanceEvent.objects.select_for_update()
        .filter(organization=organization, user=user)
        .order_by("-event_at", "-id")
        .first()
    )


def validate_attendance_transition(last_event: AttendanceEvent | None, event_type: str) -> None:
    if event_type == AttendanceEvent.EVENT_IN:
        if last_event is not None and last_event.event_type == AttendanceEvent.EVENT_IN:
            raise AttendanceTransitionError("ورود قبلاً ثبت شده و شیفت باز است.")
        return
    if event_type == AttendanceEvent.EVENT_OUT:
        if last_event is None or last_event.event_type != AttendanceEvent.EVENT_IN:
            raise AttendanceTransitionError("برای خروج، ابتدا باید ورود ثبت شده باشد.")
        return
    raise AttendanceTransitionError("نوع رویداد معتبر نیست.")


@transaction.atomic
def create_attendance_event(
    *,
    organization: Organization,
    user: User,
    event_type: str,
    source: str,
    note: str = "",
    event_at: datetime | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    distance_meters: float | None = None,
) -> AttendanceEvent:
    User.objects.select_for_update().filter(pk=user.pk).first()
    last_event = latest_attendance_event_for_update(organization, user)
    validate_attendance_transition(last_event, event_type)
    return AttendanceEvent.objects.create(
        organization=organization,
        user=user,
        event_type=event_type,
        source=source,
        note=note or "",
        event_at=event_at or timezone.now(),
        latitude=latitude,
        longitude=longitude,
        distance_meters=distance_meters,
    )
