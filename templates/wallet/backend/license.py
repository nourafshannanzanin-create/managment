from dataclasses import dataclass


@dataclass(frozen=True)
class LicenseStatus:
    is_locked: bool
    reason: str
    notice: str
    grace_days: int
    amount_due: str = '0'


def build_license_status(*, has_required_purchase, overdue_days=0, grace_days=7, amount_due='0'):
    if not has_required_purchase:
        return LicenseStatus(
            is_locked=True,
            reason='core_purchase_required',
            notice='برای استفاده از نرم‌افزار باید خرید اصلی ثبت شود.',
            grace_days=grace_days,
            amount_due=amount_due,
        )
    if overdue_days > grace_days:
        return LicenseStatus(
            is_locked=True,
            reason='installment_overdue',
            notice='سررسید پرداخت گذشته و دسترسی قفل شده است.',
            grace_days=grace_days,
            amount_due=amount_due,
        )
    if overdue_days > 0:
        return LicenseStatus(
            is_locked=False,
            reason='installment_overdue_warning',
            notice='سررسید پرداخت گذشته اما هنوز داخل بازه مهلت هستید.',
            grace_days=grace_days,
            amount_due=amount_due,
        )
    return LicenseStatus(
        is_locked=False,
        reason='',
        notice='',
        grace_days=grace_days,
        amount_due=amount_due,
    )
