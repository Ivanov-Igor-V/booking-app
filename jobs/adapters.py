from datetime import datetime


def parse_publication_date(value, *, source_timezone=None):
    if not isinstance(value, str):
        raise ValueError("publication_date must be a string")
    if not value.strip():
        raise ValueError("date is required")
    formatted_datetime = datetime.fromisoformat(value)
    if formatted_datetime.utcoffset() is None:
        if source_timezone is None:
            raise ValueError("publication_date must include a timezone")
        formatted_datetime = formatted_datetime.replace(tzinfo=source_timezone)
    return formatted_datetime


def optional_text(raw_job, field):
    value = raw_job.get(field)
    if value is None:
        return ""

    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")

    return value


def require_text(raw_job, field):
    value = raw_job.get(field)

    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{field} is required")

    return value


def normalize_remotive_job(raw_job):
    external_id = str(raw_job["id"])

    data = {
        "title": require_text(raw_job, "title"),
        "company_name": require_text(raw_job, "company_name"),
        "original_url": require_text(raw_job, "url"),
        "publication_date": raw_job["publication_date"],
        "description": optional_text(raw_job, "description"),
    }

    return external_id, data
