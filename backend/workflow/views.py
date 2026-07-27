from __future__ import annotations

import json
import mimetypes
import os
from urllib import error as urllib_error
from urllib import request as urllib_request
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.models import Q
from django.db.utils import OperationalError, ProgrammingError
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from ai.stamp_processing import normalize_signature_data_url, normalize_stamp_data_url
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
from workflow.document_signing import build_approval_mark, sign_document_file
from workflow.models import (
    ApprovalAssignment,
    ApprovalAssignmentStatus,
    AttendanceEvent,
    AuditLog,
    ConfidentialityLevel,
    Department,
    Document,
    DocumentRisk,
    DocumentStatus,
    Expense,
    ExpenseApprovalAssignment,
    ExpenseCategory,
    ExpenseStatus,
    FeaturePurchase,
    OrganizationMembership,
    OrganizationPreference,
    PlatformRole,
    Request,
    RequestApprovalAssignment,
    RequestAttachment,
    RequestPriority,
    RequestStatus,
    RequestTimeline,
    RegistrationRequest,
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
from workflow.seed import ensure_required_login_users, seed_demo_data
from workflow.support_tickets import (
    close_stale_support_tickets,
    default_hq_support_user,
    is_hq_admin as user_is_hq_admin,
    is_hq_user as user_is_hq_user,
    recalculate_support_metrics,
    response_quality_score,
)
from workflow.services import (
    approval_metrics,
    build_bootstrap_payload,
    build_hq_payload,
    format_money,
    HQ_USERNAME,
    CORE_FEATURE_KEY,
    PURCHASABLE_FEATURES,
    license_status_payload,
    normalize_money,
    next_code,
    render_report_export,
    save_uploaded_file,
    serialize_approval,
    serialize_current_user,
    serialize_expense,
    serialize_hq_team_member,
    serialize_request,
    serialize_support_ticket,
    serialize_user,
    wallet_options_payload,
    wallet_dashboard_payload,
    ensure_organization_wallets,
    update_document_status,
    visible_approvals,
    visible_expenses,
    visible_reports_payload,
    visible_requests,
    visible_department_catalog,
)

JSON_KWARGS = {"ensure_ascii": False}
DEFAULT_SIGNATURE_DATA = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="
PERSIAN_DIGIT_TRANSLATION = str.maketrans("\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669", "01234567890123456789")
SMS_FOOTER_TEXT = "از طرف کارنومند"


def public_app_url() -> str:
    return str(os.getenv("WORKFLOW_PUBLIC_APP_URL", "https://carnomand.ir") or "https://carnomand.ir").strip().rstrip("/")


def sms_join_lines(*lines: str) -> str:
    return "\n".join(str(line).strip() for line in lines if str(line or "").strip())


def organization_display_name(organization: Organization | None) -> str:
    if organization is None:
        return "سامانه کارنومند"
    return str(organization.name or "").strip() or "سامانه کارنومند"


def build_account_credentials_sms(
    *,
    full_name: str,
    organization_name: str,
    username: str,
    password: str,
    role_label: str = "کاربر",
    app_url: str | None = None,
) -> str:
    url = (app_url or public_app_url()).rstrip("/")
    person = str(full_name or "").strip() or "کاربر گرامی"
    org = str(organization_name or "").strip() or "سامانه کارنومند"
    return sms_join_lines(
        "کارنومند | مشخصات ورود به سامانه",
        f"{person} گرامی",
        f"حساب کاربری شما در مجموعه «{org}» ایجاد شد.",
        f"نقش شما: {role_label}",
        "این پیامک برای اعلام مشخصات ورود شما به سامانه مدیریت کارنومند ارسال شده است.",
        "اطلاعات ورود:",
        f"نام کاربری: {username}",
        f"رمز عبور: {password}",
        f"آدرس سامانه: {url}",
        "پس از ورود می‌توانید رمز عبور خود را از بخش تنظیمات تغییر دهید.",
    )


def build_workflow_event_sms(
    *,
    organization: Organization | None,
    headline: str,
    details: list[str] | tuple[str, ...] = (),
    action_hint: str = "برای مشاهده جزئیات وارد سامانه شوید.",
) -> str:
    org_name = organization_display_name(organization)
    lines = [
        "کارنومند | اطلاع‌رسانی سامانه",
        f"مجموعه: {org_name}",
        headline,
        *[str(item).strip() for item in details if str(item or "").strip()],
        action_hint,
        f"آدرس سامانه: {public_app_url()}",
    ]
    return sms_join_lines(*lines)


def has_saved_signature(signature_data: str | None) -> bool:
    normalized = (signature_data or "").strip()
    return bool(normalized) and normalized != DEFAULT_SIGNATURE_DATA


def has_saved_stamp(stamp_data: str | None) -> bool:
    return bool((stamp_data or "").strip())


def sms_provider_config() -> dict[str, str]:
    return {
        "base_url": str(os.getenv("IRANPAYAMAK_BASE_URL", "https://api.iranpayamak.com") or "https://api.iranpayamak.com").strip(),
        "line_number": str(os.getenv("IRANPAYAMAK_LINE_NUMBER", "") or "").strip(),
        "api_key": str(os.getenv("IRANPAYAMAK_API_KEY", "") or "").strip(),
    }


def provider_message_text(provider_data: dict, fallback: str = "ارسال پیامک با خطا مواجه شد.") -> str:
    if not isinstance(provider_data, dict):
        return fallback
    for key in ("message", "error", "detail"):
        value = provider_data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    data = provider_data.get("data")
    if isinstance(data, dict):
        for key in ("message", "error", "detail"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return fallback


def normalize_sms_recipient(value: str | None) -> str:
    digits = "".join(char for char in str(value or "").translate(PERSIAN_DIGIT_TRANSLATION) if char.isdigit())
    if digits.startswith("0098") and len(digits) >= 14:
        digits = f"0{digits[4:]}"
    elif digits.startswith("98") and len(digits) >= 12:
        digits = f"0{digits[2:]}"
    elif len(digits) == 10 and digits.startswith("9"):
        digits = f"0{digits}"
    if len(digits) == 11 and digits.startswith("09"):
        return digits
    return digits


def normalize_sms_recipients(recipients) -> list[str]:
    normalized = []
    seen = set()
    for raw_value in recipients or []:
        phone = normalize_sms_recipient(raw_value)
        if not (len(phone) == 11 and phone.startswith("09")):
            continue
        if phone in seen:
            continue
        seen.add(phone)
        normalized.append(phone)
    return normalized


def sms_char_blocks(text: str) -> int:
    """Billable character blocks for SMS pricing (1-70=1, 71-140=2, ...)."""
    length = len(str(text or ""))
    if length <= 0:
        return 0
    raw_chars_per_block = str(
        os.getenv("SMS_CHARS_PER_SEGMENT")
        or os.getenv("SMS_CHARS_PER_100")
        or "70"
    ).strip()
    try:
        chars_per_block = max(1, int(raw_chars_per_block))
    except ValueError:
        chars_per_block = 70
    return (length + (chars_per_block - 1)) // chars_per_block


def sms_price_per_100_chars() -> Decimal:
    raw_value = str(
        os.getenv("SMS_PRICE_PER_100_CHARS")
        or os.getenv("SMS_PRICE_PER_SEGMENT")
        or "185"
    ).strip()
    try:
        return Decimal(raw_value)
    except InvalidOperation:
        return Decimal("185")


def sms_text_with_footer(text: str) -> str:
    normalized = str(text or "").strip()
    if SMS_FOOTER_TEXT in normalized:
        return normalized
    return f"{normalized}\n\n{SMS_FOOTER_TEXT}" if normalized else SMS_FOOTER_TEXT


def sms_send_cost(text: str, recipients: list[str]) -> Decimal:
    price = sms_price_per_100_chars()
    blocks = sms_char_blocks(text)
    if price <= 0 or blocks <= 0 or not recipients:
        return Decimal("0")
    return (price * Decimal(blocks) * Decimal(len(recipients))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def sms_wallet_can_send(tenant: Organization | None, cost: Decimal) -> bool:
    if tenant is None or cost <= 0:
        return False
    ensure_organization_wallets(tenant)
    wallet = Wallet.objects.filter(organization=tenant, key="sms", is_active=True).first()
    if wallet is None:
        return False
    return Decimal(wallet.balance) >= cost and Decimal(wallet.balance) > 0


def charge_sms_wallet(tenant: Organization | None, actor: User | None, text: str, recipients: list[str], provider_id: str = "") -> None:
    if tenant is None:
        return
    amount = sms_send_cost(text, recipients)
    if amount <= 0:
        return
    with transaction.atomic():
        wallet = (
            Wallet.objects.select_for_update()
            .filter(organization=tenant, key="sms", is_active=True)
            .first()
        )
        if wallet is None:
            return
        current_balance = Decimal(wallet.balance)
        next_balance = current_balance - amount
        if next_balance < 0:
            return
        wallet.balance = next_balance
        wallet.updated_at = timezone.now()
        wallet.save(update_fields=["balance", "updated_at"])
        WalletTransaction.objects.create(
            organization=tenant,
            wallet=wallet,
            actor=actor,
            direction="out",
            transaction_type="sms_send",
            amount=amount,
            balance_after=next_balance,
            note=f"sms:{len(recipients)}:{sms_char_blocks(text)}",
            reference_id=provider_id[:80],
        )


def send_provider_sms(tenant, text, recipients, *, provider_config=None):
    config = provider_config or sms_provider_config()
    api_key = str(config.get("api_key", "") or "").strip()
    line_number = str(config.get("line_number", "") or "").strip()
    base_url = str(config.get("base_url", "https://api.iranpayamak.com") or "https://api.iranpayamak.com").rstrip("/")
    recipients = normalize_sms_recipients(recipients)
    text = str(text or "").strip()
    if not api_key or not line_number:
        message = "تنظیمات سرویس پیامک کامل نیست."
        return {"ok": False, "message": message, "provider_status": 0, "provider_data": {}, "raw_body": message, "payload": {}}
    if not text:
        message = "متن پیامک خالی است."
        return {"ok": False, "message": message, "provider_status": 0, "provider_data": {}, "raw_body": message, "payload": {}}
    if not recipients:
        message = "شماره موبایل معتبری برای ارسال پیامک ثبت نشده است."
        return {"ok": False, "message": message, "provider_status": 0, "provider_data": {}, "raw_body": message, "payload": {}}

    payload = {
        "text": text,
        "line_number": line_number,
        "recipients": recipients,
        "number_format": "english",
        "schedule": None,
    }
    req = urllib_request.Request(
        url=f"{base_url}/ws/v1/sms/simple",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Api-Key": api_key,
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=20) as response:
            raw_body = response.read().decode("utf-8")
            response_status = response.status
    except urllib_error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            provider_data = json.loads(raw_body or "{}") if raw_body else {}
        except json.JSONDecodeError:
            provider_data = {"message": raw_body}
        return {
            "ok": False,
            "message": provider_message_text(provider_data, fallback="سرویس پیامک درخواست را نپذیرفت."),
            "provider_status": exc.code,
            "provider_data": provider_data,
            "raw_body": raw_body,
            "payload": payload,
        }
    except urllib_error.URLError as exc:
        provider_response = str(getattr(exc, "reason", exc))
        return {
            "ok": False,
            "message": "ارتباط با سرویس پیامک برقرار نشد.",
            "provider_status": 0,
            "provider_data": {"message": provider_response},
            "raw_body": provider_response,
            "payload": payload,
        }

    try:
        provider_data = json.loads(raw_body or "{}") if raw_body else {}
    except json.JSONDecodeError:
        provider_data = {"status": "error", "message": raw_body}
    if response_status not in {200, 201} or str(provider_data.get("status") or "").lower() != "success":
        return {
            "ok": False,
            "message": provider_message_text(provider_data),
            "provider_status": response_status,
            "provider_data": provider_data,
            "raw_body": raw_body,
            "payload": payload,
        }

    data = provider_data.get("data")
    provider_id = str(data.get("id") or "") if isinstance(data, dict) else str(data or "")
    provider_delivery_status = str(data.get("status") or "") if isinstance(data, dict) else ""
    return {
        "ok": True,
        "message": "پیامک با موفقیت در صف ارسال قرار گرفت.",
        "provider_status": response_status,
        "provider_data": provider_data,
        "provider_id": provider_id,
        "provider_delivery_status": provider_delivery_status,
        "raw_body": raw_body,
        "payload": payload,
    }


def notify_sms(tenant: Organization | None, text: str, recipients, *, actor: User | None = None) -> dict:
    try:
        text = sms_text_with_footer(text)
        recipients = normalize_sms_recipients(recipients)
        if not recipients:
            message = "شماره موبایل معتبری برای ارسال پیامک ثبت نشده است."
            return {
                "ok": False,
                "message": message,
                "provider_status": 0,
                "provider_data": {"message": message},
                "raw_body": message,
                "payload": {"text": text, "recipients": recipients},
            }
        cost = sms_send_cost(text, recipients)
        if not sms_wallet_can_send(tenant, cost):
            message = "به دلیل عدم موجودی کیف پول پیامک، پیامک ارسال نشد."
            return {
                "ok": False,
                "message": message,
                "provider_status": 0,
                "provider_data": {"message": message},
                "raw_body": message,
                "payload": {"text": text, "recipients": recipients},
            }
        result = send_provider_sms(tenant, text, recipients)
        if result.get("ok"):
            charge_sms_wallet(
                tenant,
                actor,
                text,
                list(result.get("payload", {}).get("recipients") or recipients),
                provider_id=str(result.get("provider_id") or ""),
            )
        return result
    except Exception as exc:
        return {
            "ok": False,
            "message": "ارسال پیامک با خطا مواجه شد.",
            "provider_status": 0,
            "provider_data": {"message": str(exc)},
            "raw_body": str(exc),
            "payload": {},
        }


def notify_system_sms(text: str, recipients, *, actor: User | None = None) -> dict:
    """Send operational/system SMS without charging an organization SMS wallet."""
    try:
        text = sms_text_with_footer(text)
        recipients = normalize_sms_recipients(recipients)
        if not recipients:
            message = "شماره موبایل معتبری برای ارسال پیامک ثبت نشده است."
            return {
                "ok": False,
                "message": message,
                "provider_status": 0,
                "provider_data": {"message": message},
                "raw_body": message,
                "payload": {"text": text, "recipients": recipients},
            }
        return send_provider_sms(None, text, recipients)
    except Exception as exc:
        return {
            "ok": False,
            "message": "ارسال پیامک با خطا مواجه شد.",
            "provider_status": 0,
            "provider_data": {"message": str(exc)},
            "raw_body": str(exc),
            "payload": {},
        }


def json_response(payload, status=200, safe=True):
    return JsonResponse(payload, status=status, safe=safe, json_dumps_params=JSON_KWARGS)


ERROR_FIELD_PATTERNS = [
    ("title", "عنوان", ("عنوان",)),
    ("description", "شرح", ("شرح", "توضیح")),
    ("manager", "ارجاع گیرنده", ("مدیر", "ارجاع", "گیرنده")),
    ("amount", "مبلغ", ("مبلغ", "هزینه")),
    ("fullName", "نام کامل", ("نام کامل", "نام کاربر")),
    ("email", "ایمیل", ("ایمیل",)),
    ("password", "رمز عبور", ("رمز عبور",)),
    ("file", "فایل", ("فایل", "پیوست", "سند")),
    ("signatureData", "امضا", ("امضا",)),
    ("organizationName", "نام سازمان", ("سازمان", "مجموعه")),
]


def error_title(status: int) -> str:
    if status == 401:
        return "نیاز به ورود مجدد"
    if status == 403:
        return "دسترسی کافی نیست"
    if status == 404:
        return "موردی پیدا نشد"
    if status == 409:
        return "تداخل در اطلاعات"
    if status == 422:
        return "اطلاعات فرم نیاز به اصلاح دارد"
    if status >= 500:
        return "خطای داخلی سامانه"
    return "خطا در انجام عملیات"


def infer_error_fields(detail: str) -> list[dict]:
    fields = []
    for key, label, patterns in ERROR_FIELD_PATTERNS:
        if any(pattern in detail for pattern in patterns):
            fields.append({"field": key, "label": label, "message": detail})
    return fields


def json_error(detail: str, status=400, fields=None, title: str | None = None, suggestion: str | None = None):
    normalized_fields = fields if fields is not None else infer_error_fields(detail)
    payload = {
        "detail": detail,
        "title": title or error_title(status),
        "fields": normalized_fields,
        "suggestion": suggestion or ("فیلدهای مشخص شده را اصلاح کنید و دوباره ثبت کنید." if normalized_fields else "اطلاعات را بررسی کنید و دوباره تلاش کنید."),
    }
    return json_response(payload, status=status)


def parse_json(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


USER_SECTION_KEYS = ("users", "approvals", "expenses", "reports", "settings")


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
        {"key": "users", "title": "کاربران", "description": "مدیریت فهرست کاربران، نقش‌ها و دسترسی‌ها", "route": "/users"},
        {"key": "expenses", "title": "هزینه‌ها", "description": "ثبت، ارجاع، بررسی و کنترل هزینه‌ها", "route": "/expenses"},
        {"key": "reports", "title": "گزارشات", "description": "نمای مدیریتی و تحلیل عملکرد سازمان", "route": "/reports"},
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
        "systemId": str(organization.code or "").upper(),
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
        "departments": [
            {"id": item.id, "code": item.code, "name": item.name}
            for item in visible_department_catalog()
        ],
        "canEdit": can_manage_users(user),
    }


def user_can_access_wallet(user: User) -> bool:
    return user.slug == HQ_USERNAME or user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER}


def user_can_access_attendance(user: User) -> bool:
    if user.slug == HQ_USERNAME:
        return True
    if not is_manager(user):
        return False
    organization = get_user_organization(user)
    return FeaturePurchase.objects.filter(organization=organization, feature_key="attendance", is_active=True).exists()


def attendance_organization_for_user(user: User) -> Organization:
    return get_user_organization(user)


def attendance_user_queryset(organization: Organization):
    return (
        User.objects.filter(organization_membership__organization=organization, is_active=True)
        .select_related("department")
        .order_by("full_name")
    )


def attendance_current_status(user: User) -> str:
    last_event = user.attendance_events.order_by("-event_at", "-id").first()
    return last_event.event_type if last_event else AttendanceEvent.EVENT_OUT


def serialize_attendance_event(event: AttendanceEvent) -> dict:
    return {
        "id": event.id,
        "userId": event.user_id,
        "userName": event.user.full_name,
        "eventType": event.event_type,
        "event_type": event.event_type,
        "source": event.source,
        "note": event.note,
        "eventAt": event.event_at.isoformat(),
        "event_at": event.event_at.isoformat(),
    }


def serialize_attendance_user(user: User, organization: Organization) -> dict:
    today_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    events = list(
        AttendanceEvent.objects.filter(organization=organization, user=user, event_at__gte=today_start)
        .select_related("user")
        .order_by("event_at", "id")
    )
    worked_seconds = 0
    open_checkin = None
    for event in events:
        if event.event_type == AttendanceEvent.EVENT_IN:
            open_checkin = event.event_at
        elif event.event_type == AttendanceEvent.EVENT_OUT and open_checkin:
            worked_seconds += max((event.event_at - open_checkin).total_seconds(), 0)
            open_checkin = None
    if open_checkin:
        worked_seconds += max((timezone.now() - open_checkin).total_seconds(), 0)
    status = events[-1].event_type if events else attendance_current_status(user)
    return {
        "id": user.id,
        "name": user.full_name,
        "role": user.job_title,
        "department": user.department.name if user.department else "بدون واحد",
        "phone": user.phone or "",
        "avatar": user.avatar,
        "status": status,
        "todayEventsCount": len(events),
        "today_events_count": len(events),
        "todayWorkedHours": round(worked_seconds / 3600, 1),
        "today_worked_hours": round(worked_seconds / 3600, 1),
        "attendancePath": f"/attendance/{user.attendance_token}",
        "attendance_path": f"/attendance/{user.attendance_token}",
        "attendanceToken": user.attendance_token,
    }


def build_attendance_dashboard_payload(user: User) -> dict:
    organization = attendance_organization_for_user(user)
    users = list(attendance_user_queryset(organization))
    attendance_users = [serialize_attendance_user(item, organization) for item in users]
    today_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    recent_events = list(
        AttendanceEvent.objects.filter(organization=organization)
        .select_related("user")
        .order_by("-event_at", "-id")[:12]
    )
    present_count = sum(1 for item in attendance_users if item["status"] == AttendanceEvent.EVENT_IN)
    today_events = AttendanceEvent.objects.filter(organization=organization, event_at__gte=today_start)
    return {
        "organization": {"id": organization.id, "name": organization.name, "code": organization.code},
        "summary": {
            "usersCount": len(attendance_users),
            "users_count": len(attendance_users),
            "presentCount": present_count,
            "present_count": present_count,
            "absentCount": max(len(attendance_users) - present_count, 0),
            "absent_count": max(len(attendance_users) - present_count, 0),
            "todayEventsCount": today_events.count(),
            "today_events_count": today_events.count(),
            "todayWorkedHours": round(sum(float(item["todayWorkedHours"]) for item in attendance_users), 1),
            "today_worked_hours": round(sum(float(item["todayWorkedHours"]) for item in attendance_users), 1),
        },
        "users": attendance_users,
        "recentEvents": [serialize_attendance_event(item) for item in recent_events],
        "recent_events": [serialize_attendance_event(item) for item in recent_events],
    }


def parse_iso_date_param(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def build_attendance_report_payload(user: User, params) -> dict:
    organization = attendance_organization_for_user(user)
    events = AttendanceEvent.objects.filter(organization=organization).select_related("user", "user__department").order_by("-event_at", "-id")
    start_date = parse_iso_date_param(params.get("start"))
    end_date = parse_iso_date_param(params.get("end"))
    event_type = (params.get("eventType") or params.get("event_type") or "").strip()
    user_id = (params.get("userId") or params.get("user_id") or "").strip()
    query = (params.get("q") or "").strip()

    if start_date:
        events = events.filter(event_at__date__gte=start_date)
    if end_date:
        events = events.filter(event_at__date__lte=end_date)
    if event_type in {AttendanceEvent.EVENT_IN, AttendanceEvent.EVENT_OUT}:
        events = events.filter(event_type=event_type)
    if user_id.isdigit():
        events = events.filter(user_id=int(user_id))
    if query:
        events = events.filter(
            Q(user__full_name__icontains=query)
            | Q(user__job_title__icontains=query)
            | Q(user__department__name__icontains=query)
            | Q(note__icontains=query)
        )

    rows = list(events[:500])
    checkins = sum(1 for item in rows if item.event_type == AttendanceEvent.EVENT_IN)
    checkouts = sum(1 for item in rows if item.event_type == AttendanceEvent.EVENT_OUT)
    return {
        "summary": {
            "total": len(rows),
            "checkins": checkins,
            "checkouts": checkouts,
            "managerEvents": sum(1 for item in rows if item.source == AttendanceEvent.SOURCE_MANAGER),
            "linkEvents": sum(1 for item in rows if item.source == AttendanceEvent.SOURCE_LINK),
        },
        "rows": [
            {
                **serialize_attendance_event(item),
                "row": index + 1,
                "userRole": item.user.job_title,
                "userDepartment": item.user.department.name if item.user.department else "بدون واحد",
            }
            for index, item in enumerate(rows)
        ],
        "users": [
            {"id": item.id, "name": item.full_name}
            for item in attendance_user_queryset(organization)
        ],
    }


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


def feature_config(feature_key: str) -> dict | None:
    return next((item for item in PURCHASABLE_FEATURES if item["feature_key"] == feature_key), None)


def license_safe_path(path: str) -> bool:
    safe_paths = (
        "/api/v1/auth/me",
        "/api/v1/bootstrap",
        "/api/v1/wallet",
        "/api/v1/wallet/options",
        "/api/v1/wallet/purchases",
        "/api/v1/support",
        "/api/v1/hq",
    )
    return any(path.startswith(item) for item in safe_paths)


def user_license_locked(user: User) -> bool:
    if user.slug == HQ_USERNAME:
        return False
    return bool(license_status_payload(get_user_organization(user)).get("isLocked"))


def parse_user_amount(value, label: str) -> Decimal:
    try:
        amount = Decimal(str(value or 0).replace(",", "")).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"مقدار {label} معتبر نیست.")
    if amount < 0:
        raise ValueError(f"مقدار {label} نمی‌تواند منفی باشد.")
    return amount


def support_ticket_wallet_id(ticket: SupportTicket) -> int | None:
    for line in (ticket.message or "").splitlines():
        if not line.startswith("WALLET_ID:"):
            continue
        raw_value = line.split(":", 1)[1].strip()
        if raw_value.isdigit():
            return int(raw_value)
    return None


def support_ticket_withdrawal_source_wallet_id(ticket: SupportTicket) -> int | None:
    for line in (ticket.message or "").splitlines():
        if not line.startswith("SOURCE_WALLET_ID:"):
            continue
        raw_value = line.split(":", 1)[1].strip()
        if raw_value.isdigit():
            return int(raw_value)
    return None


def scoped_support_organization(request: HttpRequest) -> Organization | None:
    return resolve_wallet_organization(request)


def send_ticket_assigned_sms(ticket: SupportTicket) -> dict:
    assignee = getattr(ticket, "assigned_to", None)
    phone = (getattr(assignee, "phone", "") or "").strip()
    if not phone:
        return {"sent": False, "reason": "no_assignee_phone"}
    body = sms_join_lines(
        "کارنومند | تیکت جدید",
        f"شماره تیکت: {ticket.id}",
        f"موضوع: {ticket.subject}",
        f"مجموعه: {ticket.organization.name if ticket.organization_id else '-'}",
        f"آدرس سامانه: {public_app_url()}",
    )
    try:
        return notify_sms(ticket.organization, body, [phone], actor=None)
    except Exception as exc:
        return {"sent": False, "error": str(exc)}


def scoped_support_tickets(request: HttpRequest):
    organization = scoped_support_organization(request)
    include_internal = user_is_hq_user(request.current_user)
    base = (
        SupportTicket.objects.select_related("organization", "requester", "responded_by", "assigned_to", "registration_request")
        .prefetch_related("messages", "attachments")
        .order_by("-last_message_at", "-updated_at", "-id")
    )
    if user_is_hq_user(request.current_user) and organization is None:
        qs = base
        if not user_is_hq_admin(request.current_user):
            qs = qs.filter(Q(assigned_to=request.current_user) | Q(assigned_to__isnull=True))
        return qs
    if organization is None:
        return SupportTicket.objects.none()
    ticket_filter = Q(organization=organization)
    if user_is_hq_user(request.current_user):
        ticket_filter |= Q(registration_request__isnull=False)
    return base.filter(ticket_filter)


def ensure_signature(user: User) -> UserSignature:
    signature, _ = UserSignature.objects.get_or_create(
        user=user,
        defaults={"signature_data": "", "stamp_data": ""},
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
            "password_hash": get_password_hash("m11051386M!@"),
            "role": UserRole.ADMIN,
            "platform_role": PlatformRole.HQ_ADMIN,
            "job_title": "HQ",
            "avatar": "MD",
            "bio": "",
            "is_active": True,
            "department": department,
        },
    )
    update_fields = []
    if not created and not verify_password("m11051386M!@", user.password_hash):
        user.password_hash = get_password_hash("m11051386M!@")
        update_fields.append("password_hash")
    if user.role != UserRole.ADMIN:
        user.role = UserRole.ADMIN
        update_fields.append("role")
    if getattr(user, "platform_role", "") != PlatformRole.HQ_ADMIN:
        user.platform_role = PlatformRole.HQ_ADMIN
        update_fields.append("platform_role")
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
        if env_bool("WORKFLOW_ENFORCE_LICENSE_LOCK", False) and user_license_locked(user) and not license_safe_path(request.path):
            return json_error("برای استفاده از نرم افزار باید خرید اصلی ثبت و تایید شود.", status=402)
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
    ensure_required_login_users()
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
    identifier = (payload.get("email") or payload.get("username") or "").strip()
    password = payload.get("password") or ""
    identifier_lower = identifier.lower()
    identifier_slug = normalize_slug(identifier)

    user = None
    if identifier_lower:
        user = User.objects.select_related("department").filter(email=identifier_lower).first()
    if user is None and identifier_lower:
        user = User.objects.select_related("department").filter(slug=identifier_lower).first()
    if user is None and identifier_slug and identifier_slug != identifier_lower:
        user = User.objects.select_related("department").filter(slug=identifier_slug).first()
    if user is None and identifier_slug:
        user = User.objects.select_related("department").filter(email=f"{identifier_slug}@hq.local").first()

    if user is None or not user.is_active or getattr(user, "is_deleted", False) or not verify_password(password, user.password_hash):
        return json_error("نام کاربری/ایمیل یا رمز عبور نادرست است.", status=401)
    ensure_signature(user)
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])
    AuditLog.objects.create(actor=user, actor_name=user.full_name, action="login", entity_type="user", detail="ورود به سیستم", icon="login")
    token = create_access_token(str(user.id), {"role": user.role})
    return json_response({"access_token": token, "token_type": "bearer", "user": serialize_current_user(user)})


@require_auth
@methods("POST")
def logout_view(request: HttpRequest):
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="logout",
        entity_type="user",
        detail="خروج از سیستم",
        icon="logout",
    )
    return json_response({"ok": True})


def create_organization_with_manager(payload: dict, actor: User | None = None) -> Organization:
    organization_name = (payload.get("organizationName") or "").strip()
    organization_code = normalize_slug(payload.get("organizationCode") or organization_name)
    manager_name = (payload.get("managerName") or "").strip()
    manager_username = normalize_slug(payload.get("managerUsername") or "")
    manager_email = (payload.get("managerEmail") or "").strip().lower()
    manager_password = payload.get("managerPassword") or ""
    manager_phone = (payload.get("managerPhone") or "").strip()

    if not organization_name:
        raise ValueError("نام مجموعه الزامی است.")
    if not organization_code:
        raise ValueError("کد مجموعه معتبر نیست.")
    if not manager_name or not manager_username or not manager_password:
        raise ValueError("نام مدیر، نام کاربری و رمز عبور الزامی است.")
    if len(manager_password) < 6:
        raise ValueError("رمز عبور باید حداقل 6 کاراکتر باشد.")
    if not manager_email:
        manager_email = f"{manager_username}@{organization_code}.local"
    if Organization.objects.filter(code=organization_code).exists():
        raise IntegrityError("کد مجموعه قبلا ثبت شده است.")
    if Organization.objects.filter(name=organization_name).exists():
        raise IntegrityError("نام مجموعه قبلا ثبت شده است.")
    if User.objects.filter(slug=manager_username).exists():
        raise IntegrityError("نام کاربری مدیر قبلا ثبت شده است.")
    if User.objects.filter(email=manager_email).exists():
        raise IntegrityError("ایمیل مدیر قبلا ثبت شده است.")

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
            department=None,
        )
        OrganizationMembership.objects.create(organization=organization, user=manager, display_title=manager.job_title)
        OrganizationPreference.objects.get_or_create(organization=organization)
        UserSignature.objects.get_or_create(user=manager, defaults={"signature_data": ""})
        AuditLog.objects.create(
            actor=actor,
            actor_name=actor.full_name if actor else manager.full_name,
            action="hq_organization_created" if actor else "organization_registered",
            entity_type="organization",
            entity_code=organization.code,
            detail=organization.name,
            icon="domain_add",
        )
    notify_sms(
        organization,
        build_account_credentials_sms(
            full_name=manager.full_name,
            organization_name=organization.name,
            username=manager.slug,
            password=manager_password,
            role_label="مدیر مجموعه",
        ),
        [manager.phone],
        actor=actor,
    )
    return organization


@csrf_exempt
@methods("POST")
def register_view(request: HttpRequest):
    startup_ready()
    payload = request.POST
    organization_name = (payload.get("organizationName") or "").strip()
    manager_name = (payload.get("managerName") or "").strip()
    manager_username = normalize_slug(payload.get("managerUsername") or "")
    manager_email = (payload.get("managerEmail") or "").strip().lower()
    manager_phone = (payload.get("managerPhone") or "").strip()
    manager_password = payload.get("managerPassword") or ""
    documents = request.FILES.getlist("documents")

    if not organization_name or not manager_name or not manager_username or not manager_phone or not manager_password:
        return json_error("نام مجموعه، نام مدیر، نام کاربری، تلفن و رمز عبور الزامی است.", status=422)
    if len(manager_password) < 6:
        return json_error("رمز عبور باید حداقل ۶ کاراکتر باشد.", status=422)
    if not documents:
        return json_error("بارگذاری حداقل یک مدرک یا تصویر جواز الزامی است.", status=422)
    for document in documents:
        content_type = (getattr(document, "content_type", "") or "").lower()
        if content_type != "application/pdf" and not content_type.startswith("image/"):
            return json_error("مدارک فقط باید تصویر یا فایل PDF باشند.", status=422)
        if (getattr(document, "size", 0) or 0) > 10 * 1024 * 1024:
            return json_error("حجم هر مدرک نباید بیشتر از ۱۰ مگابایت باشد.", status=422)
    if Organization.objects.filter(name=organization_name).exists() or RegistrationRequest.objects.filter(organization_name=organization_name, status="pending").exists():
        return json_error("برای این نام مجموعه قبلاً درخواست ثبت شده است.", status=409)
    if User.objects.filter(slug=manager_username).exists() or RegistrationRequest.objects.filter(manager_username=manager_username, status="pending").exists():
        return json_error("این نام کاربری قبلاً استفاده شده است.", status=409)
    if manager_email and (User.objects.filter(email=manager_email).exists() or RegistrationRequest.objects.filter(manager_email=manager_email, status="pending").exists()):
        return json_error("این ایمیل قبلاً استفاده شده است.", status=409)

    with transaction.atomic():
        hq_organization, _ = Organization.objects.get_or_create(code="hq-control", defaults={"name": "HQ"})
        message = "\n".join([
            "درخواست خودکار ثبت مجموعه",
            f"نام مجموعه: {organization_name}",
            f"نام مدیر: {manager_name}",
            f"نام کاربری مدیر: {manager_username}",
            f"ایمیل مدیر: {manager_email or '-'}",
            f"تلفن مدیر: {manager_phone}",
            f"تعداد مدارک: {len(documents)}",
        ])
        ticket = SupportTicket.objects.create(
            organization=hq_organization,
            subject=f"ثبت‌نام مجموعه {organization_name}",
            message=message,
            category=SupportTicketCategory.ACCOUNT,
            priority=SupportTicketPriority.HIGH,
            status=SupportTicketStatus.OPEN,
            assigned_to=default_hq_support_user(),
            last_message_at=timezone.now(),
            updated_at=timezone.now(),
        )
        SupportMessage.objects.create(ticket=ticket, sender_name=manager_name, sender_platform_role="registration", body=message)
        RegistrationRequest.objects.create(
            ticket=ticket,
            organization_name=organization_name,
            manager_name=manager_name,
            manager_username=manager_username,
            manager_email=manager_email,
            manager_phone=manager_phone,
            manager_password_hash=get_password_hash(manager_password),
        )
        for document in documents:
            stored_name = save_uploaded_file(document)
            SupportAttachment.objects.create(
                ticket=ticket,
                original_name=document.name,
                stored_name=stored_name,
                mime_type=getattr(document, "content_type", "") or "",
                size_bytes=getattr(document, "size", 0) or 0,
            )
    if ticket.assigned_to_id:
        send_ticket_assigned_sms(ticket)
    return json_response({"ok": True, "message": "درخواست ثبت‌نام ارسال شد و پس از بررسی مدارک فعال می‌شود.", "ticketId": ticket.id}, status=201)


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
    if not user_is_hq_admin(user):
        return json_error("دسترسی HQ ادمین لازم است.", status=403)
    return None


def ensure_hq_staff(user: User):
    if not user_is_hq_user(user):
        return json_error("دسترسی HQ فقط برای حساب مرکزی فعال است.", status=403)
    return None


def hq_selected_user_ids(request: HttpRequest) -> list[int] | None:
    if not user_is_hq_user(request.current_user):
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
        .prefetch_related("assigned_managers", "assigned_employees", "attachments", "approval_assignments__approver")
        .order_by("-created_at")
    )


def scoped_expenses(request: HttpRequest):
    user_ids = hq_selected_user_ids(request)
    if user_ids is None:
        return visible_expenses(request.current_user)
    return (
        Expense.objects.filter(owner_id__in=user_ids)
        .select_related("owner", "department")
        .prefetch_related("approval_assignments__approver")
        .order_by("-expense_date", "-created_at")
    )


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


def parse_id_list(raw_value: str) -> list[int]:
    return [int(item) for item in str(raw_value or "").split(",") if item.strip().isdigit()]


def request_referral_users(request: HttpRequest, manager_slug: str, manager_assignee_ids: list[int], employee_assignee_ids: list[int]) -> tuple[User | None, list[User], list[User]]:
    manager = User.objects.filter(slug=manager_slug).first() if manager_slug else None
    assigned_managers = list(User.objects.filter(pk__in=manager_assignee_ids)) if manager_assignee_ids else []
    assigned_employees = list(User.objects.filter(pk__in=employee_assignee_ids)) if employee_assignee_ids else []
    if manager_assignee_ids and manager is None:
        raise ValueError("مدیر اصلی باید به درخواست ارجاع شود.")
    if manager_assignee_ids and (len(assigned_managers) != len(manager_assignee_ids) or any(not is_manager(item) for item in assigned_managers)):
        raise ValueError("مدیران ارجاعی باید از مدیران مجاز انتخاب شوند.")
    if employee_assignee_ids and (len(assigned_employees) != len(employee_assignee_ids) or any(is_manager(item) for item in assigned_employees)):
        raise ValueError("کارمندان ارجاعی باید از میان کارمندان مجاز انتخاب شوند.")
    if manager:
        assigned_managers = [item for item in assigned_managers if item.slug != manager.slug]
    return manager, assigned_managers, assigned_employees


def create_request_referrals(request_obj: Request, actor: User, manager: User | None, assigned_managers: list[User], assigned_employees: list[User]) -> None:
    if manager is not None:
        request_obj.manager = manager
        request_obj.save(update_fields=["manager"])
    if assigned_managers:
        request_obj.assigned_managers.add(*assigned_managers)
    if assigned_employees:
        request_obj.assigned_employees.add(*assigned_employees)
    created_assignments = []
    for approver in unique_users([manager] if manager else [], assigned_managers, assigned_employees):
        assignment, created = RequestApprovalAssignment.objects.get_or_create(
            request=request_obj,
            approver=approver,
            defaults={"status": ApprovalAssignmentStatus.PENDING},
        )
        if not created and assignment.status != ApprovalAssignmentStatus.PENDING:
            assignment.status = ApprovalAssignmentStatus.PENDING
            assignment.decision_note = ""
            assignment.acted_at = None
            assignment.save(update_fields=["status", "decision_note", "acted_at"])
        created_assignments.append((assignment, created))
    if any(created for _, created in created_assignments):
        request_obj.status = RequestStatus.UNDER_REVIEW
        request_obj.updated_at = timezone.now()
        request_obj.save(update_fields=["status", "updated_at"])
    RequestTimeline.objects.create(request=request_obj, action="referred", note="ارجاع مجدد درخواست", actor_name=actor.full_name)
    if assigned_managers:
        RequestTimeline.objects.create(request=request_obj, action="manager_referrals", note=f"ارجاع به مدیران: {', '.join(item.full_name for item in assigned_managers)}", actor_name=actor.full_name)
    if assigned_employees:
        RequestTimeline.objects.create(request=request_obj, action="employee_referrals", note=f"ارجاع به کارمندان: {', '.join(item.full_name for item in assigned_employees)}", actor_name=actor.full_name)
    recipients = [item.phone for item in unique_users([manager] if manager else [], assigned_managers, assigned_employees)]
    if recipients:
        org = get_user_organization(actor)
        notify_sms(
            org,
            build_workflow_event_sms(
                organization=org,
                headline="یک درخواست جدید به شما ارجاع شد.",
                details=[
                    f"کد درخواست: {request_obj.code}",
                    f"عنوان: {request_obj.title}",
                    f"ثبت‌کننده/ارجاع‌دهنده: {actor.full_name}",
                ],
                action_hint="لطفا وارد سامانه شوید و درخواست را بررسی کنید.",
            ),
            recipients,
            actor=actor,
        )


def create_expense_referrals(expense: Expense, actor: User, manager_assignee_ids: list[int], employee_assignee_ids: list[int]) -> None:
    assignee_ids = manager_assignee_ids + employee_assignee_ids
    assignees = list(User.objects.filter(pk__in=assignee_ids, organization_membership__organization=get_user_organization(actor)))
    if not assignees or len(assignees) != len(assignee_ids):
        raise ValueError("حداقل یک ارجاع گیرنده معتبر انتخاب کنید.")
    new_assignment_created = False
    for approver in unique_users(assignees):
        assignment, created = ExpenseApprovalAssignment.objects.get_or_create(
            expense=expense,
            approver=approver,
            defaults={"status": ApprovalAssignmentStatus.PENDING},
        )
        if not created and assignment.status != ApprovalAssignmentStatus.PENDING:
            assignment.status = ApprovalAssignmentStatus.PENDING
            assignment.decision_note = ""
            assignment.acted_at = None
            assignment.save(update_fields=["status", "decision_note", "acted_at"])
        new_assignment_created = new_assignment_created or created
    if new_assignment_created:
        expense.status = ExpenseStatus.UNDER_REVIEW
        expense.save(update_fields=["status"])
    AuditLog.objects.create(actor=actor, actor_name=actor.full_name, action="expense_referred", entity_type="expense", entity_code=expense.code, detail=expense.title, icon="forward_to_inbox")
    org = get_user_organization(actor)
    notify_sms(
        org,
        build_workflow_event_sms(
            organization=org,
            headline="یک هزینه جدید به شما ارجاع شد.",
            details=[
                f"کد هزینه: {expense.code}",
                f"شرح: {expense.title}",
                f"ارجاع‌دهنده: {actor.full_name}",
            ],
            action_hint="لطفا وارد سامانه شوید و هزینه را بررسی کنید.",
        ),
        [item.phone for item in unique_users(assignees)],
        actor=actor,
    )


def create_document_referrals(document: Document, actor: User, assignee_ids: list[int]) -> None:
    organization = get_user_organization(actor)
    normalized_ids = list(dict.fromkeys(assignee_ids))
    approvers = list(
        User.objects.filter(pk__in=normalized_ids, organization_membership__organization=organization)
    )
    if not approvers or len(approvers) != len(normalized_ids):
        raise ValueError("ارجاع گیرنده سند معتبر نیست.")
    created_any = False
    for approver in unique_users(approvers):
        assignment, created = ApprovalAssignment.objects.get_or_create(
            document=document,
            approver=approver,
            defaults={"status": ApprovalAssignmentStatus.PENDING},
        )
        if not created and assignment.status != ApprovalAssignmentStatus.PENDING:
            assignment.status = ApprovalAssignmentStatus.PENDING
            assignment.decision_note = ""
            assignment.signed_signature_data = ""
            assignment.acted_at = None
            assignment.save(update_fields=["status", "decision_note", "signed_signature_data", "acted_at"])
        created_any = created_any or created
    if created_any and document.status == DocumentStatus.REJECTED:
        document.status = DocumentStatus.PENDING
        document.rejection_reason = ""
        document.rejected_at = None
        document.approved_at = None
        document.save(update_fields=["status", "rejection_reason", "rejected_at", "approved_at"])
    AuditLog.objects.create(actor=actor, actor_name=actor.full_name, action="document_referred", entity_type="document", entity_code=document.code, detail=document.title, icon="forward_to_inbox")
    org = get_user_organization(actor)
    notify_sms(
        org,
        build_workflow_event_sms(
            organization=org,
            headline="یک سند/تأییدیه جدید به شما ارجاع شد.",
            details=[
                f"کد سند: {document.code}",
                f"عنوان: {document.title}",
                f"ارجاع‌دهنده: {actor.full_name}",
            ],
            action_hint="لطفا وارد سامانه شوید و سند را بررسی کنید.",
        ),
        [item.phone for item in unique_users(approvers)],
        actor=actor,
    )


def update_request_status_from_assignments(request_obj: Request) -> None:
    statuses = set(request_obj.approval_assignments.values_list("status", flat=True))
    if ApprovalAssignmentStatus.REJECTED in statuses:
        request_obj.status = RequestStatus.REJECTED
    elif statuses and statuses == {ApprovalAssignmentStatus.APPROVED}:
        request_obj.status = RequestStatus.APPROVED
    else:
        request_obj.status = RequestStatus.UNDER_REVIEW
    request_obj.updated_at = timezone.now()
    request_obj.save(update_fields=["status", "updated_at"])


def update_expense_status_from_assignments(expense: Expense) -> None:
    statuses = set(expense.approval_assignments.values_list("status", flat=True))
    if ApprovalAssignmentStatus.REJECTED in statuses:
        expense.status = ExpenseStatus.REJECTED
        expense.progress = 100
    elif statuses and statuses == {ApprovalAssignmentStatus.APPROVED}:
        expense.status = ExpenseStatus.APPROVED
        expense.progress = 100
    else:
        expense.status = ExpenseStatus.UNDER_REVIEW
        total = max(len(statuses), expense.approval_assignments.count(), 1)
        approved = expense.approval_assignments.filter(status=ApprovalAssignmentStatus.APPROVED).count()
        expense.progress = int((approved / total) * 80) + 10
    expense.save(update_fields=["status", "progress"])


def unique_users(*groups):
    seen = set()
    users = []
    for group in groups:
        for user in group or []:
            if user and user.id not in seen:
                seen.add(user.id)
                users.append(user)
    return users


@require_auth
@methods("GET")
def hq_panel_view(request: HttpRequest):
    denied = ensure_hq_staff(request.current_user)
    if denied:
        return denied
    if not user_is_hq_admin(request.current_user):
        close_stale_support_tickets()
        tickets = list(hq_ticket_queryset(request.current_user)[:300])
        open_tickets = sum(1 for item in tickets if item.status == SupportTicketStatus.OPEN)
        pending_tickets = sum(1 for item in tickets if item.status == SupportTicketStatus.PENDING)
        answered_tickets = sum(1 for item in tickets if item.status == SupportTicketStatus.ANSWERED)
        return json_response({
            "summary": {
                "organizations": 0,
                "users": 0,
                "activeUsers": 0,
                "payments": 0,
                "paymentTotal": "0.00",
                "paymentTotalRaw": 0,
                "pendingPaymentTotal": "0.00",
                "approvedPaymentTotal": "0.00",
                "openRequests": 0,
                "pendingDocuments": 0,
                "tickets": len(tickets),
                "openTickets": open_tickets,
                "pendingTickets": pending_tickets,
                "answeredTickets": answered_tickets,
                "auditEvents": 0,
            },
            "organizations": [],
            "users": [],
            "requests": [],
            "payments": [],
            "documents": [],
            "tickets": [serialize_support_ticket(item, include_internal=True) for item in tickets],
            "audits": [],
            "segments": {"roles": [], "payments": [], "requests": [], "documents": [], "tickets": []},
            "directories": {
                "organizations": [],
                "departments": [],
                "users": [],
                "roles": [],
                "requestStatuses": [],
                "expenseStatuses": [],
                "documentStatuses": [],
            },
        })
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
@methods("GET")
def wallet_options_view(request: HttpRequest):
    if not user_can_access_wallet(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    organization = resolve_wallet_organization(request)
    if request.current_user.slug == HQ_USERNAME and organization is None:
        return json_response(wallet_options_payload(None))
    if organization is None:
        return json_error("مجموعه پیدا نشد.", status=404)
    return json_response(wallet_options_payload(organization))


@require_auth
@methods("POST")
def wallet_purchase_view(request: HttpRequest):
    if not user_can_access_wallet(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)

    payload = parse_json(request)
    organization = resolve_wallet_organization(request, payload)
    if organization is None:
        return json_error("مجموعه پیدا نشد.", status=404)

    key = str(payload.get("featureKey") or payload.get("feature_key") or "").strip()
    config = feature_config(key)
    if config is None:
        return json_error("گزینه خرید معتبر نیست.", status=422)
    if config.get("disabled"):
        return json_error("این گزینه فعلا غیرفعال است.", status=422)

    payment_plan = str(payload.get("paymentPlan") or payload.get("payment_plan") or "cash").strip()
    if payment_plan not in {"cash", "installment"}:
        return json_error("روش پرداخت معتبر نیست.", status=422)

    total_amount = normalize_money(config["base_price"])
    requested_paid_amount = normalize_money(payload.get("paidAmount") or payload.get("paid_amount") or 0)
    if payment_plan == "cash":
        paid_amount = total_amount
    elif requested_paid_amount > 0:
        paid_amount = requested_paid_amount
    else:
        paid_amount = normalize_money(config.get("upfront_amount", 0) or config.get("monthly_installment_amount", 0))
    if paid_amount <= 0:
        return json_error("مبلغ پرداخت معتبر نیست.", status=422)

    wallet_id = payload.get("walletId") or payload.get("wallet_id")
    with transaction.atomic():
        wallet_qs = Wallet.objects.select_for_update().filter(organization=organization, is_active=True)
        wallet = wallet_qs.filter(pk=wallet_id).first() if wallet_id else wallet_qs.filter(key="main").first()
        if wallet is None:
            return json_error("کیف پول معتبر برای پرداخت پیدا نشد.", status=404)
        current_balance = Decimal(wallet.balance)
        if current_balance < paid_amount:
            return json_error("موجودی کیف پول برای خرید کافی نیست.", status=409)

        wallet.balance = current_balance - paid_amount
        wallet.updated_at = timezone.now()
        wallet.save(update_fields=["balance", "updated_at"])

        remaining_amount = max(total_amount - paid_amount, Decimal("0"))
        annual_amount = normalize_money(config.get("annual_subscription_amount", 0))
        annual_installment_months = int(config.get("annual_subscription_installment_months", 0) or 0)
        renewal_due_at = date.today() + timedelta(days=365) if remaining_amount <= 0 and annual_amount > 0 else None
        purchase, _ = FeaturePurchase.objects.update_or_create(
            organization=organization,
            feature_key=key,
            defaults={
                "title": config["title"],
                "payment_plan": payment_plan,
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "remaining_amount": remaining_amount,
                "next_installment_due_at": date.today() + timedelta(days=30) if payment_plan == "installment" and remaining_amount > 0 else None,
                "renewal_due_at": renewal_due_at,
                "annual_subscription_amount": annual_amount,
                "annual_subscription_installment_months": annual_installment_months,
                "is_active": True,
                "updated_at": timezone.now(),
            },
        )
        WalletTransaction.objects.create(
            organization=organization,
            wallet=wallet,
            actor=request.current_user,
            direction="out",
            transaction_type="feature_purchase",
            amount=paid_amount,
            balance_after=wallet.balance,
            note=f"{key}:{payment_plan}",
            reference_id=str(purchase.id),
        )
        AuditLog.objects.create(
            actor=request.current_user,
            actor_name=request.current_user.full_name,
            action="feature_purchase_activated",
            entity_type="feature_purchase",
            entity_code=purchase.feature_key,
            detail=f"{organization.code}:{payment_plan}:{format_money(paid_amount)}",
            icon="verified",
        )
    return json_response(wallet_dashboard_payload(organization), status=201)


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
@methods("GET")
def attendance_dashboard_view(request: HttpRequest):
    if not user_can_access_attendance(request.current_user):
        return json_error("برای استفاده از ماژول ورود و خروج باید این گزینه از کیف پول خریداری و فعال شود.", status=402)
    return json_response(build_attendance_dashboard_payload(request.current_user))


@require_auth
@methods("POST")
def attendance_event_view(request: HttpRequest):
    if not user_can_access_attendance(request.current_user):
        return json_error("برای استفاده از ماژول ورود و خروج باید این گزینه از کیف پول خریداری و فعال شود.", status=402)
    payload = parse_json(request)
    user_id = payload.get("userId") or payload.get("user_id")
    event_type = payload.get("eventType") or payload.get("event_type")
    if event_type not in {AttendanceEvent.EVENT_IN, AttendanceEvent.EVENT_OUT}:
        return json_error("نوع رویداد معتبر نیست.", status=422)
    organization = attendance_organization_for_user(request.current_user)
    target_user = attendance_user_queryset(organization).filter(pk=user_id).first()
    if target_user is None:
        return json_error("کاربر پیدا نشد.", status=404)
    event = AttendanceEvent.objects.create(
        organization=organization,
        user=target_user,
        event_type=event_type,
        source=AttendanceEvent.SOURCE_MANAGER,
        note=(payload.get("note") or "").strip(),
    )
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="attendance_event",
        entity_type="attendance",
        entity_code=str(target_user.id),
        detail=f"{target_user.full_name}: {'ورود' if event_type == AttendanceEvent.EVENT_IN else 'خروج'}",
        icon="badge",
    )
    return json_response({"event": serialize_attendance_event(event), **build_attendance_dashboard_payload(request.current_user)}, status=201)


@require_auth
@methods("GET")
def attendance_reports_view(request: HttpRequest):
    if not user_can_access_attendance(request.current_user):
        return json_error("برای استفاده از گزارشات ورود و خروج باید این گزینه از کیف پول خریداری و فعال شود.", status=402)
    return json_response(build_attendance_report_payload(request.current_user, request.GET))


@methods("GET", "POST")
@csrf_exempt
def public_attendance_view(request: HttpRequest, token: str):
    target_user = User.objects.select_related("department", "organization_membership__organization").filter(attendance_token=token, is_active=True).first()
    if target_user is None:
        return json_error("لینک ورود و خروج معتبر نیست.", status=404)
    organization = get_user_organization(target_user)
    if not FeaturePurchase.objects.filter(organization=organization, feature_key="attendance", is_active=True).exists():
        return json_error("ماژول ورود و خروج برای این سازمان فعال نیست.", status=402)

    if request.method == "POST":
        payload = parse_json(request)
        event_type = payload.get("eventType") or payload.get("event_type")
        if event_type not in {AttendanceEvent.EVENT_IN, AttendanceEvent.EVENT_OUT}:
            return json_error("نوع رویداد معتبر نیست.", status=422)
        AttendanceEvent.objects.create(
            organization=organization,
            user=target_user,
            event_type=event_type,
            source=AttendanceEvent.SOURCE_LINK,
            note=(payload.get("note") or "").strip(),
        )

    user_payload = serialize_attendance_user(target_user, organization)
    today_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    events = list(
        AttendanceEvent.objects.filter(organization=organization, user=target_user, event_at__gte=today_start)
        .select_related("user")
        .order_by("-event_at", "-id")
    )
    return json_response({
        "organization": {"name": organization.name, "code": organization.code},
        "user": user_payload,
        "events": [serialize_attendance_event(item) for item in events],
        "serverTime": timezone.now().isoformat(),
        "server_time": timezone.now().isoformat(),
    }, status=201 if request.method == "POST" else 200)


@require_auth
@methods("GET", "POST")
def support_tickets_view(request: HttpRequest):
    close_stale_support_tickets()
    organization = scoped_support_organization(request)
    if user_is_hq_user(request.current_user) and organization is None and request.method == "GET":
        tickets = scoped_support_tickets(request)
        return json_response(
            [serialize_support_ticket(ticket, include_internal=True) for ticket in tickets[:300]],
            safe=False,
        )
    if organization is None:
        return json_error("مجموعه پیدا نشد.", status=404)

    if request.method == "GET":
        tickets = scoped_support_tickets(request)
        include_internal = user_is_hq_user(request.current_user)
        return json_response(
            [serialize_support_ticket(ticket, include_internal=include_internal) for ticket in tickets],
            safe=False,
        )

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

    now_value = timezone.now()
    assignee = default_hq_support_user()
    with transaction.atomic():
        ticket = SupportTicket.objects.create(
            organization=organization,
            requester=request.current_user,
            subject=subject,
            message=message,
            category=category,
            priority=priority,
            status=SupportTicketStatus.OPEN,
            assigned_to=assignee,
            last_message_at=now_value,
            updated_at=now_value,
        )
        SupportMessage.objects.create(
            ticket=ticket,
            sender=request.current_user,
            sender_name=request.current_user.full_name,
            sender_platform_role="hq_support" if user_is_hq_user(request.current_user) else "tenant",
            body=message,
            is_internal=False,
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

    if assignee:
        send_ticket_assigned_sms(ticket)

    ticket = (
        SupportTicket.objects.select_related("organization", "requester", "responded_by", "assigned_to")
        .prefetch_related("messages", "attachments")
        .get(pk=ticket.id)
    )
    return json_response(serialize_support_ticket(ticket, include_detail=True, include_internal=user_is_hq_user(request.current_user)), status=201)


@require_auth
@methods("GET")
def support_ticket_detail_view(request: HttpRequest, ticket_id: int):
    close_stale_support_tickets()
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)
    include_internal = user_is_hq_user(request.current_user)
    return json_response(serialize_support_ticket(ticket, include_detail=True, include_internal=include_internal))


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
    is_hq = user_is_hq_user(request.current_user)
    with transaction.atomic():
        if body:
            SupportMessage.objects.create(
                ticket=ticket,
                sender=request.current_user,
                sender_name=request.current_user.full_name,
                sender_platform_role="hq_support" if is_hq else "tenant",
                body=body,
                is_internal=False,
            )
            ticket.last_message_at = now_value
        if close_ticket and is_hq:
            ticket.status = SupportTicketStatus.CLOSED
            ticket.closed_at = now_value
        elif is_hq:
            ticket.status = SupportTicketStatus.ANSWERED
            ticket.responded_by = request.current_user
            ticket.responded_at = now_value
            ticket.response_text = body or ticket.response_text
            if ticket.first_response_at is None:
                ticket.first_response_at = now_value
            if body:
                ticket.response_quality_score = response_quality_score(ticket, body)
            if not ticket.assigned_to_id:
                ticket.assigned_to = request.current_user
        else:
            ticket.status = SupportTicketStatus.OPEN
        ticket.updated_at = now_value
        ticket.save(
            update_fields=[
                "status",
                "responded_by",
                "responded_at",
                "first_response_at",
                "closed_at",
                "updated_at",
                "last_message_at",
                "response_text",
                "response_quality_score",
                "assigned_to",
            ]
        )
        if is_hq and ticket.assigned_to_id:
            recalculate_support_metrics(ticket.assigned_to)

    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    return json_response(serialize_support_ticket(ticket, include_detail=True, include_internal=is_hq))


@require_auth
@methods("POST")
def support_ticket_feedback_view(request: HttpRequest, ticket_id: int):
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)
    if ticket.status not in {SupportTicketStatus.CLOSED, SupportTicketStatus.ANSWERED}:
        return json_error("امتیازدهی فقط برای تیکت پاسخ‌داده‌شده یا بسته‌شده فعال است.", status=409)

    payload = parse_json(request)
    try:
        score = int(payload.get("score") or payload.get("customer_satisfaction") or 0)
    except (TypeError, ValueError):
        score = 0
    if score < 1 or score > 5:
        return json_error("امتیاز معتبر نیست.", status=422)

    ticket.customer_satisfaction = score
    ticket.customer_feedback = (payload.get("feedback") or payload.get("customer_feedback") or "").strip()
    ticket.updated_at = timezone.now()
    ticket.save(update_fields=["customer_satisfaction", "customer_feedback", "updated_at"])
    if ticket.assigned_to_id:
        recalculate_support_metrics(ticket.assigned_to)
    return json_response(serialize_support_ticket(ticket, include_detail=True, include_internal=False))


@require_auth
@methods("POST")
def support_ticket_approve_registration_view(request: HttpRequest, ticket_id: int):
    denied = ensure_hq_staff(request.current_user)
    if denied:
        return denied
    company_code = normalize_slug(parse_json(request).get("companyCode") or "")
    if not company_code:
        return json_error("کد شرکت الزامی است.", status=422)

    now_value = timezone.now()
    with transaction.atomic():
        registration = RegistrationRequest.objects.select_for_update().select_related("ticket").filter(ticket_id=ticket_id).first()
        if registration is None:
            return json_error("این تیکت درخواست ثبت‌نام نیست.", status=404)
        if registration.status != "pending":
            return json_error("این درخواست قبلاً بررسی شده است.", status=409)
        manager_email = registration.manager_email or f"{registration.manager_username}@{company_code}.local"
        if Organization.objects.filter(code=company_code).exists():
            return json_error("این کد شرکت قبلاً ثبت شده است.", status=409)
        if Organization.objects.filter(name=registration.organization_name).exists():
            return json_error("این نام مجموعه قبلاً ثبت شده است.", status=409)
        if User.objects.filter(slug=registration.manager_username).exists():
            return json_error("نام کاربری مدیر قبلاً ثبت شده است.", status=409)
        if User.objects.filter(email=manager_email).exists():
            return json_error("ایمیل مدیر قبلاً ثبت شده است.", status=409)

        organization = Organization.objects.create(code=company_code, name=registration.organization_name)
        manager = User.objects.create(
            slug=registration.manager_username,
            full_name=registration.manager_name,
            email=manager_email,
            phone=registration.manager_phone,
            password_hash=registration.manager_password_hash,
            role=UserRole.ADMIN,
            job_title="مدیر مجموعه",
            avatar=(registration.manager_name[:2] or "AD").upper(),
            bio="",
            is_active=True,
        )
        OrganizationMembership.objects.create(organization=organization, user=manager, display_title=manager.job_title)
        OrganizationPreference.objects.get_or_create(organization=organization)
        UserSignature.objects.get_or_create(user=manager, defaults={"signature_data": ""})

        registration.status = "approved"
        registration.company_code = company_code
        registration.reviewed_by = request.current_user
        registration.reviewed_at = now_value
        registration.created_organization = organization
        registration.save(update_fields=["status", "company_code", "reviewed_by", "reviewed_at", "created_organization"])
        ticket = registration.ticket
        SupportMessage.objects.create(ticket=ticket, sender=request.current_user, sender_name=request.current_user.full_name, sender_platform_role="hq_support", body=f"ثبت‌نام تأیید شد و مجموعه با کد {company_code} ساخته شد.")
        ticket.status = SupportTicketStatus.CLOSED
        ticket.responded_by = request.current_user
        ticket.responded_at = now_value
        ticket.first_response_at = ticket.first_response_at or now_value
        ticket.closed_at = now_value
        ticket.updated_at = now_value
        ticket.save(update_fields=["status", "responded_by", "responded_at", "first_response_at", "closed_at", "updated_at"])
        AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="registration_approved", entity_type="organization", entity_code=company_code, detail=registration.organization_name, icon="domain_add")

    notify_sms(
        organization,
        build_account_credentials_sms(
            full_name=manager.full_name,
            organization_name=organization.name,
            username=manager.slug,
            password="همان رمزی که هنگام ثبت‌نام وارد کرده‌اید",
            role_label="مدیر مجموعه",
        ),
        [manager.phone],
        actor=request.current_user,
    )
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    return json_response(serialize_support_ticket(ticket, include_detail=True))


@require_auth
@methods("POST")
def support_ticket_wallet_deposit_view(request: HttpRequest, ticket_id: int):
    denied = ensure_hq_staff(request.current_user)
    if denied:
        return denied
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)
    if ticket.category != SupportTicketCategory.FINANCIAL:
        return json_error("این تیکت برای عملیات کیف پول نیست.", status=409)
    payload = parse_json(request)
    amount = parse_wallet_amount(payload.get("amount"))
    if amount is None:
        return json_error("مبلغ معتبر نیست.", status=422)
    action_meta = serialize_support_ticket(ticket).get("actionMeta") or {}
    now_value = timezone.now()
    with transaction.atomic():
        if action_meta.get("actionType") == "wallet_withdrawal" and action_meta.get("destinationType") == "wallet":
            source_wallet_id = support_ticket_withdrawal_source_wallet_id(ticket)
            target_wallet_id = action_meta.get("targetWalletId")
            if not source_wallet_id or not target_wallet_id:
                return json_error("اطلاعات برداشت کامل نیست.", status=422)
            source_wallet = Wallet.objects.select_for_update().filter(pk=source_wallet_id, organization=ticket.organization, is_active=True).first()
            target_wallet = Wallet.objects.select_for_update().filter(pk=target_wallet_id, organization=ticket.organization, is_active=True).first()
            if source_wallet is None or target_wallet is None:
                return json_error("کیف پول مبدا یا مقصد پیدا نشد.", status=404)
            if Decimal(source_wallet.balance) < amount:
                return json_error("موجودی کیف پول مبدا کافی نیست.", status=409)
            source_wallet.balance = Decimal(source_wallet.balance) - amount
            source_wallet.updated_at = now_value
            source_wallet.save(update_fields=["balance", "updated_at"])
            target_wallet.balance = Decimal(target_wallet.balance) + amount
            target_wallet.updated_at = now_value
            target_wallet.save(update_fields=["balance", "updated_at"])
            WalletTransaction.objects.create(organization=ticket.organization, wallet=source_wallet, actor=request.current_user, direction="out", transaction_type="support_ticket_withdrawal", amount=amount, balance_after=source_wallet.balance, note=f"support_ticket:{ticket.id}:wallet_transfer_out", reference_id=str(payload.get("referenceId") or ticket.id))
            WalletTransaction.objects.create(organization=ticket.organization, wallet=target_wallet, actor=request.current_user, direction="in", transaction_type="support_ticket_deposit", amount=amount, balance_after=target_wallet.balance, note=f"support_ticket:{ticket.id}:wallet_transfer_in", reference_id=str(payload.get("referenceId") or ticket.id))
            entity_code = target_wallet.key
            message_body = f"انتقال بین کیف پول ها انجام شد. مبلغ: {format_money(amount)}"
        else:
            wallet_id = support_ticket_wallet_id(ticket)
            if wallet_id is None:
                return json_error("شناسه کیف پول در تیکت ثبت نشده است.", status=422)
            wallet = Wallet.objects.select_for_update().filter(pk=wallet_id, organization=ticket.organization, is_active=True).first()
            if wallet is None:
                return json_error("کیف پول پیدا نشد.", status=404)
            next_balance = Decimal(wallet.balance) + amount
            wallet.balance = next_balance
            wallet.updated_at = now_value
            wallet.save(update_fields=["balance", "updated_at"])
            WalletTransaction.objects.create(organization=ticket.organization, wallet=wallet, actor=request.current_user, direction="in", transaction_type="support_ticket_deposit", amount=amount, balance_after=next_balance, note=f"support_ticket:{ticket.id}", reference_id=str(payload.get("referenceId") or ticket.id))
            entity_code = wallet.key
            message_body = f"واریز کیف پول انجام شد. مبلغ: {format_money(amount)}"
        SupportMessage.objects.create(ticket=ticket, sender=request.current_user, sender_name=request.current_user.full_name, sender_platform_role="hq_support", body=message_body)
        ticket.status = SupportTicketStatus.ANSWERED
        ticket.responded_by = request.current_user
        ticket.responded_at = now_value
        if ticket.first_response_at is None:
            ticket.first_response_at = now_value
        ticket.updated_at = now_value
        ticket.save(update_fields=["status", "responded_by", "responded_at", "first_response_at", "updated_at"])
        AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="support_ticket_wallet_deposit", entity_type="wallet", entity_code=entity_code, detail=f"{ticket.organization.code}:{ticket.id}:{format_money(amount)}", icon="account_balance_wallet")
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    return json_response(serialize_support_ticket(ticket, include_detail=True))


@require_auth
@methods("POST")
def support_ticket_bank_withdraw_complete_view(request: HttpRequest, ticket_id: int):
    denied = ensure_hq_staff(request.current_user)
    if denied:
        return denied
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)
    action_meta = serialize_support_ticket(ticket).get("actionMeta") or {}
    if action_meta.get("actionType") != "wallet_withdrawal" or action_meta.get("destinationType") != "bank":
        return json_error("این تیکت از نوع برداشت بانکی نیست.", status=409)
    payload = parse_json(request)
    amount = parse_wallet_amount(payload.get("amount") or action_meta.get("amount"))
    if amount is None:
        return json_error("مبلغ معتبر نیست.", status=422)
    source_wallet_id = support_ticket_withdrawal_source_wallet_id(ticket)
    if source_wallet_id is None:
        return json_error("کیف پول مبدا در تیکت ثبت نشده است.", status=422)
    now_value = timezone.now()
    with transaction.atomic():
        source_wallet = Wallet.objects.select_for_update().filter(pk=source_wallet_id, organization=ticket.organization, is_active=True).first()
        if source_wallet is None:
            return json_error("کیف پول مبدا پیدا نشد.", status=404)
        if Decimal(source_wallet.balance) < amount:
            return json_error("موجودی کیف پول مبدا کافی نیست.", status=409)
        source_wallet.balance = Decimal(source_wallet.balance) - amount
        source_wallet.updated_at = now_value
        source_wallet.save(update_fields=["balance", "updated_at"])
        WalletTransaction.objects.create(organization=ticket.organization, wallet=source_wallet, actor=request.current_user, direction="out", transaction_type="support_ticket_bank_withdrawal", amount=amount, balance_after=source_wallet.balance, note=f"support_ticket:{ticket.id}:bank_withdrawal", reference_id=str(payload.get("referenceId") or ticket.id))
        SupportMessage.objects.create(ticket=ticket, sender=request.current_user, sender_name=request.current_user.full_name, sender_platform_role="hq_support", body=f"درخواست شما با موفقیت برداشت شد و مبلغ {format_money(amount)} به حساب شما با شماره شبا {action_meta.get('iban') or '-'} واریز شد.")
        ticket.status = SupportTicketStatus.ANSWERED
        ticket.responded_by = request.current_user
        ticket.responded_at = now_value
        if ticket.first_response_at is None:
            ticket.first_response_at = now_value
        ticket.updated_at = now_value
        ticket.save(update_fields=["status", "responded_by", "responded_at", "first_response_at", "updated_at"])
    ticket = scoped_support_tickets(request).filter(pk=ticket_id).first()
    return json_response(serialize_support_ticket(ticket, include_detail=True))


def hq_ticket_queryset(user: User):
    qs = (
        SupportTicket.objects.select_related("organization", "requester", "responded_by", "assigned_to", "registration_request")
        .prefetch_related("messages", "attachments")
        .order_by("-last_message_at", "-updated_at", "-id")
    )
    if not user_is_hq_admin(user):
        qs = qs.filter(Q(assigned_to=user) | Q(assigned_to__isnull=True))
    return qs


@require_auth
@methods("GET")
def hq_tickets_view(request: HttpRequest):
    denied = ensure_hq_staff(request.current_user)
    if denied:
        return denied
    close_stale_support_tickets()
    q = str(request.GET.get("q") or "").strip()
    status_filter = str(request.GET.get("status") or "all").strip().lower()
    priority_filter = str(request.GET.get("priority") or "all").strip().lower()
    organization_id = request.GET.get("organizationId") or request.GET.get("organization_id")

    queryset = hq_ticket_queryset(request.current_user)
    if status_filter == SupportTicketStatus.OPEN:
        queryset = queryset.exclude(status=SupportTicketStatus.CLOSED)
    elif status_filter in SupportTicketStatus.values:
        queryset = queryset.filter(status=status_filter)
    if priority_filter in SupportTicketPriority.values:
        queryset = queryset.filter(priority=priority_filter)
    if organization_id and str(organization_id).isdigit():
        queryset = queryset.filter(organization_id=int(organization_id))
    if q:
        queryset = queryset.filter(
            Q(subject__icontains=q)
            | Q(message__icontains=q)
            | Q(organization__name__icontains=q)
            | Q(requester__full_name__icontains=q)
            | Q(requester__slug__icontains=q)
        )
    return json_response([serialize_support_ticket(ticket, include_internal=True) for ticket in queryset[:300]], safe=False)


@require_auth
@methods("GET")
def hq_ticket_detail_view(request: HttpRequest, ticket_id: int):
    denied = ensure_hq_staff(request.current_user)
    if denied:
        return denied
    close_stale_support_tickets()
    ticket = hq_ticket_queryset(request.current_user).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)
    return json_response(serialize_support_ticket(ticket, include_detail=True, include_internal=True))


@require_auth
@methods("POST")
def hq_ticket_message_view(request: HttpRequest, ticket_id: int):
    denied = ensure_hq_staff(request.current_user)
    if denied:
        return denied
    ticket = hq_ticket_queryset(request.current_user).filter(pk=ticket_id).first()
    if ticket is None:
        return json_error("تیکت پیدا نشد.", status=404)

    payload = parse_json(request)
    body = (payload.get("body") or "").strip()
    if not body:
        return json_error("متن پیام الزامی است.", status=422)

    status_value = (payload.get("status") or "").strip()
    if status_value and status_value not in SupportTicketStatus.values:
        return json_error("وضعیت معتبر نیست.", status=422)
    is_internal = bool(payload.get("isInternal") or payload.get("is_internal"))
    assign_to_user_id = payload.get("assignToUserId") or payload.get("assign_to_user_id")

    previous_assignee = ticket.assigned_to
    now_value = timezone.now()
    with transaction.atomic():
        if assign_to_user_id:
            assignee = User.objects.filter(
                pk=assign_to_user_id,
                platform_role__in=[PlatformRole.HQ_ADMIN, PlatformRole.HQ_SUPPORT],
                is_active=True,
                is_deleted=False,
            ).first()
            if assignee:
                ticket.assigned_to = assignee
        elif not ticket.assigned_to_id:
            ticket.assigned_to = request.current_user

        message = SupportMessage.objects.create(
            ticket=ticket,
            sender=request.current_user,
            sender_name=request.current_user.full_name,
            sender_platform_role="hq_support",
            body=body,
            is_internal=is_internal,
        )
        ticket.last_message_at = message.created_at
        if not is_internal:
            ticket.response_text = body
            ticket.responded_by = request.current_user
            ticket.responded_at = message.created_at
            if not ticket.first_response_at:
                ticket.first_response_at = message.created_at
            if status_value:
                ticket.status = status_value
                if status_value == SupportTicketStatus.CLOSED:
                    ticket.closed_at = message.created_at
            else:
                ticket.status = SupportTicketStatus.ANSWERED
            ticket.response_quality_score = response_quality_score(ticket, body)
        elif status_value:
            ticket.status = status_value
            if status_value == SupportTicketStatus.CLOSED:
                ticket.closed_at = message.created_at
        ticket.updated_at = now_value
        ticket.save(
            update_fields=[
                "assigned_to",
                "response_text",
                "responded_by",
                "first_response_at",
                "responded_at",
                "last_message_at",
                "status",
                "closed_at",
                "response_quality_score",
                "updated_at",
            ]
        )
        if previous_assignee and previous_assignee.id != ticket.assigned_to_id:
            recalculate_support_metrics(previous_assignee)
        if ticket.assigned_to_id:
            recalculate_support_metrics(ticket.assigned_to)

    ticket = hq_ticket_queryset(request.current_user).filter(pk=ticket_id).first()
    return json_response(serialize_support_ticket(ticket, include_detail=True, include_internal=True), status=201)


@require_auth
@methods("GET", "POST")
def hq_team_view(request: HttpRequest):
    denied = ensure_hq_staff(request.current_user)
    if denied:
        return denied

    if request.method == "GET":
        users = (
            User.objects.filter(platform_role__in=[PlatformRole.HQ_ADMIN, PlatformRole.HQ_SUPPORT], is_deleted=False)
            .order_by("platform_role", "full_name")
        )
        return json_response([serialize_hq_team_member(user) for user in users], safe=False)

    denied_admin = ensure_hq_admin(request.current_user)
    if denied_admin:
        return denied_admin

    payload = parse_json(request)
    full_name = (payload.get("fullName") or payload.get("full_name") or "").strip()
    username = normalize_slug(payload.get("username") or payload.get("slug") or "")
    phone = (payload.get("phone") or "").strip()
    email = (payload.get("email") or "").strip().lower() or f"{username}@hq.local"
    password = (payload.get("password") or "").strip() or "Support123!"
    if not full_name or not username:
        return json_error("نام و نام کاربری الزامی است.", status=422)
    if not phone:
        return json_error("شماره موبایل پشتیبان برای ارسال پیامک مشخصات ورود الزامی است.", status=422)
    if not normalize_sms_recipients([phone]):
        return json_error("شماره موبایل پشتیبان معتبر نیست.", status=422)
    if User.objects.filter(slug=username).exists():
        return json_error("نام کاربری قبلاً ثبت شده است.", status=409)
    if User.objects.filter(email=email).exists():
        return json_error("ایمیل قبلاً ثبت شده است.", status=409)

    hq_org = Organization.objects.filter(code="hq-control").first()
    hq_dept = Department.objects.filter(code="hq-control").first()
    user = User.objects.create(
        slug=username,
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=get_password_hash(password),
        role=UserRole.ADMIN,
        platform_role=PlatformRole.HQ_SUPPORT,
        job_title="پشتیبان مرکزی",
        avatar=(full_name[:2] or "SP").upper(),
        bio="",
        is_active=True,
        department=hq_dept,
    )
    if hq_org:
        OrganizationMembership.objects.update_or_create(user=user, defaults={"organization": hq_org, "display_title": "پشتیبان مرکزی"})

    sms_result = notify_system_sms(
        build_account_credentials_sms(
            full_name=full_name,
            organization_name="پنل مرکزی کارنومند",
            username=username,
            password=password,
            role_label="پشتیبان مرکزی",
        ),
        [phone],
        actor=request.current_user,
    )
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="hq_support_created",
        entity_type="user",
        entity_code=username,
        detail=f"{full_name} | sms:{'ok' if sms_result.get('ok') else 'failed'}",
        icon="support_agent",
    )
    payload_out = serialize_hq_team_member(user)
    payload_out["smsSent"] = bool(sms_result.get("ok"))
    payload_out["smsMessage"] = sms_result.get("message") or ""
    return json_response(payload_out, status=201)


@require_auth
@methods("PATCH", "DELETE")
def hq_team_detail_view(request: HttpRequest, user_id: int):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied

    user = User.objects.filter(pk=user_id, platform_role=PlatformRole.HQ_SUPPORT, is_deleted=False).first()
    if user is None:
        return json_error("پشتیبان پیدا نشد.", status=404)

    if request.method == "DELETE":
        SupportTicket.objects.filter(assigned_to=user).update(assigned_to=None)
        user.is_active = False
        user.is_deleted = True
        user.deleted_at = timezone.now()
        user.deleted_by = request.current_user
        user.save(update_fields=["is_active", "is_deleted", "deleted_at", "deleted_by"])
        return json_response({"softDeleted": True})

    payload = parse_json(request)
    update_fields = []
    if "fullName" in payload or "full_name" in payload:
        user.full_name = (payload.get("fullName") or payload.get("full_name") or user.full_name).strip()
        user.avatar = (user.full_name[:2] or "SP").upper()
        update_fields.extend(["full_name", "avatar"])
    if "username" in payload or "slug" in payload:
        username = normalize_slug(payload.get("username") or payload.get("slug") or "")
        if username and username != user.slug:
            if User.objects.exclude(pk=user.pk).filter(slug=username).exists():
                return json_error("نام کاربری قبلاً ثبت شده است.", status=409)
            user.slug = username
            update_fields.append("slug")
    if "phone" in payload:
        user.phone = (payload.get("phone") or "").strip()
        update_fields.append("phone")
    if "email" in payload and payload.get("email"):
        email = str(payload.get("email")).strip().lower()
        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            return json_error("ایمیل قبلاً ثبت شده است.", status=409)
        user.email = email
        update_fields.append("email")
    if "isActive" in payload or "is_active" in payload:
        user.is_active = bool(payload.get("isActive") if "isActive" in payload else payload.get("is_active"))
        update_fields.append("is_active")
    if payload.get("password"):
        user.password_hash = get_password_hash(str(payload.get("password")))
        update_fields.append("password_hash")
    if update_fields:
        user.save(update_fields=list(dict.fromkeys(update_fields)))

    sms_result = None
    if payload.get("password") and user.phone:
        sms_result = notify_system_sms(
            build_account_credentials_sms(
                full_name=user.full_name,
                organization_name="پنل مرکزی کارنومند",
                username=user.slug,
                password=str(payload.get("password")),
                role_label="پشتیبان مرکزی",
            ),
            [user.phone],
            actor=request.current_user,
        )

    payload_out = serialize_hq_team_member(user)
    if sms_result is not None:
        payload_out["smsSent"] = bool(sms_result.get("ok"))
        payload_out["smsMessage"] = sms_result.get("message") or ""
    return json_response(payload_out)


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


def build_internal_user_email(username: str) -> str:
    normalized_username = normalize_slug(username) or "user"
    email = f"{normalized_username}@workflow.local"
    suffix = 2
    while User.objects.filter(email=email).exists():
        email = f"{normalized_username}-{suffix}@workflow.local"
        suffix += 1
    return email


def organization_identity_conflict(code: str, name: str, exclude_id: int | None = None) -> HttpResponse | None:
    code_qs = Organization.objects.filter(code=code)
    name_qs = Organization.objects.filter(name=name)
    if exclude_id is not None:
        code_qs = code_qs.exclude(pk=exclude_id)
        name_qs = name_qs.exclude(pk=exclude_id)
    if code_qs.exists():
        return json_error("کد مجموعه قبلا ثبت شده است.", status=409)
    if name_qs.exists():
        return json_error("نام مجموعه قبلا ثبت شده است.", status=409)
    return None


def user_identity_conflict(username: str, email: str, exclude_id: int | None = None) -> HttpResponse | None:
    username_qs = User.objects.filter(slug=username)
    email_qs = User.objects.filter(email=email)
    if exclude_id is not None:
        username_qs = username_qs.exclude(pk=exclude_id)
        email_qs = email_qs.exclude(pk=exclude_id)
    if username_qs.exists():
        return json_error("این نام کاربری قبلا ثبت شده است.", status=409)
    if email_qs.exists():
        return json_error("شناسه داخلی کاربر تکراری است.", status=409)
    return None


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
    conflict = organization_identity_conflict(organization_code, organization_name)
    if conflict:
        return conflict

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
def hq_organization_create_view(request: HttpRequest):
    denied = ensure_hq_admin(request.current_user)
    if denied:
        return denied
    try:
        create_organization_with_manager(parse_json(request), actor=request.current_user)
    except ValueError as exc:
        return json_error(str(exc), status=422)
    except IntegrityError as exc:
        return json_error(str(exc), status=409)
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
    code = normalize_slug(payload.get("code") or organization.code)
    conflict = organization_identity_conflict(code, name or organization.name, exclude_id=organization.id)
    if conflict:
        return conflict
    if name:
        organization.name = name
    if code:
        organization.code = code
    try:
        organization.save(update_fields=["name", "code"])
    except IntegrityError:
        return json_error("کد یا نام مجموعه تکراری است.", status=409)
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
    if "username" in payload or "slug" in payload:
        target.slug = normalize_slug(payload.get("username") or payload.get("slug") or target.slug)
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
    password = (payload.get("password") or "").strip()
    if password:
        if len(password) < 6:
            return json_error("رمز عبور باید حداقل 6 کاراکتر باشد.", status=422)
        target.password_hash = get_password_hash(password)
    conflict = user_identity_conflict(target.slug, target.email, exclude_id=target.id)
    if conflict:
        return conflict
    target.avatar = (target.full_name[:2] if target.full_name else target.avatar or "NA").upper()
    try:
        target.save()
    except IntegrityError:
        return json_error("نام کاربری یا شناسه کاربر تکراری است.", status=409)

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
        amount = parse_wallet_amount(payload.get("amount"))
        if amount is None:
            return json_error("مبلغ معتبر نیست.", status=422)
        target.amount = amount
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
        items = list(visible_requests(request.current_user))
        for item in items:
            item._current_user = request.current_user
        return json_response([serialize_request(item) for item in items], safe=False)

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
        return json_error("اقدام درخواست معتبر نیست.", status=422)
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
        "approve": ("approved", "تایید درخواست"),
        "reject": ("rejected", "رد درخواست"),
        "refer": ("referred", "ارجاع درخواست"),
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
    if manager:
        assigned_managers = [item for item in assigned_managers if item.slug != manager.slug]
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
    for approver in unique_users([manager] if manager else [], assigned_managers, assigned_employees):
        RequestApprovalAssignment.objects.create(
            request=request_obj,
            approver=approver,
            status=ApprovalAssignmentStatus.PENDING,
        )

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

    request_obj = Request.objects.select_related("requester", "manager", "department").prefetch_related("assigned_managers", "assigned_employees", "attachments", "approval_assignments__approver").get(pk=request_obj.pk)
    request_obj._current_user = request.current_user
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="request_created", entity_type="request", entity_code=request_obj.code, detail=request_obj.title, icon="assignment")
    org = get_user_organization(request.current_user)
    notify_sms(
        org,
        build_workflow_event_sms(
            organization=org,
            headline="یک درخواست جدید به شما ارجاع شد.",
            details=[
                f"کد درخواست: {request_obj.code}",
                f"عنوان: {request_obj.title}",
                f"ثبت‌کننده: {request.current_user.full_name}",
            ],
            action_hint="لطفا وارد سامانه شوید و درخواست را بررسی کنید.",
        ),
        [item.phone for item in unique_users([manager] if manager else [], assigned_managers, assigned_employees)],
        actor=request.current_user,
    )
    return json_response(serialize_request(request_obj), status=201)


@require_auth
@methods("GET")
def request_detail_view(request: HttpRequest, request_code: str):
    request_obj = scoped_requests(request).filter(code=request_code).first()
    if request_obj is None:
        return json_error("درخواست پیدا نشد.", status=404)
    request_obj._current_user = request.current_user
    return json_response({"request": serialize_request(request_obj), "timeline": []})


@require_auth
@methods("GET")
def request_attachment_view(request: HttpRequest, request_code: str, attachment_id: int):
    request_obj = scoped_requests(request).filter(code=request_code).first()
    if request_obj is None:
        return json_error("درخواست پیدا نشد.", status=404)
    attachment = request_obj.attachments.filter(pk=attachment_id).first()
    if attachment is None:
        return json_error("فایل پیدا نشد.", status=404)
    file_path = Path(settings.MEDIA_ROOT) / attachment.stored_name
    if not file_path.exists():
        return json_error("فایل موجود نیست.", status=404)
    content_type, _ = mimetypes.guess_type(file_path.name)
    response = FileResponse(file_path.open("rb"), content_type=content_type or attachment.mime_type or "application/octet-stream")
    response["Content-Disposition"] = f'inline; filename="{attachment.original_name}"'
    return response


@require_auth
@csrf_exempt
@methods("POST")
def request_approve_view(request: HttpRequest, request_code: str):
    request_obj = scoped_requests(request).filter(code=request_code).first()
    if request_obj is None:
        return json_error("درخواست پیدا نشد.", status=404)

    assignment = request_obj.approval_assignments.filter(approver=request.current_user).first()
    if assignment is None or assignment.status != ApprovalAssignmentStatus.PENDING or request_obj.status not in {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW}:
        return json_error("این درخواست به شما ارجاع نشده یا قبلا تعیین تکلیف شده است.", status=403)

    assignment.status = ApprovalAssignmentStatus.APPROVED
    assignment.decision_note = ""
    assignment.acted_at = timezone.now()
    assignment.save(update_fields=["status", "decision_note", "acted_at"])
    update_request_status_from_assignments(request_obj)
    RequestTimeline.objects.create(request=request_obj, action="approved", note="تایید درخواست", actor_name=request.current_user.full_name)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="request_approved", entity_type="request", entity_code=request_obj.code, detail=request_obj.title, icon="assignment_turned_in")
    org = get_user_organization(request.current_user)
    notify_sms(
        org,
        build_workflow_event_sms(
            organization=org,
            headline="وضعیت درخواست شما به‌روزرسانی شد.",
            details=[
                f"کد درخواست: {request_obj.code}",
                f"عنوان: {request_obj.title}",
                f"نتیجه: تایید توسط {request.current_user.full_name}",
                f"وضعیت فعلی: {request_obj.get_status_display()}",
            ],
        ),
        [request_obj.requester.phone],
        actor=request.current_user,
    )
    return json_response({"status": request_obj.status, "request": request_obj.code})


@require_auth
@csrf_exempt
@methods("POST")
def request_reject_view(request: HttpRequest, request_code: str):
    request_obj = scoped_requests(request).filter(code=request_code).first()
    if request_obj is None:
        return json_error("درخواست پیدا نشد.", status=404)

    payload = parse_json(request)
    reason = (payload.get("reason") or "").strip()
    if not reason:
        return json_error("علت رد الزامی است.", status=422)

    assignment = request_obj.approval_assignments.filter(approver=request.current_user).first()
    if assignment is None or assignment.status != ApprovalAssignmentStatus.PENDING or request_obj.status not in {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW}:
        return json_error("این درخواست به شما ارجاع نشده یا قبلا تعیین تکلیف شده است.", status=403)

    assignment.status = ApprovalAssignmentStatus.REJECTED
    assignment.decision_note = reason
    assignment.acted_at = timezone.now()
    assignment.save(update_fields=["status", "decision_note", "acted_at"])
    update_request_status_from_assignments(request_obj)
    RequestTimeline.objects.create(request=request_obj, action="rejected", note=reason, actor_name=request.current_user.full_name)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="request_rejected", entity_type="request", entity_code=request_obj.code, detail=request_obj.title, icon="cancel")
    org = get_user_organization(request.current_user)
    notify_sms(
        org,
        build_workflow_event_sms(
            organization=org,
            headline="وضعیت درخواست شما به‌روزرسانی شد.",
            details=[
                f"کد درخواست: {request_obj.code}",
                f"عنوان: {request_obj.title}",
                f"نتیجه: رد توسط {request.current_user.full_name}",
                f"علت: {reason}",
            ],
        ),
        [request_obj.requester.phone],
        actor=request.current_user,
    )
    return json_response({"status": "rejected", "request": request_obj.code})


@require_auth
@csrf_exempt
@methods("POST")
def request_refer_view(request: HttpRequest, request_code: str):
    request_obj = scoped_requests(request).filter(code=request_code).first()
    if request_obj is None:
        return json_error("درخواست پیدا نشد.", status=404)
    assignment = request_obj.approval_assignments.filter(approver=request.current_user, status=ApprovalAssignmentStatus.PENDING).first()
    if assignment is None:
        return json_error("فقط ارجاع گیرنده فعلی می‌تواند درخواست را ارجاع مجدد کند.", status=403)
    payload = parse_json(request)
    try:
        manager, assigned_managers, assigned_employees = request_referral_users(
            request_obj,
            (payload.get("manager") or "").strip(),
            [int(item) for item in payload.get("managerAssigneeIds", []) if str(item).isdigit()],
            [int(item) for item in payload.get("employeeAssigneeIds", []) if str(item).isdigit()],
        )
        if not any([manager, assigned_managers, assigned_employees]):
            return json_error("حداقل یک ارجاع گیرنده انتخاب کنید.", status=422)
        create_request_referrals(request_obj, request.current_user, manager, assigned_managers, assigned_employees)
    except ValueError as exc:
        return json_error(str(exc), status=422)
    refreshed_request = scoped_requests(request).get(pk=request_obj.pk)
    refreshed_request._current_user = request.current_user
    return json_response(serialize_request(refreshed_request))


@require_auth
@csrf_exempt
@methods("GET", "POST")
def expenses_view(request: HttpRequest):
    if not can_access_expenses(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    if request.method == "GET":
        items = list(visible_expenses(request.current_user))
        for item in items:
            item._current_user = request.current_user
        return json_response([serialize_expense(item) for item in items], safe=False)

    description = request.POST.get("description", "").strip()
    amount = request.POST.get("amount", "0")
    expense_date_raw = request.POST.get("expenseDate", "").strip()
    if not expense_date_raw:
        return json_error("تاریخ هزینه الزامی است.", status=422)
    expense_date = date.fromisoformat(expense_date_raw)
    if expense_date > date.today():
        return json_error("انتخاب تاریخ آینده مجاز نیست.", status=422)
    if not description:
        return json_error("شرح هزینه الزامی است.", status=422)
    parsed_amount = parse_wallet_amount(amount)
    if parsed_amount is None:
        return json_error("مبلغ معتبر نیست.", status=422)

    department_code = request.POST.get("department", "").strip()
    assignee_ids = [int(item) for item in request.POST.get("assigneeIds", "").split(",") if item.strip().isdigit()]
    assignee_ids += [int(item) for item in request.POST.get("managerAssigneeIds", "").split(",") if item.strip().isdigit()]
    assignee_ids += [int(item) for item in request.POST.get("employeeAssigneeIds", "").split(",") if item.strip().isdigit()]
    assignee_ids = list(dict.fromkeys(assignee_ids))
    if not assignee_ids:
        return json_error("حداقل یک ارجاع گیرنده انتخاب کنید.", status=422)
    assignees = list(User.objects.filter(pk__in=assignee_ids, organization_membership__organization=get_user_organization(request.current_user)))
    if len(assignees) != len(assignee_ids):
        return json_error("ارجاع گیرنده معتبر نیست.", status=422)

    invoice = request.FILES.get("invoice")
    invoice_name = save_uploaded_file(invoice) if invoice else None
    department = Department.objects.exclude(code__in=["hq-control", "hq"]).filter(code=department_code).first() or request.current_user.department
    expense = Expense.objects.create(
        code=next_code("EXP"),
        title=(description[:180] or "هزینه جدید"),
        amount=parsed_amount,
        category=ExpenseCategory.MISCELLANEOUS,
        status=ExpenseStatus.UNDER_REVIEW,
        progress=10,
        expense_date=expense_date,
        notes=description,
        department=department,
        owner=request.current_user,
        invoice_file_name=invoice_name,
    )
    for approver in unique_users(assignees):
        ExpenseApprovalAssignment.objects.create(expense=expense, approver=approver, status=ApprovalAssignmentStatus.PENDING)
    expense = Expense.objects.select_related("owner", "department").prefetch_related("approval_assignments__approver").get(pk=expense.pk)
    expense._current_user = request.current_user
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="expense_created", entity_type="expense", entity_code=expense.code, detail=expense.title, icon="payments")
    org = get_user_organization(request.current_user)
    notify_sms(
        org,
        build_workflow_event_sms(
            organization=org,
            headline="یک هزینه جدید به شما ارجاع شد.",
            details=[
                f"کد هزینه: {expense.code}",
                f"شرح: {expense.title}",
                f"ثبت‌کننده: {request.current_user.full_name}",
            ],
            action_hint="لطفا وارد سامانه شوید و هزینه را بررسی کنید.",
        ),
        [item.phone for item in unique_users(assignees)],
        actor=request.current_user,
    )
    return json_response(serialize_expense(expense), status=201)


@require_auth
@methods("GET")
def expense_detail_view(request: HttpRequest, expense_code: str):
    if not can_access_expenses(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    expense = scoped_expenses(request).filter(code=expense_code).first()
    if expense is None:
        return json_error("هزینه پیدا نشد.", status=404)
    expense._current_user = request.current_user
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

    assignment = expense.approval_assignments.filter(approver=request.current_user).first()
    if assignment is None or assignment.status != ApprovalAssignmentStatus.PENDING or expense.status not in {ExpenseStatus.PENDING, ExpenseStatus.UNDER_REVIEW}:
        return json_error("این هزینه به شما ارجاع نشده یا قبلا تعیین تکلیف شده است.", status=403)

    assignment.status = ApprovalAssignmentStatus.APPROVED
    assignment.decision_note = ""
    assignment.acted_at = timezone.now()
    assignment.save(update_fields=["status", "decision_note", "acted_at"])
    update_expense_status_from_assignments(expense)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="expense_approved", entity_type="expense", entity_code=expense.code, detail=expense.title, icon="payments")
    org = get_user_organization(request.current_user)
    notify_sms(
        org,
        build_workflow_event_sms(
            organization=org,
            headline="وضعیت هزینه شما به‌روزرسانی شد.",
            details=[
                f"کد هزینه: {expense.code}",
                f"شرح: {expense.title}",
                f"نتیجه: تایید توسط {request.current_user.full_name}",
                f"وضعیت فعلی: {expense.get_status_display()}",
            ],
        ),
        [expense.owner.phone],
        actor=request.current_user,
    )
    return json_response({"status": expense.status, "expense": expense.code})


@require_auth
@csrf_exempt
@methods("POST")
def expense_reject_view(request: HttpRequest, expense_code: str):
    if not can_access_expenses(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    expense = scoped_expenses(request).filter(code=expense_code).first()
    if expense is None:
        return json_error("هزینه پیدا نشد.", status=404)

    payload = parse_json(request)
    reason = (payload.get("reason") or "").strip()
    if not reason:
        return json_error("علت رد الزامی است.", status=422)

    assignment = expense.approval_assignments.filter(approver=request.current_user).first()
    if assignment is None or assignment.status != ApprovalAssignmentStatus.PENDING or expense.status not in {ExpenseStatus.PENDING, ExpenseStatus.UNDER_REVIEW}:
        return json_error("این هزینه به شما ارجاع نشده یا قبلا تعیین تکلیف شده است.", status=403)

    assignment.status = ApprovalAssignmentStatus.REJECTED
    assignment.decision_note = reason
    assignment.acted_at = timezone.now()
    assignment.save(update_fields=["status", "decision_note", "acted_at"])
    expense.notes = f"{expense.notes or expense.title}\n\nعلت رد: {reason}"
    expense.save(update_fields=["notes"])
    update_expense_status_from_assignments(expense)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="expense_rejected", entity_type="expense", entity_code=expense.code, detail=expense.title, icon="payments")
    org = get_user_organization(request.current_user)
    notify_sms(
        org,
        build_workflow_event_sms(
            organization=org,
            headline="وضعیت هزینه شما به‌روزرسانی شد.",
            details=[
                f"کد هزینه: {expense.code}",
                f"شرح: {expense.title}",
                f"نتیجه: رد توسط {request.current_user.full_name}",
                f"علت: {reason}",
            ],
        ),
        [expense.owner.phone],
        actor=request.current_user,
    )
    return json_response({"status": "rejected", "expense": expense.code})


@require_auth
@csrf_exempt
@methods("POST")
def expense_refer_view(request: HttpRequest, expense_code: str):
    if not can_access_expenses(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    expense = scoped_expenses(request).filter(code=expense_code).first()
    if expense is None:
        return json_error("هزینه پیدا نشد.", status=404)
    assignment = expense.approval_assignments.filter(approver=request.current_user, status=ApprovalAssignmentStatus.PENDING).first()
    if assignment is None:
        return json_error("فقط ارجاع گیرنده فعلی می‌تواند هزینه را ارجاع مجدد کند.", status=403)
    payload = parse_json(request)
    try:
        create_expense_referrals(
            expense,
            request.current_user,
            [int(item) for item in payload.get("managerAssigneeIds", []) if str(item).isdigit()],
            [int(item) for item in payload.get("employeeAssigneeIds", []) if str(item).isdigit()],
        )
    except ValueError as exc:
        return json_error(str(exc), status=422)
    refreshed_expense = scoped_expenses(request).get(pk=expense.pk)
    refreshed_expense._current_user = request.current_user
    return json_response(serialize_expense(refreshed_expense))


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
    username = normalize_slug(payload.get("username") or payload.get("slug") or "")
    conflict = user_identity_conflict(username, (payload.get("email") or "").strip().lower() or build_internal_user_email(username)) if username else None
    if not username:
        return json_error("نام کاربری الزامی است.", status=422)
    if conflict:
        return conflict
    if User.objects.filter(slug=username).exists():
        return json_error("این نام کاربری قبلا ثبت شده است.", status=409)
    email = (payload.get("email") or "").strip().lower() or build_internal_user_email(username)
    if User.objects.filter(email=email).exists():
        return json_error("شناسه داخلی کاربر تکراری است.", status=409)

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
        slug=username,
        full_name=full_name,
        email=email,
        phone=(payload.get("phone") or "").strip() or None,
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
    notify_sms(
        get_user_organization(request.current_user),
        build_account_credentials_sms(
            full_name=user.full_name,
            organization_name=organization.name,
            username=user.slug,
            password=password,
            role_label=user.job_title or ("مدیر" if role != UserRole.EMPLOYEE else "کارمند"),
        ),
        [user.phone],
        actor=request.current_user,
    )
    return json_response(serialize_user(user), status=201)


@require_auth
@csrf_exempt
@methods("PATCH")
def user_detail_view(request: HttpRequest, user_id: int):
    if not can_manage_users(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)

    allowed_ids = set(visible_users(request.current_user).values_list("id", flat=True))
    if user_id not in allowed_ids:
        return json_error("کاربر مورد نظر یافت نشد.", status=404)

    user = User.objects.select_related("department", "manager").filter(pk=user_id).first()
    if not user:
        return json_error("کاربر مورد نظر یافت نشد.", status=404)

    payload = parse_json(request)
    username = normalize_slug(payload.get("username") or payload.get("slug") or user.slug)
    conflict = user_identity_conflict(username, (payload.get("email") or user.email).strip().lower() or user.email, exclude_id=user.pk) if username else None
    if not username:
        return json_error("نام کاربری الزامی است.", status=422)
    if conflict:
        return conflict
    if User.objects.exclude(pk=user.pk).filter(slug=username).exists():
        return json_error("این نام کاربری قبلا ثبت شده است.", status=409)
    email = (payload.get("email") or user.email).strip().lower() or user.email
    if User.objects.exclude(pk=user.pk).filter(email=email).exists():
        return json_error("شناسه داخلی کاربر تکراری است.", status=409)

    manager_id = payload.get("managerId")
    manager = None
    if manager_id:
        manager = User.objects.filter(pk=manager_id).first()
        if not manager or manager.id == user.id or manager.id not in allowed_ids:
            return json_error("مدیر انتخاب شده معتبر نیست.", status=422)

    department = None
    department_code = (payload.get("department") or payload.get("departmentCode") or "").strip()
    if department_code:
        department = Department.objects.filter(code=department_code).first()

    role = payload.get("accessRole") or user.role
    try:
        bonus_delta = parse_user_amount(payload.get("bonusDelta", 0), "پاداش")
        penalty_delta = parse_user_amount(payload.get("penaltyDelta", 0), "جریمه")
    except ValueError as exc:
        return json_error(str(exc), status=422)
    user.full_name = (payload.get("fullName") or user.full_name).strip()
    user.slug = username
    user.email = email
    user.phone = (payload.get("phone") or "").strip() or None
    user.role = role
    user.job_title = (payload.get("jobTitle") or user.job_title).strip() or user.job_title
    user.department = department
    user.manager = manager
    user.bonus_amount = Decimal(user.bonus_amount or 0) + bonus_delta
    user.penalty_amount = Decimal(user.penalty_amount or 0) + penalty_delta
    if bonus_delta or penalty_delta:
        user.finance_updated_at = timezone.now()
    if "isActive" in payload:
        user.is_active = bool(payload.get("isActive"))
    user.avatar = (user.full_name[:2] if user.full_name else user.avatar or "NA").upper()
    update_fields = ["full_name", "slug", "email", "phone", "role", "job_title", "department", "manager", "bonus_amount", "penalty_amount", "is_active", "avatar"]
    if bonus_delta or penalty_delta:
        update_fields.append("finance_updated_at")

    password = (payload.get("password") or "").strip()
    if password:
        user.password_hash = get_password_hash(password)
        update_fields.append("password_hash")

    try:
        user.save(update_fields=update_fields)
    except IntegrityError:
        return json_error("نام کاربری یا شناسه داخلی کاربر تکراری است.", status=409)
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
        file_name, content = render_report_export(
            report_key,
            request.current_user,
            organization_id,
            {
                "period": request.GET.get("period", ""),
                "startDate": request.GET.get("startDate", ""),
                "endDate": request.GET.get("endDate", ""),
                "userId": request.GET.get("userId", ""),
            },
        )
    except ValueError as exc:
        return json_error(str(exc), status=404)

    response = HttpResponse(f"\ufeff{content}", content_type="text/csv; charset=utf-8")
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
        has_stamp = bool((signature.stamp_data or "").strip())
        return json_response(
            {
                "hasSignature": has_signature,
                "signatureData": signature.signature_data if has_signature else "",
                "hasStamp": has_stamp,
                "stampData": signature.stamp_data if has_stamp else "",
            }
        )

    payload = parse_json(request)
    signature_data = (payload.get("signatureData") or "").strip()
    stamp_data = (payload.get("stampData") or "").strip()
    if not has_saved_signature(signature_data):
        return json_error("امضای معتبر ثبت نشده است.", status=422)
    try:
        normalized_signature = normalize_signature_data_url(signature_data)
    except ValueError as exc:
        return json_error(str(exc), status=422)
    normalized_stamp = ""
    if stamp_data:
        try:
            normalized_stamp = normalize_stamp_data_url(stamp_data)
        except ValueError as exc:
            return json_error(str(exc), status=422)
    signature.signature_data = normalized_signature
    signature.stamp_data = normalized_stamp
    signature.updated_at = timezone.now()
    signature.save(update_fields=["signature_data", "stamp_data", "updated_at"])
    return json_response(
        {
            "hasSignature": True,
            "signatureData": signature.signature_data,
            "hasStamp": bool((signature.stamp_data or "").strip()),
            "stampData": signature.stamp_data,
        }
    )


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
        return json_error("حداقل یک دریافت کننده باید انتخاب شود.", status=422)

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
    try:
        create_document_referrals(document, request.current_user, assignee_ids)
    except ValueError as exc:
        document.delete()
        return json_error(str(exc), status=422)
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
        org = get_user_organization(document.owner)
        notify_sms(
            org,
            build_workflow_event_sms(
                organization=org,
                headline="وضعیت سند/تأییدیه شما به‌روزرسانی شد.",
                details=[
                    f"کد سند: {document.code}",
                    f"عنوان: {document.title}",
                    "نتیجه: تایید شد",
                ],
            ),
            [document.owner.phone],
            actor=request.current_user,
        )
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
        return json_error("\u0627\u0645\u0636\u0627\u06cc \u062f\u06cc\u062c\u06cc\u062a\u0627\u0644 \u0645\u0639\u062a\u0628\u0631 \u062e\u0648\u062f \u0631\u0627 \u062b\u0628\u062a \u06a9\u0646\u06cc\u062f.", status=422)
    if document.status == DocumentStatus.REJECTED:
        return json_error("این سند قبلا رد شده است و دیگر قابل تایید نیست.", status=409)

    try:
        with transaction.atomic():
            assignment.status = ApprovalAssignmentStatus.APPROVED
            assignment.decision_note = ""
            assignment.acted_at = timezone.now()
            assignment.save(update_fields=["status", "decision_note", "acted_at"])
            update_fields = []
            if document.file_name:
                document.file_name, assignment.signed_signature_data = sign_document_file(document, assignment, signature.signature_data, signature.stamp_data)
                update_fields.append("signed_signature_data")
                document.save(update_fields=["file_name"])
            else:
                _, assignment.signed_signature_data = build_approval_mark(signature.signature_data, signature.stamp_data)
                update_fields.append("signed_signature_data")
            if update_fields:
                assignment.save(update_fields=update_fields)
            update_document_status(document)
    except (ValueError, FileNotFoundError) as exc:
        return json_error(str(exc), status=422)
    except Exception:
        return json_error("امضای سند با خطا مواجه شد.", status=500)
    notify_sms(
        get_user_organization(request.current_user),
        build_workflow_event_sms(
            organization=get_user_organization(request.current_user),
            headline="وضعیت سند/تأییدیه شما به‌روزرسانی شد.",
            details=[
                f"کد سند: {document.code}",
                f"عنوان: {document.title}",
                f"نتیجه: تایید توسط {request.current_user.full_name}",
                f"وضعیت فعلی: {document.get_status_display()}",
            ],
        ),
        [document.owner.phone],
        actor=request.current_user,
    )
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
    if not reason:
        return json_error("علت رد الزامی است.", status=422)
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
        org = get_user_organization(document.owner)
        notify_sms(
            org,
            build_workflow_event_sms(
                organization=org,
                headline="وضعیت سند/تأییدیه شما به‌روزرسانی شد.",
                details=[
                    f"کد سند: {document.code}",
                    f"عنوان: {document.title}",
                    "نتیجه: رد شد",
                    f"علت: {reason}",
                ],
            ),
            [document.owner.phone],
            actor=request.current_user,
        )
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
    notify_sms(
        get_user_organization(request.current_user),
        build_workflow_event_sms(
            organization=get_user_organization(request.current_user),
            headline="وضعیت سند/تأییدیه شما به‌روزرسانی شد.",
            details=[
                f"کد سند: {document.code}",
                f"عنوان: {document.title}",
                f"نتیجه: رد توسط {request.current_user.full_name}",
                f"علت: {reason}",
            ],
        ),
        [document.owner.phone],
        actor=request.current_user,
    )
    return json_response({"status": "rejected", "document": document.code})


@require_auth
@csrf_exempt
@methods("POST")
def approval_refer_view(request: HttpRequest, document_code: str):
    if not can_access_approvals(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    document = scoped_documents(request).filter(code=document_code).first()
    if document is None:
        return json_error("سند پیدا نشد.", status=404)
    assignment = document.approval_assignments.filter(approver=request.current_user, status=ApprovalAssignmentStatus.PENDING).first()
    if assignment is None:
        return json_error("فقط ارجاع گیرنده فعلی می‌تواند سند را ارجاع مجدد کند.", status=403)
    payload = parse_json(request)
    assignee_ids = [int(item) for item in payload.get("assigneeIds", []) if str(item).isdigit()]
    if not assignee_ids:
        return json_error("حداقل یک ارجاع گیرنده انتخاب کنید.", status=422)
    try:
        create_document_referrals(document, request.current_user, assignee_ids)
    except ValueError as exc:
        return json_error(str(exc), status=422)
    return json_response(serialize_approval(scoped_documents(request).get(pk=document.pk), request.current_user))


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
        if section_key not in USER_SECTION_KEYS:
            return json_error("بخش دسترسی معتبر نیست.", status=422)
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
        submitted_ids: set[int] = set()
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
                submitted_ids.add(department.id)
            else:
                code = normalize_slug(item.get("code") or name) or f"department-{Department.objects.count() + 1}"
                base_code = code
                index = 2
                while Department.objects.filter(code=code).exists():
                    code = f"{base_code}-{index}"
                    index += 1
                if Department.objects.filter(name=name).exists():
                    return json_error("نام بخش تکراری است.", status=409)
                department = Department.objects.create(code=code, name=name)
                submitted_ids.add(department.id)
        Department.objects.exclude(code__in=["hq-control", "hq"]).exclude(name__iexact="HQ").exclude(id__in=submitted_ids).delete()
    else:
        organization_name = (payload.get("organizationName") or "").strip()
        system_id = normalize_slug(payload.get("systemId") or organization.code)
        if not organization_name:
            return json_error("نام سازمان الزامی است.", status=422)
        if not system_id:
            return json_error("کدنوم سازمان الزامی است.", status=422)
        if Organization.objects.exclude(pk=organization.pk).filter(code=system_id).exists():
            return json_error("کدنوم سازمان تکراری است.", status=409)
        organization.name = organization_name
        organization.code = system_id
        organization.save(update_fields=["name", "code"])

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
        return json_error("دسترسی کافی ندارید.", status=403)
    return json_response(
        [
            {"title": "حساب کاربری", "description": "مدیریت نقش ها و دسترسی"},
            {"title": "اسناد", "description": "گردش کار امضای دیجیتال"},
            {"title": "هزینه ها", "description": "ثبت، پیگیری و کنترل هزینه"},
            {"title": "گزارشات", "description": "تحلیل مدیریتی"},
        ],
        safe=False,
    )
