from .models import Job


def save_imported_job(source, external_id, data):
    if external_id is None:
        raise ValueError("external_id is required")

    external_id = str(external_id).strip()

    if not external_id:
        raise ValueError("external_id is required")
    job, created = Job.objects.update_or_create(
        source=source,
        external_id=external_id,
        defaults=data,
    )
    return job, created
