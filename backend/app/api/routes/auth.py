from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.auth import CurrentUserResponse, LoginRequest, TokenResponse

router = APIRouter()


def serialize_user(user: User) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        slug=user.slug,
        name=user.full_name,
        role=user.job_title,
        department=user.department.name if user.department else "بدون واحد",
        avatar=user.avatar,
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email).options(joinedload(User.department)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ایمیل یا رمز عبور نادرست است.")

    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id), {"role": user.role.value})
    return TokenResponse(access_token=token, user=serialize_user(user))


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)
