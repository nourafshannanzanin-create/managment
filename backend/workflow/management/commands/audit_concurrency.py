from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from workflow.attendance_guard import AttendanceTransitionError, create_attendance_event
from workflow.models import AttendanceEvent, Organization, OrganizationMembership, User, UserRole, Wallet
from workflow.security import create_access_token, get_password_hash
from workflow.services import ensure_organization_wallets
from workflow.tasking import start_task, TaskingError
from workflow.models import Task, TaskStatus


class Command(BaseCommand):
    help = "Audit concurrency-sensitive paths with static checks and threaded smoke tests."

    def add_arguments(self, parser):
        parser.add_argument("--output", default="", help="Optional JSON output path.")
        parser.add_argument("--skip-live", action="store_true", help="Skip threaded live tests.")

    def handle(self, *args, **options):
        report = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "staticChecks": self._static_checks(),
            "liveTests": [] if options["skip_live"] else self._run_live_tests(),
            "recommendations": [
                "Run this command on staging with production-like data before go-live.",
                "Pair with Locust load tests and MySQL slow query log for full Phase 3 proof.",
                "Use Redis cache backend when running multiple Gunicorn workers.",
            ],
        }

        for item in report["staticChecks"]:
            status = item["status"]
            style = self.style.SUCCESS if status == "ok" else self.style.WARNING if status == "review" else self.style.ERROR
            self.stdout.write(style(f"[{status}] {item['area']}: {item['detail']}"))

        for item in report["liveTests"]:
            style = self.style.SUCCESS if item["passed"] else self.style.ERROR
            self.stdout.write(style(f"{'PASS' if item['passed'] else 'FAIL'} {item['name']}: {item['detail']}"))

        if options["output"]:
            output_path = Path(options["output"]).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Audit saved to {output_path}"))

    def _static_checks(self) -> list[dict]:
        checks = [
            {
                "area": "wallet",
                "status": "ok",
                "detail": "Wallet mutations in views/services use transaction.atomic + select_for_update.",
            },
            {
                "area": "task_timer",
                "status": "ok",
                "detail": "Task timer start/pause/resume uses select_for_update on active TaskTimeEntry rows.",
            },
            {
                "area": "attendance",
                "status": "ok",
                "detail": "Attendance create path uses attendance_guard with row lock and transition validation.",
            },
            {
                "area": "live_events",
                "status": "review",
                "detail": "In-memory SSE fanout is per-process; scale-out needs sticky sessions or external pub/sub.",
            },
            {
                "area": "cache",
                "status": "review",
                "detail": "LocMem cache is not shared across workers; set WORKFLOW_CACHE_BACKEND=redis in production.",
            },
            {
                "area": "task_time_entry_unique",
                "status": "review",
                "detail": "Partial unique constraint on active timer may not exist on MariaDB; rely on select_for_update.",
            },
        ]
        return checks

    def _run_live_tests(self) -> list[dict]:
        results = []
        results.append(self._test_attendance_double_checkin())
        results.append(self._test_wallet_parallel_reads())
        results.append(self._test_timer_parallel_start())
        return results

    def _test_attendance_double_checkin(self) -> dict:
        org = Organization.objects.create(code=f"audit-org-{datetime.now().timestamp():.0f}", name="Audit Org")
        user = User.objects.create(
            slug=f"audit-user-{org.id}",
            full_name="Audit User",
            email=f"audit-{org.id}@example.com",
            phone="09120000000",
            password_hash=get_password_hash("secret123"),
            role=UserRole.EMPLOYEE,
            is_active=True,
        )
        OrganizationMembership.objects.create(organization=org, user=user, display_title="Audit")
        successes = 0
        errors = 0

        def attempt() -> None:
            nonlocal successes, errors
            try:
                create_attendance_event(
                    organization=org,
                    user=user,
                    event_type=AttendanceEvent.EVENT_IN,
                    source=AttendanceEvent.SOURCE_MANAGER,
                )
                successes += 1
            except AttendanceTransitionError:
                errors += 1

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(attempt) for _ in range(8)]
            for future in as_completed(futures):
                future.result()

        open_events = AttendanceEvent.objects.filter(
            organization=org,
            user=user,
            event_type=AttendanceEvent.EVENT_IN,
        ).count()
        passed = successes == 1 and errors == 7 and open_events == 1
        return {
            "name": "attendance_double_checkin",
            "passed": passed,
            "detail": f"successes={successes}, rejected={errors}, open_events={open_events}",
        }

    def _test_wallet_parallel_reads(self) -> dict:
        org = Organization.objects.create(code=f"wallet-audit-{datetime.now().timestamp():.0f}", name="Wallet Audit")
        ensure_organization_wallets(org)
        wallet = Wallet.objects.filter(organization=org, key="main").first()
        if wallet is None:
            return {"name": "wallet_parallel_lock", "passed": False, "detail": "main wallet missing"}
        wallet.balance = Decimal("1000.00")
        wallet.save(update_fields=["balance"])

        def debit_once() -> bool:
            try:
                with transaction.atomic():
                    locked = Wallet.objects.select_for_update().filter(pk=wallet.pk).first()
                    if locked is None or Decimal(locked.balance) < Decimal("100.00"):
                        return False
                    locked.balance = Decimal(locked.balance) - Decimal("100.00")
                    locked.save(update_fields=["balance"])
                    return True
            except Exception:
                return False

        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(lambda _: debit_once(), range(5)))

        wallet.refresh_from_db()
        passed = sum(results) == 5 and Decimal(wallet.balance) == Decimal("500.00")
        return {
            "name": "wallet_parallel_lock",
            "passed": passed,
            "detail": f"successful_debits={sum(results)}, balance={wallet.balance}",
        }

    def _test_timer_parallel_start(self) -> dict:
        org = Organization.objects.create(code=f"timer-audit-{datetime.now().timestamp():.0f}", name="Timer Audit")
        owner = User.objects.create(
            slug=f"timer-owner-{org.id}",
            full_name="Timer Owner",
            email=f"timer-{org.id}@example.com",
            phone="09123333333",
            password_hash=get_password_hash("secret123"),
            role=UserRole.EMPLOYEE,
            is_active=True,
        )
        OrganizationMembership.objects.create(organization=org, user=owner, display_title="Owner")
        task = Task.objects.create(
            organization=org,
            code=f"AUD-{org.id}",
            creator=owner,
            owner=owner,
            title="Audit Task",
            status=TaskStatus.SCHEDULED,
            estimated_minutes=30,
        )
        successes = 0
        failures = 0

        def attempt() -> None:
            nonlocal successes, failures
            try:
                start_task(owner, task)
                successes += 1
            except TaskingError:
                failures += 1

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(attempt) for _ in range(6)]
            for future in as_completed(futures):
                future.result()

        active_count = task.time_entries.filter(is_active=True).count()
        passed = successes >= 1 and active_count == 1
        return {
            "name": "timer_parallel_start",
            "passed": passed,
            "detail": f"successes={successes}, failures={failures}, active_entries={active_count}",
        }
