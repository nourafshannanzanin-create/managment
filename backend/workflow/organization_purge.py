from __future__ import annotations

from django.db import transaction
from django.db.models import Q

from workflow.models import (
    ApprovalAssignment,
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
    User,
    UserSignature,
)
from workflow.services import HQ_ORG_CODE, HQ_USERNAME, SHOWCASE_ORG_CODE

KEEP_ORG_CODES = {HQ_ORG_CODE, SHOWCASE_ORG_CODE}
PROTECTED_USER_SLUGS = {HQ_USERNAME}


def organizations_to_purge():
    return Organization.objects.exclude(code__in=KEEP_ORG_CODES).order_by("code")


def member_user_ids(organization: Organization) -> list[int]:
    return list(
        OrganizationMembership.objects.filter(organization=organization)
        .exclude(user__slug__in=PROTECTED_USER_SLUGS)
        .values_list("user_id", flat=True)
    )


def purge_user_workflow_data(user_ids: list[int]) -> dict[str, int]:
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

    counts["user_signatures"] = UserSignature.objects.filter(user_id__in=user_ids).delete()[0]
    counts["section_access_grants"] = SectionAccessGrant.objects.filter(user_id__in=user_ids).delete()[0]

    User.objects.filter(manager_id__in=user_ids).update(manager_id=None)
    User.objects.filter(deleted_by_id__in=user_ids).update(deleted_by_id=None)

    return counts


@transaction.atomic
def purge_non_core_organizations(*, dry_run: bool = False) -> dict:
    targets = list(organizations_to_purge())
    summary = {
        "dry_run": dry_run,
        "kept_org_codes": sorted(KEEP_ORG_CODES),
        "organizations": [],
        "deleted_organizations": 0,
        "deleted_users": 0,
    }

    for organization in targets:
        user_ids = member_user_ids(organization)
        org_summary = {
            "code": organization.code,
            "name": organization.name,
            "user_count": len(user_ids),
            "user_slugs": list(
                User.objects.filter(pk__in=user_ids).order_by("slug").values_list("slug", flat=True)
            ),
        }
        summary["organizations"].append(org_summary)

        if dry_run:
            continue

        purge_user_workflow_data(user_ids)
        deleted_users, _ = User.objects.filter(pk__in=user_ids).delete()
        organization.delete()
        summary["deleted_users"] += deleted_users
        summary["deleted_organizations"] += 1

    return summary
