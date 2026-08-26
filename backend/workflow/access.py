from __future__ import annotations

from functools import wraps
from typing import Callable

from django.http import HttpRequest

from workflow.models import Organization, OrganizationMembership, SectionAccessGrant, User, UserRole

MANAGER_ROLES = {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER}
DEFAULT_ORGANIZATION_CODE = "default-workflow"
DEFAULT_ORGANIZATION_NAME = "سازمان پیش فرض"
SECTION_USERS = "users"
SECTION_REPORTS = "reports"
SECTION_APPROVALS = "approvals"
SECTION_EXPENSES = "expenses"
SECTION_SETTINGS = "settings"
SECTION_ATTENDANCE = "attendance"
SECTION_ARCHIVE = "archive"


def is_manager(user: User) -> bool:
    return user.role in MANAGER_ROLES


def ensure_default_organization() -> Organization:
    organization, _ = Organization.objects.get_or_create(
        code=DEFAULT_ORGANIZATION_CODE,
        defaults={"name": DEFAULT_ORGANIZATION_NAME},
    )
    return organization


def ensure_user_memberships() -> None:
    """Create missing memberships in bulk — never re-scan every user on every request."""
    organization = ensure_default_organization()
    existing_ids = set(OrganizationMembership.objects.values_list("user_id", flat=True))
    missing = list(User.objects.exclude(id__in=existing_ids).only("id", "job_title"))
    if not missing:
        return
    OrganizationMembership.objects.bulk_create(
        [
            OrganizationMembership(
                user=user,
                organization=organization,
                display_title=user.job_title or "",
            )
            for user in missing
        ],
        ignore_conflicts=True,
    )


def get_user_organization(user: User) -> Organization:
    from workflow.cache_utils import get_cached_user_organization

    return get_cached_user_organization(user)


def organization_users(user: User):
    organization = get_user_organization(user)
    return User.objects.filter(organization_membership__organization=organization)


def visible_users(user: User):
    if is_manager(user):
        return organization_users(user)
    return User.objects.filter(pk=user.pk)


def has_section_access(user: User, section_key: str) -> bool:
    if user.role == UserRole.ADMIN:
        return True

    if section_key == SECTION_APPROVALS:
        return True

    organization = get_user_organization(user)
    grants = SectionAccessGrant.objects.filter(organization=organization, section_key=section_key)
    if grants.exists():
        return grants.filter(user=user).exists()

    if section_key == SECTION_USERS:
        return False
    if section_key == SECTION_REPORTS:
        return False
    if section_key == SECTION_EXPENSES:
        return False
    if section_key == SECTION_SETTINGS:
        return False
    # attendance / archive: by default open to all roles until grants are configured
    if section_key in {SECTION_ATTENDANCE, SECTION_ARCHIVE}:
        return True
    return True


def can_access_users(user: User) -> bool:
    return has_section_access(user, SECTION_USERS)


def can_manage_users(user: User) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.EXECUTIVE_MANAGER:
        return True
    if user.role == UserRole.MANAGER and has_section_access(user, SECTION_USERS):
        return True
    return False


def can_view_reports(user: User) -> bool:
    return has_section_access(user, SECTION_REPORTS)


def can_access_approvals(user: User) -> bool:
    return has_section_access(user, SECTION_APPROVALS)


def can_approve_documents(user: User) -> bool:
    return has_section_access(user, SECTION_APPROVALS)


def can_access_expenses(user: User) -> bool:
    return has_section_access(user, SECTION_EXPENSES)


def can_access_settings(user: User) -> bool:
    if is_manager(user):
        return True
    return has_section_access(user, SECTION_SETTINGS)


def can_access_attendance(user: User) -> bool:
    return has_section_access(user, SECTION_ATTENDANCE)


def can_access_archive(user: User) -> bool:
    return has_section_access(user, SECTION_ARCHIVE)


def can_edit_work_times(user: User) -> bool:
    return is_manager(user)


def attach_user(request: HttpRequest, user: User) -> None:
    request.current_user = user


def require_roles(*roles: str) -> Callable:
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapped(request: HttpRequest, *args, **kwargs):
            current_user = getattr(request, "current_user", None)
            if current_user is None or current_user.role not in roles:
                from workflow.views import json_error

                return json_error("دسترسی کافی ندارید.", status=403)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
