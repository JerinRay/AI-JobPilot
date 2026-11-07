
from database.job_repository import (
    save_job,
    get_all_jobs,
    get_job_count,
)


def run_tests():
    print("=" * 55)
    print("AI-JOBPILOT DATABASE TESTING")
    print("=" * 55)

    # Sample job
    sample_job = {
        "source": "test_portal",
        "source_job_id": "AIJOB-001",
        "title": "Junior AI Engineer",
        "company": "Tech Solutions India",
        "location": "Bangalore, India",
        "work_mode": "Office",
        "employment_type": "Full-time",
        "salary_min": 300000,
        "salary_max": 500000,
        "salary_currency": "INR",
        "description": (
            "Looking for a Junior AI Engineer with Python, "
            "Machine Learning, PyTorch and SQL knowledge."
        ),
        "apply_url": "https://example.com/jobs/AIJOB-001",
    }

    # Test 1: Save a new job
    job, created = save_job(sample_job)

    assert created is True
    print("\nTEST 1 PASSED: New job saved successfully.")
    print("Job ID:", job.id)
    print("Job Title:", job.title)

    # Test 2: Attempt to save the same job again
    duplicate_job, created_again = save_job(sample_job)

    assert created_again is False
    assert duplicate_job.id == job.id

    print("\nTEST 2 PASSED: Duplicate job detected.")
    print("Existing Job ID:", duplicate_job.id)

    # Test 3: Retrieve all jobs
    jobs = get_all_jobs()

    assert len(jobs) >= 1

    print("\nTEST 3 PASSED: Jobs retrieved successfully.")
    print("Total jobs:", len(jobs))

    # Test 4: Check job count
    count = get_job_count()

    assert count >= 1

    print("\nTEST 4 PASSED: Job count verified.")
    print("Database job count:", count)

    print("\n" + "=" * 55)
    print("ALL DATABASE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 55)


if __name__ == "__main__":
    run_tests()
