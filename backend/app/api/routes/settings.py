from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models import User

router = APIRouter()


@router.get("")
def settings_overview(_: User = Depends(get_current_user)):
    return [
        {"title": "امنیت", "description": ""},
        {"title": "برندینگ", "description": ""},
        {"title": "اعلان ها", "description": ""},
        {"title": "یکپارچه سازی", "description": ""},
    ]
