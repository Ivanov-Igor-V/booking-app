def filter_jobs(jobs, keyword):
    return [
        job
        for job in jobs
        if keyword.lower() in job["title"].lower()
        or keyword.lower() in job["company_name"].lower()
    ]


def sort_jobs_by_date(jobs):
    return sorted(jobs, key=lambda job: job["publication_date"], reverse=True)


def paginate_jobs(jobs, page, page_size) -> list:
    if page <= 0 or page_size <= 0:
        raise ValueError("page and page_size must be positive")
    start = (page - 1) * page_size
    end = start + page_size

    return jobs[start:end]
