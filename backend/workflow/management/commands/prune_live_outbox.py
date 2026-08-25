from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from workflow.models import IdempotencyRecord, LiveOutbox


class Command(BaseCommand):
    help = "Prune expired live outbox invalidations; never use this as an audit-log cleanup."

    def add_arguments(self, parser):
        parser.add_argument("--retention-hours", type=int, default=72)
        parser.add_argument("--idempotency-retention-hours", type=int, default=168)
        parser.add_argument("--batch-size", type=int, default=500)
        parser.add_argument("--max-batches", type=int, default=20)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        retention_hours = options["retention_hours"]
        if retention_hours < 24:
            raise CommandError("Retention must be at least 24 hours so reconnect replay remains useful.")
        cutoff = timezone.now() - timedelta(hours=retention_hours)
        batch_size = max(1, options["batch_size"])
        max_batches = max(1, options["max_batches"])
        queryset = LiveOutbox.objects.filter(created_at__lt=cutoff)
        count = queryset.count()
        if options["dry_run"]:
            self.stdout.write(f"Would delete {count} LiveOutbox rows older than {cutoff.isoformat()}.")
            return
        deleted = self._delete_bounded(queryset, batch_size=batch_size, max_batches=max_batches)
        idem_cutoff = timezone.now() - timedelta(hours=max(24, options["idempotency_retention_hours"]))
        idem_deleted = self._delete_bounded(
            IdempotencyRecord.objects.filter(created_at__lt=idem_cutoff),
            batch_size=batch_size,
            max_batches=max_batches,
        )
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} LiveOutbox and {idem_deleted} IdempotencyRecord rows."))

    @staticmethod
    def _delete_bounded(queryset, *, batch_size: int, max_batches: int) -> int:
        deleted = 0
        for _ in range(max_batches):
            with transaction.atomic():
                ids = list(queryset.select_for_update().order_by("id").values_list("id", flat=True)[:batch_size])
                if not ids:
                    break
                removed, _ = queryset.model.objects.filter(pk__in=ids).delete()
                deleted += removed
        return deleted
