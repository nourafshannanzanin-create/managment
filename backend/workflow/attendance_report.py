from __future__ import annotations

from datetime import date, datetime, time, timedelta

from django.utils import timezone

from workflow.models import AttendanceEvent, LeaveRequest, OrganizationPreference, RequestStatus, User

PERSIAN_WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]


def _div(a: int, b: int) -> int:
    return a // b


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    gdm = [0, 31, 29 if (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = 365 * gy + _div(gy2 + 3, 4) - _div(gy2 + 99, 100) + _div(gy2 + 399, 400) - 80 + gd
    for i in range(gm):
        days += gdm[i]
    jy += 33 * _div(days, 12053)
    days %= 12053
    jy += 4 * _div(days, 1461)
    days %= 1461
    if days > 365:
        jy += _div(days - 1, 365)
        days = (days - 1) % 365
    jm = 1 + _div(days, 31) if days < 186 else 7 + _div(days - 186, 30)
    jd = 1 + (days % 31 if days < 186 else (days - 186) % 30)
    return jy, jm, jd


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> tuple[int, int, int]:
    if jy > 979:
        gy = 1600
        jy -= 979
    else:
        gy = 621
    days = 365 * jy + _div(jy, 33) * 8 + _div((jy % 33) + 3, 4) + 78 + jd + ((jm - 1) * 31 if jm < 7 else (jm - 7) * 30 + 186)
    gy += 400 * _div(days, 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * _div(days, 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * _div(days, 1461)
    days %= 1461
    if days > 365:
        gy += _div(days - 1, 365)
        days = (days - 1) % 365
    gd = days + 1
    sal_a = [0, 31, 29 if (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 1
    while gm <= 12 and gd > sal_a[gm]:
        gd -= sal_a[gm]
        gm += 1
    return gy, gm, gd


def is_jalali_leap_year(jy: int) -> bool:
    gy, gm, gd = jalali_to_gregorian(jy + 1, 1, 1)
    last = date(gy, gm, gd) - timedelta(days=1)
    _, _, jd = gregorian_to_jalali(last.year, last.month, last.day)
    return jd == 30


def jalali_month_length(jy: int, jm: int) -> int:
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if is_jalali_leap_year(jy) else 29


def jalali_month_bounds(jy: int, jm: int) -> tuple[date, date]:
    gy1, gm1, gd1 = jalali_to_gregorian(jy, jm, 1)
    last_day = jalali_month_length(jy, jm)
    gy2, gm2, gd2 = jalali_to_gregorian(jy, jm, last_day)
    return date(gy1, gm1, gd1), date(gy2, gm2, gd2)


def format_jalali_display(day: date) -> str:
    jy, jm, jd = gregorian_to_jalali(day.year, day.month, day.day)
    return f"{jd:02d} / {jm:02d} / {jy}"


def persian_weekday(day: date) -> str:
    # Python weekday: Mon=0 ... Sun=6 → Persian week starts Saturday
    return PERSIAN_WEEKDAYS[(day.weekday() + 2) % 7]


def _as_local(dt: datetime) -> datetime:
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return timezone.localtime(dt)


def scheduled_hours_per_day(preference: OrganizationPreference) -> float:
    start = preference.work_day_start_time or time(9, 0)
    end = preference.work_day_end_time or time(17, 0)
    start_dt = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return max(0.0, (end_dt - start_dt).total_seconds() / 3600.0)


def compute_pairs_worked_hours(events: list[AttendanceEvent], day: date) -> tuple[float, list[dict], bool]:
    day_events = sorted(
        [item for item in events if _as_local(item.event_at).date() == day],
        key=lambda item: item.event_at,
    )
    punches = []
    total_seconds = 0.0
    open_in = None
    open_now = False
    now = timezone.localtime()
    for event in day_events:
        local_at = _as_local(event.event_at)
        punches.append(
            {
                "id": event.id,
                "type": event.event_type,
                "at": local_at.isoformat(),
                "time": local_at.strftime("%H:%M"),
                "note": event.note or "",
            }
        )
        if event.event_type == AttendanceEvent.EVENT_IN:
            open_in = local_at
        elif event.event_type == AttendanceEvent.EVENT_OUT and open_in is not None:
            total_seconds += max(0.0, (local_at - open_in).total_seconds())
            open_in = None
    if open_in is not None and day == now.date():
        total_seconds += max(0.0, (now - open_in).total_seconds())
        open_now = True
    return round(total_seconds / 3600.0, 2), punches, open_now


def leave_hours_for_day(leaves: list[LeaveRequest], day: date, scheduled: float = 8.0) -> float:
    total = 0.0
    day_start = timezone.make_aware(datetime.combine(day, time.min))
    day_end = timezone.make_aware(datetime.combine(day, time.max))
    for leave in leaves:
        start = _as_local(leave.starts_at)
        end = _as_local(leave.ends_at)
        if end.date() < day or start.date() > day:
            continue
        if leave.mode == LeaveRequest.MODE_DAILY:
            span_days = max(1, (end.date() - start.date()).days + 1)
            per_day = float(leave.hours or 0) / span_days if leave.hours else scheduled
            total += per_day
            continue
        overlap_start = max(start, day_start)
        overlap_end = min(end, day_end)
        if overlap_end > overlap_start:
            total += (overlap_end - overlap_start).total_seconds() / 3600.0
    return round(total, 2)


def build_monthly_attendance_report(
    *,
    organization,
    user: User,
    year: int | None = None,
    month: int | None = None,
    jalali_year: int | None = None,
    jalali_month: int | None = None,
) -> dict:
    preference, _ = OrganizationPreference.objects.get_or_create(organization=organization)
    scheduled = scheduled_hours_per_day(preference)
    leave_quota = float(preference.monthly_leave_hours or 20)

    calendar_kind = "jalali"
    if jalali_year is not None and jalali_month is not None:
        jy = int(jalali_year)
        jm = int(jalali_month)
        month_start, month_end = jalali_month_bounds(jy, jm)
        label_year, label_month = jy, jm
    else:
        calendar_kind = "gregorian"
        gy = int(year)
        gm = int(month)
        month_start = date(gy, gm, 1)
        if gm == 12:
            month_end = date(gy + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(gy, gm + 1, 1) - timedelta(days=1)
        label_year, label_month = gy, gm
        jy, jm, _ = gregorian_to_jalali(month_start.year, month_start.month, month_start.day)

    range_start = timezone.make_aware(datetime.combine(month_start, time.min))
    range_end = timezone.make_aware(datetime.combine(month_end, time.max))

    events = list(
        AttendanceEvent.objects.filter(
            organization=organization,
            user=user,
            event_at__gte=range_start,
            event_at__lte=range_end,
        ).order_by("event_at")
    )
    leaves = list(
        LeaveRequest.objects.filter(
            request__requester=user,
            status=RequestStatus.APPROVED,
            starts_at__lte=range_end,
            ends_at__gte=range_start,
        ).select_related("request")
    )

    days = []
    total_worked = 0.0
    total_overtime = 0.0
    total_shortage = 0.0
    total_leave = 0.0

    today = timezone.localdate()
    cursor = month_start
    while cursor <= month_end:
        if cursor > today:
            break
        worked, punches, open_now = compute_pairs_worked_hours(events, cursor)
        leave_hours = leave_hours_for_day(leaves, cursor, scheduled)
        effective = worked + leave_hours
        overtime = max(0.0, round(worked - scheduled, 2)) if scheduled else 0.0
        shortage = max(0.0, round(scheduled - effective, 2)) if scheduled else 0.0
        total_worked += worked
        total_overtime += overtime
        total_shortage += shortage
        total_leave += leave_hours
        jy_day, jm_day, jd_day = gregorian_to_jalali(cursor.year, cursor.month, cursor.day)
        days.append(
            {
                "date": cursor.isoformat(),
                "day": jd_day,
                "jalaliDate": format_jalali_display(cursor),
                "jalaliYear": jy_day,
                "jalaliMonth": jm_day,
                "jalaliDay": jd_day,
                "weekday": persian_weekday(cursor),
                "punches": punches,
                "workedHours": worked,
                "leaveHours": leave_hours,
                "scheduledHours": scheduled,
                "overtimeHours": overtime,
                "shortageHours": shortage,
                "openShift": open_now,
            }
        )
        cursor += timedelta(days=1)

    unpaid_leave = max(0.0, round(total_leave - leave_quota, 2))
    paid_leave = round(min(total_leave, leave_quota), 2)
    return {
        "userId": user.id,
        "userName": user.full_name,
        "year": label_year,
        "month": label_month,
        "jalaliYear": jy,
        "jalaliMonth": jm,
        "calendar": calendar_kind,
        "startDate": month_start.isoformat(),
        "endDate": month_end.isoformat(),
        "workDayStart": (preference.work_day_start_time or time(9, 0)).strftime("%H:%M"),
        "workDayEnd": (preference.work_day_end_time or time(17, 0)).strftime("%H:%M"),
        "scheduledHoursPerDay": scheduled,
        "monthlyLeaveQuota": leave_quota,
        "summary": {
            "workedHours": round(total_worked, 2),
            "overtimeHours": round(total_overtime, 2),
            "shortageHours": round(total_shortage, 2),
            "leaveHours": round(total_leave, 2),
            "paidLeaveHours": paid_leave,
            "unpaidLeaveHours": unpaid_leave,
            "leaveRemaining": round(max(0.0, leave_quota - total_leave), 2),
            "daysCount": len(days),
        },
        "days": days,
    }
