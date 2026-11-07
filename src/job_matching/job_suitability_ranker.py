
import json
from pathlib import Path

INPUT_FILE = Path("data/processed/job_analysis_results.json")
OUTPUT_FILE = Path("data/processed/job_suitability_rankings.json")

TARGET_ROLES = [
    "ai engineer",
    "machine learning engineer",
    "ml engineer",
    "data scientist",
    "data analyst",
    "market data analyst",
    "nlp engineer",
    "computer vision engineer",
    "deep learning engineer",
]

JUNIOR_KEYWORDS = [
    "junior",
    "entry level",
    "entry-level",
    "graduate",
    "fresher",
    "associate",
    "intern",
    "trainee",
]

SENIOR_KEYWORDS = [
    "senior",
    "principal",
    "lead",
    "staff",
    "director",
    "head of",
    "manager",
]

INDIA_LOCATIONS = [
    "india", "bengaluru", "bangalore", "chennai",
    "hyderabad", "pune", "mumbai", "delhi",
    "noida", "gurgaon", "gurugram", "kolkata",
    "coimbatore", "kochi", "trivandrum",
]


def calculate_suitability(job):
    title = (job.get("title") or "").lower()
    location = (job.get("location") or "").lower()
    source = (job.get("source") or "").lower()

    analysis = job.get("analysis", {})

    if source == "test_portal":
        return None

    # Check role relevance
    if not any(role in title for role in TARGET_ROLES):
        return None

    # Exclude clearly senior positions from fresher shortlist
    if any(word in title for word in SENIOR_KEYWORDS):
        return None

    score = 30
    reasons = ["Relevant AI/Data role"]

    # Location score
    is_india = any(place in location for place in INDIA_LOCATIONS)

    if is_india:
        score += 25
        reasons.append("India-based opportunity")
    else:
        reasons.append("Outside India - location preference mismatch")

    # Experience suitability
    is_junior = any(word in title for word in JUNIOR_KEYWORDS)
    experience_level = (
        analysis.get("experience_level") or ""
    ).lower()

    if is_junior:
        score += 20
        reasons.append("Junior / entry-level title")
    elif experience_level in ["fresher", "entry level", "junior"]:
        score += 20
        reasons.append("Fresher-friendly experience classification")
    else:
        reasons.append(
            "Experience eligibility unclear - verify job description"
        )

    # Skill match
    skill_match = float(
        analysis.get("match_percentage", 0) or 0
    )

    skill_points = max(0, min(25, skill_match * 0.25))
    score += skill_points

    reasons.append(f"Skill match: {skill_match}%")

    return {
        "job_id": job.get("job_id"),
        "title": job.get("title"),
        "company": job.get("company"),
        "location": job.get("location"),
        "apply_url": job.get("apply_url"),
        "is_india_based": is_india,
        "experience_status": (
            "Junior title"
            if is_junior
            else "Needs manual verification"
        ),
        "suitability_score": round(score, 2),
        "skill_match_percentage": skill_match,
        "reasons": reasons,
    }


def rank_jobs():
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        jobs = json.load(file)

    rankings = []

    for job in jobs:
        result = calculate_suitability(job)

        if result is not None:
            rankings.append(result)

    rankings.sort(
        key=lambda item: (
            item["is_india_based"],
            item["suitability_score"],
        ),
        reverse=True,
    )

    for rank, job in enumerate(rankings, start=1):
        job["rank"] = rank

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            rankings,
            file,
            indent=4,
            ensure_ascii=False,
        )

    india_jobs = [
        job for job in rankings if job["is_india_based"]
    ]

    print("=" * 55)
    print("AI-JOBPILOT - CORRECTED JOB RANKING")
    print("=" * 55)

    print(f"Total analyzed jobs: {len(jobs)}")
    print(f"Fresher shortlist candidates: {len(rankings)}")
    print(f"India-based candidates: {len(india_jobs)}")
    print(f"Other locations: {len(rankings) - len(india_jobs)}")
    print(f"Saved to: {OUTPUT_FILE}")

    print("\nTOP RECOMMENDATIONS")
    print("-" * 55)

    for job in rankings[:10]:
        print(f"\nRank: {job['rank']}")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Score: {job['suitability_score']}/100")
        print(f"Experience: {job['experience_status']}")
        print(f"Reasons: {', '.join(job['reasons'])}")


if __name__ == "__main__":
    rank_jobs()
