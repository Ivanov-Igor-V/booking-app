import json

from job_filters import filter_jobs, paginate_jobs, sort_jobs_by_date


def load_jobs(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    try:
        jobs = load_jobs("jobs.json")

    except FileNotFoundError:
        print("Файл с вакансиями не найден")
        return
    except json.JSONDecodeError:
        print("Файл содержит некорректный JSON")
        return

    keyword = input("Search jobs: ").strip()

    filtered_jobs = filter_jobs(jobs, keyword)
    print(f"Found: {len(filtered_jobs)}")

    if not filtered_jobs:
        print("No jobs found")
        return

    sorted_jobs = sort_jobs_by_date(filtered_jobs)
    page_size = 5

    while True:
        value = input("Page number or q to quit: ").strip()

        if value.lower() == "q":
            break

        try:
            page = int(value)
            page_jobs = paginate_jobs(sorted_jobs, page, page_size)
        except ValueError:
            print("Enter a positive whole number")
            continue

        if not page_jobs:
            print("No jobs on this page")
            continue

        start = (page - 1) * page_size + 1
        for index, job in enumerate(page_jobs, start=start):
            print(f"{index}. {job['title']} — {job['company_name']}")


if __name__ == "__main__":
    main()
