
from database.job_repository import validate_job_data


def run_validation_tests():
    print("=" * 50)
    print("JOB DATA VALIDATION TESTS")
    print("=" * 50)

    # Test 1: Valid job data
    valid_job = {
        "title": "Junior AI Engineer",
        "company": "ABC Technologies",
        "description": "Python and Machine Learning role.",
        "salary_min": 300000,
        "salary_max": 500000,
    }

    validate_job_data(valid_job)
    print("\nTEST 1 PASSED: Valid job data accepted.")

    # Test 2: Missing company name
    invalid_job = {
        "title": "AI Engineer",
        "company": " ",
        "description": "AI role.",
    }

    try:
        validate_job_data(invalid_job)
        raise AssertionError("Invalid company name was accepted.")
    except ValueError:
        print("TEST 2 PASSED: Missing company rejected.")

    # Test 3: Negative salary
    invalid_job = {
        "title": "AI Engineer",
        "company": "ABC Technologies",
        "description": "AI role.",
        "salary_min": -1000,
    }

    try:
        validate_job_data(invalid_job)
        raise AssertionError("Negative salary was accepted.")
    except ValueError:
        print("TEST 3 PASSED: Negative salary rejected.")

    # Test 4: Minimum salary greater than maximum
    invalid_job = {
        "title": "AI Engineer",
        "company": "ABC Technologies",
        "description": "AI role.",
        "salary_min": 800000,
        "salary_max": 500000,
    }

    try:
        validate_job_data(invalid_job)
        raise AssertionError("Invalid salary range was accepted.")
    except ValueError:
        print("TEST 4 PASSED: Invalid salary range rejected.")

    print("\nALL VALIDATION TESTS PASSED!")


if __name__ == "__main__":
    run_validation_tests()
