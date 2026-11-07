
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.job_matching.job_model import Base


class Application(Base):
    """Tracks a candidate's application to a specific job."""

    __tablename__ = "applications"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            name="uq_application_job",
        ),
        Index("idx_application_status", "status"),
        Index("idx_application_company", "company"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    candidate_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    job_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    application_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PREPARED",
    )

    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self):
        return (
            f"<Application(id={self.id}, "
            f"job_id={self.job_id}, "
            f"company='{self.company}', "
            f"status='{self.status}')>"
        )
