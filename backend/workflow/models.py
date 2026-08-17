from django.db import models
from django.utils import timezone
from uuid import uuid4
from datetime import time as dt_time


class UserRole(models.TextChoices):
    ADMIN = "admin", "مدیرعامل"
    EXECUTIVE_MANAGER = "executive_manager", "مدیر ارشد"
    MANAGER = "manager", "مدیر"
    EMPLOYEE = "employee", "کارمند"


class PlatformRole(models.TextChoices):
    NONE = "", ""
    HQ_ADMIN = "hq_admin", "HQ Admin"
    HQ_SUPPORT = "hq_support", "HQ Support"


class RequestPriority(models.TextChoices):
    LOW = "low", "پایین"
    MEDIUM = "medium", "متوسط"
    HIGH = "high", "بالا"
    CRITICAL = "critical", "بحرانی"


class RequestType(models.TextChoices):
    GENERAL = "general", "عمومی"
    LEAVE_HOURLY = "leave_hourly", "مرخصی ساعتی"
    LEAVE_DAILY = "leave_daily", "مرخصی روزانه"
    MISSION = "mission", "مأموریت"
    OVERTIME = "overtime", "اضافه‌کار"
    REMOTE = "remote", "دورکاری"
    PURCHASE = "purchase", "خرید/تدارکات"


class RequestStatus(models.TextChoices):
    DRAFT = "draft", "پیش نویس"
    SUBMITTED = "submitted", "ثبت شده"
    UNDER_REVIEW = "under_review", "در بررسی"
    APPROVED = "approved", "تایید شده"
    REJECTED = "rejected", "رد شده"
    CLOSED = "closed", "بسته شده"


class ExpenseStatus(models.TextChoices):
    PENDING = "pending", "در انتظار"
    UNDER_REVIEW = "under_review", "در بررسی"
    APPROVED = "approved", "تایید شده"
    NEEDS_DOCUMENT = "needs_document", "نیازمند سند"
    REJECTED = "rejected", "رد شده"


class ExpenseCategory(models.TextChoices):
    SALARY = "salary", "حقوق"
    EQUIPMENT = "equipment", "تجهیزات"
    MARKETING = "marketing", "بازاریابی"
    TRANSPORTATION = "transportation", "حمل و نقل"
    MAINTENANCE = "maintenance", "نگهداری"
    OFFICE_SUPPLIES = "office_supplies", "ملزومات"
    MISCELLANEOUS = "miscellaneous", "سایر"
    TECHNOLOGY = "technology", "فناوری"
    OPERATIONS = "operations", "عملیات"
    CAPITAL = "capital", "سرمایه ای"


class DocumentStatus(models.TextChoices):
    PENDING = "pending", "در انتظار"
    WAITING_SIGNATURE = "waiting_signature", "در انتظار امضا"
    APPROVED = "approved", "تایید شده"
    REJECTED = "rejected", "رد شده"
    ARCHIVED = "archived", "بایگانی شده"


class DocumentRisk(models.TextChoices):
    LOW = "low", "پایین"
    MEDIUM = "medium", "متوسط"
    HIGH = "high", "بالا"


class ConfidentialityLevel(models.TextChoices):
    PUBLIC = "public", "عمومی"
    INTERNAL = "internal", "داخلی"
    CONFIDENTIAL = "confidential", "محرمانه"
    STRICT = "strict", "خیلی محرمانه"


class ApprovalAssignmentStatus(models.TextChoices):
    PENDING = "pending", "در انتظار"
    APPROVED = "approved", "تایید شده"
    REJECTED = "rejected", "رد شده"


class SupportTicketStatus(models.TextChoices):
    OPEN = "open", "Open"
    PENDING = "pending", "Pending"
    ANSWERED = "answered", "Answered"
    CLOSED = "closed", "Closed"


class SupportTicketPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class SupportTicketCategory(models.TextChoices):
    TECHNICAL = "technical", "Technical"
    FINANCIAL = "financial", "Financial"
    OPERATIONS = "operations", "Operations"
    ACCOUNT = "account", "Account"
    OTHER = "other", "Other"


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class Organization(TimeStampedModel):
    code = models.CharField(max_length=80, unique=True, db_index=True)
    name = models.CharField(max_length=180, unique=True)
    is_showcase = models.BooleanField(default=False, db_index=True)
    province_id = models.PositiveIntegerField(blank=True, null=True)
    province_name = models.CharField(max_length=120, blank=True, default="")
    city_id = models.PositiveIntegerField(blank=True, null=True)
    city_name = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        db_table = "organizations"


class Department(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "departments"


class User(TimeStampedModel):
    slug = models.CharField(max_length=80, unique=True, db_index=True)
    full_name = models.CharField(max_length=120)
    email = models.EmailField(max_length=160, unique=True, db_index=True)
    phone = models.CharField(max_length=40, blank=True, null=True)
    password_hash = models.CharField(max_length=255)
    password_plain = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(max_length=32, choices=UserRole.choices)
    platform_role = models.CharField(max_length=32, choices=PlatformRole.choices, blank=True, default="")
    job_title = models.CharField(max_length=120)
    avatar = models.CharField(max_length=8)
    avatar_image = models.CharField(max_length=255, blank=True, default="")
    bio = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    bonus_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    penalty_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    insurance_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    finance_updated_at = models.DateTimeField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True, related_name="users")
    manager = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, related_name="direct_reports")
    last_login_at = models.DateTimeField(blank=True, null=True)
    attendance_token = models.CharField(max_length=64, unique=True, db_index=True, default=uuid4)
    support_star_rating = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    support_rating_count = models.PositiveIntegerField(default=0)
    support_customer_satisfaction_avg = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    support_response_quality_avg = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    support_first_response_minutes_avg = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    support_total_responses = models.PositiveIntegerField(default=0)
    support_resolved_tickets_count = models.PositiveIntegerField(default=0)
    support_last_scored_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="deleted_users",
    )

    class Meta:
        db_table = "users"


class UserEntrustedItem(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="entrusted_items")
    title = models.CharField(max_length=180)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    entrusted_at = models.DateField(default=timezone.localdate)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "user_entrusted_items"
        ordering = ["-entrusted_at", "-id"]


class OrganizationMembership(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="organization_membership")
    display_title = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        db_table = "organization_memberships"


class OrganizationPreference(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="preferences")
    two_factor_required = models.BooleanField(default=True)
    sms_daily_limit = models.PositiveIntegerField(default=0)
    sms_monthly_limit = models.PositiveIntegerField(default=0)
    attendance_latitude = models.FloatField(blank=True, null=True)
    attendance_longitude = models.FloatField(blank=True, null=True)
    attendance_location_label = models.CharField(max_length=255, blank=True, default="")
    attendance_radius_meters = models.PositiveIntegerField(default=20)
    work_day_start_time = models.TimeField(default=dt_time(9, 0))
    work_day_end_time = models.TimeField(default=dt_time(17, 0))
    monthly_leave_hours = models.PositiveIntegerField(default=20)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "organization_preferences"

    @property
    def has_attendance_location(self) -> bool:
        return self.attendance_latitude is not None and self.attendance_longitude is not None


class SectionAccessGrant(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="section_access_grants")
    section_key = models.CharField(max_length=40, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="section_access_grants")

    class Meta:
        db_table = "section_access_grants"
        constraints = [
            models.UniqueConstraint(fields=["organization", "section_key", "user"], name="uq_section_access_grant"),
        ]


class Wallet(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="wallets")
    key = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    low_balance_threshold = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "wallets"
        constraints = [
            models.UniqueConstraint(fields=["organization", "key"], name="uq_organization_wallet_key"),
        ]


class WalletTransaction(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="wallet_transactions")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="wallet_transactions")
    direction = models.CharField(max_length=12)
    transaction_type = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    balance_after = models.DecimalField(max_digits=18, decimal_places=2)
    note = models.TextField(blank=True)
    reference_id = models.CharField(max_length=80, blank=True)
    transacted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "wallet_transactions"
        indexes = [
            models.Index(fields=["organization", "-transacted_at"], name="idx_wallet_tx_org_date"),
            models.Index(fields=["wallet", "-transacted_at"], name="idx_wallet_tx_wallet_date"),
        ]


class FeaturePurchase(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="feature_purchases")
    feature_key = models.CharField(max_length=60, db_index=True)
    title = models.CharField(max_length=140)
    payment_plan = models.CharField(max_length=24, default="cash")
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    next_installment_due_at = models.DateField(blank=True, null=True)
    renewal_due_at = models.DateField(blank=True, null=True)
    annual_subscription_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    annual_subscription_installment_months = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "feature_purchases"
        constraints = [
            models.UniqueConstraint(fields=["organization", "feature_key"], name="uq_organization_feature_purchase"),
        ]


class AttendanceEvent(TimeStampedModel):
    EVENT_IN = "in"
    EVENT_OUT = "out"
    SOURCE_MANAGER = "manager"
    SOURCE_LINK = "link"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="attendance_events")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendance_events")
    event_type = models.CharField(max_length=12, choices=((EVENT_IN, "ورود"), (EVENT_OUT, "خروج")))
    source = models.CharField(max_length=20, choices=((SOURCE_MANAGER, "ثبت مدیر"), (SOURCE_LINK, "لینک پرسنل")), default=SOURCE_LINK)
    note = models.TextField(blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    distance_meters = models.FloatField(blank=True, null=True)
    event_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "attendance_events"
        indexes = [
            models.Index(fields=["organization", "-event_at"], name="idx_attendance_org_time"),
            models.Index(fields=["user", "-event_at"], name="idx_attendance_user_time"),
        ]


class SupportTicket(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="support_tickets")
    requester = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="support_tickets")
    subject = models.CharField(max_length=180)
    message = models.TextField()
    category = models.CharField(max_length=32, choices=SupportTicketCategory.choices, default=SupportTicketCategory.TECHNICAL)
    priority = models.CharField(max_length=32, choices=SupportTicketPriority.choices, default=SupportTicketPriority.MEDIUM)
    status = models.CharField(max_length=32, choices=SupportTicketStatus.choices, default=SupportTicketStatus.OPEN)
    response_text = models.TextField(blank=True, default="")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assigned_support_tickets",
    )
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="answered_support_tickets")
    responded_at = models.DateTimeField(blank=True, null=True)
    first_response_at = models.DateTimeField(blank=True, null=True)
    response_quality_score = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    closed_at = models.DateTimeField(blank=True, null=True)
    last_message_at = models.DateTimeField(blank=True, null=True)
    customer_satisfaction = models.IntegerField(blank=True, null=True)
    customer_feedback = models.TextField(blank=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "support_tickets"
        indexes = [
            models.Index(fields=["organization", "-updated_at"], name="idx_support_ticket_org_date"),
            models.Index(fields=["status", "-updated_at"], name="idx_support_ticket_status"),
            models.Index(fields=["assigned_to", "-last_message_at"], name="idx_support_ticket_assignee"),
        ]


class SupportMessage(TimeStampedModel):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="support_messages")
    sender_name = models.CharField(max_length=120)
    sender_platform_role = models.CharField(max_length=32, blank=True)
    body = models.TextField()
    is_internal = models.BooleanField(default=False)

    class Meta:
        db_table = "support_messages"
        indexes = [
            models.Index(fields=["ticket", "created_at"], name="idx_support_msg_ticket_date"),
        ]


class SupportAttachment(TimeStampedModel):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="attachments")
    original_name = models.CharField(max_length=255)
    stored_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120, blank=True, null=True)
    size_bytes = models.IntegerField(default=0)

    class Meta:
        db_table = "support_attachments"


class RegistrationRequest(TimeStampedModel):
    ticket = models.OneToOneField(SupportTicket, on_delete=models.CASCADE, related_name="registration_request")
    organization_name = models.CharField(max_length=180)
    manager_name = models.CharField(max_length=120)
    manager_username = models.CharField(max_length=80)
    manager_email = models.EmailField(max_length=160, blank=True)
    manager_phone = models.CharField(max_length=40)
    manager_password_hash = models.CharField(max_length=255)
    province_id = models.PositiveIntegerField(blank=True, null=True)
    province_name = models.CharField(max_length=120, blank=True, default="")
    city_id = models.PositiveIntegerField(blank=True, null=True)
    city_name = models.CharField(max_length=120, blank=True, default="")
    status = models.CharField(max_length=24, default="pending", db_index=True)
    company_code = models.CharField(max_length=80, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviewed_registration_requests")
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_organization = models.OneToOneField(Organization, on_delete=models.SET_NULL, blank=True, null=True, related_name="source_registration_request")

    class Meta:
        db_table = "registration_requests"


class UserSignature(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="signature")
    signature_data = models.TextField()
    stamp_data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_signatures"


class Request(models.Model):
    code = models.CharField(max_length=40, unique=True, db_index=True)
    title = models.CharField(max_length=180)
    description = models.TextField()
    request_type = models.CharField(max_length=32, choices=RequestType.choices, default=RequestType.GENERAL, db_index=True)
    priority = models.CharField(max_length=32, choices=RequestPriority.choices)
    status = models.CharField(max_length=32, choices=RequestStatus.choices, default=RequestStatus.SUBMITTED)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True, related_name="requests")
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_requests")
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="managed_requests")
    assigned_managers = models.ManyToManyField(User, blank=True, related_name="assigned_requests")
    assigned_employees = models.ManyToManyField(User, blank=True, related_name="employee_assigned_requests")
    deadline = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "requests"


class LeaveRequest(TimeStampedModel):
    MODE_HOURLY = "hourly"
    MODE_DAILY = "daily"

    request = models.OneToOneField(Request, on_delete=models.CASCADE, related_name="leave_request")
    mode = models.CharField(max_length=16, choices=((MODE_HOURLY, "ساعتی"), (MODE_DAILY, "روزانه")), default=MODE_HOURLY)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=32, choices=RequestStatus.choices, default=RequestStatus.SUBMITTED)

    class Meta:
        db_table = "leave_requests"
        indexes = [
            models.Index(fields=["starts_at", "ends_at"], name="idx_leave_request_range"),
        ]


class RequestAttachment(TimeStampedModel):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="attachments")
    original_name = models.CharField(max_length=255)
    stored_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120, blank=True, null=True)
    size_bytes = models.IntegerField()

    class Meta:
        db_table = "request_attachments"


class RequestTimeline(TimeStampedModel):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="timeline_items")
    action = models.CharField(max_length=120)
    note = models.TextField(blank=True)
    actor_name = models.CharField(max_length=120)

    class Meta:
        db_table = "request_timeline"


class RequestApprovalAssignment(TimeStampedModel):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="approval_assignments")
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="request_approval_assignments")
    status = models.CharField(max_length=32, choices=ApprovalAssignmentStatus.choices, default=ApprovalAssignmentStatus.PENDING)
    decision_note = models.TextField(blank=True, null=True)
    acted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "request_approval_assignments"
        constraints = [
            models.UniqueConstraint(fields=["request", "approver"], name="uq_request_approver"),
        ]


class Expense(models.Model):
    code = models.CharField(max_length=40, unique=True, db_index=True)
    title = models.CharField(max_length=180)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    category = models.CharField(max_length=32, choices=ExpenseCategory.choices)
    status = models.CharField(max_length=32, choices=ExpenseStatus.choices)
    progress = models.IntegerField(default=0)
    expense_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True, related_name="expenses")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    invoice_file_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "expenses"


class ExpenseApprovalAssignment(TimeStampedModel):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="approval_assignments")
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expense_approval_assignments")
    status = models.CharField(max_length=32, choices=ApprovalAssignmentStatus.choices, default=ApprovalAssignmentStatus.PENDING)
    decision_note = models.TextField(blank=True, null=True)
    acted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "expense_approval_assignments"
        constraints = [
            models.UniqueConstraint(fields=["expense", "approver"], name="uq_expense_approver"),
        ]


class Document(models.Model):
    code = models.CharField(max_length=40, unique=True, db_index=True)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=80)
    status = models.CharField(max_length=32, choices=DocumentStatus.choices)
    risk = models.CharField(max_length=16, choices=DocumentRisk.choices)
    confidentiality = models.CharField(max_length=16, choices=ConfidentialityLevel.choices)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True, related_name="documents")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    file_name = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    approved_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "documents"


class ApprovalAssignment(TimeStampedModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="approval_assignments")
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="approval_assignments")
    status = models.CharField(max_length=32, choices=ApprovalAssignmentStatus.choices, default=ApprovalAssignmentStatus.PENDING)
    decision_note = models.TextField(blank=True, null=True)
    signed_signature_data = models.TextField(blank=True, null=True)
    acted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "approval_assignments"
        constraints = [
            models.UniqueConstraint(fields=["document", "approver"], name="uq_document_approver"),
        ]


class AuditLog(TimeStampedModel):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="audit_logs")
    actor_name = models.CharField(max_length=120)
    action = models.CharField(max_length=120)
    entity_type = models.CharField(max_length=80)
    entity_code = models.CharField(max_length=80, blank=True, null=True)
    detail = models.TextField(blank=True)
    icon = models.CharField(max_length=80, default="history")

    class Meta:
        db_table = "audit_logs"


class DirectConversation(TimeStampedModel):
    class ConversationType(models.TextChoices):
        DIRECT = "direct", "خصوصی"
        GROUP = "group", "گروهی"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="direct_conversations")
    participants = models.ManyToManyField(User, through="DirectConversationMember", related_name="direct_conversations")
    conversation_type = models.CharField(
        max_length=16,
        choices=ConversationType.choices,
        default=ConversationType.DIRECT,
        db_index=True,
    )
    title = models.CharField(max_length=120, blank=True, default="")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_chat_conversations",
    )
    pair_key = models.CharField(max_length=64, db_index=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "direct_conversations"
        constraints = [
            models.UniqueConstraint(fields=["organization", "pair_key"], name="uq_direct_conversation_pair"),
        ]
        indexes = [
            models.Index(fields=["organization", "-updated_at"], name="idx_direct_conv_org_updated"),
            models.Index(fields=["organization", "conversation_type"], name="idx_direct_conv_org_type"),
        ]


class DirectConversationMember(models.Model):
    conversation = models.ForeignKey(DirectConversation, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="direct_conversation_memberships")
    last_read_at = models.DateTimeField(blank=True, null=True)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "direct_conversation_members"
        constraints = [
            models.UniqueConstraint(fields=["conversation", "user"], name="uq_direct_conversation_member"),
        ]


class DirectMessage(TimeStampedModel):
    conversation = models.ForeignKey(DirectConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="direct_messages")
    body = models.TextField(blank=True, default="")
    attachment_original_name = models.CharField(max_length=255, blank=True, default="")
    attachment_stored_name = models.CharField(max_length=255, blank=True, default="")
    attachment_mime_type = models.CharField(max_length=120, blank=True, default="")
    attachment_size_bytes = models.IntegerField(default=0)

    class Meta:
        db_table = "direct_messages"
        indexes = [
            models.Index(fields=["conversation", "created_at"], name="idx_direct_msg_conv_date"),
        ]

    @property
    def has_attachment(self) -> bool:
        return bool(self.attachment_stored_name)


class TaskPriority(models.TextChoices):
    CRITICAL = "critical", "بحرانی"
    HIGH = "high", "بالا"
    MEDIUM = "medium", "متوسط"
    NORMAL = "normal", "عادی"
    LOW = "low", "پایین"


class TaskStatus(models.TextChoices):
    DRAFT = "draft", "پیش‌نویس"
    PENDING_ACCEPTANCE = "pending_acceptance", "نیازمند پذیرش"
    SCHEDULED = "scheduled", "برنامه‌ریزی‌شده"
    UPCOMING = "upcoming", "پیش‌رو"
    IN_PROGRESS = "in_progress", "در حال انجام"
    PAUSED = "paused", "متوقف‌شده"
    BLOCKED = "blocked", "مسدود"
    PENDING_REVIEW = "pending_review", "در انتظار بررسی"
    CHANGES_REQUESTED = "changes_requested", "نیازمند اصلاح"
    COMPLETED = "completed", "تکمیل‌شده"
    CANCELLED = "cancelled", "لغوشده"


class TaskAssignmentStatus(models.TextChoices):
    PENDING = "pending", "در انتظار"
    ACCEPTED = "accepted", "پذیرفته‌شده"
    REJECTED = "rejected", "ردشده"
    CANCELLED = "cancelled", "لغوشده"


class TaskReviewStatus(models.TextChoices):
    PENDING = "pending", "در انتظار"
    APPROVED = "approved", "تأیید شده"
    CHANGES_REQUESTED = "changes_requested", "نیازمند اصلاح"
    REJECTED = "rejected", "رد شده"


class TaskingSettings(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="tasking_settings")
    enabled = models.BooleanField(default=True)
    timezone_name = models.CharField(max_length=64, default="Asia/Tehran")
    work_days = models.JSONField(default=list)  # 0=Mon .. 6=Sun; default Sat-Wed
    work_day_start = models.TimeField(default=dt_time(8, 0))
    work_day_end = models.TimeField(default=dt_time(16, 0))
    break_minutes = models.PositiveIntegerField(default=0)
    subtract_break = models.BooleanField(default=False)
    target_utilization_percent = models.PositiveIntegerField(default=80)
    max_utilization_percent = models.PositiveIntegerField(default=90)
    under_planned_threshold_percent = models.PositiveIntegerField(default=80)
    overload_threshold_percent = models.PositiveIntegerField(default=100)
    allow_overbooking = models.BooleanField(default=True)
    overbooking_requires_reason = models.BooleanField(default=True)
    scheduler_mode = models.CharField(max_length=24, default="automatic")
    allow_task_splitting = models.BooleanField(default=True)
    minimum_segment_minutes = models.PositiveIntegerField(default=15)
    round_estimate_to_minutes = models.PositiveIntegerField(default=5)
    auto_prioritize_overdue = models.BooleanField(default=True)
    auto_prioritize_critical = models.BooleanField(default=True)
    auto_move_high_priority = models.BooleanField(default=True)
    respect_pinned_tasks = models.BooleanField(default=True)
    schedule_only_working_days = models.BooleanField(default=True)
    assignment_requires_acceptance = models.BooleanField(default=True)
    assignee_can_reject = models.BooleanField(default=True)
    rejection_reason_required = models.BooleanField(default=True)
    completion_requires_review = models.BooleanField(default=True)
    default_reviewer_rule = models.CharField(max_length=32, default="direct_manager")
    allow_multiple_active_timers = models.BooleanField(default=False)
    allow_manual_time_entry = models.BooleanField(default=True)
    manual_time_requires_reason = models.BooleanField(default=True)
    show_own_utilization = models.BooleanField(default=True)
    show_peer_utilization = models.BooleanField(default=False)
    week_starts_on = models.PositiveSmallIntegerField(default=5)  # Saturday
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tasking_settings"


class Task(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="tasks")
    code = models.CharField(max_length=40, unique=True, db_index=True)
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=80, blank=True, default="")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True, related_name="tasks")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_tasks")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_tasks")
    direct_manager_snapshot = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="snapshot_managed_tasks",
    )
    priority = models.CharField(max_length=16, choices=TaskPriority.choices, default=TaskPriority.NORMAL, db_index=True)
    status = models.CharField(max_length=32, choices=TaskStatus.choices, default=TaskStatus.DRAFT, db_index=True)
    estimated_minutes = models.PositiveIntegerField(default=0)
    original_estimated_minutes = models.PositiveIntegerField(default=0)
    remaining_estimated_minutes = models.PositiveIntegerField(default=0)
    actual_minutes = models.PositiveIntegerField(default=0)
    due_at = models.DateTimeField(blank=True, null=True, db_index=True)
    start_not_before = models.DateTimeField(blank=True, null=True)
    scheduled_start_at = models.DateTimeField(blank=True, null=True)
    scheduled_end_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    review_required = models.BooleanField(default=True)
    review_status = models.CharField(max_length=32, choices=TaskReviewStatus.choices, blank=True, default="")
    reviewer_rule = models.CharField(max_length=32, default="direct_manager")
    is_pinned = models.BooleanField(default=False)
    source_type = models.CharField(max_length=24, default="self")
    source_reference_id = models.CharField(max_length=80, blank=True, default="")
    delivery_note = models.TextField(blank=True, default="")
    blocked_reason = models.TextField(blank=True, default="")
    review_iteration = models.PositiveIntegerField(default=0)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "tasks"
        indexes = [
            models.Index(fields=["organization", "status"], name="idx_task_org_status"),
            models.Index(fields=["organization", "owner", "status"], name="idx_task_org_owner_status"),
            models.Index(fields=["organization", "due_at"], name="idx_task_org_due"),
        ]


class TaskAssignment(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="assignments")
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_assignments")
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="created_task_assignments")
    status = models.CharField(max_length=24, choices=TaskAssignmentStatus.choices, default=TaskAssignmentStatus.PENDING, db_index=True)
    assigned_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(blank=True, null=True)
    response_reason = models.TextField(blank=True, default="")
    previous_assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="previous_task_assignments",
    )

    class Meta:
        db_table = "task_assignments"
        indexes = [
            models.Index(fields=["assignee", "status"], name="idx_task_assign_user_status"),
        ]


class TaskObserver(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="observers")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="observed_tasks")
    observer_type = models.CharField(max_length=32, default="explicit")
    can_review = models.BooleanField(default=False)
    can_comment = models.BooleanField(default=True)
    can_view_time = models.BooleanField(default=True)

    class Meta:
        db_table = "task_observers"
        constraints = [
            models.UniqueConstraint(fields=["task", "user"], name="uq_task_observer"),
        ]


class TaskAllocation(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="allocations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_allocations")
    work_date = models.DateField(db_index=True)
    planned_minutes = models.PositiveIntegerField(default=0)
    sequence = models.PositiveIntegerField(default=0)
    segment_status = models.CharField(max_length=24, default="planned")
    scheduled_start_time = models.TimeField(blank=True, null=True)
    scheduled_end_time = models.TimeField(blank=True, null=True)
    is_over_capacity = models.BooleanField(default=False)
    created_by_scheduler = models.BooleanField(default=True)
    locked_by_user = models.BooleanField(default=False)

    class Meta:
        db_table = "task_allocations"
        indexes = [
            models.Index(fields=["user", "work_date"], name="idx_task_alloc_user_date"),
            models.Index(fields=["task", "work_date"], name="idx_task_alloc_task_date"),
        ]


class TaskTimeEntry(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="time_entries")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_time_entries")
    allocation = models.ForeignKey(TaskAllocation, on_delete=models.SET_NULL, blank=True, null=True, related_name="time_entries")
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    entry_type = models.CharField(max_length=24, default="timer")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="created_time_entries")
    adjustment_reason = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "task_time_entries"
        indexes = [
            models.Index(fields=["task", "-started_at"], name="idx_task_time_task_start"),
            models.Index(fields=["user", "is_active"], name="idx_task_time_user_active"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_active=True),
                name="uq_task_active_timer_per_user",
            ),
        ]


class TaskReview(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_reviews")
    status = models.CharField(max_length=32, choices=TaskReviewStatus.choices, default=TaskReviewStatus.PENDING)
    comment = models.TextField(blank=True, default="")
    reviewed_at = models.DateTimeField(blank=True, null=True)
    iteration_no = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "task_reviews"
        indexes = [
            models.Index(fields=["task", "iteration_no"], name="idx_task_review_iteration"),
        ]


class TaskComment(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True, related_name="replies")
    body = models.TextField()
    message_type = models.CharField(max_length=24, default="comment")
    edited_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "task_comments"
        indexes = [
            models.Index(fields=["task", "created_at"], name="idx_task_comment_date"),
        ]


class TaskMention(TimeStampedModel):
    comment = models.ForeignKey(TaskComment, on_delete=models.CASCADE, related_name="mentions")
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_mentions")
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "task_mentions"
        constraints = [
            models.UniqueConstraint(fields=["comment", "mentioned_user"], name="uq_task_mention"),
        ]


class TaskAttachment(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="task_attachments")
    original_name = models.CharField(max_length=255)
    stored_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120, blank=True, default="")
    size_bytes = models.IntegerField(default=0)
    visibility = models.CharField(max_length=24, default="task")

    class Meta:
        db_table = "task_attachments"


class TaskDependency(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="dependencies")
    depends_on = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="dependents")
    relation = models.CharField(max_length=24, default="blocks")

    class Meta:
        db_table = "task_dependencies"
        constraints = [
            models.UniqueConstraint(fields=["task", "depends_on"], name="uq_task_dependency"),
        ]


class TaskActivity(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="task_activities")
    actor_name = models.CharField(max_length=120, blank=True, default="")
    action = models.CharField(max_length=80)
    detail = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "task_activities"
        indexes = [
            models.Index(fields=["task", "-created_at"], name="idx_task_activity_date"),
        ]

