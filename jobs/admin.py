# Register your models here.
from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company_name", "publication_date")
    search_fields = ("title", "company_name")
    ordering = ("-publication_date", "-id")
