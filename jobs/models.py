from django.db import models


class Job(models.Model):
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    original_url = models.URLField()
    publication_date = models.DateTimeField()
    description = models.TextField(blank=True, default="")

    objects = models.Manager()

    def __str__(self) -> str:
        return str(self.title)
