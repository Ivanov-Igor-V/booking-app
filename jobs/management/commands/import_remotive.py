import json
from pathlib import Path

from django.core.management.base import BaseCommand

from jobs.models import Job, Source


class Command(BaseCommand):
    help = "Import vacancies from a Remotive JSON file"

    def handle(self, *args, **options):
        path = options["path"]
        self.stdout.write(f"Reading: {path}")
        with open(path, encoding="utf-8") as f:
            vacancy = json.load(f)
            print(vacancy["title"])
        self.stdout.write(vacancy["title"])
        count = Job.objects.count()
        count_of_sources = Source.objects.count()
        self.stdout.write(
            f"Jobs currently stored: {count}, with {count_of_sources} sources"
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            type=Path,
            help="Path to a Remotive JSON file",
        )
