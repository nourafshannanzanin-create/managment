from __future__ import annotations

import mimetypes
from datetime import date, datetime
from pathlib import Path

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse, HttpRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from workflow.access import can_access_archive, get_user_organization, is_manager, organization_users
from workflow.models import ArchiveDocument, ArchiveReferral, AuditLog, Department, UserRole
from workflow.services import media_url, next_code, preview_kind_for_file, save_uploaded_file, user_avatar_url, validate_upload_file
from workflow.views import json_error, json_response, methods, parse_json, require_auth

ARCHIVE_UPLOAD_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
    ".txt",
}
ARCHIVE_MAX_BYTES = 15 * 1024 * 1024


def _can_manage_archive(user) -> bool:
    return bool(
        is_manager(user)
        or user.role in {UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER}
        or getattr(user, "platform_role", "") in {"hq_admin", "hq_support"}
    )


def _require_archive_access(user):
    if not can_access_archive(user):
        return json_error("دسترسی به بایگانی ندارید.", status=403)
    return None


def _scoped_archive_qs(user):
    organization = get_user_organization(user)
    qs = (
        ArchiveDocument.objects.filter(organization=organization, deleted_at__isnull=True)
        .select_related("owner", "department")
        .prefetch_related("referrals__user", "referrals__referred_by")
    )
    if _can_manage_archive(user):
        return qs
    return qs.filter(Q(owner=user) | Q(referrals__user=user)).distinct()


def _parse_date(raw) -> date | None:
    value = str(raw or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None


def _serialize_user(user, *, referral: ArchiveReferral | None = None) -> dict:
    if user is None:
        return {"id": None, "name": "", "jobTitle": "", "department": "", "avatar": "", "avatarUrl": ""}
    payload = {
        "id": user.id,
        "name": user.full_name,
        "jobTitle": user.job_title or "",
        "department": user.department.name if user.department_id else "",
        "avatar": user.avatar or "",
        "avatarUrl": user_avatar_url(user),
        "avatar_url": user_avatar_url(user),
    }
    if referral is not None:
        payload["status"] = referral.status
        payload["statusLabel"] = "تأیید شده" if referral.status == ArchiveReferral.Status.APPROVED else "در حال بررسی"
        payload["decidedAt"] = referral.decided_at.isoformat() if referral.decided_at else ""
        payload["isApproved"] = referral.status == ArchiveReferral.Status.APPROVED
    return payload


def _document_status(referrals: list[ArchiveReferral]) -> tuple[str, str]:
    if not referrals:
        return "recorded", "ثبت شده"
    if all(item.status == ArchiveReferral.Status.APPROVED for item in referrals):
        return "approved", "تأیید شده"
    return "reviewing", "در حال بررسی"


def serialize_archive_document(doc: ArchiveDocument, current_user) -> dict:
    referrals = list(doc.referrals.all())
    referral_users = [_serialize_user(item.user, referral=item) for item in referrals]
    is_owner = doc.owner_id == current_user.id
    my_referral = next((item for item in referrals if item.user_id == current_user.id), None)
    is_referred = my_referral is not None
    can_manage = _can_manage_archive(current_user)
    status_key, status_label = _document_status(referrals)
    return {
        "id": doc.code,
        "code": doc.code,
        "title": doc.title,
        "description": doc.description or "",
        "documentDate": doc.document_date.isoformat() if doc.document_date else "",
        "createdAt": doc.created_at.isoformat() if doc.created_at else "",
        "updatedAt": doc.updated_at.isoformat() if doc.updated_at else "",
        "owner": _serialize_user(doc.owner),
        "ownerName": doc.owner.full_name if doc.owner_id else "",
        "department": doc.department.name if doc.department_id else "",
        "departmentId": doc.department_id,
        "fileName": doc.original_name or doc.file_name,
        "originalName": doc.original_name or doc.file_name,
        "mimeType": doc.mime_type or "",
        "sizeBytes": int(doc.size_bytes or 0),
        "previewKind": preview_kind_for_file(doc.original_name or doc.file_name),
        "previewUrl": media_url(doc.file_name),
        "downloadUrl": f"/api/v1/archive/{doc.code}/download",
        "status": status_key,
        "statusLabel": status_label,
        "referrals": referral_users,
        "referralNames": [item["name"] for item in referral_users if item.get("name")],
        "isOwner": is_owner,
        "isReferred": is_referred,
        "myReferralStatus": my_referral.status if my_referral else "",
        "canApprove": bool(is_referred and my_referral and my_referral.status != ArchiveReferral.Status.APPROVED),
        "canDelete": is_owner or can_manage,
        "canRefer": is_owner or is_referred or can_manage,
        "canDownload": True,
    }


@require_auth
@csrf_exempt
@methods("GET", "POST")
def archive_list_view(request: HttpRequest):
    denied = _require_archive_access(request.current_user)
    if denied:
        return denied

    if request.method == "GET":
        q = (request.GET.get("q") or "").strip().lower()
        scope = (request.GET.get("scope") or "all").strip()
        qs = _scoped_archive_qs(request.current_user).order_by("-document_date", "-created_at")
        if scope == "mine":
            qs = qs.filter(owner=request.current_user)
        elif scope == "shared":
            qs = qs.filter(referrals__user=request.current_user).exclude(owner=request.current_user).distinct()
        items = []
        for item in qs[:400]:
            payload = serialize_archive_document(item, request.current_user)
            if q:
                hay = " ".join(
                    [
                        payload["title"],
                        payload["description"],
                        payload["ownerName"],
                        payload["department"],
                        " ".join(payload["referralNames"]),
                        payload["fileName"],
                        payload["code"],
                        payload["statusLabel"],
                    ]
                ).lower()
                if q not in hay:
                    continue
            items.append(payload)
        mine_count = sum(1 for item in items if item["isOwner"])
        shared_count = sum(1 for item in items if item["isReferred"] and not item["isOwner"])
        return json_response(
            {
                "items": items,
                "stats": {
                    "total": len(items),
                    "mine": mine_count,
                    "shared": shared_count,
                },
            }
        )

    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    document_date = _parse_date(request.POST.get("documentDate") or request.POST.get("document_date"))
    department_raw = (request.POST.get("departmentId") or request.POST.get("department") or "").strip()
    assignee_raw = request.POST.get("assigneeIds") or request.POST.get("referralIds") or ""
    assignee_ids = [int(part) for part in str(assignee_raw).replace("[", "").replace("]", "").split(",") if str(part).strip().isdigit()]
    file_obj = request.FILES.get("file")

    if not title:
        return json_error("نام سند الزامی است.", status=422)
    if document_date is None:
        return json_error("تاریخ سند معتبر نیست.", status=422)
    if file_obj is None:
        return json_error("بارگذاری فایل الزامی است.", status=422)

    try:
        validate_upload_file(file_obj, max_bytes=ARCHIVE_MAX_BYTES, allowed_extensions=ARCHIVE_UPLOAD_EXTENSIONS)
    except ValueError as exc:
        return json_error(str(exc), status=422)

    organization = get_user_organization(request.current_user)
    department = None
    if department_raw:
        if department_raw.isdigit():
            department = Department.objects.filter(pk=int(department_raw)).first()
        else:
            department = Department.objects.filter(code=department_raw).first()

    try:
        stored = save_uploaded_file(file_obj)
        doc = ArchiveDocument.objects.create(
            organization=organization,
            code=next_code("ARC"),
            title=title[:180],
            description=description,
            document_date=document_date,
            owner=request.current_user,
            department=department or request.current_user.department,
            file_name=stored,
            original_name=getattr(file_obj, "name", "") or stored,
            mime_type=getattr(file_obj, "content_type", "") or "",
            size_bytes=int(getattr(file_obj, "size", 0) or 0),
        )

        allowed_ids = set(
            organization_users(request.current_user)
            .filter(is_active=True, is_deleted=False)
            .values_list("id", flat=True)
        )
        for user_id in assignee_ids:
            if user_id == request.current_user.id or user_id not in allowed_ids:
                continue
            ArchiveReferral.objects.get_or_create(
                document=doc,
                user_id=user_id,
                defaults={"referred_by": request.current_user, "note": ""},
            )

        AuditLog.objects.create(
            actor=request.current_user,
            actor_name=request.current_user.full_name,
            action="archive_created",
            entity_type="archive",
            entity_code=doc.code,
            detail=doc.title,
            icon="folder_open",
        )
    except Exception as exc:
        return json_error(f"ثبت سند بایگانی ناموفق بود: {exc}", status=500)

    doc = _scoped_archive_qs(request.current_user).filter(pk=doc.pk).first() or doc
    return json_response(serialize_archive_document(doc, request.current_user), status=201)


@require_auth
@csrf_exempt
@methods("GET", "DELETE")
def archive_detail_view(request: HttpRequest, document_code: str):
    denied = _require_archive_access(request.current_user)
    if denied:
        return denied

    doc = _scoped_archive_qs(request.current_user).filter(code=document_code).first()
    if doc is None:
        return json_error("سند بایگانی پیدا نشد.", status=404)

    if request.method == "GET":
        return json_response(serialize_archive_document(doc, request.current_user))

    if not (doc.owner_id == request.current_user.id or _can_manage_archive(request.current_user)):
        return json_error("فقط ثبت‌کننده سند می‌تواند آن را حذف کند.", status=403)

    doc.deleted_at = timezone.now()
    doc.save(update_fields=["deleted_at", "updated_at"])
    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="archive_deleted",
        entity_type="archive",
        entity_code=doc.code,
        detail=doc.title,
        icon="delete",
    )
    return json_response({"ok": True, "id": doc.code})


@require_auth
@methods("GET")
def archive_download_view(request: HttpRequest, document_code: str):
    denied = _require_archive_access(request.current_user)
    if denied:
        return denied

    doc = _scoped_archive_qs(request.current_user).filter(code=document_code).first()
    if doc is None or not doc.file_name:
        return json_error("فایل پیدا نشد.", status=404)

    file_path = Path(settings.MEDIA_ROOT) / doc.file_name
    if not file_path.exists():
        return json_error("فایل روی سرور موجود نیست.", status=404)

    content_type, _ = mimetypes.guess_type(file_path.name)
    download_name = doc.original_name or f"{doc.code}{file_path.suffix.lower()}"
    inline = str(request.GET.get("inline") or "").strip().lower() in {"1", "true", "yes"}
    response = FileResponse(file_path.open("rb"), content_type=content_type or "application/octet-stream")
    disposition = "inline" if inline else "attachment"
    response["Content-Disposition"] = f'{disposition}; filename="{download_name}"'
    return response


@require_auth
@csrf_exempt
@methods("POST")
def archive_refer_view(request: HttpRequest, document_code: str):
    denied = _require_archive_access(request.current_user)
    if denied:
        return denied

    doc = _scoped_archive_qs(request.current_user).filter(code=document_code).first()
    if doc is None:
        return json_error("سند بایگانی پیدا نشد.", status=404)

    is_owner = doc.owner_id == request.current_user.id
    is_referred = doc.referrals.filter(user=request.current_user).exists()
    if not (is_owner or is_referred or _can_manage_archive(request.current_user)):
        return json_error("اجازه ارجاع این سند را ندارید.", status=403)

    payload = parse_json(request)
    assignee_ids = [int(item) for item in payload.get("assigneeIds", []) if str(item).isdigit()]
    note = (payload.get("note") or "").strip()
    if not assignee_ids:
        return json_error("حداقل یک نفر برای ارجاع انتخاب کنید.", status=422)

    allowed_ids = set(organization_users(request.current_user).filter(is_active=True, is_deleted=False).values_list("id", flat=True))
    created = 0
    for user_id in assignee_ids:
        if user_id == request.current_user.id or user_id not in allowed_ids:
            continue
        _, was_created = ArchiveReferral.objects.get_or_create(
            document=doc,
            user_id=user_id,
            defaults={"referred_by": request.current_user, "note": note},
        )
        if was_created:
            created += 1

    if created <= 0:
        return json_error("ارجاع جدیدی ثبت نشد. افراد انتخاب‌شده قبلاً دسترسی دارند.", status=422)

    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="archive_referred",
        entity_type="archive",
        entity_code=doc.code,
        detail=f"{created} ارجاع جدید",
        icon="forward",
    )
    refreshed = _scoped_archive_qs(request.current_user).filter(pk=doc.pk).first() or doc
    return json_response(serialize_archive_document(refreshed, request.current_user))


@require_auth
@csrf_exempt
@methods("POST")
def archive_approve_view(request: HttpRequest, document_code: str):
    denied = _require_archive_access(request.current_user)
    if denied:
        return denied

    doc = _scoped_archive_qs(request.current_user).filter(code=document_code).first()
    if doc is None:
        return json_error("سند بایگانی پیدا نشد.", status=404)

    referral = doc.referrals.filter(user=request.current_user).first()
    if referral is None:
        return json_error("فقط افراد ارجاع‌شده می‌توانند این سند را تأیید کنند.", status=403)

    if referral.status != ArchiveReferral.Status.APPROVED:
        referral.status = ArchiveReferral.Status.APPROVED
        referral.decided_at = timezone.now()
        referral.save(update_fields=["status", "decided_at"])

    AuditLog.objects.create(
        actor=request.current_user,
        actor_name=request.current_user.full_name,
        action="archive_approved",
        entity_type="archive",
        entity_code=doc.code,
        detail=doc.title,
        icon="verified",
    )
    refreshed = _scoped_archive_qs(request.current_user).filter(pk=doc.pk).first() or doc
    return json_response(serialize_archive_document(refreshed, request.current_user))
