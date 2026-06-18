from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models import Request, User

router = APIRouter()


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    users = db.scalars(select(User).options(joinedload(User.department))).all()
    requests = db.scalars(select(Request)).all()

    payload = []
    for item in users:
        if item.role.value in {"admin", "executive_manager", "manager"}:
            kpi = "96% تایید به موقع"
        else:
            count = sum(1 for req in requests if req.requester_id == item.id)
            kpi = f"{count} درخواست فعال"
        payload.append(
            {
                "name": item.full_name,
                "role": item.job_title,
                "department": item.department.name if item.department else "بدون واحد",
                "kpi": kpi,
            }
        )
    return payload
