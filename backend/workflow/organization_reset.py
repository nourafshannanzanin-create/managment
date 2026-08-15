from __future__ import annotations

from django.db import transaction
from django.db.models import Q

from workflow.models import (
    ApprovalAssignment,
    AttendanceEvent,
    AuditLog,
    DirectConversation,
    Document,
    Expense,
    ExpenseApprovalAssignment,
    Organization,
    OrganizationMembership,
    Request,
    RequestApprovalAssignment,
    RequestAttachment,
    RequestTimeline,
    SectionAccessGrant,
    SupportTicket,
    Task,
    User,
    UserRole,
    Wallet,
    WalletTransaction,
)


def resolve_organization(*, name: str = "", code: str = "") -> Organization:
    name = str(name or "").strip()
    code = str(code or "").strip()
    qs = Organization.objects.all()
    if code:
        qs = qs.filter(code__iexact=code)
    elif name:
        # Exact name first so «کارنو» never matches «کارنومند نمونه».
        exact = qs.filter(name=name)
        if exact.exists():
            qs = exact
        else:
            qs = qs.filter(name__iexact=name)
    else:
        raise ValueError("نام یا کد سازمان الزامی است.")

    matches = list(qs.order_by("id")[:5])
    if not matches:
        raise Organization.DoesNotExist(f"سازمانی با این مشخصات پیدا نشد (name={name!r}, code={code!r}).")
    if len(matches) > 1:
        labels = ", ".join(f"{item.name} ({item.code})" for item in matches)
        raise ValueError(f"چند سازمان هم‌نام پیدا شد؛ با --code مشخص کنید: {labels}")
    return matches[0]


def organization_member_ids(organization: Organization) -> list[int]:
    return list(
        OrganizationMembership.objects.filter(organization=organization).values_list("user_id", flat=True)
    )


def keep_admin_user_ids(organization: Organization, member_ids: list[int]) -> list[int]:
    admins = list(
        User.objects.filter(pk__in=member_ids, role=UserRole.ADMIN, is_deleted=False)
        .order_by("id")
        .values_list("pk", flat=True)
    )
    if not admins:
        raise ValueError(
            f"برای مجموعه «{organization.name}» هیچ کاربر مدیرعامل (admin) فعالی پیدا نشد؛ "
            "پاکسازی بدون نگه‌داشتن مدیرعامل انجام نمی‌شود."
        )
    return admins


def _delete_workflow_for_users(user_ids: list[int]) -> dict[str, int]:
    if not user_ids:
        return {}
    counts: dict[str, int] = {}

    request_ids = list(
        Request.objects.filter(
            Q(requester_id__in=user_ids)
            | Q(manager_id__in=user_ids)
            | Q(assigned_managers__in=user_ids)
            | Q(assigned_employees__in=user_ids)
        )
        .distinct()
        .values_list("pk", flat=True)
    )
    counts["request_approval_assignments"] = RequestApprovalAssignment.objects.filter(
        Q(request_id__in=request_ids) | Q(approver_id__in=user_ids)
    ).delete()[0]
    counts["request_attachments"] = RequestAttachment.objects.filter(request_id__in=request_ids).delete()[0]
    counts["request_timeline"] = RequestTimeline.objects.filter(request_id__in=request_ids).delete()[0]
    counts["requests"] = Request.objects.filter(pk__in=request_ids).delete()[0]

    document_ids = list(Document.objects.filter(owner_id__in=user_ids).values_list("pk", flat=True))
    counts["document_approval_assignments"] = ApprovalAssignment.objects.filter(
        Q(document_id__in=document_ids) | Q(approver_id__in=user_ids)
    ).delete()[0]
    counts["documents"] = Document.objects.filter(pk__in=document_ids).delete()[0]

    expense_ids = list(Expense.objects.filter(owner_id__in=user_ids).values_list("pk", flat=True))
    counts["expense_approval_assignments"] = ExpenseApprovalAssignment.objects.filter(
        Q(expense_id__in=expense_ids) | Q(approver_id__in=user_ids)
    ).delete()[0]
    counts["expenses"] = Expense.objects.filter(pk__in=expense_ids).delete()[0]

    counts["audit_logs"] = AuditLog.objects.filter(actor_id__in=user_ids).delete()[0]
    return counts


@transaction.atomic
def reset_organization_keep_admin_wallet_settings(
    organization: Organization,
    *,
    dry_run: bool = False,
) -> dict:
    """
    Wipe operational data for one organization.

    Keep:
      - Organization row
      - OrganizationPreference / TaskingSettings
      - Wallet (+ transactions / feature purchases)
      - مدیرعامل (role=admin) user account(s) + membership + signature + section grants

    Delete:
      - All other members
      - Attendance, chat, tasks, requests, expenses, documents, support tickets, audit trail, etc.
    """
    member_ids = organization_member_ids(organization)
    keep_ids = keep_admin_user_ids(organization, member_ids)
    remove_ids = [uid for uid in member_ids if uid not in set(keep_ids)]

    keep_users = list(
        User.objects.filter(pk__in=keep_ids).order_by("id").values_list("slug", "full_name", "role")
    )
    remove_users = list(
        User.objects.filter(pk__in=remove_ids).order_by("slug").values_list("slug", "full_name", "role")
    )

    preview = {
        "organization": {"id": organization.id, "code": organization.code, "name": organization.name},
        "keep_users": [{"slug": s, "name": n, "role": r} for s, n, r in keep_users],
        "remove_users": [{"slug": s, "name": n, "role": r} for s, n, r in remove_users],
        "counts": {
            "members_total": len(member_ids),
            "members_keep": len(keep_ids),
            "members_remove": len(remove_ids),
            "attendance": AttendanceEvent.objects.filter(organization=organization).count(),
            "tasks": Task.objects.filter(organization=organization).count(),
            "conversations": DirectConversation.objects.filter(organization=organization).count(),
            "support_tickets": SupportTicket.objects.filter(organization=organization).count(),
            "wallets": Wallet.objects.filter(organization=organization).count(),
            "wallet_transactions": WalletTransaction.objects.filter(organization=organization).count(),
        },
        "dry_run": dry_run,
        "deleted": {},
    }

    if dry_run:
        return preview

    deleted: dict[str, int] = {}

    # Org-scoped operational data (including admin's attendance / tasks / chat).
    deleted["tasks"] = Task.objects.filter(organization=organization).delete()[0]
    deleted["attendance"] = AttendanceEvent.objects.filter(organization=organization).delete()[0]
    deleted["direct_conversations"] = DirectConversation.objects.filter(organization=organization).delete()[0]
    deleted["support_tickets"] = SupportTicket.objects.filter(organization=organization).delete()[0]

    # Workflow rows owned/assigned across all current members (admin included).
    deleted.update(_delete_workflow_for_users(member_ids))

    # Drop grants for users that will be removed; keep admin grants.
    deleted["section_access_grants_removed"] = SectionAccessGrant.objects.filter(
        organization=organization, user_id__in=remove_ids
    ).delete()[0]

    # Detach manager/deleted_by pointers before user delete.
    User.objects.filter(manager_id__in=remove_ids).update(manager_id=None)
    User.objects.filter(deleted_by_id__in=remove_ids).update(deleted_by_id=None)
    WalletTransaction.objects.filter(organization=organization, actor_id__in=remove_ids).update(actor_id=None)

    # Remove non-admin users (membership / signature cascade with user).
    deleted["users"] = User.objects.filter(pk__in=remove_ids).delete()[0] if remove_ids else 0

    preview["deleted"] = deleted
    preview["kept_wallet_balance"] = list(
        Wallet.objects.filter(organization=organization).values("key", "name", "balance")
    )
    preview["kept_preferences"] = True
    return preview
