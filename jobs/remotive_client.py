import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REMOTIVE_URL = "https://remotive.com/api/remote-jobs?category=software-dev"


def fetch_remotive_jobs():
    request = Request(
        REMOTIVE_URL,
        headers={
            "User-Agent": "JobAtlas-Learning/0.1",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            data = json.load(response)
    except HTTPError as error:
        raise RemotiveAPIError(f"Remotive returned HTTP {error.code}") from error
    except URLError as error:
        raise RemotiveAPIError(f"Cannot connect to Remotive: {error.reason}") from error
    except TimeoutError as error:
        raise RemotiveAPIError("Remotive request timed out") from error
    except json.JSONDecodeError as error:
        raise RemotiveAPIError("Remotive returned invalid JSON") from error

    if not isinstance(data, dict):
        raise RemotiveAPIError("Expected a JSON object from Remotive")

    jobs = data.get("jobs")

    if not isinstance(jobs, list):
        raise RemotiveAPIError("Expected a jobs list from Remotive")

    return jobs


class RemotiveAPIError(Exception):
    pass
