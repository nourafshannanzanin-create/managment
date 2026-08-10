from django.core.management.base import BaseCommand, CommandError

from workflow.organization_purge import KEEP_ORG_CODES, purge_non_core_organizations


class Command(BaseCommand):
    help = "Delete every organization except HQ and the showcase sample (کارنومند نمونه)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only list organizations and users that would be deleted.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirm deletion. Required unless --dry-run is used.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        confirmed = options["yes"]

        if not dry_run and not confirmed:
            raise CommandError("Refusing to delete data without --yes. Use --dry-run to preview first.")

        summary = purge_non_core_organizations(dry_run=dry_run)

        self.stdout.write(f"Keeping organizations: {', '.join(summary['kept_org_codes'])}")
        if not summary["organizations"]:
            self.stdout.write(self.style.SUCCESS("Nothing to delete."))
            return

        for org in summary["organizations"]:
            self.stdout.write(f"- {org['name']} ({org['code']}) -> {org['user_count']} user(s)")
            for slug in org["user_slugs"]:
                self.stdout.write(f"    • {slug}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run only. {len(summary['organizations'])} organization(s) would be deleted."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                "Deleted "
                f"{summary['deleted_organizations']} organization(s) and "
                f"{summary['deleted_users']} related user record(s)."
            )
        )
