from django.db import models
from django.utils import timezone
from uuid import uuid4


class UserRole(models.TextChoices):
    ADMIN = "admin", "مدیرعامل"
    EXECUTIVE_MANAGER = "executive_manager", "مدیر ارشد"
    MANAGER = "manager", "مدیر"
    EMPLOYEE = "employee", "کارمند"


class RequestPriority(models.TextChoices):
    LOW = "low", "پایین"
    MEDIUM = "medium", "متوسط"
    HIGH = "high", "بالا"
    CRITICAL = "critical", "بحرانی"


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
    role = models.CharField(max_length=32, choices=UserRole.choices)
    job_title = models.CharField(max_length=120)
    avatar = models.CharField(max_length=8)
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

    class Meta:
        db_table = "users"


class OrganizationMembership(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="organization_membership")
    display_title = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        db_table = "organization_memberships"


class OrganizationPreference(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="preferences")
    two_factor_required = models.BooleanField(default=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "organization_preferences"


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
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="answered_support_tickets")
    responded_at = models.DateTimeField(blank=True, null=True)
    first_response_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    customer_satisfaction = models.IntegerField(blank=True, null=True)
    customer_feedback = models.TextField(blank=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "support_tickets"
        indexes = [
            models.Index(fields=["organization", "-updated_at"], name="idx_support_ticket_org_date"),
            models.Index(fields=["status", "-updated_at"], name="idx_support_ticket_status"),
        ]


class SupportMessage(TimeStampedModel):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="support_messages")
    sender_name = models.CharField(max_length=120)
    sender_platform_role = models.CharField(max_length=32, blank=True)
    body = models.TextField()

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



