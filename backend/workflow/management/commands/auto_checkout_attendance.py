from django.core.management.base import BaseCommand

from workflow.attendance_auto_checkout import auto_checkout_open_shifts


class Command(BaseCommand):
    help = "Auto-register checkout for open attendance shifts (run daily around 03:05)."

    def handle(self, *args, **options):
        created = auto_checkout_open_shifts()
        self.stdout.write(self.style.SUCCESS(f"Auto checkout created {created} event(s)."))
