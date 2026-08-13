from datetime import timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from workflow.models import PlatformRole, SupportTicket, SupportTicketStatus, User

SUPPORT_TICKET_AUTO_CLOSE_AFTER_DAYS = 3


def default_hq_support_user():
    return (
        User.objects.filter(platform_role=PlatformRole.HQ_SUPPORT, is_active=True, is_deleted=False)
        .order_by("-id")
        .first()
    ) or (
        User.objects.filter(platform_role=PlatformRole.HQ_ADMIN, is_active=True, is_deleted=False)
        .order_by("-id")
        .first()
    )


def close_stale_support_tickets(*, now=None):
    """Close tickets idle 3+ days while waiting for organization response."""
    current = now or timezone.now()
    cutoff = current - timedelta(days=SUPPORT_TICKET_AUTO_CLOSE_AFTER_DAYS)
    # Waiting for the organization (= answered by HQ / awaiting tenant reply)
    queryset = SupportTicket.objects.filter(status=SupportTicketStatus.ANSWERED).filter(
        Q(last_message_at__lte=cutoff) | Q(last_message_at__isnull=True, created_at__lte=cutoff)
    )
    return queryset.update(
        status=SupportTicketStatus.CLOSED,
        closed_at=current,
        updated_at=current,
    )


def response_status_score(status_value):
    return {
        SupportTicketStatus.CLOSED: Decimal("5.0"),
        SupportTicketStatus.ANSWERED: Decimal("4.4"),
        SupportTicketStatus.PENDING: Decimal("3.6"),
        SupportTicketStatus.OPEN: Decimal("3.0"),
    }.get(status_value, Decimal("3.0"))


def response_length_score(body):
    size = len(str(body or "").strip())
    if size >= 280:
        return Decimal("5.0")
    if size >= 160:
        return Decimal("4.6")
    if size >= 80:
        return Decimal("4.2")
    if size >= 40:
        return Decimal("3.7")
    return Decimal("2.8")


def response_quality_score(ticket, body):
    status_score = response_status_score(ticket.status)
    length_score = response_length_score(body)
    return ((status_score * Decimal("0.65")) + (length_score * Decimal("0.35"))).quantize(Decimal("0.01"))


def response_speed_score(first_response_minutes):
    minutes = float(first_response_minutes or 0)
    if minutes <= 10:
        return Decimal("5.0")
    if minutes <= 30:
        return Decimal("4.7")
    if minutes <= 60:
        return Decimal("4.2")
    if minutes <= 180:
        return Decimal("3.6")
    if minutes <= 720:
        return Decimal("3.0")
    if minutes <= 1440:
        return Decimal("2.4")
    return Decimal("1.8")


def average_decimal(values):
    if not values:
        return Decimal("0")
    total = sum((Decimal(str(value)) for value in values), Decimal("0"))
    return (total / Decimal(str(len(values)))).quantize(Decimal("0.01"))


def recalculate_support_metrics(user):
    if not user or user.platform_role not in {PlatformRole.HQ_ADMIN, PlatformRole.HQ_SUPPORT}:
        return

    tickets = list(
        SupportTicket.objects.filter(assigned_to=user, responded_at__isnull=False).only(
            "id",
            "status",
            "created_at",
            "first_response_at",
            "response_quality_score",
            "customer_satisfaction",
        )
    )
    satisfaction_values = [ticket.customer_satisfaction for ticket in tickets if ticket.customer_satisfaction]
    quality_values = [ticket.response_quality_score for ticket in tickets if Decimal(str(ticket.response_quality_score or 0)) > 0]
    response_minutes = []
    response_speed_values = []
    resolved_count = 0

    for ticket in tickets:
        if ticket.status == SupportTicketStatus.CLOSED:
            resolved_count += 1
        if ticket.first_response_at and ticket.created_at:
            minutes = max((ticket.first_response_at - ticket.created_at).total_seconds() / 60, 0)
            response_minutes.append(Decimal(str(round(minutes, 2))))
            response_speed_values.append(response_speed_score(minutes))

    satisfaction_avg = average_decimal(satisfaction_values)
    quality_avg = average_decimal(quality_values)
    first_response_minutes_avg = average_decimal(response_minutes)
    speed_avg = average_decimal(response_speed_values)

    weighted_parts = []
    if satisfaction_values:
        weighted_parts.append((satisfaction_avg, Decimal("0.55")))
    if quality_values:
        weighted_parts.append((quality_avg, Decimal("0.30")))
    if response_speed_values:
        weighted_parts.append((speed_avg, Decimal("0.15")))

    if weighted_parts:
        total_weight = sum((weight for _, weight in weighted_parts), Decimal("0"))
        star_rating = (sum((value * weight for value, weight in weighted_parts), Decimal("0")) / total_weight).quantize(Decimal("0.01"))
    else:
        star_rating = Decimal("0")

    user.support_star_rating = star_rating
    user.support_rating_count = len(satisfaction_values)
    user.support_customer_satisfaction_avg = satisfaction_avg
    user.support_response_quality_avg = quality_avg
    user.support_first_response_minutes_avg = first_response_minutes_avg
    user.support_total_responses = len(tickets)
    user.support_resolved_tickets_count = resolved_count
    user.support_last_scored_at = timezone.now()
    user.save(
        update_fields=[
            "support_star_rating",
            "support_rating_count",
            "support_customer_satisfaction_avg",
            "support_response_quality_avg",
            "support_first_response_minutes_avg",
            "support_total_responses",
            "support_resolved_tickets_count",
            "support_last_scored_at",
        ]
    )


HQ_CONTROL_SLUG = "milad_dhs"


def is_hq_user(user) -> bool:
    if not user:
        return False
    role = getattr(user, "platform_role", "") or ""
    if role in {PlatformRole.HQ_ADMIN, PlatformRole.HQ_SUPPORT}:
        return True
    return getattr(user, "slug", "") == HQ_CONTROL_SLUG


def is_hq_admin(user) -> bool:
    if not user:
        return False
    if getattr(user, "platform_role", "") == PlatformRole.HQ_ADMIN:
        return True
    return getattr(user, "slug", "") == HQ_CONTROL_SLUG
