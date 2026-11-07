
import json
import re
from pathlib import Path

from database.db import SessionLocal
from src.job_matching.job_model import Job


OUTPUT_FILE = Path("data/processed/job_requirement_analysis.json")

SKILL_TERMS = [
    "python", "sql", "java", "javascript", "typescript", "node.js",
    "machine learning", "deep learning", "artificial intelligence",
    "pytorch", "tensorflow", "scikit-learn", "xgboost",
    "natural language processing", "nlp", "computer vision",
    "opencv", "yolo", "large language models", "llm", "llms",
    "generative ai", "agentic ai", "ai agents", "multi-agent",
    "orchestration", "tool-calling", "prompt engineering",
    "fastapi", "flask", "docker", "kubernetes", "aws",
    "azure", "gcp", "data analysis", "data visualization",
    "pandas", "numpy", "statistics", "power bi", "tableau",
    "evaluation frameworks", "observability", "structured outputs",
    "context management", "memory management"
]

PREFERRED_MARKERS = [
    "nice to have",
    "preferred",
    "preferably",
    "bonus",
    "a plus",
    "desirable",
    "would be an advantage",
    "ideally",
    "good to have"
]

FRESHER_MARKERS = [
    "fresh graduate",
    "recent graduate",
    "graduates welcome",
    "entry level",
    "entry-level",
    "junior position",
    "no experience required",
    "no prior experience",
    "0 years of experience",
    "zero years of experience",
    "training provided"
]

EXPERIENCE_MARKERS = [
    "production experience",
    "production-ready",
    "production deployment",
    "hands-on experience",
    "proven experience",
    "independently delivering",
    "advanced practical experience",
    "significant experience",
    "years of experience",
    "strong professional experience",
    "technical ownership",
    "high level of autonomy"
]

SENIORITY_MARKERS = [
    "senior", "principal", "lead", "staff",
    "director", "head of", "manager"
]


def normalize_text(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def find_skills(text):
    text = normalize_text(text)
    found = []

    for skill in SKILL_TERMS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"

        if re.search(pattern, text):
            found.append(skill)

    return sorted(set(found))


def extract_years_experience(text):
    text = normalize_text(text)

    patterns = [
        r"(\d+)\s*\+?\s*years?\s+of\s+experience",
        r"minimum\s+of\s+(\d+)\s+years?",
        r"at\s+least\s+(\d+)\s+years?"
    ]

    values = []

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            values.append(int(match.group(1)))

    return max(values) if values else None


def extract_preferred_skills(text, skills):
    text = normalize_text(text)
    preferred = []

    for skill in skills:
        positions = [
            match.start()
            for match in re.finditer(re.escape(skill), text)
        ]

        for position in positions:
            context = text[max(0, position - 100):position + 150]

            if any(marker in context for marker in PREFERRED_MARKERS):
                preferred.append(skill)
                break

    return sorted(set(preferred))


def extract_requirement_section(text):
    text = normalize_text(text)

    start_markers = [
        "requirements",
        "qualifications",
        "what we're looking for",
        "what you bring",
        "your profile"
    ]

    end_markers = [
        "benefits",
        "what we offer",
        "perks",
        "about us",
        "how to apply"
    ]

    start = -1

    for marker in start_markers:
        position = text.find(marker)

        if position != -1 and (start == -1 or position < start):
            start = position

    if start == -1:
        return ""

    end_positions = [
        text.find(marker, start + 1)
        for marker in end_markers
        if text.find(marker, start + 1) != -1
    ]

    end = min(end_positions) if end_positions else len(text)

    return text[start:end]


def analyze_requirements(description, title="", location=""):
    text = normalize_text(description)
    title_text = normalize_text(title)

    all_skills = find_skills(text)
    requirement_section = extract_requirement_section(text)

    requirement_skills = find_skills(requirement_section)

    preferred_skills = extract_preferred_skills(text, all_skills)

    mandatory_skills = [
        skill for skill in requirement_skills
        if skill not in preferred_skills
    ]

    other_skills = [
        skill for skill in all_skills
        if skill not in mandatory_skills
        and skill not in preferred_skills
    ]

    years = extract_years_experience(text)

    fresher_signals = [
        marker for marker in FRESHER_MARKERS
        if marker in text
    ]

    experience_signals = [
        marker for marker in EXPERIENCE_MARKERS
        if marker in text
    ]

    seniority_signals = [
        marker for marker in SENIORITY_MARKERS
        if marker in title_text
    ]

    if years is not None and years >= 2:
        eligibility = "experienced_required"
    elif seniority_signals:
        eligibility = "likely_not_fresher_friendly"
    elif years == 0 or fresher_signals:
        eligibility = "fresher_friendly_signal"
    elif len(experience_signals) >= 3:
        eligibility = "likely_experienced_role"
    else:
        eligibility = "unclear_manual_verification"

    production_required = any(
        marker in text
        for marker in [
            "production experience",
            "production-ready",
            "production deployment",
            "operated in production environments"
        ]
    )

    return {
        "job_title": title,
        "location": location,
        "mandatory_skills": mandatory_skills,
        "preferred_skills": preferred_skills,
        "other_detected_skills": other_skills,
        "required_experience_years": years,
        "fresher_signals": fresher_signals,
        "experience_signals": experience_signals,
        "seniority_signals": seniority_signals,
        "production_experience_required": production_required,
        "eligibility_classification": eligibility,
        "manual_verification_required": (
            eligibility == "unclear_manual_verification"
            or production_required
        )
    }


def main():
    session = SessionLocal()

    results = []
    failed = 0

    try:
        jobs = session.query(Job).filter(
            Job.source != "test_portal"
        ).all()

        print("=" * 60)
        print("AI-JOBPILOT - REQUIREMENT ANALYSIS")
        print("=" * 60)
        print("Jobs found:", len(jobs))

        for index, job in enumerate(jobs, start=1):
            try:
                result = analyze_requirements(
                    description=job.description or "",
                    title=job.title or "",
                    location=job.location or ""
                )

                result.update({
                    "job_id": job.id,
                    "company": job.company,
                    "source": job.source,
                    "apply_url": job.apply_url
                })

                results.append(result)

                print(
                    f"[{index}/{len(jobs)}] "
                    f"{job.title}: "
                    f"{result['eligibility_classification']}"
                )

            except Exception as error:
                failed += 1
                print(f"Failed job {job.id}: {error}")

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(
            json.dumps(results, indent=2),
            encoding="utf-8"
        )

        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETED")
        print("=" * 60)
        print("Successful:", len(results))
        print("Failed:", failed)
        print("Saved:", OUTPUT_FILE)

    finally:
        session.close()


if __name__ == "__main__":
    main()
