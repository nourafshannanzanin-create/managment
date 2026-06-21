from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db.models import Prefetch

from workflow.access import can_approve_documents, can_manage_users, can_view_reports, is_manager, visible_users
from workflow.models import (
    ApprovalAssignment,
    ApprovalAssignmentStatus,
    AuditLog,
    Department,
    Document,
    DocumentRisk,
    DocumentStatus,
    Expense,
    ExpenseCategory,
    ExpenseStatus,
    OrganizationMembership,
    Request,
    RequestPriority,
    RequestStatus,
    RequestTimeline,
    User,
    UserRole,
)

PERSIAN_WEEK_DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه شنبه", "چهارشنبه", "پنج شنبه", "جمعه"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
PDF_EXTENSIONS = {".pdf"}


def now():
    return datetime.now(timezone.utc)


def format_money(value: Decimal | int | float | str) -> str:
    return f"{int(Decimal(value)):,}"


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


def serialize_current_user(user: User) -> dict:
    membership = OrganizationMembership.objects.select_related("organization").filter(user=user).first()
    return {
        "id": user.id,
        "slug": user.slug,
        "name": user.full_name,
        "role": user.job_title,
        "accessRole": user.role,
        "department": user.department.name if user.department else "",
        "avatar": user.avatar,
        "email": user.email,
        "organization": membership.organization.name if membership else "",
        "canManageUsers": can_manage_users(user),
        "canViewReports": can_view_reports(user),
        "canApproveDocuments": can_approve_documents(user),
        "isManager": is_manager(user),
    }


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "role": access_role_label(user.role),
        "accessRole": user.role,
        "department": user.department.name if user.department else "بدون واحد",
        "manager": user.manager.full_name if user.manager else "تعیین نشده",
        "kpi": user.job_title,
        "joinedAt": format_date(user.created_at.date()),
        "joinedAtIso": format_date(user.created_at.date()),
        "status": "فعال" if user.is_active else "غیرفعال",
    }


def serialize_request(request_obj: Request) -> dict:
    return {
        "id": request_obj.code,
        "title": request_obj.title,
        "owner": request_obj.requester.full_name if request_obj.requester else "نامشخص",
        "manager": request_obj.manager.full_name if request_obj.manager else "تعیین نشده",
        "priority": priority_label(request_obj.priority),
        "status": request_status_label(request_obj.status),
        "department": request_obj.department.name if request_obj.department else "بدون واحد",
        "deadline": format_date(request_obj.deadline),
        "deadlineIso": format_date(request_obj.deadline),
        "createdAt": format_date(request_obj.created_at.date()),
        "createdAtIso": format_date(request_obj.created_at.date()),
        "description": request_obj.description or "",
        "attachmentsCount": request_obj.attachments.count(),
    }


def serialize_expense(expense: Expense) -> dict:
    return {
        "id": expense.code,
        "title": expense.title,
        "description": expense.notes or expense.title,
        "amount": format_money(expense.amount),
        "amountRaw": float(expense.amount),
        "category": expense_category_label(expense.category),
        "owner": expense.owner.full_name if expense.owner else "نامشخص",
        "status": expense_status_label(expense.status),
        "progress": expense.progress,
        "department": expense.department.name if expense.department else "بدون واحد",
        "submittedAt": format_date(expense.expense_date),
        "createdAtIso": format_date(expense.expense_date),
        "invoiceName": expense.invoice_file_name or "",
        "invoiceUrl": media_url(expense.invoice_file_name),
    }


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
        "owner": document.owner.full_name if document.owner else "نامشخص",
        "type": document.document_type,
        "status": document_status_label(document.status),
        "department": document.department.name if document.department else "بدون واحد",
        "uploadedAt": format_date(document.uploaded_at.date()),
        "uploadedAtIso": format_date(document.uploaded_at.date()),
        "risk": document_risk_label(document.risk),
        "summary": document.description or "",
        "assignees": [assignment.approver.full_name for assignment in document.approval_assignments.all()],
        "previewUrl": media_url(document.file_name),
        "downloadUrl": media_url(document.file_name),
        "previewKind": preview_kind_for_file(document.file_name),
        "signedSignature": current_assignment.signed_signature_data if current_assignment else "",
        "decisionNote": current_assignment.decision_note if current_assignment else (document.rejection_reason or ""),
        "bucket": current_assignment.status if current_assignment else document.status,
        "canApprove": current_assignment is not None and current_assignment.status == ApprovalAssignmentStatus.PENDING,
    }


def visible_requests(user: User):
    user_ids = list(visible_users(user).values_list("id", flat=True))
    return (
        Request.objects.filter(requester_id__in=user_ids)
        .select_related("requester", "manager", "department")
        .prefetch_related("attachments", "timeline_items")
        .order_by("-created_at")
    )


def visible_expenses(user: User):
    user_ids = list(visible_users(user).values_list("id", flat=True))
    return (
        Expense.objects.filter(owner_id__in=user_ids)
        .select_related("owner", "department")
        .order_by("-expense_date", "-created_at")
    )


def visible_approvals(user: User):
    if not can_approve_documents(user):
        return Document.objects.none()
    return (
        Document.objects.filter(approval_assignments__approver=user)
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


def visible_reports_payload(user: User) -> dict:
    users_qs = visible_users(user).select_related("department", "manager")
    requests_qs = list(visible_requests(user))
    expenses_qs = list(visible_expenses(user))
    expense_total = sum(Decimal(item.amount) for item in expenses_qs)
    request_status = Counter(item.status for item in requests_qs)
    top_submitters = Counter(item.owner.full_name for item in expenses_qs if item.owner)
    return {
        "summary": {
            "users": users_qs.count(),
            "requests": len(requests_qs),
            "expenses": len(expenses_qs),
            "expenseTotal": format_money(expense_total),
        },
        "requestStatus": dict(request_status),
        "topSubmitters": [{"name": name, "count": count} for name, count in top_submitters.most_common(5)],
        "requests": [serialize_request(item) for item in requests_qs],
        "expenses": [serialize_expense(item) for item in expenses_qs],
        "users": [serialize_user(item) for item in users_qs],
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


def build_bootstrap_payload(user: User) -> dict:
    requests_qs = list(visible_requests(user))
    expenses_qs = list(visible_expenses(user))
    approvals_qs = list(visible_approvals(user))
    users_qs = list(visible_users(user).select_related("department", "manager").order_by("created_at"))
    departments = list(Department.objects.order_by("name"))
    activities = list(
        AuditLog.objects.filter(actor_id__in=[item.id for item in users_qs]).select_related("actor").order_by("-created_at")[:6]
    )

    month_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date.month == date.today().month)
    year_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date.year == date.today().year)
    active_requests = sum(1 for item in requests_qs if item.status in {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW})
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

    today_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date == date.today())
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date >= week_start)

    return {
        "currentUser": serialize_current_user(user),
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
                "user": item.actor_name,
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
                {"id": item.id, "slug": item.slug, "name": item.full_name, "role": access_role_label(item.role)}
                for item in users_qs
                if item.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER}
            ],
            "users": [{"id": item.id, "name": item.full_name} for item in users_qs],
        },
    }
