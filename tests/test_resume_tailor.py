
import json
import unittest
from pathlib import Path

from src.resume_intelligence.resume_tailor import (
    load_json,
    extract_required_skills,
    compare_candidate_skills,
    extract_individual_projects,
    build_tailored_resume,
    RESUME_FILE,
    OUTPUT_FILE,
)


class TestResumeTailor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.resume = load_json(RESUME_FILE)

    def test_job_required_skills(self):
        description = "Requirements: Python SQL C++"

        skills = extract_required_skills(description)

        self.assertEqual(
            skills,
            ["Python", "SQL", "C++"]
        )

    def test_candidate_skill_matching(self):
        required = ["Python", "SQL", "C++"]
        candidate = self.resume.get("skills", [])

        matched, missing = compare_candidate_skills(
            required,
            candidate
        )

        self.assertEqual(len(matched), 3)
        self.assertEqual(missing, [])

    def test_project_count(self):
        projects = extract_individual_projects(self.resume)

        self.assertEqual(len(projects), 2)

    def test_project_descriptions_are_separate(self):
        projects = extract_individual_projects(self.resume)

        radar = projects[0]["description"].lower()
        analytics = projects[1]["description"].lower()

        self.assertNotIn("predictive data analytics", radar)

        self.assertNotIn(
            "high-fidelity spatiotemporal radar nowcasting system",
            analytics
        )

    def test_project_descriptions_are_not_empty(self):
        projects = extract_individual_projects(self.resume)

        for project in projects:
            self.assertTrue(project["description"].strip())

    def test_original_project_titles_preserved(self):
        projects = extract_individual_projects(self.resume)

        titles = [project["title"] for project in projects]

        self.assertEqual(
            titles,
            self.resume["projects"]["titles"]
        )

    def test_no_invented_information(self):
        result = build_tailored_resume(job_id=21)

        integrity = result["integrity_checks"]

        self.assertFalse(integrity["invented_skills_added"])
        self.assertFalse(integrity["invented_experience_added"])
        self.assertFalse(integrity["invented_certifications_added"])

    def test_output_json_created(self):
        self.assertTrue(OUTPUT_FILE.exists())

        with OUTPUT_FILE.open("r", encoding="utf-8") as file:
            result = json.load(file)

        self.assertEqual(
            result["target_job"]["job_id"],
            21
        )

    def test_candidate_identity_preserved(self):
        result = build_tailored_resume(job_id=21)

        self.assertEqual(
            result["candidate"]["name"],
            self.resume["candidate_name"]
        )

        self.assertEqual(
            result["candidate"]["email"],
            self.resume["email"]
        )

    def test_missing_skills_are_not_added_to_candidate_skills(self):
        result = build_tailored_resume(job_id=21)

        missing = result["skill_match_analysis"]["missing_skills"]
        selected = [
            skill.lower()
            for skill in result["technical_skills"]
        ]

        for skill in missing:
            self.assertNotIn(skill.lower(), selected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
