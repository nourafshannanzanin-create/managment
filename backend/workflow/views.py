from __future__ import annotations

import json
import mimetypes
import os
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import connection, transaction
from django.db.utils import OperationalError, ProgrammingError
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from workflow.access import (
    attach_user,
    can_access_approvals,
    can_access_expenses,
    can_access_settings,
    can_access_users,
    can_approve_documents,
    can_manage_users,
    can_view_reports,
    ensure_user_memberships,
    get_user_organization,
    is_manager,
    require_roles,
    visible_users,
)
from workflow.document_signing import sign_document_file
from workflow.models import (
    ApprovalAssignment,
    ApprovalAssignmentStatus,
    AuditLog,
    ConfidentialityLevel,
    Department,
    Document,
    DocumentRisk,
    DocumentStatus,
    Expense,
    ExpenseCategory,
    ExpenseStatus,
    OrganizationMembership,
    OrganizationPreference,
    Request,
    RequestPriority,
    RequestStatus,
    RequestTimeline,
    SectionAccessGrant,
    SupportAttachment,
    SupportMessage,
    SupportTicket,
    SupportTicketCategory,
    SupportTicketPriority,
    SupportTicketStatus,
    User,
    UserRole,
    UserSignature,
    Wallet,
    WalletTransaction,
    Organization,
)
from workflow.security import create_access_token, decode_token, get_password_hash, verify_password
from workflow.seed import seed_demo_data
from workflow.services import (
    approval_metrics,
    build_bootstrap_payload,
    build_hq_payload,
    format_money,
    HQ_USERNAME,
    next_code,
    render_report_export,
    save_uploaded_file,
    serialize_approval,
    serialize_current_user,
    serialize_expense,
    serialize_request,
    serialize_support_ticket,
    serialize_user,
    wallet_dashboard_payload,
    update_document_status,
    visible_approvals,
    visible_expenses,
    visible_reports_payload,
    visible_requests,
)

JSON_KWARGS = {"ensure_ascii": False}
DEFAULT_SIGNATURE_DATA = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="


def has_saved_signature(signature_data: str | None) -> bool:
    normalized = (signature_data or "").strip()
    return bool(normalized) and normalized != DEFAULT_SIGNATURE_DATA


def json_response(payload, status=200, safe=True):
    return JsonResponse(payload, status=status, safe=safe, json_dumps_params=JSON_KWARGS)


def json_error(detail: str, status=400):
    return json_response({"detail": detail}, status=status)


def parse_json(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


USER_SECTION_KEYS = ("reports", "users", "settings")


def section_access_payload(payload: dict) -> dict[str, bool]:
    access = payload.get("sectionAccess") or {}
    return {key: bool(access.get(key)) for key in USER_SECTION_KEYS}


def sync_user_section_access(actor: User, user: User, access_map: dict[str, bool]) -> None:
    organization = get_user_organization(actor)
    for section_key, allowed in access_map.items():
        SectionAccessGrant.objects.filter(
            organization=organization,
            section_key=section_key,
            user=user,
        ).delete()
        if allowed and user.id != actor.id:
            SectionAccessGrant.objects.create(
                organization=organization,
                section_key=section_key,
                user=user,
            )


USER_SECTION_KEYS = ("reports", "users", "settings")


def section_access_payload(payload: dict) -> dict[str, bool]:
    access = payload.get("sectionAccess") or {}
    return {key: bool(access.get(key)) for key in USER_SECTION_KEYS}


def sync_user_section_access(actor: User, user: User, access_map: dict[str, bool]) -> None:
    organization = get_user_organization(actor)
    for section_key, allowed in access_map.items():
        SectionAccessGrant.objects.filter(
            organization=organization,
            section_key=section_key,
            user=user,
        ).delete()
        if allowed and user.id != actor.id:
            SectionAccessGrant.objects.create(
                organization=organization,
                section_key=section_key,
                user=user,
            )


def build_settings_profile_payload(user: User, organization_id: int | None = None) -> dict:
    organization = None
    if user.slug == HQ_USERNAME and organization_id:
        organization = Organization.objects.exclude(code="hq-control").filter(pk=organization_id).first()
    if organization is None:
        organization = get_user_organization(user)
    preference, _ = OrganizationPreference.objects.get_or_create(organization=organization)
    if user.slug == HQ_USERNAME and organization_id:
        organization_users_qs = User.objects.filter(organization_membership__organization=organization).select_related("department", "manager").order_by("full_name")
    else:
        organization_users_qs = visible_users(user).select_related("department", "manager").order_by("full_name")
    recent_logins = list(
        AuditLog.objects.filter(actor_id__in=organization_users_qs.values_list("id", flat=True), action="login").order_by("-created_at")[:3]
    )
    recent_session_label = "بدون نشست اخیر"
    if recent_logins:
        recent_session_label = f"{len(recent_logins)} دستگاه فعال شناسایی شد"

    sections = [
        {"key": "users", "title": "حساب کاربری", "description": "مدیریت نقش ها و دسترسی", "route": "/users"},
        {"key": "approvals", "title": "اسناد", "description": "گردش کار امضای دیجیتال", "route": "/approvals"},
        {"key": "expenses", "title": "هزینه ها", "description": "ثبت، پیگیری و کنترل هزینه", "route": "/expenses"},
        {"key": "reports", "title": "گزارشات", "description": "نمای مدیریتی و تحلیل عملکرد", "route": "/reports"},
        {"key": "settings", "title": "تنظیمات", "description": "مدیریت پروفایل سازمان و دسترسی‌ها", "route": "/settings"},
    ]
    section_payload = []
    for section in sections:
        grants = SectionAccessGrant.objects.filter(organization=organization, section_key=section["key"]).select_related("user", "user__department")
        allowed_users = [
            {
                "id": grant.user.id,
                "name": grant.user.full_name,
                "role": grant.user.job_title,
                "department": grant.user.department.name if grant.user.department else "بدون واحد",
            }
            for grant in grants
        ]
        section_payload.append({**section, "allowedUserIds": [item["id"] for item in allowed_users], "allowedUsers": allowed_users})

    return {
        "organizationName": organization.name,
        "systemId": f"KARO-{str(user.id or 0).zfill(4)}",
        "security": {
            "twoFactorRequired": preference.two_factor_required,
            "recentSessionCount": len(recent_logins),
            "recentSessionLabel": recent_session_label,
        },
        "sections": section_payload,
        "organizationUsers": [
            {
                "id": item.id,
                "name": item.full_name,
                "role": item.job_title,
                "department": item.department.name if item.department else "بدون واحد",
            }
            for item in organization_users_qs
        ],
        "departments": [{"id": item.id, "code": item.code, "name": item.name} for item in Department.objects.order_by("name")],
        "canEdit": can_manage_users(user),
    }


def user_can_access_wallet(user: User) -> bool:
    return user.slug == HQ_USERNAME or user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER}


def resolve_wallet_organization(request: HttpRequest, payload: dict | None = None) -> Organization | None:
    payload = payload or {}
    raw_organization_id = request.GET.get("organizationId") or payload.get("organizationId")
    if request.current_user.slug == HQ_USERNAME:
        if not raw_organization_id:
            return None
        return Organization.objects.exclude(code="hq-control").filter(pk=raw_organization_id).first()
    return get_user_organization(request.current_user)


def parse_wallet_amount(value) -> Decimal | None:
    try:
        amount = Decimal(str(value).replace(",", "")).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return amount if amount > 0 else None


def support_ticket_wallet_id(ticket: SupportTicket) -> int | None:
    for line in (ticket.message or "").splitlines():
        if not line.startswith("WALLET_ID:"):
            continue
        raw_value = line.split(":", 1)[1].strip()
        if raw_value.isdigit():
            return int(raw_value)
    return None


def scoped_support_organization(request: HttpRequest) -> Organization | None:
    return resolve_wallet_organization(request)


def scoped_support_tickets(request: HttpRequest):
    organization = scoped_support_organization(request)
    if request.current_user.slug == HQ_USERNAME and organization is None:
        return (
            SupportTicket.objects.all()
            .select_related("organization", "requester", "responded_by")
            .prefetch_related("messages", "attachments")
            .order_by("-updated_at", "-id")
        )
    if organization is None:
        return SupportTicket.objects.none()
    return (
        SupportTicket.objects.filter(organization=organization)
        .select_related("organization", "requester", "responded_by")
        .prefetch_related("messages", "attachments")
        .order_by("-updated_at", "-id")
    )


def ensure_signature(user: User) -> UserSignature:
    signature, _ = UserSignature.objects.get_or_create(
        user=user,
        defaults={"signature_data": ""},
    )
    if signature.signature_data == DEFAULT_SIGNATURE_DATA:
        signature.signature_data = ""
        signature.updated_at = timezone.now()
        signature.save(update_fields=["signature_data", "updated_at"])
    return signature


def env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def workflow_tables_exist() -> bool:
    try:
        tables = set(connection.introspection.table_names())
    except (OperationalError, ProgrammingError):
        return False
    return {"users", "departments", "organizations", "organization_memberships"}.issubset(tables)


def ensure_hq_control_user() -> None:
    department, _ = Department.objects.get_or_create(code="hq-control", defaults={"name": "HQ"})
    organization, _ = Organization.objects.get_or_create(code="hq-control", defaults={"name": "HQ"})
    user, created = User.objects.get_or_create(
        slug=HQ_USERNAME,
        defaults={
            "full_name": "Milad DHS",
            "email": "milad_dhs@hq.local",
            "phone": "",
            "password_hash": get_password_hash("milad_dhs@123"),
            "role": UserRole.ADMIN,
            "job_title": "HQ",
            "avatar": "MD",
            "bio": "",
            "is_active": True,
            "department": department,
        },
    )
    update_fields = []
    if not created and not verify_password("milad_dhs@123", user.password_hash):
        user.password_hash = get_password_hash("milad_dhs@123")
        update_fields.append("password_hash")
    if user.role != UserRole.ADMIN:
        user.role = UserRole.ADMIN
        update_fields.append("role")
    if not user.is_active:
        user.is_active = True
        update_fields.append("is_active")
    if update_fields:
        user.save(update_fields=update_fields)
    OrganizationMembership.objects.update_or_create(user=user, defaults={"organization": organization, "display_title": "HQ"})


def require_auth(view_func):
    @wraps(view_func)
    def wrapped(request: HttpRequest, *args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return json_error("توکن نامعتبر است.", status=401)
        token = header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
            user_id = int(payload.get("sub"))
        except Exception:
            return json_error("توکن نامعتبر است.", status=401)
        user = User.objects.select_related("department", "manager").filter(pk=user_id, is_active=True).first()
        if user is None:
            return json_error("کاربر معتبر نیست.", status=401)
        attach_user(request, user)
        return view_func(request, *args, **kwargs)

    return wrapped


def methods(*allowed_methods):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request: HttpRequest, *args, **kwargs):
            if request.method not in allowed_methods:
                return HttpResponseNotAllowed(allowed_methods)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def startup_ready():
    if env_bool("WORKFLOW_AUTO_INIT_DB", True) and not workflow_tables_exist():
        call_command("migrate", interactive=False, verbosity=0)
    if not workflow_tables_exist():
        return
    if env_bool("WORKFLOW_AUTO_SEED_DB", True) and not User.objects.exists():
        seed_demo_data()
    ensure_user_memberships()
    ensure_hq_control_user()


@methods("GET")
def health_view(request: HttpRequest):
    del request
    return json_response({"status": "ok"})


@csrf_exempt
@methods("POST")
def login_view(request: HttpRequest):
    startup_ready()
    payload = parse_json(request)
    email = (payload.get("email") or payload.get("username") or "").strip().lower()
    password = payload.get("password") or ""
    user = User.objects.select_related("department").filter(email=email).first()
    if user is None:
        user = User.objects.select_related("department").filter(slug=email).first()
    if user is None or not verify_password(password, user.password_hash):
        return json_error("ایمیل یا رمز عبور نادرست است.", status=401)
    ensure_signature(user)
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])
    AuditLog.objects.create(actor=user, actor_name=user.full_name, action="login", entity_type="user", detail="ورود به سیستم", icon="login")
    token = create_access_token(str(user.id), {"role": user.role})
    return json_response({"access_token": token, "token_type": "bearer", "user": serialize_current_user(user)})


@require_auth
@methods("GET")
def me_view(request: HttpRequest):
    return json_response(serialize_current_user(request.current_user))


@require_auth
@methods("GET")
def bootstrap_view(request: HttpRequest):
    startup_ready()
    ensure_signature(request.current_user)
    organization_id = request.GET.get("organizationId")
    selected_organization_id = int(organization_id) if organization_id and organization_id.isdigit() else None
    return json_response(build_bootstrap_payload(request.current_user, selected_organization_id))


def ensure_hq_admin(user: User):
    if user.slug != HQ_USERNAME:
        return json_error("دسترسی HQ فقط برای حساب HQ فعال است.", status=403)
    return None


def hq_selected_user_ids(request: HttpRequest) -> list[int] | None:
    if request.current_user.slug != HQ_USERNAME:
        return None
    organization_id = request.GET.get("organizationId")
    if not organization_id or not organization_id.isdigit():
        return []
    organization = Organization.objects.exclude(code="hq-control").filter(pk=int(organization_id)).first()
    if organization is None:
        return []
    return list(User.objects.filter(organization_membership__organization=organization).values_list("id", flat=True))


def scoped_requests(request: HttpRequest):
    user_ids = hq_selected_user_ids(request)
    if user_ids is None:
        return visible_requests(request.current_user)
    return (
        Request.objects.filter(requester_id__in=user_ids)
        .select_related("requester", "manager", "department")
        .prefetch_related("assigned_managers", "attachments", "timeline_items")
        .order_by("-created_at")
    )


def scoped_expenses(request: HttpRequest):
    user_ids = hq_selected_user_ids(request)
    if user_ids is None:
        return visible_expenses(request.current_user)
    return Expense.objects.filter(owner_id__in=user_ids).select_related("owner", "department").order_by("-expense_date", "-created_at")


def scoped_documents(request: HttpRequest):
    user_ids = hq_selected_user_ids(request)
    if user_ids is None:
        return visible_approvals(request.current_user)
    return (
        Document.objects.filter(owner_id__in=user_ids)
        .select_related("owner", "department")
        .prefetch_related(
            "approval_assignments",
            "approval_assignments__approver",
        )
        .order_by("-uploaded_at")
    )


@require_auth
@methods("GET")
def hq_panel_view(request: HttpRequest):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied
    return json_response(build_hq_payload())


@require_auth
@methods("GET")
def wallet_view(request: HttpRequest):
    if not user_can_access_wallet(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)

    organization = resolve_wallet_organization(request)
    if request.current_user.slug == HQ_USERNAME and organization is None:
        return json_response(
            {
                "organization": None,
                "summary": {
                    "totalBalance": "0.00",
                    "totalBalanceRaw": 0,
                    "mainBalance": "0.00",
                    "mainBalanceRaw": 0,
                    "smsBalance": "0.00",
                    "smsBalanceRaw": 0,
                    "depositsTotal": "0.00",
                    "depositsTotalRaw": 0,
                    "withdrawalsTotal": "0.00",
                    "withdrawalsTotalRaw": 0,
                    "transactions": 0,
                },
                "wallets": [],
                "transactions": [],
            }
        )
    if organization is None:
        return json_error("مجموعه پیدا نشد.", status=404)
    return json_response(wallet_dashboard_payload(organization))


@require_auth
@methods("POST")
def wallet_transaction_view(request: HttpRequest):
    if not user_can_access_wallet(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)

    payload = parse_json(request)
    organization = resolve_wallet_organization(request, payload)
    if organization is None:
        return json_error("مجموعه پیدا نشد.", status=404)

    direction = str(payload.get("direction") or payload.get("type") or "").strip()
    if direction in {"deposit", "charge", "in"}:
        direction = "in"
        transaction_type = "deposit"
    elif direction in {"withdraw", "out"}:
        direction = "out"
        transaction_type = "withdraw"
    else:
        return json_error("نوع تراکنش معتبر نیست.", status=422)

    amount = parse_wallet_amount(payload.get("amount"))
    if amount is None:
        return json_error("مبلغ معتبر نیست.", status=422)

    wallet_id = payload.get("walletId")
    with transaction.atomic():
        wallet = (
            Wallet.objects.select_for_update()
            .filter(pk=wallet_id, organization=organization, is_active=True)
            .first()
        )
        if wallet is None:
            return json_error("کیف پول پیدا نشد.", status=404)

        current_balance = Decimal(wallet.balance)
        next_balance = current_balance + amount if direction == "in" else current_balance - amount
        if next_balance < 0:
            return json_error("موجودی کیف پول کافی نیست.", status=409)

        wallet.balance = next_balance
        wallet.updated_at = timezone.now()
        wallet.save(update_fields=["balance", "updated_at"])

        WalletTransaction.objects.create(
            organization=organization,
            wallet=wallet,
            actor=request.current_user,
            direction=direction,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=next_balance,
            note=str(payload.get("note") or "").strip(),
            reference_id=str(payload.get("referenceId") or "").strip(),
        )
        AuditLog.objects.create(
            actor=request.current_user,
            actor_name=request.current_user.full_name,
            action="wallet_transaction",
            entity_type="wallet",
            entity_code=wallet.key,
            detail=f"{transaction_type}:{format_money(amount)}:{organization.code}",
            icon="account_balance_wallet",
        )

    return json_response(wallet_dashboard_payload(organization), status=201)


@require_auth
@methods("GET", "POST")
def support_tickets_view(request: HttpRequest):
    organization = scoped_support_organization(request)
    if request.current_user.slug == HQ_USERNAME and organization is None:
        return json_response([], safe=False)
    if organization is None:
        return json_error("مجموعه پیدا نشد.", status=404)

    if request.method == "GET":
        tickets = scoped_support_tickets(request)
        return json_response([serialize_support_ticket(ticket) for ticket in tickets], safe=False)

    subject = (request.POST.get("subject") or "").strip()
    message = (request.POST.get("message") or "").strip()
    category = (request.POST.get("category") or SupportTicketCategory.TECHNICAL).strip()
    priority = (request.POST.get("priority") or SupportTicketPriority.MEDIUM).strip()
    if not subject or not message:
        return json_error("عنوان و متن تیکت الزامی است.", status=422)
    if category not in SupportTicketCategory.values:
        return json_error("دسته‌بندی معتبر نیست.", status=422)
    if priority not in SupportTicketPriority.values:
        return json_error("اولویت معتبر نیست.", status=422)

    with transaction.atomic():
        ticket = SupportTicket.objects.create(
            organization=organization,
            requester=request.current_user,
            subject=subject,
            message=message,
            category=category,
            priority=priority,
            status=SupportTicketStatus.OPEN,
            updated_at=timezone.now(),
        )
        SupportMessage.objects.create(
            ticket=ticket,
            sender=request.current_user,
            sender_name=request.current_user.full_name,
            sender_platform_role="hq_support" if request.current_user.slug == HQ_USERNAME else "tenant",
            body=message,
        )
        for attachment in request.FILES.getlist("attachments"):
            stored_name = save_uploaded_file(attachment)
            SupportAttachment.objects.create(
                ticket=ticket,
                original_name=attachment.name,
                stored_name=stored_name,
                mime_type=getattr(attachment, "content_type", "") or "",
                size_bytes=getattr(attachment, "size", 0) or 0,
            )
        AuditLog.objects.create(
            actor=request.current_user,
            actor_name=request.current_user.full_name,
            action="support_ticket_created",
            entity_type="support_ticket",
            entity_code=str(ticket.id),
            detail=f"{organization.code}:{subject}",
            icon="support_agent",
        )

    ticket = SupportTicket.objects.select_related("organization", "requester", "responded_by").prefetch_related("messages", "attachments").get(pk=ticket.id)
    return json_response(serialize_support_ticket(ticket, include_detail=True), status=201)


@require_auth
@methods("GET")
def support_ticket_detail_view(request: HttpRequest, ticket_id: int):
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)
    return json_response(serialize_support_ticket(ticket, include_detail=True))


@require_auth
@methods("POST")
def support_ticket_message_view(request: HttpRequest, ticket_id: int):
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)
    if ticket.status == SupportTicketStatus.CLOSED:
        return json_error("این تیکت بسته شده است.", status=409)

    payload = parse_json(request)
    body = (payload.get("body") or "").strip()
    close_ticket = bool(payload.get("close"))
    if not body and not close_ticket:
        return json_error("متن پیام الزامی است.", status=422)

    now_value = timezone.now()
    with transaction.atomic():
        if body:
            SupportMessage.objects.create(
                ticket=ticket,
                sender=request.current_user,
                sender_name=request.current_user.full_name,
                sender_platform_role="hq_support" if request.current_user.slug == HQ_USERNAME else "tenant",
                body=body,
            )
        if close_ticket:
            ticket.status = SupportTicketStatus.CLOSED
            ticket.closed_at = now_value
        elif request.current_user.slug == HQ_USERNAME:
            ticket.status = SupportTicketStatus.ANSWERED
            ticket.responded_by = request.current_user
            ticket.responded_at = now_value
            if ticket.first_response_at is None:
                ticket.first_response_at = now_value
        else:
            ticket.status = SupportTicketStatus.PENDING
        ticket.updated_at = now_value
        ticket.save(update_fields=["status", "responded_by", "responded_at", "first_response_at", "closed_at", "updated_at"])

    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    return json_response(serialize_support_ticket(ticket, include_detail=True))


@require_auth
@methods("POST")
def support_ticket_feedback_view(request: HttpRequest, ticket_id: int):
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)
    if ticket.status != SupportTicketStatus.CLOSED:
        return json_error("امتیازدهی فقط برای تیکت بسته شده فعال است.", status=409)

    payload = parse_json(request)
    try:
        score = int(payload.get("score"))
    except (TypeError, ValueError):
        score = 0
    if score < 1 or score > 5:
        return json_error("امتیاز معتبر نیست.", status=422)

    ticket.customer_satisfaction = score
    ticket.customer_feedback = (payload.get("feedback") or "").strip()
    ticket.updated_at = timezone.now()
    ticket.save(update_fields=["customer_satisfaction", "customer_feedback", "updated_at"])
    return json_response(serialize_support_ticket(ticket, include_detail=True))


@require_auth
@methods("POST")
def support_ticket_wallet_deposit_view(request: HttpRequest, ticket_id: int):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied

    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)
    if ticket.category != SupportTicketCategory.FINANCIAL:
        return json_error("این تیکت برای واریز کیف پول نیست.", status=409)

    wallet_id = support_ticket_wallet_id(ticket)
    if wallet_id is None:
        return json_error("شناسه کیف پول در تیکت ثبت نشده است.", status=422)

    payload = parse_json(request)
    amount = parse_wallet_amount(payload.get("amount"))
    if amount is None:
        return json_error("مبلغ معتبر نیست.", status=422)

    now_value = timezone.now()
    with transaction.atomic():
        wallet = (
            Wallet.objects.select_for_update()
            .filter(pk=wallet_id, organization=ticket.organization, is_active=True)
            .first()
        )
        if wallet is None:
            return json_error("کیف پول پیدا نشد.", status=404)

        next_balance = Decimal(wallet.balance) + amount
        wallet.balance = next_balance
        wallet.updated_at = now_value
        wallet.save(update_fields=["balance", "updated_at"])

        WalletTransaction.objects.create(
            organization=ticket.organization,
            wallet=wallet,
            actor=request.current_user,
            direction="in",
            transaction_type="support_ticket_deposit",
            amount=amount,
            balance_after=next_balance,
            note=f"support_ticket:{ticket.id}",
            reference_id=str(payload.get("referenceId") or ticket.id),
        )

        SupportMessage.objects.create(
            ticket=ticket,
            sender=request.current_user,
            sender_name=request.current_user.full_name,
            sender_platform_role="hq_support",
            body=f"واریز کیف پول انجام شد. مبلغ: {format_money(amount)}",
        )

        ticket.status = SupportTicketStatus.ANSWERED
        ticket.responded_by = request.current_user
        ticket.responded_at = now_value
        if ticket.first_response_at is None:
            ticket.first_response_at = now_value
        ticket.updated_at = now_value
        ticket.save(update_fields=["status", "responded_by", "responded_at", "first_response_at", "updated_at"])

        AuditLog.objects.create(
            actor=request.current_user,
            actor_name=request.current_user.full_name,
            action="support_ticket_wallet_deposit",
            entity_type="wallet",
            entity_code=wallet.key,
            detail=f"{ticket.organization.code}:{ticket.id}:{format_money(amount)}",
            icon="account_balance_wallet",
        )

    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    return json_response(serialize_support_ticket(ticket, include_detail=True))


def normalize_slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    normalized = "-".join(part for part in normalized.split("-") if part)
    return normalized[:80]


def build_unique_user_slug(base_value: str) -> str:
    base_slug = normalize_slug(base_value) or "user"
    slug = base_slug
    suffix = 2
    while User.objects.filter(slug=slug).exists():
        suffix_text = f"-{suffix}"
        slug = f"{base_slug[: max(1, 80 - len(suffix_text))]}{suffix_text}"
        suffix += 1
    return slug


@require_auth
@csrf_exempt
@methods("POST")
def hq_organization_create_view(request: HttpRequest):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied

    payload = parse_json(request)
    organization_name = (payload.get("organizationName") or "").strip()
    organization_code = normalize_slug(payload.get("organizationCode") or organization_name)
    manager_name = (payload.get("managerName") or "").strip()
    manager_username = normalize_slug(payload.get("managerUsername") or "")
    manager_email = (payload.get("managerEmail") or "").strip().lower()
    manager_password = payload.get("managerPassword") or ""
    manager_phone = (payload.get("managerPhone") or "").strip()

    if not organization_name:
        return json_error("نام مجموعه الزامی است.", status=422)
    if not organization_code:
        return json_error("کد مجموعه معتبر نیست.", status=422)
    if not manager_name or not manager_username or not manager_password:
        return json_error("نام مدیر، نام کاربری و رمز عبور الزامی است.", status=422)
    if len(manager_password) < 6:
        return json_error("رمز عبور باید حداقل ۶ کاراکتر باشد.", status=422)
    if not manager_email:
        manager_email = f"{manager_username}@{organization_code}.local"

    if Organization.objects.filter(code=organization_code).exists():
        return json_error("کد مجموعه قبلا ثبت شده است.", status=409)
    if Organization.objects.filter(name=organization_name).exists():
        return json_error("نام مجموعه قبلا ثبت شده است.", status=409)
    if User.objects.filter(slug=manager_username).exists():
        return json_error("نام کاربری مدیر قبلا ثبت شده است.", status=409)
    if User.objects.filter(email=manager_email).exists():
        return json_error("ایمیل مدیر قبلا ثبت شده است.", status=409)

    department, _ = Department.objects.get_or_create(
        code=f"{organization_code}-admin",
        defaults={"name": f"مدیریت {organization_name}"},
    )
    with transaction.atomic():
        organization = Organization.objects.create(code=organization_code, name=organization_name)
        manager = User.objects.create(
            slug=manager_username,
            full_name=manager_name,
            email=manager_email,
            phone=manager_phone or None,
            password_hash=get_password_hash(manager_password),
            role=UserRole.ADMIN,
            job_title="مدیر مجموعه",
            avatar=(manager_name[:2] if manager_name else "AD").upper(),
            bio="",
            is_active=True,
            department=department,
        )
        OrganizationMembership.objects.create(organization=organization, user=manager, display_title=manager.job_title)
        OrganizationPreference.objects.get_or_create(organization=organization)
        UserSignature.objects.get_or_create(user=manager, defaults={"signature_data": ""})
        AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="hq_organization_created", entity_type="organization", entity_code=organization.code, detail=organization.name, icon="domain_add")

    return json_response(build_hq_payload(), status=201)


@require_auth
@csrf_exempt
@methods("POST")
def hq_organization_update_view(request: HttpRequest, organization_id: int):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied
    organization = Organization.objects.filter(pk=organization_id).first()
    if organization is None:
        return json_error("سازمان پیدا نشد.", status=404)
    payload = parse_json(request)
    name = (payload.get("name") or "").strip()
    code = (payload.get("code") or "").strip()
    if name:
        organization.name = name
    if code:
        organization.code = code
    organization.save(update_fields=["name", "code"])
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="hq_organization_updated", entity_type="organization", entity_code=organization.code, detail=organization.name, icon="admin_panel_settings")
    return json_response(build_hq_payload())


@require_auth
@csrf_exempt
@methods("POST")
def hq_user_update_view(request: HttpRequest, user_id: int):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied
    target = User.objects.select_related("organization_membership").filter(pk=user_id).first()
    if target is None:
        return json_error("کاربر پیدا نشد.", status=404)
    payload = parse_json(request)
    if "name" in payload:
        target.full_name = (payload.get("name") or target.full_name).strip()
    if "email" in payload:
        target.email = (payload.get("email") or target.email).strip().lower()
    if "phone" in payload:
        target.phone = (payload.get("phone") or "").strip() or None
    if "accessRole" in payload and payload.get("accessRole") in dict(UserRole.choices):
        target.role = payload.get("accessRole")
    if "jobTitle" in payload or "kpi" in payload:
        target.job_title = (payload.get("jobTitle") or payload.get("kpi") or target.job_title).strip()
    if "departmentCode" in payload:
        target.department = Department.objects.filter(code=payload.get("departmentCode")).first()
    if "managerId" in payload:
        manager_id = payload.get("managerId")
        target.manager = User.objects.filter(pk=manager_id).first() if manager_id else None
    if "isActive" in payload:
        target.is_active = bool(payload.get("isActive"))
    target.avatar = (target.full_name[:2] if target.full_name else target.avatar or "NA").upper()
    target.save()

    organization_id = payload.get("organizationId")
    if organization_id:
        organization = Organization.objects.filter(pk=organization_id).first()
        if organization:
            OrganizationMembership.objects.update_or_create(user=target, defaults={"organization": organization, "display_title": target.job_title})

    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="hq_user_updated", entity_type="user", entity_code=str(target.id), detail=target.full_name, icon="manage_accounts")
    return json_response(build_hq_payload())


@require_auth
@csrf_exempt
@methods("POST")
def hq_request_update_view(request: HttpRequest, request_code: str):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied
    target = Request.objects.filter(code=request_code).first()
    if target is None:
        return json_error("درخواست پیدا نشد.", status=404)
    payload = parse_json(request)
    if "title" in payload:
        target.title = (payload.get("title") or target.title).strip()
    if "description" in payload:
        target.description = payload.get("description") or ""
    if "status" in payload and payload.get("status") in dict(RequestStatus.choices):
        target.status = payload.get("status")
    if "priority" in payload and payload.get("priority") in dict(RequestPriority.choices):
        target.priority = payload.get("priority")
    if "departmentCode" in payload:
        target.department = Department.objects.filter(code=payload.get("departmentCode")).first()
    if "managerId" in payload:
        target.manager = User.objects.filter(pk=payload.get("managerId")).first() if payload.get("managerId") else None
    target.updated_at = timezone.now()
    target.save()
    RequestTimeline.objects.create(request=target, action="hq_updated", note="ویرایش HQ", actor_name=request.current_user.full_name)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="hq_request_updated", entity_type="request", entity_code=target.code, detail=target.title, icon="tune")
    return json_response(build_hq_payload())


@require_auth
@csrf_exempt
@methods("POST")
def hq_payment_update_view(request: HttpRequest, expense_code: str):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied
    target = Expense.objects.filter(code=expense_code).first()
    if target is None:
        return json_error("پرداخت پیدا نشد.", status=404)
    payload = parse_json(request)
    if "title" in payload:
        target.title = (payload.get("title") or target.title).strip()
    if "amount" in payload:
        target.amount = payload.get("amount") or target.amount
    if "status" in payload and payload.get("status") in dict(ExpenseStatus.choices):
        target.status = payload.get("status")
    if "category" in payload and payload.get("category") in dict(ExpenseCategory.choices):
        target.category = payload.get("category")
    if "departmentCode" in payload:
        target.department = Department.objects.filter(code=payload.get("departmentCode")).first()
    if "notes" in payload:
        target.notes = payload.get("notes") or ""
    target.progress = 100 if target.status in {ExpenseStatus.APPROVED, ExpenseStatus.REJECTED} else max(target.progress, 30)
    target.save()
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="hq_payment_updated", entity_type="expense", entity_code=target.code, detail=target.title, icon="payments")
    return json_response(build_hq_payload())


@require_auth
@csrf_exempt
@methods("POST")
def hq_document_update_view(request: HttpRequest, document_code: str):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied
    target = Document.objects.filter(code=document_code).first()
    if target is None:
        return json_error("سند پیدا نشد.", status=404)
    payload = parse_json(request)
    if "title" in payload:
        target.title = (payload.get("title") or target.title).strip()
    if "description" in payload:
        target.description = payload.get("description") or ""
    if "status" in payload and payload.get("status") in dict(DocumentStatus.choices):
        target.status = payload.get("status")
    if "risk" in payload and payload.get("risk") in dict(DocumentRisk.choices):
        target.risk = payload.get("risk")
    if "departmentCode" in payload:
        target.department = Department.objects.filter(code=payload.get("departmentCode")).first()
    target.save()
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="hq_document_updated", entity_type="document", entity_code=target.code, detail=target.title, icon="fact_check")
    return json_response(build_hq_payload())


@require_auth
@csrf_exempt
@methods("GET", "POST")
def requests_view(request: HttpRequest):
    if request.method == "GET":
        return json_response([serialize_request(item) for item in visible_requests(request.current_user)], safe=False)

    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    department_code = request.POST.get("department", "").strip()
    manager_slug = request.POST.get("manager", "").strip()
    manager_assignee_ids = [int(item) for item in request.POST.get("managerAssigneeIds", "").split(",") if item.strip()]
    employee_assignee_ids = [int(item) for item in request.POST.get("employeeAssigneeIds", "").split(",") if item.strip()]
    priority = request.POST.get("priority", RequestPriority.MEDIUM)
    request_action = request.POST.get("action", "refer").strip().lower()
    deadline_raw = request.POST.get("deadline", "").strip()
    deadline = date.fromisoformat(deadline_raw) if deadline_raw else None
    if request_action != "refer":
        request_action = "refer"
    if request_action not in {"approve", "reject", "refer"}:
        return json_error("Ø§Ù‚Ø¯Ø§Ù… Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ù…Ø¹ØªØ¨Ø± Ù†ÛŒØ³Øª.", status=422)
    if deadline and deadline > date.today():
        return json_error("انتخاب تاریخ های آینده مجاز نیست.", status=422)
    department = Department.objects.filter(code=department_code).first()
    manager = User.objects.filter(slug=manager_slug).first() if manager_slug else None
    assigned_managers = list(User.objects.filter(pk__in=manager_assignee_ids)) if manager_assignee_ids else []
    assigned_employees = list(User.objects.filter(pk__in=employee_assignee_ids)) if employee_assignee_ids else []
    status_by_action = {
        "approve": RequestStatus.APPROVED,
        "reject": RequestStatus.REJECTED,
        "refer": RequestStatus.UNDER_REVIEW,
    }
    timeline_by_action = {
        "approve": ("approved", "ØªØ§ÛŒÛŒØ¯ Ø¯Ø±Ø®ÙˆØ§Ø³Øª"),
        "reject": ("rejected", "Ø±Ø¯ Ø¯Ø±Ø®ÙˆØ§Ø³Øª"),
        "refer": ("referred", "Ø§Ø±Ø¬Ø§Ø¹ Ø¯Ø±Ø®ÙˆØ§Ø³Øª"),
    }

    timeline_by_action = {
        "approve": ("approved", "\u062a\u0627\u06cc\u06cc\u062f \u062f\u0631\u062e\u0648\u0627\u0633\u062a"),
        "reject": ("rejected", "\u0631\u062f \u062f\u0631\u062e\u0648\u0627\u0633\u062a"),
        "refer": ("referred", "\u0627\u0631\u062c\u0627\u0639 \u062f\u0631\u062e\u0648\u0627\u0633\u062a"),
    }

    if manager_assignee_ids and manager is None:
        return json_error("مدیر اصلی باید به درخواست ارجاع شود.", status=422)
    if manager_assignee_ids and (len(assigned_managers) != len(manager_assignee_ids) or any(not is_manager(item) for item in assigned_managers)):
        return json_error("مدیران ارجاعی باید از مدیران مجاز انتخاب شوند.", status=422)
    if employee_assignee_ids and (len(assigned_employees) != len(employee_assignee_ids) or any(is_manager(item) for item in assigned_employees)):
        return json_error("کارمندان ارجاعی باید از میان کارمندان مجاز انتخاب شوند.", status=422)
    if manager and any(item.slug == manager.slug for item in assigned_managers):
        return json_error("مدیر اصلی نباید در فهرست مدیران ارجاعی تکرار شود.", status=422)
    request_obj = Request.objects.create(
        code=next_code("REQ"),
        title=title or "درخواست جدید",
        description=description or "",
        priority=priority,
        status=status_by_action[request_action],
        department=department,
        requester=request.current_user,
        manager=manager,
        deadline=deadline,
        updated_at=timezone.now(),
    )
    if assigned_managers:
        request_obj.assigned_managers.set(assigned_managers)
    if assigned_employees:
        request_obj.assigned_employees.set(assigned_employees)

    RequestTimeline.objects.create(request=request_obj, action="created", note="ایجاد درخواست", actor_name=request.current_user.full_name)
    RequestTimeline.objects.create(request=request_obj, action="submitted", note="ثبت درخواست", actor_name=request.current_user.full_name)
    action_name, action_note = timeline_by_action[request_action]
    RequestTimeline.objects.create(request=request_obj, action=action_name, note=action_note, actor_name=request.current_user.full_name)
    if assigned_managers:
        RequestTimeline.objects.create(
            request=request_obj,
            action="manager_referrals",
            note=f"ارجاع به مدیران: {', '.join(item.full_name for item in assigned_managers)}",
            actor_name=request.current_user.full_name,
        )
    if assigned_employees:
        RequestTimeline.objects.create(
            request=request_obj,
            action="employee_referrals",
            note=f"ارجاع به کارمندان: {', '.join(item.full_name for item in assigned_employees)}",
            actor_name=request.current_user.full_name,
        )
    for file_obj in request.FILES.getlist("attachments"):
        stored_name = save_uploaded_file(file_obj)
        request_obj.attachments.create(
            original_name=file_obj.name,
            stored_name=stored_name,
            mime_type=file_obj.content_type,
            size_bytes=file_obj.size,
        )

    request_obj = Request.objects.select_related("requester", "manager", "department").prefetch_related("assigned_managers", "assigned_employees", "attachments").get(pk=request_obj.pk)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="request_created", entity_type="request", entity_code=request_obj.code, detail=request_obj.title, icon="assignment")
    return json_response(serialize_request(request_obj), status=201)


@require_auth
@methods("GET")
def request_detail_view(request: HttpRequest, request_code: str):
    request_obj = scoped_requests(request).filter(code=request_code).first()
    if request_obj is None:
        return json_error("درخواست پیدا نشد.", status=404)
    return json_response(
        {
            "request": serialize_request(request_obj),
            "timeline": [
                {"step": index + 1, "title": item.action, "note": item.note}
                for index, item in enumerate(request_obj.timeline_items.order_by("created_at"))
            ],
        }
    )


@require_auth
@csrf_exempt
@methods("POST")
def request_approve_view(request: HttpRequest, request_code: str):
    request_obj = scoped_requests(request).filter(code=request_code).first()
    if request_obj is None:
        return json_error("درخواست پیدا نشد.", status=404)

    can_approve = (
        request_obj.status in {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW}
        and (
            request_obj.manager_id == request.current_user.id
            or request_obj.assigned_managers.filter(pk=request.current_user.id).exists()
            or request.current_user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER}
            or request.current_user.slug == HQ_USERNAME
        )
    )
    if not can_approve:
        return json_error("دسترسی کافی برای تایید این درخواست ندارید.", status=403)

    request_obj.status = RequestStatus.APPROVED
    request_obj.updated_at = timezone.now()
    request_obj.save(update_fields=["status", "updated_at"])
    RequestTimeline.objects.create(
        request=request_obj,
        action="approved",
        note="تایید درخواست",
        actor_name=request.current_user.full_name,
    )
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="request_approved",
        entity_type="request",
        entity_code=request_obj.code,
        detail=request_obj.title,
        icon="assignment_turned_in",
    )
    return json_response({"status": "approved", "request": request_obj.code})


@require_auth
@csrf_exempt
@methods("POST")
def request_reject_view(request: HttpRequest, request_code: str):
    request_obj = scoped_requests(request).filter(code=request_code).first()
    if request_obj is None:
        return json_error("درخواست پیدا نشد.", status=404)

    can_approve = (
        request_obj.status in {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW}
        and (
            request_obj.manager_id == request.current_user.id
            or request_obj.assigned_managers.filter(pk=request.current_user.id).exists()
            or request.current_user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER}
            or request.current_user.slug == HQ_USERNAME
        )
    )
    if not can_approve:
        return json_error("دسترسی کافی برای رد این درخواست ندارید.", status=403)

    payload = parse_json(request)
    reason = (payload.get("reason") or "").strip()
    request_obj.status = RequestStatus.REJECTED
    request_obj.updated_at = timezone.now()
    request_obj.save(update_fields=["status", "updated_at"])
    RequestTimeline.objects.create(
        request=request_obj,
        action="rejected",
        note=reason or "رد درخواست",
        actor_name=request.current_user.full_name,
    )
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="request_rejected",
        entity_type="request",
        entity_code=request_obj.code,
        detail=request_obj.title,
        icon="cancel",
    )
    return json_response({"status": "rejected", "request": request_obj.code})


@require_auth
@csrf_exempt
@methods("GET", "POST")
def expenses_view(request: HttpRequest):
    if not can_access_expenses(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    if request.method == "GET":
        return json_response([serialize_expense(item) for item in visible_expenses(request.current_user)], safe=False)

    description = request.POST.get("description", "").strip()
    amount = request.POST.get("amount", "0")
    expense_action = request.POST.get("action", "refer").strip().lower()
    expense_date_raw = request.POST.get("expenseDate", "").strip()
    if not expense_date_raw:
        return json_error("تاریخ هزینه الزامی است.", status=422)
    department_code = request.POST.get("department", "").strip()
    invoice = request.FILES.get("invoice")
    expense_date = date.fromisoformat(expense_date_raw)
    if expense_action not in {"approve", "reject", "refer"}:
        return json_error("Ø§Ù‚Ø¯Ø§Ù… Ù‡Ø²ÛŒÙ†Ù‡ Ù…Ø¹ØªØ¨Ø± Ù†ÛŒØ³Øª.", status=422)
    if expense_date > date.today():
        return json_error("انتخاب تاریخ های آینده مجاز نیست.", status=422)
    department = Department.objects.filter(code=department_code).first() or request.current_user.department
    invoice_name = save_uploaded_file(invoice) if invoice else None
    status_by_action = {
        "approve": ExpenseStatus.APPROVED,
        "reject": ExpenseStatus.REJECTED,
        "refer": ExpenseStatus.UNDER_REVIEW,
    }
    progress_by_action = {
        "approve": 100,
        "reject": 100,
        "refer": 50,
    }

    expense = Expense.objects.create(
        code=next_code("EXP"),
        title=(description[:180] or "هزینه جدید"),
        amount=amount,
        category=ExpenseCategory.MISCELLANEOUS,
        status=status_by_action[expense_action],
        progress=progress_by_action[expense_action],
        expense_date=expense_date,
        notes=description,
        department=department,
        owner=request.current_user,
        invoice_file_name=invoice_name,
    )
    expense = Expense.objects.select_related("owner", "department").get(pk=expense.pk)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="expense_created", entity_type="expense", entity_code=expense.code, detail=expense.title, icon="payments")
    return json_response(serialize_expense(expense), status=201)


@require_auth
@methods("GET")
def expense_detail_view(request: HttpRequest, expense_code: str):
    if not can_access_expenses(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    expense = scoped_expenses(request).filter(code=expense_code).first()
    if expense is None:
        return json_error("هزینه پیدا نشد.", status=404)
    return json_response(serialize_expense(expense))


@require_auth
@csrf_exempt
@methods("POST")
def expense_approve_view(request: HttpRequest, expense_code: str):
    if not can_access_expenses(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    expense = scoped_expenses(request).filter(code=expense_code).first()
    if expense is None:
        return json_error("هزینه پیدا نشد.", status=404)

    can_approve = (
        expense.status in {ExpenseStatus.PENDING, ExpenseStatus.UNDER_REVIEW}
        and (request.current_user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER} or request.current_user.slug == HQ_USERNAME)
    )
    if not can_approve:
        return json_error("دسترسی کافی برای تایید این هزینه ندارید.", status=403)

    expense.status = ExpenseStatus.APPROVED
    expense.progress = 100
    expense.save(update_fields=["status", "progress"])
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="expense_approved",
        entity_type="expense",
        entity_code=expense.code,
        detail=expense.title,
        icon="payments",
    )
    return json_response({"status": "approved", "expense": expense.code})


@require_auth
@csrf_exempt
@methods("POST")
def expense_reject_view(request: HttpRequest, expense_code: str):
    if not can_access_expenses(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    expense = scoped_expenses(request).filter(code=expense_code).first()
    if expense is None:
        return json_error("هزینه پیدا نشد.", status=404)

    can_approve = (
        expense.status in {ExpenseStatus.PENDING, ExpenseStatus.UNDER_REVIEW}
        and (request.current_user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER} or request.current_user.slug == HQ_USERNAME)
    )
    if not can_approve:
        return json_error("دسترسی کافی برای رد این هزینه ندارید.", status=403)

    payload = parse_json(request)
    reason = (payload.get("reason") or "").strip()
    expense.status = ExpenseStatus.REJECTED
    expense.progress = 100
    expense.notes = f"{expense.notes or expense.title}\n\nعلت رد: {reason}" if reason else expense.notes
    expense.save(update_fields=["status", "progress", "notes"])
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="expense_rejected",
        entity_type="expense",
        entity_code=expense.code,
        detail=expense.title,
        icon="payments",
    )
    return json_response({"status": "rejected", "expense": expense.code})


@require_auth
@methods("GET")
def expenses_summary_view(request: HttpRequest):
    if not can_access_expenses(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    items = list(visible_expenses(request.current_user))
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    return json_response(
        [
            {"label": "امروز", "value": format_money(sum(item.amount for item in items if item.expense_date == today))},
            {"label": "این هفته", "value": format_money(sum(item.amount for item in items if item.expense_date >= week_start))},
            {"label": "این ماه", "value": format_money(sum(item.amount for item in items if item.expense_date.month == today.month))},
            {"label": "امسال", "value": format_money(sum(item.amount for item in items if item.expense_date.year == today.year))},
        ],
        safe=False,
    )


@require_auth
@csrf_exempt
@methods("GET", "POST")
def users_view(request: HttpRequest):
    if request.method == "GET":
        if not can_access_users(request.current_user):
            return json_error("دسترسی کافی ندارید.", status=403)
        users_qs = visible_users(request.current_user).select_related("department", "manager").order_by("created_at")
        return json_response([serialize_user(item) for item in users_qs], safe=False)

    if not can_manage_users(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)

    payload = parse_json(request)
    email = (payload.get("email") or "").strip().lower()
    if User.objects.filter(email=email).exists():
        return json_error("این ایمیل قبلا ثبت شده است.", status=409)

    role = payload.get("accessRole", UserRole.EMPLOYEE)
    department = Department.objects.filter(code=payload.get("department", "")).first()
    manager = User.objects.filter(pk=payload.get("managerId")).first() if payload.get("managerId") else None
    full_name = (payload.get("fullName") or "").strip()

    user = User.objects.create(
        slug=email.split("@", 1)[0].replace(".", "-"),
        full_name=full_name,
        email=email,
        phone=None,
        password_hash=get_password_hash(payload.get("password") or "UserSecret123!"),
        role=role,
        job_title=(payload.get("jobTitle") or ("مدیر" if role != UserRole.EMPLOYEE else "کارمند")).strip(),
        avatar=(full_name[:2] if full_name else "NA").upper(),
        bio="",
        is_active=True,
        department=department,
        manager=manager,
    )
    organization = OrganizationMembership.objects.select_related("organization").get(user=request.current_user).organization
    OrganizationMembership.objects.create(organization=organization, user=user, display_title=user.job_title)
    sync_user_section_access(request.current_user, user, section_access_payload(payload))
    user = User.objects.select_related("department", "manager").get(pk=user.pk)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="user_created", entity_type="user", entity_code=str(user.id), detail=user.full_name, icon="group")
    return json_response(serialize_user(user), status=201)


@require_auth
@csrf_exempt
@methods("GET", "POST")
def users_view(request: HttpRequest):
    if request.method == "GET":
        if not can_access_users(request.current_user):
            return json_error("دسترسی کافی ندارید.", status=403)
        users_qs = visible_users(request.current_user).select_related("department", "manager").order_by("created_at")
        return json_response([serialize_user(item) for item in users_qs], safe=False)

    if not can_manage_users(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)

    payload = parse_json(request)
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return json_error("ایمیل الزامی است.", status=422)
    if User.objects.filter(email=email).exists():
        return json_error("این ایمیل قبلا ثبت شده است.", status=409)

    role = payload.get("accessRole", UserRole.EMPLOYEE)
    if role not in dict(UserRole.choices):
        return json_error("نقش کاربر معتبر نیست.", status=422)

    department = Department.objects.filter(code=payload.get("department", "")).first()
    manager = User.objects.filter(pk=payload.get("managerId")).first() if payload.get("managerId") else None
    full_name = (payload.get("fullName") or "").strip()
    if not full_name:
        return json_error("نام کامل الزامی است.", status=422)

    password = payload.get("password") or "UserSecret123!"
    if len(password) < 6:
        return json_error("رمز عبور باید حداقل 6 کاراکتر باشد.", status=422)
    if manager and manager.role == UserRole.EMPLOYEE:
        return json_error("مدیر مستقیم باید از سطح مدیریتی انتخاب شود.", status=422)

    user = User.objects.create(
        slug=build_unique_user_slug(email.split("@", 1)[0]),
        full_name=full_name,
        email=email,
        phone=None,
        password_hash=get_password_hash(password),
        role=role,
        job_title=(payload.get("jobTitle") or ("مدیر" if role != UserRole.EMPLOYEE else "کارمند")).strip(),
        avatar=(full_name[:2] if full_name else "NA").upper(),
        bio="",
        is_active=True,
        department=department,
        manager=manager,
    )
    organization = OrganizationMembership.objects.select_related("organization").get(user=request.current_user).organization
    OrganizationMembership.objects.create(organization=organization, user=user, display_title=user.job_title)
    sync_user_section_access(request.current_user, user, section_access_payload(payload))
    user = User.objects.select_related("department", "manager").get(pk=user.pk)
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="user_created",
        entity_type="user",
        entity_code=str(user.id),
        detail=user.full_name,
        icon="group",
    )
    return json_response(serialize_user(user), status=201)


@require_auth
@csrf_exempt
@methods("PATCH")
def user_detail_view(request: HttpRequest, user_id: int):
    if not can_manage_users(request.current_user):
        return json_error("Ø¯Ø³ØªØ±Ø³ÛŒ Ú©Ø§ÙÛŒ Ù†Ø¯Ø§Ø±ÛŒØ¯.", status=403)

    allowed_ids = set(visible_users(request.current_user).values_list("id", flat=True))
    if user_id not in allowed_ids:
        return json_error("Ú©Ø§Ø±Ø¨Ø± Ù…ÙˆØ±Ø¯ Ù†Ø¸Ø± ÛŒØ§ÙØª Ù†Ø´Ø¯.", status=404)

    user = User.objects.select_related("department", "manager").filter(pk=user_id).first()
    if not user:
        return json_error("Ú©Ø§Ø±Ø¨Ø± Ù…ÙˆØ±Ø¯ Ù†Ø¸Ø± ÛŒØ§ÙØª Ù†Ø´Ø¯.", status=404)

    payload = parse_json(request)
    email = (payload.get("email") or user.email).strip().lower()
    if User.objects.exclude(pk=user.pk).filter(email=email).exists():
        return json_error("Ø§ÛŒÙ† Ø§ÛŒÙ…ÛŒÙ„ Ù‚Ø¨Ù„Ø§ Ø«Ø¨Øª Ø´Ø¯Ù‡ Ø§Ø³Øª.", status=409)

    manager_id = payload.get("managerId")
    manager = None
    if manager_id:
        manager = User.objects.filter(pk=manager_id).first()
        if not manager or manager.id == user.id or manager.id not in allowed_ids:
            return json_error("Ù…Ø¯ÛŒØ± Ø§Ù†ØªØ®Ø§Ø¨ Ø´Ø¯Ù‡ Ù…Ø¹ØªØ¨Ø± Ù†ÛŒØ³Øª.", status=422)

    department = None
    department_code = (payload.get("department") or payload.get("departmentCode") or "").strip()
    if department_code:
        department = Department.objects.filter(code=department_code).first()

    role = payload.get("accessRole") or user.role
    user.full_name = (payload.get("fullName") or user.full_name).strip()
    user.email = email
    user.role = role
    user.job_title = (payload.get("jobTitle") or user.job_title).strip() or user.job_title
    user.department = department
    user.manager = manager
    if "isActive" in payload:
        user.is_active = bool(payload.get("isActive"))
    user.avatar = (user.full_name[:2] if user.full_name else user.avatar or "NA").upper()
    update_fields = ["full_name", "email", "role", "job_title", "department", "manager", "is_active", "avatar"]

    password = (payload.get("password") or "").strip()
    if password:
        user.password_hash = get_password_hash(password)
        update_fields.append("password_hash")

    user.save(update_fields=update_fields)
    sync_user_section_access(request.current_user, user, section_access_payload(payload))
    user.refresh_from_db()
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="user_updated",
        entity_type="user",
        entity_code=str(user.id),
        detail=user.full_name,
        icon="manage_accounts",
    )
    return json_response(serialize_user(user))


@require_auth
@methods("GET")
def reports_view(request: HttpRequest):
    if not can_view_reports(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    return json_response(visible_reports_payload(request.current_user))


@require_auth
@methods("GET")
def report_export_view(request: HttpRequest, report_key: str):
    if not can_view_reports(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    export_format = (request.GET.get("format") or "csv").strip().lower()
    organization_id_raw = request.GET.get("organizationId")
    organization_id = int(organization_id_raw) if organization_id_raw and organization_id_raw.isdigit() else None
    if export_format != "csv":
        return json_error("فرمت خروجی معتبر نیست.", status=422)
    try:
        file_name, content = render_report_export(report_key, request.current_user, organization_id)
    except ValueError as exc:
        return json_error(str(exc), status=404)

    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    return response


@require_auth
@methods("GET")
def approvals_view(request: HttpRequest):
    if not can_access_approvals(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    return json_response([serialize_approval(item, request.current_user) for item in visible_approvals(request.current_user)], safe=False)


@require_auth
@methods("GET")
def approvals_metrics_view(request: HttpRequest):
    if not can_access_approvals(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    return json_response(approval_metrics(request.current_user))


@require_auth
@csrf_exempt
@methods("GET", "POST")
def approvals_signature_view(request: HttpRequest):
    if not can_approve_documents(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    signature = ensure_signature(request.current_user)
    if request.method == "GET":
        has_signature = has_saved_signature(signature.signature_data)
        return json_response({"hasSignature": has_signature, "signatureData": signature.signature_data if has_signature else ""})

    payload = parse_json(request)
    signature_data = (payload.get("signatureData") or "").strip()
    if not has_saved_signature(signature_data):
        return json_error("امضای معتبر ثبت نشده است.", status=422)
    signature.signature_data = signature_data
    signature.updated_at = timezone.now()
    signature.save(update_fields=["signature_data", "updated_at"])
    return json_response({"hasSignature": True, "signatureData": signature.signature_data})


@require_auth
@csrf_exempt
@methods("POST")
def documents_create_view(request: HttpRequest):
    if not can_access_approvals(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    department_code = request.POST.get("department", "").strip()
    document_type = request.POST.get("documentType", "سند").strip()
    risk = request.POST.get("risk", DocumentRisk.MEDIUM)
    assignee_ids = [int(item) for item in request.POST.get("assigneeIds", "").split(",") if item.strip()]
    file_obj = request.FILES.get("file")
    if not assignee_ids:
        return json_error("حداقل یک مدیر باید انتخاب شود.", status=422)
    approvers = list(User.objects.filter(pk__in=assignee_ids))
    if not approvers or any(not is_manager(item) for item in approvers):
        return json_error("ارجاع سند فقط به مدیر مجاز است.", status=422)

    document = Document.objects.create(
        code=next_code("DOC"),
        title=title or "سند جدید",
        document_type=document_type,
        description=description,
        status=DocumentStatus.PENDING,
        risk=risk,
        confidentiality=ConfidentialityLevel.INTERNAL,
        department=Department.objects.filter(code=department_code).first() or request.current_user.department,
        owner=request.current_user,
        file_name=save_uploaded_file(file_obj) if file_obj else None,
    )
    for approver in approvers:
        ApprovalAssignment.objects.create(document=document, approver=approver, status=ApprovalAssignmentStatus.PENDING)
    document = Document.objects.select_related("owner", "department").prefetch_related("approval_assignments__approver").get(pk=document.pk)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="document_created", entity_type="document", entity_code=document.code, detail=document.title, icon="description")
    return json_response(serialize_approval(document, request.current_user), status=201)


@require_auth
@methods("GET")
def approval_detail_view(request: HttpRequest, document_code: str):
    if not can_access_approvals(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    document = scoped_documents(request).filter(code=document_code).first()
    if document is None:
        return json_error("سند پیدا نشد.", status=404)
    return json_response(serialize_approval(document, request.current_user))


@require_auth
@methods("GET")
def approval_download_view(request: HttpRequest, document_code: str):
    if not can_access_approvals(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    document = scoped_documents(request).filter(code=document_code).first()
    if document is None or not document.file_name:
        return json_error("سند پیدا نشد.", status=404)

    document_path = Path(settings.MEDIA_ROOT) / document.file_name
    if not document_path.exists():
        return json_error("فایل سند موجود نیست.", status=404)

    content_type, _ = mimetypes.guess_type(document_path.name)
    download_name = f"{document.code}{document_path.suffix.lower()}"
    response = FileResponse(document_path.open("rb"), content_type=content_type or "application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{download_name}"'
    return response


@require_auth
@csrf_exempt
@methods("POST")
def approval_approve_view(request: HttpRequest, document_code: str):
    if not can_approve_documents(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    document = scoped_documents(request).filter(code=document_code).first()
    if document is None:
        return json_error("سند پیدا نشد.", status=404)
    if request.current_user.slug == HQ_USERNAME and request.GET.get("organizationId"):
        if document.status == DocumentStatus.REJECTED:
            return json_error("این سند قبلا رد شده است.", status=409)
        now_value = timezone.now()
        document.approval_assignments.filter(status=ApprovalAssignmentStatus.PENDING).update(
            status=ApprovalAssignmentStatus.APPROVED,
            decision_note="HQ",
            acted_at=now_value,
        )
        document.status = DocumentStatus.APPROVED
        document.approved_at = now_value
        document.rejected_at = None
        document.rejection_reason = ""
        document.save(update_fields=["status", "approved_at", "rejected_at", "rejection_reason"])
        AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="hq_document_approved", entity_type="document", entity_code=document.code, detail=document.title, icon="fact_check")
        return json_response({"status": "approved", "document": document.code})
    assignment = document.approval_assignments.filter(approver=request.current_user).first()
    if assignment is None:
        return json_error("این سند به شما ارجاع نشده است.", status=403)
    if assignment.status == ApprovalAssignmentStatus.REJECTED:
        return json_error("این ارجاع قبلا رد شده است و دیگر قابل تایید نیست.", status=409)
    if assignment.status == ApprovalAssignmentStatus.APPROVED:
        return json_response({"status": "approved", "document": document.code})
    signature = ensure_signature(request.current_user)
    if not has_saved_signature(signature.signature_data):
        return json_error("ابتدا امضای دیجیتال معتبر خود را ثبت کنید.", status=422)
    if document.status == DocumentStatus.REJECTED:
        return json_error("این سند قبلا رد شده است و دیگر قابل تایید نیست.", status=409)

    try:
        with transaction.atomic():
            assignment.status = ApprovalAssignmentStatus.APPROVED
            assignment.decision_note = ""
            assignment.signed_signature_data = signature.signature_data
            assignment.acted_at = timezone.now()
            assignment.save(update_fields=["status", "decision_note", "signed_signature_data", "acted_at"])
            if document.file_name:
                document.file_name = sign_document_file(document, assignment, signature.signature_data)
                document.save(update_fields=["file_name"])
            update_document_status(document)
    except (ValueError, FileNotFoundError) as exc:
        return json_error(str(exc), status=422)
    except Exception:
        return json_error("امضای سند با خطا مواجه شد.", status=500)
    return json_response({"status": "approved", "document": document.code})


@require_auth
@csrf_exempt
@methods("POST")
def approval_reject_view(request: HttpRequest, document_code: str):
    if not can_approve_documents(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    payload = parse_json(request)
    document = scoped_documents(request).filter(code=document_code).first()
    if document is None:
        return json_error("سند پیدا نشد.", status=404)
    reason = (payload.get("reason") or "").strip()
    if request.current_user.slug == HQ_USERNAME and request.GET.get("organizationId"):
        if document.status == DocumentStatus.APPROVED:
            return json_error("این سند قبلا تایید شده است.", status=409)
        now_value = timezone.now()
        document.approval_assignments.filter(status=ApprovalAssignmentStatus.PENDING).update(
            status=ApprovalAssignmentStatus.REJECTED,
            decision_note=reason,
            signed_signature_data="",
            acted_at=now_value,
        )
        document.status = DocumentStatus.REJECTED
        document.rejection_reason = reason
        document.rejected_at = now_value
        document.approved_at = None
        document.save(update_fields=["status", "rejection_reason", "rejected_at", "approved_at"])
        AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="hq_document_rejected", entity_type="document", entity_code=document.code, detail=document.title, icon="cancel")
        return json_response({"status": "rejected", "document": document.code})
    assignment = document.approval_assignments.filter(approver=request.current_user).first()
    if assignment is None:
        return json_error("این سند به شما ارجاع نشده است.", status=403)
    if assignment.status == ApprovalAssignmentStatus.APPROVED:
        return json_error("این ارجاع قبلا تایید شده است و دیگر قابل رد نیست.", status=409)
    if assignment.status == ApprovalAssignmentStatus.REJECTED:
        return json_response({"status": "rejected", "document": document.code})
    if document.status == DocumentStatus.REJECTED:
        return json_error("این سند قبلا رد شده است.", status=409)
    reason = (payload.get("reason") or "").strip()
    assignment.status = ApprovalAssignmentStatus.REJECTED
    assignment.decision_note = reason
    assignment.signed_signature_data = ""
    assignment.acted_at = timezone.now()
    assignment.save(update_fields=["status", "decision_note", "signed_signature_data", "acted_at"])
    document.rejection_reason = reason
    document.save(update_fields=["rejection_reason"])
    update_document_status(document)
    return json_response({"status": "rejected", "document": document.code})


@require_auth
@csrf_exempt
@methods("GET", "POST")
def settings_profile_view(request: HttpRequest):
    organization_id_raw = request.GET.get("organizationId") or request.POST.get("organizationId")
    organization_id = int(organization_id_raw) if organization_id_raw and str(organization_id_raw).isdigit() else None
    if request.method == "GET":
        return json_response(build_settings_profile_payload(request.current_user, organization_id))

    if not can_manage_users(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)

    payload = parse_json(request)
    if organization_id is None:
        payload_organization_id = payload.get("organizationId")
        organization_id = int(payload_organization_id) if payload_organization_id and str(payload_organization_id).isdigit() else None
    if request.current_user.slug == HQ_USERNAME and organization_id:
        organization = Organization.objects.exclude(code="hq-control").filter(pk=organization_id).first()
        if organization is None:
            return json_error("مجموعه پیدا نشد.", status=404)
    else:
        organization = get_user_organization(request.current_user)
    preference, _ = OrganizationPreference.objects.get_or_create(organization=organization)
    section_key = (payload.get("sectionKey") or "").strip()

    if section_key:
        allowed_user_ids = [int(item) for item in payload.get("allowedUserIds", []) if str(item).strip().isdigit()]
        if request.current_user.slug == HQ_USERNAME and organization_id:
            allowed_ids = set(User.objects.filter(organization_membership__organization=organization).values_list("id", flat=True))
        else:
            allowed_ids = set(visible_users(request.current_user).values_list("id", flat=True))
        SectionAccessGrant.objects.filter(organization=organization, section_key=section_key).delete()
        SectionAccessGrant.objects.bulk_create(
            [
                SectionAccessGrant(organization=organization, section_key=section_key, user_id=user_id)
                for user_id in allowed_user_ids
                if user_id in allowed_ids and user_id != request.current_user.id
            ]
        )
    elif "departments" in payload:
        departments_payload = payload.get("departments") or []
        if not isinstance(departments_payload, list):
            return json_error("فهرست بخش‌ها معتبر نیست.", status=422)
        for item in departments_payload:
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or "").strip()
            if not name:
                continue
            department_id = item.get("id")
            if department_id:
                department = Department.objects.filter(pk=department_id).first()
                if department is None:
                    continue
                if Department.objects.exclude(pk=department.pk).filter(name=name).exists():
                    return json_error("نام بخش تکراری است.", status=409)
                department.name = name
                department.save(update_fields=["name"])
            else:
                code = normalize_slug(item.get("code") or name) or f"department-{Department.objects.count() + 1}"
                base_code = code
                index = 2
                while Department.objects.filter(code=code).exists():
                    code = f"{base_code}-{index}"
                    index += 1
                if Department.objects.filter(name=name).exists():
                    return json_error("نام بخش تکراری است.", status=409)
                Department.objects.create(code=code, name=name)
    else:
        organization_name = (payload.get("organizationName") or "").strip()
        if not organization_name:
            return json_error("نام سازمان الزامی است.", status=422)
        organization.name = organization_name
        organization.save(update_fields=["name"])

        if "twoFactorRequired" in payload:
            preference.two_factor_required = bool(payload.get("twoFactorRequired"))
            preference.updated_at = timezone.now()
            preference.save(update_fields=["two_factor_required", "updated_at"])

    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="settings_updated",
        entity_type="organization",
        entity_code=organization.code,
        detail=section_key or organization.name,
        icon="settings",
    )
    return json_response(build_settings_profile_payload(request.current_user, organization_id))


@require_auth
@methods("GET")
def settings_view(request: HttpRequest):
    if not can_access_settings(request.current_user) and not can_manage_users(request.current_user):
        return json_error("Ø¯Ø³ØªØ±Ø³ÛŒ Ú©Ø§ÙÛŒ Ù†Ø¯Ø§Ø±ÛŒØ¯.", status=403)
    return json_response(
        [
            {"title": "حساب کاربری", "description": "مدیریت نقش ها و دسترسی"},
            {"title": "اسناد", "description": "گردش کار امضای دیجیتال"},
            {"title": "هزینه ها", "description": "ثبت، پیگیری و کنترل هزینه"},
            {"title": "گزارشات", "description": "تحلیل مدیریتی"},
        ],
        safe=False,
    )
