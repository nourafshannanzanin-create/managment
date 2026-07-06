from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db.models import Prefetch, Q

from workflow.access import can_access_approvals, can_access_expenses, can_access_settings, can_access_users, can_approve_documents, can_manage_users, can_view_reports, get_user_organization, is_manager, visible_users
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

PERSIAN_WEEK_DAYS = ["Ø´Ù†Ø¨Ù‡", "ÛŒÚ©Ø´Ù†Ø¨Ù‡", "Ø¯ÙˆØ´Ù†Ø¨Ù‡", "Ø³Ù‡ Ø´Ù†Ø¨Ù‡", "Ú†Ù‡Ø§Ø±Ø´Ù†Ø¨Ù‡", "Ù¾Ù†Ø¬ Ø´Ù†Ø¨Ù‡", "Ø¬Ù…Ø¹Ù‡"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
PDF_EXTENSIONS = {".pdf"}
HQ_USERNAME = "milad_dhs"


def now():
    return datetime.now(timezone.utc)


def format_money(value: Decimal | int | float | str) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:,.2f}"


def format_date(value):
    if not value:
        return ""
    return value.isoformat()


def relative_time(value: datetime) -> str:
    delta = now() - value.astimezone(timezone.utc)
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return "Ø§Ø®ÛŒØ±Ø§"
    hours = minutes // 60
    if hours < 24:
        return "Ø§Ù…Ø±ÙˆØ²"
    days = hours // 24
    if days < 7:
        return f"{days} Ø±ÙˆØ² Ù‚Ø¨Ù„"
    return value.date().isoformat()


def access_role_label(role: str) -> str:
    return {
        UserRole.ADMIN: "Ù…Ø¯ÛŒØ±Ø¹Ø§Ù…Ù„",
        UserRole.EXECUTIVE_MANAGER: "Ù…Ø¯ÛŒØ± Ø§Ø±Ø´Ø¯",
        UserRole.MANAGER: "Ù…Ø¯ÛŒØ±",
        UserRole.EMPLOYEE: "Ú©Ø§Ø±Ù…Ù†Ø¯",
    }[role]


def normalize_person_name(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("Ø¢Ø±Ù…Ø§Ù† Ú©Ø±ÛŒÙ…ÛŒ", "Ø§Ù…ÛŒØ¯ Ú©Ø±ÛŒÙ…ÛŒ")


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
    is_hq = user.slug == HQ_USERNAME
    return {
        "id": user.id,
        "slug": user.slug,
        "name": normalize_person_name(user.full_name),
        "role": user.job_title,
        "accessRole": user.role,
        "department": user.department.name if user.department else "",
        "avatar": user.avatar,
        "email": user.email,
        "phone": user.phone or "",
        "organization": membership.organization.name if membership else "",
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
    }


def serialize_user(user: User) -> dict:
    membership = getattr(user, "organization_membership", None)
    return {
        "id": user.id,
        "name": normalize_person_name(user.full_name),
        "email": user.email,
        "phone": user.phone or "",
        "role": access_role_label(user.role),
        "accessRole": user.role,
        "departmentCode": user.department.code if user.department else "",
        "department": user.department.name if user.department else "Ø¨Ø¯ÙˆÙ† ÙˆØ§Ø­Ø¯",
        "manager": normalize_person_name(user.manager.full_name) if user.manager else "ØªØ¹ÛŒÛŒÙ† Ù†Ø´Ø¯Ù‡",
        "kpi": user.job_title,
        "managerId": user.manager_id,
        "avatar": user.avatar,
        "organization": membership.organization.name if membership else "",
        "organizationId": membership.organization_id if membership else None,
        "joinedAt": format_date(user.created_at.date()),
        "joinedAtIso": format_date(user.created_at.date()),
        "isActive": user.is_active,
        "status": "ÙØ¹Ø§Ù„" if user.is_active else "ØºÛŒØ±ÙØ¹Ø§Ù„",
    }


def settings_cards() -> list[dict]:
    return [
        {"title": "Ø­Ø³Ø§Ø¨ Ú©Ø§Ø±Ø¨Ø±ÛŒ", "description": "Ù…Ø¯ÛŒØ±ÛŒØª Ù†Ù‚Ø´ Ù‡Ø§ Ùˆ Ø¯Ø³ØªØ±Ø³ÛŒ"},
        {"title": "Ø§Ø³Ù†Ø§Ø¯", "description": "Ú¯Ø±Ø¯Ø´ Ú©Ø§Ø± Ø§Ù…Ø¶Ø§ÛŒ Ø¯ÛŒØ¬ÛŒØªØ§Ù„"},
        {"title": "Ù‡Ø²ÛŒÙ†Ù‡ Ù‡Ø§", "description": "Ø«Ø¨ØªØŒ Ù¾ÛŒÚ¯ÛŒØ±ÛŒ Ùˆ Ú©Ù†ØªØ±Ù„ Ù‡Ø²ÛŒÙ†Ù‡"},
        {"title": "Ú¯Ø²Ø§Ø±Ø´Ø§Øª", "description": "Ù†Ù…Ø§ÛŒ Ù…Ø¯ÛŒØ±ÛŒØªÛŒ Ùˆ ØªØ­Ù„ÛŒÙ„ Ø¹Ù…Ù„Ú©Ø±Ø¯"},
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
    recent_session_label = "Ø¨Ø¯ÙˆÙ† Ù†Ø´Ø³Øª Ø§Ø®ÛŒØ±"
    if recent_logins:
        recent_session_label = f"{len(recent_logins)} Ø¯Ø³ØªÚ¯Ø§Ù‡ ÙØ¹Ø§Ù„ Ø´Ù†Ø§Ø³Ø§ÛŒÛŒ Ø´Ø¯"

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
        "owner": normalize_person_name(request_obj.requester.full_name) if request_obj.requester else "Ù†Ø§Ù…Ø´Ø®Øµ",
        "manager": normalize_person_name(request_obj.manager.full_name) if request_obj.manager else "ØªØ¹ÛŒÛŒÙ† Ù†Ø´Ø¯Ù‡",
        "managerAssignees": [normalize_person_name(item.full_name) for item in request_obj.assigned_managers.all()],
        "managerAssigneeIds": [item.id for item in request_obj.assigned_managers.all()],
        "employeeAssignees": [normalize_person_name(item.full_name) for item in request_obj.assigned_employees.all()],
        "employeeAssigneeIds": [item.id for item in request_obj.assigned_employees.all()],
        "priority": priority_label(request_obj.priority),
        "priorityValue": request_obj.priority,
        "status": request_status_label(request_obj.status),
        "statusValue": request_obj.status,
        "department": request_obj.department.name if request_obj.department else "Ø¨Ø¯ÙˆÙ† ÙˆØ§Ø­Ø¯",
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
        "owner": normalize_person_name(expense.owner.full_name) if expense.owner else "Ù†Ø§Ù…Ø´Ø®Øµ",
        "status": expense_status_label(expense.status),
        "statusValue": expense.status,
        "progress": expense.progress,
        "department": expense.department.name if expense.department else "Ø¨Ø¯ÙˆÙ† ÙˆØ§Ø­Ø¯",
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
    }


def ensure_organization_wallets(organization: Organization) -> list[Wallet]:
    defaults = [
        ("main", "Ú©ÛŒÙ Ù¾ÙˆÙ„ Ø§ØµÙ„ÛŒ", Decimal("1000000")),
        ("sms", "Ú©ÛŒÙ Ù¾ÙˆÙ„ Ù¾ÛŒØ§Ù…Ú©", Decimal("250000")),
    ]
    wallets = []
    for key, name, threshold in defaults:
        wallet, _ = Wallet.objects.get_or_create(
            organization=organization,
            key=key,
            defaults={"name": name, "low_balance_threshold": threshold},
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

    return {
        "organization": {"id": organization.id, "name": organization.name, "code": organization.code},
        "summary": {
            "totalBalance": format_money(total_balance),
            "totalBalanceRaw": float(total_balance),
            "mainBalance": format_money(main_balance),
            "mainBalanceRaw": float(main_balance),
            "smsBalance": format_money(sms_balance),
            "smsBalanceRaw": float(sms_balance),
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
        "open": "Ø¨Ø§Ø²",
        "pending": "Ø¯Ø± Ø­Ø§Ù„ Ø¨Ø±Ø±Ø³ÛŒ",
        "answered": "Ù¾Ø§Ø³Ø® Ø¯Ø§Ø¯Ù‡ Ø´Ø¯Ù‡",
        "closed": "Ø¨Ø³ØªÙ‡ Ø´Ø¯Ù‡",
    }.get(value, value)


def support_category_label(value: str) -> str:
    return {
        "technical": "ÙÙ†ÛŒ",
        "financial": "Ù…Ø§Ù„ÛŒ",
        "operations": "Ø¹Ù…Ù„ÛŒØ§Øª",
        "account": "Ø­Ø³Ø§Ø¨ Ú©Ø§Ø±Ø¨Ø±ÛŒ",
        "other": "Ø³Ø§ÛŒØ±",
    }.get(value, value)


def support_priority_label(value: str) -> str:
    return {
        "low": "Ú©Ù…",
        "medium": "Ù…ØªÙˆØ³Ø·",
        "high": "Ø²ÛŒØ§Ø¯",
        "urgent": "ÙÙˆØ±ÛŒ",
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
        "owner": normalize_person_name(document.owner.full_name) if document.owner else "Ù†Ø§Ù…Ø´Ø®Øµ",
        "type": document.document_type,
        "status": document_status_label(document.status),
        "statusValue": document.status,
        "department": document.department.name if document.department else "Ø¨Ø¯ÙˆÙ† ÙˆØ§Ø­Ø¯",
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
    owner = normalize_person_name(user.full_name) or "Ù…Ø¯ÛŒØ±Ø¹Ø§Ù…Ù„"
    today = date.today().isoformat()
    return [
        {
            "id": "requests",
            "title": "Ú¯Ø²Ø§Ø±Ø´ Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ù‡Ø§",
            "description": "Ù†Ù…Ø§ÛŒ Ú©Ù„ÛŒ Ø¬Ø±ÛŒØ§Ù† Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ù‡Ø§ Ùˆ ÙˆØ¶Ø¹ÛŒØª Ù¾ÛŒÚ¯ÛŒØ±ÛŒ Ø¢Ù† Ù‡Ø§",
            "export": "CSV / Excel",
            "owner": owner,
            "generatedAt": today,
            "generatedAtIso": today,
            "downloadUrl": "/api/v1/reports/requests/export?format=csv",
        },
        {
            "id": "expenses",
            "title": "Ú¯Ø²Ø§Ø±Ø´ Ù‡Ø²ÛŒÙ†Ù‡ Ù‡Ø§",
            "description": "ØªØ­Ù„ÛŒÙ„ Ù‡Ø²ÛŒÙ†Ù‡ Ù‡Ø§ÛŒ Ø³Ø§Ø²Ù…Ø§Ù† Ø¨Ø± Ø§Ø³Ø§Ø³ Ø«Ø¨Øª Ú©Ù†Ù†Ø¯Ù‡ Ùˆ Ù…Ø¨Ù„Øº",
            "export": "CSV / Excel",
            "owner": owner,
            "generatedAt": today,
            "generatedAtIso": today,
            "downloadUrl": "/api/v1/reports/expenses/export?format=csv",
        },
        {
            "id": "approvals",
            "title": "Ú¯Ø²Ø§Ø±Ø´ ØªØ§ÛŒÛŒØ¯Ù‡Ø§",
            "description": "Ø¹Ù…Ù„Ú©Ø±Ø¯ Ù…Ø¯ÛŒØ±Ø§Ù† Ø¯Ø± ØªØ§ÛŒÛŒØ¯ØŒ Ø±Ø¯ Ùˆ Ú¯Ø±Ø¯Ø´ Ø§Ø³Ù†Ø§Ø¯",
            "export": "CSV / Excel",
            "owner": owner,
            "generatedAt": today,
            "generatedAtIso": today,
            "downloadUrl": "/api/v1/reports/approvals/export?format=csv",
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

    departments = list(Department.objects.exclude(code__in=["hq-control", "hq"]).exclude(name__iexact="HQ").order_by("name"))
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
            {"title": "Ú¯Ø²Ø§Ø±Ø´ Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ù‡Ø§", "description": "Ù†Ù…Ø§ÛŒ Ú©Ù„ÛŒ Ø¬Ø±ÛŒØ§Ù† Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ù‡Ø§", "export": "CSV / Excel", "owner": "Ù…Ø¯ÛŒØ±Ø¹Ø§Ù…Ù„", "generatedAt": date.today().isoformat(), "generatedAtIso": date.today().isoformat()},
            {"title": "Ú¯Ø²Ø§Ø±Ø´ Ù‡Ø²ÛŒÙ†Ù‡ Ù‡Ø§", "description": "ØªØ­Ù„ÛŒÙ„ Ù‡Ø²ÛŒÙ†Ù‡ Ù‡Ø§ÛŒ Ø³Ø§Ø²Ù…Ø§Ù†", "export": "CSV / Excel", "owner": "Ù…Ø¯ÛŒØ±Ø¹Ø§Ù…Ù„", "generatedAt": date.today().isoformat(), "generatedAtIso": date.today().isoformat()},
            {"title": "Ú¯Ø²Ø§Ø±Ø´ ØªØ§ÛŒÛŒØ¯Ù‡Ø§", "description": "Ø¹Ù…Ù„Ú©Ø±Ø¯ Ù…Ø¯ÛŒØ±Ø§Ù† Ø¯Ø± ØªØ§ÛŒÛŒØ¯ Ø§Ø³Ù†Ø§Ø¯", "export": "CSV / Excel", "owner": "Ù…Ø¯ÛŒØ±Ø¹Ø§Ù…Ù„", "generatedAt": date.today().isoformat(), "generatedAtIso": date.today().isoformat()},
        ]

    reports = report_catalog(user) if can_view_reports(user) else []

    today_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date == date.today())
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_total = sum(Decimal(item.amount) for item in expenses_qs if item.expense_date >= week_start)

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
            {"id": "active", "label": "Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ù‡Ø§", "value": str(active_requests), "detail": "", "tone": "primary", "icon": "assignment"},
            {"id": "pending", "label": "ØªØ§ÛŒÛŒØ¯Ù‡Ø§", "value": str(metrics["pending"]), "detail": "", "tone": "warning", "icon": "pending_actions"},
            {"id": "monthly", "label": "Ù‡Ø²ÛŒÙ†Ù‡ Ù…Ø§Ù‡", "value": format_money(month_total), "detail": "", "tone": "secondary", "icon": "payments"},
            {"id": "approved", "label": "Ø§Ø³Ù†Ø§Ø¯ ØªØ§ÛŒÛŒØ¯", "value": str(metrics["approved"]), "detail": "", "tone": "success", "icon": "fact_check"},
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
            {"label": "Ø§Ù…Ø±ÙˆØ²", "value": format_money(today_total)},
            {"label": "Ø§ÛŒÙ† Ù‡ÙØªÙ‡", "value": format_money(week_total)},
            {"label": "Ø§ÛŒÙ† Ù…Ø§Ù‡", "value": format_money(month_total)},
            {"label": "Ø§Ù…Ø³Ø§Ù„", "value": format_money(year_total)},
        ],
        "approvalMetrics": metrics,
        "settingsCards": [
            {"title": "Ø­Ø³Ø§Ø¨ Ú©Ø§Ø±Ø¨Ø±ÛŒ", "description": "Ù…Ø¯ÛŒØ±ÛŒØª Ù†Ù‚Ø´ Ù‡Ø§ Ùˆ Ø¯Ø³ØªØ±Ø³ÛŒ"},
            {"title": "Ø§Ø³Ù†Ø§Ø¯", "description": "Ú¯Ø±Ø¯Ø´ Ú©Ø§Ø± Ø§Ù…Ø¶Ø§ÛŒ Ø¯ÛŒØ¬ÛŒØªØ§Ù„"},
            {"title": "Ù‡Ø²ÛŒÙ†Ù‡ Ù‡Ø§", "description": "Ø«Ø¨ØªØŒ Ù¾ÛŒÚ¯ÛŒØ±ÛŒ Ùˆ Ú©Ù†ØªØ±Ù„ Ù‡Ø²ÛŒÙ†Ù‡"},
            {"title": "Ú¯Ø²Ø§Ø±Ø´Ø§Øª", "description": "Ù†Ù…Ø§ÛŒ Ù…Ø¯ÛŒØ±ÛŒØªÛŒ Ùˆ ØªØ­Ù„ÛŒÙ„ Ø¹Ù…Ù„Ú©Ø±Ø¯"},
        ],
        "directories": {
            "departments": [{"code": item.code, "name": item.name} for item in departments],
            "managers": [
                {"id": item.id, "slug": item.slug, "name": normalize_person_name(item.full_name), "role": access_role_label(item.role)}
                for item in users_qs
                if item.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER}
            ],
            "users": [{"id": item.id, "name": normalize_person_name(item.full_name)} for item in users_qs],
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
    else:
        raise ValueError("Invalid report key.")

    return f"{report_key}-report-{today}.csv", buffer.getvalue()

def serialize_user(user: User) -> dict:
    organization = get_user_organization(user)
    section_access = set(
        user.section_access_grants.filter(organization=organization).values_list("section_key", flat=True)
    )
    return {
        "id": user.id,
        "name": normalize_person_name(user.full_name),
        "email": user.email,
        "role": access_role_label(user.role),
        "accessRole": user.role,
        "department": user.department.name if user.department else "Ø¨Ø¯ÙˆÙ† ÙˆØ§Ø­Ø¯",
        "manager": normalize_person_name(user.manager.full_name) if user.manager else "ØªØ¹ÛŒÛŒÙ† Ù†Ø´Ø¯Ù‡",
        "jobTitle": user.job_title,
        "kpi": user.job_title,
        "joinedAt": format_date(user.created_at.date()),
        "joinedAtIso": format_date(user.created_at.date()),
        "status": "ÙØ¹Ø§Ù„" if user.is_active else "ØºÛŒØ±ÙØ¹Ø§Ù„",
        "isActive": user.is_active,
        "managerId": user.manager_id,
        "departmentCode": user.department.code if user.department else "",
        "sectionAccess": {
            "reports": "reports" in section_access,
            "users": "users" in section_access,
            "settings": "settings" in section_access,
        },
    }

