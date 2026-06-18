from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models import Expense, User
from app.services.bootstrap_service import expense_category_label, expense_status_label, format_money

router = APIRouter()


@router.get("")
def list_expenses(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.scalars(
        select(Expense)
        .options(joinedload(Expense.owner), joinedload(Expense.department))
        .order_by(Expense.expense_date.desc())
    ).unique().all()
    return [
        {
            "id": item.code,
            "title": item.title,
            "amount": format_money(item.amount),
            "category": expense_category_label(item.category),
            "owner": item.owner.full_name if item.owner else "نامشخص",
            "status": expense_status_label(item.status),
            "progress": item.progress,
        }
        for item in items
    ]


@router.get("/summary")
def expense_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.scalars(select(Expense)).all()
    today_total = sum(Decimal(item.amount) for item in items if item.expense_date == date.today())
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_total = sum(Decimal(item.amount) for item in items if item.expense_date >= week_start)
    month_total = sum(Decimal(item.amount) for item in items if item.expense_date.month == date.today().month)
    year_total = sum(Decimal(item.amount) for item in items if item.expense_date.year == date.today().year)
    return [
        {"label": "امروز", "value": format_money(today_total)},
        {"label": "این هفته", "value": format_money(week_total)},
        {"label": "این ماه", "value": format_money(month_total)},
        {"label": "امسال", "value": format_money(year_total)},
    ]
