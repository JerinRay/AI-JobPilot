
import re
import json
from pathlib import Path


RESUME_FILE = Path("data/processed/extracted_resume.txt")
OUTPUT_FILE = Path("data/processed/resume_information.json")


SKILL_KEYWORDS = [
    "Python", "SQL", "C++", "Java",
    "Machine Learning", "Deep Learning",
    "PyTorch", "TensorFlow", "Keras",
    "Scikit-learn", "Pandas", "NumPy", "SciPy",
    "NLP", "Natural Language Processing",
    "Computer Vision", "OpenCV", "YOLO",
    "CNN", "RNN", "ConvLSTM", "PredRNN",
    "Spatiotemporal Modeling",
    "Matplotlib", "Seaborn",
    "Git", "GitHub", "Docker", "AWS",
    "FastAPI", "Flask", "SQLAlchemy",
    "Power BI", "Tableau",
    "Exploratory Data Analysis",
    "Feature Engineering",
    "JupyterLab", "VS Code", "Google Colab",
    "Linux", "Bash",
    "Statistical Inference", "Predictive Analytics"
]


SECTION_NAMES = [
    "PROFESSIONAL SUMMARY",
    "TECHNICAL SKILLS",
    "RESEARCH & PUBLICATIONS",
    "TECHNICAL PROJECTS",
    "EDUCATION",
    "CORE COMPETENCIES & INTERESTS",
    "WORK EXPERIENCE",
    "EXPERIENCE",
    "INTERNSHIP",
    "CERTIFICATIONS",
    "PROJECTS"
]


def extract_email(text):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )
    return match.group(0) if match else None


def extract_phone(text):
    match = re.search(
        r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
        text
    )
    return match.group(0) if match else None


def extract_linkedin(text):
    match = re.search(
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+",
        text,
        re.IGNORECASE
    )
    return match.group(0) if match else None


def extract_name(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines[:5]:
        if (
            "@" not in line
            and "linkedin.com" not in line.lower()
            and not re.search(r"\d", line)
            and len(line.split()) <= 4
        ):
            return line

    return None


def extract_skills(text):
    found_skills = []

    for skill in SKILL_KEYWORDS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text, re.IGNORECASE):
            found_skills.append(skill)

    return sorted(found_skills, key=str.lower)


def extract_sections(text):
    sections = {}
    current_section = "OTHER"
    sections[current_section] = []

    for line in text.splitlines():
        cleaned = line.strip()

        if not cleaned:
            continue

        if cleaned.upper() in SECTION_NAMES:
            current_section = cleaned.upper()
            sections[current_section] = []
        else:
            sections[current_section].append(cleaned)

    return {
        section: "\n".join(content)
        for section, content in sections.items()
        if content
    }


def extract_education(text):
    education_terms = [
        "Bachelor of Technology",
        "B.Tech",
        "B.E.",
        "B.Sc",
        "M.Tech",
        "M.Sc",
        "Master of Technology",
        "University",
        "College"
    ]

    results = []

    for line in text.splitlines():
        cleaned = line.strip()

        if any(
            term.lower() in cleaned.lower()
            for term in education_terms
        ):
            results.append(cleaned)

    return results


def clean_project_title(line):
    """Remove technology stack appended to a project title."""

    cleaned = re.sub(r"\s+", " ", line).strip()

    technology_pattern = (
        r"\s+(?=(?:Python|PyTorch|Pandas|NumPy|"
        r"Scikit-learn|Seaborn|OpenCV|TensorFlow),)"
    )

    parts = re.split(technology_pattern, cleaned, maxsplit=1)

    return parts[0].strip()


def extract_project_titles(project_text):
    if not project_text:
        return []

    titles = []

    action_verbs = (
        "Engineered", "Implemented", "Constructed",
        "Designed", "Built", "Created", "Developed",
        "Conducted", "Performed", "Analyzed"
    )

    for line in project_text.splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip()

        if not cleaned:
            continue

        if cleaned.startswith(action_verbs):
            continue

        # Project headings in this resume contain technology stacks.
        has_technology_stack = bool(
            re.search(
                r"\b(?:Python|PyTorch|Pandas|NumPy|"
                r"Scikit-learn|Seaborn|OpenCV|TensorFlow),",
                cleaned
            )
        )

        if has_technology_stack:
            title = clean_project_title(cleaned)

            if title and title not in titles:
                titles.append(title)

    return titles


def build_resume_information():
    if not RESUME_FILE.exists():
        raise FileNotFoundError(
            f"Resume text file not found: {RESUME_FILE}"
        )

    text = RESUME_FILE.read_text(encoding="utf-8")

    sections = extract_sections(text)

    projects_text = sections.get(
        "TECHNICAL PROJECTS",
        sections.get("PROJECTS", "")
    )

    information = {
        "candidate_name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin": extract_linkedin(text),

        "skills": extract_skills(text),

        "education": extract_education(text),

        "professional_summary": sections.get(
            "PROFESSIONAL SUMMARY", ""
        ),

        "research_publications": sections.get(
            "RESEARCH & PUBLICATIONS", ""
        ),

        "projects": {
            "titles": extract_project_titles(projects_text),
            "full_description": projects_text
        },

        "experience": sections.get(
            "WORK EXPERIENCE",
            sections.get("EXPERIENCE", "")
        ),

        "internship": sections.get("INTERNSHIP", ""),

        "certifications": sections.get("CERTIFICATIONS", ""),

        "core_competencies": sections.get(
            "CORE COMPETENCIES & INTERESTS", ""
        ),

        "detected_sections": list(sections.keys())
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            information,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return information


if __name__ == "__main__":
    try:
        result = build_resume_information()

        print("\nRESUME INFORMATION EXTRACTION SUCCESSFUL")
        print("=" * 50)

        print("\nCANDIDATE INFORMATION")
        print("---------------------")
        print("Name:", result["candidate_name"])
        print("Email:", result["email"])
        print("Phone:", result["phone"])
        print("LinkedIn:", result["linkedin"])

        print("\nDETECTED SKILLS")
        print("---------------")
        for skill in result["skills"]:
            print("-", skill)

        print("\nEDUCATION")
        print("---------")
        for item in result["education"]:
            print("-", item)

        print("\nRESEARCH PUBLICATION")
        print("--------------------")
        print(result["research_publications"][:500] or "Not detected")

        print("\nPROJECT TITLES")
        print("--------------")
        for title in result["projects"]["titles"]:
            print("-", title)

        print("\nDETECTED SECTIONS")
        print("-----------------")
        for section in result["detected_sections"]:
            print("-", section)

        print("\nJSON saved to:", OUTPUT_FILE)

    except Exception as error:
        print("\nERROR:", error)
