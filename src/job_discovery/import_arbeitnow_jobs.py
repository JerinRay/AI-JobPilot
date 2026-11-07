
from datetime import datetime

from bs4 import BeautifulSoup

from src.job_discovery.arbeitnow_connector import ArbeitnowConnector
from database.job_repository import save_job


def clean_description(raw_description):
    """Convert HTML job descriptions into readable text."""

    if not raw_description:
        return ""

    return BeautifulSoup(
        raw_description,
        "html.parser"
    ).get_text(separator=" ", strip=True)


def parse_posted_date(value):
    """Convert an API date string into a Python datetime."""

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).replace(tzinfo=None)

    except (ValueError, TypeError, AttributeError):
        return None


def normalize_job(api_job):
    """Convert an Arbeitnow listing into our database format."""

    job_types = api_job.get("job_types") or []

    if isinstance(job_types, list):
        employment_type = ", ".join(
            str(item) for item in job_types
        ) or None
    else:
        employment_type = str(job_types) if job_types else None

    remote = api_job.get("remote")

    if remote is True:
        work_mode = "Remote"
    elif remote is False:
        work_mode = "On-site"
    else:
        work_mode = None

    return {
        "source": "arbeitnow",
        "source_job_id": api_job.get("slug"),
        "title": api_job.get("title"),
        "company": api_job.get("company_name"),
        "location": api_job.get("location"),
        "work_mode": work_mode,
        "employment_type": employment_type,
        "salary_min": None,
        "salary_max": None,
        "description": clean_description(
            api_job.get("description")
        ),
        "apply_url": api_job.get("url"),
        "posted_date": parse_posted_date(
            api_job.get("created_at")
        ),
    }


def import_jobs(page=1):
    """Fetch jobs from Arbeitnow and save them into SQLite."""

    connector = ArbeitnowConnector()

    print("=" * 60)
    print("AI-JOBPILOT - ARBEITNOW JOB IMPORT")
    print("=" * 60)

    api_jobs = connector.fetch_jobs(page=page)

    inserted = 0
    duplicates = 0
    skipped = 0

    print(f"\nJobs received from API: {len(api_jobs)}")

    for api_job in api_jobs:
        try:
            job_data = normalize_job(api_job)

            # Skip incomplete listings.
            if not job_data["source_job_id"]:
                skipped += 1
                continue

            saved_job, was_inserted = save_job(job_data)

            if was_inserted:
                inserted += 1
                print(
                    f"[SAVED] {saved_job.title} - "
                    f"{saved_job.company}"
                )
            else:
                duplicates += 1

        except (ValueError, TypeError, KeyError) as error:
            skipped += 1
            print(f"[SKIPPED] Invalid job: {error}")

    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print("API jobs received:", len(api_jobs))
    print("New jobs inserted:", inserted)
    print("Duplicates ignored:", duplicates)
    print("Jobs skipped:", skipped)

    print("\nTotal jobs currently in database:")

    from database.job_repository import get_job_count

    print(get_job_count())


if __name__ == "__main__":
    import_jobs(page=1)
