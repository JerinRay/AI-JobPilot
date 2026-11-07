
import json
from pathlib import Path

COMPARISON_FILE = Path(
    "data/processed/candidate_job_comparison.json"
)

OUTPUT_FILE = Path(
    "data/processed/intelligent_job_rankings.json"
)

# Target job roles
TARGET_ROLES = {
    "ai_engineer": [
        "ai engineer",
        "artificial intelligence engineer",
        "applied ai engineer",
        "generative ai engineer"
    ],
    "ml_engineer": [
        "machine learning engineer",
        "ml engineer",
        "deep learning engineer"
    ],
    "data_scientist": [
        "data scientist",
        "junior data scientist"
    ],
    "data_analyst": [
        "data analyst",
        "business data analyst",
        "market data analyst"
    ],
    "data_engineer": [
        "data engineer"
    ],
    "nlp_cv": [
        "nlp engineer",
        "computer vision engineer",
        "computer vision researcher"
    ],
    "ai_research": [
        "ai researcher",
        "machine learning researcher",
        "research scientist"
    ]
}

SENIOR_KEYWORDS = [
    "senior",
    "principal",
    "lead",
    "staff",
    "director",
    "head of",
    "manager"
]

JUNIOR_KEYWORDS = [
    "junior",
    "entry level",
    "entry-level",
    "graduate",
    "fresher",
    "intern",
    "internship",
    "trainee",
    "associate"
]

INDIA_LOCATIONS = [
    "india",
    "bengaluru",
    "bangalore",
    "chennai",
    "hyderabad",
    "mumbai",
    "pune",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "kochi",
    "trivandrum",
    "thiruvananthapuram",
    "coimbatore",
    "kolkata",
    "ahmedabad"
]

EXPERIENCED_CLASSIFICATIONS = {
    "experienced_required",
    "likely_experienced_role",
    "likely_not_fresher_friendly"
}


def load_jobs():
    if not COMPARISON_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {COMPARISON_FILE}"
        )

    with COMPARISON_FILE.open(
        "r", encoding="utf-8"
    ) as file:
        return json.load(file)


def get_role_category(title):
    title = (title or "").lower()

    for category, keywords in TARGET_ROLES.items():
        if any(keyword in title for keyword in keywords):
            return category

    return None


def is_senior_role(title):
    title = (title or "").lower()

    return any(
        keyword in title
        for keyword in SENIOR_KEYWORDS
    )


def is_india_location(location):
    location = (location or "").lower()

    return any(
        place in location
        for place in INDIA_LOCATIONS
    )


def calculate_role_score(category):
    if category is None:
        return 0

    return 30


def calculate_location_score(location):
    if is_india_location(location):
        return 25

    return 0


def calculate_fresher_score(job):
    title = (job.get("job_title") or "").lower()

    fresher_signals = job.get("fresher_signals", [])

    if any(
        keyword in title
        for keyword in JUNIOR_KEYWORDS
    ):
        return 20, "Fresher-friendly title signal"

    if fresher_signals:
        return 20, "Fresher signal detected in description"

    eligibility = job.get(
        "eligibility_classification",
        "unclear_manual_verification"
    )

    if eligibility == "unclear_manual_verification":
        return 8, "Experience eligibility needs manual review"

    return 0, "No fresher eligibility evidence"


def calculate_skill_score(job):
    match = job.get(
        "mandatory_skill_match_percentage"
    )

    if match is None:
        return 0, "Mandatory skill score unavailable"

    return round(match * 0.25, 2), "Mandatory skill match available"


def rank_job(job):
    title = job.get("job_title", "")
    location = job.get("location", "")

    category = get_role_category(title)

    eligibility = job.get(
        "eligibility_classification",
        "unclear_manual_verification"
    )

    reasons = []

    # Exclude unrelated roles
    if category is None:
        return None, "Not a target AI/Data role"

    # Exclude senior titles
    if is_senior_role(title):
        return None, "Senior-level title"

    # Exclude roles explicitly classified as experienced
    if eligibility in EXPERIENCED_CLASSIFICATIONS:
        return None, "Not suitable for fresher shortlist"

    role_score = calculate_role_score(category)
    location_score = calculate_location_score(location)

    fresher_score, fresher_reason = calculate_fresher_score(job)

    skill_score, skill_reason = calculate_skill_score(job)

    total_score = round(
        role_score
        + location_score
        + fresher_score
        + skill_score,
        2
    )

    reasons.append("Relevant role: " + category)
    reasons.append(fresher_reason)
    reasons.append(skill_reason)

    if location_score:
        reasons.append("India location preference matched")
    else:
        reasons.append("Outside India or India location not confirmed")

    if job.get("manual_verification_required", True):
        reasons.append("Manual eligibility verification required")

    result = {
        "job_id": job.get("job_id"),
        "job_title": title,
        "company": job.get("company"),
        "location": location,
        "source": job.get("source"),
        "apply_url": job.get("apply_url"),
        "role_category": category,
        "eligibility": eligibility,
        "mandatory_skill_match_percentage": job.get(
            "mandatory_skill_match_percentage"
        ),
        "role_score": role_score,
        "location_score": location_score,
        "fresher_score": fresher_score,
        "skill_score": skill_score,
        "total_suitability_score": total_score,
        "manual_verification_required": job.get(
            "manual_verification_required", True
        ),
        "reasons": reasons
    }

    return result, None


def main():
    print("=" * 65)
    print("AI-JOBPILOT INTELLIGENT JOB RANKING ENGINE")
    print("=" * 65)

    jobs = load_jobs()

    shortlisted = []
    excluded = []

    for job in jobs:
        result, exclusion_reason = rank_job(job)

        if result is not None:
            shortlisted.append(result)
        else:
            excluded.append({
                "job_title": job.get("job_title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "reason": exclusion_reason
            })

    # India jobs first, then score
    shortlisted.sort(
        key=lambda job: (
            job["location_score"] > 0,
            job["total_suitability_score"]
        ),
        reverse=True
    )

    for index, job in enumerate(shortlisted, start=1):
        job["rank"] = index

    india_jobs = [
        job for job in shortlisted
        if job["location_score"] > 0
    ]

    review_jobs = [
        job for job in shortlisted
        if job["manual_verification_required"]
    ]

    output = {
        "summary": {
            "total_jobs_analyzed": len(jobs),
            "shortlisted_jobs": len(shortlisted),
            "india_based_jobs": len(india_jobs),
            "manual_review_jobs": len(review_jobs),
            "excluded_jobs": len(excluded)
        },
        "rankings": shortlisted,
        "excluded_jobs": excluded
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("\nRANKING SUMMARY")
    print("-" * 65)

    for key, value in output["summary"].items():
        print(key.replace("_", " ").title() + ":", value)

    print("\nTOP 15 SHORTLISTED JOBS")
    print("-" * 65)

    for job in shortlisted[:15]:
        print(f"\nRank: {job['rank']}")
        print("Role:", job["job_title"])
        print("Company:", job["company"])
        print("Location:", job["location"])
        print("Category:", job["role_category"])
        print("Skill match:", job["mandatory_skill_match_percentage"])
        print("Eligibility:", job["eligibility"])
        print("Suitability score:", job["total_suitability_score"])
        print("Reasons:", "; ".join(job["reasons"]))

    print("\nSaved:", OUTPUT_FILE)
    print("=" * 65)


if __name__ == "__main__":
    main()
