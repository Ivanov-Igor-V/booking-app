import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from job_filters import filter_jobs

URL = "https://remotive.com/api/remote-jobs?category=software-dev"


def main():
    request = Request(
        URL,
        headers={
            "User-Agent": "JobAtlas-Learning/0.1",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            data = json.load(response)
    except HTTPError as error:
        print(f"Сервер отклонил запрос: HTTP {error.code}")
        print(error.read().decode("utf-8", errors="replace")[:1000])
        return

    jobs = data["jobs"]
    print(f"Получено вакансий: {len(jobs)}")
    filter_key = lambda element: "Shopify".lower() in element["title"].lower()

    filtered_jobs = filter_jobs(jobs, "lemon")

    print(f"Количество вакансий: {len(filtered_jobs)}")

    if not filtered_jobs:
        print("Нет вакансий")
    else:
        for index, job in enumerate(filtered_jobs, start=1):
            print(f"#{index} - {job['title']}")

    def save_jobs(jobs, filename):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(jobs, file, ensure_ascii=False, indent=2)

    save_jobs(jobs, "jobs.json")


if __name__ == "__main__":
    main()
