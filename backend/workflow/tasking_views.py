from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt

from workflow.access import can_access_settings, can_manage_users, can_view_reports, get_user_organization, is_manager
from workflow.models import Task, TaskAttachment, TaskStatus, UserRole
from workflow.services import save_uploaded_file, validate_upload_file
from workflow.tasking import (
    TaskingError,
    accept_task,
    add_comment,
    approve_task,
    create_task,
    dashboard_payload,
    end_of_day_due_at,
    get_or_create_tasking_settings,
    local_today,
    mark_task_mentions_read,
    parse_iso_date,
    pause_task,
    preview_schedule,
    reject_task,
    reports_summary,
    request_changes,
    serialize_comment,
    serialize_task,
    serialize_tasking_settings,
    start_task,
    submit_review,
    update_estimate,
    update_tasking_settings,
    visible_tasks_queryset,
)
from workflow.views import json_error, json_response, methods, parse_json, require_auth


def _handle_tasking_error(exc: Exception):
    if isinstance(exc, TaskingError):
        return json_error(exc.message, status=exc.status)
    if isinstance(exc, ValueError):
        return json_error(str(exc), status=422)
    raise exc


@require_auth
@methods("GET")
def tasking_dashboard_view(request: HttpRequest):
    focus = parse_iso_date(request.GET.get("date"))
    try:
        return json_response(dashboard_payload(request.current_user, focus_date=focus))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("GET", "POST")
@csrf_exempt
def tasking_tasks_view(request: HttpRequest):
    if request.method == "GET":
        focus = parse_iso_date(request.GET.get("date"))
        scope = (request.GET.get("scope") or "mine").strip()
        status = (request.GET.get("status") or "").strip()
        q = (request.GET.get("q") or "").strip()
        qs = visible_tasks_queryset(request.current_user)
        if scope == "mine":
            qs = qs.filter(owner=request.current_user)
        elif scope == "supervise":
            qs = qs.exclude(owner=request.current_user)
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(code__icontains=q)
        items = [serialize_task(item, request.current_user, focus_date=focus) for item in qs.order_by("-updated_at")[:300]]
        return json_response({"tasks": items}, safe=True)

    payload = {}
    files = None
    content_type = str(request.content_type or "")
    if "multipart/form-data" in content_type or request.FILES:
        payload = {key: request.POST.get(key) for key in request.POST.keys()}
        if payload.get("observerIds"):
            try:
                import json

                payload["observerIds"] = json.loads(payload.get("observerIds") or "[]")
            except Exception:
                payload["observerIds"] = []
        files = request.FILES.getlist("attachments")
    else:
        payload = parse_json(request)
    try:
        task = create_task(request.current_user, payload, files=files)
        return json_response(serialize_task(task, request.current_user, include_detail=True), status=201)
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("GET", "PATCH")
@csrf_exempt
def tasking_task_detail_view(request: HttpRequest, task_id: int):
    task = visible_tasks_queryset(request.current_user).filter(pk=task_id).first()
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    if request.method == "GET":
        return json_response(serialize_task(task, request.current_user, include_detail=True))

    payload = parse_json(request)
    try:
        if "estimatedMinutes" in payload or "estimated_minutes" in payload:
            task = update_estimate(
                request.current_user,
                task,
                int(payload.get("estimatedMinutes") or payload.get("estimated_minutes")),
                reason=payload.get("reason") or "",
            )
        changed = []
        if "title" in payload:
            title = (payload.get("title") or "").strip()
            if title:
                task.title = title
                changed.append("title")
        if "description" in payload:
            task.description = (payload.get("description") or "").strip()
            changed.append("description")
        if "priority" in payload and payload.get("priority"):
            task.priority = payload["priority"]
            changed.append("priority")
        if "category" in payload:
            task.category = (payload.get("category") or "").strip()[:80]
            changed.append("category")
        if "departmentId" in payload or "department_id" in payload:
            dept_id = payload.get("departmentId", payload.get("department_id"))
            task.department_id = int(dept_id) if dept_id not in (None, "", 0, "0") else None
            changed.append("department")
        if "dueAt" in payload or "due_at" in payload:
            settings_obj = get_or_create_tasking_settings(task.organization)
            task.due_at = end_of_day_due_at(payload.get("dueAt") or payload.get("due_at"), settings_obj)
            changed.append("due_at")
        if "isPinned" in payload or "is_pinned" in payload:
            task.is_pinned = bool(payload.get("isPinned", payload.get("is_pinned")))
            changed.append("is_pinned")
        if changed:
            task.version = (task.version or 0) + 1
            task.save()
        return json_response(serialize_task(task, request.current_user, include_detail=True))
    except Exception as exc:
        return _handle_tasking_error(exc)


def _get_owned_or_visible_task(request: HttpRequest, task_id: int) -> Task | None:
    return visible_tasks_queryset(request.current_user).filter(pk=task_id).first()


@require_auth
@methods("POST")
@csrf_exempt
def tasking_accept_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    try:
        task = accept_task(request.current_user, task)
        return json_response(serialize_task(task, request.current_user, include_detail=True))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_reject_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    payload = parse_json(request)
    try:
        task = reject_task(request.current_user, task, reason=payload.get("reason") or "")
        return json_response(serialize_task(task, request.current_user, include_detail=True))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_start_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    payload = parse_json(request)
    try:
        task = start_task(request.current_user, task, stop_other=bool(payload.get("stopOther") or payload.get("stop_other")))
        return json_response(serialize_task(task, request.current_user, include_detail=True))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_pause_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    try:
        task = pause_task(request.current_user, task)
        return json_response(serialize_task(task, request.current_user, include_detail=True))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_resume_view(request: HttpRequest, task_id: int):
    return tasking_start_view(request, task_id)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_submit_review_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    payload = parse_json(request)
    try:
        task = submit_review(request.current_user, task, delivery_note=payload.get("deliveryNote") or payload.get("delivery_note") or "")
        return json_response(serialize_task(task, request.current_user, include_detail=True))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_approve_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    payload = parse_json(request)
    try:
        task = approve_task(request.current_user, task, comment=payload.get("comment") or "")
        return json_response(serialize_task(task, request.current_user, include_detail=True))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_request_changes_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    payload = parse_json(request)
    try:
        task = request_changes(request.current_user, task, comment=payload.get("comment") or payload.get("reason") or "")
        return json_response(serialize_task(task, request.current_user, include_detail=True))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_cancel_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    if request.current_user.id not in {task.creator_id, task.owner_id} and not is_manager(request.current_user):
        return json_error("اجازه لغو این تسک را ندارید.", status=403)
    task.status = TaskStatus.CANCELLED
    task.save(update_fields=["status", "updated_at", "version"])
    return json_response(serialize_task(task, request.current_user, include_detail=True))


@require_auth
@methods("GET", "POST")
@csrf_exempt
def tasking_comments_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    if request.method == "GET":
        comments = [
            serialize_comment(item)
            for item in task.comments.filter(deleted_at__isnull=True).select_related("author").prefetch_related("mentions").order_by("created_at")
        ]
        return json_response({"comments": comments})
    payload = parse_json(request)
    try:
        comment = add_comment(
            request.current_user,
            task,
            body=payload.get("body") or "",
            parent_id=payload.get("parentId") or payload.get("parent_id"),
            mention_ids=payload.get("mentionIds") or payload.get("mention_ids") or [],
        )
        return json_response(serialize_comment(comment), status=201)
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_mark_mentions_read_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    try:
        updated = mark_task_mentions_read(request.current_user, task)
        return json_response({"updated": updated, "task": serialize_task(task, request.current_user, include_detail=True)})
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_attachments_view(request: HttpRequest, task_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    files = request.FILES.getlist("attachments") or ([request.FILES.get("file")] if request.FILES.get("file") else [])
    if not files:
        return json_error("فایلی ارسال نشده است.", status=422)
    created = []
    for file_obj in files:
        if file_obj is None:
            continue
        try:
            validate_upload_file(file_obj)
        except ValueError as exc:
            return json_error(str(exc), status=422)
        stored = save_uploaded_file(file_obj)
        item = TaskAttachment.objects.create(
            task=task,
            uploader=request.current_user,
            original_name=file_obj.name,
            stored_name=stored,
            mime_type=getattr(file_obj, "content_type", "") or "",
            size_bytes=int(getattr(file_obj, "size", 0) or 0),
        )
        created.append(item)
    return json_response(serialize_task(task, request.current_user, include_detail=True), status=201)


@require_auth
@methods("GET")
def tasking_attachment_download_view(request: HttpRequest, task_id: int, attachment_id: int):
    task = _get_owned_or_visible_task(request, task_id)
    if task is None:
        return json_error("تسک پیدا نشد.", status=404)
    attachment = task.attachments.filter(pk=attachment_id).first()
    if attachment is None:
        return json_error("فایل پیدا نشد.", status=404)
    file_path = Path(settings.MEDIA_ROOT) / attachment.stored_name
    if not file_path.exists():
        return json_error("فایل موجود نیست.", status=404)
    return FileResponse(file_path.open("rb"), as_attachment=False, filename=attachment.original_name)


@require_auth
@methods("GET", "PATCH")
@csrf_exempt
def tasking_settings_view(request: HttpRequest):
    organization = get_user_organization(request.current_user)
    if request.method == "GET":
        settings_obj = get_or_create_tasking_settings(organization)
        return json_response(serialize_tasking_settings(settings_obj))
    if not can_access_settings(request.current_user) and not can_manage_users(request.current_user):
        return json_error("دسترسی کافی ندارید.", status=403)
    payload = parse_json(request)
    try:
        settings_obj = update_tasking_settings(organization, payload)
        return json_response(serialize_tasking_settings(settings_obj))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("POST")
@csrf_exempt
def tasking_schedule_preview_view(request: HttpRequest):
    payload = parse_json(request)
    organization = get_user_organization(request.current_user)
    settings_obj = get_or_create_tasking_settings(organization)
    assignee_id = payload.get("assigneeId") or payload.get("assignee_id") or request.current_user.id
    from workflow.access import organization_users

    assignee = organization_users(request.current_user).filter(pk=assignee_id).first() or request.current_user
    try:
        estimated = int(payload.get("estimatedMinutes") or payload.get("estimated_minutes") or 0)
    except (TypeError, ValueError):
        return json_error("زمان تخمینی معتبر نیست.", status=422)
    preview = preview_schedule(assignee, estimated, settings_obj, due_at=None)
    return json_response(preview)


@require_auth
@methods("GET")
def tasking_active_timer_view(request: HttpRequest):
    from workflow.models import TaskTimeEntry
    from django.utils import timezone

    entry = TaskTimeEntry.objects.filter(user=request.current_user, is_active=True).select_related("task").first()
    if entry is None:
        return json_response({"activeTimer": None})
    return json_response(
        {
            "activeTimer": {
                "taskId": entry.task_id,
                "taskTitle": entry.task.title,
                "startedAt": entry.started_at.isoformat(),
                "elapsedSeconds": max(0, int((timezone.now() - entry.started_at).total_seconds())),
            }
        }
    )


@require_auth
@methods("GET")
def tasking_reports_view(request: HttpRequest):
    if not can_view_reports(request.current_user) and not is_manager(request.current_user) and request.current_user.role not in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER}:
        # employees can still view own report
        pass
    organization = get_user_organization(request.current_user)
    settings_obj = get_or_create_tasking_settings(organization)
    today = local_today(settings_obj)
    start = parse_iso_date(request.GET.get("start") or request.GET.get("startDate")) or (today - timedelta(days=30))
    end = parse_iso_date(request.GET.get("end") or request.GET.get("endDate")) or today
    user_id = request.GET.get("userId") or request.GET.get("user_id")
    user_id = int(user_id) if user_id and str(user_id).isdigit() else None
    try:
        return json_response(reports_summary(request.current_user, start=start, end=end, user_id=user_id))
    except Exception as exc:
        return _handle_tasking_error(exc)


@require_auth
@methods("GET")
def tasking_reports_export_view(request: HttpRequest):
    import csv
    from django.http import HttpResponse

    organization = get_user_organization(request.current_user)
    settings_obj = get_or_create_tasking_settings(organization)
    today = local_today(settings_obj)
    start = parse_iso_date(request.GET.get("start") or request.GET.get("startDate")) or (today - timedelta(days=30))
    end = parse_iso_date(request.GET.get("end") or request.GET.get("endDate")) or today
    payload = reports_summary(request.current_user, start=start, end=end)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="tasking-report.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["نام", "بخش", "برنامه‌ریزی", "هدف", "واقعی", "Utilization", "وضعیت ظرفیت", "تکمیل", "عقب‌افتاده"])
    for row in payload["users"]:
        user = row["user"] or {}
        writer.writerow(
            [
                user.get("name"),
                user.get("department"),
                row["plannedMinutes"],
                row["targetMinutes"],
                row["actualMinutes"],
                row["utilizationPercent"],
                row["bandLabel"],
                row["completedCount"],
                row["overdueCount"],
            ]
        )
    return response
