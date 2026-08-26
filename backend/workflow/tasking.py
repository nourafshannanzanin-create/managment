from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, time as dt_time
from typing import Any
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from workflow.access import can_access_users, can_manage_users, can_view_reports, get_user_organization, is_manager, organization_users
from workflow.services import media_url, next_code, normalize_person_name, user_avatar_url
from workflow.models import (
    AuditLog,
    Department,
    LeaveRequest,
    Organization,
    OrganizationPreference,
    RequestStatus,
    Task,
    TaskActivity,
    TaskAllocation,
    TaskAssignment,
    TaskAssignmentStatus,
    TaskAttachment,
    TaskComment,
    TaskMention,
    TaskObserver,
    TaskPriority,
    TaskReview,
    TaskReviewStatus,
    TaskStatus,
    TaskTimeEntry,
    TaskingSettings,
    User,
    UserRole,
)


DEFAULT_WORK_DAYS = [5, 6, 0, 1, 2, 3]  # Sat..Thu (Iran common work week)
PRIORITY_SCORE = {
    TaskPriority.CRITICAL: 1000,
    TaskPriority.HIGH: 700,
    TaskPriority.MEDIUM: 400,
    TaskPriority.NORMAL: 200,
    TaskPriority.LOW: 50,
}

TASK_TERMINAL_STATUSES = {TaskStatus.COMPLETED, TaskStatus.CANCELLED}

STATUS_LABELS = {
    TaskStatus.DRAFT: "پیش‌نویس",
    TaskStatus.PENDING_ACCEPTANCE: "نیازمند پذیرش",
    TaskStatus.SCHEDULED: "برنامه‌ریزی‌شده",
    TaskStatus.UPCOMING: "پیش‌رو",
    TaskStatus.IN_PROGRESS: "در حال انجام",
    TaskStatus.PAUSED: "متوقف‌شده",
    TaskStatus.BLOCKED: "مسدود",
    TaskStatus.PENDING_REVIEW: "در انتظار بررسی",
    TaskStatus.CHANGES_REQUESTED: "نیازمند اصلاح",
    TaskStatus.COMPLETED: "تکمیل‌شده",
    TaskStatus.CANCELLED: "لغوشده",
}

PRIORITY_LABELS = {
    TaskPriority.CRITICAL: "بحرانی",
    TaskPriority.HIGH: "بالا",
    TaskPriority.MEDIUM: "متوسط",
    TaskPriority.NORMAL: "عادی",
    TaskPriority.LOW: "پایین",
}


class TaskingError(Exception):
    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.message = message
        self.status = status


def _default_work_days() -> list[int]:
    return list(DEFAULT_WORK_DAYS)


def get_or_create_tasking_settings(organization: Organization, *, use_cache: bool = True) -> TaskingSettings:
    if use_cache:
        from workflow.cache_utils import get_cached_tasking_settings

        return get_cached_tasking_settings(organization)
    settings_obj, created = TaskingSettings.objects.get_or_create(
        organization=organization,
        defaults={"work_days": _default_work_days()},
    )
    if created and not settings_obj.work_days:
        settings_obj.work_days = _default_work_days()
        settings_obj.save(update_fields=["work_days"])
    if not settings_obj.work_days:
        settings_obj.work_days = _default_work_days()
        settings_obj.save(update_fields=["work_days"])
    # Migrate legacy Sat-Wed defaults to include Thursday.
    days = [int(item) for item in (settings_obj.work_days or [])]
    if sorted(days) == [0, 1, 2, 5, 6]:
        settings_obj.work_days = _default_work_days()
        settings_obj.save(update_fields=["work_days"])
    return settings_obj


def org_timezone(settings_obj: TaskingSettings) -> ZoneInfo:
    try:
        return ZoneInfo(settings_obj.timezone_name or "Asia/Tehran")
    except Exception:
        return ZoneInfo("Asia/Tehran")


def local_today(settings_obj: TaskingSettings) -> date:
    return timezone.now().astimezone(org_timezone(settings_obj)).date()


def parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if timezone.is_aware(value) else timezone.make_aware(value)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise TaskingError("تاریخ/زمان معتبر نیست.") from exc
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed)
    return parsed


def end_of_day_due_at(value: Any, settings_obj: TaskingSettings | None = None) -> datetime | None:
    """Deadline is day-only: store as end of that local day (23:59:59)."""
    if not value:
        return None
    tz = org_timezone(settings_obj) if settings_obj else ZoneInfo("Asia/Tehran")
    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and ("T" not in text[:11] or text.endswith("T00:00:00") or text.endswith("T00:00:00Z")):
        day = parse_iso_date(text[:10])
        if day is None:
            return None
        local_dt = datetime.combine(day, dt_time(23, 59, 59), tzinfo=tz)
        return local_dt.astimezone(timezone.get_current_timezone()) if timezone.get_current_timezone() else local_dt
    parsed = parse_iso_datetime(value)
    if parsed is None:
        return None
    local = parsed.astimezone(tz)
    local_eod = datetime.combine(local.date(), dt_time(23, 59, 59), tzinfo=tz)
    return local_eod


def parse_iso_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise TaskingError("تاریخ معتبر نیست.") from exc


def round_minutes(value: int, step: int) -> int:
    if step <= 1:
        return max(0, int(value))
    return max(step, int(round(int(value) / step) * step))


def serialize_user_brief(user: User | None) -> dict | None:
    if user is None:
        return None
    avatar = user_avatar_url(user)
    return {
        "id": user.id,
        "name": normalize_person_name(user.full_name),
        "avatar": user.avatar or "",
        "avatarUrl": avatar,
        "avatar_url": avatar,
        "jobTitle": user.job_title or "",
        "department": user.department.name if user.department_id else "",
        "role": user.role,
    }


def serialize_tasking_settings(settings_obj: TaskingSettings) -> dict:
    return {
        "enabled": settings_obj.enabled,
        "timezoneName": settings_obj.timezone_name,
        "workDays": list(settings_obj.work_days or _default_work_days()),
        "workDayStart": settings_obj.work_day_start.strftime("%H:%M"),
        "workDayEnd": settings_obj.work_day_end.strftime("%H:%M"),
        "breakMinutes": settings_obj.break_minutes,
        "subtractBreak": settings_obj.subtract_break,
        "targetUtilizationPercent": settings_obj.target_utilization_percent,
        "maxUtilizationPercent": settings_obj.max_utilization_percent,
        "underPlannedThresholdPercent": settings_obj.under_planned_threshold_percent,
        "overloadThresholdPercent": settings_obj.overload_threshold_percent,
        "allowOverbooking": settings_obj.allow_overbooking,
        "overbookingRequiresReason": settings_obj.overbooking_requires_reason,
        "schedulerMode": settings_obj.scheduler_mode,
        "allowTaskSplitting": settings_obj.allow_task_splitting,
        "minimumSegmentMinutes": settings_obj.minimum_segment_minutes,
        "roundEstimateToMinutes": settings_obj.round_estimate_to_minutes,
        "autoPrioritizeOverdue": settings_obj.auto_prioritize_overdue,
        "autoPrioritizeCritical": settings_obj.auto_prioritize_critical,
        "autoMoveHighPriority": settings_obj.auto_move_high_priority,
        "respectPinnedTasks": settings_obj.respect_pinned_tasks,
        "scheduleOnlyWorkingDays": settings_obj.schedule_only_working_days,
        "assignmentRequiresAcceptance": settings_obj.assignment_requires_acceptance,
        "assigneeCanReject": settings_obj.assignee_can_reject,
        "rejectionReasonRequired": settings_obj.rejection_reason_required,
        "completionRequiresReview": settings_obj.completion_requires_review,
        "defaultReviewerRule": settings_obj.default_reviewer_rule,
        "allowMultipleActiveTimers": settings_obj.allow_multiple_active_timers,
        "allowManualTimeEntry": settings_obj.allow_manual_time_entry,
        "manualTimeRequiresReason": settings_obj.manual_time_requires_reason,
        "showOwnUtilization": settings_obj.show_own_utilization,
        "showPeerUtilization": settings_obj.show_peer_utilization,
        "weekStartsOn": settings_obj.week_starts_on,
        "updatedAt": settings_obj.updated_at.isoformat() if settings_obj.updated_at else "",
    }


def update_tasking_settings(organization: Organization, payload: dict) -> TaskingSettings:
    settings_obj = get_or_create_tasking_settings(organization)
    mapping = {
        "enabled": ("enabled", bool),
        "timezoneName": ("timezone_name", str),
        "timezone_name": ("timezone_name", str),
        "workDays": ("work_days", list),
        "work_days": ("work_days", list),
        "workDayStart": ("work_day_start", "time"),
        "work_day_start": ("work_day_start", "time"),
        "workDayEnd": ("work_day_end", "time"),
        "work_day_end": ("work_day_end", "time"),
        "breakMinutes": ("break_minutes", int),
        "subtractBreak": ("subtract_break", bool),
        "targetUtilizationPercent": ("target_utilization_percent", int),
        "maxUtilizationPercent": ("max_utilization_percent", int),
        "underPlannedThresholdPercent": ("under_planned_threshold_percent", int),
        "overloadThresholdPercent": ("overload_threshold_percent", int),
        "allowOverbooking": ("allow_overbooking", bool),
        "overbookingRequiresReason": ("overbooking_requires_reason", bool),
        "schedulerMode": ("scheduler_mode", str),
        "allowTaskSplitting": ("allow_task_splitting", bool),
        "minimumSegmentMinutes": ("minimum_segment_minutes", int),
        "roundEstimateToMinutes": ("round_estimate_to_minutes", int),
        "autoPrioritizeOverdue": ("auto_prioritize_overdue", bool),
        "autoPrioritizeCritical": ("auto_prioritize_critical", bool),
        "autoMoveHighPriority": ("auto_move_high_priority", bool),
        "respectPinnedTasks": ("respect_pinned_tasks", bool),
        "scheduleOnlyWorkingDays": ("schedule_only_working_days", bool),
        "assignmentRequiresAcceptance": ("assignment_requires_acceptance", bool),
        "assigneeCanReject": ("assignee_can_reject", bool),
        "rejectionReasonRequired": ("rejection_reason_required", bool),
        "completionRequiresReview": ("completion_requires_review", bool),
        "defaultReviewerRule": ("default_reviewer_rule", str),
        "allowMultipleActiveTimers": ("allow_multiple_active_timers", bool),
        "allowManualTimeEntry": ("allow_manual_time_entry", bool),
        "manualTimeRequiresReason": ("manual_time_requires_reason", bool),
        "showOwnUtilization": ("show_own_utilization", bool),
        "showPeerUtilization": ("show_peer_utilization", bool),
        "weekStartsOn": ("week_starts_on", int),
    }
    update_fields = []
    for key, (field, cast) in mapping.items():
        if key not in payload:
            continue
        value = payload.get(key)
        if cast == "time":
            text = str(value or "").strip()
            try:
                hour, minute = [int(part) for part in text.split(":")[:2]]
                value = dt_time(hour, minute)
            except Exception as exc:
                raise TaskingError("ساعت کاری معتبر نیست.") from exc
        elif cast is bool:
            value = bool(value)
        elif cast is int:
            try:
                value = int(value)
            except (TypeError, ValueError) as exc:
                raise TaskingError(f"مقدار {key} معتبر نیست.") from exc
        elif cast is list:
            if not isinstance(value, list):
                raise TaskingError("روزهای کاری معتبر نیست.")
            value = [int(item) for item in value if str(item).strip() != ""]
        elif cast is str:
            value = str(value or "").strip()
        setattr(settings_obj, field, value)
        update_fields.append(field)

    if settings_obj.target_utilization_percent < 50 or settings_obj.target_utilization_percent > 95:
        raise TaskingError("هدف ظرفیت باید بین ۵۰ تا ۹۵ درصد باشد.")
    if settings_obj.max_utilization_percent < settings_obj.target_utilization_percent or settings_obj.max_utilization_percent > 100:
        raise TaskingError("سقف ظرفیت باید بین هدف و ۱۰۰ درصد باشد.")

    settings_obj.updated_at = timezone.now()
    update_fields.append("updated_at")
    settings_obj.save(update_fields=list(dict.fromkeys(update_fields)))
    from workflow.cache_utils import invalidate_tasking_settings_cache

    invalidate_tasking_settings_cache(organization.id)
    return settings_obj


def day_length_minutes(settings_obj: TaskingSettings, work_date: date, preference: OrganizationPreference | None = None) -> int:
    """Raw work-day length from settings/preference (never zero when hours are misconfigured)."""
    start = settings_obj.work_day_start
    end = settings_obj.work_day_end
    if preference and preference.work_day_start_time and preference.work_day_end_time:
        start = preference.work_day_start_time
        end = preference.work_day_end_time
    start_dt = datetime.combine(work_date, start)
    end_dt = datetime.combine(work_date, end)
    minutes = max(0, int((end_dt - start_dt).total_seconds() // 60))
    if minutes <= 0:
        minutes = 8 * 60
    if settings_obj.subtract_break:
        minutes = max(0, minutes - int(settings_obj.break_minutes or 0))
    return minutes if minutes > 0 else 8 * 60


def scheduled_work_minutes(settings_obj: TaskingSettings, work_date: date, preference: OrganizationPreference | None = None) -> int:
    work_days = settings_obj.work_days or _default_work_days()
    if settings_obj.schedule_only_working_days and work_date.weekday() not in work_days:
        return 0
    return day_length_minutes(settings_obj, work_date, preference)


def approved_leave_minutes(user: User, work_date: date) -> int:
    day_start = timezone.make_aware(datetime.combine(work_date, dt_time.min))
    day_end = timezone.make_aware(datetime.combine(work_date, dt_time.max))
    leaves = (
        LeaveRequest.objects.filter(
            request__requester=user,
            status=RequestStatus.APPROVED,
            starts_at__lt=day_end,
            ends_at__gt=day_start,
        )
        .select_related("request")
    )
    total = 0
    for leave in leaves:
        overlap_start = max(leave.starts_at, day_start)
        overlap_end = min(leave.ends_at, day_end)
        if overlap_end > overlap_start:
            total += int((overlap_end - overlap_start).total_seconds() // 60)
    return total


def effective_work_minutes(
    user: User,
    settings_obj: TaskingSettings,
    work_date: date,
    preference: OrganizationPreference | None = None,
) -> int:
    if preference is None:
        preference = OrganizationPreference.objects.filter(organization=settings_obj.organization).first()
    scheduled = scheduled_work_minutes(settings_obj, work_date, preference)
    leave = approved_leave_minutes(user, work_date)
    return max(0, scheduled - leave)


def capacity_for_day(
    user: User,
    settings_obj: TaskingSettings,
    work_date: date,
    *,
    preference: OrganizationPreference | None = None,
    batch_ctx=None,
) -> dict:
    closed_seconds = 0
    active_seconds = 0
    if batch_ctx is not None:
        metrics = batch_ctx.capacity_metrics(user.id, work_date)
        effective = metrics["effectiveWorkMinutes"]
        target = metrics["targetMinutes"]
        maximum = int(effective * settings_obj.max_utilization_percent / 100) if effective else 0
        planned = metrics["plannedMinutes"]
        actual_minutes = metrics["actualMinutes"]
        if preference is None:
            preference = batch_ctx.preference
        closed_seconds = batch_ctx.closed_seconds_by_user_date.get((user.id, work_date), 0)
        active = batch_ctx.active_by_user.get(user.id)
        if active is not None and active.started_at and active.started_at.astimezone(batch_ctx.tz).date() == work_date:
            active_seconds = max(0, int((timezone.now() - active.started_at).total_seconds()))
    else:
        if preference is None:
            preference = OrganizationPreference.objects.filter(organization=settings_obj.organization).first()
        effective = effective_work_minutes(user, settings_obj, work_date, preference=preference)
        if effective <= 0:
            effective = day_length_minutes(settings_obj, work_date, preference)
        target = int(effective * settings_obj.target_utilization_percent / 100) if effective else 0
        maximum = int(effective * settings_obj.max_utilization_percent / 100) if effective else 0
        planned = (
            TaskAllocation.objects.filter(user=user, work_date=work_date)
            .exclude(task__status__in=[TaskStatus.CANCELLED, TaskStatus.PENDING_ACCEPTANCE, TaskStatus.DRAFT])
            .aggregate(total=Sum("planned_minutes"))
            .get("total")
            or 0
        )
        tz = org_timezone(settings_obj)
        day_start = datetime.combine(work_date, dt_time.min, tzinfo=tz)
        day_end = datetime.combine(work_date, dt_time.max, tzinfo=tz)
        closed_entries = TaskTimeEntry.objects.filter(
            user=user,
            is_active=False,
            started_at__gte=day_start,
            started_at__lte=day_end,
        ).only("duration_seconds", "started_at", "ended_at")
        for entry in closed_entries:
            seconds = int(entry.duration_seconds or 0)
            if seconds <= 0 and entry.started_at and entry.ended_at:
                seconds = max(0, int((entry.ended_at - entry.started_at).total_seconds()))
            closed_seconds += seconds
        active_now = TaskTimeEntry.objects.filter(user=user, is_active=True).order_by("-started_at").first()
        if active_now is not None:
            local_started = active_now.started_at.astimezone(tz).date() if active_now.started_at else None
            if local_started == work_date:
                active_seconds = max(0, int((timezone.now() - active_now.started_at).total_seconds()))
        actual_minutes = max(0, int((closed_seconds + active_seconds) // 60))
    progress_base = int(planned) if int(planned) > 0 else int(target) if int(target) > 0 else int(effective)
    progress_denominator = int(target) if int(target) > 0 else int(effective)
    done_percent = int((actual_minutes / progress_denominator) * 100) if progress_denominator else (100 if actual_minutes else 0)
    done_percent = min(100, done_percent)

    load_minutes = max(int(planned), actual_minutes)
    utilization = int((actual_minutes / target) * 100) if target else (100 if actual_minutes else 0)
    if utilization < settings_obj.under_planned_threshold_percent:
        band = "under"
        band_label = "کمتر از ظرفیت هدف"
    elif utilization <= settings_obj.target_utilization_percent:
        band = "target"
        band_label = "در محدوده هدف"
    elif utilization <= settings_obj.max_utilization_percent:
        band = "high"
        band_label = "بار کاری بالا"
    else:
        band = "over"
        band_label = "بیش از ظرفیت"
    return {
        "date": work_date.isoformat(),
        "effectiveWorkMinutes": effective,
        "targetMinutes": target,
        "maxMinutes": maximum,
        "plannedMinutes": int(planned),
        "remainingTargetMinutes": max(0, target - int(planned)),
        "remainingMaxMinutes": max(0, maximum - int(planned)),
        "actualMinutes": actual_minutes,
        "timerClosedMinutes": max(0, int(closed_seconds // 60)),
        "timerActiveSeconds": int(active_seconds),
        "progressBaseMinutes": progress_base,
        "donePercent": done_percent,
        "utilizationPercent": utilization,
        "band": band,
        "bandLabel": band_label,
    }


def is_working_day(settings_obj: TaskingSettings, work_date: date) -> bool:
    work_days = settings_obj.work_days or _default_work_days()
    return work_date.weekday() in work_days


def next_working_day(settings_obj: TaskingSettings, start: date, *, skip_user: User | None = None) -> date:
    cursor = start
    for _ in range(366):
        if is_working_day(settings_obj, cursor):
            if skip_user is None or effective_work_minutes(skip_user, settings_obj, cursor) > 0:
                return cursor
        cursor += timedelta(days=1)
    return start


def priority_score(task: Task, settings_obj: TaskingSettings, today: date) -> int:
    score = PRIORITY_SCORE.get(task.priority, 200)
    if settings_obj.respect_pinned_tasks and task.is_pinned:
        score += 2000
    if task.due_at:
        due_local = task.due_at.astimezone(org_timezone(settings_obj)).date()
        if settings_obj.auto_prioritize_overdue and due_local < today:
            score += 800
        elif due_local == today:
            score += 500
        elif due_local == today + timedelta(days=1):
            score += 300
    age_days = max(0, (today - task.created_at.date()).days)
    score += min(age_days * 5, 100)
    return score


def supervised_user_ids(user: User) -> set[int] | None:
    """Return user IDs whose owned tasks this manager can supervise, or None for all org users."""
    if user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER}:
        return None
    if not is_manager(user):
        return {user.id}
    if can_view_reports(user) or can_manage_users(user) or can_access_users(user):
        return None

    org_users = organization_users(user).filter(is_active=True, is_deleted=False)
    managed_ids: set[int] = set()
    frontier = {user.id}
    while frontier:
        report_ids = set(org_users.filter(manager_id__in=frontier).values_list("id", flat=True))
        report_ids -= managed_ids
        report_ids.discard(user.id)
        if not report_ids:
            break
        managed_ids |= report_ids
        frontier = report_ids
    managed_ids.add(user.id)
    return managed_ids


def _user_can_supervise_owner(user: User, owner_id: int | None) -> bool:
    if owner_id is None:
        return False
    if owner_id == user.id:
        return True
    supervised_ids = supervised_user_ids(user)
    if supervised_ids is None:
        return is_manager(user) or user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER}
    return owner_id in supervised_ids


def can_delete_task(user: User, task: Task) -> bool:
    if task.deleted_at:
        return False
    if user.id != task.creator_id:
        return False
    return task.status not in TASK_TERMINAL_STATUSES


def can_view_task(user: User, task: Task) -> bool:
    if task.deleted_at:
        return False
    org = get_user_organization(user)
    if task.organization_id != org.id:
        return False
    if task.owner_id == user.id or task.creator_id == user.id:
        return True
    if TaskObserver.objects.filter(task=task, user=user).exists():
        return True
    if TaskReview.objects.filter(task=task, reviewer=user).exists():
        return True
    if _user_can_supervise_owner(user, task.owner_id):
        return True
    return False


def can_review_task(user: User, task: Task) -> bool:
    if task.owner_id == user.id:
        return False
    if TaskObserver.objects.filter(task=task, user=user, can_review=True).exists():
        return True
    if TaskReview.objects.filter(task=task, reviewer=user, status=TaskReviewStatus.PENDING).exists():
        return True
    if _user_can_supervise_owner(user, task.owner_id) and task.owner_id != user.id:
        return True
    if task.creator_id == user.id and is_manager(user):
        return True
    return False


def visible_tasks_queryset(user: User):
    org = get_user_organization(user)
    qs = (
        Task.objects.filter(organization=org, deleted_at__isnull=True)
        .select_related("owner", "creator", "department", "direct_manager_snapshot")
        .prefetch_related("observers", "allocations", "assignments", "attachments", "time_entries")
    )
    supervised_ids = supervised_user_ids(user)
    if supervised_ids is None and (user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER} or is_manager(user)):
        return qs
    if is_manager(user):
        return qs.filter(
            Q(owner=user)
            | Q(creator=user)
            | Q(owner_id__in=supervised_ids or {user.id})
            | Q(observers__user=user)
            | Q(reviews__reviewer=user)
        ).distinct()
    return qs.filter(
        Q(owner=user)
        | Q(creator=user)
        | Q(observers__user=user)
        | Q(assignments__assignee=user)
    ).distinct()


def supervised_tasks_queryset(user: User, qs=None):
    """Tasks visible in team/supervise views (excluding the viewer's own tasks)."""
    base = qs if qs is not None else visible_tasks_queryset(user)
    supervised_ids = supervised_user_ids(user)
    if supervised_ids is None and (user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER} or is_manager(user)):
        return base.exclude(owner=user)
    if is_manager(user):
        return base.filter(owner_id__in=supervised_ids or {user.id}).exclude(owner=user).distinct()
    return base.exclude(owner=user).filter(
        Q(observers__user=user) | Q(owner__manager=user) | Q(reviews__reviewer=user) | Q(creator=user)
    ).distinct()


def log_activity(task: Task, actor: User | None, action: str, detail: str = "", metadata: dict | None = None):
    TaskActivity.objects.create(
        task=task,
        actor=actor,
        actor_name=actor.full_name if actor else "",
        action=action,
        detail=detail,
        metadata=metadata or {},
    )
    AuditLog.objects.create(
        actor=actor,
        actor_name=actor.full_name if actor else "",
        action=f"task_{action}",
        entity_type="task",
        entity_code=task.code,
        detail=detail or task.title,
        icon="task_alt",
    )


def compute_actual_minutes(task: Task) -> int:
    total = (
        TaskTimeEntry.objects.filter(task=task, is_active=False).aggregate(total=Sum("duration_seconds")).get("total")
        or 0
    )
    active = TaskTimeEntry.objects.filter(task=task, is_active=True).first()
    if active:
        total += max(0, int((timezone.now() - active.started_at).total_seconds()))
    return int(total // 60)


def refresh_task_time_fields(task: Task):
    actual = compute_actual_minutes(task)
    remaining = max(0, int(task.estimated_minutes) - actual)
    task.actual_minutes = actual
    task.remaining_estimated_minutes = remaining
    task.updated_at = timezone.now()
    task.save(update_fields=["actual_minutes", "remaining_estimated_minutes", "updated_at", "version"])


def schedule_task(task: Task, *, settings_obj: TaskingSettings | None = None, start_date: date | None = None) -> list[TaskAllocation]:
    if task.status in {TaskStatus.PENDING_ACCEPTANCE, TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.DRAFT}:
        TaskAllocation.objects.filter(task=task, locked_by_user=False).delete()
        return []

    settings_obj = settings_obj or get_or_create_tasking_settings(task.organization)
    today = local_today(settings_obj)
    start = start_date or (task.start_not_before.astimezone(org_timezone(settings_obj)).date() if task.start_not_before else today)
    start = next_working_day(settings_obj, start, skip_user=task.owner)

    remaining = max(0, int(task.remaining_estimated_minutes or task.estimated_minutes or 0))
    if remaining <= 0:
        TaskAllocation.objects.filter(task=task, locked_by_user=False).delete()
        return []

    locked = list(TaskAllocation.objects.filter(task=task, locked_by_user=True).order_by("work_date", "sequence"))
    locked_minutes = sum(item.planned_minutes for item in locked)
    remaining = max(0, remaining - locked_minutes)

    TaskAllocation.objects.filter(task=task, locked_by_user=False).delete()

    allocations: list[TaskAllocation] = []
    cursor = start
    sequence = (locked[-1].sequence + 1) if locked else 1
    safety = 0
    while remaining > 0 and safety < 400:
        safety += 1
        cursor = next_working_day(settings_obj, cursor, skip_user=task.owner)
        capacity = capacity_for_day(task.owner, settings_obj, cursor)
        # Exclude current task from planned when recomputing
        other_planned = (
            TaskAllocation.objects.filter(user=task.owner, work_date=cursor)
            .exclude(task=task)
            .exclude(task__status__in=[TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.PENDING_ACCEPTANCE])
            .aggregate(total=Sum("planned_minutes"))
            .get("total")
            or 0
        )
        target_remaining = max(0, capacity["targetMinutes"] - int(other_planned))
        max_remaining = max(0, capacity["maxMinutes"] - int(other_planned))
        room = target_remaining
        due_forces = False
        if task.due_at:
            due_local = task.due_at.astimezone(org_timezone(settings_obj)).date()
            if due_local <= cursor:
                room = max_remaining
                due_forces = True
        if room <= 0:
            if settings_obj.allow_overbooking and due_forces:
                room = max(settings_obj.minimum_segment_minutes, min(remaining, max(30, max_remaining or 30)))
            else:
                cursor += timedelta(days=1)
                continue

        take = min(remaining, room)
        if settings_obj.allow_task_splitting:
            if take < settings_obj.minimum_segment_minutes and remaining > settings_obj.minimum_segment_minutes:
                # leave for later day if too small and more remains
                if not due_forces:
                    cursor += timedelta(days=1)
                    continue
            take = max(take, min(remaining, settings_obj.minimum_segment_minutes)) if due_forces else take
        else:
            take = remaining if room >= remaining else 0
            if take <= 0:
                cursor += timedelta(days=1)
                continue

        take = min(take, remaining)
        if take <= 0:
            cursor += timedelta(days=1)
            continue
        alloc = TaskAllocation.objects.create(
            task=task,
            user=task.owner,
            work_date=cursor,
            planned_minutes=take,
            sequence=sequence,
            segment_status="planned",
            is_over_capacity=other_planned + take > capacity["maxMinutes"],
            created_by_scheduler=True,
        )
        allocations.append(alloc)
        remaining -= take
        sequence += 1
        if not settings_obj.allow_task_splitting:
            break
        cursor += timedelta(days=1)

    if remaining > 0:
        cursor = next_working_day(settings_obj, cursor, skip_user=task.owner)
        alloc = TaskAllocation.objects.create(
            task=task,
            user=task.owner,
            work_date=cursor,
            planned_minutes=remaining,
            sequence=sequence,
            segment_status="planned",
            is_over_capacity=True,
            created_by_scheduler=True,
        )
        allocations.append(alloc)
        remaining = 0

    all_allocs = list(TaskAllocation.objects.filter(task=task).order_by("work_date", "sequence"))
    if all_allocs:
        first = all_allocs[0]
        last = all_allocs[-1]
        task.scheduled_start_at = timezone.make_aware(datetime.combine(first.work_date, settings_obj.work_day_start))
        task.scheduled_end_at = timezone.make_aware(datetime.combine(last.work_date, settings_obj.work_day_end))
        if task.status in {TaskStatus.SCHEDULED, TaskStatus.UPCOMING}:
            task.status = TaskStatus.UPCOMING if first.work_date > today else TaskStatus.SCHEDULED
        # Do not overwrite CHANGES_REQUESTED / IN_PROGRESS / PAUSED during reschedule
        task.updated_at = timezone.now()
        task.version += 1
        task.save(update_fields=["scheduled_start_at", "scheduled_end_at", "status", "updated_at", "version"])
    return all_allocs


def preview_schedule(user: User, estimated_minutes: int, settings_obj: TaskingSettings, *, start_date: date | None = None, due_at: datetime | None = None) -> dict:
    today = local_today(settings_obj)
    start = start_date or today
    start = next_working_day(settings_obj, start, skip_user=user)
    remaining = max(0, int(estimated_minutes))
    segments = []
    cursor = start
    safety = 0
    while remaining > 0 and safety < 60:
        safety += 1
        cursor = next_working_day(settings_obj, cursor, skip_user=user)
        capacity = capacity_for_day(user, settings_obj, cursor)
        room = capacity["remainingTargetMinutes"]
        if due_at and due_at.astimezone(org_timezone(settings_obj)).date() <= cursor:
            room = capacity["remainingMaxMinutes"]
        if room <= 0:
            cursor += timedelta(days=1)
            continue
        take = min(remaining, room)
        segments.append({"date": cursor.isoformat(), "plannedMinutes": take})
        remaining -= take
        cursor += timedelta(days=1)
    return {
        "estimatedMinutes": estimated_minutes,
        "segments": segments,
        "spillover": len(segments) > 1,
        "unscheduledMinutes": remaining,
    }


def serialize_allocation(item: TaskAllocation) -> dict:
    return {
        "id": item.id,
        "workDate": item.work_date.isoformat(),
        "plannedMinutes": item.planned_minutes,
        "sequence": item.sequence,
        "segmentStatus": item.segment_status,
        "isOverCapacity": item.is_over_capacity,
        "lockedByUser": item.locked_by_user,
    }


def serialize_comment(comment: TaskComment) -> dict:
    mention_rows = list(comment.mentions.select_related("mentioned_user").all()) if hasattr(comment, "mentions") else list(comment.mentions.all())
    parent = comment.parent
    parent_payload = None
    if parent_id := getattr(comment, "parent_id", None):
        parent = parent or TaskComment.objects.filter(pk=parent_id).select_related("author").first()
        if parent:
            parent_payload = {
                "id": parent.id,
                "body": (parent.body or "")[:180],
                "author": serialize_user_brief(parent.author),
            }
    return {
        "id": comment.id,
        "body": comment.body,
        "messageType": comment.message_type,
        "createdAt": comment.created_at.isoformat() if comment.created_at else "",
        "editedAt": comment.edited_at.isoformat() if comment.edited_at else "",
        "author": serialize_user_brief(comment.author),
        "parentId": comment.parent_id,
        "parent": parent_payload,
        "mentions": [item.mentioned_user_id for item in mention_rows],
        "mentionUsers": [
            serialize_user_brief(item.mentioned_user)
            for item in mention_rows
            if getattr(item, "mentioned_user_id", None)
        ],
    }


def _timer_payload(task: Task, user: User, active_timer: TaskTimeEntry | None) -> dict | None:
    if not active_timer:
        return None
    accumulated = (
        TaskTimeEntry.objects.filter(task=task, user=user, is_active=False).aggregate(total=Sum("duration_seconds")).get("total")
        or 0
    )
    current = max(0, int((timezone.now() - active_timer.started_at).total_seconds()))
    return {
        "id": active_timer.id,
        "startedAt": active_timer.started_at.isoformat(),
        "accumulatedSeconds": int(accumulated),
        "elapsedSeconds": int(accumulated) + current,
    }


def serialize_activity(item: TaskActivity) -> dict:
    return {
        "id": item.id,
        "action": item.action,
        "detail": item.detail,
        "createdAt": item.created_at.isoformat() if item.created_at else "",
        "actor": serialize_user_brief(item.actor) if item.actor_id else {"id": None, "name": item.actor_name},
        "metadata": item.metadata or {},
    }


def task_approved_at(task: Task):
    if task.review_status != TaskReviewStatus.APPROVED:
        return None
    return task.closed_at or task.completed_at


def serialize_task(task: Task, current_user: User, *, include_detail: bool = False, focus_date: date | None = None) -> dict:
    settings_obj = get_or_create_tasking_settings(task.organization)
    today = focus_date or local_today(settings_obj)
    allocations = list(task.allocations.all()) if hasattr(task, "_prefetched_objects_cache") else list(task.allocations.order_by("work_date", "sequence"))
    today_planned = sum(item.planned_minutes for item in allocations if item.work_date == today)
    spillover = sum(item.planned_minutes for item in allocations if item.work_date > today)
    actual_minutes = compute_actual_minutes(task)
    active_timer = next((item for item in task.time_entries.all() if item.is_active and item.user_id == current_user.id), None)
    if active_timer is None:
        active_timer = TaskTimeEntry.objects.filter(task=task, user=current_user, is_active=True).first()
    pending_assignment = next(
        (item for item in task.assignments.all() if item.status == TaskAssignmentStatus.PENDING and item.assignee_id == current_user.id),
        None,
    )
    unread_count = TaskMention.objects.filter(mentioned_user=current_user, read_at__isnull=True, comment__task=task).count()
    overdue = bool(task.due_at and task.due_at < timezone.now() and task.status not in {TaskStatus.COMPLETED, TaskStatus.CANCELLED})
    approved_at = task_approved_at(task)
    payload = {
        "id": task.id,
        "code": task.code,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "priorityLabel": PRIORITY_LABELS.get(task.priority, task.priority),
        "status": task.status,
        "statusLabel": STATUS_LABELS.get(task.status, task.status),
        "overdue": overdue,
        "assignee": serialize_user_brief(task.owner),
        "creator": serialize_user_brief(task.creator),
        "department": task.department.name if task.department_id else "",
        "departmentId": task.department_id,
        "category": task.category,
        "estimatedMinutes": task.estimated_minutes,
        "originalEstimatedMinutes": task.original_estimated_minutes,
        "remainingMinutes": task.remaining_estimated_minutes,
        "actualMinutes": actual_minutes,
        "todayPlannedMinutes": today_planned,
        "spilloverMinutes": spillover,
        "spillover": spillover > 0,
        "dueAt": task.due_at.isoformat() if task.due_at else "",
        "startNotBefore": task.start_not_before.isoformat() if task.start_not_before else "",
        "scheduledStartAt": task.scheduled_start_at.isoformat() if task.scheduled_start_at else "",
        "scheduledEndAt": task.scheduled_end_at.isoformat() if task.scheduled_end_at else "",
        "completedAt": task.completed_at.isoformat() if task.completed_at else "",
        "approvedAt": approved_at.isoformat() if approved_at else "",
        "closedAt": task.closed_at.isoformat() if task.closed_at else "",
        "reviewRequired": task.review_required,
        "reviewStatus": task.review_status,
        "reviewIteration": task.review_iteration,
        "isPinned": task.is_pinned,
        "sourceType": task.source_type,
        "deliveryNote": task.delivery_note,
        "blockedReason": task.blocked_reason,
        "hasUnreadComments": unread_count > 0,
        "unreadCount": unread_count,
        "attachmentsCount": task.attachments.count() if not hasattr(task, "_prefetched_objects_cache") else len(list(task.attachments.all())),
        "activeTimer": _timer_payload(task, current_user, active_timer),
        "pendingAssignment": bool(pending_assignment),
        "canAccept": bool(pending_assignment),
        "canReject": bool(pending_assignment),
        "canStart": task.owner_id == current_user.id and task.status in {TaskStatus.SCHEDULED, TaskStatus.UPCOMING, TaskStatus.PAUSED, TaskStatus.CHANGES_REQUESTED},
        "canPause": task.owner_id == current_user.id and task.status == TaskStatus.IN_PROGRESS,
        "canComplete": task.owner_id == current_user.id and task.status in {TaskStatus.IN_PROGRESS, TaskStatus.PAUSED, TaskStatus.SCHEDULED, TaskStatus.UPCOMING, TaskStatus.CHANGES_REQUESTED},
        "canReview": can_review_task(current_user, task) and task.status == TaskStatus.PENDING_REVIEW,
        "canEdit": current_user.id in {task.owner_id, task.creator_id} or is_manager(current_user) or can_review_task(current_user, task),
        "canDelete": can_delete_task(current_user, task),
        "version": task.version,
        "createdAt": task.created_at.isoformat() if task.created_at else "",
        "updatedAt": task.updated_at.isoformat() if task.updated_at else "",
        "allocations": [serialize_allocation(item) for item in sorted(allocations, key=lambda row: (row.work_date, row.sequence))],
    }
    if include_detail:
        payload["observers"] = [
            {
                **serialize_user_brief(item.user),
                "observerType": item.observer_type,
                "canReview": item.can_review,
            }
            for item in task.observers.select_related("user", "user__department")
        ]
        payload["comments"] = [
            serialize_comment(item)
            for item in task.comments.filter(deleted_at__isnull=True)
            .select_related("author")
            .prefetch_related("mentions__mentioned_user")
            .order_by("created_at")
        ]
        payload["activities"] = [serialize_activity(item) for item in task.activities.select_related("actor").order_by("-created_at")[:100]]
        payload["attachments"] = [
            {
                "id": item.id,
                "originalName": item.original_name,
                "fileUrl": media_url(item.stored_name),
                "mimeType": item.mime_type,
                "sizeBytes": item.size_bytes,
            }
            for item in task.attachments.all()
        ]
        payload["reviews"] = [
            {
                "id": item.id,
                "status": item.status,
                "comment": item.comment,
                "iterationNo": item.iteration_no,
                "reviewedAt": item.reviewed_at.isoformat() if item.reviewed_at else "",
                "reviewer": serialize_user_brief(item.reviewer),
            }
            for item in task.reviews.select_related("reviewer").order_by("-iteration_no", "-id")
        ]
        payload["assignments"] = [
            {
                "id": item.id,
                "status": item.status,
                "assignedAt": item.assigned_at.isoformat() if item.assigned_at else "",
                "respondedAt": item.responded_at.isoformat() if item.responded_at else "",
                "responseReason": item.response_reason,
                "assignee": serialize_user_brief(item.assignee),
                "assignedBy": serialize_user_brief(item.assigned_by),
            }
            for item in task.assignments.select_related("assignee", "assigned_by").order_by("-assigned_at")
        ]
    return payload


def ensure_default_reviewer(task: Task, settings_obj: TaskingSettings):
    reviewer = None
    rule = task.reviewer_rule or settings_obj.default_reviewer_rule
    if rule == "direct_manager" and task.owner.manager_id:
        reviewer = task.owner.manager
    elif rule == "creator":
        reviewer = task.creator
    elif rule == "task_observer":
        observer = task.observers.filter(can_review=True).select_related("user").first()
        reviewer = observer.user if observer else None
    if reviewer is None and task.owner.manager_id:
        reviewer = task.owner.manager
    if reviewer and reviewer.id != task.owner_id:
        TaskObserver.objects.update_or_create(
            task=task,
            user=reviewer,
            defaults={"observer_type": "reviewer", "can_review": True, "can_comment": True, "can_view_time": True},
        )
        TaskReview.objects.get_or_create(
            task=task,
            reviewer=reviewer,
            iteration_no=max(1, task.review_iteration or 1),
            defaults={"status": TaskReviewStatus.PENDING},
        )


@transaction.atomic
def create_task(actor: User, payload: dict, files=None) -> Task:
    organization = get_user_organization(actor)
    settings_obj = get_or_create_tasking_settings(organization)
    if not settings_obj.enabled:
        raise TaskingError("ماژول تسکینگ برای این مجموعه غیرفعال است.", status=403)

    title = (payload.get("title") or "").strip()
    if not title:
        raise TaskingError("عنوان تسک الزامی است.")
    try:
        estimated = int(payload.get("estimatedMinutes") or payload.get("estimated_minutes") or 0)
    except (TypeError, ValueError) as exc:
        raise TaskingError("زمان تخمینی معتبر نیست.") from exc
    if estimated <= 0:
        raise TaskingError("زمان تخمینی باید بیشتر از صفر باشد.")
    estimated = round_minutes(estimated, settings_obj.round_estimate_to_minutes)

    assignee_id = payload.get("assigneeId") or payload.get("assignee_id") or actor.id
    try:
        assignee_id = int(assignee_id)
    except (TypeError, ValueError) as exc:
        raise TaskingError("مسئول تسک معتبر نیست.") from exc
    assignee = organization_users(actor).filter(pk=assignee_id, is_active=True, is_deleted=False).select_related("manager", "department").first()
    if assignee is None:
        raise TaskingError("مسئول انتخاب‌شده در مجموعه یافت نشد یا غیرفعال است.")

    priority = (payload.get("priority") or TaskPriority.NORMAL).strip()
    if priority not in TaskPriority.values:
        raise TaskingError("اولویت معتبر نیست.")

    due_at = end_of_day_due_at(payload.get("dueAt") or payload.get("due_at"), settings_obj)
    start_not_before = parse_iso_datetime(payload.get("startNotBefore") or payload.get("start_not_before"))
    if due_at and start_not_before and due_at < start_not_before:
        raise TaskingError("ددلاین نمی‌تواند قبل از تاریخ شروع مجاز باشد.")

    for_other = assignee.id != actor.id
    if for_other and not is_manager(actor) and actor.role not in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER}:
        # employees can only create for self unless manager
        if assignee.manager_id != actor.id:
            raise TaskingError("اجازه ساخت تسک برای این کاربر را ندارید.", status=403)

    requires_acceptance = settings_obj.assignment_requires_acceptance and for_other
    # Self-created tasks complete without review; assigned tasks always need assigner review.
    if for_other:
        review_required = True
    else:
        review_required = False
    if "reviewRequired" in payload or "review_required" in payload:
        raw_review = payload.get("reviewRequired", payload.get("review_required"))
        if isinstance(raw_review, str):
            review_required = raw_review.strip().lower() in {"1", "true", "yes", "on"}
        elif raw_review is not None:
            review_required = bool(raw_review)
        if not for_other:
            review_required = False
    status = TaskStatus.PENDING_ACCEPTANCE if requires_acceptance else TaskStatus.SCHEDULED

    raw_department = payload.get("departmentId") if "departmentId" in payload else payload.get("department_id")
    department_id = assignee.department_id
    if raw_department not in (None, "", 0, "0"):
        if str(raw_department).isdigit():
            dept = Department.objects.filter(pk=int(raw_department)).exclude(code__in=["hq-control", "hq"]).first()
            if dept is None:
                raise TaskingError("بخش انتخاب‌شده معتبر نیست.")
            department_id = dept.id
        else:
            dept = Department.objects.filter(code=str(raw_department)).exclude(code__in=["hq-control", "hq"]).first()
            if dept is None:
                raise TaskingError("بخش انتخاب‌شده معتبر نیست.")
            department_id = dept.id

    task = Task.objects.create(
        organization=organization,
        code=next_code("TSK"),
        title=title,
        description=(payload.get("description") or "").strip(),
        category=(payload.get("category") or "").strip()[:80],
        department_id=department_id,
        creator=actor,
        owner=assignee,
        direct_manager_snapshot=assignee.manager,
        priority=priority,
        status=status,
        estimated_minutes=estimated,
        original_estimated_minutes=estimated,
        remaining_estimated_minutes=estimated,
        due_at=due_at,
        start_not_before=start_not_before,
        review_required=review_required,
        reviewer_rule=(payload.get("reviewerRule") or settings_obj.default_reviewer_rule),
        is_pinned=bool(payload.get("isPinned") or payload.get("is_pinned")),
        source_type="assigned" if for_other else "self",
        review_iteration=1 if review_required else 0,
    )

    if requires_acceptance:
        TaskAssignment.objects.create(task=task, assignee=assignee, assigned_by=actor, status=TaskAssignmentStatus.PENDING)
    else:
        TaskAssignment.objects.create(
            task=task,
            assignee=assignee,
            assigned_by=actor,
            status=TaskAssignmentStatus.ACCEPTED,
            responded_at=timezone.now(),
        )

    observer_ids = payload.get("observerIds") or payload.get("observer_ids") or []
    if not isinstance(observer_ids, list):
        observer_ids = []
    added_observer_ids: list[int] = []
    for oid in observer_ids:
        try:
            oid_int = int(oid)
        except (TypeError, ValueError):
            continue
        if oid_int in {actor.id, assignee.id}:
            continue
        user = organization_users(actor).filter(pk=oid_int, is_active=True).first()
        if user:
            TaskObserver.objects.get_or_create(
                task=task,
                user=user,
                defaults={"observer_type": "explicit", "can_review": bool(payload.get("observersCanReview")), "can_comment": True},
            )
            added_observer_ids.append(oid_int)
    if added_observer_ids:
        _notify_observers_on_create(task, actor, added_observer_ids)

    if assignee.manager_id and assignee.manager_id not in {assignee.id}:
        TaskObserver.objects.get_or_create(
            task=task,
            user_id=assignee.manager_id,
            defaults={"observer_type": "direct_manager", "can_review": True, "can_comment": True},
        )

    if review_required:
        ensure_default_reviewer(task, settings_obj)

    if files:
        from workflow.services import save_uploaded_file, validate_upload_file

        for file_obj in files:
            validate_upload_file(file_obj)
            stored = save_uploaded_file(file_obj)
            TaskAttachment.objects.create(
                task=task,
                uploader=actor,
                original_name=file_obj.name,
                stored_name=stored,
                mime_type=getattr(file_obj, "content_type", "") or "",
                size_bytes=int(getattr(file_obj, "size", 0) or 0),
            )

    log_activity(task, actor, "created", f"تسک «{task.title}» ایجاد شد.")
    if requires_acceptance:
        log_activity(task, actor, "assigned", f"به {assignee.full_name} ارجاع شد.")
    else:
        try:
            schedule_task(task, settings_obj=settings_obj)
            log_activity(task, actor, "scheduled", "برنامه زمانی تسک محاسبه شد.")
        except Exception:
            # Never fail task creation just because scheduling could not place segments yet.
            log_activity(task, actor, "created", "تسک ثبت شد؛ زمان‌بندی بعداً محاسبه می‌شود.")

    return Task.objects.select_related("owner", "creator", "department").prefetch_related(
        "allocations", "assignments", "observers", "attachments", "time_entries"
    ).get(pk=task.pk)


@transaction.atomic
def add_additional_estimate(actor: User, task: Task, additional_minutes: int, reason: str = "") -> Task:
    """Add extra planned minutes to an existing task and reschedule remaining work."""
    if actor.id not in {task.owner_id, task.creator_id} and not can_review_task(actor, task) and not is_manager(actor):
        raise TaskingError("اجازه افزودن زمان به این تسک را ندارید.", status=403)
    settings_obj = get_or_create_tasking_settings(task.organization)
    try:
        extra = round_minutes(int(additional_minutes or 0), settings_obj.round_estimate_to_minutes)
    except (TypeError, ValueError) as exc:
        raise TaskingError("زمان اضافی معتبر نیست.") from exc
    if extra <= 0:
        raise TaskingError("زمان اضافی باید بیشتر از صفر باشد.")
    refresh_task_time_fields(task)
    old = int(task.estimated_minutes or 0)
    task.estimated_minutes = old + extra
    task.remaining_estimated_minutes = max(0, int(task.remaining_estimated_minutes or 0) + extra)
    task.updated_at = timezone.now()
    task.version += 1
    task.save(update_fields=["estimated_minutes", "remaining_estimated_minutes", "updated_at", "version"])
    if task.status not in {TaskStatus.PENDING_ACCEPTANCE, TaskStatus.COMPLETED, TaskStatus.CANCELLED}:
        schedule_task(task, settings_obj=settings_obj)
    log_activity(
        task,
        actor,
        "estimate_added",
        reason or f"{extra} دقیقه به تخمین اضافه شد (از {old} به {task.estimated_minutes})",
        {"from": old, "added": extra, "to": task.estimated_minutes},
    )
    return task


@transaction.atomic
def change_task_assignee(actor: User, task: Task, assignee_id: int, reason: str = "") -> Task:
    if task.status in TASK_TERMINAL_STATUSES:
        raise TaskingError("تغییر مسئول پس از تکمیل مجاز نیست.", status=409)
    if actor.id not in {task.creator_id, task.owner_id} and not is_manager(actor):
        raise TaskingError("اجازه تغییر مسئول را ندارید.", status=403)
    try:
        assignee_id = int(assignee_id)
    except (TypeError, ValueError) as exc:
        raise TaskingError("مسئول تسک معتبر نیست.") from exc
    if assignee_id == task.owner_id:
        return task
    assignee = (
        organization_users(actor)
        .filter(pk=assignee_id, is_active=True, is_deleted=False)
        .select_related("manager", "department")
        .first()
    )
    if assignee is None:
        raise TaskingError("مسئول انتخاب‌شده در مجموعه یافت نشد یا غیرفعال است.")

    settings_obj = get_or_create_tasking_settings(task.organization)
    active = TaskTimeEntry.objects.filter(task=task, is_active=True).select_for_update().first()
    if active:
        _close_time_entry(active)
        refresh_task_time_fields(task)
        if task.status == TaskStatus.IN_PROGRESS:
            task.status = TaskStatus.PAUSED
            task.save(update_fields=["status", "updated_at", "version"])

    for_other = assignee.id != actor.id
    requires_acceptance = settings_obj.assignment_requires_acceptance and for_other
    previous_owner = task.owner
    task.owner = assignee
    task.direct_manager_snapshot = assignee.manager
    if not task.department_id and assignee.department_id:
        task.department_id = assignee.department_id
    if requires_acceptance:
        task.status = TaskStatus.PENDING_ACCEPTANCE
    elif task.status == TaskStatus.PENDING_ACCEPTANCE:
        task.status = TaskStatus.SCHEDULED
    task.updated_at = timezone.now()
    task.version += 1
    task.save(update_fields=["owner", "direct_manager_snapshot", "department", "status", "updated_at", "version"])

    task.assignments.filter(status=TaskAssignmentStatus.PENDING).update(status=TaskAssignmentStatus.CANCELLED)
    assignment_status = TaskAssignmentStatus.PENDING if requires_acceptance else TaskAssignmentStatus.ACCEPTED
    TaskAssignment.objects.create(
        task=task,
        assignee=assignee,
        assigned_by=actor,
        status=assignment_status,
        responded_at=None if requires_acceptance else timezone.now(),
    )

    TaskAllocation.objects.filter(task=task).delete()
    if not requires_acceptance and task.status not in TASK_TERMINAL_STATUSES:
        schedule_task(task, settings_obj=settings_obj)

    detail = reason or f"مسئول از {previous_owner.full_name} به {assignee.full_name} تغییر کرد."
    log_activity(task, actor, "reassigned", detail)
    return task


@transaction.atomic
def accept_task(actor: User, task: Task, additional_minutes: int = 0) -> Task:
    assignment = task.assignments.filter(assignee=actor, status=TaskAssignmentStatus.PENDING).select_for_update().first()
    if assignment is None:
        raise TaskingError("ارجاع قابل پذیرشی یافت نشد.", status=409)
    assignment.status = TaskAssignmentStatus.ACCEPTED
    assignment.responded_at = timezone.now()
    assignment.save(update_fields=["status", "responded_at"])
    task.owner = actor
    task.status = TaskStatus.SCHEDULED
    task.updated_at = timezone.now()
    task.version += 1
    task.save(update_fields=["owner", "status", "updated_at", "version"])
    if additional_minutes:
        add_additional_estimate(actor, task, additional_minutes, reason="زمان اضافه‌شده هنگام پذیرش ارجاع")
        task.refresh_from_db()
    settings_obj = get_or_create_tasking_settings(task.organization)
    schedule_task(task, settings_obj=settings_obj)
    log_activity(task, actor, "assignment_accepted", "ارجاع پذیرفته شد.")
    return task


@transaction.atomic
def reject_task(actor: User, task: Task, reason: str = "") -> Task:
    settings_obj = get_or_create_tasking_settings(task.organization)
    if not settings_obj.assignee_can_reject:
        raise TaskingError("رد ارجاع در تنظیمات غیرفعال است.", status=403)
    if settings_obj.rejection_reason_required and not (reason or "").strip():
        raise TaskingError("دلیل رد ارجاع الزامی است.")
    assignment = task.assignments.filter(assignee=actor, status=TaskAssignmentStatus.PENDING).select_for_update().first()
    if assignment is None:
        raise TaskingError("ارجاع قابل ردی یافت نشد.", status=409)
    assignment.status = TaskAssignmentStatus.REJECTED
    assignment.responded_at = timezone.now()
    assignment.response_reason = (reason or "").strip()
    assignment.save(update_fields=["status", "responded_at", "response_reason"])
    # Return ownership to creator for reassignment
    task.owner = task.creator
    task.status = TaskStatus.DRAFT
    task.updated_at = timezone.now()
    task.version += 1
    task.save(update_fields=["owner", "status", "updated_at", "version"])
    TaskAllocation.objects.filter(task=task).delete()
    log_activity(task, actor, "assignment_rejected", assignment.response_reason or "ارجاع رد شد.")
    return task


@transaction.atomic
def start_task(actor: User, task: Task, *, stop_other: bool = False, additional_minutes: int = 0) -> Task:
    if task.owner_id != actor.id:
        raise TaskingError("فقط مسئول تسک می‌تواند تایمر را شروع کند.", status=403)
    if task.status in {TaskStatus.PENDING_ACCEPTANCE, TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.BLOCKED}:
        raise TaskingError("شروع این تسک در وضعیت فعلی مجاز نیست.", status=409)

    if additional_minutes:
        add_additional_estimate(actor, task, additional_minutes, reason="زمان اضافه‌شده هنگام ادامه اصلاح")
        task.refresh_from_db()

    settings_obj = get_or_create_tasking_settings(task.organization)
    active = TaskTimeEntry.objects.select_for_update().filter(user=actor, is_active=True).first()
    if active and active.task_id != task.id:
        if not stop_other:
            raise TaskingError(
                f"تایمر تسک «{active.task.title}» فعال است. ابتدا آن را متوقف کنید.",
                status=409,
            )
        _close_time_entry(active)
        if active.task.status == TaskStatus.IN_PROGRESS:
            active.task.status = TaskStatus.PAUSED
            active.task.updated_at = timezone.now()
            active.task.save(update_fields=["status", "updated_at", "version"])
            refresh_task_time_fields(active.task)
            log_activity(active.task, actor, "paused", "به‌خاطر شروع تسک دیگر متوقف شد.")

    if TaskTimeEntry.objects.filter(user=actor, task=task, is_active=True).exists():
        return task

    TaskTimeEntry.objects.create(
        task=task,
        user=actor,
        started_at=timezone.now(),
        entry_type="timer",
        created_by=actor,
        is_active=True,
    )
    task.status = TaskStatus.IN_PROGRESS
    task.updated_at = timezone.now()
    task.version += 1
    task.save(update_fields=["status", "updated_at", "version"])
    log_activity(task, actor, "started", "اجرای تسک شروع شد.")
    return task


def _close_time_entry(entry: TaskTimeEntry):
    now = timezone.now()
    entry.ended_at = now
    entry.duration_seconds = max(0, int((now - entry.started_at).total_seconds()))
    entry.is_active = False
    entry.save(update_fields=["ended_at", "duration_seconds", "is_active"])


@transaction.atomic
def pause_task(actor: User, task: Task) -> Task:
    if task.owner_id != actor.id:
        raise TaskingError("فقط مسئول تسک می‌تواند تایمر را متوقف کند.", status=403)
    entry = TaskTimeEntry.objects.select_for_update().filter(task=task, user=actor, is_active=True).first()
    if entry is None:
        raise TaskingError("تایمر فعالی برای این تسک وجود ندارد.", status=409)
    _close_time_entry(entry)
    task.status = TaskStatus.PAUSED
    task.updated_at = timezone.now()
    task.version += 1
    task.save(update_fields=["status", "updated_at", "version"])
    refresh_task_time_fields(task)
    log_activity(task, actor, "paused", f"{entry.duration_seconds // 60} دقیقه ثبت شد.")
    return task


@transaction.atomic
def submit_review(actor: User, task: Task, delivery_note: str = "") -> Task:
    if task.owner_id != actor.id:
        raise TaskingError("فقط مسئول تسک می‌تواند آن را برای بررسی ارسال کند.", status=403)
    entry = TaskTimeEntry.objects.select_for_update().filter(task=task, user=actor, is_active=True).first()
    if entry:
        _close_time_entry(entry)
    refresh_task_time_fields(task)
    settings_obj = get_or_create_tasking_settings(task.organization)
    task.delivery_note = (delivery_note or "").strip()
    # Self-made tasks close immediately; assigned tasks need assigner/reviewer approval.
    assigned_by_other = bool(task.creator_id and task.creator_id != actor.id)
    has_inbound_assignment = task.assignments.filter(assignee=actor).exclude(
        status=TaskAssignmentStatus.REJECTED
    ).exists()
    needs_review = assigned_by_other or (bool(task.review_required) and has_inbound_assignment)
    if needs_review:
        task.status = TaskStatus.PENDING_REVIEW
        task.review_status = TaskReviewStatus.PENDING
        task.review_iteration = max(1, task.review_iteration or 1)
        ensure_default_reviewer(task, settings_obj)
        # Prefer the assigner/creator as reviewer for assigned tasks.
        if task.creator_id and task.creator_id != actor.id:
            TaskReview.objects.update_or_create(
                task=task,
                reviewer_id=task.creator_id,
                iteration_no=task.review_iteration,
                defaults={"status": TaskReviewStatus.PENDING},
            )
        TaskReview.objects.filter(task=task, iteration_no=task.review_iteration).update(status=TaskReviewStatus.PENDING)
        log_activity(task, actor, "completed_submitted", "برای بررسی ارسال شد.")
    else:
        task.status = TaskStatus.COMPLETED
        task.completed_at = timezone.now()
        task.closed_at = timezone.now()
        task.review_status = TaskReviewStatus.APPROVED
        refresh_task_time_fields(task)
        log_activity(task, actor, "completed", "تسک تکمیل و ثبت شد.")
    task.updated_at = timezone.now()
    task.version += 1
    task.save(
        update_fields=[
            "delivery_note",
            "status",
            "review_status",
            "review_iteration",
            "completed_at",
            "closed_at",
            "actual_minutes",
            "remaining_estimated_minutes",
            "updated_at",
            "version",
        ]
    )
    return task


@transaction.atomic
def approve_task(actor: User, task: Task, comment: str = "", additional_minutes: int = 0) -> Task:
    if not can_review_task(actor, task):
        raise TaskingError("اجازه بررسی این تسک را ندارید.", status=403)
    if task.status != TaskStatus.PENDING_REVIEW:
        raise TaskingError("تسک در انتظار بررسی نیست.", status=409)
    if additional_minutes:
        add_additional_estimate(actor, task, additional_minutes, reason="زمان اضافه‌شده هنگام تأیید اصلاح")
        task.refresh_from_db()
    review = TaskReview.objects.filter(task=task, reviewer=actor, iteration_no=task.review_iteration).first()
    if review is None:
        review = TaskReview.objects.create(
            task=task,
            reviewer=actor,
            iteration_no=task.review_iteration or 1,
            status=TaskReviewStatus.PENDING,
        )
    review.status = TaskReviewStatus.APPROVED
    review.comment = (comment or "").strip()
    review.reviewed_at = timezone.now()
    review.save(update_fields=["status", "comment", "reviewed_at"])
    task.status = TaskStatus.COMPLETED
    task.review_status = TaskReviewStatus.APPROVED
    task.completed_at = timezone.now()
    task.closed_at = timezone.now()
    refresh_task_time_fields(task)
    task.updated_at = timezone.now()
    task.version += 1
    task.save(
        update_fields=[
            "status",
            "review_status",
            "completed_at",
            "closed_at",
            "actual_minutes",
            "remaining_estimated_minutes",
            "updated_at",
            "version",
        ]
    )
    log_activity(task, actor, "review_approved", review.comment or "تسک تأیید و بسته شد.")
    return task


@transaction.atomic
def request_changes(actor: User, task: Task, comment: str = "", additional_minutes: int = 0) -> Task:
    if not can_review_task(actor, task):
        raise TaskingError("اجازه بررسی این تسک را ندارید.", status=403)
    if task.status != TaskStatus.PENDING_REVIEW:
        raise TaskingError("تسک در انتظار بررسی نیست.", status=409)
    if not (comment or "").strip():
        raise TaskingError("دلیل درخواست اصلاح الزامی است.")
    review = TaskReview.objects.filter(task=task, reviewer=actor, iteration_no=task.review_iteration).first()
    if review is None:
        review = TaskReview.objects.create(task=task, reviewer=actor, iteration_no=task.review_iteration or 1)
    review.status = TaskReviewStatus.CHANGES_REQUESTED
    review.comment = comment.strip()
    review.reviewed_at = timezone.now()
    review.save(update_fields=["status", "comment", "reviewed_at"])
    task.status = TaskStatus.CHANGES_REQUESTED
    task.review_status = TaskReviewStatus.CHANGES_REQUESTED
    task.review_iteration = (task.review_iteration or 1) + 1
    task.updated_at = timezone.now()
    task.version += 1
    task.save(update_fields=["status", "review_status", "review_iteration", "updated_at", "version"])
    TaskReview.objects.create(
        task=task,
        reviewer=actor,
        iteration_no=task.review_iteration,
        status=TaskReviewStatus.PENDING,
    )
    if additional_minutes:
        add_additional_estimate(actor, task, additional_minutes, reason="زمان اضافه‌شده برای اصلاح")
        task.refresh_from_db()
    else:
        settings_obj = get_or_create_tasking_settings(task.organization)
        remaining = max(task.remaining_estimated_minutes, settings_obj.minimum_segment_minutes)
        task.remaining_estimated_minutes = remaining
        task.save(update_fields=["remaining_estimated_minutes"])
        schedule_task(task, settings_obj=settings_obj)
    task.status = TaskStatus.CHANGES_REQUESTED
    task.updated_at = timezone.now()
    task.save(update_fields=["status", "updated_at"])
    log_activity(task, actor, "review_changes_requested", comment.strip())
    return task


@transaction.atomic
def update_estimate(actor: User, task: Task, estimated_minutes: int, reason: str = "") -> Task:
    if actor.id not in {task.owner_id, task.creator_id} and not can_review_task(actor, task) and not is_manager(actor):
        raise TaskingError("اجازه تغییر زمان تخمینی را ندارید.", status=403)
    settings_obj = get_or_create_tasking_settings(task.organization)
    estimated_minutes = round_minutes(int(estimated_minutes), settings_obj.round_estimate_to_minutes)
    if estimated_minutes <= 0:
        raise TaskingError("زمان تخمینی باید بیشتر از صفر باشد.")
    old = task.estimated_minutes
    if old and abs(estimated_minutes - old) / old > 0.3 and not (reason or "").strip():
        raise TaskingError("برای تغییر بیش از ۳۰٪، دلیل الزامی است.")
    refresh_task_time_fields(task)
    task.estimated_minutes = estimated_minutes
    task.remaining_estimated_minutes = max(0, estimated_minutes - task.actual_minutes)
    task.updated_at = timezone.now()
    task.version += 1
    task.save(update_fields=["estimated_minutes", "remaining_estimated_minutes", "updated_at", "version"])
    if task.status not in {TaskStatus.PENDING_ACCEPTANCE, TaskStatus.COMPLETED, TaskStatus.CANCELLED}:
        schedule_task(task, settings_obj=settings_obj)
    log_activity(task, actor, "estimate_changed", reason or f"از {old} به {estimated_minutes} دقیقه", {"from": old, "to": estimated_minutes})
    return task


def _notify_observers_on_create(task: Task, actor: User, observer_ids: list[int]) -> None:
    if not observer_ids:
        return
    body = f"شما به عنوان ناظر تسک «{task.title}» اضافه شدید."
    comment = TaskComment.objects.create(task=task, author=actor, body=body)
    org_user_ids = set(organization_users(actor).values_list("id", flat=True))
    for mid_int in observer_ids:
        if mid_int in org_user_ids and mid_int != actor.id:
            TaskMention.objects.get_or_create(comment=comment, mentioned_user_id=mid_int)


@transaction.atomic
def add_comment(actor: User, task: Task, body: str, parent_id: int | None = None, mention_ids: list[int] | None = None) -> TaskComment:
    if not can_view_task(actor, task):
        raise TaskingError("دسترسی به این تسک را ندارید.", status=403)
    body = (body or "").strip()
    if not body:
        raise TaskingError("متن پیام الزامی است.")
    parent = None
    if parent_id:
        parent = task.comments.filter(pk=parent_id, deleted_at__isnull=True).select_related("author").first()
    comment = TaskComment.objects.create(task=task, author=actor, parent=parent, body=body)
    org_user_ids = set(organization_users(actor).values_list("id", flat=True))
    mention_set = set()
    for mid in mention_ids or []:
        try:
            mention_set.add(int(mid))
        except (TypeError, ValueError):
            continue
    # Reply under a message also mentions the parent author
    if parent and parent.author_id and parent.author_id != actor.id:
        mention_set.add(parent.author_id)
    for mid_int in mention_set:
        if mid_int in org_user_ids and mid_int != actor.id:
            TaskMention.objects.get_or_create(comment=comment, mentioned_user_id=mid_int)
            TaskObserver.objects.get_or_create(
                task=task,
                user_id=mid_int,
                defaults={"observer_type": "mentioned", "can_review": False, "can_comment": True},
            )
    log_activity(task, actor, "comment_added", body[:180])
    return comment


@transaction.atomic
def mark_task_mentions_read(actor: User, task: Task) -> int:
    now = timezone.now()
    updated = TaskMention.objects.filter(
        mentioned_user=actor,
        read_at__isnull=True,
        comment__task=task,
        comment__deleted_at__isnull=True,
    ).update(read_at=now)
    return int(updated)


def _carry_forward_overdue_tasks(user: User, today: date) -> None:
    """Create today-allocations for incomplete tasks that only have past-day allocations."""
    active_statuses = [
        TaskStatus.SCHEDULED, TaskStatus.UPCOMING, TaskStatus.IN_PROGRESS,
        TaskStatus.PAUSED, TaskStatus.BLOCKED, TaskStatus.CHANGES_REQUESTED,
    ]
    past_task_ids = list(
        TaskAllocation.objects.filter(
            user=user,
            work_date__lt=today,
            task__status__in=active_statuses,
            task__deleted_at__isnull=True,
        ).values_list("task_id", flat=True).distinct()
    )
    if not past_task_ids:
        return
    already_today = set(
        TaskAllocation.objects.filter(user=user, work_date=today, task_id__in=past_task_ids)
        .values_list("task_id", flat=True)
    )
    need_carry = [tid for tid in past_task_ids if tid not in already_today]
    if not need_carry:
        return
    latest_allocs = {}
    for alloc in TaskAllocation.objects.filter(user=user, task_id__in=need_carry).order_by("task_id", "-work_date"):
        if alloc.task_id not in latest_allocs:
            latest_allocs[alloc.task_id] = alloc
    for alloc in latest_allocs.values():
        TaskAllocation.objects.create(
            task_id=alloc.task_id,
            user=user,
            work_date=today,
            planned_minutes=alloc.planned_minutes,
            sequence=0,
            segment_status="planned",
            created_by_scheduler=True,
        )


def dashboard_payload(user: User, focus_date: date | None = None, supervise_owner_id: int | None = None) -> dict:
    organization = get_user_organization(user)
    settings_obj = get_or_create_tasking_settings(organization)
    today = focus_date or local_today(settings_obj)

    if focus_date is None or focus_date == local_today(settings_obj):
        _carry_forward_overdue_tasks(user, today)

    qs = visible_tasks_queryset(user)
    my_tasks = qs.filter(owner=user).exclude(status__in=[TaskStatus.CANCELLED])
    pending_assignments = TaskAssignment.objects.filter(
        assignee=user,
        status=TaskAssignmentStatus.PENDING,
        task__deleted_at__isnull=True,
        task__organization=organization,
    ).select_related("task", "task__creator", "task__owner", "task__department", "assigned_by")
    supervised = supervised_tasks_queryset(user, qs)
    if supervise_owner_id:
        if _user_can_supervise_owner(user, supervise_owner_id):
            supervised = supervised.filter(owner_id=supervise_owner_id)
        else:
            supervised = supervised.none()

    capacity = capacity_for_day(user, settings_obj, today)
    closed_statuses = {
        TaskStatus.COMPLETED,
        TaskStatus.CANCELLED,
        TaskStatus.PENDING_REVIEW,
        TaskStatus.PENDING_ACCEPTANCE,
        TaskStatus.DRAFT,
    }
    tz = org_timezone(settings_obj)
    day_start = datetime.combine(today, dt_time.min, tzinfo=tz)
    day_end = datetime.combine(today, dt_time.max, tzinfo=tz)
    today_task_ids = list(
        TaskAllocation.objects.filter(user=user, work_date=today)
        .exclude(task__status__in=[TaskStatus.CANCELLED, TaskStatus.PENDING_ACCEPTANCE, TaskStatus.DRAFT])
        .values_list("task_id", flat=True)
        .distinct()
    )
    today_open_ids = list(
        my_tasks.filter(id__in=today_task_ids)
        .exclude(status__in=closed_statuses)
        .values_list("id", flat=True)
    )
    today_tasks = [
        serialize_task(item, user, focus_date=today)
        for item in my_tasks.filter(id__in=today_open_ids).order_by("priority", "due_at", "id")
    ]
    # Also include in-progress without allocation edge cases
    active_extra = my_tasks.filter(status__in=[TaskStatus.IN_PROGRESS, TaskStatus.PAUSED]).exclude(id__in=[t["id"] for t in today_tasks])
    today_tasks.extend(serialize_task(item, user, focus_date=today) for item in active_extra)

    def sort_key(item):
        return (-PRIORITY_SCORE.get(item["priority"], 0), item.get("dueAt") or "9999", item["id"])

    today_tasks = sorted(today_tasks, key=sort_key)

    upcoming = [
        serialize_task(item, user, focus_date=today)
        for item in my_tasks.filter(allocations__work_date__gt=today).exclude(status__in=closed_statuses).distinct()[:50]
    ]
    # Scheduled/open tasks without a future allocation still belong in "پیش‌رو"
    upcoming_ids = {item["id"] for item in upcoming}
    today_ids = {item["id"] for item in today_tasks}
    orphan_open = my_tasks.filter(
        status__in=[TaskStatus.SCHEDULED, TaskStatus.UPCOMING, TaskStatus.PAUSED, TaskStatus.BLOCKED]
    ).exclude(id__in=upcoming_ids | today_ids).order_by("-updated_at")[:50]
    upcoming.extend(serialize_task(item, user, focus_date=today) for item in orphan_open)
    in_progress = [serialize_task(item, user, focus_date=today) for item in my_tasks.filter(status__in=[TaskStatus.IN_PROGRESS, TaskStatus.PAUSED])]
    pending_review = [serialize_task(item, user, focus_date=today) for item in my_tasks.filter(status=TaskStatus.PENDING_REVIEW)]
    changes = [serialize_task(item, user, focus_date=today) for item in my_tasks.filter(status=TaskStatus.CHANGES_REQUESTED)]
    closed = [serialize_task(item, user, focus_date=today) for item in my_tasks.filter(status=TaskStatus.COMPLETED).order_by("-completed_at")[:50]]
    assignments = []
    for row in pending_assignments:
        task_payload = serialize_task(row.task, user, focus_date=today)
        task_payload["assignment"] = {
            "id": row.id,
            "assignedAt": row.assigned_at.isoformat() if row.assigned_at else "",
            "assignedBy": serialize_user_brief(row.assigned_by),
        }
        task_payload["schedulePreview"] = preview_schedule(
            user,
            row.task.estimated_minutes,
            settings_obj,
            due_at=row.task.due_at,
        )
        assignments.append(task_payload)

    outbound_qs = (
        Task.objects.filter(
            organization=organization,
            deleted_at__isnull=True,
            creator=user,
        )
        .exclude(owner=user)
        .exclude(status__in=[TaskStatus.CANCELLED])
        .select_related("owner", "creator", "department")
        .order_by("-updated_at")[:200]
    )
    outbound_all = [serialize_task(item, user, focus_date=today) for item in outbound_qs]
    outbound_pending_review = [item for item in outbound_all if item.get("status") == TaskStatus.PENDING_REVIEW]
    outbound_active = [
        item
        for item in outbound_all
        if item.get("status")
        in {
            TaskStatus.PENDING_ACCEPTANCE,
            TaskStatus.SCHEDULED,
            TaskStatus.UPCOMING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.PAUSED,
            TaskStatus.CHANGES_REQUESTED,
        }
    ]

    supervise_pending = [serialize_task(item, user, focus_date=today) for item in supervised.filter(status=TaskStatus.PENDING_REVIEW)]
    supervise_active = [serialize_task(item, user, focus_date=today) for item in supervised.filter(status__in=[TaskStatus.IN_PROGRESS, TaskStatus.PAUSED, TaskStatus.SCHEDULED, TaskStatus.UPCOMING])]
    supervise_overdue = [serialize_task(item, user, focus_date=today) for item in supervised.filter(due_at__lt=timezone.now()).exclude(status__in=[TaskStatus.COMPLETED, TaskStatus.CANCELLED])]
    supervise_done = [serialize_task(item, user, focus_date=today) for item in supervised.filter(status=TaskStatus.COMPLETED).order_by("-completed_at")[:50]]

    active_timer = TaskTimeEntry.objects.filter(user=user, is_active=True).select_related("task").first()
    unread_mentions_qs = (
        TaskMention.objects.filter(
            mentioned_user=user,
            read_at__isnull=True,
            comment__deleted_at__isnull=True,
            comment__task__organization=organization,
            comment__task__deleted_at__isnull=True,
        )
        .select_related("comment", "comment__author", "comment__task", "comment__task__owner", "comment__task__creator")
        .order_by("-id")
    )
    mention_task_ids = list(dict.fromkeys(unread_mentions_qs.values_list("comment__task_id", flat=True)))
    # Include mentioned tasks even if not otherwise in default visibility edge cases
    mention_task_qs = Task.objects.filter(
        id__in=mention_task_ids,
        organization=organization,
        deleted_at__isnull=True,
    ).select_related("owner", "creator", "department")
    mention_tasks = [serialize_task(item, user, focus_date=today) for item in mention_task_qs]
    mention_tasks.sort(key=lambda row: mention_task_ids.index(row["id"]) if row["id"] in mention_task_ids else 9999)
    unread_mention_count = unread_mentions_qs.count()
    # Also keep recently-read mentions briefly visible in "all"
    recent_mentions_qs = (
        TaskMention.objects.filter(
            mentioned_user=user,
            comment__deleted_at__isnull=True,
            comment__task__organization=organization,
            comment__task__deleted_at__isnull=True,
        )
        .select_related("comment__task")
        .order_by("-id")[:100]
    )
    all_mention_task_ids = list(dict.fromkeys(recent_mentions_qs.values_list("comment__task_id", flat=True)))
    all_mention_tasks = [
        serialize_task(item, user, focus_date=today)
        for item in Task.objects.filter(id__in=all_mention_task_ids, deleted_at__isnull=True).select_related("owner", "creator", "department")
    ]
    all_mention_tasks.sort(key=lambda row: all_mention_task_ids.index(row["id"]) if row["id"] in all_mention_task_ids else 9999)

    action_badge = (
        pending_assignments.count()
        + my_tasks.filter(status=TaskStatus.CHANGES_REQUESTED).count()
        + supervised.filter(status=TaskStatus.PENDING_REVIEW).count()
        + unread_mention_count
    )
    mine_open_count = my_tasks.exclude(status=TaskStatus.COMPLETED).count()
    mine_counts = {
        "today": len(today_tasks),
        "upcoming": len(upcoming),
        "inProgress": len(in_progress),
        "pendingReview": len(pending_review),
        "changesRequested": len(changes),
        "closed": len(closed),
        "all": mine_open_count,
    }
    assignment_counts = {
        "pending": len(assignments),
        "outbound": len(outbound_active),
        "outboundReview": len(outbound_pending_review),
        "all": len(assignments) + len(outbound_active) + len(outbound_pending_review),
    }
    supervise_open_count = len(supervise_pending) + len(supervise_active) + len(supervise_overdue)
    supervise_counts = {
        "pendingReview": len(supervise_pending),
        "inProgress": len(supervise_active),
        "overdue": len(supervise_overdue),
        "completed": len(supervise_done),
        "all": supervise_open_count,
    }

    supervise_focus = None
    supervised_ids = supervised_user_ids(user)
    team_qs = organization_users(user).filter(is_active=True, is_deleted=False).order_by("full_name")
    if supervised_ids is not None:
        team_qs = team_qs.filter(id__in=supervised_ids)
    elif is_manager(user) or user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER}:
        team_qs = team_qs.exclude(id=user.id)

    # Full org roster for task composer (managers need every employee + self).
    # Do NOT call capacity_for_day per user here — that N+1 made dashboard/create refresh hang.
    assignee_options_qs = (
        organization_users(user)
        .filter(is_active=True, is_deleted=False)
        .select_related("department", "manager")
        .order_by("full_name")
    )

    if supervise_owner_id:
        focus_owner = team_qs.filter(pk=supervise_owner_id).first()
        if focus_owner is not None:
            owner_capacity = capacity_for_day(focus_owner, settings_obj, today)
            owner_supervised = supervised.filter(owner=focus_owner)
            supervise_focus = {
                "user": serialize_user_brief(focus_owner),
                "capacity": owner_capacity,
                "stats": {
                    "todayCount": owner_supervised.filter(allocations__work_date=today).distinct().count(),
                    "remainingMinutes": owner_capacity["remainingTargetMinutes"],
                    "needsAction": (
                        owner_supervised.filter(status=TaskStatus.PENDING_REVIEW).count()
                        + owner_supervised.filter(status=TaskStatus.CHANGES_REQUESTED).count()
                        + owner_supervised.filter(due_at__lt=timezone.now())
                        .exclude(status__in=[TaskStatus.COMPLETED, TaskStatus.CANCELLED])
                        .count()
                    ),
                    "completedToday": owner_supervised.filter(
                        status=TaskStatus.COMPLETED,
                        completed_at__gte=day_start,
                        completed_at__lte=day_end,
                    ).count(),
                },
            }

    return {
        "date": today.isoformat(),
        "settings": serialize_tasking_settings(settings_obj),
        "capacity": capacity,
        "stats": {
            "todayCount": len(set(today_task_ids)),
            "remainingMinutes": capacity["remainingTargetMinutes"],
            "needsAction": action_badge,
            "completedToday": my_tasks.filter(
                status=TaskStatus.COMPLETED,
                completed_at__gte=day_start,
                completed_at__lte=day_end,
            ).count(),
            "unreadMentions": unread_mention_count,
            "mineCount": mine_open_count,
            "assignmentCount": assignment_counts["all"],
            "superviseCount": supervise_open_count,
        },
        "counts": {
            "mine": mine_counts,
            "assignments": assignment_counts,
            "supervise": supervise_counts,
            "mentions": unread_mention_count,
            "mentionsAll": len(all_mention_task_ids),
        },
        "badgeCount": action_badge,
        "activeTimer": (
            {
                "taskId": active_timer.task_id,
                "taskTitle": active_timer.task.title,
                **(_timer_payload(active_timer.task, user, active_timer) or {}),
            }
            if active_timer
            else None
        ),
        "mine": {
            "today": today_tasks,
            "upcoming": upcoming,
            "inProgress": in_progress,
            "pendingReview": pending_review,
            "changesRequested": changes,
            "closed": closed,
            "all": [serialize_task(item, user, focus_date=today) for item in my_tasks.order_by("-updated_at")[:200]],
        },
        "assignments": {
            "pending": assignments,
            "outbound": outbound_active,
            "outboundReview": outbound_pending_review,
            "outboundActive": outbound_active,
            "accepted": [],
            "rejected": [],
            "all": assignments + outbound_active + outbound_pending_review,
        },
        "supervise": {
            "pendingReview": supervise_pending,
            "inProgress": supervise_active,
            "overdue": supervise_overdue,
            "completed": supervise_done,
            "all": [serialize_task(item, user, focus_date=today) for item in supervised.order_by("-updated_at")[:200]],
            "summary": {
                "pendingReview": len(supervise_pending),
                "inProgress": len(supervise_active),
                "overdue": len(supervise_overdue),
                "changesRequested": supervised.filter(status=TaskStatus.CHANGES_REQUESTED).count(),
            },
        },
        "mentions": {
            "unread": mention_tasks,
            "all": all_mention_tasks,
        },
        "departments": [
            {"id": item.id, "code": item.code, "name": item.name}
            for item in Department.objects.exclude(code__in=["hq-control", "hq"]).exclude(name__iexact="HQ").exclude(code__endswith="-admin").order_by("name")
        ],
        "superviseTeamMembers": [serialize_user_brief(item) for item in team_qs[:300]],
        "supervise_team_members": [serialize_user_brief(item) for item in team_qs[:300]],
        "assigneeOptions": [
            {
                **serialize_user_brief(item),
                "capacityToday": None,
            }
            for item in assignee_options_qs[:500]
        ],
        "superviseFocus": supervise_focus,
    }


def reports_summary(user: User, *, start: date, end: date, user_id: int | None = None) -> dict:
    from workflow.performance import CapacityBatchContext, batch_task_stats

    organization = get_user_organization(user)
    settings_obj = get_or_create_tasking_settings(organization)
    users_qs = organization_users(user).filter(is_active=True, is_deleted=False).select_related("department")
    if user_id:
        users_qs = users_qs.filter(pk=user_id)
    if not is_manager(user) and user.role not in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER}:
        users_qs = users_qs.filter(pk=user.id)

    people = list(users_qs)
    user_ids = [person.id for person in people]
    batch_ctx = CapacityBatchContext(settings_obj=settings_obj, user_ids=user_ids, start=start, end=end)
    task_stats = batch_task_stats(organization.id, user_ids, start=start, end=end)

    rows = []
    buckets = {"under": 0, "target": 0, "high": 0, "over": 0}
    completed_tasks = Task.objects.filter(
        organization=organization,
        owner_id__in=user_ids,
        deleted_at__isnull=True,
        status=TaskStatus.COMPLETED,
        completed_at__date__gte=start,
        completed_at__date__lte=end,
    ).only("owner_id", "estimated_minutes", "actual_minutes")
    variance_by_user: dict[int, list[float]] = defaultdict(list)
    for task in completed_tasks:
        if task.estimated_minutes:
            variance_by_user[task.owner_id].append((task.actual_minutes - task.estimated_minutes) / task.estimated_minutes)

    for person in people:
        planned = 0
        target = 0
        actual = 0
        cursor = start
        days = 0
        day_rows = []
        while cursor <= end:
            if is_working_day(settings_obj, cursor):
                cap = capacity_for_day(person, settings_obj, cursor, batch_ctx=batch_ctx)
                day_target = int(cap["targetMinutes"] or 0)
                day_actual = int(cap["actualMinutes"] or 0)
                day_deficit = max(0, day_target - day_actual)
                day_overtime = max(0, day_actual - day_target)
                day_ratio = (day_actual / day_target) if day_target else (1.0 if day_actual else 0.0)
                if day_target <= 0 and day_actual <= 0:
                    day_status = "empty"
                    day_status_label = "بدون داده"
                elif day_ratio >= 0.95:
                    day_status = "ok"
                    day_status_label = "در هدف"
                elif day_ratio >= 0.7:
                    day_status = "warn"
                    day_status_label = "کسری جزئی"
                else:
                    day_status = "bad"
                    day_status_label = "کسری زیاد"
                if day_overtime > 0 and day_status == "ok":
                    day_status_label = "اضافه‌کار"
                day_rows.append(
                    {
                        "date": cursor.isoformat(),
                        "targetMinutes": day_target,
                        "actualMinutes": day_actual,
                        "deficitMinutes": day_deficit,
                        "overtimeMinutes": day_overtime,
                        "utilizationPercent": int(day_ratio * 100) if day_target else (100 if day_actual else 0),
                        "status": day_status,
                        "statusLabel": day_status_label,
                    }
                )
                planned += cap["plannedMinutes"]
                target += day_target
                actual += day_actual
                days += 1
            cursor += timedelta(days=1)
        utilization = int((actual / target) * 100) if target else 0
        if utilization < settings_obj.under_planned_threshold_percent:
            band = "under"
        elif utilization <= settings_obj.target_utilization_percent:
            band = "target"
        elif utilization <= settings_obj.max_utilization_percent:
            band = "high"
        else:
            band = "over"
        buckets[band] += 1
        person_stats = task_stats.get(person.id, {})
        samples = variance_by_user.get(person.id, [])
        avg_variance = sum(samples) / len(samples) if samples else 0
        rows.append(
            {
                "user": serialize_user_brief(person),
                "effectiveDays": days,
                "plannedMinutes": planned,
                "targetMinutes": target,
                "actualMinutes": actual,
                "utilizationPercent": utilization,
                "band": band,
                "bandLabel": {
                    "under": "کمتر از ظرفیت هدف",
                    "target": "در محدوده هدف",
                    "high": "بار کاری بالا",
                    "over": "بیش از ظرفیت",
                }[band],
                "completedCount": person_stats.get("completedCount", 0),
                "pendingCount": person_stats.get("pendingCount", 0),
                "overdueCount": person_stats.get("overdueCount", 0),
                "reworkCount": person_stats.get("reworkCount", 0),
                "estimateAccuracyVariance": round(avg_variance, 3),
                "days": day_rows,
            }
        )

    return {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "kpi": {
            "activeUsers": len(rows),
            "targetMetUsers": buckets["target"],
            "underTargetUsers": buckets["under"],
            "highLoadUsers": buckets["high"],
            "overloadedUsers": buckets["over"],
            "completionRate": 0,
            "overdueTasks": Task.objects.filter(organization=organization, due_at__lt=timezone.now(), deleted_at__isnull=True)
            .exclude(status__in=[TaskStatus.COMPLETED, TaskStatus.CANCELLED])
            .count(),
            "pendingReviews": Task.objects.filter(organization=organization, status=TaskStatus.PENDING_REVIEW, deleted_at__isnull=True).count(),
        },
        "distribution": buckets,
        "users": rows,
    }
