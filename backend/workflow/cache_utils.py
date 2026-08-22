from __future__ import annotations

from typing import Callable, TypeVar

from django.conf import settings
from django.core.cache import cache

from workflow.models import Organization, OrganizationMembership, OrganizationPreference, TaskingSettings, User

T = TypeVar("T")

DEFAULT_CACHE_TTL = getattr(settings, "WORKFLOW_CACHE_TTL", 300)


def _cache_get(key: str, loader: Callable[[], T], ttl: int | None = None) -> T:
    cached = cache.get(key)
    if cached is not None:
        return cached
    value = loader()
    cache.set(key, value, ttl if ttl is not None else DEFAULT_CACHE_TTL)
    return value


def invalidate_user_organization_cache(user_id: int | None = None) -> None:
    if user_id is not None:
        cache.delete(f"wf:org:user:{user_id}")


def invalidate_organization_cache(organization_id: int) -> None:
    cache.delete(f"wf:org:obj:{organization_id}")
    cache.delete(f"wf:tasking:settings:{organization_id}")
    cache.delete(f"wf:org:preference:{organization_id}")


def get_organization_by_id(organization_id: int) -> Organization:
    return _cache_get(
        f"wf:org:obj:{organization_id}",
        lambda: Organization.objects.get(pk=organization_id),
    )


def cached_user_organization_id(user_id: int) -> int | None:
    key = f"wf:org:user:{user_id}"
    cached = cache.get(key)
    if cached is not None:
        return int(cached) if cached else None

    membership = (
        OrganizationMembership.objects.filter(user_id=user_id)
        .values_list("organization_id", flat=True)
        .first()
    )
    cache.set(key, membership or 0, DEFAULT_CACHE_TTL)
    return membership


def get_cached_user_organization(user: User) -> Organization:
    membership = getattr(user, "organization_membership", None)
    if membership is not None:
        return membership.organization

    organization_id = cached_user_organization_id(user.id)
    if organization_id:
        return get_organization_by_id(organization_id)

    from workflow.access import ensure_user_memberships

    ensure_user_memberships()
    invalidate_user_organization_cache(user.id)
    return OrganizationMembership.objects.select_related("organization").get(user=user).organization


def get_cached_tasking_settings(organization: Organization) -> TaskingSettings:
    key = f"wf:tasking:settings:{organization.id}"

    def loader() -> TaskingSettings:
        from workflow.tasking import get_or_create_tasking_settings

        return get_or_create_tasking_settings(organization, use_cache=False)

    settings_id = _cache_get(key, lambda: loader().pk)
    return TaskingSettings.objects.get(pk=settings_id)


def invalidate_tasking_settings_cache(organization_id: int) -> None:
    cache.delete(f"wf:tasking:settings:{organization_id}")


def get_cached_organization_preference(organization: Organization) -> OrganizationPreference:
    key = f"wf:org:preference:{organization.id}"

    def loader() -> OrganizationPreference:
        preference, _ = OrganizationPreference.objects.get_or_create(organization=organization)
        return preference

    preference_id = _cache_get(key, lambda: loader().pk)
    return OrganizationPreference.objects.get(pk=preference_id)


def cache_throttled(key: str, ttl: int) -> bool:
    """Return True when the action should run (first call within ttl)."""
    if cache.get(key):
        return False
    cache.set(key, 1, ttl)
    return True
