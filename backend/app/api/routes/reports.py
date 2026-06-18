from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models import User

router = APIRouter()


@router.get("")
def list_reports(_: User = Depends(get_current_user)):
    return [
        {
            "title": "گزارش درخواست ها",
            "description": "تحلیل بر اساس کاربر، مدیر، واحد و بازه زمانی",
            "export": "PDF / Excel / CSV",
        },
        {
            "title": "گزارش هزینه ها",
            "description": "ماهانه، فصلی، سالانه و تفکیک دسته بندی",
            "export": "Excel / CSV",
        },
        {
            "title": "گزارش اسناد",
            "description": "در انتظار، تایید شده، رد شده و آرشیو",
            "export": "PDF / Excel",
        },
    ]
