from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_roles
from app.models import Document, User
from app.models.enums import DocumentStatus, UserRole
from app.services.bootstrap_service import document_risk_label, document_status_label

router = APIRouter()


class RejectPayload(BaseModel):
    reason: str


@router.get("")
def list_approvals(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.scalars(
        select(Document)
        .options(joinedload(Document.owner), joinedload(Document.department))
        .order_by(Document.uploaded_at.desc())
    ).unique().all()
    return [
        {
            "id": item.code,
            "title": item.title,
            "owner": item.owner.full_name if item.owner else "نامشخص",
            "type": item.document_type,
            "status": document_status_label(item.status),
            "department": item.department.name if item.department else "بدون واحد",
            "uploadedAt": item.uploaded_at.date().isoformat(),
            "risk": document_risk_label(item.risk.value),
            "summary": item.description,
        }
        for item in items
    ]


@router.get("/metrics")
def approval_metrics(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.scalars(select(Document)).all()
    return {
        "pending": sum(1 for item in items if item.status in {DocumentStatus.PENDING, DocumentStatus.WAITING_SIGNATURE}),
        "approved": sum(1 for item in items if item.status == DocumentStatus.APPROVED),
        "rejected": sum(1 for item in items if item.status == DocumentStatus.REJECTED),
    }


@router.post("/{document_code}/approve")
def approve_document(
    document_code: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER)),
):
    document = db.scalar(select(Document).where(Document.code == document_code))
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="سند پیدا نشد.")
    document.status = DocumentStatus.APPROVED
    document.approved_at = datetime.now(timezone.utc)
    document.rejected_at = None
    document.rejection_reason = None
    db.add(document)
    db.commit()
    return {"status": "approved", "document": document.code}


@router.post("/{document_code}/reject")
def reject_document(
    document_code: str,
    payload: RejectPayload,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.EXECUTIVE_MANAGER, UserRole.MANAGER)),
):
    document = db.scalar(select(Document).where(Document.code == document_code))
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="سند پیدا نشد.")
    document.status = DocumentStatus.REJECTED
    document.rejected_at = datetime.now(timezone.utc)
    document.rejection_reason = payload.reason
    db.add(document)
    db.commit()
    return {"status": "rejected", "document": document.code}
