from django.core.management.base import BaseCommand

from workflow.support_tickets import close_stale_support_tickets


class Command(BaseCommand):
    help = "Close support tickets that have been idle for 3 days."

    def handle(self, *args, **options):
        closed = close_stale_support_tickets()
        self.stdout.write(self.style.SUCCESS(f"Closed {closed} stale support ticket(s)."))
