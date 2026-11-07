
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.db import SessionLocal
from src.job_matching.job_model import Job
from src.tracking.application_model import Application
from src.tracking.application_history_model import ApplicationHistory


VALID_STATUSES = {
    "PREPARED",
    "READY_FOR_REVIEW",
    "SUBMITTED",
    "FAILED",
    "INTERVIEW",
    "REJECTED",
    "WITHDRAWN",
    "OFFER_RECEIVED",
}

ALLOWED_TRANSITIONS = {
    "PREPARED": {"READY_FOR_REVIEW", "FAILED", "WITHDRAWN"},
    "READY_FOR_REVIEW": {"SUBMITTED", "FAILED", "WITHDRAWN"},
    "SUBMITTED": {"INTERVIEW", "REJECTED", "WITHDRAWN", "OFFER_RECEIVED", "FAILED"},
    "FAILED": {"PREPARED", "READY_FOR_REVIEW"},
    "INTERVIEW": {"REJECTED", "WITHDRAWN", "OFFER_RECEIVED"},
    "REJECTED": set(),
    "WITHDRAWN": set(),
    "OFFER_RECEIVED": set(),
}


def create_application(
    job_id: int,
    candidate_name: str,
    status: str = "PREPARED",
):
    """Create an application record for an existing job."""

    normalized_status = status.strip().upper()

    if normalized_status not in VALID_STATUSES:
        raise ValueError(f"Invalid application status: {status}")

    if not candidate_name or not candidate_name.strip():
        raise ValueError("Candidate name is required.")

    with SessionLocal() as db:
        job = db.get(Job, job_id)

        if job is None:
            raise ValueError(f"Job with ID {job_id} does not exist.")

        existing = db.scalar(
            select(Application).where(Application.job_id == job_id)
        )

        if existing:
            return existing, False

        application = Application(
            job_id=job.id,
            candidate_name=candidate_name.strip(),
            job_title=job.title,
            company=job.company,
            application_url=job.apply_url,
            status=normalized_status,
        )

        try:
            db.add(application)
            db.flush()

            db.add(
                ApplicationHistory(
                    application_id=application.id,
                    old_status=None,
                    new_status=normalized_status,
                    event_type="APPLICATION_CREATED",
                    details="Application tracking record created.",
                )
            )

            db.commit()
            db.refresh(application)

            return application, True

        except IntegrityError:
            db.rollback()

            existing = db.scalar(
                select(Application).where(Application.job_id == job_id)
            )

            if existing:
                return existing, False

            raise


def update_application_status(
    application_id: int,
    new_status: str,
    details: Optional[str] = None,
):
    """Update application status and record its history."""

    normalized_status = new_status.strip().upper()

    if normalized_status not in VALID_STATUSES:
        raise ValueError(f"Invalid application status: {new_status}")

    with SessionLocal() as db:
        application = db.get(Application, application_id)

        if application is None:
            raise ValueError(
                f"Application with ID {application_id} does not exist."
            )

        old_status = application.status

        if normalized_status == old_status:
            return application

        allowed = ALLOWED_TRANSITIONS.get(old_status, set())

        if normalized_status not in allowed:
            raise ValueError(
                f"Status transition not allowed: "
                f"{old_status} -> {normalized_status}"
            )

        application.status = normalized_status

        if normalized_status == "SUBMITTED":
            application.applied_at = datetime.now()

        if normalized_status == "FAILED":
            application.retry_count += 1
            application.last_error = details

        elif normalized_status in {"PREPARED", "READY_FOR_REVIEW"}:
            application.last_error = None

        db.add(
            ApplicationHistory(
                application_id=application.id,
                old_status=old_status,
                new_status=normalized_status,
                event_type="STATUS_CHANGE",
                details=details,
            )
        )

        db.commit()
        db.refresh(application)

        return application


def record_application_failure(
    application_id: int,
    error_message: str,
):
    """Record an application failure through the status workflow."""

    if not error_message or not error_message.strip():
        raise ValueError("Failure reason is required.")

    return update_application_status(
        application_id=application_id,
        new_status="FAILED",
        details=error_message.strip(),
    )


def get_application(application_id: int):
    """Retrieve one application by ID."""

    with SessionLocal() as db:
        return db.get(Application, application_id)


def get_all_applications(status: Optional[str] = None):
    """Retrieve applications, optionally filtered by status."""

    with SessionLocal() as db:
        statement = select(Application).order_by(
            Application.created_at.desc()
        )

        if status:
            normalized_status = status.strip().upper()

            if normalized_status not in VALID_STATUSES:
                raise ValueError(f"Invalid application status: {status}")

            statement = statement.where(
                Application.status == normalized_status
            )

        return list(db.scalars(statement).all())


def get_application_history(application_id: int):
    """Retrieve chronological history for one application."""

    with SessionLocal() as db:
        application = db.get(Application, application_id)

        if application is None:
            raise ValueError(
                f"Application with ID {application_id} does not exist."
            )

        statement = (
            select(ApplicationHistory)
            .where(
                ApplicationHistory.application_id == application_id
            )
            .order_by(ApplicationHistory.changed_at.asc())
        )

        return list(db.scalars(statement).all())


def get_application_statistics():
    """Return application counts grouped by status."""

    with SessionLocal() as db:
        applications = db.scalars(select(Application)).all()

        statistics = {
            status: 0 for status in sorted(VALID_STATUSES)
        }

        for application in applications:
            statistics[application.status] = (
                statistics.get(application.status, 0) + 1
            )

        statistics["TOTAL"] = len(applications)

        return statistics
