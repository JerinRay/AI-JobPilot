
import json
from pathlib import Path
from datetime import date


# =========================================================
# PATHS
# =========================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

RESUME_DATA_FILE = (
    ROOT_DIR
    / "data"
    / "processed"
    / "tailored_resume_content.json"
)

COVER_LETTER_FILE = (
    ROOT_DIR
    / "data"
    / "processed"
    / "generated_cover_letter.json"
)

OUTPUT_FILE = (
    ROOT_DIR
    / "data"
    / "processed"
    / "application_payload.json"
)

RESUME_DOCX = (
    ROOT_DIR
    / "outputs"
    / "resumes"
    / "Jerin_Ray_Data_Scientist_Tailored.docx"
)

RESUME_PDF = (
    ROOT_DIR
    / "outputs"
    / "resumes"
    / "Jerin_Ray_Data_Scientist_Tailored.pdf"
)

COVER_LETTER_DOCX = (
    ROOT_DIR
    / "outputs"
    / "cover_letters"
    / "Jerin_Ray_Data_Scientist_Cover_Letter.docx"
)

COVER_LETTER_PDF = (
    ROOT_DIR
    / "outputs"
    / "cover_letters"
    / "Jerin_Ray_Data_Scientist_Cover_Letter.pdf"
)


# =========================================================
# LOAD JSON
# =========================================================

def load_json(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


# =========================================================
# NAME PARSER
# =========================================================

def split_candidate_name(full_name):

    parts = str(full_name or "").strip().split()

    if not parts:
        return {
            "first_name": None,
            "middle_name": None,
            "last_name": None,
        }

    if len(parts) == 1:
        return {
            "first_name": parts[0],
            "middle_name": None,
            "last_name": None,
        }

    if len(parts) == 2:
        return {
            "first_name": parts[0],
            "middle_name": None,
            "last_name": parts[1],
        }

    return {
        "first_name": parts[0],
        "middle_name": " ".join(parts[1:-1]),
        "last_name": parts[-1],
    }


# =========================================================
# FILE CHECKS
# =========================================================

def get_file_status(path):

    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
    }


# =========================================================
# APPLICATION DATA PREPARATION
# =========================================================

def prepare_application_data(resume_data, cover_letter_data):

    candidate = resume_data.get("candidate", {})
    job = resume_data.get("target_job", {})

    name = candidate.get("name")
    email = candidate.get("email")
    phone = candidate.get("phone")
    linkedin = candidate.get("linkedin")

    name_parts = split_candidate_name(name)

    resume_files = {
        "docx": get_file_status(RESUME_DOCX),
        "pdf": get_file_status(RESUME_PDF),
    }

    cover_letter_files = {
        "docx": get_file_status(COVER_LETTER_DOCX),
        "pdf": get_file_status(COVER_LETTER_PDF),
    }

    # -----------------------------------------------------
    # Candidate information
    # -----------------------------------------------------

    candidate_data = {
        "full_name": name,
        "first_name": name_parts["first_name"],
        "middle_name": name_parts["middle_name"],
        "last_name": name_parts["last_name"],
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "portfolio": None,
        "github": None,
        "address": None,
        "city": None,
        "state": None,
        "country": None,
        "postal_code": None,
        "date_of_birth": None,
        "work_authorization": None,
        "visa_sponsorship_required": None,
        "years_of_experience": None,
        "notice_period": None,
        "current_salary": None,
        "expected_salary": None,
    }

    # -----------------------------------------------------
    # Education
    # -----------------------------------------------------

    education = resume_data.get("education", [])

    # -----------------------------------------------------
    # Skills and projects
    # -----------------------------------------------------

    skills = resume_data.get("technical_skills", [])
    projects = resume_data.get("projects", [])

    # -----------------------------------------------------
    # Application documents
    # -----------------------------------------------------

    documents = {
        "resume": resume_files,
        "cover_letter": cover_letter_files,
    }

    # -----------------------------------------------------
    # Missing required information
    # -----------------------------------------------------

    required_fields = {
        "full_name": candidate_data["full_name"],
        "email": candidate_data["email"],
        "phone": candidate_data["phone"],
        "resume_pdf": resume_files["pdf"]["exists"],
    }

    missing_fields = [
        field
        for field, value in required_fields.items()
        if not value
    ]

    # -----------------------------------------------------
    # Application readiness
    # -----------------------------------------------------

    manual_review_reasons = []

    if missing_fields:
        manual_review_reasons.append(
            "Some candidate or application fields are missing."
        )

    if not resume_files["pdf"]["exists"]:
        manual_review_reasons.append(
            "Resume PDF file is unavailable."
        )

    if not cover_letter_files["pdf"]["exists"]:
        manual_review_reasons.append(
            "Cover letter PDF file is unavailable."
        )

    if cover_letter_data.get("manual_review_required"):
        manual_review_reasons.append(
            "Job description requires manual verification."
        )

    if not job.get("application_url"):
        manual_review_reasons.append(
            "Application URL is unavailable."
        )

    # -----------------------------------------------------
    # Form field mapping
    # -----------------------------------------------------

    form_mapping = {
        "first_name": candidate_data["first_name"],
        "middle_name": candidate_data["middle_name"],
        "last_name": candidate_data["last_name"],
        "full_name": candidate_data["full_name"],
        "email": candidate_data["email"],
        "phone": candidate_data["phone"],
        "linkedin_url": candidate_data["linkedin"],
        "portfolio_url": candidate_data["portfolio"],
        "github_url": candidate_data["github"],
        "resume": str(RESUME_PDF),
        "cover_letter": str(COVER_LETTER_PDF),
    }

    # -----------------------------------------------------
    # Final payload
    # -----------------------------------------------------

    payload = {
        "project": "AI-JobPilot",
        "generated_date": date.today().isoformat(),

        "application_status": "PREPARED_NOT_SUBMITTED",

        "candidate": candidate_data,

        "target_job": {
            "job_id": job.get("job_id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "work_mode": job.get("work_mode"),
            "employment_type": job.get("employment_type"),
            "application_url": job.get("application_url"),
        },

        "education": education,
        "technical_skills": skills,
        "projects": projects,

        "documents": documents,

        "form_field_mapping": form_mapping,

        "missing_fields": missing_fields,

        "manual_review": {
            "required": bool(manual_review_reasons),
            "reasons": manual_review_reasons,
        },

        "submission": {
            "submitted": False,
            "submission_timestamp": None,
            "confirmation_id": None,
            "human_approval_required": True,
        },

        "data_integrity": {
            "unknown_fields_left_blank": True,
            "candidate_information_invented": False,
            "application_submitted_automatically": False,
        },
    }

    return payload


# =========================================================
# SAVE PAYLOAD
# =========================================================

def save_payload(payload):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            payload,
            file,
            indent=4,
            ensure_ascii=False,
        )


# =========================================================
# VALIDATE PAYLOAD
# =========================================================

def validate_payload(payload):

    assert payload["candidate"]["full_name"], (
        "Candidate name is missing."
    )

    assert payload["candidate"]["email"], (
        "Candidate email is missing."
    )

    assert payload["application_status"] == "PREPARED_NOT_SUBMITTED"

    assert payload["submission"]["submitted"] is False

    assert payload["submission"]["human_approval_required"] is True

    assert payload["data_integrity"]["candidate_information_invented"] is False

    assert payload["target_job"]["title"], (
        "Target job title is missing."
    )

    assert payload["documents"]["resume"]["pdf"]["exists"], (
        "Resume PDF is unavailable."
    )

    assert payload["documents"]["cover_letter"]["pdf"]["exists"], (
        "Cover letter PDF is unavailable."
    )

    return True


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("AI-JOBPILOT - DAY 10")
    print("APPLICATION DATA PREPARATION")
    print("=" * 60)

    print("\n[1/5] Loading tailored resume...")
    resume_data = load_json(RESUME_DATA_FILE)

    print("[2/5] Loading generated cover letter...")
    cover_letter_data = load_json(COVER_LETTER_FILE)

    print("[3/5] Preparing application information...")
    payload = prepare_application_data(
        resume_data,
        cover_letter_data,
    )

    print("[4/5] Saving application payload...")
    save_payload(payload)

    print("[5/5] Validating application payload...")
    validate_payload(payload)

    print("\n" + "=" * 60)
    print("APPLICATION DATA PREPARATION SUCCESSFUL")
    print("=" * 60)

    print("\nCandidate:", payload["candidate"]["full_name"])
    print("Email:", payload["candidate"]["email"])

    print(
        "Target job:",
        payload["target_job"]["title"],
    )

    print(
        "Company:",
        payload["target_job"]["company"],
    )

    print(
        "Missing fields:",
        len(payload["missing_fields"]),
    )

    for field in payload["missing_fields"]:
        print(" -", field)

    print(
        "\nManual review required:",
        payload["manual_review"]["required"],
    )

    for reason in payload["manual_review"]["reasons"]:
        print(" -", reason)

    print("\nApplication status:", payload["application_status"])

    print("\nOutput file:")
    print(OUTPUT_FILE)

    print("\nApplication has NOT been submitted.")
    print("Human approval is required before submission.")

    print("\nDAY 10 APPLICATION DATA MODULE COMPLETED")


if __name__ == "__main__":
    main()
