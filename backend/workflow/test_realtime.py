from __future__ import annotations

import queue
import os
from unittest.mock import patch

from django.http import JsonResponse
from django.test import RequestFactory, TestCase

from workflow.live import _LiveSubscriber, _replay_events, record_live_event
from workflow.models import IdempotencyRecord, LiveOutbox, Organization, OrganizationMembership, User, UserRole
from workflow.security import get_password_hash
from workflow.views import _run_idempotent_request


class LiveOutboxTests(TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {"WORKFLOW_LIVE_OUTBOX_ENABLED": "true", "WORKFLOW_IDEMPOTENCY_ENABLED": "true"},
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.organization = Organization.objects.create(code="live-test", name="Live Test")
        self.user = User.objects.create(
            slug="live-user",
            full_name="Live User",
            email="live@example.test",
            password_hash=get_password_hash("secret123"),
            role=UserRole.EMPLOYEE,
            job_title="Employee",
            avatar="LU",
        )
        OrganizationMembership.objects.create(organization=self.organization, user=self.user)

    def _subscriber(self, organization_id: int | None):
        return _LiveSubscriber(queue=queue.Queue(), user_id=self.user.id, organization_id=organization_id, is_hq=False)

    def test_publish_runs_only_after_commit(self):
        with patch("workflow.live._publish_outbox_row") as publish:
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                record_live_event(
                    "task.updated",
                    {"organization_id": self.organization.id},
                    tenant_id=self.organization.id,
                    entity_type="task",
                    entity_id="TASK-1",
                )
                self.assertEqual(publish.call_count, 0)
                self.assertEqual(LiveOutbox.objects.count(), 1)
            self.assertEqual(len(callbacks), 1)
            self.assertEqual(publish.call_count, 0)
            callbacks[0]()
            publish.assert_called_once()

    def test_replay_is_tenant_scoped_and_uses_monotonic_cursor(self):
        record_live_event(
            "task.updated",
            {"organization_id": self.organization.id},
            tenant_id=self.organization.id,
            entity_type="task",
            entity_id="TASK-1",
        )
        record_live_event(
            "task.updated",
            {"organization_id": self.organization.id + 1},
            tenant_id=self.organization.id + 1,
            entity_type="task",
            entity_id="TASK-2",
        )
        events = list(_replay_events(self._subscriber(self.organization.id), 0))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["tenant_id"], str(self.organization.id))
        self.assertTrue(events[0]["event_id"].isdigit())

    def test_idempotency_replays_the_original_unsafe_response(self):
        request_factory = RequestFactory()
        calls = []

        def view(request):
            calls.append(request.method)
            return JsonResponse({"created": len(calls)}, status=201)

        first = request_factory.post("/api/v1/requests", data="{}", content_type="application/json", HTTP_IDEMPOTENCY_KEY="same-key")
        first.current_user = self.user
        second = request_factory.post("/api/v1/requests", data="{}", content_type="application/json", HTTP_IDEMPOTENCY_KEY="same-key")
        second.current_user = self.user

        first_response = _run_idempotent_request(first, view)
        second_response = _run_idempotent_request(second, view)

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(second_response["Idempotency-Replayed"], "true")
        self.assertEqual(calls, ["POST"])
        self.assertEqual(IdempotencyRecord.objects.count(), 1)
