from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models import Department, Request, RequestAttachment, RequestTimeline, User
from app.models.enums import RequestPriority, RequestStatus


def next_request_code(session: Session) -> str:
    count = session.scalar(select(func.count(Request.id))) or 0
    return f"REQ-{2409 + count}"


def save_upload(file: UploadFile) -> tuple[str, int]:
    unique_name = f"{uuid4().hex}-{file.filename}"
    destination = settings.upload_path / unique_name
    content = file.file.read()
    destination.write_bytes(content)
    return unique_name, len(content)


def create_request(
    session: Session,
    requester: User,
    title: str,
    description: str,
    department_code: str,
    manager_slug: str | None,
    priority: RequestPriority,
    deadline: date | None,
    files: list[UploadFile],
) -> Request:
    department = session.scalar(select(Department).where(Department.code == department_code))
    manager = session.scalar(select(User).where(User.slug == manager_slug)) if manager_slug else None

    request = Request(
        code=next_request_code(session),
        title=title or "درخواست بدون عنوان",
        description=description or "توضیحی ثبت نشده است.",
        priority=priority,
        status=RequestStatus.SUBMITTED,
        department_id=getattr(department, "id", None),
        requester_id=requester.id,
        manager_id=getattr(manager, "id", None),
        deadline=deadline,
    )
    session.add(request)
    session.flush()

    timeline_items = [
        RequestTimeline(
            request_id=request.id,
            action="created",
            note="ثبت اولیه توسط کاربر",
            actor_name=requester.full_name,
        ),
        RequestTimeline(
            request_id=request.id,
            action="submitted",
            note="درخواست ثبت و برای بررسی ارسال شد",
            actor_name=requester.full_name,
        ),
    ]
    session.add_all(timeline_items)

    for file in files:
        stored_name, size = save_upload(file)
        session.add(
            RequestAttachment(
                request_id=request.id,
                original_name=file.filename or "attachment",
                stored_name=stored_name,
                mime_type=file.content_type,
                size_bytes=size,
            )
        )

    session.commit()
    session.refresh(request)
    return session.scalar(
        select(Request)
        .where(Request.id == request.id)
        .options(
            joinedload(Request.requester),
            joinedload(Request.manager),
            joinedload(Request.department),
            joinedload(Request.timeline_items),
        )
    )
