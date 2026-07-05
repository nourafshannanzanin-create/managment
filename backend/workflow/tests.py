from __future__ import annotations

import base64
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.test import Client, TestCase, override_settings

from workflow.access import ensure_default_organization
from workflow.models import (
    ApprovalAssignment,
    ApprovalAssignmentStatus,
    Department,
    Document,
    DocumentRisk,
    DocumentStatus,
    OrganizationMembership,
    User,
    UserRole,
    UserSignature,
)
from workflow.security import create_access_token, get_password_hash
from workflow.views import DEFAULT_SIGNATURE_DATA

SOURCE_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="
SIGNATURE_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAQAAAACCAYAAAB/qH1jAAAAE0lEQVR4nGMUERH5z4AEmBjQAAAlyAE/YHhewAAAAABJRU5ErkJggg=="
SIGNATURE_DATA_URL = f"data:image/png;base64,{SIGNATURE_PNG_BASE64}"


class ApprovalFlowTests(TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.temp_dir.name, MEDIA_URL="/media/")
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.organization = ensure_default_organization()
        self.department = Department.objects.create(code="finance", name="امور مالی")
        self.owner = self._create_user("owner", "owner@example.com", UserRole.EMPLOYEE, "کارشناس")
        self.approver = self._create_user("approver", "approver@example.com", UserRole.MANAGER, "مدیر")
        self.client = Client()
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {create_access_token(str(self.approver.id), {'role': self.approver.role})}"

    def _create_user(self, slug: str, email: str, role: str, job_title: str) -> User:
        user = User.objects.create(
            slug=slug,
            full_name=slug,
            email=email,
            password_hash=get_password_hash("secret123"),
            role=role,
            job_title=job_title,
            avatar=slug[:2].upper(),
            department=self.department,
        )
        OrganizationMembership.objects.create(organization=self.organization, user=user, display_title=job_title)
        return user

    def _create_document(self, file_name: str = "source.png") -> Document:
        file_path = Path(settings.MEDIA_ROOT) / file_name
        file_path.write_bytes(base64.b64decode(SOURCE_PNG_BASE64))
        document = Document.objects.create(
            code="DOC-TEST",
            title="سند تست",
            description="برای تست فلو",
            document_type="قرارداد",
            status=DocumentStatus.PENDING,
            risk=DocumentRisk.MEDIUM,
            confidentiality="internal",
            department=self.department,
            owner=self.owner,
            file_name=file_name,
        )
        ApprovalAssignment.objects.create(document=document, approver=self.approver, status=ApprovalAssignmentStatus.PENDING)
        return document

    def test_signature_endpoint_hides_placeholder_signature(self):
        UserSignature.objects.create(user=self.approver, signature_data=DEFAULT_SIGNATURE_DATA)

        response = self.client.get("/api/v1/approvals/signature")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"hasSignature": False, "signatureData": ""})

    def test_approve_document_requires_real_signature(self):
        document = self._create_document()
        UserSignature.objects.create(user=self.approver, signature_data=DEFAULT_SIGNATURE_DATA)

        response = self.client.post(f"/api/v1/approvals/{document.code}/approve")

        self.assertEqual(response.status_code, 422)
        self.assertIn("امضای دیجیتال معتبر", response.json()["detail"])
        assignment = ApprovalAssignment.objects.get(document=document, approver=self.approver)
        self.assertEqual(assignment.status, ApprovalAssignmentStatus.PENDING)

    def test_approve_document_signs_file_when_real_signature_exists(self):
        document = self._create_document()
        UserSignature.objects.create(user=self.approver, signature_data=SIGNATURE_DATA_URL)

        response = self.client.post(f"/api/v1/approvals/{document.code}/approve")

        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        assignment = ApprovalAssignment.objects.get(document=document, approver=self.approver)
        self.assertEqual(assignment.status, ApprovalAssignmentStatus.APPROVED)
        self.assertEqual(assignment.signed_signature_data, SIGNATURE_DATA_URL)
        self.assertIn("-signed-", document.file_name or "")
        self.assertTrue((Path(settings.MEDIA_ROOT) / document.file_name).exists())
