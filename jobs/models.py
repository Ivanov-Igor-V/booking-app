from typing import TYPE_CHECKING

from django.db import models


class Source(models.Model):
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField()

    objects: models.Manager["Source"] = models.Manager()

    if TYPE_CHECKING:
        jobs: models.Manager["Job"]

    def __str__(self):
        return str(self.name)


class Job(models.Model):
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    original_url = models.URLField()
    publication_date = models.DateTimeField()
    description = models.TextField(blank=True, default="")
    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        related_name="jobs",
        null=True,
        blank=True,
    )
    objects = models.Manager()

    def __str__(self) -> str:
        return str(self.title)
