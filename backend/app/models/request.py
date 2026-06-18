from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RequestPriority, RequestStatus


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[RequestPriority] = mapped_column(Enum(RequestPriority))
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.SUBMITTED)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    department = relationship("Department", back_populates="requests")
    requester = relationship("User", foreign_keys=[requester_id], back_populates="created_requests")
    manager = relationship("User", foreign_keys=[manager_id], back_populates="managed_requests")
    attachments = relationship("RequestAttachment", back_populates="request", cascade="all, delete-orphan")
    timeline_items = relationship("RequestTimeline", back_populates="request", cascade="all, delete-orphan")


class RequestAttachment(Base):
    __tablename__ = "request_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    request = relationship("Request", back_populates="attachments")


class RequestTimeline(Base):
    __tablename__ = "request_timeline"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"))
    action: Mapped[str] = mapped_column(String(120))
    note: Mapped[str] = mapped_column(Text)
    actor_name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    request = relationship("Request", back_populates="timeline_items")
