from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch, Q

from workflow.access import can_access_approvals, can_access_expenses, can_access_settings, can_access_users, can_approve_documents, can_manage_users, can_view_reports, get_user_organization, is_manager, organization_users, visible_users
from workflow.models import (
    ApprovalAssignment,
    ApprovalAssignmentStatus,
    AuditLog,
    Department,
    Document,
    DocumentRisk,
    DocumentStatus,
    Expense,
    ExpenseApprovalAssignment,
    ExpenseCategory,
    ExpenseStatus,
    FeaturePurchase,
    Organization,
    OrganizationMembership,
    OrganizationPreference,
    Request,
    RequestApprovalAssignment,
    RequestAttachment,
    RequestPriority,
    RequestStatus,
    RequestTimeline,
    SupportAttachment,
    SupportMessage,
    SupportTicket,
    SupportTicketStatus,
    User,
    UserRole,
    Wallet,
    WalletTransaction,
)

PERSIAN_WEEK_DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه شنبه", "چهارشنبه", "پنج شنبه", "جمعه"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
PDF_EXTENSIONS = {".pdf"}
HQ_USERNAME = "milad_dhs"
CORE_FEATURE_KEY = "core_software"
PURCHASABLE_FEATURES = [
    {
        "feature_key": CORE_FEATURE_KEY,
        "title": "خرید نرم افزار",
        "subtitle": "دسترسی پایه سامانه",
        "description": "تا زمانی که این گزینه فعال نشود، دسترسی عملیاتی سازمان قفل می ماند.",
        "accent": "#315f9f",
        "base_price": Decimal("4000000"),
        "upfront_amount": Decimal("1000000"),
        "monthly_installment_amount": Decimal("500000"),
        "installment_months": 6,
        "annual_subscription_amount": Decimal("1500000"),
        "annual_subscription_installment_months": 3,
        "annual_subscription_installment_amount": Decimal("500000"),
        "renewal_after_months": 12,
        "required": True,
    },
    {
        "feature_key": "cloud_storage",
        "title": "فضای ابری",
        "subtitle": "نگهداری و مدیریت فایل های سازمانی",
        "description": "بخش فضای ابری برای مشاهده، پیگیری و بارگذاری اسناد سازمانی.",
        "accent": "#287a6e",
        "base_price": Decimal("12000000"),
        "monthly_installment_amount": Decimal("2500000"),
        "installment_months": 5,
        "required": False,
    },
    {
        "feature_key": "attendance",
        "title": "ورود و خروج",
        "subtitle": "لاگین، خروج و کنترل نشست",
        "description": "فعال سازی کامل گزینه های ورود و خروج و کنترل دسترسی کاربران.",
        "accent": "#8a5b23",
        "base_price": Decimal("8000000"),
        "monthly_installment_amount": Decimal("2000000"),
        "installment_months": 4,
        "required": False,
    },
    {
        "feature_key": "accounting",
        "title": "حسابداری",
        "subtitle": "مدیریت مالی و گزارش های حسابداری",
        "description": "این گزینه فعلا غیرفعال است و پس از آماده سازی امکان خرید آن فعال می شود.",
        "accent": "#183153",
        "base_price": Decimal("0"),
        "monthly_installment_amount": Decimal("0"),
        "installment_months": 0,
        "required": False,
        "disabled": True,
        "disabled_label": "غیرفعال",
    },
]


def now():
    return datetime.now(timezone.utc)


def format_money(value: Decimal | int | float | str) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:,.2f}"


def normalize_money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_date(value):
    if not value:
        return ""
    return value.isoformat()


def relative_time(value: datetime) -> str:
    delta = now() - value.astimezone(timezone.utc)
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return "اخیرا"
    hours = minutes // 60
    if hours < 24:
        return "امروز"
    days = hours // 24
    if days < 7:
        return f"{days} روز قبل"
    return value.date().isoformat()


def access_role_label(role: str) -> str:
    return {
        UserRole.ADMIN: "مدیرعامل",
        UserRole.EXECUTIVE_MANAGER: "مدیر ارشد",
        UserRole.MANAGER: "مدیر",
        UserRole.EMPLOYEE: "کارمند",
    }[role]


def normalize_person_name(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("آرمان کریمی", "امید کریمی")


def priority_label(value: str) -> str:
    return dict(RequestPriority.choices).get(value, value)


def request_status_label(value: str) -> str:
    return dict(RequestStatus.choices).get(value, value)


def expense_status_label(value: str) -> str:
    return dict(ExpenseStatus.choices).get(value, value)


def expense_category_label(value: str) -> str:
    return dict(ExpenseCategory.choices).get(value, value)


def document_status_label(value: str) -> str:
    return dict(DocumentStatus.choices).get(value, value)


def document_risk_label(value: str) -> str:
    return dict(DocumentRisk.choices).get(value, value)


def assignment_status_label(value: str) -> str:
    return dict(ApprovalAssignmentStatus.choices).get(value, value)


def visible_department_catalog():
    return Department.objects.exclude(code__in=["hq-control", "hq"]).exclude(name__iexact="HQ").exclude(code__endswith="-admin").order_by("name")


def parse_support_ticket_meta(ticket: SupportTicket) -> dict:
    try:
        registration = ticket.registration_request
    except ObjectDoesNotExist:
        registration = None
    if registration is not None:
        return {
            "actionType": "organization_registration",
            "status": registration.status,
            "organizationName": registration.organization_name,
            "managerName": registration.manager_name,
            "managerUsername": registration.manager_username,
            "managerEmail": registration.manager_email,
            "managerPhone": registration.manager_phone,
            "companyCode": registration.company_code,
            "canApprove": registration.status == "pending",
        }
    meta = {}
    for line in (ticket.message or "").splitlines():
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip().upper()
        value = raw_value.strip()
        if key:
            meta[key] = value
    action_type = meta.get("ACTION_TYPE", "")
    if action_type == "wallet_withdrawal":
        return {
            "actionType": action_type,
            "sourceWalletId": int(meta["SOURCE_WALLET_ID"]) if meta.get("SOURCE_WALLET_ID", "").isdigit() else None,
            "sourceWalletName": meta.get("SOURCE_WALLET_NAME", ""),
            "destinationType": meta.get("DESTINATION_TYPE", ""),
            "targetWalletId": int(meta["TARGET_WALLET_ID"]) if meta.get("TARGET_WALLET_ID", "").isdigit() else None,
            "targetWalletName": meta.get("TARGET_WALLET_NAME", ""),
            "iban": meta.get("IBAN", ""),
            "amount": meta.get("AMOUNT", ""),
            "note": meta.get("NOTE", ""),
        }
    if action_type == "wallet_payment":
        return {
            "actionType": action_type,
            "walletId": int(meta["WALLET_ID"]) if meta.get("WALLET_ID", "").isdigit() else None,
            "walletName": meta.get("WALLET_NAME", ""),
            "amount": meta.get("AMOUNT", ""),
            "purpose": meta.get("PURPOSE", ""),
            "method": meta.get("METHOD", ""),
        }
    return {}


def save_uploaded_file(file_obj) -> str:
    unique_name = f"{uuid4().hex}-{file_obj.name}"
    destination = Path(settings.MEDIA_ROOT) / unique_name
    with destination.open("wb") as stream:
        for chunk in file_obj.chunks():
            stream.write(chunk)
    return unique_name


def next_code(prefix: str) -> str:
    alpha_code = "".join(char for char in uuid4().hex if char.isalpha())[:8].upper()
    return f"{prefix}-{alpha_code or prefix}"


def media_url(file_name: str | None) -> str:
    if not file_name:
        return ""
    return f"{settings.MEDIA_URL}{file_name}"


def preview_kind_for_file(file_name: str | None) -> str:
    if not file_name:
        return "none"
    extension = Path(file_name).suffix.lower()
    if extension in IMAGE_EXTENSIONS:
        return "image"
    if extension in PDF_EXTENSIONS:
        return "pdf"
    return "file"


def organization_feature_purchase(organization: Organization | None, feature_key: str) -> FeaturePurchase | None:
    if organization is None:
        return None
    return FeaturePurchase.objects.filter(organization=organization, feature_key=feature_key).first()


def active_feature_keys(organization: Organization | None) -> set[str]:
    if organization is None:
        return set()
    return set(
        FeaturePurchase.objects.filter(organization=organization, is_active=True).values_list("feature_key", flat=True)
    )


def license_status_payload(organization: Organization | None) -> dict:
    core_purchase = organization_feature_purchase(organization, CORE_FEATURE_KEY)
    if core_purchase is None or not core_purchase.is_active:
        return {
            "isLocked": True,
            "is_locked": True,
            "reason": "core_purchase_required",
            "notice": "برای استفاده از نرم افزار باید خرید اصلی ثبت و تایید شود.",
            "graceDays": 0,
            "grace_days": 0,
            "amountDue": "0.00" if core_purchase is None else format_money(core_purchase.remaining_amount),
            "amount_due": "0.00" if core_purchase is None else format_money(core_purchase.remaining_amount),
        }
    if Decimal(core_purchase.remaining_amount or 0) <= 0 and core_purchase.renewal_due_at:
        renewal_overdue_days = max((date.today() - core_purchase.renewal_due_at).days, 0)
        if renewal_overdue_days > 0:
            is_locked = renewal_overdue_days > 7
            annual_due = normalize_money(core_purchase.annual_subscription_amount or 0)
            return {
                "isLocked": is_locked,
                "is_locked": is_locked,
                "reason": "annual_subscription_due" if is_locked else "annual_subscription_warning",
                "notice": "اشتراک سالانه کارنومند سررسید شده است." if is_locked else "اشتراک سالانه کارنومند نزدیک/داخل مهلت پرداخت است.",
                "graceDays": 7,
                "grace_days": 7,
                "amountDue": format_money(annual_due),
                "amount_due": format_money(annual_due),
                "renewalDueAt": format_date(core_purchase.renewal_due_at),
                "renewal_due_at": format_date(core_purchase.renewal_due_at),
            }
    overdue_days = 0
    if core_purchase.next_installment_due_at and core_purchase.remaining_amount > 0:
        overdue_days = max((date.today() - core_purchase.next_installment_due_at).days, 0)
    is_locked = overdue_days > 7
    return {
        "isLocked": is_locked,
        "is_locked": is_locked,
        "reason": "installment_overdue" if is_locked else ("installment_overdue_warning" if overdue_days else ""),
        "notice": "سررسید پرداخت گذشته و دسترسی قفل شده است." if is_locked else ("سررسید پرداخت گذشته اما هنوز داخل بازه مهلت هستید." if overdue_days else ""),
        "graceDays": 7,
        "grace_days": 7,
        "amountDue": format_money(core_purchase.remaining_amount),
        "amount_due": format_money(core_purchase.remaining_amount),
    }


def menu_access_payload(user: User) -> dict:
    if user.slug == HQ_USERNAME:
        return {
            "core_software": True,
            "cloud_storage": True,
            "attendance": True,
            "wallet": True,
        }
    organization = get_user_organization(user)
    features = active_feature_keys(organization)
    return {
        "core_software": CORE_FEATURE_KEY in features,
        "cloud_storage": "cloud_storage" in features,
        "attendance": "attendance" in features,
        "wallet": is_manager(user),
    }


def wallet_feature_option_payload(config: dict, purchase: FeaturePurchase | None = None) -> dict:
    total_amount = normalize_money(config["base_price"])
    upfront_amount = normalize_money(config.get("upfront_amount", 0))
    annual_amount = normalize_money(config.get("annual_subscription_amount", getattr(purchase, "annual_subscription_amount", 0)))
    annual_installment_months = int(config.get("annual_subscription_installment_months", getattr(purchase, "annual_subscription_installment_months", 0)) or 0)
    annual_installment_amount = normalize_money(config.get("annual_subscription_installment_amount", annual_amount / annual_installment_months if annual_installment_months else 0))
    paid_amount = normalize_money(getattr(purchase, "paid_amount", 0))
    remaining_amount = normalize_money(getattr(purchase, "remaining_amount", total_amount if purchase is None else 0))
    return {
        "featureKey": config["feature_key"],
        "feature_key": config["feature_key"],
        "title": config["title"],
        "subtitle": config.get("subtitle", ""),
        "description": config.get("description", ""),
        "accent": config.get("accent", "#315f9f"),
        "required": bool(config.get("required")),
        "disabled": bool(config.get("disabled")),
        "disabledLabel": config.get("disabled_label", ""),
        "disabled_label": config.get("disabled_label", ""),
        "isActive": bool(getattr(purchase, "is_active", False)),
        "is_active": bool(getattr(purchase, "is_active", False)),
        "paymentPlan": getattr(purchase, "payment_plan", ""),
        "payment_plan": getattr(purchase, "payment_plan", ""),
        "totalAmount": format_money(total_amount),
        "total_amount": format_money(total_amount),
        "totalAmountRaw": float(total_amount),
        "paidAmount": format_money(paid_amount),
        "paid_amount": format_money(paid_amount),
        "paidAmountRaw": float(paid_amount),
        "remainingAmount": format_money(remaining_amount),
        "remaining_amount": format_money(remaining_amount),
        "remainingAmountRaw": float(remaining_amount),
        "cashAmount": format_money(total_amount),
        "cash_amount": format_money(total_amount),
        "upfrontAmount": format_money(upfront_amount),
        "upfront_amount": format_money(upfront_amount),
        "upfrontAmountRaw": float(upfront_amount),
        "monthlyInstallmentAmount": format_money(config.get("monthly_installment_amount", 0)),
        "monthly_installment_amount": format_money(config.get("monthly_installment_amount", 0)),
        "monthlyInstallmentAmountRaw": float(normalize_money(config.get("monthly_installment_amount", 0))),
        "installmentMonths": int(config.get("installment_months", 0) or 0),
        "installment_months": int(config.get("installment_months", 0) or 0),
        "nextInstallmentDueAt": format_date(getattr(purchase, "next_installment_due_at", None)),
        "next_installment_due_at": format_date(getattr(purchase, "next_installment_due_at", None)),
        "annualSubscriptionAmount": format_money(annual_amount),
        "annual_subscription_amount": format_money(annual_amount),
        "annualSubscriptionAmountRaw": float(annual_amount),
        "annualSubscriptionInstallmentMonths": annual_installment_months,
        "annual_subscription_installment_months": annual_installment_months,
        "annualSubscriptionInstallmentAmount": format_money(annual_installment_amount),
        "annual_subscription_installment_amount": format_money(annual_installment_amount),
        "renewalAfterMonths": int(config.get("renewal_after_months", 0) or 0),
        "renewal_after_months": int(config.get("renewal_after_months", 0) or 0),
        "renewalDueAt": format_date(getattr(purchase, "renewal_due_at", None)),
        "renewal_due_at": format_date(getattr(purchase, "renewal_due_at", None)),
    }


def wallet_options_payload(organization: Organization | None) -> dict:
    purchases = {
        item.feature_key: item
        for item in FeaturePurchase.objects.filter(organization=organization)
    } if organization is not None else {}
    return {
        "licenseStatus": license_status_payload(organization),
        "license_status": license_status_payload(organization),
        "options": [wallet_feature_option_payload(config, purchases.get(config["feature_key"])) for config in PURCHASABLE_FEATURES],
    }


def serialize_current_user(user: User) -> dict:
    membership = OrganizationMembership.objects.select_related("organization").filter(user=user).first()
    is_hq = user.slug == HQ_USERNAME
    organization = membership.organization if membership else None
    menu_access = menu_access_payload(user)
    license_status = {"isLocked": False, "is_locked": False, "reason": "", "notice": "", "graceDays": 0, "grace_days": 0, "amountDue": "0.00", "amount_due": "0.00"} if is_hq else license_status_payload(organization)
    bonus_amount = Decimal(user.bonus_amount or 0)
    penalty_amount = Decimal(user.penalty_amount or 0)
    net_adjustment = bonus_amount - penalty_amount
    return {
        "id": user.id,
        "slug": user.slug,
        "username": user.slug,
        "name": normalize_person_name(user.full_name),
        "role": user.job_title,
        "accessRole": user.role,
        "department": user.department.name if user.department else "",
        "avatar": user.avatar,
        "email": user.email,
        "phone": user.phone or "",
        "organization": membership.organization.name if membership else "",
        "bonusAmount": format_money(bonus_amount),
        "bonusAmountRaw": float(bonus_amount),
        "penaltyAmount": format_money(penalty_amount),
        "penaltyAmountRaw": float(penalty_amount),
        "netAdjustment": format_money(net_adjustment),
        "netAdjustmentRaw": float(net_adjustment),
        "canManageUsers": can_manage_users(user),
        "canAccessUsers": can_access_users(user),
        "canAccessExpenses": can_access_expenses(user),
        "canAccessSettings": can_access_settings(user),
        "canViewReports": can_view_reports(user),
        "canAccessApprovals": can_access_approvals(user),
        "canApproveDocuments": can_approve_documents(user),
        "isManager": is_manager(user),
        "isHq": is_hq,
        "canUseHq": is_hq,
        "purchasedMenuAccess": sorted([key for key, allowed in menu_access.items() if allowed]),
        "menuAccess": menu_access,
        "menu_access": menu_access,
        "licenseStatus": license_status,
        "license_status": license_status,
    }


def serialize_user(user: User) -> dict:
    membership = getattr(user, "organization_membership", None)
    finance_updated_at = user.finance_updated_at
    return {
        "id": user.id,
        "name": normalize_person_name(user.full_name),
        "username": user.slug,
        "email": user.email,
        "phone": user.phone or "",
        "role": access_role_label(user.role),
        "accessRole": user.role,
        "departmentCode": user.department.code if user.department else "",
        "department": user.department.name if user.department else "\u0628\u062f\u0648\u0646 \u0648\u0627\u062d\u062f",
        "manager": normalize_person_name(user.manager.full_name) if user.manager else "\u062a\u0639\u06cc\u06cc\u0646 \u0646\u0634\u062f\u0647",
        "kpi": user.job_title,
        "managerId": user.manager_id,
        "avatar": user.avatar,
        "organization": membership.organization.name if membership else "",
        "organizationId": membership.organization_id if membership else None,
        "joinedAt": format_date(user.created_at.date()),
        "joinedAtIso": format_date(user.created_at.date()),
        "financeUpdatedAt": finance_updated_at.isoformat() if finance_updated_at else "",
        "financeUpdatedAtIso": format_date(finance_updated_at.date()) if finance_updated_at else "",
        "isActive": user.is_active,
        "status": "\u0641\u0639\u0627\u0644" if user.is_active else "\u063a\u06cc\u0631\u0641\u0639\u0627\u0644",
    }


def settings_cards() -> list[dict]:
    return [
        {"title": "حساب کاربری", "description": "مدیریت نقش ها و دسترسی"},
        {"title": "اسناد", "description": "گردش کار امضای دیجیتال"},
        {"title": "هزینه ها", "description": "ثبت، پیگیری و کنترل هزینه"},
        {"title": "گزارشات", "description": "نمای مدیریتی و تحلیل عملکرد"},
    ]


def visible_settings_payload(user: User) -> dict:
    membership = OrganizationMembership.objects.select_related("organization").filter(user=user).first()
    organization = membership.organization if membership else None
    preference = None
    if organization:
        preference, _ = OrganizationPreference.objects.get_or_create(organization=organization)

    recent_logins = list(
        AuditLog.objects.filter(actor_id__in=visible_users(user).values_list("id", flat=True), action="login").order_by("-created_at")[:3]
    )
    recent_session_label = "بدون نشست اخیر"
    if recent_logins:
        recent_session_label = f"{len(recent_logins)} دستگاه فعال شناسایی شد"

    return {
        "organizationName": organization.name if organization else "",
        "systemId": f"KARO-{str(user.id or 0).zfill(4)}",
        "security": {
            "twoFactorRequired": preference.two_factor_required if preference else True,
            "recentSessionCount": len(recent_logins),
            "recentSessionLabel": recent_session_label,
        },
        "sections": settings_cards(),
        "canEdit": can_manage_users(user),
    }


def serialize_request(request_obj: Request) -> dict:
    current_user = getattr(request_obj, "_current_user", None)
    assignments = list(getattr(request_obj, "_prefetched_objects_cache", {}).get("approval_assignments", []))
    if not assignments and request_obj.pk:
        assignments = list(request_obj.approval_assignments.select_related("approver").order_by("created_at"))
    current_assignment = next((item for item in assignments if current_user and item.approver_id == current_user.id), None)
    can_approve = (
        current_assignment is not None
        and current_assignment.status == ApprovalAssignmentStatus.PENDING
        and request_obj.status in {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW}
    )
    attachments = list(getattr(request_obj, "_prefetched_objects_cache", {}).get("attachments", []))
    return {
        "id": request_obj.code,
        "title": request_obj.title,
        "owner": normalize_person_name(request_obj.requester.full_name) if request_obj.requester else "نامشخص",
        "manager": normalize_person_name(request_obj.manager.full_name) if request_obj.manager else "تعیین نشده",
        "managerAssignees": [normalize_person_name(item.full_name) for item in request_obj.assigned_managers.all()],
        "managerAssigneeIds": [item.id for item in request_obj.assigned_managers.all()],
        "employeeAssignees": [normalize_person_name(item.full_name) for item in request_obj.assigned_employees.all()],
        "employeeAssigneeIds": [item.id for item in request_obj.assigned_employees.all()],
        "priority": priority_label(request_obj.priority),
        "priorityValue": request_obj.priority,
        "status": request_status_label(request_obj.status),
        "statusValue": request_obj.status,
        "department": request_obj.department.name if request_obj.department else "بدون واحد",
        "departmentCode": request_obj.department.code if request_obj.department else "",
        "deadline": format_date(request_obj.deadline),
        "deadlineIso": format_date(request_obj.deadline),
        "createdAt": format_date(request_obj.created_at.date()),
        "createdAtIso": format_date(request_obj.created_at.date()),
        "description": request_obj.description or "",
        "attachments": [
            {
                "id": item.id,
                "originalName": item.original_name,
                "fileUrl": f"/api/v1/requests/{request_obj.code}/attachments/{item.id}",
                "mimeType": item.mime_type or "",
                "sizeBytes": item.size_bytes,
            }
            for item in attachments
        ],
        "attachmentsCount": len(attachments) if attachments else request_obj.attachments.count(),
        "decisions": [
            {
                "id": item.id,
                "approverId": item.approver_id,
                "approver": normalize_person_name(item.approver.full_name) if item.approver else "",
                "role": access_role_label(item.approver.role) if item.approver else "",
                "status": item.status,
                "statusLabel": assignment_status_label(item.status),
                "decisionNote": item.decision_note or "",
                "actedAt": item.acted_at.isoformat() if item.acted_at else "",
            }
            for item in assignments
        ],
        "bucket": current_assignment.status if current_assignment else request_obj.status,
        "canApprove": can_approve,
        "currentApproverId": current_assignment.approver_id if current_assignment else None,
    }


def serialize_expense(expense: Expense) -> dict:
    current_user = getattr(expense, "_current_user", None)
    assignments = list(getattr(expense, "_prefetched_objects_cache", {}).get("approval_assignments", []))
    if not assignments and expense.pk:
        assignments = list(expense.approval_assignments.select_related("approver").order_by("created_at"))
    current_assignment = next((item for item in assignments if current_user and item.approver_id == current_user.id), None)
    can_approve = (
        current_assignment is not None
        and current_assignment.status == ApprovalAssignmentStatus.PENDING
        and expense.status in {ExpenseStatus.PENDING, ExpenseStatus.UNDER_REVIEW}
    )
    return {
        "id": expense.code,
        "title": expense.title,
        "description": expense.notes or expense.title,
        "amount": format_money(expense.amount),
        "amountRaw": float(expense.amount),
        "category": expense_category_label(expense.category),
        "categoryValue": expense.category,
        "owner": normalize_person_name(expense.owner.full_name) if expense.owner else "نامشخص",
        "status": expense_status_label(expense.status),
        "statusValue": expense.status,
        "progress": expense.progress,
        "department": expense.department.name if expense.department else "بدون واحد",
        "departmentCode": expense.department.code if expense.department else "",
        "submittedAt": format_date(expense.expense_date),
        "createdAtIso": format_date(expense.expense_date),
        "invoiceName": expense.invoice_file_name or "",
        "invoiceUrl": media_url(expense.invoice_file_name),
        "decisions": [
            {
                "id": item.id,
                "approverId": item.approver_id,
                "approver": normalize_person_name(item.approver.full_name) if item.approver else "",
                "role": access_role_label(item.approver.role) if item.approver else "",
                "status": item.status,
                "statusLabel": assignment_status_label(item.status),
                "decisionNote": item.decision_note or "",
                "actedAt": item.acted_at.isoformat() if item.acted_at else "",
            }
            for item in assignments
        ],
        "bucket": current_assignment.status if current_assignment else expense.status,
        "canApprove": can_approve,
        "currentApproverId": current_assignment.approver_id if current_assignment else None,
    }


def ensure_organization_wallets(organization: Organization) -> list[Wallet]:
    defaults = [
        ("main", "کیف پول اصلی", Decimal("1000000")),
        ("sms", "کیف پول پیامک", Decimal("1500000")),
    ]
    wallets = []
    for key, name, threshold in defaults:
        wallet, _ = Wallet.objects.get_or_create(
            organization=organization,
            key=key,
            defaults={"name": name, "balance": Decimal("15000000") if key == "sms" else Decimal("0"), "low_balance_threshold": threshold},
        )
        wallets.append(wallet)
    return wallets


def serialize_wallet(wallet: Wallet) -> dict:
    balance = Decimal(wallet.balance)
    threshold = Decimal(wallet.low_balance_threshold)
    return {
        "id": wallet.id,
        "key": wallet.key,
        "name": wallet.name,
        "balance": format_money(balance),
        "balanceRaw": float(balance),
        "lowBalanceThreshold": format_money(threshold),
        "lowBalanceThresholdRaw": float(threshold),
        "isActive": wallet.is_active,
        "isLow": balance <= threshold,
        "updatedAt": wallet.updated_at.isoformat(),
    }


def serialize_wallet_transaction(transaction: WalletTransaction) -> dict:
    return {
        "id": transaction.id,
        "walletId": transaction.wallet_id,
        "walletName": transaction.wallet.name,
        "direction": transaction.direction,
        "type": transaction.transaction_type,
        "amount": format_money(transaction.amount),
        "amountRaw": float(transaction.amount),
        "balanceAfter": format_money(transaction.balance_after),
        "balanceAfterRaw": float(transaction.balance_after),
        "actor": normalize_person_name(transaction.actor.full_name) if transaction.actor else "",
        "note": transaction.note,
        "referenceId": transaction.reference_id,
        "createdAt": transaction.transacted_at.isoformat(),
        "createdAtIso": format_date(transaction.transacted_at.date()),
        "time": relative_time(transaction.transacted_at),
    }


def wallet_dashboard_payload(organization: Organization) -> dict:
    ensure_organization_wallets(organization)
    wallets = list(organization.wallets.order_by("key"))
    transactions = list(
        WalletTransaction.objects.filter(organization=organization)
        .select_related("wallet", "actor")
        .order_by("-transacted_at", "-id")[:100]
    )
    deposits_total = sum((item.amount for item in transactions if item.direction == "in"), Decimal("0"))
    withdrawals_total = sum((item.amount for item in transactions if item.direction == "out"), Decimal("0"))
    total_balance = sum((wallet.balance for wallet in wallets), Decimal("0"))
    wallet_by_key = {wallet.key: wallet for wallet in wallets}
    main_balance = wallet_by_key.get("main").balance if wallet_by_key.get("main") else Decimal("0")
    sms_balance = wallet_by_key.get("sms").balance if wallet_by_key.get("sms") else Decimal("0")
    sms_threshold = wallet_by_key.get("sms").low_balance_threshold if wallet_by_key.get("sms") else Decimal("0")

    return {
        "organization": {"id": organization.id, "name": organization.name, "code": organization.code},
        **wallet_options_payload(organization),
        "summary": {
            "totalBalance": format_money(total_balance),
            "totalBalanceRaw": float(total_balance),
            "mainBalance": format_money(main_balance),
            "mainBalanceRaw": float(main_balance),
            "smsBalance": format_money(sms_balance),
            "smsBalanceRaw": float(sms_balance),
            "smsLowBalanceThreshold": format_money(sms_threshold),
            "smsLowBalanceThresholdRaw": float(sms_threshold),
            "smsIsLow": sms_balance <= sms_threshold,
            "depositsTotal": format_money(deposits_total),
            "depositsTotalRaw": float(deposits_total),
            "withdrawalsTotal": format_money(withdrawals_total),
            "withdrawalsTotalRaw": float(withdrawals_total),
            "transactions": len(transactions),
        },
        "wallets": [serialize_wallet(wallet) for wallet in wallets],
        "transactions": [serialize_wallet_transaction(item) for item in transactions],
    }


def support_status_label(value: str) -> str:
    return {
        "open": "باز",
        "pending": "در حال بررسی",
        "answered": "پاسخ داده شده",
        "closed": "بسته شده",
    }.get(value, value)


def support_category_label(value: str) -> str:
    return {
        "technical": "فنی",
        "financial": "مالی",
        "operations": "عملیات",
        "account": "حساب کاربری",
        "other": "سایر",
    }.get(value, value)


def support_priority_label(value: str) -> str:
    return {
        "low": "کم",
        "medium": "متوسط",
        "high": "زیاد",
        "urgent": "فوری",
    }.get(value, value)


def serialize_support_attachment(attachment: SupportAttachment) -> dict:
    return {
        "id": attachment.id,
        "originalName": attachment.original_name,
        "fileUrl": media_url(attachment.stored_name),
        "mimeType": attachment.mime_type or "",
        "sizeBytes": attachment.size_bytes,
    }


def serialize_support_message(message: SupportMessage) -> dict:
    return {
        "id": message.id,
        "sender": normalize_person_name(message.sender_name),
        "senderPlatformRole": message.sender_platform_role,
        "body": message.body,
        "createdAt": message.created_at.isoformat(),
        "createdAtIso": format_date(message.created_at.date()),
        "time": relative_time(message.created_at),
    }


def serialize_support_ticket(ticket: SupportTicket, include_detail: bool = False) -> dict:
    messages = list(ticket.messages.all()) if include_detail else []
    last_message = messages[-1] if messages else ticket.messages.order_by("-created_at").first()
    payload = {
        "id": ticket.id,
        "subject": ticket.subject,
        "message": ticket.message,
        "category": ticket.category,
        "categoryLabel": support_category_label(ticket.category),
        "priority": ticket.priority,
        "priorityLabel": support_priority_label(ticket.priority),
        "status": ticket.status,
        "statusLabel": support_status_label(ticket.status),
        "requester": normalize_person_name(ticket.requester.full_name) if ticket.requester else "",
        "organization": ticket.organization.name,
        "organizationId": ticket.organization_id,
        "respondedBy": normalize_person_name(ticket.responded_by.full_name) if ticket.responded_by else "",
        "respondedAt": ticket.responded_at.isoformat() if ticket.responded_at else "",
        "firstResponseAt": ticket.first_response_at.isoformat() if ticket.first_response_at else "",
        "closedAt": ticket.closed_at.isoformat() if ticket.closed_at else "",
        "customerSatisfaction": ticket.customer_satisfaction,
        "customerFeedback": ticket.customer_feedback,
        "messagesCount": ticket.messages.count(),
        "lastMessagePreview": (last_message.body if last_message else ticket.message)[:180],
        "createdAt": ticket.created_at.isoformat(),
        "createdAtIso": format_date(ticket.created_at.date()),
        "updatedAt": ticket.updated_at.isoformat(),
        "updatedAtIso": format_date(ticket.updated_at.date()),
        "time": relative_time(ticket.updated_at),
        "actionMeta": parse_support_ticket_meta(ticket),
    }
    if include_detail:
        payload["messages"] = [serialize_support_message(message) for message in messages]
        payload["attachments"] = [serialize_support_attachment(item) for item in ticket.attachments.all()]
    return payload


def serialize_approval(document: Document, current_user: User | None = None) -> dict:
    current_assignment = None
    if current_user:
        current_assignment = next(
            (assignment for assignment in document.approval_assignments.all() if assignment.approver_id == current_user.id),
            None,
        )
    return {
        "id": document.code,
        "title": document.title,
        "owner": normalize_person_name(document.owner.full_name) if document.owner else "نامشخص",
        "type": document.document_type,
        "status": document_status_label(document.status),
        "statusValue": document.status,
        "department": document.department.name if document.department else "بدون واحد",
        "departmentCode": document.department.code if document.department else "",
        "uploadedAt": format_date(document.uploaded_at.date()),
        "uploadedAtIso": format_date(document.uploaded_at.date()),
        "risk": document_risk_label(document.risk),
        "riskValue": document.risk,
        "summary": document.description or "",
        "assignees": [normalize_person_name(assignment.approver.full_name) for assignment in document.approval_assignments.all()],
        "previewUrl": media_url(document.file_name),
        "downloadUrl": f"/api/v1/approvals/{document.code}/download" if document.file_name else "",
        "previewKind": preview_kind_for_file(document.file_name),
        "signedSignature": current_assignment.signed_signature_data if current_assignment else "",
        "decisionNote": current_assignment.decision_note if current_assignment else (document.rejection_reason or ""),
        "bucket": current_assignment.status if current_assignment else document.status,
        "canApprove": (
            (current_assignment is not None and current_assignment.status == ApprovalAssignmentStatus.PENDING)
            or (current_user is not None and current_user.slug == HQ_USERNAME and document.status in {DocumentStatus.PENDING, DocumentStatus.WAITING_SIGNATURE})
        ),
        "currentApproverId": current_assignment.approver_id if current_assignment else None,
    }


def visible_requests(user: User):
    return (
        Request.objects.filter(Q(requester=user) | Q(approval_assignments__approver=user))
        .select_related("requester", "manager", "department")
        .prefetch_related(
            "assigned_managers",
            "assigned_employees",
            "attachments",
            Prefetch("approval_assignments", queryset=RequestApprovalAssignment.objects.select_related("approver").order_by("created_at")),
        )
        .distinct()
        .order_by("-created_at")
    )


def visible_expenses(user: User):
    return (
        Expense.objects.filter(Q(owner=user) | Q(approval_assignments__approver=user))
        .select_related("owner", "department")
        .prefetch_related(Prefetch("approval_assignments", queryset=ExpenseApprovalAssignment.objects.select_related("approver").order_by("created_at")))
        .distinct()
        .order_by("-expense_date", "-created_at")
    )


def visible_approvals(user: User):
    if not can_access_approvals(user):
        return Document.objects.none()
    return (
        Document.objects.filter(Q(owner=user) | Q(approval_assignments__approver=user))
        .select_related("owner", "department")
        .prefetch_related(
            Prefetch(
                "approval_assignments",
                queryset=ApprovalAssignment.objects.select_related("approver").order_by("created_at"),
            )
        )
        .distinct()
        .order_by("-uploaded_at")
    )


def report_catalog(user: User) -> list[dict]:
    owner = normalize_person_name(user.full_name) or "مدیرعامل"
    today = date.today().isoformat()
    return [
        {
            "id": "requests",
            "title": "گزارش درخواست ها",
            "description": "نمای کلی جریان درخواست ها و وضعیت پیگیری آن ها",
            "export": "CSV / Excel",
            "owner": owner,
            "generatedAt": today,
            "generatedAtIso": today,
            "downloadUrl": "/api/v1/reports/requests/export?format=csv",
        },
        {
            "id": "expenses",
            "title": "گزارش هزینه ها",
            "description": "تحلیل هزینه های سازمان بر اساس ثبت کننده و مبلغ",
            "export": "CSV / Excel",
            "owner": owner,
            "generatedAt": today,
            "generatedAtIso": today,
            "downloadUrl": "/api/v1/reports/expenses/export?format=csv",
        },
        {
            "id": "approvals",
            "title": "گزارش تاییدها",
            "description": "عملکرد مدیران در تایید، رد و گردش اسناد",
            "export": "CSV / Excel",
            "owner": owner,
            "generatedAt": today,
            "generatedAtIso": today,
            "downloadUrl": "/api/v1/reports/approvals/export?format=csv",
        },
        {
            "id": "users",
            "title": "گزارش کاربران",
            "description": "نمای وضعیت کاربران، مدیر مستقیم، پاداش و جریمه ثبت‌شده",
            "export": "CSV / Excel",
            "owner": owner,
            "generatedAt": today,
            "generatedAtIso": today,
            "downloadUrl": "/api/v1/reports/users/export?format=csv",
        },
    ]


def visible_reports_payload(user: User) -> dict:
    organization = get_user_organization(user)
    users_qs = User.objects.filter(organization_membership__organization=organization).select_related("department", "manager")
    user_ids = list(users_qs.values_list("id", flat=True))
    requests_qs = list(
        Request.objects.filter(requester_id__in=user_ids)
        .select_related("requester", "manager", "department")
        .prefetch_related(
            "assigned_managers",
            "assigned_employees",
            "attachments",
            Prefetch("approval_assignments", queryset=RequestApprovalAssignment.objects.select_related("approver").order_by("created_at")),
        )
        .order_by("-created_at")
    )
    expenses_qs = list(
        Expense.objects.filter(owner_id__in=user_ids)
        .select_related("owner", "department")
        .prefetch_related(Prefetch("approval_assignments", queryset=ExpenseApprovalAssignment.objects.select_related("approver").order_by("created_at")))
        .order_by("-expense_date", "-created_at")
    )
    approvals_qs = list(
        Document.objects.filter(owner_id__in=user_ids)
        .select_related("owner", "department")
        .prefetch_related(Prefetch("approval_assignments", queryset=ApprovalAssignment.objects.select_related("approver").order_by("created_at")))
        .order_by("-uploaded_at")
    )
    for item in requests_qs:
        item._current_user = user
    for item in expenses_qs:
        item._current_user = user
    expense_total = sum(Decimal(item.amount) for item in expenses_qs)
    request_status = Counter(item.status for item in requests_qs)
    expense_by_submitter: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for item in expenses_qs:
        if item.owner:
            expense_by_submitter[normalize_person_name(item.owner.full_name)] += Decimal(item.amount)
    return {
        "summary": {
            "users": users_qs.count(),
            "requests": len(requests_qs),
            "expenses": len(expenses_qs),
            "approvals": len(approvals_qs),
            "expenseTotal": format_money(expense_total),
        },
        "requestStatus": dict(request_status),
        "topSubmitters": [
            {"name": name, "count": float(total), "amount": format_money(total)}
            for name, total in sorted(expense_by_submitter.items(), key=lambda item: item[1], reverse=True)[:5]
        ],
        "reports": report_catalog(user),
        "requests": [serialize_request(item) for item in requests_qs],
        "expenses": [serialize_expense(item) for item in expenses_qs],
        "approvals": [serialize_approval(item, user) for item in approvals_qs],
        "users": [serialize_user(item) for item in users_qs],
    }


def serialize_hq_organization(organization: Organization) -> dict:
    users = list(User.objects.filter(organization_membership__organization=organization))
    user_ids = [item.id for item in users]
    requests = Request.objects.filter(requester_id__in=user_ids)
    expenses = Expense.objects.filter(owner_id__in=user_ids)
    documents = Document.objects.filter(owner_id__in=user_ids)
    total_expense = sum(Decimal(item.amount) for item in expenses)
    active_users = sum(1 for item in users if item.is_active)
    return {
        "id": organization.id,
        "code": organization.code,
        "name": organization.name,
        "createdAt": format_date(organization.created_at.date()),
        "createdAtIso": format_date(organization.created_at.date()),
        "users": len(users),
        "activeUsers": active_users,
        "requests": requests.count(),
        "expenses": expenses.count(),
        "documents": documents.count(),
        "paymentTotal": format_money(total_expense),
        "paymentTotalRaw": float(total_expense),
    }


def serialize_hq_audit(item: AuditLog) -> dict:
    return {
        "id": item.id,
        "actor": normalize_person_name(item.actor_name),
        "action": item.action,
        "entityType": item.entity_type,
        "entityCode": item.entity_code or "",
        "detail": item.detail,
        "icon": item.icon,
        "createdAt": item.created_at.isoformat(),
        "time": relative_time(item.created_at),
    }


def build_hq_payload() -> dict:
    organizations = list(Organization.objects.exclude(code="hq-control").order_by("-created_at"))
    users = list(
        User.objects.select_related("department", "manager", "organization_membership__organization").order_by("-created_at")
    )
    requests_qs = list(
        Request.objects.select_related("requester", "manager", "department")
        .prefetch_related("assigned_managers", "attachments")
        .order_by("-created_at")
    )
    expenses_qs = list(Expense.objects.select_related("owner", "department").order_by("-created_at"))
    documents_qs = list(
        Document.objects.select_related("owner", "department")
        .prefetch_related(Prefetch("approval_assignments", queryset=ApprovalAssignment.objects.select_related("approver")))
        .order_by("-uploaded_at")
    )
    tickets_qs = list(
        SupportTicket.objects.select_related("organization", "requester", "responded_by")
        .prefetch_related("messages", "attachments")
        .order_by("-updated_at", "-id")
    )
    audits = list(AuditLog.objects.select_related("actor").order_by("-created_at")[:80])

    total_payments = sum(Decimal(item.amount) for item in expenses_qs)
    pending_payments = sum(Decimal(item.amount) for item in expenses_qs if item.status in {ExpenseStatus.PENDING, ExpenseStatus.UNDER_REVIEW})
    approved_payments = sum(Decimal(item.amount) for item in expenses_qs if item.status == ExpenseStatus.APPROVED)
    open_requests = sum(1 for item in requests_qs if item.status in {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW})
    pending_documents = sum(1 for item in documents_qs if item.status in {DocumentStatus.PENDING, DocumentStatus.WAITING_SIGNATURE})
    open_tickets = sum(1 for item in tickets_qs if item.status == SupportTicketStatus.OPEN)
    pending_tickets = sum(1 for item in tickets_qs if item.status == SupportTicketStatus.PENDING)
    answered_tickets = sum(1 for item in tickets_qs if item.status == SupportTicketStatus.ANSWERED)

    role_counts = Counter(item.role for item in users)
    payment_status = Counter(item.status for item in expenses_qs)
    request_status = Counter(item.status for item in requests_qs)
    document_status = Counter(item.status for item in documents_qs)
    ticket_status = Counter(item.status for item in tickets_qs)
    organization_options = [{"id": item.id, "name": item.name, "code": item.code} for item in organizations]

    return {
        "summary": {
            "organizations": len(organizations),
            "users": len(users),
            "activeUsers": sum(1 for item in users if item.is_active),
            "payments": len(expenses_qs),
            "paymentTotal": format_money(total_payments),
            "paymentTotalRaw": float(total_payments),
            "pendingPaymentTotal": format_money(pending_payments),
            "approvedPaymentTotal": format_money(approved_payments),
            "openRequests": open_requests,
            "pendingDocuments": pending_documents,
            "tickets": len(tickets_qs),
            "openTickets": open_tickets,
            "pendingTickets": pending_tickets,
            "answeredTickets": answered_tickets,
            "auditEvents": len(audits),
        },
        "organizations": [serialize_hq_organization(item) for item in organizations],
        "users": [serialize_user(item) for item in users],
        "requests": [serialize_request(item) for item in requests_qs],
        "payments": [serialize_expense(item) for item in expenses_qs],
        "documents": [serialize_approval(item) for item in documents_qs],
        "tickets": [serialize_support_ticket(item) for item in tickets_qs],
        "audits": [serialize_hq_audit(item) for item in audits],
        "segments": {
            "roles": [{"key": key, "label": access_role_label(key), "count": value} for key, value in role_counts.items()],
            "payments": [{"key": key, "label": expense_status_label(key), "count": value} for key, value in payment_status.items()],
            "requests": [{"key": key, "label": request_status_label(key), "count": value} for key, value in request_status.items()],
            "documents": [{"key": key, "label": document_status_label(key), "count": value} for key, value in document_status.items()],
            "tickets": [{"key": key, "label": support_status_label(key), "count": value} for key, value in ticket_status.items()],
        },
        "directories": {
            "organizations": organization_options,
            "departments": [{"code": item.code, "name": item.name} for item in Department.objects.order_by("name")],
            "users": [{"id": item.id, "name": normalize_person_name(item.full_name), "role": access_role_label(item.role)} for item in users],
            "roles": [{"value": value, "label": label} for value, label in UserRole.choices],
            "requestStatuses": [{"value": value, "label": label} for value, label in RequestStatus.choices],
            "expenseStatuses": [{"value": value, "label": label} for value, label in ExpenseStatus.choices],
            "documentStatuses": [{"value": value, "label": label} for value, label in DocumentStatus.choices],
        },
    }


def approval_metrics(user: User) -> dict:
    assignments = ApprovalAssignment.objects.filter(approver=user)
    return {
        "pending": assignments.filter(status=ApprovalAssignmentStatus.PENDING).count(),
        "approved": assignments.filter(status=ApprovalAssignmentStatus.APPROVED).count(),
        "rejected": assignments.filter(status=ApprovalAssignmentStatus.REJECTED).count(),
    }


def update_document_status(document: Document) -> None:
    statuses = set(document.approval_assignments.values_list("status", flat=True))
    if ApprovalAssignmentStatus.REJECTED in statuses:
        document.status = DocumentStatus.REJECTED
        document.rejected_at = now()
        document.approved_at = None
    elif statuses and statuses == {ApprovalAssignmentStatus.APPROVED}:
        document.status = DocumentStatus.APPROVED
        document.approved_at = now()
        document.rejected_at = None
        document.rejection_reason = ""
    else:
        document.status = DocumentStatus.PENDING
        document.approved_at = None
        document.rejected_at = None
    document.save(update_fields=["status", "approved_at", "rejected_at", "rejection_reason"])


def build_bootstrap_payload(user: User, organization_id: int | None = None) -> dict:
    hq_selected_organization = None
    if user.slug == HQ_USERNAME and organization_id:
        hq_selected_organization = Organization.objects.exclude(code="hq-control").filter(pk=organization_id).first()

    if user.slug == HQ_USERNAME and hq_selected_organization is None:
        requests_qs = []
        expenses_qs = []
        approvals_qs = []
        users_qs = []
    elif hq_selected_organization is not None:
        users_qs = list(
            User.objects.filter(organization_membership__organization=hq_selected_organization)
            .select_related("department", "manager", "organization_membership__organization")
            .order_by("created_at")
        )
        user_ids = [item.id for item in users_qs]
        requests_qs = list(
            Request.objects.filter(requester_id__in=user_ids)
            .select_related("requester", "manager", "department")
            .prefetch_related(
                "assigned_managers",
                "assigned_employees",
                "attachments",
                Prefetch("approval_assignments", queryset=RequestApprovalAssignment.objects.select_related("approver").order_by("created_at")),
            )
            .order_by("-created_at")
        )
        expenses_qs = list(
            Expense.objects.filter(owner_id__in=user_ids)
            .select_related("owner", "department")
            .prefetch_related(Prefetch("approval_assignments", queryset=ExpenseApprovalAssignment.objects.select_related("approver").order_by("created_at")))
            .order_by("-expense_date", "-created_at")
        )
        approvals_qs = list(
            Document.objects.filter(owner_id__in=user_ids)
            .select_related("owner", "department")
            .prefetch_related(Prefetch("approval_assignments", queryset=ApprovalAssignment.objects.select_related("approver").order_by("created_at")))
            .order_by("-uploaded_at")
        )
    else:
        requests_qs = list(visible_requests(user))
        expenses_qs = list(visible_expenses(user))
        approvals_qs = list(visible_approvals(user))
        users_qs = list(visible_users(user).select_related("department", "manager", "organization_membership__organization").order_by("created_at"))

    for request_obj in requests_qs:
        request_obj._current_user = user
    for expense in expenses_qs:
        expense._current_user = user

    departments = list(visible_department_catalog())
    directory_users_qs = list(
        organization_users(user)
        .select_related("department", "manager", "organization_membership__organization")
        .order_by("created_at")
    )
    activities = list(
        AuditLog.objects.filter(actor_id__in=[item.id for item in users_qs]).select_related("actor").order_by("-created_at")[:6]
    )

    month_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date.month == date.today().month)
    year_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date.year == date.today().year)
    active_requests = sum(1 for item in requests_qs if item.status in {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW})
    if hq_selected_organization is not None:
        metrics = {
            "pending": sum(1 for item in approvals_qs if item.status in {DocumentStatus.PENDING, DocumentStatus.WAITING_SIGNATURE}),
            "approved": sum(1 for item in approvals_qs if item.status == DocumentStatus.APPROVED),
            "rejected": sum(1 for item in approvals_qs if item.status == DocumentStatus.REJECTED),
        }
    else:
        metrics = approval_metrics(user)

    expense_by_day: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
    start_day = date.today() - timedelta(days=6)
    for expense in expenses_qs:
        if expense.expense_date >= start_day:
            expense_by_day[expense.expense_date] += Decimal(expense.amount)

    max_total = max(expense_by_day.values(), default=Decimal("0"))
    chart_data = []
    for index in range(7):
        current_day = start_day + timedelta(days=index)
        day_total = expense_by_day[current_day]
        scaled = int((day_total / max_total) * 100) if max_total > 0 and day_total > 0 else 0
        chart_data.append({"day": PERSIAN_WEEK_DAYS[index], "value": scaled})

    pipeline = [
        {"label": label, "count": sum(1 for item in requests_qs if item.status == code)}
        for code, label in RequestStatus.choices
        if code != RequestStatus.CLOSED
    ]

    reports = []
    if can_view_reports(user):
        reports = [
            {"title": "گزارش درخواست ها", "description": "نمای کلی جریان درخواست ها", "export": "CSV / Excel", "owner": "مدیرعامل", "generatedAt": date.today().isoformat(), "generatedAtIso": date.today().isoformat()},
            {"title": "گزارش هزینه ها", "description": "تحلیل هزینه های سازمان", "export": "CSV / Excel", "owner": "مدیرعامل", "generatedAt": date.today().isoformat(), "generatedAtIso": date.today().isoformat()},
            {"title": "گزارش تاییدها", "description": "عملکرد مدیران در تایید اسناد", "export": "CSV / Excel", "owner": "مدیرعامل", "generatedAt": date.today().isoformat(), "generatedAtIso": date.today().isoformat()},
        ]

    reports = report_catalog(user) if can_view_reports(user) else []

    today_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date == date.today())
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date >= week_start)
    wallet_organization = hq_selected_organization
    if wallet_organization is None and user.slug != HQ_USERNAME:
        wallet_organization = get_user_organization(user)
    sms_balance = Decimal("0")
    if wallet_organization is not None:
        ensure_organization_wallets(wallet_organization)
        sms_wallet = wallet_organization.wallets.filter(key="sms", is_active=True).first()
        sms_balance = Decimal(sms_wallet.balance) if sms_wallet else Decimal("0")
        sms_threshold = Decimal(sms_wallet.low_balance_threshold) if sms_wallet else Decimal("0")
    else:
        sms_threshold = Decimal("0")

    return {
        "currentUser": serialize_current_user(user),
        "selectedOrganization": (
            {"id": hq_selected_organization.id, "name": hq_selected_organization.name, "code": hq_selected_organization.code}
            if hq_selected_organization
            else None
        ),
        "hqOrganizations": [
            {"id": item.id, "name": item.name, "code": item.code}
            for item in Organization.objects.exclude(code="hq-control").order_by("name")
        ]
        if user.slug == HQ_USERNAME
        else [],
        "stats": [
            {"id": "active", "label": "درخواست ها", "value": str(active_requests), "detail": "", "tone": "primary", "icon": "assignment"},
            {"id": "pending", "label": "تاییدها", "value": str(metrics["pending"]), "detail": "", "tone": "warning", "icon": "pending_actions"},
            {"id": "monthly", "label": "هزینه ماه", "value": format_money(month_total), "detail": "", "tone": "secondary", "icon": "payments"},
            {"id": "approved", "label": "اسناد تایید", "value": str(metrics["approved"]), "detail": "", "tone": "success", "icon": "fact_check"},
        ],
        "chartData": chart_data,
        "pipeline": pipeline,
        "requests": [serialize_request(item) for item in requests_qs],
        "expenses": [serialize_expense(item) for item in expenses_qs],
        "approvals": [serialize_approval(item, user) for item in approvals_qs],
        "users": [serialize_user(item) for item in users_qs],
        "reports": reports,
        "activities": [
            {
                "id": item.id,
                "user": normalize_person_name(item.actor_name),
                "action": item.action,
                "detail": item.detail,
                "time": relative_time(item.created_at),
                "icon": item.icon,
            }
            for item in activities
        ],
        "insights": [],
        "expenseSummary": [
            {"label": "امروز", "value": format_money(today_total)},
            {"label": "این هفته", "value": format_money(week_total)},
            {"label": "این ماه", "value": format_money(month_total)},
            {"label": "امسال", "value": format_money(year_total)},
        ],
        "wallet": {
            "summary": {
                "smsBalance": format_money(sms_balance),
                "smsBalanceRaw": float(sms_balance),
                "smsLowBalanceThreshold": format_money(sms_threshold),
                "smsLowBalanceThresholdRaw": float(sms_threshold),
                "smsIsLow": sms_balance <= sms_threshold,
            },
        },
        "approvalMetrics": metrics,
        "settingsCards": [
            {"title": "حساب کاربری", "description": "مدیریت نقش ها و دسترسی"},
            {"title": "اسناد", "description": "گردش کار امضای دیجیتال"},
            {"title": "هزینه ها", "description": "ثبت، پیگیری و کنترل هزینه"},
            {"title": "گزارشات", "description": "نمای مدیریتی و تحلیل عملکرد"},
        ],
        "directories": {
            "departments": [{"code": item.code, "name": item.name} for item in departments],
            "managers": [
                {"id": item.id, "slug": item.slug, "name": normalize_person_name(item.full_name), "role": access_role_label(item.role)}
                for item in directory_users_qs
                if item.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER}
            ],
            "users": [serialize_user(item) for item in directory_users_qs],
        },
    }


def _report_date_bounds(filters: dict | None = None) -> tuple[date | None, date | None]:
    filters = filters or {}
    today_value = date.today()
    period = (filters.get("period") or "").strip()
    if period == "today":
        return today_value, today_value
    if period == "week":
        return today_value - timedelta(days=today_value.weekday()), today_value
    if period == "month":
        return today_value.replace(day=1), today_value
    if period == "year":
        return today_value.replace(month=1, day=1), today_value

    def parse(raw_value):
        try:
            return date.fromisoformat(raw_value) if raw_value else None
        except ValueError:
            return None

    return parse(filters.get("startDate")), parse(filters.get("endDate"))


def _in_report_bounds(item_date: date, start_date: date | None, end_date: date | None) -> bool:
    if start_date and item_date < start_date:
        return False
    if end_date and item_date > end_date:
        return False
    return True


def _report_user_ids(user: User, organization_id: int | None, filters: dict | None = None) -> list[int]:
    filters = filters or {}
    organization = None
    if user.slug == HQ_USERNAME and organization_id:
        organization = Organization.objects.exclude(code="hq-control").filter(pk=organization_id).first()
    if organization is None:
        organization = get_user_organization(user)
    user_ids = list(User.objects.filter(organization_membership__organization=organization).values_list("id", flat=True))
    selected_user_id = filters.get("userId")
    if selected_user_id and str(selected_user_id).isdigit() and int(selected_user_id) in user_ids:
        return [int(selected_user_id)]
    return user_ids


def render_report_export(report_key: str, user: User, organization_id: int | None = None, filters: dict | None = None) -> tuple[str, str]:
    buffer = StringIO()
    writer = csv.writer(buffer)
    today = date.today().isoformat()
    filters = filters or {}
    start_date, end_date = _report_date_bounds(filters)
    user_ids = _report_user_ids(user, organization_id, filters)

    if report_key == "requests":
        writer.writerow(["code", "title", "requester", "manager", "assignees", "status", "priority", "department", "created_at", "deadline", "decisions"])
        request_items = (
            Request.objects.filter(requester_id__in=user_ids)
            .select_related("requester", "manager", "department")
            .prefetch_related(
                "assigned_managers",
                "assigned_employees",
                Prefetch("approval_assignments", queryset=RequestApprovalAssignment.objects.select_related("approver").order_by("created_at")),
            )
            .order_by("-created_at")
        )
        for item in request_items:
            if not _in_report_bounds(item.created_at.date(), start_date, end_date):
                continue
            assignees = [normalize_person_name(manager.full_name) for manager in item.assigned_managers.all()]
            assignees += [normalize_person_name(employee.full_name) for employee in item.assigned_employees.all()]
            decisions = " | ".join(
                f"{normalize_person_name(assignment.approver.full_name)}: {assignment_status_label(assignment.status)}"
                for assignment in item.approval_assignments.all()
            )
            writer.writerow([
                item.code,
                item.title,
                normalize_person_name(item.requester.full_name) if item.requester else "",
                normalize_person_name(item.manager.full_name) if item.manager else "",
                "، ".join(assignees),
                request_status_label(item.status),
                priority_label(item.priority),
                item.department.name if item.department else "",
                format_date(item.created_at.date()),
                format_date(item.deadline),
                decisions,
            ])
    elif report_key == "expenses":
        writer.writerow(["code", "description", "owner", "amount", "category", "status", "department", "expense_date", "decisions"])
        expense_items = (
            Expense.objects.filter(owner_id__in=user_ids)
            .select_related("owner", "department")
            .prefetch_related(Prefetch("approval_assignments", queryset=ExpenseApprovalAssignment.objects.select_related("approver").order_by("created_at")))
            .order_by("-expense_date", "-created_at")
        )
        for item in expense_items:
            if not _in_report_bounds(item.expense_date, start_date, end_date):
                continue
            decisions = " | ".join(
                f"{normalize_person_name(assignment.approver.full_name)}: {assignment_status_label(assignment.status)}"
                for assignment in item.approval_assignments.all()
            )
            writer.writerow([
                item.code,
                item.notes or item.title,
                normalize_person_name(item.owner.full_name) if item.owner else "",
                format_money(item.amount),
                expense_category_label(item.category),
                expense_status_label(item.status),
                item.department.name if item.department else "",
                format_date(item.expense_date),
                decisions,
            ])
    elif report_key == "approvals":
        writer.writerow(["code", "title", "owner", "type", "status", "risk", "department", "uploaded_at", "approvers", "decisions"])
        approval_items = (
            Document.objects.filter(owner_id__in=user_ids)
            .select_related("owner", "department")
            .prefetch_related(Prefetch("approval_assignments", queryset=ApprovalAssignment.objects.select_related("approver").order_by("created_at")))
            .order_by("-uploaded_at")
        )
        for item in approval_items:
            if not _in_report_bounds(item.uploaded_at.date(), start_date, end_date):
                continue
            approvers = "، ".join(normalize_person_name(assignment.approver.full_name) for assignment in item.approval_assignments.all())
            decisions = " | ".join(
                f"{normalize_person_name(assignment.approver.full_name)}: {assignment_status_label(assignment.status)}"
                for assignment in item.approval_assignments.all()
            )
            writer.writerow([
                item.code,
                item.title,
                normalize_person_name(item.owner.full_name) if item.owner else "",
                item.document_type,
                document_status_label(item.status),
                document_risk_label(item.risk),
                item.department.name if item.department else "",
                format_date(item.uploaded_at.date()),
                approvers,
                decisions,
            ])
    elif report_key == "users":
        writer.writerow(["id", "name", "username", "role", "job_title", "department", "manager", "status", "joined_at", "bonus_amount", "penalty_amount", "net_adjustment"])
        user_items = (
            User.objects.filter(id__in=user_ids)
            .select_related("department", "manager")
            .order_by("-created_at")
        )
        for item in user_items:
            if not _in_report_bounds(item.created_at.date(), start_date, end_date):
                continue
            bonus_amount = Decimal(item.bonus_amount or 0)
            penalty_amount = Decimal(item.penalty_amount or 0)
            writer.writerow([
                item.id,
                normalize_person_name(item.full_name),
                item.slug,
                access_role_label(item.role),
                item.job_title,
                item.department.name if item.department else "",
                normalize_person_name(item.manager.full_name) if item.manager else "",
                "فعال" if item.is_active else "غیرفعال",
                format_date(item.created_at.date()),
                format_money(bonus_amount),
                format_money(penalty_amount),
                format_money(bonus_amount - penalty_amount),
            ])
    else:
        raise ValueError("Invalid report key.")

    return f"{report_key}-report-{today}.csv", buffer.getvalue()

def serialize_user(user: User) -> dict:
    organization = get_user_organization(user)
    section_access = set(
        user.section_access_grants.filter(organization=organization).values_list("section_key", flat=True)
    )
    bonus_amount = Decimal(user.bonus_amount or 0)
    penalty_amount = Decimal(user.penalty_amount or 0)
    net_adjustment = bonus_amount - penalty_amount
    finance_updated_at = user.finance_updated_at
    return {
        "id": user.id,
        "name": normalize_person_name(user.full_name),
        "username": user.slug,
        "email": user.email,
        "phone": user.phone or "",
        "role": access_role_label(user.role),
        "accessRole": user.role,
        "department": user.department.name if user.department else "بدون واحد",
        "manager": normalize_person_name(user.manager.full_name) if user.manager else "تعیین نشده",
        "jobTitle": user.job_title,
        "kpi": user.job_title,
        "joinedAt": format_date(user.created_at.date()),
        "joinedAtIso": format_date(user.created_at.date()),
        "financeUpdatedAt": finance_updated_at.isoformat() if finance_updated_at else "",
        "financeUpdatedAtIso": format_date(finance_updated_at.date()) if finance_updated_at else "",
        "status": "فعال" if user.is_active else "غیرفعال",
        "isActive": user.is_active,
        "managerId": user.manager_id,
        "departmentCode": user.department.code if user.department else "",
        "bonusAmount": format_money(bonus_amount),
        "bonusAmountRaw": float(bonus_amount),
        "penaltyAmount": format_money(penalty_amount),
        "penaltyAmountRaw": float(penalty_amount),
        "netAdjustment": format_money(net_adjustment),
        "netAdjustmentRaw": float(net_adjustment),
        "sectionAccess": {
            "approvals": "approvals" in section_access,
            "expenses": "expenses" in section_access,
            "reports": "reports" in section_access,
            "users": "users" in section_access,
            "settings": "settings" in section_access,
        },
    }

