from django.core.management.base import BaseCommand, CommandError

from workflow.models import Organization
from workflow.organization_reset import (
    reset_organization_keep_admin_wallet_settings,
    resolve_organization,
)


class Command(BaseCommand):
    help = (
        "پاکسازی عملیاتی یک مجموعه: کاربران غیرمدیرعامل، ورود/خروج، تسک، چت، "
        "درخواست، هزینه، سند و ... حذف می‌شوند. "
        "تنظیمات، کیف پول و مدیرعامل نگه داشته می‌شوند."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default="کارنو",
            help="نام دقیق مجموعه (پیش‌فرض: کارنو)",
        )
        parser.add_argument(
            "--code",
            default="",
            help="کد سازمان (اگر چند هم‌نام دارید، با این مشخص کنید)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="فقط پیش‌نمایش؛ چیزی حذف نمی‌شود",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="تأیید حذف واقعی (بدون این فلگ فقط dry-run مجاز است)",
        )

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        if not dry_run and not options["yes"]:
            raise CommandError("برای حذف واقعی --yes لازم است. اول با --dry-run ببینید.")

        try:
            organization = resolve_organization(name=options["name"], code=options["code"])
        except Organization.DoesNotExist as exc:
            raise CommandError(str(exc)) from exc
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        try:
            summary = reset_organization_keep_admin_wallet_settings(organization, dry_run=dry_run)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        org = summary["organization"]
        self.stdout.write(f"مجموعه: {org['name']} ({org['code']})")
        self.stdout.write("نگه داشته می‌شود:")
        for user in summary["keep_users"]:
            self.stdout.write(f"  • مدیرعامل: {user['name']} (@{user['slug']})")
        self.stdout.write(
            "  • تنظیمات سازمان / تسکینگ، کیف پول و تراکنش‌های کیف پول، اشتراک‌ها"
        )

        self.stdout.write(f"کاربران حذف‌شونده: {summary['counts']['members_remove']}")
        for user in summary["remove_users"]:
            self.stdout.write(f"  - {user['name']} (@{user['slug']}) [{user['role']}]")

        counts = summary["counts"]
        self.stdout.write(
            "داده عملیاتی: "
            f"ورود/خروج={counts['attendance']}، "
            f"تسک={counts['tasks']}، "
            f"چت={counts['conversations']}، "
            f"تیکت={counts['support_tickets']}، "
            f"کیف‌پول={counts['wallets']} (نگه داشته می‌شود)"
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: هیچ چیزی حذف نشد."))
            return

        deleted = summary.get("deleted") or {}
        self.stdout.write(self.style.SUCCESS("پاکسازی انجام شد."))
        for key, value in sorted(deleted.items()):
            self.stdout.write(f"  {key}: {value}")
        for wallet in summary.get("kept_wallet_balance") or []:
            self.stdout.write(
                self.style.SUCCESS(
                    f"کیف پول باقی‌مانده: {wallet['name']} ({wallet['key']}) = {wallet['balance']}"
                )
            )
