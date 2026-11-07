
import re


SKILL_DATABASE = {
    "python": ["python"],
    "sql": ["sql", "mysql", "postgresql"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "pytorch": ["pytorch"],
    "tensorflow": ["tensorflow"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "nlp": ["nlp", "natural language processing"],
    "llm": ["llm", "large language models"],
    "generative ai": ["generative ai", "genai"],
    "computer vision": ["computer vision"],
    "yolo": ["yolo"],
    "aws": ["aws", "amazon web services"],
    "docker": ["docker"],
    "git": ["git", "github"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "transformers": ["transformers", "hugging face"],
    "opencv": ["opencv"],
    "xgboost": ["xgboost"],
    "power bi": ["power bi"],
    "excel": ["excel", "microsoft excel"],
    "statistics": ["statistics", "statistical analysis"]
}


ROLE_KEYWORDS = {
    "AI Engineer": ["ai engineer", "artificial intelligence engineer"],
    "Machine Learning Engineer": ["machine learning engineer", "ml engineer"],
    "Data Scientist": ["data scientist"],
    "Data Analyst": ["data analyst"],
    "Data Engineer": ["data engineer"],
    "NLP Engineer": ["nlp engineer", "natural language processing engineer"],
    "Computer Vision Engineer": ["computer vision engineer"],
    "Deep Learning Engineer": ["deep learning engineer"],
    "AI Researcher": ["ai researcher", "research scientist"]
}


EDUCATION_KEYWORDS = [
    "phd",
    "doctorate",
    "master's degree",
    "masters degree",
    "bachelor's degree",
    "bachelors degree",
    "b.tech",
    "b.e.",
    "b.sc",
    "m.tech",
    "m.sc",
    "computer science degree",
    "engineering degree",
    "degree in computer science"
]


def normalize_text(text):
    """Normalize text for consistent matching."""

    if not isinstance(text, str):
        return ""

    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_phrase(text, phrase):
    """Check a phrase without matching inside unrelated words."""

    pattern = (
        r"(?<![a-z0-9+#])"
        + re.escape(phrase.lower())
        + r"(?![a-z0-9+#])"
    )

    return bool(re.search(pattern, text))


def extract_skills(text):
    """Identify known technical skills in a job description."""

    text = normalize_text(text)
    detected_skills = []

    for skill, aliases in SKILL_DATABASE.items():
        if any(contains_phrase(text, alias) for alias in aliases):
            detected_skills.append(skill)

    return sorted(detected_skills)


def get_candidate_skills(profile):
    """Collect skills declared in candidate profile."""

    skills = profile.get("technical_skills", {})
    candidate_skills = []

    if isinstance(skills, dict):
        for skill_list in skills.values():
            if isinstance(skill_list, list):
                candidate_skills.extend(skill_list)

    elif isinstance(skills, list):
        candidate_skills.extend(skills)

    return {
        normalize_text(skill)
        for skill in candidate_skills
        if isinstance(skill, str)
    }


def extract_job_role(text, job_title=None):
    """Identify the most likely job role."""

    title_text = normalize_text(job_title or "")

    search_text = title_text if title_text else normalize_text(text)

    for role, keywords in ROLE_KEYWORDS.items():
        if any(contains_phrase(search_text, keyword) for keyword in keywords):
            return role

    # If the supplied title does not identify a role,
    # inspect the full description.
    if title_text:
        return extract_job_role(text)

    return "Other / Not identified"


def extract_experience_level(text):
    """Estimate the experience level using explicit job wording."""

    text = normalize_text(text)

    if re.search(
        r"\b(intern|internship|entry[- ]level|fresher|graduate trainee)\b",
        text
    ):
        return "Fresher / Internship"

    if re.search(
        r"\b(junior|jr\.?|associate|early career)\b",
        text
    ):
        return "Junior"

    if re.search(
        r"\b(senior|sr\.?|lead|principal|staff|head of)\b",
        text
    ):
        return "Senior"

    if re.search(r"\b(mid[- ]level|intermediate)\b", text):
        return "Mid-level"

    return "Not specified"


def extract_required_experience(text):
    """Extract explicitly stated years of experience."""

    text = normalize_text(text)

    patterns = [
        r"(\d+)\s*(?:-|to)\s*(\d+)\s*\+?\s*years?",
        r"(\d+)\s*\+\s*years?",
        r"at least\s+(\d+)\s+years?",
        r"minimum of\s+(\d+)\s+years?",
        r"minimum\s+(\d+)\s+years?",
        r"(\d+)\s+years?"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            if len(match.groups()) == 2:
                return {
                    "minimum_years": int(match.group(1)),
                    "maximum_years": int(match.group(2))
                }

            return {
                "minimum_years": int(match.group(1)),
                "maximum_years": None
            }

    if re.search(r"\b(no experience required|no prior experience)\b", text):
        return {
            "minimum_years": 0,
            "maximum_years": None
        }

    return {
        "minimum_years": None,
        "maximum_years": None
    }


def extract_education(text):
    """Identify education requirements mentioned in the description."""

    text = normalize_text(text)

    return sorted({
        keyword
        for keyword in EDUCATION_KEYWORDS
        if contains_phrase(text, keyword)
    })


def extract_work_mode(text):
    """Identify remote, hybrid or on-site work arrangements."""

    text = normalize_text(text)
    modes = []

    if re.search(r"\b(remote|work from home|work remotely)\b", text):
        modes.append("Remote")

    if re.search(r"\bhybrid\b", text):
        modes.append("Hybrid")

    if re.search(r"\b(on[- ]site|onsite|office[- ]based)\b", text):
        modes.append("On-site")

    return modes if modes else ["Not specified"]


def extract_employment_type(text):
    """Identify the employment type."""

    text = normalize_text(text)
    employment_types = []

    patterns = {
        "Full-time": r"\bfull[- ]time\b",
        "Part-time": r"\bpart[- ]time\b",
        "Internship": r"\binternship|intern\b",
        "Contract": r"\bcontract|contractor\b",
        "Temporary": r"\btemporary\b",
        "Freelance": r"\bfreelance|freelancer\b"
    }

    for employment_type, pattern in patterns.items():
        if re.search(pattern, text):
            employment_types.append(employment_type)

    return employment_types if employment_types else ["Not specified"]


def extract_location(text, supplied_location=None):
    """Use the known job location, if provided."""

    if supplied_location and str(supplied_location).strip():
        return str(supplied_location).strip()

    return "Not specified"


def analyze_job_description(job_description, profile, job_title=None, location=None):
    """Extract structured job requirements and compare candidate skills."""

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    required_skills = extract_skills(job_description)
    candidate_skills = get_candidate_skills(profile)

    matched_skills = []
    missing_skills = []

    for skill in required_skills:
        aliases = SKILL_DATABASE[skill]

        candidate_has_skill = (
            skill in candidate_skills
            or any(alias in candidate_skills for alias in aliases)
        )

        if candidate_has_skill:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    total = len(required_skills)

    match_percentage = (
        round(len(matched_skills) / total * 100, 2)
        if total else 0
    )

    return {
        "job_role": extract_job_role(job_description, job_title),
        "job_title": job_title or "Not provided",
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "total_required_skills": total,
        "match_percentage": match_percentage,
        "experience_level": extract_experience_level(
            (job_title or "") + " " + job_description
        ),
        "required_experience": extract_required_experience(
            job_description
        ),
        "education_requirements": extract_education(
            job_description
        ),
        "work_mode": extract_work_mode(job_description),
        "employment_type": extract_employment_type(job_description),
        "location": extract_location(job_description, location)
    }


def display_analysis(result):

    print("\n" + "=" * 55)
    print("       AI-JOBPILOT - JOB INTELLIGENCE ANALYSIS")
    print("=" * 55)

    print("\nJOB INFORMATION")
    print("-" * 55)
    print("Title:", result["job_title"])
    print("Role:", result["job_role"])
    print("Experience Level:", result["experience_level"])
    print("Location:", result["location"])
    print("Work Mode:", ", ".join(result["work_mode"]))
    print("Employment Type:", ", ".join(result["employment_type"]))

    experience = result["required_experience"]

    print(
        "Required Experience:",
        experience["minimum_years"]
        if experience["minimum_years"] is not None
        else "Not specified",
        "years"
    )

    print("\nEDUCATION REQUIREMENTS")
    print("-" * 55)

    for item in result["education_requirements"]:
        print(" -", item)

    if not result["education_requirements"]:
        print("Not specified")

    print("\nREQUIRED SKILLS")
    for skill in result["required_skills"]:
        print(" -", skill)

    print("\nMATCHED SKILLS")
    for skill in result["matched_skills"]:
        print(" +", skill)

    print("\nMISSING SKILLS")
    for skill in result["missing_skills"]:
        print(" -", skill)

    print("\nSKILL MATCH SCORE:", result["match_percentage"], "%")
    print("(Keyword overlap only; not an overall hiring probability.)")

    print("=" * 55)


if __name__ == "__main__":

    from src.profile_loader import load_candidate_profile

    sample_job = """
    Junior AI Engineer

    Requirements:
    Bachelor's degree in Computer Science or Engineering.
    0-2 years of experience.
    Python, SQL, Machine Learning,
    PyTorch, TensorFlow, NLP,
    AWS, Docker, FastAPI,
    Computer Vision and XGBoost.

    Full-time position.
    Hybrid work arrangement.
    Location: Bengaluru, India.
    """

    profile = load_candidate_profile()

    result = analyze_job_description(
        sample_job,
        profile,
        job_title="Junior AI Engineer",
        location="Bengaluru, India"
    )

    display_analysis(result)
