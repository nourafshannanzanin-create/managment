from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import Department, User
from app.models.enums import UserRole


def seed_database(session: Session) -> None:
    departments = {
        "hq": Department(code="hq", name="ستاد مرکزی"),
        "it": Department(code="it", name="فناوری اطلاعات"),
        "finance": Department(code="finance", name="امور مالی"),
        "hr": Department(code="hr", name="منابع انسانی"),
        "ops": Department(code="ops", name="عملیات"),
        "marketing": Department(code="marketing", name="بازاریابی"),
        "procurement": Department(code="procurement", name="تدارکات"),
    }
    session.add_all(departments.values())
    session.flush()

    admin_user = User(
        slug="arman-karimi",
        full_name="آرمان کریمی",
        email="admin@karomand.local",
        phone=None,
        password_hash=get_password_hash("AdminSecret!"),
        role=UserRole.ADMIN,
        job_title="مدیر ارشد عملیات",
        avatar="AK",
        department_id=departments["hq"].id,
        bio="",
    )

    session.add(admin_user)
    session.commit()
