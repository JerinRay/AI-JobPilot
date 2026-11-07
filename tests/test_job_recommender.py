
import unittest

from src.recommendation_engine.job_recommender import (
    classify_location,
    classify_fresher_eligibility,
    make_job_identity,
    build_role_groups,
    build_skill_recommendations,
)


class TestJobRecommender(unittest.TestCase):

    def test_india_location(self):
        self.assertEqual(
            classify_location("Chennai, India"),
            "india"
        )

    def test_india_remote_location(self):
        self.assertEqual(
            classify_location("Remote, India"),
            "india_remote"
        )

    def test_generic_remote_not_assumed_india(self):
        self.assertEqual(
            classify_location("Remote"),
            "remote_location_unverified"
        )

    def test_overseas_location(self):
        self.assertEqual(
            classify_location("Berlin, Germany"),
            "overseas"
        )

    def test_unknown_location(self):
        self.assertEqual(
            classify_location(""),
            "location_unclear"
        )

    def test_fresher_title(self):
        job = {
            "job_title": "Junior Python Developer",
            "eligibility_classification": "unclear_manual_verification",
            "fresher_signals": [],
            "experience_signals": [],
            "production_experience_required": False,
            "required_experience_years": None,
        }

        self.assertEqual(
            classify_fresher_eligibility(job),
            "potentially_fresher"
        )

    def test_experienced_role(self):
        job = {
            "job_title": "Senior AI Engineer",
            "eligibility_classification": "unclear_manual_verification",
            "fresher_signals": [],
            "experience_signals": [],
            "production_experience_required": False,
            "required_experience_years": None,
        }

        self.assertEqual(
            classify_fresher_eligibility(job),
            "likely_experienced"
        )

    def test_unclear_eligibility_requires_review(self):
        job = {
            "job_title": "AI Engineer",
            "eligibility_classification": "unclear_manual_verification",
            "fresher_signals": [],
            "experience_signals": [],
            "production_experience_required": False,
            "required_experience_years": None,
        }

        self.assertEqual(
            classify_fresher_eligibility(job),
            "manual_review"
        )

    def test_production_experience_requires_review(self):
        job = {
            "job_title": "AI Engineer",
            "eligibility_classification": "unclear_manual_verification",
            "fresher_signals": [],
            "experience_signals": [],
            "production_experience_required": True,
            "required_experience_years": None,
        }

        self.assertEqual(
            classify_fresher_eligibility(job),
            "manual_review"
        )

    def test_exact_job_identity(self):
        job = {
            "source": "arbeitnow",
            "job_id": 123,
            "company": "Example",
            "job_title": "AI Engineer",
            "location": "London",
        }

        self.assertEqual(
            make_job_identity(job),
            "arbeitnow:123"
        )

    def test_different_location_variants_preserved(self):
        jobs = [
            {
                "company": "Example",
                "job_title": "AI Engineer",
                "location": "London",
                "job_id": 1,
            },
            {
                "company": "Example",
                "job_title": "AI Engineer",
                "location": "Berlin",
                "job_id": 2,
            },
        ]

        groups = build_role_groups(jobs)

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["variant_count"], 2)
        self.assertEqual(
            set(groups[0]["locations"]),
            {"London", "Berlin"}
        )

    def test_missing_skill_recommendation(self):
        jobs = [
            {
                "job_title": "AI Engineer",
                "missing_mandatory_skills": ["Python", "Docker"],
            },
            {
                "job_title": "ML Engineer",
                "missing_mandatory_skills": ["Docker"],
            },
        ]

        recommendations = build_skill_recommendations(jobs)

        docker = next(
            item for item in recommendations
            if item["skill"] == "docker"
        )

        self.assertEqual(
            docker["shortlisted_jobs_missing_this_skill"],
            2
        )
        self.assertEqual(docker["priority"], "medium")


if __name__ == "__main__":
    unittest.main(verbosity=2)
