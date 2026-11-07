
import json
from pathlib import Path

from database.db import SessionLocal
from src.job_matching.job_model import Job
from src.job_matching.job_description_analyzer import (
    analyze_job_description,
)
from src.profile_loader import load_candidate_profile


OUTPUT_FILE = Path("data/processed/job_analysis_results.json")


def analyze_all_jobs():
    print("=" * 60)
    print("AI-JOBPILOT - BULK JOB ANALYSIS")
    print("=" * 60)

    profile = load_candidate_profile()
    session = SessionLocal()

    results = []
    successful = 0
    failed = 0

    try:
        jobs = session.query(Job).all()

        print(f"\nTotal jobs found: {len(jobs)}")

        for index, job in enumerate(jobs, start=1):
            try:
                result = analyze_job_description(
                    job_description=job.description or "",
                    profile=profile,
                    job_title=job.title,
                    location=job.location,
                )

                results.append({
                    "job_id": job.id,
                    "source": job.source,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "apply_url": job.apply_url,
                    "analysis": result,
                })

                successful += 1

                print(
                    f"[{index}/{len(jobs)}] "
                    f"Analyzed: {job.title} - {job.company}"
                )

            except Exception as error:
                failed += 1
                print(
                    f"[{index}/{len(jobs)}] "
                    f"Failed: {job.title} | {error}"
                )

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        with OUTPUT_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                results,
                file,
                indent=4,
                ensure_ascii=False,
                default=str,
            )

        print("\n" + "=" * 60)
        print("BULK ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total jobs:      {len(jobs)}")
        print(f"Successful:      {successful}")
        print(f"Failed:          {failed}")
        print(f"Results saved:   {OUTPUT_FILE}")

    finally:
        session.close()


if __name__ == "__main__":
    analyze_all_jobs()
