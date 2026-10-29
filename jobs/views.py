from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.html import format_html

from .models import Job


def job_list(request):
    keyword = request.GET.get("q", "").strip()
    vacancies = Job.objects.order_by("-publication_date", "-id")

    if keyword:
        vacancies = vacancies.filter(
            Q(title__icontains=keyword) | Q(company_name__icontains=keyword)
        )
    paginator = Paginator(vacancies, 2)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "jobs/job_list.html",
        {"jobs": page_obj, "keyword": keyword, "page_obj": page_obj},
    )


def jobs_about(request, test):
    return HttpResponse(format_html("<p>Job Atlas: {}</p>", test))


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, "jobs/job_detail.html", {"job": job})


def home(request):
    return render(request, "jobs/home.html")
