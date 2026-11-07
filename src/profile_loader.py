
import json
from pathlib import Path


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Candidate profile location
PROFILE_PATH = BASE_DIR / "config" / "candidate_profile.json"


def load_candidate_profile():
    """Load candidate information from JSON."""

    if not PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"Candidate profile not found: {PROFILE_PATH}"
        )

    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as file:
            profile = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON profile: {error}"
        ) from error

    validate_profile(profile)

    return profile


def validate_profile(profile):
    """Validate the candidate profile structure."""

    required_sections = [
        "personal_information",
        "education",
        "career_preferences",
        "technical_skills",
        "experience",
        "projects",
        "certifications"
    ]

    if not isinstance(profile, dict):
        raise ValueError("Profile must be a JSON object.")

    for section in required_sections:
        if section not in profile:
            raise ValueError(
                f"Missing profile section: {section}"
            )

    personal = profile["personal_information"]

    if not isinstance(personal, dict):
        raise ValueError("Personal information must be an object.")

    if not personal.get("full_name"):
        raise ValueError("Candidate name is missing.")

    if not profile["career_preferences"].get("preferred_roles"):
        raise ValueError("Preferred job roles are missing.")

    print("Profile validation successful!")


def display_profile_summary(profile):
    """Display a basic candidate profile summary."""

    personal = profile["personal_information"]
    preferences = profile["career_preferences"]
    skills = profile["technical_skills"]

    total_skills = sum(
        len(skill_list)
        for skill_list in skills.values()
        if isinstance(skill_list, list)
    )

    print("\n" + "=" * 45)
    print("       AI JOBPILOT - CANDIDATE PROFILE")
    print("=" * 45)

    print(f"Candidate: {personal['full_name']}")
    print(f"Location: {personal.get('location', 'Not specified')}")

    print("\nPreferred Job Roles:")

    for role in preferences["preferred_roles"]:
        print(f" - {role}")

    print(f"\nTotal Technical Skills: {total_skills}")

    print("\nProfile loaded successfully!")
    print("=" * 45)


if __name__ == "__main__":

    try:
        candidate = load_candidate_profile()
        display_profile_summary(candidate)

    except (ValueError, FileNotFoundError) as error:
        print(f"\nERROR: {error}")
