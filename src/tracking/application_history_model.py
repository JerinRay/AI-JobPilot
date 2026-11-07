
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.job_matching.job_model import Base


class ApplicationHistory(Base):
    """Records every status change for an application."""

    __tablename__ = "application_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id"),
        nullable=False,
        index=True,
    )

    old_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    new_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="STATUS_CHANGE",
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
