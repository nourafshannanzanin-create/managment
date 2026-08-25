from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from workflow.models import LiveOutbox


class Command(BaseCommand):
    help = "Prune expired live outbox invalidations; never use this as an audit-log cleanup."

    def add_arguments(self, parser):
        parser.add_argument("--retention-hours", type=int, default=72)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        retention_hours = options["retention_hours"]
        if retention_hours < 24:
            raise CommandError("Retention must be at least 24 hours so reconnect replay remains useful.")
        cutoff = timezone.now() - timedelta(hours=retention_hours)
        queryset = LiveOutbox.objects.filter(created_at__lt=cutoff)
        count = queryset.count()
        if options["dry_run"]:
            self.stdout.write(f"Would delete {count} LiveOutbox rows older than {cutoff.isoformat()}.")
            return
        deleted, _ = queryset.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired LiveOutbox rows."))
