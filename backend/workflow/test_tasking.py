from datetime import date, datetime, time as dt_time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from workflow.models import (
    Organization,
    OrganizationMembership,
    OrganizationPreference,
    TaskPriority,
    TaskStatus,
    TaskTimeEntry,
    User,
    UserRole,
)
from workflow.security import get_password_hash
from workflow.tasking import (
    accept_task,
    capacity_for_day,
    create_task,
    effective_work_minutes,
    get_or_create_tasking_settings,
    pause_task,
    priority_score,
    request_changes,
    schedule_task,
    start_task,
    submit_review,
)


class TaskingCoreTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(code="task-org", name="Task Org")
        self.pref = OrganizationPreference.objects.create(
            organization=self.org,
            work_day_start_time=dt_time(8, 0),
            work_day_end_time=dt_time(16, 0),
        )
        self.manager = User.objects.create(
            slug="manager1",
            full_name="مدیر تست",
            email="manager1@test.local",
            password_hash=get_password_hash("secret12"),
            role=UserRole.MANAGER,
            job_title="مدیر",
            avatar="مد",
        )
        self.employee = User.objects.create(
            slug="employee1",
            full_name="کارمند تست",
            email="employee1@test.local",
            password_hash=get_password_hash("secret12"),
            role=UserRole.EMPLOYEE,
            job_title="کارشناس",
            avatar="کا",
            manager=self.manager,
        )
        OrganizationMembership.objects.create(organization=self.org, user=self.manager)
        OrganizationMembership.objects.create(organization=self.org, user=self.employee)
        self.settings = get_or_create_tasking_settings(self.org)
        self.settings.work_days = [0, 1, 2, 3, 4, 5, 6]
        self.settings.work_day_start = dt_time(8, 0)
        self.settings.work_day_end = dt_time(16, 0)
        self.settings.target_utilization_percent = 80
        self.settings.max_utilization_percent = 90
        self.settings.assignment_requires_acceptance = True
        self.settings.allow_task_splitting = True
        self.settings.save()

    def test_ac01_capacity_base(self):
        today = date.today()
        minutes = effective_work_minutes(self.employee, self.settings, today)
        self.assertEqual(minutes, 480)
        capacity = capacity_for_day(self.employee, self.settings, today)
        self.assertEqual(capacity["targetMinutes"], 384)

    def test_ac02_split_allocation(self):
        # Fill most of today's target capacity, then ensure a new task spills over.
        filler = create_task(
            self.manager,
            {
                "title": "پر کردن ظرفیت",
                "assigneeId": self.employee.id,
                "priority": TaskPriority.NORMAL,
                "estimatedMinutes": 360,
                "reviewRequired": False,
            },
        )
        accept_task(self.employee, filler)
        task = create_task(
            self.manager,
            {
                "title": "تسک تقسیم‌شونده",
                "assigneeId": self.employee.id,
                "priority": TaskPriority.NORMAL,
                "estimatedMinutes": 120,
                "reviewRequired": False,
            },
        )
        accept_task(self.employee, task)
        allocations = list(task.allocations.order_by("work_date", "sequence"))
        self.assertGreaterEqual(len(allocations), 2)
        self.assertEqual(sum(item.planned_minutes for item in allocations), task.estimated_minutes)

    def test_ac04_active_task_not_interrupted(self):
        task_a = create_task(
            self.employee,
            {
                "title": "تسک فعال",
                "assigneeId": self.employee.id,
                "priority": TaskPriority.NORMAL,
                "estimatedMinutes": 60,
                "reviewRequired": False,
            },
        )
        start_task(self.employee, task_a)
        task_b = create_task(
            self.manager,
            {
                "title": "تسک بحرانی",
                "assigneeId": self.employee.id,
                "priority": TaskPriority.CRITICAL,
                "estimatedMinutes": 30,
                "reviewRequired": False,
            },
        )
        accept_task(self.employee, task_b)
        task_a.refresh_from_db()
        self.assertEqual(task_a.status, TaskStatus.IN_PROGRESS)
        self.assertTrue(TaskTimeEntry.objects.filter(task=task_a, user=self.employee, is_active=True).exists())

    def test_ac05_assignment_pending(self):
        task = create_task(
            self.manager,
            {
                "title": "ارجاع جدید",
                "assigneeId": self.employee.id,
                "priority": TaskPriority.HIGH,
                "estimatedMinutes": 45,
            },
        )
        self.assertEqual(task.status, TaskStatus.PENDING_ACCEPTANCE)
        self.assertEqual(task.allocations.count(), 0)

    def test_ac06_timer_uniqueness(self):
        task_a = create_task(
            self.employee,
            {"title": "A", "assigneeId": self.employee.id, "priority": TaskPriority.NORMAL, "estimatedMinutes": 30, "reviewRequired": False},
        )
        task_b = create_task(
            self.employee,
            {"title": "B", "assigneeId": self.employee.id, "priority": TaskPriority.NORMAL, "estimatedMinutes": 30, "reviewRequired": False},
        )
        start_task(self.employee, task_a)
        with self.assertRaises(Exception):
            start_task(self.employee, task_b, stop_other=False)
        start_task(self.employee, task_b, stop_other=True)
        self.assertEqual(TaskTimeEntry.objects.filter(user=self.employee, is_active=True).count(), 1)
        self.assertTrue(TaskTimeEntry.objects.filter(task=task_b, user=self.employee, is_active=True).exists())

    def test_ac07_review_rejection_keeps_history(self):
        task = create_task(
            self.manager,
            {
                "title": "نیازمند بررسی",
                "assigneeId": self.employee.id,
                "priority": TaskPriority.NORMAL,
                "estimatedMinutes": 40,
                "reviewRequired": True,
            },
        )
        accept_task(self.employee, task)
        start_task(self.employee, task)
        pause_task(self.employee, task)
        submit_review(self.employee, task, delivery_note="انجام شد")
        request_changes(self.manager, task, comment="لطفا اصلاح شود")
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.CHANGES_REQUESTED)
        self.assertGreaterEqual(task.review_iteration, 2)
        self.assertTrue(task.activities.filter(action="review_changes_requested").exists())

    def test_priority_score_critical_above_normal(self):
        normal = create_task(
            self.employee,
            {"title": "عادی", "assigneeId": self.employee.id, "priority": TaskPriority.NORMAL, "estimatedMinutes": 20, "reviewRequired": False},
        )
        critical = create_task(
            self.employee,
            {"title": "بحرانی", "assigneeId": self.employee.id, "priority": TaskPriority.CRITICAL, "estimatedMinutes": 20, "reviewRequired": False},
        )
        today = date.today()
        self.assertGreater(priority_score(critical, self.settings, today), priority_score(normal, self.settings, today))
