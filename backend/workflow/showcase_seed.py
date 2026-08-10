from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from django.db import transaction
from django.utils import timezone as django_timezone

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
    Organization,
    OrganizationMembership,
    OrganizationPreference,
    Request,
    RequestApprovalAssignment,
    RequestPriority,
    RequestStatus,
    RequestTimeline,
    SectionAccessGrant,
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
)
from workflow.security import get_password_hash
from workflow.services import (
    CLOUD_STORAGE_FEATURE_KEY,
    CORE_FEATURE_KEY,
    PURCHASABLE_FEATURES,
    SHOWCASE_ORG_CODE,
    ensure_organization_wallets,
)


SHOWCASE_ORG_NAME = "کارنومند نمونه"
SHOWCASE_MANAGER_SLUG = "carnomand"
SHOWCASE_MANAGER_PASSWORD = "carnomand@123"
SHOWCASE_MANAGER_LEGACY_SLUGS = ("milad_dehestani",)
SHOWCASE_SMS_DAILY_LIMIT = 150
SHOWCASE_SMS_MONTHLY_LIMIT = 3000
SHOWCASE_MAIN_BALANCE = Decimal("28500000.00")
SHOWCASE_SMS_BALANCE = Decimal("4200000.00")

SECTION_KEYS = ("users", "approvals", "expenses", "reports", "settings")


def _utc_days_ago(days: int, hour: int = 10) -> datetime:
    base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    clamped_hour = max(0, min(23, hour))
    return (base - timedelta(days=days)).replace(hour=clamped_hour)


def _department(code: str, name: str) -> Department:
    department, _ = Department.objects.get_or_create(code=code, defaults={"name": name})
    if department.name != name:
        department.name = name
        department.save(update_fields=["name"])
    return department


def _ensure_user(
    *,
    slug: str,
    full_name: str,
    email: str,
    phone: str,
    role: str,
    job_title: str,
    avatar: str,
    department: Department | None,
    manager: User | None,
    password: str,
    organization: Organization,
) -> User:
    user, created = User.objects.update_or_create(
        slug=slug,
        defaults={
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password_hash": get_password_hash(password),
            "role": role,
            "job_title": job_title,
            "avatar": avatar,
            "bio": "",
            "is_active": True,
            "is_deleted": False,
            "department": department,
            "manager": manager,
            "bonus_amount": Decimal("0"),
            "penalty_amount": Decimal("0"),
        },
    )
    OrganizationMembership.objects.update_or_create(
        user=user,
        defaults={"organization": organization, "display_title": job_title},
    )
    UserSignature.objects.get_or_create(user=user, defaults={"signature_data": ""})
    if created:
        user.created_at = _utc_days_ago(40)
        user.save(update_fields=["created_at"])
    return user


def _set_wallet_balance(organization: Organization, key: str, balance: Decimal, note: str, actor: User | None) -> Wallet:
    """Set a display-only balance for showcase; never creates money-moving transactions."""
    del note, actor  # schematic wallet: no ledger side-effects
    ensure_organization_wallets(organization)
    wallet = Wallet.objects.select_for_update().get(organization=organization, key=key)
    wallet.balance = balance
    wallet.updated_at = django_timezone.now()
    wallet.is_active = True
    wallet.save(update_fields=["balance", "updated_at", "is_active"])
    WalletTransaction.objects.filter(organization=organization, wallet=wallet).delete()
    return wallet


def _migrate_legacy_manager_slug(organization: Organization) -> None:
    if User.objects.filter(slug=SHOWCASE_MANAGER_SLUG).exists():
        return
    for legacy_slug in SHOWCASE_MANAGER_LEGACY_SLUGS:
        legacy = (
            User.objects.filter(slug=legacy_slug, organization_membership__organization=organization)
            .select_related("organization_membership")
            .first()
        )
        if legacy is None:
            continue
        legacy.slug = SHOWCASE_MANAGER_SLUG
        legacy.email = "carnomand@carnomand-sample.local"
        legacy.password_hash = get_password_hash(SHOWCASE_MANAGER_PASSWORD)
        legacy.full_name = "کارنومند"
        legacy.save(update_fields=["slug", "email", "password_hash", "full_name"])
        return


def _activate_feature(organization: Organization, feature_key: str) -> FeaturePurchase | None:
    config = next((item for item in PURCHASABLE_FEATURES if item["feature_key"] == feature_key), None)
    if config is None or config.get("disabled"):
        return None
    total = Decimal(str(config.get("base_price") or 0))
    purchase, _ = FeaturePurchase.objects.update_or_create(
        organization=organization,
        feature_key=feature_key,
        defaults={
            "title": config["title"],
            "payment_plan": "cash",
            "total_amount": total,
            "paid_amount": total,
            "remaining_amount": Decimal("0"),
            "next_installment_due_at": None,
            "renewal_due_at": date.today() + timedelta(days=365),
            "annual_subscription_amount": Decimal(str(config.get("annual_subscription_amount") or 0)),
            "annual_subscription_installment_months": int(config.get("annual_subscription_installment_months") or 0),
            "is_active": True,
            "updated_at": django_timezone.now(),
        },
    )
    return purchase


def _clear_operational_data(organization: Organization, user_ids: list[int]) -> None:
    Request.objects.filter(requester_id__in=user_ids).delete()
    Expense.objects.filter(owner_id__in=user_ids).delete()
    Document.objects.filter(owner_id__in=user_ids).delete()
    AttendanceEvent.objects.filter(organization=organization).delete()
    SupportTicket.objects.filter(organization=organization).delete()
    SectionAccessGrant.objects.filter(organization=organization).delete()
    AuditLog.objects.filter(actor_id__in=user_ids).delete()


@transaction.atomic
def ensure_showcase_organization(*, reset: bool = False) -> dict:
    if reset:
        existing = Organization.objects.filter(code=SHOWCASE_ORG_CODE).first()
        if existing:
            user_ids = list(
                User.objects.filter(organization_membership__organization=existing).values_list("id", flat=True)
            )
            OrganizationMembership.objects.filter(organization=existing).delete()
            User.objects.filter(id__in=user_ids).delete()
            existing.delete()

    organization, created = Organization.objects.get_or_create(
        code=SHOWCASE_ORG_CODE,
        defaults={"name": SHOWCASE_ORG_NAME, "is_showcase": True},
    )
    if organization.name != SHOWCASE_ORG_NAME or not organization.is_showcase:
        organization.name = SHOWCASE_ORG_NAME
        organization.is_showcase = True
        organization.save(update_fields=["name", "is_showcase"])

    preference, _ = OrganizationPreference.objects.get_or_create(organization=organization)
    preference.two_factor_required = False
    preference.sms_daily_limit = SHOWCASE_SMS_DAILY_LIMIT
    preference.sms_monthly_limit = SHOWCASE_SMS_MONTHLY_LIMIT
    preference.updated_at = django_timezone.now()
    preference.save(
        update_fields=["two_factor_required", "sms_daily_limit", "sms_monthly_limit", "updated_at"]
    )

    _migrate_legacy_manager_slug(organization)

    departments = {
        "ops": _department("sample-ops", "عملیات نمونه"),
        "it": _department("sample-it", "فناوری نمونه"),
        "finance": _department("sample-finance", "مالی نمونه"),
        "hr": _department("sample-hr", "منابع انسانی نمونه"),
        "sales": _department("sample-sales", "فروش نمونه"),
    }

    manager = _ensure_user(
        slug=SHOWCASE_MANAGER_SLUG,
        full_name="کارنومند",
        email="carnomand@carnomand-sample.local",
        phone="09134279848",
        role=UserRole.ADMIN,
        job_title="مدیر مجموعه",
        avatar="کا",
        department=departments["ops"],
        manager=None,
        password=SHOWCASE_MANAGER_PASSWORD,
        organization=organization,
    )

    team_specs = [
        ("sample_sara", "سارا نوری", "sara.nouri@carnomand-sample.local", "09121110001", UserRole.MANAGER, "مدیر فنی", "سن", "it"),
        ("sample_reza", "رضا کاظمی", "reza.kazemi@carnomand-sample.local", "09121110002", UserRole.MANAGER, "مدیر مالی", "رک", "finance"),
        ("sample_neda", "ندا اکبری", "neda.akbari@carnomand-sample.local", "09121110003", UserRole.MANAGER, "مدیر منابع انسانی", "نا", "hr"),
        ("sample_omid", "امید شریفی", "omid.sharifi@carnomand-sample.local", "09121110004", UserRole.EXECUTIVE_MANAGER, "مدیر ارشد عملیات", "اع", "ops"),
        ("sample_parsa_mgr", "کیان صالحی", "kian.salehi@carnomand-sample.local", "09121110010", UserRole.MANAGER, "مدیر فروش", "کس", "sales"),
        ("sample_ali", "علی مرادی", "ali.moradi@carnomand-sample.local", "09121110005", UserRole.EMPLOYEE, "کارشناس زیرساخت", "عم", "it"),
        ("sample_mina", "مینا حسینی", "mina.hosseini@carnomand-sample.local", "09121110006", UserRole.EMPLOYEE, "کارشناس مالی", "مه", "finance"),
        ("sample_parsa", "پارسا جلالی", "parsa.jalali@carnomand-sample.local", "09121110007", UserRole.EMPLOYEE, "کارشناس فروش", "پج", "sales"),
        ("sample_fateme", "فاطمه رضایی", "fateme.rezaei@carnomand-sample.local", "09121110008", UserRole.EMPLOYEE, "کارشناس منابع انسانی", "فر", "hr"),
        ("sample_hossein", "حسین بابایی", "hossein.babaei@carnomand-sample.local", "09121110009", UserRole.EMPLOYEE, "کارشناس عملیات", "حب", "ops"),
    ]

    users_by_slug: dict[str, User] = {SHOWCASE_MANAGER_SLUG: manager}
    managers_by_dept = {
        "it": None,
        "finance": None,
        "hr": None,
        "ops": None,
        "sales": None,
    }

    for slug, full_name, email, phone, role, job_title, avatar, dept_key in team_specs:
        parent = manager if role != UserRole.EMPLOYEE else None
        user = _ensure_user(
            slug=slug,
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            job_title=job_title,
            avatar=avatar,
            department=departments[dept_key],
            manager=parent,
            password="UserDemo@1405",
            organization=organization,
        )
        users_by_slug[slug] = user
        if role in {UserRole.MANAGER, UserRole.EXECUTIVE_MANAGER}:
            managers_by_dept[dept_key] = user

    # Link employees to department managers
    for slug, *_rest, dept_key in team_specs:
        user = users_by_slug[slug]
        if user.role == UserRole.EMPLOYEE and managers_by_dept.get(dept_key):
            user.manager = managers_by_dept[dept_key]
            user.save(update_fields=["manager"])

    user_ids = [item.id for item in users_by_slug.values()]
    _clear_operational_data(organization, user_ids)

    for section_key in SECTION_KEYS:
        for slug in (
            SHOWCASE_MANAGER_SLUG,
            "sample_sara",
            "sample_reza",
            "sample_neda",
            "sample_omid",
            "sample_parsa_mgr",
        ):
            SectionAccessGrant.objects.get_or_create(
                organization=organization,
                section_key=section_key,
                user=users_by_slug[slug],
            )

    FeaturePurchase.objects.filter(organization=organization, feature_key=CLOUD_STORAGE_FEATURE_KEY).delete()
    _activate_feature(organization, CORE_FEATURE_KEY)
    _activate_feature(organization, "attendance")

    _set_wallet_balance(organization, "main", SHOWCASE_MAIN_BALANCE, "شارژ نمونه کیف پول اصلی", manager)
    _set_wallet_balance(organization, "sms", SHOWCASE_SMS_BALANCE, "شارژ نمونه کیف پول پیامک", manager)

    sara = users_by_slug["sample_sara"]
    reza = users_by_slug["sample_reza"]
    omid = users_by_slug["sample_omid"]
    ali = users_by_slug["sample_ali"]
    mina = users_by_slug["sample_mina"]
    parsa = users_by_slug["sample_parsa"]
    fateme = users_by_slug["sample_fateme"]
    hossein = users_by_slug["sample_hossein"]
    sales_manager = users_by_slug["sample_parsa_mgr"]

    request_rows = [
        ("REQ-SAMPLE-001", "تامین لپ‌تاپ برای تیم فروش", "نیاز به ۲ دستگاه لپ‌تاپ برای نیروهای جدید فروش.", RequestPriority.HIGH, RequestStatus.UNDER_REVIEW, "sales", parsa, sales_manager, [sales_manager], [parsa], 2),
        ("REQ-SAMPLE-002", "ارتقای سرور داخلی", "افزایش ظرفیت ذخیره‌سازی سرور عملیات.", RequestPriority.CRITICAL, RequestStatus.APPROVED, "it", ali, sara, [sara], [ali], 5),
        ("REQ-SAMPLE-003", "برگزاری دوره آموزشی ایمنی", "جلسه آموزشی ایمنی کار برای پرسنل عملیات.", RequestPriority.MEDIUM, RequestStatus.SUBMITTED, "hr", fateme, users_by_slug["sample_neda"], [users_by_slug["sample_neda"]], [fateme], 1),
        ("REQ-SAMPLE-004", "خرید ملزومات اداری", "سفارش کاغذ، کارتریج و لوازم میز کار.", RequestPriority.LOW, RequestStatus.APPROVED, "finance", mina, reza, [reza], [mina], 8),
        ("REQ-SAMPLE-005", "هماهنگی ماموریت خارج استان", "هماهنگی سفر کاری تیم فروش به اصفهان.", RequestPriority.HIGH, RequestStatus.REJECTED, "sales", parsa, sales_manager, [sales_manager], [parsa], 4),
        ("REQ-SAMPLE-006", "بازبینی دسترسی کاربران", "بازبینی سطح دسترسی سامانه برای نیروهای جدید.", RequestPriority.MEDIUM, RequestStatus.UNDER_REVIEW, "it", ali, sara, [sara, manager], [ali], 0),
    ]
    for code, title, description, priority, status, dept_key, requester, mgr, assigned_managers, assigned_employees, days_ago in request_rows:
        item = Request.objects.create(
            code=code,
            title=title,
            description=description,
            priority=priority,
            status=status,
            department=departments[dept_key],
            requester=requester,
            manager=mgr,
            deadline=date.today() + timedelta(days=7),
            created_at=_utc_days_ago(days_ago),
            updated_at=_utc_days_ago(max(days_ago - 1, 0)),
        )
        item.assigned_managers.set(assigned_managers)
        item.assigned_employees.set(assigned_employees)
        RequestTimeline.objects.create(
            request=item,
            action="ثبت درخواست",
            note="ایجاد داده نمونه برای دمو",
            actor_name=requester.full_name,
            created_at=item.created_at,
        )
        for approver in assigned_managers:
            assignment_status = ApprovalAssignmentStatus.PENDING
            if status == RequestStatus.APPROVED:
                assignment_status = ApprovalAssignmentStatus.APPROVED
            elif status == RequestStatus.REJECTED:
                assignment_status = ApprovalAssignmentStatus.REJECTED
            RequestApprovalAssignment.objects.create(
                request=item,
                approver=approver,
                status=assignment_status,
                decision_note="تایید نمونه" if assignment_status == ApprovalAssignmentStatus.APPROVED else "",
                acted_at=_utc_days_ago(max(days_ago - 1, 0)) if assignment_status != ApprovalAssignmentStatus.PENDING else None,
            )

    expense_rows = [
        ("EXP-SAMPLE-001", "هزینه تبلیغات دیجیتال", Decimal("1850000.00"), ExpenseCategory.MARKETING, ExpenseStatus.APPROVED, "sales", parsa, reza, 3),
        ("EXP-SAMPLE-002", "خرید تجهیزات شبکه", Decimal("4200000.00"), ExpenseCategory.TECHNOLOGY, ExpenseStatus.UNDER_REVIEW, "it", ali, sara, 1),
        ("EXP-SAMPLE-003", "ایاب و ذهاب ماموریت", Decimal("760000.00"), ExpenseCategory.TRANSPORTATION, ExpenseStatus.PENDING, "ops", hossein, omid, 0),
        ("EXP-SAMPLE-004", "تعمیر سیستم تهویه", Decimal("980000.00"), ExpenseCategory.MAINTENANCE, ExpenseStatus.APPROVED, "ops", hossein, omid, 6),
        ("EXP-SAMPLE-005", "ملزومات دفتر مرکزی", Decimal("540000.00"), ExpenseCategory.OFFICE_SUPPLIES, ExpenseStatus.REJECTED, "finance", mina, reza, 4),
        ("EXP-SAMPLE-006", "حق‌الزحمه مشاوره منابع انسانی", Decimal("1500000.00"), ExpenseCategory.MISCELLANEOUS, ExpenseStatus.APPROVED, "hr", fateme, users_by_slug["sample_neda"], 9),
    ]
    for code, title, amount, category, status, dept_key, owner, approver, days_ago in expense_rows:
        item = Expense.objects.create(
            code=code,
            title=title,
            amount=amount,
            category=category,
            status=status,
            progress=100 if status == ExpenseStatus.APPROVED else 45 if status == ExpenseStatus.UNDER_REVIEW else 20,
            expense_date=date.today() - timedelta(days=days_ago),
            notes="داده نمونه برای نمایش محصول",
            department=departments[dept_key],
            owner=owner,
            created_at=_utc_days_ago(days_ago),
        )
        assignment_status = ApprovalAssignmentStatus.PENDING
        if status == ExpenseStatus.APPROVED:
            assignment_status = ApprovalAssignmentStatus.APPROVED
        elif status == ExpenseStatus.REJECTED:
            assignment_status = ApprovalAssignmentStatus.REJECTED
        ExpenseApprovalAssignment.objects.create(
            expense=item,
            approver=approver,
            status=assignment_status,
            decision_note="بررسی نمونه",
            acted_at=_utc_days_ago(max(days_ago - 1, 0)) if assignment_status != ApprovalAssignmentStatus.PENDING else None,
        )

    document_rows = [
        ("DOC-SAMPLE-001", "قرارداد همکاری تامین‌کننده", "قرارداد سالانه خدمات پشتیبانی", "قرارداد", DocumentStatus.APPROVED, DocumentRisk.MEDIUM, "finance", mina, reza, 7),
        ("DOC-SAMPLE-002", "دستورالعمل ایمنی کارگاه", "نسخه به‌روز دستورالعمل ایمنی", "دستورالعمل", DocumentStatus.PENDING, DocumentRisk.LOW, "ops", hossein, omid, 2),
        ("DOC-SAMPLE-003", "پیشنهاد ارتقای زیرساخت", "پیشنهاد فنی ارتقای سرور", "پیشنهاد", DocumentStatus.WAITING_SIGNATURE, DocumentRisk.HIGH, "it", ali, sara, 1),
        ("DOC-SAMPLE-004", "گزارش ماهانه فروش", "خلاصه عملکرد فروش ماه جاری", "گزارش", DocumentStatus.REJECTED, DocumentRisk.LOW, "sales", parsa, sales_manager, 5),
    ]
    for code, title, description, doc_type, status, risk, dept_key, owner, approver, days_ago in document_rows:
        item = Document.objects.create(
            code=code,
            title=title,
            description=description,
            document_type=doc_type,
            status=status,
            risk=risk,
            confidentiality=ConfidentialityLevel.INTERNAL,
            department=departments[dept_key],
            owner=owner,
            file_name=f"{code.lower()}.pdf",
            uploaded_at=_utc_days_ago(days_ago),
            approved_at=_utc_days_ago(max(days_ago - 1, 0)) if status == DocumentStatus.APPROVED else None,
            rejected_at=_utc_days_ago(max(days_ago - 1, 0)) if status == DocumentStatus.REJECTED else None,
            rejection_reason="نیاز به اصلاح محتوا" if status == DocumentStatus.REJECTED else "",
        )
        assignment_status = ApprovalAssignmentStatus.PENDING
        if status == DocumentStatus.APPROVED:
            assignment_status = ApprovalAssignmentStatus.APPROVED
        elif status == DocumentStatus.REJECTED:
            assignment_status = ApprovalAssignmentStatus.REJECTED
        ApprovalAssignment.objects.create(
            document=item,
            approver=approver,
            status=assignment_status,
            decision_note="گردش نمونه سند",
            acted_at=_utc_days_ago(max(days_ago - 1, 0)) if assignment_status != ApprovalAssignmentStatus.PENDING else None,
        )

    for user, offset_hours in ((ali, 8), (mina, 7), (parsa, 6), (fateme, 5), (hossein, 4)):
        AttendanceEvent.objects.create(
            organization=organization,
            user=user,
            event_type=AttendanceEvent.EVENT_IN,
            source=AttendanceEvent.SOURCE_LINK,
            note="ورود نمونه",
            event_at=django_timezone.now() - timedelta(hours=offset_hours),
        )
    AttendanceEvent.objects.create(
        organization=organization,
        user=parsa,
        event_type=AttendanceEvent.EVENT_OUT,
        source=AttendanceEvent.SOURCE_MANAGER,
        note="خروج نمونه",
        event_at=django_timezone.now() - timedelta(hours=1),
    )

    ticket = SupportTicket.objects.create(
        organization=organization,
        requester=ali,
        subject="سوال درباره گزارش هزینه‌ها",
        message="در خروجی گزارش هزینه‌ها فیلتر تاریخ به‌درستی اعمال نمی‌شود؟ این تیکت نمونه است.",
        category=SupportTicketCategory.TECHNICAL,
        priority=SupportTicketPriority.MEDIUM,
        status=SupportTicketStatus.ANSWERED,
        response_text="در نسخه فعلی فیلتر تاریخ شمسی فعال است؛ در صورت تکرار جزئیات را ارسال کنید.",
        responded_by=manager,
        responded_at=_utc_days_ago(1),
        first_response_at=_utc_days_ago(1),
        last_message_at=_utc_days_ago(1),
        updated_at=_utc_days_ago(1),
    )
    SupportMessage.objects.create(
        ticket=ticket,
        sender=ali,
        sender_name=ali.full_name,
        sender_platform_role="",
        body=ticket.message,
        created_at=_utc_days_ago(2),
    )
    SupportMessage.objects.create(
        ticket=ticket,
        sender=manager,
        sender_name=manager.full_name,
        sender_platform_role="",
        body=ticket.response_text,
        created_at=_utc_days_ago(1),
    )
    open_ticket = SupportTicket.objects.create(
        organization=organization,
        requester=mina,
        subject="درخواست راهنمایی کیف پول",
        message="برای شارژ کیف پول پیامک چه مسیری پیشنهاد می‌شود؟",
        category=SupportTicketCategory.ACCOUNT,
        priority=SupportTicketPriority.LOW,
        status=SupportTicketStatus.OPEN,
        last_message_at=_utc_days_ago(0, hour=12),
        updated_at=_utc_days_ago(0, hour=12),
    )
    SupportMessage.objects.create(
        ticket=open_ticket,
        sender=mina,
        sender_name=mina.full_name,
        sender_platform_role="",
        body=open_ticket.message,
        created_at=_utc_days_ago(0, hour=12),
    )

    AuditLog.objects.create(
        actor=manager,
        actor_name=manager.full_name,
        action="showcase_seed",
        entity_type="organization",
        entity_code=organization.code,
        detail="بارگذاری داده نمونه کارنومند",
        icon="verified",
        created_at=_utc_days_ago(0, hour=9),
    )

    return {
        "organization_id": organization.id,
        "organization_code": organization.code,
        "organization_name": organization.name,
        "created": created,
        "manager_username": SHOWCASE_MANAGER_SLUG,
        "manager_password": SHOWCASE_MANAGER_PASSWORD,
        "manager_phone": manager.phone,
        "users": len(users_by_slug),
        "sms_daily_limit": SHOWCASE_SMS_DAILY_LIMIT,
        "sms_monthly_limit": SHOWCASE_SMS_MONTHLY_LIMIT,
        "main_balance": str(SHOWCASE_MAIN_BALANCE),
        "sms_balance": str(SHOWCASE_SMS_BALANCE),
        "wallet_mode": "schematic",
        "active_features": ["core_software", "attendance"],
        "inactive_features": ["cloud_storage", "accounting"],
    }
