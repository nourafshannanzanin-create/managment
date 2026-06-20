from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models import User

router = APIRouter()


@router.get("")
def list_reports(_: User = Depends(get_current_user)):
    return [
        {"title": "گزارش درخواست ها", "description": "", "export": "PDF / Excel / CSV"},
        {"title": "گزارش هزینه ها", "description": "", "export": "Excel / CSV"},
        {"title": "گزارش اسناد", "description": "", "export": "PDF / Excel"},
    ]
