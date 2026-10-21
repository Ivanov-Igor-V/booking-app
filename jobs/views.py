from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render

from .models import Job


def job_list(request):
    keyword = request.GET.get("q", "").strip()
    vacancies = Job.objects.order_by("-publication_date", "-id")
    if keyword:
        vacancies = vacancies.filter(
            Q(title__icontains=keyword) | Q(company_name__icontains=keyword)
        )
    return render(
        request, "jobs/job_list.html", {"jobs": vacancies, "keyword": keyword}
    )


def jobs_about(request):
    return HttpResponse("<strong>Job Atlas collects developer vacancies</strong>")
