from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.test import Client
from django.test.utils import CaptureQueriesContext

from workflow.models import User
from workflow.security import create_access_token


class Command(BaseCommand):
    help = "Benchmark workflow endpoints: response time, query count, optional EXPLAIN hints."

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int, help="User id to authenticate benchmark requests.")
        parser.add_argument("--username", default="", help="User slug/username fallback when --user-id is omitted.")
        parser.add_argument("--label", default="run", help="Label stored in benchmark output.")
        parser.add_argument(
            "--output",
            default="",
            help="JSON output path. Defaults to backend/benchmarks/workflow-<label>-<timestamp>.json",
        )
        parser.add_argument(
            "--explain",
            action="store_true",
            help="Include EXPLAIN for a small set of hot queryset SQL statements.",
        )

    def handle(self, *args, **options):
        user = self._resolve_user(options)
        token = create_access_token(str(user.id), {"role": user.role})
        client = Client(HTTP_HOST="127.0.0.1")
        auth_header = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        endpoints = [
            ("bootstrap_full", "/api/v1/bootstrap?mode=full"),
            ("bootstrap_summary", "/api/v1/bootstrap?mode=summary"),
            ("bootstrap_requests", "/api/v1/bootstrap/collections?section=requests&limit=200&offset=0"),
            ("bootstrap_expenses", "/api/v1/bootstrap/collections?section=expenses&limit=200&offset=0"),
            ("bootstrap_approvals", "/api/v1/bootstrap/collections?section=approvals&limit=200&offset=0"),
            ("attendance_reports", "/api/v1/attendance/reports"),
            ("tasking_reports", "/api/v1/tasking/reports"),
        ]

        results = {
            "label": options["label"],
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "userId": user.id,
            "userSlug": user.slug,
            "database": connection.settings_dict.get("NAME"),
            "connMaxAge": connection.settings_dict.get("CONN_MAX_AGE"),
            "endpoints": [],
            "notes": [
                "Compare the same label across deployments only after identical data volume.",
                "Use responseBytes/responseKB to prove summary vs full payload shrink on large datasets.",
                "Pair with Locust (backend/loadtests/locustfile.py) for P95/P99 under concurrent users.",
                "Restart Django applies code changes; benchmark before/after to prove performance gains.",
            ],
        }

        for name, path in endpoints:
            reset_queries()
            with CaptureQueriesContext(connection) as ctx:
                started = time.perf_counter()
                response = client.get(path, **auth_header)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

            entry = {
                "name": name,
                "path": path,
                "status": response.status_code,
                "queries": len(ctx.captured_queries),
                "ms": elapsed_ms,
                "responseBytes": len(response.content),
                "responseKB": round(len(response.content) / 1024, 2),
            }
            if response.status_code >= 400:
                try:
                    entry["error"] = response.json()
                except Exception:
                    entry["error"] = response.content[:300].decode("utf-8", errors="replace")
            results["endpoints"].append(entry)
            self.stdout.write(f"{name}: {entry['status']} | {entry['queries']} queries | {entry['ms']} ms")

        if options["explain"]:
            results["explain"] = self._collect_explain_samples(user.id)

        output_path = self._resolve_output_path(options)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Benchmark saved to {output_path}"))

    def _resolve_user(self, options) -> User:
        if options.get("user_id"):
            return User.objects.get(pk=options["user_id"])
        username = (options.get("username") or "").strip()
        if username:
            user = User.objects.filter(slug=username).first()
            if user is not None:
                return user
        user = User.objects.filter(is_active=True).order_by("id").first()
        if user is None:
            raise SystemExit("No active users found. Seed the database or pass --user-id.")
        return user

    def _resolve_output_path(self, options) -> Path:
        if options.get("output"):
            return Path(options["output"]).resolve()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base_dir = Path(__file__).resolve().parents[3]
        return base_dir / "benchmarks" / f"workflow-{options['label']}-{timestamp}.json"

    def _collect_explain_samples(self, user_id: int) -> list[dict]:
        samples: list[dict] = []
        statements = [
            (
                "requests_visible",
                """
                SELECT COUNT(*) FROM requests r
                LEFT JOIN request_approval_assignments ra ON ra.request_id = r.id
                WHERE r.requester_id = %s OR ra.approver_id = %s
                """,
                [user_id, user_id],
            ),
            (
                "task_time_entries",
                """
                EXPLAIN SELECT id FROM task_time_entries
                WHERE user_id = %s
                ORDER BY started_at DESC
                LIMIT 20
                """,
                [user_id],
            ),
        ]
        with connection.cursor() as cursor:
            for name, sql, params in statements:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description] if cursor.description else []
                samples.append({"name": name, "columns": columns, "rows": [list(row) for row in rows]})
        return samples
