import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    KeepTogether,
)

from pypdf import PdfReader


# =========================================================
# PATH CONFIGURATION
# =========================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT_DIR
    / "data"
    / "processed"
    / "tailored_resume_content.json"
)

OUTPUT_DIR = ROOT_DIR / "outputs" / "resumes"

DOCX_FILE = OUTPUT_DIR / "Jerin_Ray_Data_Scientist_Tailored.docx"
PDF_FILE = OUTPUT_DIR / "Jerin_Ray_Data_Scientist_Tailored.pdf"


# =========================================================
# DATA LOADING AND VALIDATION
# =========================================================

def load_resume_data():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input JSON not found: {INPUT_FILE}"
        )

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    required_sections = [
        "candidate",
        "professional_summary",
        "technical_skills",
        "projects",
        "education",
    ]

    for section in required_sections:
        if section not in data:
            raise ValueError(
                f"Missing required section: {section}"
            )

    candidate = data["candidate"]

    if not candidate.get("name"):
        raise ValueError("Candidate name is missing.")

    if not candidate.get("email"):
        raise ValueError("Candidate email is missing.")

    if not data["projects"]:
        raise ValueError("No projects available.")

    if not data["education"]:
        raise ValueError("No education information available.")

    integrity = data.get("integrity_checks", {})

    for key in [
        "invented_skills_added",
        "invented_experience_added",
        "invented_certifications_added",
    ]:
        if integrity.get(key) is True:
            raise ValueError(
                f"Resume integrity check failed: {key}"
            )

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

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_sentences(text):

    text = clean_text(text)

    if not text:
        return []

    # Split on sentence-ending punctuation followed by a capital
    # letter or a digit.
    parts = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text,
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


# =========================================================
# PROJECT CONTENT EXTRACTION
# =========================================================

def extract_project(project):

    title = clean_text(project.get("title", ""))

    description = clean_text(
        project.get("description", "")
    )

    technologies = clean_text(
        project.get("technologies", "")
    )

    if not description:
        description = clean_text(
            project.get("details", "")
        )

    # Remove duplicated project title from description.
    if title and description.lower().startswith(title.lower()):
        description = description[len(title):].strip()

    description = description.lstrip(" :-|,")

    # Detect technology list before the first action statement.
    if not technologies:

        action_match = re.search(
            r"\b(Engineered|Developed|Built|Designed|"
            r"Implemented|Created|Automated|Trained|"
            r"Constructed|Performed|Evaluated|Applied)\b",
            description,
            flags=re.IGNORECASE,
        )

        if action_match:

            possible_technologies = (
                description[:action_match.start()]
            )

            possible_technologies = possible_technologies.strip(
                " :-|,"
            )

            if possible_technologies:
                technologies = possible_technologies

            description = description[action_match.start():]

    # Remove duplicated technology text if present.
    if technologies and description.lower().startswith(
        technologies.lower()
    ):
        description = description[len(technologies):].strip()

    description = description.lstrip(" :-|,")

    bullets = split_sentences(description)

    if not bullets and description:
        bullets = [description]

    return {
        "title": title,
        "technologies": technologies,
        "bullets": bullets,
    }


# =========================================================
# PUBLICATION EXTRACTION
# =========================================================

def extract_publication(publication):

    if not publication:
        return []

    text = clean_text(publication)

    # Keep the original publication text intact.
    return [text]


# =========================================================
# PREPARE RESUME CONTENT
# =========================================================

def prepare_resume(data):

    candidate = data["candidate"]

    contact = []

    email = clean_text(candidate.get("email"))
    phone = clean_text(candidate.get("phone"))
    linkedin = clean_text(candidate.get("linkedin"))

    if email:
        contact.append(email)

    if phone:
        contact.append(phone)

    if linkedin:
        if not linkedin.startswith("http"):
            linkedin = "https://" + linkedin

        contact.append(linkedin)

    skills = [
        clean_text(skill)
        for skill in data.get("technical_skills", [])
        if clean_text(skill)
    ]

    projects = [
        extract_project(project)
        for project in data.get("projects", [])
    ]

    education = [
        clean_text(item)
        for item in data.get("education", [])
        if clean_text(item)
    ]

    publication = extract_publication(
        data.get("research_publication")
    )

    summary = clean_text(
        data.get("professional_summary")
    )

    return {
        "name": clean_text(candidate["name"]),
        "contact": contact,
        "summary": summary,
        "skills": skills,
        "projects": projects,
        "publication": publication,
        "education": education,
    }


# =========================================================
# DOCX SECTION HEADING
# =========================================================

def add_docx_heading(document, heading):

    paragraph = document.add_paragraph()

    paragraph.paragraph_format.space_before = Pt(9)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.keep_with_next = True

    run = paragraph.add_run(heading.upper())

    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(31, 78, 121)

    return paragraph


# =========================================================
# DOCX BULLET
# =========================================================

def add_docx_bullet(document, text):

    paragraph = document.add_paragraph(style="List Bullet")

    paragraph.paragraph_format.left_indent = Inches(0.22)
    paragraph.paragraph_format.first_line_indent = Inches(-0.12)
    paragraph.paragraph_format.space_after = Pt(3)

    run = paragraph.add_run(clean_text(text))

    run.font.name = "Arial"
    run.font.size = Pt(9)

    return paragraph


# =========================================================
# GENERATE DOCX
# =========================================================

def generate_docx(resume):

    document = Document()

    section = document.sections[0]

    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)

    normal = document.styles["Normal"]

    normal.font.name = "Arial"
    normal.font.size = Pt(9)
    normal.paragraph_format.space_after = Pt(3)

    # Candidate name
    paragraph = document.add_paragraph()

    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(3)

    run = paragraph.add_run(resume["name"])

    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(19)
    run.font.color.rgb = RGBColor(31, 78, 121)

    # Contact information
    paragraph = document.add_paragraph()

    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(7)

    run = paragraph.add_run(
        " | ".join(resume["contact"])
    )

    run.font.name = "Arial"
    run.font.size = Pt(8)

    # Professional summary
    add_docx_heading(
        document,
        "Professional Summary",
    )

    document.add_paragraph(resume["summary"])

    # Technical skills
    add_docx_heading(
        document,
        "Technical Skills",
    )

    skills_paragraph = document.add_paragraph()

    skills_run = skills_paragraph.add_run(
        ", ".join(resume["skills"])
    )

    skills_run.font.name = "Arial"
    skills_run.font.size = Pt(9)

    # Projects
    add_docx_heading(
        document,
        "Projects",
    )

    for project in resume["projects"]:

        title_paragraph = document.add_paragraph()

        title_paragraph.paragraph_format.space_before = Pt(4)
        title_paragraph.paragraph_format.space_after = Pt(2)
        title_paragraph.paragraph_format.keep_with_next = True

        title_run = title_paragraph.add_run(
            project["title"]
        )

        title_run.bold = True
        title_run.font.name = "Arial"
        title_run.font.size = Pt(10)

        if project["technologies"]:

            tech_paragraph = document.add_paragraph()

            tech_paragraph.paragraph_format.space_after = Pt(2)
            tech_paragraph.paragraph_format.keep_with_next = True

            tech_run = tech_paragraph.add_run(
                "Technologies: " + project["technologies"]
            )

            tech_run.italic = True
            tech_run.font.name = "Arial"
            tech_run.font.size = Pt(8)

        for bullet in project["bullets"]:
            add_docx_bullet(document, bullet)

    # Research publication
    if resume["publication"]:

        add_docx_heading(
            document,
            "Research Publication",
        )

        for publication in resume["publication"]:
            document.add_paragraph(publication)

    # Education
    add_docx_heading(
        document,
        "Education",
    )

    for item in resume["education"]:
        add_docx_bullet(document, item)

    document.save(DOCX_FILE)


# =========================================================
# PDF STYLES
# =========================================================

def create_pdf_styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ResumeName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1F4E79"),
            spaceAfter=3,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeContact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor("#1F4E79"),
            spaceBefore=8,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeProjectTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            spaceBefore=4,
            spaceAfter=2,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeTechnology",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            spaceAfter=2,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeBullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        )
    )

    return styles


# =========================================================
# GENERATE PDF
# =========================================================

def generate_pdf(resume):

    styles = create_pdf_styles()

    story = []

    # Candidate name
    story.append(
        Paragraph(
            escape(resume["name"]),
            styles["ResumeName"],
        )
    )

    # Contact
    contact_text = " | ".join(resume["contact"])

    story.append(
        Paragraph(
            escape(contact_text),
            styles["ResumeContact"],
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.7,
            color=colors.HexColor("#1F4E79"),
            spaceAfter=5,
        )
    )

    # Summary
    story.append(
        Paragraph(
            "PROFESSIONAL SUMMARY",
            styles["ResumeHeading"],
        )
    )

    story.append(
        Paragraph(
            escape(resume["summary"]),
            styles["ResumeBody"],
        )
    )

    # Skills
    story.append(
        Paragraph(
            "TECHNICAL SKILLS",
            styles["ResumeHeading"],
        )
    )

    story.append(
        Paragraph(
            escape(", ".join(resume["skills"])),
            styles["ResumeBody"],
        )
    )

    # Projects
    story.append(
        Paragraph(
            "PROJECTS",
            styles["ResumeHeading"],
        )
    )

    for project in resume["projects"]:

        elements = []

        elements.append(
            Paragraph(
                escape(project["title"]),
                styles["ResumeProjectTitle"],
            )
        )

        if project["technologies"]:

            elements.append(
                Paragraph(
                    "Technologies: "
                    + escape(project["technologies"]),
                    styles["ResumeTechnology"],
                )
            )

        for bullet in project["bullets"]:

            elements.append(
                Paragraph(
                    "- " + escape(bullet),
                    styles["ResumeBullet"],
                )
            )

        story.append(
            KeepTogether(elements)
        )

    # Publication
    if resume["publication"]:

        story.append(
            Paragraph(
                "RESEARCH PUBLICATION",
                styles["ResumeHeading"],
            )
        )

        for publication in resume["publication"]:

            story.append(
                Paragraph(
                    escape(publication),
                    styles["ResumeBody"],
                )
            )

    # Education
    story.append(
        Paragraph(
            "EDUCATION",
            styles["ResumeHeading"],
        )
    )

    for item in resume["education"]:

        story.append(
            Paragraph(
                "- " + escape(item),
                styles["ResumeBullet"],
            )
        )

    pdf = SimpleDocTemplate(
        str(PDF_FILE),
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
        title="Jerin Ray - Data Scientist Resume",
        author=resume["name"],
    )

    pdf.build(story)


# =========================================================
# VALIDATE GENERATED DOCUMENTS
# =========================================================

def validate_outputs(resume):

    if not DOCX_FILE.exists():
        raise FileNotFoundError("DOCX file was not generated.")

    if not PDF_FILE.exists():
        raise FileNotFoundError("PDF file was not generated.")

    if DOCX_FILE.stat().st_size == 0:
        raise ValueError("DOCX file is empty.")

    if PDF_FILE.stat().st_size == 0:
        raise ValueError("PDF file is empty.")

    # Read DOCX again
    doc = Document(str(DOCX_FILE))

    docx_text = "\n".join(
        paragraph.text
        for paragraph in doc.paragraphs
    )

    # Read PDF again
    reader = PdfReader(str(PDF_FILE))

    pdf_text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    required_content = [
        resume["name"],
        "PROFESSIONAL SUMMARY",
        "TECHNICAL SKILLS",
        "PROJECTS",
        "EDUCATION",
    ]

    for item in required_content:

        if item not in docx_text:
            raise AssertionError(
                f"Missing from DOCX: {item}"
            )

        if item not in pdf_text:
            raise AssertionError(
                f"Missing from PDF: {item}"
            )

    # Check both project titles
    for project in resume["projects"]:

        if project["title"] not in docx_text:
            raise AssertionError(
                f"Project missing from DOCX: {project['title']}"
            )

        if project["title"] not in pdf_text:
            raise AssertionError(
                f"Project missing from PDF: {project['title']}"
            )

    if not reader.pages:
        raise AssertionError("PDF has no pages.")

    return {
        "docx_size_bytes": DOCX_FILE.stat().st_size,
        "pdf_size_bytes": PDF_FILE.stat().st_size,
        "pdf_page_count": len(reader.pages),
        "docx_paragraph_count": len(doc.paragraphs),
    }


# =========================================================
# MAIN EXECUTION
# =========================================================

def main():

    print("=" * 60)
    print("AI-JOBPILOT - DAY 9")
    print("ATS RESUME DOCUMENT GENERATOR")
    print("=" * 60)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\n[1/5] Loading resume JSON...")

    data = load_resume_data()

    print("[2/5] Preparing resume content...")

    resume = prepare_resume(data)

    print("[3/5] Generating DOCX...")

    generate_docx(resume)

    print("[4/5] Generating PDF...")

    generate_pdf(resume)

    print("[5/5] Validating generated documents...")

    results = validate_outputs(resume)

    print("\n" + "=" * 60)
    print("SUCCESS - RESUME DOCUMENTS GENERATED")
    print("=" * 60)

    print("\nCandidate:", resume["name"])
    print("Target role:", data["target_job"]["title"])

    print("\nDOCX FILE:")
    print(DOCX_FILE)

    print("\nPDF FILE:")
    print(PDF_FILE)

    print("\nVALIDATION RESULTS:")

    for key, value in results.items():
        print(f"{key}: {value}")

    print("\nRESUME CONTENT:")
    print("Projects:", len(resume["projects"]))
    print("Skills:", len(resume["skills"]))
    print("Education entries:", len(resume["education"]))
    print("Publication entries:", len(resume["publication"]))

    print("\nINTEGRITY:")
    print(
        "Invented skills:",
        data["integrity_checks"].get("invented_skills_added"),
    )
    print(
        "Invented experience:",
        data["integrity_checks"].get("invented_experience_added"),
    )
    print(
        "Invented certifications:",
        data["integrity_checks"].get("invented_certifications_added"),
    )

    print("\nDAY 9 GENERATION COMPLETED")


if __name__ == "__main__":
    main()