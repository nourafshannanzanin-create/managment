from __future__ import annotations

import os
import random

from locust import HttpUser, between, task


API_PREFIX = os.getenv("LOADTEST_API_PREFIX", "/api/v1")
HOST = os.getenv("LOADTEST_HOST", "http://127.0.0.1:8000")
USERNAME = os.getenv("LOADTEST_USERNAME", "milad_dhs")
PASSWORD = os.getenv("LOADTEST_PASSWORD", "")


class WorkflowUser(HttpUser):
    """Simulates a logged-in workflow user hitting hot read paths."""

    wait_time = between(0.5, 2.5)
    host = HOST

    def on_start(self) -> None:
        self.token = ""
        if not PASSWORD:
            return
        response = self.client.post(
            f"{API_PREFIX}/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            name="POST /auth/login",
        )
        if response.status_code == 200:
            payload = response.json()
            self.token = payload.get("access_token") or payload.get("accessToken") or ""

    @property
    def auth_headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def bootstrap_summary(self) -> None:
        self.client.get(
            f"{API_PREFIX}/bootstrap?mode=summary",
            headers=self.auth_headers,
            name="GET /bootstrap?mode=summary",
        )

    @task(4)
    def bootstrap_collection(self) -> None:
        section = random.choice(["requests", "expenses", "approvals", "users"])
        self.client.get(
            f"{API_PREFIX}/bootstrap/collections?section={section}&limit=250&offset=0",
            headers=self.auth_headers,
            name="GET /bootstrap/collections",
        )

    @task(2)
    def tasking_reports(self) -> None:
        self.client.get(
            f"{API_PREFIX}/tasking/reports",
            headers=self.auth_headers,
            name="GET /tasking/reports",
        )

    @task(2)
    def attendance_reports(self) -> None:
        self.client.get(
            f"{API_PREFIX}/attendance/reports",
            headers=self.auth_headers,
            name="GET /attendance/reports",
        )

    @task(1)
    def health(self) -> None:
        self.client.get(f"{API_PREFIX}/health", name="GET /health")
