from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import AuditLog, Department, Document, Expense, Request, User
from app.models.enums import DocumentStatus, ExpenseCategory, ExpenseStatus, RequestPriority, RequestStatus, UserRole

PERSIAN_WEEK_DAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه شنبه", "چهارشنبه", "پنج شنبه", "جمعه"]


def relative_time(value: datetime) -> str:
    now = datetime.now(UTC)
    delta = now - value.astimezone(UTC)
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return f"{max(minutes, 1)} دقیقه پیش"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} ساعت پیش"
    days = hours // 24
    return f"{days} روز پیش"


def format_money(value: Decimal | int | float) -> str:
    amount = Decimal(value)
    billion = Decimal("1000000000")
    million = Decimal("1000000")
    if amount >= billion:
        return f"{(amount / billion).quantize(Decimal('0.1'))}B"
    if amount >= million:
        return f"{(amount / million).quantize(Decimal('0.1'))}M"
    return f"{int(amount):,}"


def format_date(value: date | None) -> str:
    return value.isoformat() if value else "بدون موعد"


def priority_label(value: RequestPriority) -> str:
    return {
        RequestPriority.LOW: "پایین",
        RequestPriority.MEDIUM: "متوسط",
        RequestPriority.HIGH: "بالا",
        RequestPriority.CRITICAL: "بحرانی",
    }[value]


def request_status_label(value: RequestStatus) -> str:
    return {
        RequestStatus.DRAFT: "پیش نویس",
        RequestStatus.SUBMITTED: "ارسال شده",
        RequestStatus.UNDER_REVIEW: "در بررسی",
        RequestStatus.APPROVED: "تایید شده",
        RequestStatus.REJECTED: "رد شده",
        RequestStatus.CLOSED: "بسته شده",
    }[value]


def expense_status_label(value: ExpenseStatus) -> str:
    return {
        ExpenseStatus.PENDING: "در انتظار",
        ExpenseStatus.UNDER_REVIEW: "در بررسی",
        ExpenseStatus.APPROVED: "تایید شده",
        ExpenseStatus.NEEDS_DOCUMENT: "نیازمند سند",
        ExpenseStatus.REJECTED: "رد شده",
    }[value]


def expense_category_label(value: ExpenseCategory) -> str:
    return {
        ExpenseCategory.SALARY: "حقوق",
        ExpenseCategory.EQUIPMENT: "تجهیزات",
        ExpenseCategory.MARKETING: "بازاریابی",
        ExpenseCategory.TRANSPORTATION: "حمل و نقل",
        ExpenseCategory.MAINTENANCE: "نگهداری",
        ExpenseCategory.OFFICE_SUPPLIES: "ملزومات اداری",
        ExpenseCategory.MISCELLANEOUS: "سایر",
        ExpenseCategory.TECHNOLOGY: "فناوری",
        ExpenseCategory.OPERATIONS: "عملیات",
        ExpenseCategory.CAPITAL: "سرمایه ای",
    }[value]


def document_status_label(value: DocumentStatus) -> str:
    return {
        DocumentStatus.PENDING: "در انتظار تایید",
        DocumentStatus.WAITING_SIGNATURE: "در انتظار امضا",
        DocumentStatus.APPROVED: "تایید شده",
        DocumentStatus.REJECTED: "رد شده",
        DocumentStatus.ARCHIVED: "آرشیو شده",
    }[value]


def document_risk_label(value: str) -> str:
    return {"low": "پایین", "medium": "متوسط", "high": "بالا"}[value]


def build_bootstrap_payload(session: Session, current_user: User) -> dict:
    requests = session.scalars(
        select(Request)
        .options(joinedload(Request.requester), joinedload(Request.manager), joinedload(Request.department))
        .order_by(Request.created_at.desc())
    ).unique().all()
    expenses = session.scalars(
        select(Expense)
        .options(joinedload(Expense.owner), joinedload(Expense.department))
        .order_by(Expense.expense_date.desc())
    ).unique().all()
    documents = session.scalars(
        select(Document)
        .options(joinedload(Document.owner), joinedload(Document.department))
        .order_by(Document.uploaded_at.desc())
    ).unique().all()
    users = session.scalars(select(User).options(joinedload(User.department)).order_by(User.created_at.asc())).all()
    activities = session.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(6)).all()

    month_total = sum(Decimal(expense.amount) for expense in expenses if expense.expense_date.month == date.today().month)
    year_total = sum(Decimal(expense.amount) for expense in expenses if expense.expense_date.year == date.today().year)
    active_requests = sum(1 for item in requests if item.status in {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW})
    pending_approvals = sum(1 for item in documents if item.status in {DocumentStatus.PENDING, DocumentStatus.WAITING_SIGNATURE})
    approved_documents = sum(1 for item in documents if item.status == DocumentStatus.APPROVED)
    rejected_requests = sum(1 for item in requests if item.status == RequestStatus.REJECTED)

    stats = [
        {
            "id": "active",
            "label": "درخواست های فعال",
            "value": str(active_requests),
            "detail": f"{rejected_requests} مورد بسته یا رد شده",
            "tone": "primary",
            "icon": "assignment",
        },
        {
            "id": "pending",
            "label": "تاییدات در انتظار",
            "value": str(pending_approvals),
            "detail": "اسناد و درخواست های نیازمند اقدام فوری",
            "tone": "warning",
            "icon": "pending_actions",
        },
        {
            "id": "monthly",
            "label": "هزینه های ماه",
            "value": format_money(month_total),
            "detail": f"سال جاری {format_money(year_total)}",
            "tone": "secondary",
            "icon": "payments",
        },
        {
            "id": "approved",
            "label": "اسناد تایید شده",
            "value": str(approved_documents),
            "detail": "میانگین زمان تایید 18 ساعت",
            "tone": "success",
            "icon": "fact_check",
        },
    ]

    expense_by_day: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
    start_day = date.today() - timedelta(days=6)
    for expense in expenses:
        if expense.expense_date >= start_day:
            expense_by_day[expense.expense_date] += Decimal(expense.amount)
    max_total = max(expense_by_day.values(), default=Decimal("1"))
    chart_data = []
    for index in range(7):
        current_day = start_day + timedelta(days=index)
        day_total = expense_by_day[current_day]
        scaled = int((day_total / max_total) * 100) if max_total > 0 else 0
        chart_data.append({"day": PERSIAN_WEEK_DAYS[index], "value": max(18, scaled) if day_total > 0 else 12})

    status_order = [
        ("پیش نویس", RequestStatus.DRAFT),
        ("ارسال شده", RequestStatus.SUBMITTED),
        ("در بررسی", RequestStatus.UNDER_REVIEW),
        ("تایید شده", RequestStatus.APPROVED),
        ("رد شده", RequestStatus.REJECTED),
    ]
    pipeline = [
        {"label": label, "count": sum(1 for item in requests if item.status == status)}
        for label, status in status_order
    ]

    request_items = [
        {
            "id": item.code,
            "title": item.title,
            "owner": item.requester.full_name if item.requester else "نامشخص",
            "manager": item.manager.full_name if item.manager else "تعیین نشده",
            "priority": priority_label(item.priority),
            "status": request_status_label(item.status),
            "department": item.department.name if item.department else "بدون واحد",
            "deadline": format_date(item.deadline),
            "description": item.description,
        }
        for item in requests
    ]

    expense_items = [
        {
            "id": item.code,
            "title": item.title,
            "amount": format_money(item.amount),
            "category": expense_category_label(item.category),
            "owner": item.owner.full_name if item.owner else "نامشخص",
            "status": expense_status_label(item.status),
            "progress": item.progress,
        }
        for item in expenses[:8]
    ]

    approval_items = [
        {
            "id": item.code,
            "title": item.title,
            "owner": item.owner.full_name if item.owner else "نامشخص",
            "type": item.document_type,
            "status": document_status_label(item.status),
            "department": item.department.name if item.department else "بدون واحد",
            "uploadedAt": item.uploaded_at.date().isoformat(),
            "risk": document_risk_label(item.risk.value),
            "summary": item.description,
        }
        for item in documents
    ]

    spotlight_users = []
    for item in users[:3]:
        kpi = "زمان پاسخگویی 4h"
        if item.role == UserRole.MANAGER:
            kpi = "96% تایید به موقع"
        elif item.role == UserRole.EMPLOYEE:
            user_request_count = sum(1 for req in requests if req.requester_id == item.id)
            kpi = f"{user_request_count} درخواست فعال"
        spotlight_users.append(
            {
                "name": item.full_name,
                "role": item.job_title,
                "department": item.department.name if item.department else "بدون واحد",
                "kpi": kpi,
            }
        )

    reports = [
        {
            "title": "گزارش درخواست ها",
            "description": "تحلیل بر اساس کاربر، مدیر، واحد و بازه زمانی",
            "export": "PDF / Excel / CSV",
        },
        {
            "title": "گزارش هزینه ها",
            "description": "ماهانه، فصلی، سالانه و تفکیک دسته بندی",
            "export": "Excel / CSV",
        },
        {
            "title": "گزارش اسناد",
            "description": "در انتظار، تایید شده، رد شده و آرشیو",
            "export": "PDF / Excel",
        },
    ]

    activity_items = [
        {
            "id": item.id,
            "user": item.actor_name,
            "action": item.action,
            "detail": item.detail,
            "time": relative_time(item.created_at),
            "icon": item.icon,
        }
        for item in activities
    ]

    technology_total = sum(
        Decimal(expense.amount) for expense in expenses if expense.category == ExpenseCategory.TECHNOLOGY
    )
    finance_department = session.scalar(select(Department).where(Department.code == "finance"))
    finance_request_count = sum(1 for item in requests if item.department_id == getattr(finance_department, "id", None))
    insights = [
        f"هزینه های فناوری این ماه به {format_money(technology_total)} رسیده و بیشترین فشار روی تاییدهای زیرساخت متمرکز است.",
        f"واحد مالی با {finance_request_count} درخواست بیشترین حجم گردش کار را دارد و زمان پاسخ مدیران رو به بهبود است.",
        f"{pending_approvals} سند و درخواست هم اکنون نیازمند اقدام نهایی هستند.",
    ]

    today_total = sum(Decimal(item.amount) for item in expenses if item.expense_date == date.today())
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_total = sum(Decimal(item.amount) for item in expenses if item.expense_date >= week_start)
    expense_summary = [
        {"label": "امروز", "value": format_money(today_total)},
        {"label": "این هفته", "value": format_money(week_total)},
        {"label": "این ماه", "value": format_money(month_total)},
        {"label": "امسال", "value": format_money(year_total)},
    ]

    approval_metrics = {
        "pending": pending_approvals,
        "approved": approved_documents,
        "rejected": sum(1 for item in documents if item.status == DocumentStatus.REJECTED),
    }

    settings_cards = [
        {
            "title": "امنیت",
            "description": "احراز هویت JWT، مدیریت نشست، ثبت لاگ فعالیت و کنترل دسترسی مبتنی بر نقش.",
        },
        {
            "title": "برندینگ",
            "description": "رنگ سازمان، فونت، لوگو و هویت بصری پرتال سازمانی.",
        },
        {
            "title": "اعلان ها",
            "description": "اعلان درون برنامه ای، ایمیل و تنظیم اولویت پیام ها.",
        },
        {
            "title": "یکپارچه سازی",
            "description": "آماده اتصال به ERP، CRM، حسابداری و ذخیره سازی اسناد.",
        },
    ]

    return {
        "currentUser": {
            "id": current_user.id,
            "slug": current_user.slug,
            "name": current_user.full_name,
            "role": current_user.job_title,
            "department": current_user.department.name if current_user.department else "بدون واحد",
            "avatar": current_user.avatar,
            "email": current_user.email,
        },
        "stats": stats,
        "chartData": chart_data,
        "pipeline": pipeline,
        "requests": request_items,
        "expenses": expense_items,
        "approvals": approval_items,
        "users": spotlight_users,
        "reports": reports,
        "activities": activity_items,
        "insights": insights,
        "expenseSummary": expense_summary,
        "approvalMetrics": approval_metrics,
        "settingsCards": settings_cards,
    }
