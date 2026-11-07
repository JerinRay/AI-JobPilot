
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Job(Base):
    """Database model representing a job listing."""

    __tablename__ = "jobs"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_job_id",
            name="uq_job_source_external_id",
        ),
        Index("idx_job_title", "title"),
        Index("idx_job_company", "company"),
        Index("idx_job_location", "location"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="manual",
    )

    source_job_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    work_mode: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    employment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    salary_min: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    salary_max: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    salary_currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    apply_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    posted_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return (
            f"<Job(id={self.id}, "
            f"title='{self.title}', "
            f"company='{self.company}')>"
        )
