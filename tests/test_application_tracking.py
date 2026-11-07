
import unittest

from sqlalchemy import select, delete

from database.db import SessionLocal
from src.job_matching.job_model import Job
from src.tracking.application_model import Application
from src.tracking.application_history_model import ApplicationHistory
from src.tracking.application_tracking_service import (
    create_application,
    update_application_status,
    record_application_failure,
    get_application_history,
    get_application_statistics,
)


class TestApplicationTracking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with SessionLocal() as db:
            job = db.scalar(
                select(Job).where(
                    Job.source == "tracking_test",
                    Job.source_job_id == "tracking-test-job-001",
                )
            )

            if job is None:
                job = Job(
                    source="tracking_test",
                    source_job_id="tracking-test-job-001",
                    title="Junior AI Engineer",
                    company="Test Company",
                    location="India",
                    description="Python and machine learning role.",
                    apply_url="https://example.com/test-job",
                )
                db.add(job)
                db.commit()
                db.refresh(job)

            cls.job_id = job.id

    def setUp(self):
        """Remove previous test application and its history."""

        with SessionLocal() as db:
            application = db.scalar(
                select(Application).where(
                    Application.job_id == self.job_id
                )
            )

            if application:
                db.execute(
                    delete(ApplicationHistory).where(
                        ApplicationHistory.application_id
                        == application.id
                    )
                )

                db.delete(application)
                db.commit()

    def test_create_application(self):
        application, created = create_application(
            self.job_id,
            "JERIN RAY",
        )

        self.assertTrue(created)
        self.assertEqual(application.status, "PREPARED")
        self.assertEqual(application.candidate_name, "JERIN RAY")

    def test_duplicate_application_prevention(self):
        first, created_first = create_application(
            self.job_id,
            "JERIN RAY",
        )

        second, created_second = create_application(
            self.job_id,
            "JERIN RAY",
        )

        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first.id, second.id)

    def test_status_update_and_history(self):
        application, _ = create_application(
            self.job_id,
            "JERIN RAY",
        )

        updated = update_application_status(
            application.id,
            "READY_FOR_REVIEW",
            "Candidate details reviewed.",
        )

        self.assertEqual(updated.status, "READY_FOR_REVIEW")

        history = get_application_history(application.id)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].new_status, "PREPARED")
        self.assertEqual(history[1].old_status, "PREPARED")
        self.assertEqual(history[1].new_status, "READY_FOR_REVIEW")

    def test_failure_and_retry_count(self):
        application, _ = create_application(
            self.job_id,
            "JERIN RAY",
        )

        failed = record_application_failure(
            application.id,
            "Test submission failure.",
        )

        self.assertEqual(failed.status, "FAILED")
        self.assertEqual(failed.retry_count, 1)
        self.assertEqual(
            failed.last_error,
            "Test submission failure.",
        )

        retried = update_application_status(
            application.id,
            "PREPARED",
            "Retry prepared after review.",
        )

        self.assertEqual(retried.status, "PREPARED")
        self.assertEqual(retried.retry_count, 1)
        self.assertIsNone(retried.last_error)

    def test_invalid_status_transition(self):
        application, _ = create_application(
            self.job_id,
            "JERIN RAY",
        )

        with self.assertRaises(ValueError):
            update_application_status(
                application.id,
                "OFFER_RECEIVED",
            )

    def test_application_statistics(self):
        create_application(
            self.job_id,
            "JERIN RAY",
        )

        statistics = get_application_statistics()

        self.assertGreaterEqual(statistics["TOTAL"], 1)
        self.assertGreaterEqual(statistics["PREPARED"], 1)


if __name__ == "__main__":
    unittest.main()
