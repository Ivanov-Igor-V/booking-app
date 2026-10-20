from django.http import HttpResponse
from django.shortcuts import render

from .models import Job


def job_list(request):
    vacancies = Job.objects.order_by("-publication_date", "-id")
    return render(request, "jobs/job_list.html", {"jobs": vacancies})


def jobs_about(request):
    return HttpResponse("<strong>Job Atlas collects developer vacancies</strong>")
