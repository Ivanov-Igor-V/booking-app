from django.http import HttpResponse
from django.shortcuts import render


def job_list(request):
    vacancies = [
        {"title": "Python Developer", "company_name": "ACME"},
        {"title": "Django Developer", "company_name": "Example"},
    ]
    return render(request, "jobs/job_list.html", {"jobs": vacancies})


def jobs_about(request):
    return HttpResponse("<strong>Job Atlas collects developer vacancies</strong>")
