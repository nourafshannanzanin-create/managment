from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction

from workflow.access import ensure_default_organization
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
    Request,
    RequestPriority,
    RequestStatus,
    RequestTimeline,
    User,
    UserRole,
)
from workflow.security import get_password_hash


@transaction.atomic
def seed_demo_data(reset: bool = False) -> None:
    if reset:
        ApprovalAssignment.objects.all().delete()
        Document.objects.all().delete()
        Expense.objects.all().delete()
        RequestTimeline.objects.all().delete()
        Request.objects.all().delete()
        AuditLog.objects.all().delete()
        OrganizationMembership.objects.all().delete()
        User.objects.all().delete()
        Department.objects.all().delete()

    if User.objects.exists():
        return

    organization = ensure_default_organization()
    departments = {
        code: Department.objects.create(code=code, name=name)
        for code, name in {
            "hq": "ستاد مرکزی",
            "it": "فناوری اطلاعات",
            "finance": "امور مالی",
            "hr": "منابع انسانی",
            "ops": "عملیات",
            "marketing": "بازاریابی",
            "procurement": "تدارکات",
        }.items()
    }

    users = {}
    for payload in [
        ("arman-karimi", "آرمان کریمی", "admin@karomand.local", UserRole.ADMIN, "مدیرعامل", "AK", "hq", None),
        ("sara-ahmadi", "سارا احمدی", "sara@karomand.local", UserRole.MANAGER, "مدیر فنی", "SA", "it", None),
        ("hamid-rezaei", "حمید رضایی", "hamid@karomand.local", UserRole.MANAGER, "مدیر مالی", "HR", "finance", None),
        ("navid-farhadi", "نوید فرهادی", "navid@karomand.local", UserRole.EXECUTIVE_MANAGER, "مدیر ارشد عملیات", "NF", "ops", None),
        ("niloufar-farahmand", "نیلوفر فرهمند", "niloufar@karomand.local", UserRole.MANAGER, "مدیر منابع انسانی", "NL", "hr", None),
        ("mahdi-amiri", "مهدی امیری", "mahdi@karomand.local", UserRole.EMPLOYEE, "کارشناس زیرساخت", "MA", "it", "sara-ahmadi"),
        ("elham-rostami", "الهام رستمی", "elham@karomand.local", UserRole.EMPLOYEE, "کارشناس بازاریابی", "ER", "marketing", "navid-farhadi"),
        ("mohammad-azad", "محمد آزاد", "mohammad@karomand.local", UserRole.EMPLOYEE, "کارشناس تدارکات", "MH", "procurement", "hamid-rezaei"),
        ("ramin-shayan", "رامین شایان", "ramin@karomand.local", UserRole.EMPLOYEE, "کارشناس فناوری", "RS", "it", "sara-ahmadi"),
        ("nafiseh-kazemi", "نفیسه کاظمی", "nafiseh@karomand.local", UserRole.EMPLOYEE, "کارشناس عملیات", "NK", "ops", "navid-farhadi"),
    ]:
        slug, full_name, email, role, job_title, avatar, department_code, manager_slug = payload
        manager = users.get(manager_slug)
        user = User.objects.create(
            slug=slug,
            full_name=full_name,
            email=email,
            phone=None,
            password_hash=get_password_hash("AdminSecret!" if role == UserRole.ADMIN else "UserSecret123!"),
            role=role,
            job_title=job_title,
            avatar=avatar,
            bio="",
            is_active=True,
            department=departments[department_code],
            manager=manager,
        )
        OrganizationMembership.objects.create(
            organization=organization,
            user=user,
            display_title=job_title,
        )
        users[slug] = user

    today = date.today()
    request_specs = [
        ("REQ-2401", "افزایش بودجه کمپین تابستان", users["elham-rostami"], users["navid-farhadi"], departments["marketing"], RequestPriority.HIGH, RequestStatus.SUBMITTED, today + timedelta(days=7)),
        ("REQ-2408", "نوسازی زیرساخت شبکه کارخانه", users["mahdi-amiri"], users["sara-ahmadi"], departments["it"], RequestPriority.CRITICAL, RequestStatus.UNDER_REVIEW, today + timedelta(days=12)),
        ("REQ-2389", "تمدید قرارداد تامین قطعات", users["mohammad-azad"], users["hamid-rezaei"], departments["procurement"], RequestPriority.MEDIUM, RequestStatus.APPROVED, today + timedelta(days=14)),
        ("REQ-2364", "راه اندازی داشبورد انبار منطقه ای", users["nafiseh-kazemi"], users["navid-farhadi"], departments["ops"], RequestPriority.HIGH, RequestStatus.REJECTED, today - timedelta(days=3)),
    ]
    for code, title, requester, manager, department, priority, status, deadline in request_specs:
        request_obj = Request.objects.create(
            code=code,
            title=title,
            description=title,
            requester=requester,
            manager=manager,
            department=department,
            priority=priority,
            status=status,
            deadline=deadline,
        )
        RequestTimeline.objects.create(request=request_obj, action="created", note="ایجاد درخواست", actor_name=requester.full_name)
        RequestTimeline.objects.create(request=request_obj, action="submitted", note="ثبت در سیستم", actor_name=requester.full_name)

    for payload in [
        ("EXP-91", "زیرساخت ابری", Decimal("2400000000"), ExpenseCategory.TECHNOLOGY, ExpenseStatus.APPROVED, 82, today - timedelta(days=2), "تمدید سرویس های ابری", departments["it"], users["ramin-shayan"]),
        ("EXP-88", "حمل و نقل بین شهری", Decimal("860000000"), ExpenseCategory.TRANSPORTATION, ExpenseStatus.UNDER_REVIEW, 54, today - timedelta(days=4), "هزینه لجستیک ارسال", departments["ops"], users["nafiseh-kazemi"]),
        ("EXP-84", "تجهیزات خط تولید", Decimal("3100000000"), ExpenseCategory.CAPITAL, ExpenseStatus.NEEDS_DOCUMENT, 91, today - timedelta(days=7), "نیازمند تکمیل مستندات", departments["ops"], users["mahdi-amiri"]),
        ("EXP-80", "تبلیغات دیجیتال", Decimal("1300000000"), ExpenseCategory.MARKETING, ExpenseStatus.APPROVED, 68, today - timedelta(days=11), "کمپین های تبلیغاتی", departments["marketing"], users["elham-rostami"]),
    ]:
        code, title, amount, category, status, progress, expense_date, notes, department, owner = payload
        Expense.objects.create(
            code=code,
            title=title,
            amount=amount,
            category=category,
            status=status,
            progress=progress,
            expense_date=expense_date,
            notes=notes,
            department=department,
            owner=owner,
        )

    doc = Document.objects.create(
        code="DOC-4201",
        title="قرارداد تامین سالانه",
        description="نیازمند تایید مدیر مالی و مدیر ارشد",
        document_type="قرارداد",
        status=DocumentStatus.PENDING,
        risk=DocumentRisk.MEDIUM,
        confidentiality=ConfidentialityLevel.INTERNAL,
        department=departments["finance"],
        owner=users["arman-karimi"],
    )
    ApprovalAssignment.objects.create(document=doc, approver=users["hamid-rezaei"], status=ApprovalAssignmentStatus.PENDING)
    ApprovalAssignment.objects.create(document=doc, approver=users["navid-farhadi"], status=ApprovalAssignmentStatus.PENDING)

    AuditLog.objects.create(actor=users["arman-karimi"], actor_name=users["arman-karimi"].full_name, action="login", entity_type="user", detail="ورود به سیستم", icon="login")
    AuditLog.objects.create(actor=users["mahdi-amiri"], actor_name=users["mahdi-amiri"].full_name, action="request_created", entity_type="request", detail="ثبت درخواست جدید", icon="assignment")
    AuditLog.objects.create(actor=users["elham-rostami"], actor_name=users["elham-rostami"].full_name, action="expense_created", entity_type="expense", detail="ثبت هزینه جدید", icon="payments")
