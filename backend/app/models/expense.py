from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ExpenseCategory, ExpenseStatus


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(180))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    category: Mapped[ExpenseCategory] = mapped_column(Enum(ExpenseCategory))
    status: Mapped[ExpenseStatus] = mapped_column(Enum(ExpenseStatus))
    progress: Mapped[int] = mapped_column(default=0)
    expense_date: Mapped[date] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    invoice_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    department = relationship("Department", back_populates="expenses")
    owner = relationship("User", back_populates="expenses")
