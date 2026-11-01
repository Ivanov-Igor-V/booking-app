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
        "description": raw_job["description"],
    }

    return external_id, data
