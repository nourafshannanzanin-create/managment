from django.core.management.base import BaseCommand

from workflow.showcase_seed import ensure_showcase_organization


class Command(BaseCommand):
    help = "Seed the hidden showcase organization (کارنومند نمونه) with rich fake data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete and recreate the showcase organization from scratch",
        )

    def handle(self, *args, **options):
        result = ensure_showcase_organization(reset=options["reset"])
        self.stdout.write(self.style.SUCCESS("Showcase organization is ready."))
        lines = [
            f"  name: {result['organization_name']}",
            f"  code: {result['organization_code']}",
            f"  manager: {result['manager_username']} / {result['manager_password']}",
            f"  phone: {result['manager_phone']}",
            f"  users: {result['users']}",
            f"  wallet main: {result['main_balance']} (schematic)",
            f"  wallet sms: {result['sms_balance']} (schematic)",
            f"  sms limits: daily={result['sms_daily_limit']} monthly={result['sms_monthly_limit']}",
            f"  bought: {', '.join(result['active_features'])}",
            f"  not bought: {', '.join(result['inactive_features'])}",
            "  HQ visibility: org hidden; support tickets visible",
        ]
        for line in lines:
            try:
                self.stdout.write(line)
            except UnicodeEncodeError:
                self.stdout.write(line.encode("ascii", "backslashreplace").decode("ascii"))
