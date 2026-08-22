from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time as dt_time, timedelta
from typing import Iterable

from django.db.models import Count, Sum
from django.utils import timezone

from workflow.models import (
    LeaveRequest,
    OrganizationPreference,
    RequestStatus,
    Task,
    TaskAllocation,
    TaskStatus,
    TaskTimeEntry,
)
from workflow.tasking import (
    TaskingSettings,
    day_length_minutes,
    org_timezone,
    scheduled_work_minutes,
)


class CapacityBatchContext:
    """Preloads allocations, timer entries, and leave minutes for many users/days."""

    def __init__(
        self,
        *,
        settings_obj: TaskingSettings,
        user_ids: Iterable[int],
        start: date,
        end: date,
        preference: OrganizationPreference | None = None,
    ) -> None:
        self.settings_obj = settings_obj
        self.start = start
        self.end = end
        self.tz = org_timezone(settings_obj)
        self.preference = preference
        if preference is None:
            self.preference = OrganizationPreference.objects.filter(organization=settings_obj.organization).first()

        user_id_list = list({int(item) for item in user_ids})
        self.planned_by_user_date: dict[tuple[int, date], int] = defaultdict(int)
        if user_id_list:
            excluded_statuses = [TaskStatus.CANCELLED, TaskStatus.PENDING_ACCEPTANCE, TaskStatus.DRAFT]
            allocation_rows = (
                TaskAllocation.objects.filter(
                    user_id__in=user_id_list,
                    work_date__gte=start,
                    work_date__lte=end,
                )
                .exclude(task__status__in=excluded_statuses)
                .values("user_id", "work_date")
                .annotate(total=Sum("planned_minutes"))
            )
            for row in allocation_rows:
                self.planned_by_user_date[(int(row["user_id"]), row["work_date"])] = int(row["total"] or 0)

        self.closed_seconds_by_user_date: dict[tuple[int, date], int] = defaultdict(int)
        self.active_by_user: dict[int, TaskTimeEntry] = {}
        if user_id_list:
            range_start = datetime.combine(start, dt_time.min, tzinfo=self.tz)
            range_end = datetime.combine(end, dt_time.max, tzinfo=self.tz)
            closed_entries = TaskTimeEntry.objects.filter(
                user_id__in=user_id_list,
                is_active=False,
                started_at__gte=range_start,
                started_at__lte=range_end,
            ).only("user_id", "duration_seconds", "started_at", "ended_at")
            for entry in closed_entries:
                if not entry.started_at:
                    continue
                local_date = entry.started_at.astimezone(self.tz).date()
                seconds = int(entry.duration_seconds or 0)
                if seconds <= 0 and entry.ended_at:
                    seconds = max(0, int((entry.ended_at - entry.started_at).total_seconds()))
                self.closed_seconds_by_user_date[(int(entry.user_id), local_date)] += seconds

            active_entries = TaskTimeEntry.objects.filter(user_id__in=user_id_list, is_active=True).only(
                "user_id", "started_at"
            )
            for entry in active_entries:
                self.active_by_user[int(entry.user_id)] = entry

        self.leave_minutes_by_user_date: dict[tuple[int, date], int] = defaultdict(int)
        if user_id_list:
            range_start = timezone.make_aware(datetime.combine(start, dt_time.min))
            range_end = timezone.make_aware(datetime.combine(end, dt_time.max))
            leaves = list(
                LeaveRequest.objects.filter(
                    request__requester_id__in=user_id_list,
                    status=RequestStatus.APPROVED,
                    starts_at__lt=range_end,
                    ends_at__gt=range_start,
                )
                .select_related("request")
                .only("starts_at", "ends_at", "request__requester_id")
            )
            cursor = start
            while cursor <= end:
                day_start = timezone.make_aware(datetime.combine(cursor, dt_time.min))
                day_end = timezone.make_aware(datetime.combine(cursor, dt_time.max))
                for leave in leaves:
                    overlap_start = max(leave.starts_at, day_start)
                    overlap_end = min(leave.ends_at, day_end)
                    if overlap_end <= overlap_start:
                        continue
                    requester_id = leave.request.requester_id if leave.request_id else None
                    if requester_id:
                        minutes = int((overlap_end - overlap_start).total_seconds() // 60)
                        self.leave_minutes_by_user_date[(int(requester_id), cursor)] += minutes
                cursor += timedelta(days=1)

    def effective_work_minutes(self, user_id: int, work_date: date) -> int:
        scheduled = scheduled_work_minutes(self.settings_obj, work_date, self.preference)
        leave = self.leave_minutes_by_user_date.get((user_id, work_date), 0)
        return max(0, scheduled - leave)

    def planned_minutes(self, user_id: int, work_date: date) -> int:
        return self.planned_by_user_date.get((user_id, work_date), 0)

    def actual_minutes(self, user_id: int, work_date: date) -> int:
        closed_seconds = self.closed_seconds_by_user_date.get((user_id, work_date), 0)
        active_seconds = 0
        active = self.active_by_user.get(user_id)
        if active is not None and active.started_at:
            local_started = active.started_at.astimezone(self.tz).date()
            if local_started == work_date:
                active_seconds = max(0, int((timezone.now() - active.started_at).total_seconds()))
        return max(0, int((closed_seconds + active_seconds) // 60))

    def capacity_metrics(self, user_id: int, work_date: date) -> dict[str, int]:
        effective = self.effective_work_minutes(user_id, work_date)
        if effective <= 0:
            effective = day_length_minutes(self.settings_obj, work_date, self.preference)
        target = int(effective * self.settings_obj.target_utilization_percent / 100) if effective else 0
        planned = self.planned_minutes(user_id, work_date)
        actual = self.actual_minutes(user_id, work_date)
        return {
            "effectiveWorkMinutes": effective,
            "targetMinutes": target,
            "plannedMinutes": planned,
            "actualMinutes": actual,
        }


def batch_task_stats(
    organization_id: int,
    user_ids: Iterable[int],
    *,
    start: date,
    end: date,
) -> dict[int, dict[str, int]]:
    """Aggregate task counters per owner in a small number of queries."""
    user_id_list = list({int(item) for item in user_ids})
    stats = {
        uid: {
            "completedCount": 0,
            "pendingCount": 0,
            "overdueCount": 0,
            "reworkCount": 0,
        }
        for uid in user_id_list
    }
    if not user_id_list:
        return stats

    base_qs = Task.objects.filter(organization_id=organization_id, owner_id__in=user_id_list, deleted_at__isnull=True)
    now_value = timezone.now()
    pending_statuses = [TaskStatus.SCHEDULED, TaskStatus.UPCOMING, TaskStatus.IN_PROGRESS, TaskStatus.PAUSED]
    terminal_statuses = [TaskStatus.COMPLETED, TaskStatus.CANCELLED]

    for row in (
        base_qs.filter(status=TaskStatus.COMPLETED, completed_at__date__gte=start, completed_at__date__lte=end)
        .values("owner_id")
        .annotate(total=Count("id"))
    ):
        stats[int(row["owner_id"])]["completedCount"] = int(row["total"])

    for row in base_qs.filter(status__in=pending_statuses).values("owner_id").annotate(total=Count("id")):
        stats[int(row["owner_id"])]["pendingCount"] = int(row["total"])

    for row in (
        base_qs.filter(due_at__lt=now_value)
        .exclude(status__in=terminal_statuses)
        .values("owner_id")
        .annotate(total=Count("id"))
    ):
        stats[int(row["owner_id"])]["overdueCount"] = int(row["total"])

    for row in base_qs.filter(review_iteration__gt=1).values("owner_id").annotate(total=Count("id")):
        stats[int(row["owner_id"])]["reworkCount"] = int(row["total"])

    return stats
