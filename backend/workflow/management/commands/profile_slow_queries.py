from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection

from workflow.models import User


class Command(BaseCommand):
    help = "Run EXPLAIN on hot SQL paths to inspect index usage and scan patterns."

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int, help="User id used in query samples.")
        parser.add_argument("--output", default="", help="Optional JSON output path.")

    def handle(self, *args, **options):
        user = self._resolve_user(options)
        samples = self._explain_samples(user.id)
        report = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "userId": user.id,
            "database": connection.settings_dict.get("NAME"),
            "samples": samples,
            "notes": [
                "Review 'type=ALL' or 'Using filesort' as tuning candidates.",
                "On staging, compare with EXPLAIN ANALYZE and slow query log under Locust load.",
            ],
        }

        for sample in samples:
            self.stdout.write(self.style.HTTP_INFO(f"== {sample['name']} =="))
            if sample.get("columns"):
                self.stdout.write(" | ".join(sample["columns"]))
            for row in sample.get("rows", []):
                self.stdout.write(" | ".join(str(item) for item in row))

        if options["output"]:
            output_path = Path(options["output"]).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Profile saved to {output_path}"))

    def _resolve_user(self, options) -> User:
        if options.get("user_id"):
            return User.objects.get(pk=options["user_id"])
        user = User.objects.filter(is_active=True).order_by("id").first()
        if user is None:
            raise SystemExit("No active users found.")
        return user

    def _explain_samples(self, user_id: int) -> list[dict]:
        statements = [
            (
                "requests_by_requester",
                """
                EXPLAIN SELECT r.id
                FROM requests r
                WHERE r.requester_id = %s
                ORDER BY r.created_at DESC
                LIMIT 50
                """,
                [user_id],
            ),
            (
                "expenses_by_owner",
                """
                EXPLAIN SELECT e.id
                FROM expenses e
                WHERE e.owner_id = %s
                ORDER BY e.expense_date DESC, e.created_at DESC
                LIMIT 50
                """,
                [user_id],
            ),
            (
                "task_time_entries_active",
                """
                EXPLAIN SELECT id
                FROM task_time_entries
                WHERE user_id = %s AND is_active = 1
                ORDER BY started_at DESC
                LIMIT 5
                """,
                [user_id],
            ),
            (
                "attendance_events_org",
                """
                EXPLAIN SELECT id
                FROM attendance_events
                WHERE organization_id = (
                    SELECT organization_id FROM organization_memberships WHERE user_id = %s LIMIT 1
                )
                ORDER BY event_at DESC
                LIMIT 100
                """,
                [user_id],
            ),
            (
                "audit_logs_actor",
                """
                EXPLAIN SELECT id
                FROM audit_logs
                WHERE actor_id = %s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                [user_id],
            ),
        ]

        samples: list[dict] = []
        with connection.cursor() as cursor:
            for name, sql, params in statements:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description] if cursor.description else []
                samples.append({"name": name, "columns": columns, "rows": [list(row) for row in rows]})
        return samples
