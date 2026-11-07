
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]

PAYLOAD_FILE = ROOT_DIR / "data/processed/application_payload.json"
MAPPING_FILE = ROOT_DIR / "data/processed/application_field_mapping.json"
OUTPUT_FILE = ROOT_DIR / "data/processed/application_safety_report.json"


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_path(value):
    """Extract a file path from strings or nested document dictionaries."""

    if isinstance(value, str):
        return value.strip() or None

    if isinstance(value, dict):
        # Prefer PDF, then DOCX
        for key in ["pdf", "docx", "path", "file_path",
                    "filepath", "absolute_path", "local_path"]:
            if key in value:
                result = extract_path(value[key])
                if result:
                    return result

    return None


def check_document(value):
    path_value = extract_path(value)

    if not path_value:
        return False

    path = Path(path_value).expanduser()

    if not path.is_absolute():
        path = ROOT_DIR / path

    return path.exists() and path.is_file()


def get_list(value):
    """Return a list safely, including lists nested in dictionaries."""

    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        for key in ["fields", "items", "questions", "reasons"]:
            if isinstance(value.get(key), list):
                return value[key]

    return []


def validate_application(payload, mapping):

    checks = []
    blockers = []
    warnings = []

    candidate = payload.get("candidate", {})
    documents = payload.get("documents", {})

    if not isinstance(candidate, dict):
        candidate = {}

    if not isinstance(documents, dict):
        documents = {}

    # 1. Candidate information
    full_name = candidate.get("full_name")
    email = candidate.get("email")

    for field, value in [
        ("candidate_name", full_name),
        ("candidate_email", email)
    ]:
        passed = bool(value and str(value).strip())

        checks.append({
            "check": field,
            "passed": passed
        })

        if not passed:
            blockers.append(f"{field.replace('_', ' ').title()} is missing.")

    # 2. Documents
    resume_exists = check_document(documents.get("resume"))
    cover_letter_exists = check_document(
        documents.get("cover_letter")
    )

    checks.extend([
        {
            "check": "resume_file_exists",
            "passed": resume_exists
        },
        {
            "check": "cover_letter_file_exists",
            "passed": cover_letter_exists
        }
    ])

    if not resume_exists:
        blockers.append("Resume file is missing or inaccessible.")

    if not cover_letter_exists:
        warnings.append(
            "Cover letter file is missing or inaccessible."
        )

    # 3. Field mapping results
    ready_fields = get_list(mapping.get("ready_to_fill"))
    manual_fields = get_list(mapping.get("manual_review_required"))
    unmapped_fields = get_list(mapping.get("unmapped_fields"))
    captcha_fields = get_list(
        mapping.get("captcha_protected_fields")
    )

    # Use the mapper's reported counts if available
    ready_count = mapping.get(
        "ready_to_fill_count", len(ready_fields)
    )
    manual_count = mapping.get(
        "manual_review_count", len(manual_fields)
    )
    unmapped_count = mapping.get(
        "unmapped_count", len(unmapped_fields)
    )
    captcha_count = mapping.get(
        "captcha_protected_count", len(captcha_fields)
    )

    if manual_count:
        warnings.append(
            f"{manual_count} application fields require human review."
        )

    if unmapped_count:
        warnings.append(
            f"{unmapped_count} application fields are unmapped."
        )

    checks.append({
        "check": "manual_review_requirements_identified",
        "passed": manual_count == 0 or bool(
            mapping.get("manual_review_required")
        )
    })

    # 4. CAPTCHA protection
    captcha_detected = captcha_count > 0

    checks.append({
        "check": "captcha_not_detected",
        "passed": not captcha_detected
    })

    if captcha_detected:
        blockers.append(
            "CAPTCHA detected. Application automation is blocked "
            "until a human completes the verification."
        )

    # 5. Human approval safeguard
    human_approval_required = (
        mapping.get("human_approval_required") is True
    )

    checks.append({
        "check": "human_approval_required",
        "passed": human_approval_required
    })

    if not human_approval_required:
        blockers.append(
            "Human approval safeguard is not enabled."
        )

    # 6. Submission state
    submission_info = payload.get("submission", {})
    if not isinstance(submission_info, dict):
        submission_info = {}

    already_submitted = (
        mapping.get("submission_performed", False) is True
        or payload.get("submission_performed", False) is True
        or submission_info.get("performed", False) is True
    )

    checks.append({
        "check": "application_not_already_submitted",
        "passed": not already_submitted
    })

    if already_submitted:
        blockers.append(
            "Application is marked as already submitted."
        )

    # 7. Final decision
    safe_for_human_review = len(blockers) == 0

    return {
        "project": "AI-JobPilot",
        "validation_status": (
            "READY_FOR_HUMAN_REVIEW"
            if safe_for_human_review
            else "BLOCKED"
        ),
        "safe_for_human_review": safe_for_human_review,
        "submission_authorized": False,
        "submission_performed": False,
        "human_approval_required": True,
        "captcha_bypass_attempted": False,
        "summary": {
            "checks_passed": sum(
                1 for item in checks if item["passed"]
            ),
            "checks_failed": sum(
                1 for item in checks if not item["passed"]
            ),
            "blockers": len(blockers),
            "warnings": len(warnings),
            "ready_fields": ready_count,
            "manual_review_fields": manual_count,
            "unmapped_fields": unmapped_count,
            "captcha_fields": captcha_count
        },
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings
    }


def main():

    print("=" * 65)
    print("AI-JOBPILOT - APPLICATION SAFETY VALIDATOR")
    print("=" * 65)

    payload = load_json(PAYLOAD_FILE)
    mapping = load_json(MAPPING_FILE)

    report = validate_application(payload, mapping)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\nVALIDATION RESULTS")
    print("-" * 65)

    print("Candidate:", payload.get("candidate", {}).get("full_name"))
    print("Status:", report["validation_status"])
    print("Safe for human review:", report["safe_for_human_review"])
    print("Submission authorized:", report["submission_authorized"])
    print("Submission performed:", report["submission_performed"])

    print("\nSUMMARY")
    for key, value in report["summary"].items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    if report["blockers"]:
        print("\nBLOCKERS")
        for item in report["blockers"]:
            print("-", item)

    if report["warnings"]:
        print("\nWARNINGS")
        for item in report["warnings"]:
            print("-", item)

    print("\nOutput:", OUTPUT_FILE)
    print("\nNo application was submitted.")
    print("SAFETY VALIDATION COMPLETED")


if __name__ == "__main__":
    main()
