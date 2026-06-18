from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ConfidentialityLevel, DocumentRisk, DocumentStatus


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    document_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus))
    risk: Mapped[DocumentRisk] = mapped_column(Enum(DocumentRisk))
    confidentiality: Mapped[ConfidentialityLevel] = mapped_column(Enum(ConfidentialityLevel))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    department = relationship("Department", back_populates="documents")
    owner = relationship("User", back_populates="documents")
