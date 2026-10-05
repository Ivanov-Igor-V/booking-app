from django.db import models


class Job(models.Model):
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)

    def __str__(self):
        return self.title
