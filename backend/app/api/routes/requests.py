from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models import Request, User
from app.models.enums import RequestPriority, UserRole
from app.schemas.request import RequestDetailResponse
from app.services.bootstrap_service import format_date, priority_label, request_status_label
from app.services.request_service import create_request

router = APIRouter()


@router.get("")
def list_requests(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.scalars(
        select(Request)
        .options(joinedload(Request.requester), joinedload(Request.manager), joinedload(Request.department))
        .order_by(Request.created_at.desc())
    ).unique().all()
    return [
        {
            "id": item.code,
            "title": item.title,
            "owner": item.requester.full_name if item.requester else "نامشخص",
            "manager": item.manager.full_name if item.manager else "تعیین نشده",
            "priority": priority_label(item.priority),
            "status": request_status_label(item.status),
            "department": item.department.name if item.department else "بدون واحد",
            "deadline": format_date(item.deadline),
            "description": item.description,
        }
        for item in items
    ]


@router.get("/{request_code}", response_model=RequestDetailResponse)
def get_request(
    request_code: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.scalar(
        select(Request)
        .where(Request.code == request_code)
        .options(
            joinedload(Request.requester),
            joinedload(Request.manager),
            joinedload(Request.department),
            joinedload(Request.timeline_items),
        )
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="درخواست پیدا نشد.")

    request_payload = {
        "id": item.code,
        "title": item.title,
        "owner": item.requester.full_name if item.requester else "نامشخص",
        "manager": item.manager.full_name if item.manager else "تعیین نشده",
        "priority": priority_label(item.priority),
        "status": request_status_label(item.status),
        "department": item.department.name if item.department else "بدون واحد",
        "deadline": format_date(item.deadline),
        "description": item.description,
    }
    timeline = [
        {"step": index + 1, "title": row.action, "note": row.note}
        for index, row in enumerate(sorted(item.timeline_items, key=lambda entry: entry.created_at))
    ]
    return {"request": request_payload, "timeline": timeline}


@router.post("")
def submit_request(
    title: str = Form(""),
    description: str = Form(""),
    department: str = Form(""),
    manager: str = Form(""),
    priority: RequestPriority = Form(RequestPriority.MEDIUM),
    deadline: date | None = Form(None),
    attachments: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = create_request(
        session=db,
        requester=current_user,
        title=title,
        description=description,
        department_code=department,
        manager_slug=manager or None,
        priority=priority,
        deadline=deadline,
        files=attachments,
    )
    return {
        "id": item.code,
        "title": item.title,
        "owner": item.requester.full_name if item.requester else current_user.full_name,
        "manager": item.manager.full_name if item.manager else "تعیین نشده",
        "priority": priority_label(item.priority),
        "status": request_status_label(item.status),
        "department": item.department.name if item.department else "بدون واحد",
        "deadline": format_date(item.deadline),
        "description": item.description,
    }
