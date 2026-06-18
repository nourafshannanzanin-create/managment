from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models import User

router = APIRouter()


@router.get("")
def settings_overview(_: User = Depends(get_current_user)):
    return [
        {
            "title": "امنیت",
            "description": "احراز هویت JWT، مدیریت نشست، ثبت لاگ فعالیت و کنترل دسترسی مبتنی بر نقش.",
        },
        {
            "title": "برندینگ",
            "description": "رنگ سازمان، فونت، لوگو و هویت بصری پرتال سازمانی.",
        },
        {
            "title": "اعلان ها",
            "description": "اعلان درون برنامه ای، ایمیل و تنظیم اولویت پیام ها.",
        },
        {
            "title": "یکپارچه سازی",
            "description": "آماده اتصال به ERP، CRM، حسابداری و ذخیره سازی اسناد.",
        },
    ]
