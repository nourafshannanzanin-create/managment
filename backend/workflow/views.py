from __future__ import annotations

import json
import os
from datetime import date, timedelta
from functools import wraps

from django.core.management import call_command
from django.db import connection, transaction
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpRequest, HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from workflow.access import (
    attach_user,
    can_approve_documents,
    can_manage_users,
    can_view_reports,
    ensure_user_memberships,
    is_manager,
    require_roles,
    visible_users,
)
from workflow.document_signing import sign_document_file
from workflow.models import (
    ApprovalAssignment,
    ApprovalAssignmentStatus,
    AuditLog,
    ConfidentialityLevel,
    Department,
    Document,
    DocumentRisk,
    DocumentStatus,
    Expense,
    ExpenseCategory,
    ExpenseStatus,
    OrganizationMembership,
    Request,
    RequestPriority,
    RequestStatus,
    RequestTimeline,
    User,
    UserRole,
    UserSignature,
)
from workflow.security import create_access_token, decode_token, get_password_hash, verify_password
from workflow.seed import seed_demo_data
from workflow.services import (
    approval_metrics,
    build_bootstrap_payload,
    format_money,
    next_code,
    save_uploaded_file,
    serialize_approval,
    serialize_current_user,
    serialize_expense,
    serialize_request,
    serialize_user,
    update_document_status,
    visible_approvals,
    visible_expenses,
    visible_reports_payload,
    visible_requests,
)

JSON_KWARGS = {"ensure_ascii": False}


def json_response(payload, status=200, safe=True):
    return JsonResponse(payload, status=status, safe=safe, json_dumps_params=JSON_KWARGS)


def json_error(detail: str, status=400):
    return json_response({"detail": detail}, status=status)


def parse_json(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


def env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def workflow_tables_exist() -> bool:
    try:
        tables = set(connection.introspection.table_names())
    except (OperationalError, ProgrammingError):
        return False
    return {"users", "departments", "organizations", "organization_memberships"}.issubset(tables)


def require_auth(view_func):
    @wraps(view_func)
    def wrapped(request: HttpRequest, *args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return json_error("توکن نامعتبر است.", status=401)
        token = header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
            user_id = int(payload.get("sub"))
        except Exception:
            return json_error("توکن نامعتبر است.", status=401)
        user = User.objects.select_related("department", "manager").filter(pk=user_id, is_active=True).first()
        if user is None:
            return json_error("کاربر معتبر نیست.", status=401)
        attach_user(request, user)
        return view_func(request, *args, **kwargs)

    return wrapped


def methods(*allowed_methods):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request: HttpRequest, *args, **kwargs):
            if request.method not in allowed_methods:
                return HttpResponseNotAllowed(allowed_methods)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def startup_ready():
    if env_bool("WORKFLOW_AUTO_INIT_DB", True) and not workflow_tables_exist():
        call_command("migrate", interactive=False, verbosity=0)
    if not workflow_tables_exist():
        return
    ensure_user_memberships()
    if env_bool("WORKFLOW_AUTO_SEED_DB", True) and not User.objects.exists():
        seed_demo_data()


@methods("GET")
def health_view(request: HttpRequest):
    del request
    return json_response({"status": "ok"})


@csrf_exempt
@methods("POST")
def login_view(request: HttpRequest):
    startup_ready()
    payload = parse_json(request)
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    user = User.objects.select_related("department").filter(email=email).first()
    if user is None or not verify_password(password, user.password_hash):
        return json_error("ایمیل یا رمز عبور نادرست است.", status=401)
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])
    AuditLog.objects.create(actor=user, actor_name=user.full_name, action="login", entity_type="user", detail="ورود به سیستم", icon="login")
    token = create_access_token(str(user.id), {"role": user.role})
    return json_response({"access_token": token, "token_type": "bearer", "user": serialize_current_user(user)})


@require_auth
@methods("GET")
def me_view(request: HttpRequest):
    return json_response(serialize_current_user(request.current_user))


@require_auth
@methods("GET")
def bootstrap_view(request: HttpRequest):
    startup_ready()
    return json_response(build_bootstrap_payload(request.current_user))


@require_auth
@csrf_exempt
@methods("GET", "POST")
def requests_view(request: HttpRequest):
    if request.method == "GET":
        return json_response([serialize_request(item) for item in visible_requests(request.current_user)], safe=False)

    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    department_code = request.POST.get("department", "").strip()
    manager_slug = request.POST.get("manager", "").strip()
    priority = request.POST.get("priority", RequestPriority.MEDIUM)
    deadline_raw = request.POST.get("deadline", "").strip()
    deadline = date.fromisoformat(deadline_raw) if deadline_raw else None
    department = Department.objects.filter(code=department_code).first()
    manager = User.objects.filter(slug=manager_slug).first() if manager_slug else None

    request_obj = Request.objects.create(
        code=next_code("REQ"),
        title=title or "درخواست جدید",
        description=description or "",
        priority=priority,
        status=RequestStatus.SUBMITTED,
        department=department,
        requester=request.current_user,
        manager=manager,
        deadline=deadline,
        updated_at=timezone.now(),
    )
    RequestTimeline.objects.create(request=request_obj, action="created", note="ایجاد درخواست", actor_name=request.current_user.full_name)
    RequestTimeline.objects.create(request=request_obj, action="submitted", note="ثبت درخواست", actor_name=request.current_user.full_name)

    for file_obj in request.FILES.getlist("attachments"):
        stored_name = save_uploaded_file(file_obj)
        request_obj.attachments.create(
            original_name=file_obj.name,
            stored_name=stored_name,
            mime_type=file_obj.content_type,
            size_bytes=file_obj.size,
        )

    request_obj = Request.objects.select_related("requester", "manager", "department").prefetch_related("attachments").get(pk=request_obj.pk)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="request_created", entity_type="request", entity_code=request_obj.code, detail=request_obj.title, icon="assignment")
    return json_response(serialize_request(request_obj), status=201)


@require_auth
@methods("GET")
def request_detail_view(request: HttpRequest, request_code: str):
    request_obj = visible_requests(request.current_user).filter(code=request_code).first()
    if request_obj is None:
        return json_error("درخواست پیدا نشد.", status=404)
    return json_response(
        {
            "request": serialize_request(request_obj),
            "timeline": [
                {"step": index + 1, "title": item.action, "note": item.note}
                for index, item in enumerate(request_obj.timeline_items.order_by("created_at"))
            ],
        }
    )


@require_auth
@csrf_exempt
@methods("GET", "POST")
def expenses_view(request: HttpRequest):
    if request.method == "GET":
        return json_response([serialize_expense(item) for item in visible_expenses(request.current_user)], safe=False)

    description = request.POST.get("description", "").strip()
    amount = request.POST.get("amount", "0")
    expense_date_raw = request.POST.get("expenseDate", "").strip()
    if not expense_date_raw:
        return json_error("تاریخ هزینه الزامی است.", status=422)
    department_code = request.POST.get("department", "").strip()
    invoice = request.FILES.get("invoice")
    expense_date = date.fromisoformat(expense_date_raw)
    department = Department.objects.filter(code=department_code).first() or request.current_user.department
    invoice_name = save_uploaded_file(invoice) if invoice else None

    expense = Expense.objects.create(
        code=next_code("EXP"),
        title=(description[:180] or "هزینه جدید"),
        amount=amount,
        category=ExpenseCategory.MISCELLANEOUS,
        status=ExpenseStatus.PENDING,
        progress=25,
        expense_date=expense_date,
        notes=description,
        department=department,
        owner=request.current_user,
        invoice_file_name=invoice_name,
    )
    expense = Expense.objects.select_related("owner", "department").get(pk=expense.pk)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="expense_created", entity_type="expense", entity_code=expense.code, detail=expense.title, icon="payments")
    return json_response(serialize_expense(expense), status=201)


@require_auth
@methods("GET")
def expenses_summary_view(request: HttpRequest):
    items = list(visible_expenses(request.current_user))
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    return json_response(
        [
            {"label": "امروز", "value": format_money(sum(item.amount for item in items if item.expense_date == today))},
            {"label": "این هفته", "value": format_money(sum(item.amount for item in items if item.expense_date >= week_start))},
            {"label": "این ماه", "value": format_money(sum(item.amount for item in items if item.expense_date.month == today.month))},
            {"label": "امسال", "value": format_money(sum(item.amount for item in items if item.expense_date.year == today.year))},
        ],
        safe=False,
    )


@require_auth
@csrf_exempt
@methods("GET", "POST")
def users_view(request: HttpRequest):
    if not can_manage_users(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    if request.method == "GET":
        users_qs = visible_users(request.current_user).select_related("department", "manager").order_by("created_at")
        return json_response([serialize_user(item) for item in users_qs], safe=False)

    payload = parse_json(request)
    email = (payload.get("email") or "").strip().lower()
    if User.objects.filter(email=email).exists():
        return json_error("این ایمیل قبلا ثبت شده است.", status=409)

    role = payload.get("accessRole", UserRole.EMPLOYEE)
    department = Department.objects.filter(code=payload.get("department", "")).first()
    manager = User.objects.filter(pk=payload.get("managerId")).first() if payload.get("managerId") else None
    full_name = (payload.get("fullName") or "").strip()

    user = User.objects.create(
        slug=email.split("@", 1)[0].replace(".", "-"),
        full_name=full_name,
        email=email,
        phone=None,
        password_hash=get_password_hash(payload.get("password") or "UserSecret123!"),
        role=role,
        job_title=(payload.get("jobTitle") or ("مدیر" if role != UserRole.EMPLOYEE else "کارمند")).strip(),
        avatar=(full_name[:2] if full_name else "NA").upper(),
        bio="",
        is_active=True,
        department=department,
        manager=manager,
    )
    organization = OrganizationMembership.objects.select_related("organization").get(user=request.current_user).organization
    OrganizationMembership.objects.create(organization=organization, user=user, display_title=user.job_title)
    user = User.objects.select_related("department", "manager").get(pk=user.pk)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="user_created", entity_type="user", entity_code=str(user.id), detail=user.full_name, icon="group")
    return json_response(serialize_user(user), status=201)


@require_auth
@methods("GET")
def reports_view(request: HttpRequest):
    if not can_view_reports(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    return json_response(visible_reports_payload(request.current_user))


@require_auth
@methods("GET")
def approvals_view(request: HttpRequest):
    if not can_approve_documents(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    return json_response([serialize_approval(item, request.current_user) for item in visible_approvals(request.current_user)], safe=False)


@require_auth
@methods("GET")
def approvals_metrics_view(request: HttpRequest):
    if not can_approve_documents(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    return json_response(approval_metrics(request.current_user))


@require_auth
@csrf_exempt
@methods("GET", "POST")
def approvals_signature_view(request: HttpRequest):
    if not can_approve_documents(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    signature = UserSignature.objects.filter(user=request.current_user).first()
    if request.method == "GET":
        return json_response({"hasSignature": signature is not None, "signatureData": signature.signature_data if signature else ""})

    payload = parse_json(request)
    signature_data = payload.get("signatureData", "")
    if signature is None:
        signature = UserSignature.objects.create(user=request.current_user, signature_data=signature_data)
    else:
        signature.signature_data = signature_data
        signature.updated_at = timezone.now()
        signature.save(update_fields=["signature_data", "updated_at"])
    return json_response({"hasSignature": True, "signatureData": signature.signature_data})


@require_auth
@require_roles(UserRole.ADMIN)
@csrf_exempt
@methods("POST")
def documents_create_view(request: HttpRequest):
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    department_code = request.POST.get("department", "").strip()
    document_type = request.POST.get("documentType", "سند").strip()
    risk = request.POST.get("risk", DocumentRisk.MEDIUM)
    assignee_ids = [int(item) for item in request.POST.get("assigneeIds", "").split(",") if item.strip()]
    file_obj = request.FILES.get("file")
    if not assignee_ids:
        return json_error("حداقل یک مدیر باید انتخاب شود.", status=422)
    if file_obj is None:
        return json_error("فایل سند الزامی است.", status=422)
    approvers = list(User.objects.filter(pk__in=assignee_ids))
    if not approvers or any(not is_manager(item) for item in approvers):
        return json_error("ارجاع سند فقط به مدیر مجاز است.", status=422)

    document = Document.objects.create(
        code=next_code("DOC"),
        title=title or "سند جدید",
        description=description,
        document_type=document_type,
        status=DocumentStatus.PENDING,
        risk=risk,
        confidentiality=ConfidentialityLevel.INTERNAL,
        department=Department.objects.filter(code=department_code).first() or request.current_user.department,
        owner=request.current_user,
        file_name=save_uploaded_file(file_obj),
    )
    for approver in approvers:
        ApprovalAssignment.objects.create(document=document, approver=approver, status=ApprovalAssignmentStatus.PENDING)
    document = Document.objects.select_related("owner", "department").prefetch_related("approval_assignments__approver").get(pk=document.pk)
    AuditLog.objects.create(actor=request.current_user, actor_name=request.current_user.full_name, action="document_created", entity_type="document", entity_code=document.code, detail=document.title, icon="description")
    return json_response(serialize_approval(document, request.current_user), status=201)


@require_auth
@methods("GET")
def approval_detail_view(request: HttpRequest, document_code: str):
    if not can_approve_documents(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    document = visible_approvals(request.current_user).filter(code=document_code).first()
    if document is None:
        return json_error("سند پیدا نشد.", status=404)
    return json_response(serialize_approval(document, request.current_user))


@require_auth
@csrf_exempt
@methods("POST")
def approval_approve_view(request: HttpRequest, document_code: str):
    if not can_approve_documents(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    document = Document.objects.prefetch_related("approval_assignments").filter(code=document_code).first()
    if document is None:
        return json_error("سند پیدا نشد.", status=404)
    assignment = document.approval_assignments.filter(approver=request.current_user).first()
    if assignment is None:
        return json_error("این سند به شما ارجاع نشده است.", status=403)
    if assignment.status == ApprovalAssignmentStatus.APPROVED:
        return json_response({"status": "approved", "document": document.code})
    signature = UserSignature.objects.filter(user=request.current_user).first()
    if signature is None:
        return json_error("ابتدا امضای خود را ثبت کنید.", status=400)

    try:
        with transaction.atomic():
            assignment.status = ApprovalAssignmentStatus.APPROVED
            assignment.decision_note = ""
            assignment.signed_signature_data = signature.signature_data
            assignment.acted_at = timezone.now()
            assignment.save(update_fields=["status", "decision_note", "signed_signature_data", "acted_at"])
            document.file_name = sign_document_file(document, assignment, signature.signature_data)
            document.save(update_fields=["file_name"])
            update_document_status(document)
    except (ValueError, FileNotFoundError) as exc:
        return json_error(str(exc), status=422)
    except Exception:
        return json_error("امضای سند با خطا مواجه شد.", status=500)

    return json_response({"status": "approved", "document": document.code})


@require_auth
@csrf_exempt
@methods("POST")
def approval_reject_view(request: HttpRequest, document_code: str):
    if not can_approve_documents(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    payload = parse_json(request)
    document = Document.objects.prefetch_related("approval_assignments").filter(code=document_code).first()
    if document is None:
        return json_error("سند پیدا نشد.", status=404)
    assignment = document.approval_assignments.filter(approver=request.current_user).first()
    if assignment is None:
        return json_error("این سند به شما ارجاع نشده است.", status=403)
    reason = (payload.get("reason") or "").strip()
    assignment.status = ApprovalAssignmentStatus.REJECTED
    assignment.decision_note = reason
    assignment.signed_signature_data = ""
    assignment.acted_at = timezone.now()
    assignment.save(update_fields=["status", "decision_note", "signed_signature_data", "acted_at"])
    document.rejection_reason = reason
    document.save(update_fields=["rejection_reason"])
    update_document_status(document)
    return json_response({"status": "rejected", "document": document.code})


@require_auth
@methods("GET")
def settings_view(request: HttpRequest):
    del request
    return json_response(
        [
            {"title": "حساب کاربری", "description": "مدیریت نقش ها و دسترسی"},
            {"title": "اسناد", "description": "گردش کار امضای دیجیتال"},
            {"title": "هزینه ها", "description": "ثبت، پیگیری و کنترل هزینه"},
            {"title": "گزارشات", "description": "تحلیل مدیریتی"},
        ],
        safe=False,
    )
