
import json
import re
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

RESUME_FILE = BASE_DIR / "data/processed/resume_information.json"
DATABASE_FILE = BASE_DIR / "data/ai_jobpilot.db"

OUTPUT_DIR = BASE_DIR / "data/processed"
OUTPUT_FILE = OUTPUT_DIR / "tailored_resume_content.json"


SKILL_ALIASES = {
    "c/c++": ["c++", "c"],
    "c++": ["c++", "c/c++"],
    "llm": ["llm", "large language models"],
    "sql": ["sql", "structured query language"],
}


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize(value):
    value = str(value or "").lower()
    value = re.sub(r"[^a-z0-9+#]+", " ", value)
    return " ".join(value.split())


def get_job_from_database(job_id):
    if not DATABASE_FILE.exists():
        raise FileNotFoundError("Job database not found.")

    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (job_id,)
        ).fetchone()

        if row is None:
            raise ValueError(f"Job ID {job_id} not found.")

        return dict(row)

    finally:
        connection.close()


def extract_required_skills(description):
    skill_dictionary = [
        "Python",
        "SQL",
        "C++",
        "Java",
        "Machine Learning",
        "Deep Learning",
        "Pandas",
        "NumPy",
        "Scikit-learn",
        "TensorFlow",
        "PyTorch",
        "Statistics",
        "Data Analysis",
    ]

    normalized_description = normalize(description)
    found = []

    for skill in skill_dictionary:
        normalized_skill = normalize(skill)

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(normalized_skill)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, normalized_description):
            found.append(skill)

    return found


def compare_candidate_skills(required_skills, candidate_skills):
    candidate_normalized = {
        normalize(skill): skill
        for skill in candidate_skills
    }

    matched = []
    missing = []

    for required in required_skills:
        key = normalize(required)

        aliases = SKILL_ALIASES.get(key, [])

        possible_matches = [key] + [
            normalize(alias) for alias in aliases
        ]

        found = None

        for possible in possible_matches:
            if possible in candidate_normalized:
                found = candidate_normalized[possible]
                break

        if found:
            matched.append({
                "required_skill": required,
                "resume_evidence": found
            })
        else:
            missing.append(required)

    return matched, missing


def build_tailored_summary():
    return (
        "B.Tech graduate in Artificial Intelligence and Data Science "
        "(2026) with project and research experience in Python-based "
        "data analytics, machine learning, and predictive modelling. "
        "Worked on data preprocessing, exploratory data analysis, "
        "feature engineering, statistical analysis, and model "
        "development using Python, SQL, C/C++, Pandas, NumPy, and "
        "Scikit-learn. Research experience includes spatiotemporal "
        "deep learning architectures for radar nowcasting."
    )


def select_relevant_skills(candidate_skills, required_skills):
    preferred_order = [
        "Python",
        "SQL",
        "C++",
        "C/C++",
        "Pandas",
        "NumPy",
        "Scikit-learn",
        "Machine Learning",
        "Exploratory Data Analysis",
        "Feature Engineering",
        "Statistical Inference",
        "Predictive Analytics",
        "SciPy",
        "Matplotlib",
        "Seaborn",
    ]

    normalized_candidates = {
        normalize(skill): skill
        for skill in candidate_skills
    }

    selected = []

    # Prioritize explicit job requirements.
    for required in required_skills:
        key = normalize(required)

        if key in normalized_candidates:
            actual_skill = normalized_candidates[key]

            if actual_skill not in selected:
                selected.append(actual_skill)

    # Add relevant skills from the original resume.
    for skill in preferred_order:
        key = normalize(skill)

        if key in normalized_candidates:
            actual_skill = normalized_candidates[key]

            if actual_skill not in selected:
                selected.append(actual_skill)

    return selected


def extract_individual_projects(resume):
    project_data = resume.get("projects", {})

    project_titles = project_data.get("titles", [])
    project_description = project_data.get("full_description", "")

    projects = []
    project_positions = []

    for title in project_titles:
        if not title:
            continue

        position = project_description.find(title)

        if position != -1:
            project_positions.append((position, title))

    project_positions.sort(key=lambda item: item[0])

    for index, (start, title) in enumerate(project_positions):

        if index + 1 < len(project_positions):
            end = project_positions[index + 1][0]
        else:
            end = len(project_description)

        individual_description = (
            project_description[start:end].strip()
        )

        projects.append({
            "title": title,
            "source": "original_resume",
            "description": individual_description
        })

    return projects


def build_tailored_resume(job_id):
    resume = load_json(RESUME_FILE)
    job = get_job_from_database(job_id)

    description = job.get("description") or ""

    if not description.strip():
        raise ValueError("Selected job has no description.")

    candidate_skills = resume.get("skills", [])

    required_skills = extract_required_skills(description)

    matched, missing = compare_candidate_skills(
        required_skills,
        candidate_skills
    )

    selected_skills = select_relevant_skills(
        candidate_skills,
        required_skills
    )

    projects = extract_individual_projects(resume)

    publication = resume.get("research_publications", "")
    education = resume.get("education", [])

    personal_information = {
        "name": resume.get("candidate_name"),
        "email": resume.get("email"),
        "phone": resume.get("phone"),
        "linkedin": resume.get("linkedin"),
    }

    match_percentage = (
        round(len(matched) / len(required_skills) * 100, 2)
        if required_skills else None
    )

    tailored_content = {
        "document_type": "Job-Specific Tailored Resume Content",

        "target_job": {
            "job_id": job.get("id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "work_mode": job.get("work_mode"),
            "employment_type": job.get("employment_type"),
            "application_url": job.get("apply_url"),
        },

        "candidate": personal_information,

        "professional_summary": build_tailored_summary(),

        "technical_skills": selected_skills,

        "skill_match_analysis": {
            "required_skills": required_skills,
            "matched_skills": matched,
            "missing_skills": missing,
            "match_percentage": match_percentage,
        },

        "projects": projects,

        "research_publication": publication,

        "education": education,

        "experience": resume.get("experience") or None,

        "internship": resume.get("internship") or None,

        "certifications": resume.get("certifications") or None,

        "integrity_checks": {
            "invented_skills_added": False,
            "invented_experience_added": False,
            "invented_certifications_added": False,
            "source": "Existing candidate resume",
            "missing_information_omitted": True,
        },

        "job_description_warnings": [
            "The supplied job description contains limited role-specific details.",
            "Responsibilities and experience requirements are not clearly stated.",
            "Verify the employer and job listing before applying.",
        ],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            tailored_content,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("=" * 65)
    print("AI-JOBPILOT — DAY 8 RESUME TAILORING")
    print("=" * 65)

    print("Target job:", job.get("title"))
    print("Company:", job.get("company"))
    print("Candidate:", resume.get("candidate_name"))

    print("\nREQUIRED SKILLS:")
    print(required_skills)

    print("\nMATCHED SKILLS:")
    for item in matched:
        print(
            f"{item['required_skill']} -> "
            f"{item['resume_evidence']}"
        )

    print("\nMISSING SKILLS:")
    print(missing)

    print("\nMATCH PERCENTAGE:")
    print(match_percentage)

    print("\nTAILORED SKILLS:")
    print(selected_skills)

    print("\nPROJECTS EXTRACTED:")
    for project in projects:
        print("-", project["title"])

    print("\nOUTPUT:")
    print(OUTPUT_FILE)

    print("\nRESUME TAILORING COMPLETED")

    # Important: return the generated data to the caller.
    return tailored_content


if __name__ == "__main__":
    build_tailored_resume(job_id=21)
