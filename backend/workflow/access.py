from __future__ import annotations

from functools import wraps
from typing import Callable

from django.http import HttpRequest

from workflow.models import Organization, OrganizationMembership, User, UserRole

MANAGER_ROLES = {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER}
DEFAULT_ORGANIZATION_CODE = "default-workflow"
DEFAULT_ORGANIZATION_NAME = "سازمان پیش فرض"


def is_manager(user: User) -> bool:
    return user.role in MANAGER_ROLES


def ensure_default_organization() -> Organization:
    organization, _ = Organization.objects.get_or_create(
        code=DEFAULT_ORGANIZATION_CODE,
        defaults={"name": DEFAULT_ORGANIZATION_NAME},
    )
    return organization


def ensure_user_memberships() -> None:
    organization = ensure_default_organization()
    for user in User.objects.all():
        OrganizationMembership.objects.get_or_create(
            user=user,
            defaults={"organization": organization, "display_title": user.job_title},
        )


def get_user_organization(user: User) -> Organization:
    if hasattr(user, "organization_membership"):
        return user.organization_membership.organization
    ensure_user_memberships()
    return OrganizationMembership.objects.select_related("organization").get(user=user).organization


def organization_users(user: User):
    organization = get_user_organization(user)
    return User.objects.filter(organization_membership__organization=organization)


def visible_users(user: User):
    if is_manager(user):
        return organization_users(user)
    return User.objects.filter(pk=user.pk)


def can_manage_users(user: User) -> bool:
    return user.role == UserRole.ADMIN


def can_view_reports(user: User) -> bool:
    return user.role == UserRole.ADMIN


def can_approve_documents(user: User) -> bool:
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
