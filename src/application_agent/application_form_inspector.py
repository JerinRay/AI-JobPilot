
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PAYLOAD_PATH = PROJECT_ROOT / "data/processed/application_payload.json"
OUTPUT_PATH = PROJECT_ROOT / "data/processed/application_form_schema.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    )
}

TIMEOUT = 20

SENSITIVE_KEYWORDS = (
    "password",
    "social_security",
    "ssn",
    "credit_card",
)


def load_payload():
    if not PAYLOAD_PATH.exists():
        raise FileNotFoundError(
            f"Payload not found: {PAYLOAD_PATH}"
        )

    with PAYLOAD_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_url(url):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    return url


def fetch_page(url):
    response = requests.get(
        validate_url(url),
        headers=HEADERS,
        timeout=TIMEOUT,
        allow_redirects=True,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type", ""
    ).lower()

    if "html" not in content_type:
        raise ValueError(
            f"Expected HTML but received: {content_type}"
        )

    return response, BeautifulSoup(response.text, "html.parser")


def find_real_application_link(soup, listing_url):
    candidates = []

    for anchor in soup.find_all("a", href=True):
        text = anchor.get_text(" ", strip=True)
        href = anchor.get("href", "")

        absolute_url = urljoin(listing_url, href)
        parsed = urlparse(absolute_url)

        if parsed.scheme not in ("http", "https"):
            continue

        path = parsed.path.rstrip("/").lower()
        text_lower = text.lower()

        # Prefer an explicit Apply Now link or an /apply route.
        is_apply_route = (
            path.endswith("/apply")
            or path.endswith("/application")
        )

        is_apply_text = (
            text_lower == "apply now"
            or text_lower == "apply"
            or text_lower.startswith("apply for ")
        )

        # Ignore blog links and unrelated pages.
        if is_apply_route or is_apply_text:
            candidates.append({
                "text": text,
                "url": absolute_url,
                "domain": parsed.netloc,
                "route_match": is_apply_route,
            })

    # Prefer a URL with an explicit application route.
    candidates.sort(
        key=lambda item: item["route_match"],
        reverse=True,
    )

    unique = []
    seen = set()

    for candidate in candidates:
        if candidate["url"] not in seen:
            seen.add(candidate["url"])
            unique.append(candidate)

    return unique


def get_field_label(element, soup):
    element_id = element.get("id")

    if element_id:
        label = soup.find("label", attrs={"for": element_id})

        if label:
            return label.get_text(" ", strip=True)

    parent_label = element.find_parent("label")

    if parent_label:
        return parent_label.get_text(" ", strip=True)

    return (
        element.get("aria-label")
        or element.get("placeholder")
        or element.get("name")
        or ""
    )


def inspect_forms(soup):
    forms = []

    for index, form in enumerate(soup.find_all("form"), start=1):
        fields = []

        elements = form.find_all(
            ["input", "textarea", "select", "button"]
        )

        for element in elements:
            field_type = (
                element.get("type") or element.name
            ).lower()

            name = element.get("name", "")
            element_id = element.get("id", "")

            combined = (
                f"{name} {element_id} {field_type}"
            ).lower()

            sensitive = any(
                keyword in combined
                for keyword in SENSITIVE_KEYWORDS
            )

            options = []

            if element.name == "select":
                options = [
                    option.get_text(" ", strip=True)
                    for option in element.find_all("option")
                    if option.get_text(" ", strip=True)
                ]

            fields.append({
                "tag": element.name,
                "type": field_type,
                "name": name,
                "id": element_id,
                "label": get_field_label(element, soup),
                "placeholder": element.get("placeholder", ""),
                "required": element.has_attr("required"),
                "options": options,
                "sensitive_field": sensitive,
            })

        forms.append({
            "form_number": index,
            "method": form.get("method", "get").lower(),
            "action": form.get("action", ""),
            "field_count": len(fields),
            "fields": fields,
        })

    return forms


def inspect_page(url):
    result = {
        "requested_url": url,
        "final_url": None,
        "page_title": None,
        "http_status": None,
        "page_accessible": False,
        "forms": [],
        "warnings": [],
    }

    try:
        response, soup = fetch_page(url)

        result["http_status"] = response.status_code
        result["final_url"] = response.url
        result["page_accessible"] = True

        if soup.title:
            result["page_title"] = soup.title.get_text(
                " ",
                strip=True,
            )

        result["forms"] = inspect_forms(soup)

        if not result["forms"]:
            result["warnings"].append(
                "No HTML forms detected. The page may use "
                "JavaScript-rendered application fields."
            )

    except (requests.RequestException, ValueError) as error:
        result["warnings"].append(str(error))

    return result


def save_result(data):
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )


def main():
    print("=" * 65)
    print("AI-JOBPILOT - APPLICATION WORKFLOW INSPECTOR")
    print("=" * 65)

    payload = load_payload()

    listing_url = payload.get(
        "target_job", {}
    ).get("application_url")

    if not listing_url:
        raise ValueError("Job listing URL is missing.")

    print("\nSTEP 1: INSPECTING JOB LISTING")

    listing_result = inspect_page(listing_url)

    print("HTTP Status:", listing_result["http_status"])
    print("Page Title:", listing_result["page_title"])

    application_url = None
    possible_links = []

    if listing_result["page_accessible"]:
        _, listing_soup = fetch_page(listing_result["final_url"])

        possible_links = find_real_application_link(
            listing_soup,
            listing_result["final_url"],
        )

    print("\nSTEP 2: FINDING APPLICATION LINK")
    print("Valid application links:", len(possible_links))

    for link in possible_links:
        print("-", link["text"], "|", link["url"])

    if possible_links:
        application_url = possible_links[0]["url"]

    application_result = None

    if application_url:
        print("\nSTEP 3: INSPECTING ACTUAL APPLICATION PAGE")

        application_result = inspect_page(application_url)

        print("HTTP Status:", application_result["http_status"])
        print("Page Accessible:", application_result["page_accessible"])
        print("Page Title:", application_result["page_title"])
        print("Forms Found:", len(application_result["forms"]))

        for form in application_result["forms"]:
            print(
                f"\nForm {form['form_number']}: "
                f"{form['field_count']} fields"
            )

            for field in form["fields"]:
                print(
                    f"  {field['tag']} | "
                    f"{field['type']} | "
                    f"{field['name']} | "
                    f"{field['label']} | "
                    f"Required: {field['required']}"
                )

        for warning in application_result["warnings"]:
            print("WARNING:", warning)

    else:
        print("\nNo genuine application link found.")
        print("Manual verification is required.")

    output = {
        "inspection_time": datetime.now(
            timezone.utc
        ).isoformat(),
        "candidate": payload.get("candidate", {}).get(
            "full_name"
        ),
        "job_listing": listing_result,
        "possible_application_links": possible_links,
        "selected_application_url": application_url,
        "application_page": application_result,
        "submission_performed": False,
        "human_approval_required": True,
    }

    save_result(output)

    print("\n" + "=" * 65)
    print("INSPECTION SUMMARY")
    print("=" * 65)
    print("Application URL:", application_url)
    print(
        "Application page accessible:",
        application_result["page_accessible"]
        if application_result else False,
    )
    print(
        "Application forms:",
        len(application_result["forms"])
        if application_result else 0,
    )
    print("Submission performed: False")
    print("Human approval required: True")
    print("Saved:", OUTPUT_PATH)
    print("\nDAY 11 STEP 3 COMPLETED")


if __name__ == "__main__":
    main()
