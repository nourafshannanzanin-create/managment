from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models import User

router = APIRouter()


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    users = db.scalars(select(User).options(joinedload(User.department))).all()

    return [
        {
            "name": item.full_name,
            "role": item.job_title,
            "department": item.department.name if item.department else "",
            "kpi": "",
        }
        for item in users
    ]
