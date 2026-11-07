
from src.job_matching.intelligent_job_ranker import rank_job


def create_job(
    title="Junior AI Engineer",
    location="Bengaluru, India",
    eligibility="unclear_manual_verification",
    match=80
):
    return {
        "job_title": title,
        "company": "Test Company",
        "location": location,
        "eligibility_classification": eligibility,
        "mandatory_skill_match_percentage": match,
        "fresher_signals": [],
        "manual_verification_required": True
    }


def test_senior_role_excluded():
    job = create_job(
        title="Senior AI Engineer"
    )

    result, reason = rank_job(job)

    assert result is None
    assert reason == "Senior-level title"


def test_experienced_role_excluded():
    job = create_job(
        eligibility="experienced_required"
    )

    result, reason = rank_job(job)

    assert result is None
    assert reason == "Not suitable for fresher shortlist"


def test_india_location_points():
    job = create_job()

    result, reason = rank_job(job)

    assert result is not None
    assert result["location_score"] == 25


def test_unclear_eligibility_manual_review():
    job = create_job()

    result, reason = rank_job(job)

    assert result is not None
    assert result["manual_verification_required"] is True


def test_unrelated_role_excluded():
    job = create_job(
        title="Marketing Manager"
    )

    result, reason = rank_job(job)

    assert result is None
    assert reason == "Not a target AI/Data role"


if __name__ == "__main__":
    test_senior_role_excluded()
    test_experienced_role_excluded()
    test_india_location_points()
    test_unclear_eligibility_manual_review()
    test_unrelated_role_excluded()

    print("=" * 55)
    print("ALL 5 RANKING ENGINE TESTS PASSED")
    print("=" * 55)
