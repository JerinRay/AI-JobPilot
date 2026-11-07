
import requests


class ArbeitnowConnector:
    """Fetch job listings from the public Arbeitnow job API."""

    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"

    def __init__(self, timeout=30):
        self.timeout = timeout

    def fetch_jobs(self, page=1):
        """Fetch one page of job listings."""

        params = {"page": page}

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "AI-JobPilot/1.0",
                },
            )

            response.raise_for_status()
            payload = response.json()

            if not isinstance(payload, dict):
                raise ValueError("Unexpected API response format.")

            jobs = payload.get("data", [])

            if not isinstance(jobs, list):
                raise ValueError("The API jobs field is not a list.")

            return jobs

        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                "Arbeitnow API request timed out."
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Unable to fetch jobs from Arbeitnow: {exc}"
            ) from exc

        except ValueError as exc:
            raise RuntimeError(
                f"Invalid Arbeitnow API response: {exc}"
            ) from exc
