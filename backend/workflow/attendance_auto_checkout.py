from __future__ import annotations

from datetime import datetime, time, timedelta

from django.utils import timezone

from workflow.models import AttendanceEvent, FeaturePurchase, Organization, OrganizationPreference, TaskTimeEntry, User


def organization_has_attendance(organization: Organization) -> bool:
    return FeaturePurchase.objects.filter(organization=organization, feature_key="attendance", is_active=True).exists()


def auto_checkout_open_shifts(*, target_date=None, organization: Organization | None = None) -> int:
    """Close open attendance shifts at end-of-work time for a given day."""
    now = timezone.localtime()
    if target_date is None:
        target_date = (now - timedelta(days=1)).date()

    org_qs = Organization.objects.all()
    if organization is not None:
        org_qs = org_qs.filter(pk=organization.pk)

    created = 0
    for org in org_qs:
        if not organization_has_attendance(org):
            continue
        preference, _ = OrganizationPreference.objects.get_or_create(organization=org)
        work_end = preference.work_day_end_time or time(17, 0)
        checkout_at = timezone.make_aware(datetime.combine(target_date, work_end))
        day_start = timezone.make_aware(datetime.combine(target_date, time.min))
        day_end = timezone.make_aware(datetime.combine(target_date, time.max))

        user_ids = (
            AttendanceEvent.objects.filter(organization=org, event_at__gte=day_start, event_at__lte=day_end)
            .values_list("user_id", flat=True)
            .distinct()
        )
        users = User.objects.filter(pk__in=user_ids, is_active=True, is_deleted=False)

        for user in users:
            events = list(
                AttendanceEvent.objects.filter(
                    organization=org,
                    user=user,
                    event_at__gte=day_start,
                    event_at__lte=day_end,
                ).order_by("event_at", "id")
            )
            if not events or events[-1].event_type != AttendanceEvent.EVENT_IN:
                continue
            if TaskTimeEntry.objects.filter(user=user, is_active=True).exists():
                continue
            AttendanceEvent.objects.create(
                organization=org,
                user=user,
                event_type=AttendanceEvent.EVENT_OUT,
                source=AttendanceEvent.SOURCE_MANAGER,
                note="خروج خودکار — پایان شیفت کاری",
                event_at=checkout_at,
            )
            created += 1
    return created
