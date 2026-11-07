
import json
from pathlib import Path
from collections import OrderedDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PAYLOAD_PATH = PROJECT_ROOT / "data/processed/application_payload.json"
SCHEMA_PATH = PROJECT_ROOT / "data/processed/application_form_schema.json"
OUTPUT_PATH = PROJECT_ROOT / "data/processed/application_field_mapping.json"

RESUME_PATH = (
    PROJECT_ROOT
    / "outputs/resumes/Jerin_Ray_Data_Scientist_Tailored.pdf"
)
COVER_LETTER_PATH = (
    PROJECT_ROOT
    / "outputs/cover_letters/Jerin_Ray_Data_Scientist_Cover_Letter.pdf"
)


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_candidate_value(candidate, keys):
    for key in keys:
        value = candidate.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def get_fields(schema):
    application_page = schema.get("application_page") or {}
    forms = application_page.get("forms") or []

    return [
        field
        for form in forms
        for field in form.get("fields", [])
    ]


def group_fields(fields):
    """
    Group radio/checkbox choices only when they share a non-empty name.
    Unnamed controls remain individual fields to avoid accidental grouping.
    """

    groups = OrderedDict()

    for index, field in enumerate(fields):
        name = (field.get("name") or "").strip()
        field_type = (field.get("type") or "").lower().strip()
        field_id = (field.get("id") or "").strip()

        if field_type in ("radio", "checkbox") and name:
            key = ("choice_group", field_type, name)

        elif field_type == "select" and (name or field_id):
            key = ("select", name or field_id)

        else:
            key = (
                "individual",
                field_type,
                name or field_id or f"unnamed_{index}"
            )

        if key not in groups:
            groups[key] = {
                "name": name,
                "type": field_type,
                "label": field.get("label", ""),
                "required": bool(field.get("required", False)),
                "options": [],
                "elements": [],
            }

        group = groups[key]

        if field.get("label") and not group["label"]:
            group["label"] = field["label"]

        group["required"] = (
            group["required"] or bool(field.get("required", False))
        )

        group["elements"].append(field)

        for option in field.get("options", []):
            if option and option not in group["options"]:
                group["options"].append(option)

        if field_type in ("radio", "checkbox"):
            option_label = (field.get("label") or "").strip()

            if option_label and option_label not in group["options"]:
                group["options"].append(option_label)

    result = []

    for group in groups.values():
        group["element_count"] = len(group["elements"])
        result.append(group)

    return result


def classify_field(field):
    name = (field.get("name") or "").lower()
    label = (field.get("label") or "").lower()
    field_type = (field.get("type") or "").lower()
    field_id = " ".join(
        (element.get("id") or "").lower()
        for element in field.get("elements", [])
    )

    combined = f"{name} {label} {field_id}"

    # CAPTCHA must be checked before hidden-field handling.
    captcha_terms = (
        "captcha",
        "h-captcha",
        "hcaptcha",
        "g-recaptcha",
        "recaptcha",
    )

    if any(term in combined for term in captcha_terms):
        return "CAPTCHA_PROTECTED"

    if field_type in ("submit", "button"):
        return "IGNORE"

    if field_type == "hidden":
        return "IGNORE"

    if "resume" in combined or "cv" in combined:
        return "RESUME_UPLOAD"

    if "cover letter" in combined or "cover_letter" in combined:
        return "COVER_LETTER_UPLOAD"

    if name == "name" or "full name" in label:
        return "FULL_NAME"

    if name in ("email", "emailaddress") or field_type == "email":
        return "EMAIL"

    if name == "phone" or "phone number" in label:
        return "PHONE"

    if "linkedin" in combined:
        return "LINKEDIN"

    if "github" in combined:
        return "GITHUB"

    if "portfolio" in combined:
        return "PORTFOLIO"

    manual_terms = (
        "pronoun",
        "gender",
        "race",
        "ethnicity",
        "disability",
        "veteran",
        "age",
        "birth",
        "citizenship",
        "work authorization",
        "work_authorization",
        "visa",
        "location",
        "country",
        "education",
        "marketing",
        "consent",
        "signature",
        "survey",
    )

    if any(term in combined for term in manual_terms):
        return "MANUAL_REVIEW"

    if field_type in ("radio", "checkbox", "select"):
        return "MANUAL_REVIEW"

    return "UNMAPPED"


def build_mapping(payload, schema):
    candidate = payload.get("candidate", {})

    candidate_values = {
        "FULL_NAME": get_candidate_value(
            candidate, ["full_name", "name", "candidate_name"]
        ),
        "EMAIL": get_candidate_value(
            candidate, ["email", "email_address"]
        ),
        "PHONE": get_candidate_value(
            candidate, ["phone", "phone_number", "mobile"]
        ),
        "LINKEDIN": get_candidate_value(
            candidate, ["linkedin_url", "linkedin"]
        ),
        "GITHUB": get_candidate_value(
            candidate, ["github_url", "github"]
        ),
        "PORTFOLIO": get_candidate_value(
            candidate, ["portfolio_url", "portfolio"]
        ),
        "RESUME_UPLOAD": (
            str(RESUME_PATH) if RESUME_PATH.exists() else None
        ),
        "COVER_LETTER_UPLOAD": (
            str(COVER_LETTER_PATH)
            if COVER_LETTER_PATH.exists()
            else None
        ),
    }

    raw_fields = get_fields(schema)
    grouped_fields = group_fields(raw_fields)

    mappings = []
    ready = []
    manual = []
    unmapped = []
    ignored = []
    captcha_protected = []

    for field in grouped_fields:
        category = classify_field(field)

        entry = {
            "field_name": field["name"],
            "field_label": field["label"],
            "field_type": field["type"],
            "required": field["required"],
            "element_count": field["element_count"],
            "available_options": field["options"],
            "category": category,
            "value": None,
            "status": None,
        }

        if category == "CAPTCHA_PROTECTED":
            entry["status"] = "HUMAN_VERIFICATION_REQUIRED"
            captcha_protected.append(entry)

        elif category in candidate_values:
            value = candidate_values[category]
            entry["value"] = value

            if value:
                entry["status"] = "READY"
                ready.append(entry)
            else:
                entry["status"] = "MISSING_INFORMATION"

                if entry["required"]:
                    manual.append(entry)

        elif category == "MANUAL_REVIEW":
            entry["status"] = "USER_INPUT_REQUIRED"
            manual.append(entry)

        elif category == "UNMAPPED":
            entry["status"] = "UNMAPPED_FIELD"
            unmapped.append(entry)

        else:
            entry["status"] = "IGNORED"
            ignored.append(entry)

        mappings.append(entry)

    missing_documents = []

    if not RESUME_PATH.exists():
        missing_documents.append("Tailored resume PDF missing.")

    if not COVER_LETTER_PATH.exists():
        missing_documents.append("Cover letter PDF missing.")

    return {
        "candidate": candidate.get("full_name"),
        "application_url": schema.get("selected_application_url"),

        "total_detected_elements": len(raw_fields),
        "total_question_groups": len(grouped_fields),

        "ready_to_fill_count": len(ready),
        "manual_review_count": len(manual),
        "unmapped_count": len(unmapped),
        "ignored_count": len(ignored),
        "captcha_protected_count": len(captcha_protected),

        "mappings": mappings,
        "ready_to_fill": ready,
        "manual_review_required": manual,
        "unmapped_fields": unmapped,
        "ignored_fields": ignored,
        "captcha_protected_fields": captcha_protected,

        "missing_documents": missing_documents,

        "submission_performed": False,
        "human_approval_required": True,
        "captcha_bypass_attempted": False,
        "status": "PREPARED_FOR_HUMAN_REVIEW",
    }


def main():
    print("=" * 65)
    print("AI-JOBPILOT - INTELLIGENT APPLICATION FIELD MAPPER")
    print("=" * 65)

    payload = load_json(PAYLOAD_PATH)
    schema = load_json(SCHEMA_PATH)

    result = build_mapping(payload, schema)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    print("\nMAPPING RESULTS")
    print("-" * 65)

    print("Candidate:", result["candidate"])
    print("Detected elements:", result["total_detected_elements"])
    print("Question groups:", result["total_question_groups"])
    print("Ready to fill:", result["ready_to_fill_count"])
    print("Manual review:", result["manual_review_count"])
    print("Unmapped:", result["unmapped_count"])
    print("Ignored:", result["ignored_count"])
    print("CAPTCHA protected:", result["captcha_protected_count"])

    print("\nREADY FIELDS")

    for item in result["ready_to_fill"]:
        print(f"- {item['field_name']}: {item['value']}")

    print("\nMANUAL REVIEW QUESTIONS")

    for item in result["manual_review_required"]:
        print(
            f"- {item['field_name'] or item['field_label']} "
            f"| {item['field_label'][:80]} "
            f"| Options: {len(item['available_options'])}"
        )

    print("\nCAPTCHA PROTECTED FIELDS")

    for item in result["captcha_protected_fields"]:
        print(
            f"- {item['field_name'] or item['field_label']}"
        )

    print("\nMISSING DOCUMENTS")

    if result["missing_documents"]:
        for document in result["missing_documents"]:
            print("-", document)
    else:
        print("None")

    print("\nSubmission performed:", result["submission_performed"])
    print("Human approval required:", result["human_approval_required"])
    print("CAPTCHA bypass attempted:", result["captcha_bypass_attempted"])
    print("Output:", OUTPUT_PATH)

    print("\nFIELD MAPPING COMPLETED")


if __name__ == "__main__":
    main()
