from django.urls import path

from . import views

urlpatterns = [
    path("", views.job_list, name="job_list"),
    path("about/", views.jobs_about, name="about"),
]
