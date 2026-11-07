
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.db import SessionLocal
from src.job_matching.job_model import Job


def validate_job_data(job_data):
    """Validate required job information before saving."""

    required_fields = ["title", "company", "description"]

    for field in required_fields:
        value = job_data.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing or invalid required field: {field}")

    salary_min = job_data.get("salary_min")
    salary_max = job_data.get("salary_max")

    if salary_min is not None and salary_min < 0:
        raise ValueError("Minimum salary cannot be negative.")

    if salary_max is not None and salary_max < 0:
        raise ValueError("Maximum salary cannot be negative.")

    if (
        salary_min is not None
        and salary_max is not None
        and salary_min > salary_max
    ):
        raise ValueError("Minimum salary cannot exceed maximum salary.")


def find_duplicate(db, job_data):
    """Find an existing job using its source ID or application URL."""

    source = job_data.get("source", "manual")
    source_job_id = job_data.get("source_job_id")
    apply_url = job_data.get("apply_url")

    if source_job_id:
        statement = select(Job).where(
            Job.source == source,
            Job.source_job_id == source_job_id,
        )
        return db.scalar(statement)

    if apply_url:
        statement = select(Job).where(
            Job.source == source,
            Job.apply_url == apply_url,
        )
        return db.scalar(statement)

    return None


def save_job(job_data):
    """Validate and save a job, avoiding duplicate records."""

    validate_job_data(job_data)

    with SessionLocal() as db:
        existing_job = find_duplicate(db, job_data)

        if existing_job:
            return existing_job, False

        new_job = Job(**job_data)

        try:
            db.add(new_job)
            db.commit()
            db.refresh(new_job)

            return new_job, True

        except IntegrityError:
            db.rollback()

            existing_job = find_duplicate(db, job_data)

            if existing_job:
                return existing_job, False

            raise


def get_all_jobs():
    """Retrieve all stored jobs."""

    with SessionLocal() as db:
        statement = select(Job).order_by(Job.created_at.desc())
        return list(db.scalars(statement).all())


def get_job_count():
    """Return the total number of stored jobs."""

    return len(get_all_jobs())
