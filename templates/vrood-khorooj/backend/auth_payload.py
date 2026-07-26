def build_auth_payload(
    user,
    *,
    feature_keys=None,
    menu_access=None,
    license_status=None,
    attendance_free_workers_limit=5,
    attendance_worker_count=0,
    is_hq=False,
    is_hq_admin=False,
):
    tenant = getattr(user, 'tenant', None)
    normalized_feature_keys = set(feature_keys or [])
    attendance_feature_purchased = 'attendance' in normalized_feature_keys
    return {
        'id': user.id,
        'username': user.username,
        'full_name': getattr(user, 'full_name', ''),
        'first_name': getattr(user, 'first_name', ''),
        'last_name': getattr(user, 'last_name', ''),
        'role': getattr(user, 'role', ''),
        'platform_role': getattr(user, 'platform_role', ''),
        'phone': getattr(user, 'phone', ''),
        'tenant_id': getattr(user, 'tenant_id', None),
        'tenant_name': getattr(tenant, 'name', '') if tenant else '',
        'purchased_menu_access': sorted(normalized_feature_keys),
        'menu_access': dict(menu_access or {}),
        'attendance_free_workers_limit': attendance_free_workers_limit,
        'attendance_worker_count': attendance_worker_count,
        'attendance_feature_purchased': attendance_feature_purchased,
        'attendance_upgrade_required': bool(
            getattr(user, 'tenant_id', None)
            and not attendance_feature_purchased
            and attendance_worker_count > attendance_free_workers_limit
        ),
        'license_status': dict(license_status or {}),
        'is_hq': bool(is_hq),
        'is_hq_admin': bool(is_hq_admin),
    }
