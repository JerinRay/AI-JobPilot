
import json
from pathlib import Path

REQUIREMENTS_FILE = Path(
    "data/processed/job_requirement_analysis.json"
)

RESUME_FILE = Path(
    "data/processed/resume_information.json"
)

OUTPUT_FILE = Path(
    "data/processed/candidate_job_comparison.json"
)


# Normalize equivalent skill names
SKILL_ALIASES = {
    "llms": "large language models",
    "large language models": "large language models",
    "machine learning": "machine learning",
    "natural language processing": "nlp",
    "nlp": "nlp",
    "multi-agent": "multi-agent systems",
    "multi-agent systems": "multi-agent systems",
    "agentic ai": "agentic ai",
    "ai agents": "agentic ai",
    "tool-calling": "tool calling",
    "tool calling": "tool calling",
    "computer vision": "computer vision",
    "cv": "computer vision",
}


def normalize_skill(skill):
    """Normalize skill names to a consistent format."""
    skill = skill.lower().strip()
    return SKILL_ALIASES.get(skill, skill)


def load_json(path):
    """Load JSON data safely."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_candidate_skills(resume):
    """Extract candidate skills from resume JSON."""

    skills = resume.get("skills", [])

    # Handle dictionary-based skill structures
    if isinstance(skills, dict):
        flattened = []

        for value in skills.values():
            if isinstance(value, list):
                flattened.extend(value)
            elif isinstance(value, str):
                flattened.append(value)

        skills = flattened

    if not isinstance(skills, list):
        raise ValueError(
            "Resume skills must be a list or dictionary."
        )

    return {
        normalize_skill(skill)
        for skill in skills
        if isinstance(skill, str) and skill.strip()
    }


def compare_job(job, candidate_skills):
    """Compare job requirements against candidate skills."""

    mandatory = {
        normalize_skill(skill)
        for skill in job.get("mandatory_skills", [])
        if isinstance(skill, str)
    }

    preferred = {
        normalize_skill(skill)
        for skill in job.get("preferred_skills", [])
        if isinstance(skill, str)
    }

    matched_mandatory = mandatory & candidate_skills
    missing_mandatory = mandatory - candidate_skills

    matched_preferred = preferred & candidate_skills
    missing_preferred = preferred - candidate_skills

    # None means no skills were identified, not a 0% match.
    mandatory_score = (
        round(
            len(matched_mandatory) / len(mandatory) * 100,
            2
        )
        if mandatory else None
    )

    preferred_score = (
        round(
            len(matched_preferred) / len(preferred) * 100,
            2
        )
        if preferred else None
    )

    return {
        "mandatory_skill_match_percentage": mandatory_score,
        "preferred_skill_match_percentage": preferred_score,

        "mandatory_skill_count": len(mandatory),
        "preferred_skill_count": len(preferred),

        "matched_mandatory_skills": sorted(
            matched_mandatory
        ),

        "missing_mandatory_skills": sorted(
            missing_mandatory
        ),

        "matched_preferred_skills": sorted(
            matched_preferred
        ),

        "missing_preferred_skills": sorted(
            missing_preferred
        ),

        "production_experience_required": job.get(
            "production_experience_required",
            False
        ),

        "required_experience_years": job.get(
            "required_experience_years"
        ),

        "fresher_signals": job.get(
            "fresher_signals",
            []
        ),

        "experience_signals": job.get(
            "experience_signals",
            []
        ),

        "eligibility_classification": job.get(
            "eligibility_classification",
            "unclear_manual_verification"
        ),

        "manual_verification_required": job.get(
            "manual_verification_required",
            True
        ),
    }


def main():

    print("=" * 60)
    print("AI-JOBPILOT CANDIDATE REQUIREMENT COMPARATOR")
    print("=" * 60)

    requirements = load_json(REQUIREMENTS_FILE)
    resume = load_json(RESUME_FILE)

    candidate_skills = get_candidate_skills(resume)

    comparisons = []

    for job in requirements:

        comparison = compare_job(
            job,
            candidate_skills
        )

        record = {
            "job_id": job.get("job_id"),
            "job_title": job.get("job_title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "source": job.get("source"),
            "apply_url": job.get("apply_url"),
            **comparison
        }

        comparisons.append(record)

    # Save results
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            comparisons,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    # Summary
    print("\nCOMPARISON SUMMARY")
    print("-" * 60)

    print("Total jobs compared:", len(comparisons))
    print("Candidate skills detected:", len(candidate_skills))

    score_available = sum(
        job["mandatory_skill_match_percentage"] is not None
        for job in comparisons
    )

    print("Jobs with measurable mandatory skills:", score_available)

    print("\nFIRST FIVE RESULTS")
    print("-" * 60)

    for job in comparisons[:5]:

        print("\nJob:", job["job_title"])
        print("Company:", job["company"])
        print("Location:", job["location"])

        score = job["mandatory_skill_match_percentage"]

        if score is None:
            print("Mandatory match: N/A (No skills detected)")
        else:
            print(f"Mandatory match: {score}%")

        print(
            "Matched skills:",
            job["matched_mandatory_skills"]
        )

        print(
            "Missing skills:",
            job["missing_mandatory_skills"]
        )

        print(
            "Eligibility:",
            job["eligibility_classification"]
        )

        print(
            "Manual verification:",
            job["manual_verification_required"]
        )

    print("\n" + "=" * 60)
    print("COMPARISON COMPLETED SUCCESSFULLY")
    print("Output:", OUTPUT_FILE)
    print("=" * 60)


if __name__ == "__main__":
    main()
