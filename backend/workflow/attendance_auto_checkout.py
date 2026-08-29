from __future__ import annotations

from datetime import datetime, time

from django.db import transaction
from django.utils import timezone

from workflow.models import AttendanceEvent, AuditLog, FeaturePurchase, Organization, TaskStatus, TaskTimeEntry, User


END_OF_DAY_TIME = time(23, 59, 59)
AUTO_CHECKOUT_NOTE = "خروج خودکار — پایان روز (۲۳:۵۹)"


def organization_has_attendance(organization: Organization) -> bool:
    return FeaturePurchase.objects.filter(organization=organization, feature_key="attendance", is_active=True).exists()


def _stop_active_tasks_at(user: User, ended_at: datetime) -> list[str]:
    from workflow.tasking import log_activity, refresh_task_time_fields

    stopped_titles: list[str] = []
    entries = list(TaskTimeEntry.objects.filter(user=user, is_active=True).select_related("task"))
    for entry in entries:
        entry.ended_at = ended_at
        entry.duration_seconds = max(0, int((ended_at - entry.started_at).total_seconds()))
        entry.is_active = False
        entry.save(update_fields=["ended_at", "duration_seconds", "is_active"])
        task = entry.task
        if task.status == TaskStatus.IN_PROGRESS:
            task.status = TaskStatus.PAUSED
            task.updated_at = ended_at
            task.save(update_fields=["status", "updated_at", "version"])
            refresh_task_time_fields(task)
            log_activity(task, user, "paused", "توقف خودکار در پایان روز.")
        stopped_titles.append(task.title)
    return stopped_titles


def _checkout_user_shift(user: User, organization: Organization, checkout_at: datetime, stopped_tasks: list[str]) -> bool:
    detail_parts = ["خروج خودکار ساعت ۲۳:۵۹ ثبت شد."]
    if stopped_tasks:
        detail_parts.append(f"تسک‌های متوقف‌شده: {', '.join(stopped_tasks[:3])}")
        if len(stopped_tasks) > 3:
            detail_parts.append(f"و {len(stopped_tasks) - 3} مورد دیگر")
    detail = " ".join(detail_parts)

    AttendanceEvent.objects.create(
        organization=organization,
        user=user,
        event_type=AttendanceEvent.EVENT_OUT,
        source=AttendanceEvent.SOURCE_MANAGER,
        note=AUTO_CHECKOUT_NOTE,
        event_at=checkout_at,
    )
    AuditLog.objects.create(
        actor=None,
        actor_name=user.full_name,
        action="attendance_auto_checkout",
        entity_type="attendance",
        entity_code=str(user.id),
        detail=detail,
        icon="logout",
    )
    return True


def auto_checkout_open_shifts(*, target_date=None, organization: Organization | None = None) -> int:
    """Register checkout at 23:59 for open shifts and stop active task timers."""
    now = timezone.localtime()
    tz = timezone.get_current_timezone()

    org_qs = Organization.objects.all()
    if organization is not None:
        org_qs = org_qs.filter(pk=organization.pk)

    created = 0
    for org in org_qs:
        if not organization_has_attendance(org):
            continue

        user_ids = (
            AttendanceEvent.objects.filter(organization=org)
            .values_list("user_id", flat=True)
            .distinct()
        )
        users = User.objects.filter(pk__in=user_ids, is_active=True, is_deleted=False)

        for user in users:
            with transaction.atomic():
                last = (
                    AttendanceEvent.objects.select_for_update()
                    .filter(organization=org, user=user)
                    .order_by("-event_at", "-id")
                    .first()
                )
                if not last or last.event_type != AttendanceEvent.EVENT_IN:
                    continue

                checkin_local = timezone.localtime(last.event_at)
                checkin_date = target_date or checkin_local.date()
                if checkin_local.date() != checkin_date:
                    continue

                checkout_at = timezone.make_aware(datetime.combine(checkin_date, END_OF_DAY_TIME), tz)
                if now <= checkout_at:
                    continue

                if AttendanceEvent.objects.filter(
                    organization=org,
                    user=user,
                    event_type=AttendanceEvent.EVENT_OUT,
                    event_at__gt=last.event_at,
                ).exists():
                    continue

                if AttendanceEvent.objects.filter(
                    organization=org,
                    user=user,
                    event_type=AttendanceEvent.EVENT_OUT,
                    note=AUTO_CHECKOUT_NOTE,
                    event_at=checkout_at,
                ).exists():
                    continue

                stopped_tasks = _stop_active_tasks_at(user, checkout_at)
                if _checkout_user_shift(user, org, checkout_at, stopped_tasks):
                    created += 1

    return created
