from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import AuditLog, Department, Document, Expense, Request, RequestTimeline, User
from app.models.enums import (
    ConfidentialityLevel,
    DocumentRisk,
    DocumentStatus,
    ExpenseCategory,
    ExpenseStatus,
    RequestPriority,
    RequestStatus,
    UserRole,
)


def seed_database(session: Session) -> None:
    departments = {
        "hq": Department(code="hq", name="ستاد مرکزی"),
        "it": Department(code="it", name="فناوری اطلاعات"),
        "finance": Department(code="finance", name="امور مالی"),
        "hr": Department(code="hr", name="منابع انسانی"),
        "ops": Department(code="ops", name="عملیات"),
        "marketing": Department(code="marketing", name="بازاریابی"),
        "procurement": Department(code="procurement", name="تدارکات"),
    }
    session.add_all(departments.values())
    session.flush()

    users = {
        "admin": User(
            slug="arman-karimi",
            full_name="آرمان کریمی",
            email="admin@workflow.local",
            phone="09120000001",
            password_hash=get_password_hash("Admin123!"),
            role=UserRole.ADMIN,
            job_title="مدیر ارشد عملیات",
            avatar="AK",
            department_id=departments["hq"].id,
            bio="مسئول نظارت بر گردش کار، هزینه‌ها و تایید اسناد در سطح سازمان.",
        ),
        "sara": User(
            slug="sara-ahmadi",
            full_name="سارا احمدی",
            email="sara@workflow.local",
            phone="09120000002",
            password_hash=get_password_hash("Manager123!"),
            role=UserRole.MANAGER,
            job_title="مدیر فنی",
            avatar="SA",
            department_id=departments["it"].id,
        ),
        "hamid": User(
            slug="hamid-rezaei",
            full_name="حمید رضایی",
            email="hamid@workflow.local",
            phone="09120000003",
            password_hash=get_password_hash("Manager123!"),
            role=UserRole.MANAGER,
            job_title="مدیر مالی",
            avatar="HR",
            department_id=departments["finance"].id,
        ),
        "navid": User(
            slug="navid-farhadi",
            full_name="نوید فرهادی",
            email="navid@workflow.local",
            phone="09120000004",
            password_hash=get_password_hash("Manager123!"),
            role=UserRole.EXECUTIVE_MANAGER,
            job_title="مدیر اجرایی",
            avatar="NF",
            department_id=departments["ops"].id,
        ),
        "niloufar": User(
            slug="niloufar-farahmand",
            full_name="نیلوفر فرهمند",
            email="niloufar@workflow.local",
            phone="09120000005",
            password_hash=get_password_hash("Manager123!"),
            role=UserRole.MANAGER,
            job_title="مدیر منابع انسانی",
            avatar="NF",
            department_id=departments["hr"].id,
        ),
        "mahdi": User(
            slug="mahdi-amiri",
            full_name="مهدی امیری",
            email="mahdi@workflow.local",
            phone="09120000006",
            password_hash=get_password_hash("Employee123!"),
            role=UserRole.EMPLOYEE,
            job_title="کارشناس زیرساخت",
            avatar="MA",
            department_id=departments["it"].id,
        ),
        "elham": User(
            slug="elham-rostami",
            full_name="الهام رستمی",
            email="elham@workflow.local",
            phone="09120000007",
            password_hash=get_password_hash("Employee123!"),
            role=UserRole.EMPLOYEE,
            job_title="کارشناس بازاریابی",
            avatar="ER",
            department_id=departments["marketing"].id,
        ),
        "mohammad": User(
            slug="mohammad-azad",
            full_name="محمد آزاد",
            email="mohammad@workflow.local",
            phone="09120000008",
            password_hash=get_password_hash("Employee123!"),
            role=UserRole.EMPLOYEE,
            job_title="کارشناس تدارکات",
            avatar="MA",
            department_id=departments["procurement"].id,
        ),
        "ramin": User(
            slug="ramin-shayan",
            full_name="رامین شایان",
            email="ramin@workflow.local",
            phone="09120000009",
            password_hash=get_password_hash("Employee123!"),
            role=UserRole.EMPLOYEE,
            job_title="کارشناس فناوری",
            avatar="RS",
            department_id=departments["it"].id,
        ),
        "nafiseh": User(
            slug="nafiseh-kazemi",
            full_name="نفیسه کاظمی",
            email="nafiseh@workflow.local",
            phone="09120000010",
            password_hash=get_password_hash("Employee123!"),
            role=UserRole.EMPLOYEE,
            job_title="کارشناس عملیات",
            avatar="NK",
            department_id=departments["ops"].id,
        ),
        "sara-fallah": User(
            slug="sara-fallah",
            full_name="سارا فلاح",
            email="fallah@workflow.local",
            phone="09120000011",
            password_hash=get_password_hash("Employee123!"),
            role=UserRole.EMPLOYEE,
            job_title="کارشناس قراردادها",
            avatar="SF",
            department_id=departments["it"].id,
        ),
    }
    session.add_all(users.values())
    session.flush()

    requests = [
        Request(
            code="REQ-2408",
            title="نوسازی زیرساخت شبکه کارخانه",
            description="تعویض سوییچ‌های لایه توزیع، بهبود افزونگی و آماده‌سازی برای گسترش خط تولید.",
            priority=RequestPriority.CRITICAL,
            status=RequestStatus.UNDER_REVIEW,
            department_id=departments["it"].id,
            requester_id=users["mahdi"].id,
            manager_id=users["sara"].id,
            deadline=date.today() + timedelta(days=14),
        ),
        Request(
            code="REQ-2401",
            title="افزایش بودجه کمپین تابستان",
            description="درخواست افزایش بودجه تبلیغات عملکردی برای رشد لید ورودی و پوشش رسانه‌ای.",
            priority=RequestPriority.HIGH,
            status=RequestStatus.SUBMITTED,
            department_id=departments["marketing"].id,
            requester_id=users["elham"].id,
            manager_id=users["navid"].id,
            deadline=date.today() + timedelta(days=9),
        ),
        Request(
            code="REQ-2389",
            title="تمدید قرارداد تامین قطعات",
            description="تمدید قرارداد تامین قطعات یدکی به همراه بازبینی SLA و زمان تحویل.",
            priority=RequestPriority.MEDIUM,
            status=RequestStatus.APPROVED,
            department_id=departments["procurement"].id,
            requester_id=users["mohammad"].id,
            manager_id=users["hamid"].id,
            deadline=date.today() + timedelta(days=18),
        ),
        Request(
            code="REQ-2377",
            title="ارتقای سامانه حضور و غیاب",
            description="یکپارچه‌سازی سامانه تردد با پرتال منابع انسانی برای گزارش‌گیری بهتر.",
            priority=RequestPriority.MEDIUM,
            status=RequestStatus.DRAFT,
            department_id=departments["hr"].id,
            requester_id=users["niloufar"].id,
            manager_id=users["niloufar"].id,
            deadline=date.today() + timedelta(days=21),
        ),
        Request(
            code="REQ-2364",
            title="راه‌اندازی داشبورد انبار منطقه‌ای",
            description="نمایش موجودی لحظه‌ای و هشدار نقطه سفارش برای سه انبار عملیاتی.",
            priority=RequestPriority.HIGH,
            status=RequestStatus.REJECTED,
            department_id=departments["ops"].id,
            requester_id=users["nafiseh"].id,
            manager_id=users["navid"].id,
            deadline=date.today() - timedelta(days=1),
        ),
    ]
    session.add_all(requests)
    session.flush()

    request_timelines = [
        RequestTimeline(
            request_id=requests[0].id,
            action="created",
            note="ثبت اولیه توسط کارمند",
            actor_name="مهدی امیری",
        ),
        RequestTimeline(
            request_id=requests[0].id,
            action="assigned",
            note="ارجاع به مدیر مسئول",
            actor_name="آرمان کریمی",
        ),
        RequestTimeline(
            request_id=requests[0].id,
            action="review",
            note="در حال بررسی فنی و بودجه‌ای",
            actor_name="سارا احمدی",
        ),
    ]
    session.add_all(request_timelines)

    today = date.today()
    expenses = [
        Expense(
            code="EXP-91",
            title="زیرساخت ابری",
            amount=Decimal("2400000000"),
            category=ExpenseCategory.TECHNOLOGY,
            status=ExpenseStatus.APPROVED,
            progress=82,
            expense_date=today - timedelta(days=1),
            notes="تمدید سرویس‌های مانیتورینگ و ذخیره‌سازی ابری.",
            department_id=departments["it"].id,
            owner_id=users["ramin"].id,
        ),
        Expense(
            code="EXP-88",
            title="حمل و نقل بین شهری",
            amount=Decimal("860000000"),
            category=ExpenseCategory.TRANSPORTATION,
            status=ExpenseStatus.UNDER_REVIEW,
            progress=54,
            expense_date=today - timedelta(days=3),
            notes="هزینه لجستیک ارسال قطعات به سایت جنوبی.",
            department_id=departments["ops"].id,
            owner_id=users["nafiseh"].id,
        ),
        Expense(
            code="EXP-84",
            title="تجهیزات خط تولید",
            amount=Decimal("3100000000"),
            category=ExpenseCategory.CAPITAL,
            status=ExpenseStatus.NEEDS_DOCUMENT,
            progress=91,
            expense_date=today - timedelta(days=8),
            notes="نیازمند تکمیل مستندات خرید و ضمانت.",
            department_id=departments["ops"].id,
            owner_id=users["mahdi"].id,
        ),
        Expense(
            code="EXP-80",
            title="تبلیغات دیجیتال",
            amount=Decimal("1300000000"),
            category=ExpenseCategory.MARKETING,
            status=ExpenseStatus.APPROVED,
            progress=68,
            expense_date=today - timedelta(days=14),
            notes="هزینه کمپین‌های جست‌وجو و شبکه‌های اجتماعی.",
            department_id=departments["marketing"].id,
            owner_id=users["elham"].id,
        ),
        Expense(
            code="EXP-76",
            title="لایسنس امنیتی",
            amount=Decimal("740000000"),
            category=ExpenseCategory.TECHNOLOGY,
            status=ExpenseStatus.APPROVED,
            progress=100,
            expense_date=today - timedelta(days=5),
            notes="تمدید سامانه EDR و SIEM.",
            department_id=departments["it"].id,
            owner_id=users["ramin"].id,
        ),
    ]
    session.add_all(expenses)

    documents = [
        Document(
            code="DOC-2841",
            title="قرارداد توسعه ERP",
            description="فاز دوم استقرار سامانه مالی و انبار برای سه سایت عملیاتی نیازمند تایید نهایی است.",
            document_type="قرارداد",
            status=DocumentStatus.WAITING_SIGNATURE,
            risk=DocumentRisk.HIGH,
            confidentiality=ConfidentialityLevel.CONFIDENTIAL,
            department_id=departments["it"].id,
            owner_id=users["sara-fallah"].id,
            uploaded_at=datetime.now(timezone.utc) - timedelta(days=2),
        ),
        Document(
            code="DOC-2816",
            title="فاکتور تجهیزات دیتاسنتر",
            description="شامل رک، UPS و سوییچ‌های توزیع برای سایت پشتیبان.",
            document_type="فاکتور",
            status=DocumentStatus.PENDING,
            risk=DocumentRisk.MEDIUM,
            confidentiality=ConfidentialityLevel.INTERNAL,
            department_id=departments["it"].id,
            owner_id=users["ramin"].id,
            uploaded_at=datetime.now(timezone.utc) - timedelta(days=4),
        ),
        Document(
            code="DOC-2764",
            title="الحاقیه خدمات منابع انسانی",
            description="افزودن بند SLA برای پشتیبانی شیفت شب و آموزش پرسنل جدید.",
            document_type="الحاقیه",
            status=DocumentStatus.APPROVED,
            risk=DocumentRisk.LOW,
            confidentiality=ConfidentialityLevel.INTERNAL,
            department_id=departments["hr"].id,
            owner_id=users["niloufar"].id,
            uploaded_at=datetime.now(timezone.utc) - timedelta(days=7),
            approved_at=datetime.now(timezone.utc) - timedelta(days=5),
        ),
    ]
    session.add_all(documents)

    audits = [
        AuditLog(
            actor_id=users["elham"].id,
            actor_name="سارا علوی",
            action="درخواست جدید ثبت کرد",
            entity_type="request",
            entity_code="REQ-2401",
            detail="خرید تجهیزات سخت افزاری تیم فنی",
            icon="add_task",
        ),
        AuditLog(
            actor_id=users["hamid"].id,
            actor_name="مدیر مالی",
            action="سندی را تایید کرد",
            entity_type="document",
            entity_code="DOC-2764",
            detail="گزارش هزینه‌های سفر نمایشگاه دبی",
            icon="verified",
        ),
        AuditLog(
            actor_id=users["mahdi"].id,
            actor_name="علی رضایی",
            action="پیامی ارسال کرد",
            entity_type="comment",
            entity_code="REQ-2408",
            detail="لطفا فاکتورهای مربوط به پروژه آلفا را بررسی کنید.",
            icon="chat",
        ),
    ]
    session.add_all(audits)
    session.commit()
