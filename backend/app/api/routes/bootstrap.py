from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.bootstrap import BootstrapResponse
from app.services.bootstrap_service import build_bootstrap_payload

router = APIRouter()


@router.get("", response_model=BootstrapResponse)
def get_bootstrap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return build_bootstrap_payload(db, current_user)
