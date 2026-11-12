import json
from datetime import timezone as datetime_timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from jobs.adapters import normalize_remotive_job
from jobs.models import Source
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
        if isinstance(vacancy, dict):
            vacancies = [vacancy]
        elif isinstance(vacancy, list):
            vacancies = vacancy
        else:
            raise CommandError("Expected a JSON object or list")
        normalized_jobs = []

        for number, raw_job in enumerate(vacancies, start=1):
            if not isinstance(raw_job, dict):
                raise CommandError("Expected a JSON object")
            try:
                external_id, data = normalize_remotive_job(
                    raw_job,
                    source_timezone=datetime_timezone.utc,
                )
            except ValueError as error:
                raise CommandError(f"Vacancy {number}: {error}") from error

            normalized_jobs.append((external_id, data))
        created_count = 0
        updated_count = 0
        if normalized_jobs:
            source, _ = Source.objects.get_or_create(
                name="Remotive",
                defaults={"website": "https://remotive.com/"},
            )

            for external_id, data in normalized_jobs:
                job, created = save_imported_job(source, external_id, data)

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(f"Created: {created_count}, updated: {updated_count}")

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            type=Path,
            help="Path to a Remotive JSON file",
        )
