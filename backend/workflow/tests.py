from __future__ import annotations

import base64
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image

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
    Wallet,
)
from workflow.security import create_access_token, get_password_hash
from workflow.views import DEFAULT_SIGNATURE_DATA, notify_sms

SOURCE_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="
SIGNATURE_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAQAAAACCAYAAAB/qH1jAAAAE0lEQVR4nGMUERH5z4AEmBjQAAAlyAE/YHhewAAAAABJRU5ErkJggg=="
SIGNATURE_DATA_URL = f"data:image/png;base64,{SIGNATURE_PNG_BASE64}"
STAMP_DATA_URL = SIGNATURE_DATA_URL


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
        self.assertEqual(response.json(), {"hasSignature": False, "signatureData": "", "hasStamp": False, "stampData": ""})

    def test_approve_document_requires_real_signature(self):
        document = self._create_document()
        UserSignature.objects.create(user=self.approver, signature_data=DEFAULT_SIGNATURE_DATA)

        response = self.client.post(f"/api/v1/approvals/{document.code}/approve")

        self.assertEqual(response.status_code, 422)
        self.assertIn("امضای دیجیتال معتبر", response.json()["detail"])
        assignment = ApprovalAssignment.objects.get(document=document, approver=self.approver)
        self.assertEqual(assignment.status, ApprovalAssignmentStatus.PENDING)

    def test_signature_endpoint_normalizes_uploaded_signature_and_stamp(self):
        UserSignature.objects.create(user=self.approver, signature_data=DEFAULT_SIGNATURE_DATA)
        source = Image.new("RGBA", (32, 20), (255, 255, 255, 255))
        source.putpixel((14, 9), (32, 32, 32, 255))
        source.putpixel((15, 9), (32, 32, 32, 255))
        source.putpixel((16, 10), (32, 32, 32, 255))
        stream = io.BytesIO()
        source.save(stream, format="PNG")
        uploaded_data_url = f"data:image/png;base64,{base64.b64encode(stream.getvalue()).decode('ascii')}"

        response = self.client.post(
            "/api/v1/approvals/signature",
            data={"signatureData": uploaded_data_url, "stampData": uploaded_data_url},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["hasSignature"])
        self.assertTrue(payload["hasStamp"])
        self.assertTrue(payload["signatureData"].startswith("data:image/png;base64,"))
        self.assertTrue(payload["stampData"].startswith("data:image/png;base64,"))
        self.assertNotEqual(payload["signatureData"], uploaded_data_url)
        self.assertNotEqual(payload["stampData"], uploaded_data_url)

    def test_approve_document_signs_file_without_stamp(self):
        document = self._create_document()
        UserSignature.objects.create(user=self.approver, signature_data=SIGNATURE_DATA_URL, stamp_data="")

        response = self.client.post(f"/api/v1/approvals/{document.code}/approve")

        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        assignment = ApprovalAssignment.objects.get(document=document, approver=self.approver)
        self.assertEqual(assignment.status, ApprovalAssignmentStatus.APPROVED)
        self.assertTrue(assignment.signed_signature_data.startswith("data:image/png;base64,"))
        self.assertIn("-signed-", document.file_name or "")

    def test_approve_document_signs_file_when_real_signature_exists(self):
        document = self._create_document()
        UserSignature.objects.create(user=self.approver, signature_data=SIGNATURE_DATA_URL, stamp_data=STAMP_DATA_URL)

        response = self.client.post(f"/api/v1/approvals/{document.code}/approve")

        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        assignment = ApprovalAssignment.objects.get(document=document, approver=self.approver)
        self.assertEqual(assignment.status, ApprovalAssignmentStatus.APPROVED)
        self.assertTrue(assignment.signed_signature_data.startswith("data:image/png;base64,"))
        self.assertNotEqual(assignment.signed_signature_data, SIGNATURE_DATA_URL)
        self.assertIn("-signed-", document.file_name or "")
        self.assertTrue((Path(settings.MEDIA_ROOT) / document.file_name).exists())

    def test_manager_can_refer_document_to_employee_and_employee_can_approve(self):
        document = self._create_document()
        employee = self._create_user("employee-approver", "employee-approver@example.com", UserRole.EMPLOYEE, "کارشناس")
        UserSignature.objects.create(user=self.approver, signature_data=SIGNATURE_DATA_URL, stamp_data="")
        UserSignature.objects.create(user=employee, signature_data=SIGNATURE_DATA_URL, stamp_data="")

        refer_response = self.client.post(
            f"/api/v1/approvals/{document.code}/refer",
            data={"assigneeIds": [employee.id]},
            content_type="application/json",
        )

        self.assertEqual(refer_response.status_code, 200)
        self.assertTrue(ApprovalAssignment.objects.filter(document=document, approver=employee).exists())

        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {create_access_token(str(employee.id), {'role': employee.role})}"
        approve_response = self.client.post(f"/api/v1/approvals/{document.code}/approve")

        self.assertEqual(approve_response.status_code, 200)
        assignment = ApprovalAssignment.objects.get(document=document, approver=employee)
        self.assertEqual(assignment.status, ApprovalAssignmentStatus.APPROVED)

    def test_create_document_allows_employee_assignee(self):
        employee = self._create_user("employee-target", "employee-target@example.com", UserRole.EMPLOYEE, "کارشناس")

        response = self.client.post(
            "/api/v1/approvals/documents",
            data={
                "title": "سند برای کارمند",
                "description": "تست ارجاع مستقیم",
                "department": self.department.code,
                "documentType": "فرم",
                "risk": "medium",
                "assigneeIds": str(employee.id),
                "file": SimpleUploadedFile("document.pdf", b"pdf-content", content_type="application/pdf"),
            },
        )

        self.assertEqual(response.status_code, 201)
        created_code = response.json()["id"]
        document = Document.objects.get(code=created_code)
        self.assertTrue(ApprovalAssignment.objects.filter(document=document, approver=employee).exists())


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


class UserAndSettingsTests(TestCase):
    def setUp(self):
        self.organization = ensure_default_organization()
        self.department = Department.objects.create(code="it", name="فناوری اطلاعات")
        self.manager = User.objects.create(
            slug="manager",
            full_name="مدیر تست",
            email="manager@example.com",
            phone="09120000000",
            password_hash=get_password_hash("secret123"),
            role=UserRole.ADMIN,
            job_title="مدیر",
            avatar="MT",
            department=self.department,
        )
        OrganizationMembership.objects.create(organization=self.organization, user=self.manager, display_title=self.manager.job_title)
        self.client = Client()
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {create_access_token(str(self.manager.id), {'role': self.manager.role})}"

    @patch("workflow.views.notify_sms")
    def test_create_user_persists_phone(self, notify_sms_mock):
        response = self.client.post(
            "/api/v1/users",
            data={
                "fullName": "میلاد دهستانی",
                "username": "millaad",
                "password": "Secret123!",
                "phone": "09134279848",
                "accessRole": "manager",
                "department": self.department.code,
                "jobTitle": "مدیر فنی",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        created_user = User.objects.get(slug="millaad")
        self.assertEqual(created_user.phone, "09134279848")
        self.assertEqual(response.json()["phone"], "09134279848")
        notify_sms_mock.assert_called_once()
        sms_tenant, sms_text, sms_recipients = notify_sms_mock.call_args.args[:3]
        self.assertEqual(sms_tenant, self.organization)
        self.assertEqual(sms_recipients, ["09134279848"])
        self.assertIn("کارنومند | مشخصات ورود به سامانه", sms_text)
        self.assertIn(f"مجموعه «{self.organization.name}»", sms_text)
        self.assertIn("این پیامک برای اعلام مشخصات ورود شما", sms_text)
        self.assertIn("نام کاربری: millaad", sms_text)
        self.assertIn("رمز عبور: Secret123!", sms_text)
        self.assertIn("آدرس سامانه: https://carnomand.ir", sms_text)

    def test_settings_profile_uses_and_updates_organization_code(self):
        profile_response = self.client.get("/api/v1/settings/profile")

        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json()["systemId"], self.organization.code.upper())

        update_response = self.client.post(
            "/api/v1/settings/profile",
            data={
                "organizationName": "سلام علیک",
                "systemId": "KARO-0018",
            },
            content_type="application/json",
        )

        self.assertEqual(update_response.status_code, 200)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, "سلام علیک")
        self.assertEqual(self.organization.code, "karo-0018")
        self.assertEqual(update_response.json()["systemId"], "KARO-0018")

    def test_update_user_persists_phone(self):
        user = User.objects.create(
            slug="millaad",
            full_name="میلاد دهستانی",
            email="millaad@example.com",
            phone="",
            password_hash=get_password_hash("secret123"),
            role=UserRole.MANAGER,
            job_title="مدیر فنی",
            avatar="MD",
            department=self.department,
            manager=self.manager,
        )
        OrganizationMembership.objects.create(organization=self.organization, user=user, display_title=user.job_title)

        response = self.client.patch(
            f"/api/v1/users/{user.id}",
            data={
                "fullName": "میلاد دهستانی",
                "username": "millaad",
                "phone": "09134279848",
                "accessRole": "manager",
                "department": self.department.code,
                "managerId": self.manager.id,
                "jobTitle": "مدیر فنی",
                "isActive": True,
                "bonusDelta": "1250000",
                "penaltyDelta": "350000",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.phone, "09134279848")
        self.assertEqual(response.json()["phone"], "09134279848")
        self.assertEqual(str(user.bonus_amount), "1250000.00")
        self.assertEqual(str(user.penalty_amount), "350000.00")
        self.assertEqual(response.json()["bonusAmountRaw"], 1250000.0)
        self.assertEqual(response.json()["penaltyAmountRaw"], 350000.0)
        self.assertIsNotNone(user.finance_updated_at)
        self.assertTrue(response.json()["financeUpdatedAt"])
        self.assertTrue(response.json()["financeUpdatedAtIso"])

        second_response = self.client.patch(
            f"/api/v1/users/{user.id}",
            data={
                "fullName": "میلاد دهستانی",
                "username": "millaad",
                "phone": "09134279848",
                "accessRole": "manager",
                "department": self.department.code,
                "managerId": self.manager.id,
                "jobTitle": "مدیر فنی",
                "isActive": True,
                "bonusDelta": "500000",
                "penaltyDelta": "150000",
            },
            content_type="application/json",
        )

        self.assertEqual(second_response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(str(user.bonus_amount), "1750000.00")
        self.assertEqual(str(user.penalty_amount), "500000.00")
        self.assertIsNotNone(user.finance_updated_at)

    def test_bootstrap_exposes_global_approvals_and_restricted_expenses(self):
        employee = User.objects.create(
            slug="employee",
            full_name="کارمند تست",
            email="employee@example.com",
            phone="09121111111",
            password_hash=get_password_hash("secret123"),
            role=UserRole.EMPLOYEE,
            job_title="کارشناس",
            avatar="KT",
            department=self.department,
            manager=self.manager,
        )
        OrganizationMembership.objects.create(organization=self.organization, user=employee, display_title=employee.job_title)
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {create_access_token(str(employee.id), {'role': employee.role})}"

        response = self.client.get("/api/v1/bootstrap")

        self.assertEqual(response.status_code, 200)
        current_user = response.json()["currentUser"]
        self.assertTrue(current_user["canAccessApprovals"])
        self.assertFalse(current_user["canAccessExpenses"])

    def test_users_report_export_includes_bonus_and_penalty(self):
        user = User.objects.create(
            slug="report-user",
            full_name="کاربر گزارش",
            email="report-user@example.com",
            phone="09125555555",
            password_hash=get_password_hash("secret123"),
            role=UserRole.EMPLOYEE,
            job_title="کارشناس",
            avatar="KG",
            department=self.department,
            manager=self.manager,
            bonus_amount="2000000.00",
            penalty_amount="500000.00",
        )
        OrganizationMembership.objects.create(organization=self.organization, user=user, display_title=user.job_title)

        response = self.client.get("/api/v1/reports/users/export?format=csv")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("bonus_amount", content)
        self.assertIn("report-user", content)
        self.assertIn("2,000,000.00", content)
        self.assertIn("500,000.00", content)

    @patch("workflow.views.send_provider_sms")
    def test_notify_sms_does_not_send_when_sms_wallet_is_empty(self, send_provider_sms_mock):
        Wallet.objects.update_or_create(
            organization=self.organization,
            key="sms",
            defaults={"name": "کیف پول پیامک", "balance": 0, "low_balance_threshold": 0, "is_active": True},
        )

        result = notify_sms(self.organization, "متن تست", ["09134279848"], actor=self.manager)

        self.assertFalse(result["ok"])
        self.assertIn("عدم موجودی", result["message"])
        send_provider_sms_mock.assert_not_called()

    @patch("workflow.views.send_provider_sms")
    def test_notify_sms_appends_footer_before_send(self, send_provider_sms_mock):
        Wallet.objects.update_or_create(
            organization=self.organization,
            key="sms",
            defaults={"name": "کیف پول پیامک", "balance": 1000000, "low_balance_threshold": 0, "is_active": True},
        )
        send_provider_sms_mock.return_value = {
            "ok": True,
            "provider_id": "provider-1",
            "payload": {"recipients": ["09134279848"]},
        }

        result = notify_sms(self.organization, "متن تست", ["09134279848"], actor=self.manager)

        self.assertTrue(result["ok"])
        sent_text = send_provider_sms_mock.call_args.args[1]
        self.assertTrue(sent_text.endswith("از طرف کارنومند"))

    @override_settings()
    @patch.dict("os.environ", {"SMS_PRICE_PER_100_CHARS": "185", "SMS_CHARS_PER_SEGMENT": "70"}, clear=False)
    def test_sms_char_blocks_and_send_cost(self):
        from decimal import Decimal

        from workflow.views import sms_char_blocks, sms_send_cost, sms_text_with_footer

        self.assertEqual(sms_char_blocks(""), 0)
        self.assertEqual(sms_char_blocks("a" * 1), 1)
        self.assertEqual(sms_char_blocks("a" * 70), 1)
        self.assertEqual(sms_char_blocks("a" * 71), 2)
        self.assertEqual(sms_char_blocks("a" * 140), 2)
        self.assertEqual(sms_char_blocks("a" * 141), 3)

        one_block = "x" * 50
        two_blocks = "x" * 120
        self.assertEqual(sms_send_cost(one_block, ["09120000001"]), Decimal("185"))
        self.assertEqual(sms_send_cost(two_blocks, ["09120000001"]), Decimal("370"))
        self.assertEqual(sms_send_cost(one_block, ["09120000001", "09120000002"]), Decimal("370"))

        with_footer = sms_text_with_footer("سلام")
        expected_blocks = sms_char_blocks(with_footer)
        self.assertEqual(sms_send_cost(with_footer, ["09120000001"]), Decimal(185 * expected_blocks))

    def test_organization_trial_unlocks_then_locks(self):
        from datetime import timedelta

        from workflow.models import FeaturePurchase
        from workflow.services import (
            CORE_FEATURE_KEY,
            active_feature_keys,
            license_status_payload,
            now,
            organization_trial_active,
        )

        trial_org = Organization.objects.create(code="trial-org", name="سازمان آزمایشی رایگان")
        unlocked = license_status_payload(trial_org)
        self.assertTrue(organization_trial_active(trial_org))
        self.assertFalse(unlocked["isLocked"])
        self.assertEqual(unlocked["reason"], "trial_active")
        self.assertTrue(unlocked["trialActive"])
        self.assertGreater(unlocked["trialRemainingSeconds"], 0)
        self.assertIn(CORE_FEATURE_KEY, active_feature_keys(trial_org))
        self.assertIn("attendance", active_feature_keys(trial_org))
        self.assertIn("cloud_storage", active_feature_keys(trial_org))

        trial_org.created_at = now() - timedelta(hours=25)
        trial_org.save(update_fields=["created_at"])
        locked = license_status_payload(trial_org)
        self.assertFalse(organization_trial_active(trial_org))
        self.assertTrue(locked["isLocked"])
        self.assertEqual(locked["reason"], "core_purchase_required")

        FeaturePurchase.objects.create(
            organization=trial_org,
            feature_key=CORE_FEATURE_KEY,
            title="خرید نرم افزار",
            is_active=True,
            total_amount="4000000.00",
            paid_amount="1000000.00",
            remaining_amount="3000000.00",
        )
        paid = license_status_payload(trial_org)
        self.assertFalse(paid["isLocked"])
        self.assertFalse(paid["trialActive"])


class ShowcaseWalletSmsTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            code="carnomand-sample-test",
            name="کارنومند نمونه تست",
            is_showcase=True,
        )
        from workflow.models import OrganizationPreference

        OrganizationPreference.objects.create(
            organization=self.organization,
            two_factor_required=False,
            sms_daily_limit=5,
            sms_monthly_limit=100,
        )
        Wallet.objects.update_or_create(
            organization=self.organization,
            key="sms",
            defaults={"name": "کیف پول پیامک", "balance": 0, "low_balance_threshold": 0, "is_active": True},
        )
        Wallet.objects.update_or_create(
            organization=self.organization,
            key="main",
            defaults={"name": "کیف پول اصلی", "balance": 1000, "low_balance_threshold": 0, "is_active": True},
        )

    @patch("workflow.views.send_provider_sms")
    def test_showcase_sms_ignores_wallet_but_counts_daily_limit(self, send_provider_sms_mock):
        from decimal import Decimal

        from workflow.models import WalletTransaction
        from workflow.services import wallet_dashboard_payload

        send_provider_sms_mock.return_value = {
            "ok": True,
            "provider_id": "provider-showcase",
            "payload": {"recipients": ["09121110001"]},
        }

        result = notify_sms(self.organization, "متن تست", ["09121110001"], actor=None)
        self.assertTrue(result["ok"])
        send_provider_sms_mock.assert_called_once()

        sms_wallet = Wallet.objects.get(organization=self.organization, key="sms")
        self.assertEqual(Decimal(sms_wallet.balance), Decimal("0"))

        usage = WalletTransaction.objects.filter(organization=self.organization, transaction_type="sms_send")
        self.assertEqual(usage.count(), 1)
        self.assertEqual(Decimal(usage.first().amount), Decimal("0"))

        payload = wallet_dashboard_payload(self.organization)
        self.assertTrue(payload["schematic"])
        self.assertEqual(payload["transactions"], [])
        self.assertEqual(payload["summary"]["smsBalanceRaw"], 0.0)

    def test_showcase_wallet_mutations_are_blocked(self):
        from workflow.services import SHOWCASE_WALLET_READONLY_MESSAGE, is_showcase_organization

        self.assertTrue(is_showcase_organization(self.organization))
        self.assertIn("نمایشی", SHOWCASE_WALLET_READONLY_MESSAGE)
