
import unittest
from unittest.mock import patch

from src.application_agent.application_safety_validator import (
    validate_application
)


class TestApplicationSafetyValidator(unittest.TestCase):

    def setUp(self):
        self.payload = {
            "candidate": {
                "full_name": "JERIN RAY",
                "email": "jerryviswaraj@gmail.com"
            },
            "documents": {
                "resume": {
                    "pdf": "/fake/resume.pdf",
                    "docx": "/fake/resume.docx"
                },
                "cover_letter": {
                    "pdf": "/fake/cover_letter.pdf",
                    "docx": "/fake/cover_letter.docx"
                }
            },
            "submission": {
                "performed": False
            }
        }

        self.mapping = {
            "ready_to_fill": [
                {"field_name": "name"},
                {"field_name": "email"},
                {"field_name": "resume"},
                {"field_name": "linkedin"}
            ],
            "ready_to_fill_count": 4,
            "manual_review_required": [
                {"field_name": "gender"},
                {"field_name": "location"}
            ],
            "manual_review_count": 2,
            "unmapped_fields": [
                {"field_name": "other_url"}
            ],
            "unmapped_count": 1,
            "captcha_protected_fields": [],
            "captcha_protected_count": 0,
            "human_approval_required": True,
            "submission_performed": False
        }

    def run_validation(self):
        with patch(
            "src.application_agent.application_safety_validator.check_document",
            return_value=True
        ):
            return validate_application(self.payload, self.mapping)

    def test_valid_candidate_details(self):
        report = self.run_validation()

        self.assertTrue(
            next(
                item["passed"]
                for item in report["checks"]
                if item["check"] == "candidate_name"
            )
        )

        self.assertTrue(
            next(
                item["passed"]
                for item in report["checks"]
                if item["check"] == "candidate_email"
            )
        )

    def test_missing_candidate_name(self):
        self.payload["candidate"]["full_name"] = None

        report = self.run_validation()

        self.assertFalse(report["safe_for_human_review"])
        self.assertTrue(
            any("name" in blocker.lower()
                for blocker in report["blockers"])
        )

    def test_missing_resume(self):
        with patch(
            "src.application_agent.application_safety_validator.check_document",
            side_effect=[False, True]
        ):
            report = validate_application(
                self.payload,
                self.mapping
            )

        self.assertFalse(report["safe_for_human_review"])
        self.assertTrue(
            any("resume" in blocker.lower()
                for blocker in report["blockers"])
        )

    def test_captcha_blocks_validation(self):
        self.mapping["captcha_protected_fields"] = [
            {"field_name": "h-captcha-response"}
        ]
        self.mapping["captcha_protected_count"] = 1

        report = self.run_validation()

        self.assertEqual(report["validation_status"], "BLOCKED")
        self.assertFalse(report["submission_authorized"])

    def test_human_approval_is_mandatory(self):
        self.mapping["human_approval_required"] = False

        report = self.run_validation()

        self.assertFalse(report["safe_for_human_review"])
        self.assertTrue(
            any("approval" in blocker.lower()
                for blocker in report["blockers"])
        )

    def test_submission_is_never_authorized(self):
        report = self.run_validation()

        self.assertFalse(report["submission_authorized"])
        self.assertFalse(report["submission_performed"])

    def test_manual_review_fields_are_counted(self):
        report = self.run_validation()

        self.assertEqual(
            report["summary"]["manual_review_fields"],
            2
        )

    def test_unmapped_fields_are_counted(self):
        report = self.run_validation()

        self.assertEqual(
            report["summary"]["unmapped_fields"],
            1
        )

    def test_captcha_bypass_is_never_attempted(self):
        report = self.run_validation()

        self.assertFalse(report["captcha_bypass_attempted"])


if __name__ == "__main__":
    unittest.main()
