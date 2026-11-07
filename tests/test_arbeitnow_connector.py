
from src.job_discovery.arbeitnow_connector import ArbeitnowConnector


def run_test():
    print("=" * 55)
    print("ARBEITNOW JOB DISCOVERY CONNECTOR TEST")
    print("=" * 55)

    connector = ArbeitnowConnector()

    jobs = connector.fetch_jobs(page=1)

    print("\nAPI connection successful!")
    print("Jobs received:", len(jobs))

    if jobs:
        first_job = jobs[0]

        print("\nFIRST JOB PREVIEW")
        print("-" * 55)
        print("Title:", first_job.get("title"))
        print("Company:", first_job.get("company_name"))
        print("Location:", first_job.get("location"))
        print("Remote:", first_job.get("remote"))
        print("Job URL:", first_job.get("url"))
        print("Source ID:", first_job.get("slug"))

        assert first_job.get("title")
        assert first_job.get("company_name")
        assert first_job.get("url")
        assert first_job.get("slug")

        print("\nTEST PASSED: Job listing structure verified.")

    else:
        print("\nAPI returned no jobs on this page.")


if __name__ == "__main__":
    run_test()
