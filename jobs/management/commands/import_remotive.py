import json
from datetime import timezone as datetime_timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from jobs.adapters import normalize_remotive_job
from jobs.models import Job, Source
from jobs.services import save_imported_job


class Command(BaseCommand):
    help = "Import vacancies from a Remotive JSON file"

    def handle(self, *args, **options):
        path = options["path"]
        self.stdout.write(f"Reading: {path}")
        try:
            with open(path, encoding="utf-8") as f:
                vacancy = json.load(f)
        except FileNotFoundError as error:
            raise CommandError(f"File not found: {path}") from error
        except json.JSONDecodeError as error:
            raise CommandError(f"Invalid JSON: {path}") from error
        except UnicodeDecodeError as error:
            raise CommandError(f"File must use UTF-8: {path}") from error
        except OSError as error:
            raise CommandError(f"Cannot read file: {path}") from error
        if not isinstance(vacancy, dict):
            raise CommandError("Expected a JSON object")
        try:
            external_id, data = normalize_remotive_job(
                vacancy,
                source_timezone=datetime_timezone.utc,
            )
        except ValueError as error:
            raise CommandError(str(error)) from error

        custom_source, _ = Source.objects.get_or_create(
            name="Remotive",
            defaults={"website": "https://remotive.com/"},
        )
        job, created = save_imported_job(custom_source, external_id, data)
        message = f"Created: {job.title}"
        if not created:
            message = f"Updated: {job.title}"

        self.stdout.write(message)

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
