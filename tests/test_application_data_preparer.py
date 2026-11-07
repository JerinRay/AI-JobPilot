
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.application_agent import application_data_preparer as preparer


class TestApplicationDataPreparer(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)

        self.resume_docx = self.base / "resume.docx"
        self.resume_pdf = self.base / "resume.pdf"
        self.cover_docx = self.base / "cover.docx"
        self.cover_pdf = self.base / "cover.pdf"

        for path in [
            self.resume_docx,
            self.resume_pdf,
            self.cover_docx,
            self.cover_pdf,
        ]:
            path.write_text("test document", encoding="utf-8")

        self.resume_data = {
            "candidate": {
                "name": "JERIN RAY",
                "email": "jerryviswaraj@gmail.com",
                "phone": None,
                "linkedin": "linkedin.com/in/jerin-ray-viswaraj-a290bb36a",
            },
            "target_job": {
                "job_id": 21,
                "title": "Data Scientist",
                "company": "Test Company",
                "location": "Berlin, Germany",
                "work_mode": "On-site",
                "employment_type": "Full-Time",
                "application_url": "https://example.com/apply",
            },
            "education": [],
            "technical_skills": ["Python", "SQL"],
            "projects": [],
        }

        self.cover_data = {
            "manual_review_required": True
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def prepare(self):

        with (
            patch.object(preparer, "RESUME_DOCX", self.resume_docx),
            patch.object(preparer, "RESUME_PDF", self.resume_pdf),
            patch.object(preparer, "COVER_LETTER_DOCX", self.cover_docx),
            patch.object(preparer, "COVER_LETTER_PDF", self.cover_pdf),
        ):
            return preparer.prepare_application_data(
                self.resume_data,
                self.cover_data,
            )

    def test_name_split(self):

        result = preparer.split_candidate_name("JERIN RAY")

        self.assertEqual(result["first_name"], "JERIN")
        self.assertEqual(result["last_name"], "RAY")

    def test_candidate_email(self):

        payload = self.prepare()

        self.assertEqual(
            payload["candidate"]["email"],
            "jerryviswaraj@gmail.com",
        )

    def test_missing_phone_is_reported(self):

        payload = self.prepare()

        self.assertIn("phone", payload["missing_fields"])

    def test_documents_are_detected(self):

        payload = self.prepare()

        self.assertTrue(
            payload["documents"]["resume"]["pdf"]["exists"]
        )

        self.assertTrue(
            payload["documents"]["cover_letter"]["pdf"]["exists"]
        )

    def test_manual_review_is_required(self):

        payload = self.prepare()

        self.assertTrue(
            payload["manual_review"]["required"]
        )

    def test_application_is_not_submitted(self):

        payload = self.prepare()

        self.assertFalse(
            payload["submission"]["submitted"]
        )

        self.assertEqual(
            payload["application_status"],
            "PREPARED_NOT_SUBMITTED",
        )

    def test_unknown_information_is_not_invented(self):

        payload = self.prepare()

        self.assertIsNone(
            payload["candidate"]["phone"]
        )

        self.assertIsNone(
            payload["candidate"]["address"]
        )

        self.assertFalse(
            payload["data_integrity"]["candidate_information_invented"]
        )


if __name__ == "__main__":
    unittest.main()
