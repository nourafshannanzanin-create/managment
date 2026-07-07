from __future__ import annotations

import base64
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from workflow.access import ensure_default_organization
from workflow.models import (
    ApprovalAssignment,
    ApprovalAssignmentStatus,
    Department,
    Document,
    DocumentRisk,
    DocumentStatus,
    Organization,
    OrganizationMembership,
    RegistrationRequest,
    SupportTicket,
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


class RegistrationTests(TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.temp_dir.name, MEDIA_URL="/media/")
        self.override.enable()
        self.addCleanup(self.override.disable)

    def test_register_endpoint_creates_review_ticket_then_hq_approves(self):
        client = Client()

        response = client.post(
            "/api/v1/auth/register",
            data={
                "organizationName": "مجموعه تست ثبت نام",
                "managerName": "مدیر تست ثبت نام",
                "managerUsername": "test-manager",
                "managerPhone": "09120000000",
                "managerPassword": "secret123",
                "documents": SimpleUploadedFile("license.pdf", b"test-license", content_type="application/pdf"),
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(Organization.objects.filter(code="test-org").exists())
        self.assertFalse(User.objects.filter(slug="test-manager").exists())
        registration = RegistrationRequest.objects.select_related("ticket").get()
        self.assertEqual(registration.status, "pending")
        self.assertEqual(registration.ticket.attachments.count(), 1)
        self.assertNotEqual(registration.manager_password_hash, "secret123")

        hq_user = User.objects.get(slug="milad_dhs")
        client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {create_access_token(str(hq_user.id), {'role': hq_user.role})}"
        approve_response = client.post(
            f"/api/v1/support/tickets/{registration.ticket_id}/approve-registration",
            data={"companyCode": "test-org"},
            content_type="application/json",
        )

        self.assertEqual(approve_response.status_code, 200)
        self.assertTrue(Organization.objects.filter(code="test-org").exists())
        self.assertTrue(User.objects.filter(slug="test-manager").exists())
        registration.refresh_from_db()
        self.assertEqual(registration.status, "approved")
        self.assertEqual(SupportTicket.objects.get(pk=registration.ticket_id).status, "closed")

        duplicate_response = client.post(
            f"/api/v1/support/tickets/{registration.ticket_id}/approve-registration",
            data={"companyCode": "another-code"},
            content_type="application/json",
        )
        self.assertEqual(duplicate_response.status_code, 409)
