
import json
import re
from pathlib import Path
from datetime import date
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Inches, Pt, RGBColor

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    HRFlowable,
)

from pypdf import PdfReader


# =========================================================
# PATHS
# =========================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT_DIR / "data" / "processed" / "tailored_resume_content.json"

OUTPUT_DIR = ROOT_DIR / "outputs" / "cover_letters"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

JSON_OUTPUT = PROCESSED_DIR / "generated_cover_letter.json"

DOCX_OUTPUT = OUTPUT_DIR / "Jerin_Ray_Data_Scientist_Cover_Letter.docx"

PDF_OUTPUT = OUTPUT_DIR / "Jerin_Ray_Data_Scientist_Cover_Letter.pdf"


# =========================================================
# LOAD INPUT
# =========================================================

def load_resume_data():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Resume data not found: {INPUT_FILE}")

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    required_sections = [
        "candidate",
        "target_job",
        "professional_summary",
        "projects",
        "technical_skills",
    ]

    for section in required_sections:
        if section not in data:
            raise ValueError(f"Required section missing: {section}")

    candidate = data["candidate"]
    job = data["target_job"]

    if not candidate.get("name"):
        raise ValueError("Candidate name is missing.")

    if not candidate.get("email"):
        raise ValueError("Candidate email is missing.")

    if not job.get("title"):
        raise ValueError("Target job title is missing.")

    if not job.get("company"):
        raise ValueError("Target company is missing.")

    integrity = data.get("integrity_checks", {})

    for key in [
        "invented_skills_added",
        "invented_experience_added",
        "invented_certifications_added",
    ]:
        if integrity.get(key) is True:
            raise ValueError(f"Resume integrity check failed: {key}")

    return data


# =========================================================
# TEXT UTILITIES
# =========================================================

def clean_text(value):

    if value is None:
        return ""

    text = str(value)

    replacements = {
        "\u2022": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\xa0": " ",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return re.sub(r"\s+", " ", text).strip()


def normalize_for_validation(text):

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(text).lower()
    )


def prepare_project_description(project):

    title = clean_text(project.get("title", ""))
    description = clean_text(project.get("description", ""))

    if title and description.lower().startswith(title.lower()):
        description = description[len(title):].strip()

    return description.lstrip(" :-|,")


# =========================================================
# GENERATE COVER LETTER CONTENT
# =========================================================

def generate_cover_letter_content(data):

    candidate = data["candidate"]
    job = data["target_job"]

    candidate_name = clean_text(candidate["name"])
    email = clean_text(candidate["email"])
    linkedin = clean_text(candidate.get("linkedin"))

    job_title = clean_text(job["title"])
    company = clean_text(job["company"])

    summary = clean_text(data.get("professional_summary"))

    projects = data.get("projects", [])
    skills = [
        clean_text(skill)
        for skill in data.get("technical_skills", [])
        if clean_text(skill)
    ]

    publication = clean_text(data.get("research_publication"))

    preferred_skills = [
        "Python",
        "SQL",
        "Machine Learning",
        "Deep Learning",
        "PyTorch",
        "Pandas",
        "NumPy",
        "Scikit-learn",
    ]

    available = {skill.lower() for skill in skills}

    selected_skills = [
        skill
        for skill in preferred_skills
        if skill.lower() in available
    ]

    if not selected_skills:
        selected_skills = skills[:5]

    skills_text = ", ".join(selected_skills)

    paragraphs = [
        "Dear Hiring Team,",

        (
            f"I am writing to express my interest in the "
            f"{job_title} position at {company}. {summary}"
        ),

        (
            f"My technical background includes {skills_text}. "
            "I am interested in applying these skills to practical "
            "data science problems and continuing to develop my "
            "technical capabilities in a professional environment."
        ),
    ]

    project_titles = []

    for project in projects[:2]:

        title = clean_text(project.get("title"))
        description = prepare_project_description(project)

        if title:
            project_titles.append(title)

        if title and description:
            paragraphs.append(
                f"My project, {title}, involved {description}"
            )
        elif title:
            paragraphs.append(
                f"My project, {title}, strengthened my understanding "
                "of applied data science."
            )

    if publication:
        paragraphs.append(
            f"I have also worked on the research topic {publication}. "
            "This work reflects my interest in spatiotemporal modelling "
            "and applied machine learning."
        )

    paragraphs.extend([
        (
            "As a recent graduate in Artificial Intelligence and "
            "Data Science, I am eager to contribute, learn from an "
            "experienced team, and take responsibility for meaningful "
            "technical work. I would welcome the opportunity to discuss "
            "how my academic, project, and research background may align "
            "with your requirements."
        ),
        (
            "Thank you for your time and consideration. "
            "I look forward to hearing from you."
        ),
        f"Sincerely,\n{candidate_name}",
    ])

    warnings = data.get("job_description_warnings", [])

    return {
        "candidate": {
            "name": candidate_name,
            "email": email,
            "linkedin": linkedin or None,
        },
        "target_job": {
            "job_id": job.get("job_id"),
            "title": job_title,
            "company": company,
            "location": job.get("location"),
            "application_url": job.get("application_url"),
        },
        "generated_date": date.today().isoformat(),
        "subject": f"Application for {job_title} Position",
        "paragraphs": paragraphs,
        "skills_used": selected_skills,
        "projects_referenced": project_titles,
        "research_publication_included": bool(publication),
        "job_description_warnings": warnings,
        "manual_review_required": bool(warnings),
        "generation_method": "Rule-based template using supplied resume data",
        "integrity_checks": {
            "invented_skills_added": False,
            "invented_experience_added": False,
            "invented_certifications_added": False,
        },
    }


# =========================================================
# SAVE JSON
# =========================================================

def save_json(content):

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with JSON_OUTPUT.open("w", encoding="utf-8") as file:
        json.dump(
            content,
            file,
            indent=4,
            ensure_ascii=False,
        )


# =========================================================
# GENERATE DOCX
# =========================================================

def generate_docx(content):

    document = Document()

    section = document.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    normal = document.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(9)

    paragraph = document.add_paragraph()
    run = paragraph.add_run(content["candidate"]["name"])

    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(17)
    run.font.color.rgb = RGBColor(31, 78, 121)

    contact = [content["candidate"]["email"]]

    if content["candidate"]["linkedin"]:
        contact.append(content["candidate"]["linkedin"])

    paragraph = document.add_paragraph(" | ".join(contact))

    for run in paragraph.runs:
        run.font.name = "Arial"
        run.font.size = Pt(9)

    document.add_paragraph()
    document.add_paragraph(content["generated_date"])

    subject = document.add_paragraph()
    subject_run = subject.add_run(content["subject"])
    subject_run.bold = True
    subject_run.font.size = Pt(11)

    document.add_paragraph()

    for paragraph_text in content["paragraphs"]:

        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(9)
        paragraph.paragraph_format.line_spacing = 1.12

        run = paragraph.add_run(paragraph_text)
        run.font.name = "Arial"
        run.font.size = Pt(10)

    document.save(DOCX_OUTPUT)


# =========================================================
# GENERATE PDF
# =========================================================

def generate_pdf(content):

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="LetterName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#1F4E79"),
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="LetterContact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="LetterBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="LetterSubject",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            spaceAfter=12,
        )
    )

    story = []

    story.append(
        Paragraph(
            escape(content["candidate"]["name"]),
            styles["LetterName"],
        )
    )

    contact = [content["candidate"]["email"]]

    if content["candidate"]["linkedin"]:
        contact.append(content["candidate"]["linkedin"])

    story.append(
        Paragraph(
            escape(" | ".join(contact)),
            styles["LetterContact"],
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.7,
            color=colors.HexColor("#1F4E79"),
            spaceAfter=12,
        )
    )

    story.append(
        Paragraph(
            escape(content["generated_date"]),
            styles["LetterBody"],
        )
    )

    story.append(
        Paragraph(
            escape(content["subject"]),
            styles["LetterSubject"],
        )
    )

    for paragraph_text in content["paragraphs"]:

        safe_text = escape(paragraph_text)
        safe_text = safe_text.replace("\n", "<br/>")

        story.append(
            Paragraph(
                safe_text,
                styles["LetterBody"],
            )
        )

    pdf = SimpleDocTemplate(
        str(PDF_OUTPUT),
        pagesize=A4,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=content["subject"],
        author=content["candidate"]["name"],
    )

    pdf.build(story)


# =========================================================
# VALIDATE GENERATED FILES
# =========================================================

def validate_outputs(content):

    paths = [
        JSON_OUTPUT,
        DOCX_OUTPUT,
        PDF_OUTPUT,
    ]

    for path in paths:

        if not path.exists():
            raise FileNotFoundError(
                f"Generated file missing: {path}"
            )

        if path.stat().st_size == 0:
            raise ValueError(
                f"Generated file is empty: {path}"
            )

    # JSON validation
    with JSON_OUTPUT.open("r", encoding="utf-8") as file:
        saved_content = json.load(file)

    if saved_content["candidate"]["name"] != content["candidate"]["name"]:
        raise AssertionError("JSON candidate validation failed.")

    # DOCX validation
    doc = Document(str(DOCX_OUTPUT))

    docx_text = "\n".join(
        paragraph.text
        for paragraph in doc.paragraphs
    )

    # PDF validation
    reader = PdfReader(str(PDF_OUTPUT))

    if len(reader.pages) == 0:
        raise AssertionError("PDF contains no pages.")

    pdf_text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    normalized_docx = normalize_for_validation(docx_text)
    normalized_pdf = normalize_for_validation(pdf_text)

    required_text = [
        content["candidate"]["name"],
        content["target_job"]["title"],
        content["target_job"]["company"],
        content["subject"],
    ]

    for item in required_text:

        normalized_item = normalize_for_validation(item)

        if normalized_item not in normalized_docx:
            raise AssertionError(
                f"Missing from DOCX: {item}"
            )

        if normalized_item not in normalized_pdf:
            raise AssertionError(
                f"Missing from PDF: {item}"
            )

    return {
        "json_size_bytes": JSON_OUTPUT.stat().st_size,
        "docx_size_bytes": DOCX_OUTPUT.stat().st_size,
        "pdf_size_bytes": PDF_OUTPUT.stat().st_size,
        "pdf_page_count": len(reader.pages),
        "docx_paragraph_count": len(doc.paragraphs),
        "pdf_text_extraction": "Passed",
        "content_validation": "Passed",
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("AI-JOBPILOT - DAY 10")
    print("COVER LETTER GENERATOR")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/6] Loading tailored resume data...")
    data = load_resume_data()

    print("[2/6] Generating cover letter content...")
    content = generate_cover_letter_content(data)

    print("[3/6] Saving cover letter JSON...")
    save_json(content)

    print("[4/6] Generating DOCX...")
    generate_docx(content)

    print("[5/6] Generating PDF...")
    generate_pdf(content)

    print("[6/6] Validating generated files...")
    results = validate_outputs(content)

    print("\n" + "=" * 60)
    print("COVER LETTER GENERATION SUCCESSFUL")
    print("=" * 60)

    print("\nCandidate:", content["candidate"]["name"])
    print("Position:", content["target_job"]["title"])
    print("Company:", content["target_job"]["company"])

    print("\nGenerated files:")
    print("JSON:", JSON_OUTPUT)
    print("DOCX:", DOCX_OUTPUT)
    print("PDF :", PDF_OUTPUT)

    print("\nValidation:")

    for key, value in results.items():
        print(f"{key}: {value}")

    print("\nSkills referenced:", len(content["skills_used"]))
    print("Projects referenced:", len(content["projects_referenced"]))

    print(
        "Manual review required:",
        content["manual_review_required"],
    )

    print("\nDAY 10 COVER LETTER MODULE COMPLETED")


if __name__ == "__main__":
    main()
