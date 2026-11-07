
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

COMPARISON_FILE = PROCESSED_DIR / "candidate_job_comparison.json"
RANKING_FILE = PROCESSED_DIR / "intelligent_job_rankings.json"
REQUIREMENTS_FILE = PROCESSED_DIR / "job_requirement_analysis.json"

OUTPUT_FILE = PROCESSED_DIR / "job_recommendations.json"

INDIA_MARKERS = [
    "india", "tamil nadu", "chennai", "bangalore", "bengaluru",
    "hyderabad", "mumbai", "pune", "delhi", "gurgaon",
    "gurugram", "noida", "kochi", "trivandrum", "nagercoil"
]

REMOTE_MARKERS = ["remote", "work from home", "wfh"]

FRESHER_MARKERS = [
    "fresher", "graduate", "entry level", "entry-level",
    "junior", "intern", "internship", "trainee",
    "no experience", "0-1 years", "0 years"
]

EXPERIENCED_MARKERS = [
    "senior", "principal", "staff engineer", "lead",
    "director", "head of", "manager"
]


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(value):
    value = str(value or "").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def classify_location(location):
    """
    Conservative location classification.
    Generic remote jobs are NOT assumed to be India-remote.
    """
    normalized = normalize_text(location)

    if not normalized:
        return "location_unclear"

    if any(marker in normalized for marker in INDIA_MARKERS):
        if any(marker in normalized for marker in REMOTE_MARKERS):
            return "india_remote"
        return "india"

    if any(marker in normalized for marker in REMOTE_MARKERS):
        return "remote_location_unverified"

    return "overseas"


def classify_fresher_eligibility(job):
    title = normalize_text(job.get("job_title"))
    classification = normalize_text(
        job.get("eligibility_classification")
        or job.get("eligibility")
    )

    signals = [
        normalize_text(signal)
        for signal in job.get("fresher_signals", [])
    ]

    experience_signals = [
        normalize_text(signal)
        for signal in job.get("experience_signals", [])
    ]

    if any(marker in title for marker in EXPERIENCED_MARKERS):
        return "likely_experienced"

    if classification in {
        "likely_experienced_role",
        "likely_not_fresher_friendly"
    }:
        return "likely_experienced"

    if job.get("production_experience_required"):
        return "manual_review"

    if job.get("required_experience_years") is not None:
        try:
            years = float(job["required_experience_years"])
            if years > 1:
                return "likely_experienced"
            if years <= 1:
                return "potentially_fresher"
        except (TypeError, ValueError):
            pass

    if signals or any(marker in title for marker in FRESHER_MARKERS):
        return "potentially_fresher"

    if experience_signals:
        return "manual_review"

    return "manual_review"


def make_job_identity(job):
    """
    Exact identity uses source + source job ID where available.
    Fallback uses application URL.
    """
    source = normalize_text(job.get("source"))
    job_id = job.get("job_id")

    if job_id is not None:
        return f"{source}:{job_id}"

    apply_url = str(job.get("apply_url") or "").strip().rstrip("/")
    if apply_url:
        return apply_url.lower()

    return "|".join([
        normalize_text(job.get("company")),
        normalize_text(job.get("job_title")),
        normalize_text(job.get("location"))
    ])


def build_role_groups(jobs):
    """
    Group same company and role while preserving location variants.
    This does not delete different-location opportunities.
    """
    groups = defaultdict(list)

    for job in jobs:
        key = (
            normalize_text(job.get("company")),
            normalize_text(job.get("job_title"))
        )
        groups[key].append(job)

    result = []

    for (company, title), variants in groups.items():
        if len(variants) > 1:
            result.append({
                "company": variants[0].get("company"),
                "job_title": variants[0].get("job_title"),
                "variant_count": len(variants),
                "locations": sorted({
                    job.get("location") or "Unknown"
                    for job in variants
                }),
                "job_ids": [job.get("job_id") for job in variants]
            })

    return result


def build_skill_recommendations(shortlisted_jobs):
    """
    Aggregate missing mandatory skills from shortlisted jobs.
    Frequency is a prioritization signal, not a guarantee of job demand.
    """
    skill_frequency = Counter()
    skill_examples = defaultdict(list)

    for job in shortlisted_jobs:
        missing_skills = job.get("missing_mandatory_skills") or []

        for skill in missing_skills:
            clean_skill = str(skill).strip()
            if not clean_skill:
                continue

            skill_frequency[clean_skill.lower()] += 1

            if len(skill_examples[clean_skill.lower()]) < 3:
                skill_examples[clean_skill.lower()].append(
                    job.get("job_title", "Unknown role")
                )

    recommendations = []

    for skill, count in skill_frequency.most_common():
        recommendations.append({
            "skill": skill,
            "shortlisted_jobs_missing_this_skill": count,
            "priority": (
                "high" if count >= 3
                else "medium" if count == 2
                else "explore"
            ),
            "example_roles": skill_examples[skill]
        })

    return recommendations


def build_recommendations():
    comparisons = load_json(COMPARISON_FILE)
    rankings_data = load_json(RANKING_FILE)
    requirement_data = load_json(REQUIREMENTS_FILE)

    rankings = rankings_data.get("rankings", [])

    if not isinstance(comparisons, list):
        raise ValueError("Candidate comparison data must be a list.")

    if not isinstance(requirement_data, list):
        raise ValueError("Requirement analysis data must be a list.")

    ranking_ids = {
        str(job.get("job_id"))
        for job in rankings
        if job.get("job_id") is not None
    }

    comparison_by_id = {
        str(job.get("job_id")): job
        for job in comparisons
        if job.get("job_id") is not None
    }

    requirement_by_id = {
        str(job.get("job_id")): job
        for job in requirement_data
        if job.get("job_id") is not None
    }

    # Merge ranking, comparison, and requirement information.
    shortlisted = []

    for ranked_job in rankings:
        job_id = str(ranked_job.get("job_id"))

        comparison = comparison_by_id.get(job_id, {})
        requirements = requirement_by_id.get(job_id, {})

        merged = {
            **requirements,
            **comparison,
            **ranked_job
        }

        # Keep the detailed skill and eligibility information.
        merged["missing_mandatory_skills"] = (
            comparison.get("missing_mandatory_skills")
            or []
        )
        merged["matched_mandatory_skills"] = (
            comparison.get("matched_mandatory_skills")
            or []
        )
        merged["fresher_signals"] = (
            comparison.get("fresher_signals")
            or requirements.get("fresher_signals")
            or []
        )
        merged["experience_signals"] = (
            comparison.get("experience_signals")
            or requirements.get("experience_signals")
            or []
        )
        merged["required_experience_years"] = (
            comparison.get("required_experience_years")
        )
        merged["production_experience_required"] = (
            comparison.get("production_experience_required", False)
        )
        merged["eligibility_classification"] = (
            comparison.get("eligibility_classification")
            or requirements.get("eligibility_classification")
        )

        shortlisted.append(merged)

    # Exact duplicate detection.
    unique_jobs = []
    seen_identities = set()
    duplicate_count = 0

    for job in comparisons:
        identity = make_job_identity(job)

        if identity in seen_identities:
            duplicate_count += 1
            continue

        seen_identities.add(identity)
        unique_jobs.append(job)

    # Location and eligibility classification for shortlist.
    location_counts = Counter()
    eligibility_counts = Counter()
    final_jobs = []

    for job in shortlisted:
        location_category = classify_location(job.get("location"))
        fresher_category = classify_fresher_eligibility(job)

        location_counts[location_category] += 1
        eligibility_counts[fresher_category] += 1

        reasons = list(job.get("reasons") or [])

        if location_category == "india":
            reasons.append("Job location is in India")
        elif location_category == "india_remote":
            reasons.append("India-based remote opportunity")
        elif location_category == "overseas":
            reasons.append("Job is located outside India")
        elif location_category == "remote_location_unverified":
            reasons.append(
                "Remote opportunity, but India eligibility is unverified"
            )
        else:
            reasons.append("Job location needs verification")

        if fresher_category == "potentially_fresher":
            reasons.append("Potentially suitable for a fresher")
        elif fresher_category == "likely_experienced":
            reasons.append("Experience requirements may not suit a fresher")
        else:
            reasons.append("Experience eligibility needs manual review")

        final_jobs.append({
            "job_id": job.get("job_id"),
            "job_title": job.get("job_title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "location_category": location_category,
            "fresher_eligibility": fresher_category,
            "source": job.get("source"),
            "apply_url": job.get("apply_url"),
            "rank": job.get("rank"),
            "suitability_score": job.get("total_suitability_score"),
            "mandatory_skill_match_percentage": (
                job.get("mandatory_skill_match_percentage")
            ),
            "matched_mandatory_skills": (
                job.get("matched_mandatory_skills") or []
            ),
            "missing_mandatory_skills": (
                job.get("missing_mandatory_skills") or []
            ),
            "manual_verification_required": (
                job.get("manual_verification_required", True)
                or fresher_category == "manual_review"
                or location_category in {
                    "location_unclear",
                    "remote_location_unverified"
                }
            ),
            "recommendation_reasons": reasons
        })

    # Same company and role variants are reported, not discarded.
    role_groups = build_role_groups(unique_jobs)

    skill_recommendations = build_skill_recommendations(shortlisted)

    india_jobs = [
        job for job in final_jobs
        if job["location_category"] in {"india", "india_remote"}
    ]

    potentially_fresher_jobs = [
        job for job in final_jobs
        if job["fresher_eligibility"] == "potentially_fresher"
    ]

    manual_review_jobs = [
        job for job in final_jobs
        if job["manual_verification_required"]
    ]

    output = {
        "project": "AI-JobPilot",
        "module": "Day 7 Job Shortlist and Recommendation Engine",
        "summary": {
            "comparison_records": len(comparisons),
            "unique_jobs_after_exact_deduplication": len(unique_jobs),
            "exact_duplicates_removed": duplicate_count,
            "ranked_jobs_received": len(rankings),
            "final_recommendations": len(final_jobs),
            "india_or_india_remote_jobs": len(india_jobs),
            "potentially_fresher_friendly_jobs": len(
                potentially_fresher_jobs
            ),
            "manual_review_jobs": len(manual_review_jobs),
            "same_company_role_groups": len(role_groups)
        },
        "location_distribution": dict(location_counts),
        "eligibility_distribution": dict(eligibility_counts),
        "skill_recommendations": skill_recommendations,
        "same_company_role_variants": role_groups,
        "recommendations": final_jobs
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    print("=" * 65)
    print("AI-JOBPILOT — DAY 7 RECOMMENDATION ENGINE")
    print("=" * 65)
    print("Comparison records:", len(comparisons))
    print("Unique jobs:", len(unique_jobs))
    print("Exact duplicates removed:", duplicate_count)
    print("Ranked jobs:", len(rankings))
    print("Final recommendations:", len(final_jobs))
    print("India / India-remote jobs:", len(india_jobs))
    print("Potentially fresher-friendly:", len(potentially_fresher_jobs))
    print("Manual review required:", len(manual_review_jobs))

    print("\nLOCATION DISTRIBUTION:")
    for category, count in location_counts.items():
        print(f"{category}: {count}")

    print("\nELIGIBILITY DISTRIBUTION:")
    for category, count in eligibility_counts.items():
        print(f"{category}: {count}")

    print("\nSKILL RECOMMENDATIONS:")
    if skill_recommendations:
        for item in skill_recommendations:
            print(
                f"{item['skill']}: "
                f"{item['shortlisted_jobs_missing_this_skill']} jobs "
                f"({item['priority']} priority)"
            )
    else:
        print("No missing mandatory skills detected in shortlisted jobs.")

    print("\nOUTPUT FILE:")
    print(OUTPUT_FILE)

    print("\nDAY 7 RECOMMENDATION ENGINE COMPLETED")


if __name__ == "__main__":
    build_recommendations()
