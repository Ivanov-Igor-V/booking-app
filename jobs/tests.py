import json
from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone
from pathlib import Path

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from .adapters import normalize_remotive_job, parse_publication_date
from .models import Job, Source
from .services import save_imported_job


class JobSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.older = Job.objects.create(
            title="Python Developer",
            company_name="ACME",
            original_url="https://example.com/jobs/1",
            publication_date=now - timedelta(days=1),
        )
        cls.newer = Job.objects.create(
            title="Python Engineer",
            company_name="Python Labs",
            original_url="https://example.com/jobs/2",
            publication_date=now,
        )
        cls.other = Job.objects.create(
            title="Java Developer",
            company_name="Example",
            original_url="https://example.com/jobs/3",
            publication_date=now,
        )

    def test_title_search_preserves_order_without_duplicates(self):
        for keyword in ("python", "PYTHON", "  python  "):
            with self.subTest(keyword=keyword):
                response = self.client.get(reverse("job_list"), {"q": keyword})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    list(response.context["jobs"]), [self.newer, self.older]
                )
                self.assertContains(response, f'value="{keyword.strip()}"')
                self.assertNotContains(response, "Java Developer")

    def test_search_by_company(self):
        response = self.client.get(reverse("job_list"), {"q": "acme"})
        self.assertEqual(list(response.context["jobs"]), [self.older])
        self.assertContains(response, "Python Developer")

    def test_missing_or_blank_query_returns_all_jobs_across_pages(self):
        for params in ({}, {"q": ""}, {"q": "   "}):
            with self.subTest(params=params):
                response = self.client.get(reverse("job_list"), params)
                self.assertEqual(
                    list(response.context["jobs"]),
                    [self.other, self.newer],
                )
                self.assertEqual(response.context["page_obj"].paginator.count, 3)
                second_page = self.client.get(
                    reverse("job_list"), {**params, "page": 2}
                )
                self.assertEqual(list(second_page.context["jobs"]), [self.older])

    def test_no_matches(self):
        response = self.client.get(reverse("job_list"), {"q": "rust"})
        self.assertEqual(list(response.context["jobs"]), [])
        self.assertContains(response, "No jobs found")


class JobPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        for number in range(1, 4):
            Job.objects.create(
                title=f"Python Developer {number}",
                company_name="ACME",
                original_url=f"https://example.com/jobs/{number}",
                publication_date=now + timedelta(minutes=number),
            )

    def test_first_page_contains_two_jobs(self):
        response = self.client.get(reverse("job_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["jobs"]), 2)
        self.assertEqual(response.context["page_obj"].paginator.count, 3)
        self.assertContains(response, "Всего 3 вакансий")

    def test_second_page_contains_remaining_job_without_overlap(self):
        first = self.client.get(reverse("job_list"))
        second = self.client.get(reverse("job_list"), {"page": 2})
        self.assertEqual(second.status_code, 200)
        first_ids = {job.pk for job in first.context["jobs"]}
        second_ids = {job.pk for job in second.context["jobs"]}
        self.assertEqual(len(second_ids), 1)
        self.assertFalse(first_ids & second_ids)
        self.assertEqual(
            first_ids | second_ids, set(Job.objects.values_list("pk", flat=True))
        )
        self.assertEqual(second.context["jobs"][0].title, "Python Developer 1")

    def test_non_numeric_page_returns_first_page(self):
        response = self.client.get(reverse("job_list"), {"page": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 1)
        self.assertEqual(len(response.context["jobs"]), 2)

    def test_no_matches_returns_empty_page(self):
        response = self.client.get(reverse("job_list"), {"q": "nonexistent"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 0)
        self.assertContains(response, "No jobs found")

    def test_search_is_preserved_in_page_links(self):
        first = self.client.get(reverse("job_list"), {"q": "Python Developer"})
        self.assertContains(first, "?q=Python%20Developer&amp;page=2")
        second = self.client.get(
            reverse("job_list"), {"q": "Python Developer", "page": 2}
        )
        self.assertContains(second, "?q=Python%20Developer&amp;page=1")


class JobDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.job = Job.objects.create(
            title=f"Python Developer {1}",
            company_name="ACME",
            original_url=f"https://example.com/jobs/{1}",
            publication_date=now + timedelta(minutes=1),
        )

    def test_existing_job_returns_200(self):
        response = self.client.get(reverse("job_detail", args=[self.job.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/job_detail.html")
        self.assertTemplateUsed(response, "jobs/base.html")
        self.assertContains(response, f"<h1>{self.job.title}</h1>", html=True)
        self.assertContains(
            response, f"<title>{self.job.title} — Job Atlas</title>", html=True
        )

    def test_link_to_vac_is_proper(self):
        response = self.client.get(reverse("job_detail", args=[self.job.pk]))

        self.assertContains(
            response,
            f'href="{self.job.original_url}"',
        )

    def test_vac_do_not_exist(self):
        missing_pk = self.job.pk + 1

        response = self.client.get(reverse("job_detail", args=[missing_pk]))

        self.assertEqual(response.status_code, 404)

    def test_description_escapes_html(self):
        self.job.description = "<script>alert('test')</script>"
        self.job.save()

        response = self.client.get(reverse("job_detail", args=[self.job.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>")

    def test_empty_description_shows_placeholder(self):
        response = self.client.get(reverse("job_detail", args=[self.job.pk]))

        self.assertContains(response, "No description available")

    def test_description_preserves_line_breaks(self):
        self.job.description = "First line\nSecond line"
        self.job.save()

        response = self.client.get(reverse("job_detail", args=[self.job.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First line<br>Second line")


class SouceTests(TestCase):
    def test_source_cannot_remove(self):
        source = Source.objects.create(
            name="Test Source",
            website="https://example.com/",
        )

        Job.objects.create(
            title=f"Python Developer {1}",
            company_name="ACME",
            original_url=f"https://example.com/jobs/{1}",
            publication_date=timezone.now() + timedelta(minutes=1),
            source=source,
        )
        with self.assertRaises(ProtectedError):
            source.delete()

    def test_source_removes_if_not_used(self):
        source = Source.objects.create(
            name="Test Source",
            website="https://example.com/",
        )
        id = source.pk
        source.delete()
        self.assertFalse(Source.objects.filter(pk=id).exists())

    def test_source_len_of_vacs(self):
        source = Source.objects.create(
            name="Test Source 1",
            website="https://example.com/",
        )
        source2 = Source.objects.create(
            name="Test Source 2",
            website="https://example2.com/",
        )
        job1 = Job.objects.create(
            title="Python Developer 1",
            company_name="ACME",
            original_url=f"https://example.com/jobs/{1}",
            publication_date=timezone.now() + timedelta(minutes=1),
            source=source,
        )
        job2 = Job.objects.create(
            title="Python Developer 2",
            company_name="ACME",
            original_url=f"https://example.com/jobs/{2}",
            publication_date=timezone.now() + timedelta(minutes=1),
            source=source2,
        )
        job3 = Job.objects.create(
            title="Python Developer 3",
            company_name="ACME",
            original_url="https://example.com/jobs/3",
            publication_date=timezone.now() + timedelta(minutes=1),
            source=source,
        )
        self.assertCountEqual(source.jobs.all(), [job1, job3])
        self.assertCountEqual(source2.jobs.all(), [job2])

        self.assertEqual(job1.source, source)
        self.assertEqual(job1.source_id, source.pk)


class ImportedJobTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name="Test Source", website="https://example.com/"
        )
        self.data = {
            "title": "Python Developer",
            "company_name": "ACME",
            "original_url": "https://example.com/jobs/123",
            "publication_date": timezone.now(),
            "description": "Build Django applications",
        }

    def test_duplicate_external_id_for_same_source_is_rejected(self):
        Job.objects.create(source=self.source, external_id="123", **self.data)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Job.objects.create(source=self.source, external_id="123", **self.data)
        self.assertEqual(Job.objects.count(), 1)

    def test_same_external_id_for_different_sources_is_allowed(self):
        other_source = Source.objects.create(
            name="Other Source", website="https://other.example.com/"
        )
        first = Job.objects.create(source=self.source, external_id="123", **self.data)
        second = Job.objects.create(source=other_source, external_id="123", **self.data)
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(Job.objects.count(), 2)

    def test_repeated_import_updates_existing_job(self):
        job, created = save_imported_job(self.source, "1", self.data)
        self.assertTrue(created)
        self.data["title"] = "Senior Python Developer"
        updated_job, created = save_imported_job(self.source, "1", self.data)
        self.assertFalse(created)
        self.assertEqual(job.pk, updated_job.pk)
        job.refresh_from_db()
        self.assertEqual(job.title, "Senior Python Developer")
        self.assertEqual(Job.objects.count(), 1)

    def test_missing_external_id_is_rejected_without_creating_jobs(self):
        for external_id in (None, "", "   "):
            with self.subTest(external_id=external_id):
                with self.assertRaisesMessage(ValueError, "external_id is required"):
                    save_imported_job(self.source, external_id, self.data)
                self.assertEqual(Job.objects.count(), 0)

    def test_numeric_and_string_ids_update_same_job(self):
        job, created = save_imported_job(self.source, 123, self.data)
        self.assertTrue(created)
        self.data["title"] = "Updated title"
        updated_job, created = save_imported_job(self.source, "123", self.data)
        self.assertFalse(created)
        self.assertEqual(job.pk, updated_job.pk)
        job.refresh_from_db()
        self.assertEqual(job.external_id, "123")
        self.assertEqual(job.title, "Updated title")
        self.assertEqual(Job.objects.count(), 1)

    def test_zero_external_id_is_valid(self):
        job, created = save_imported_job(self.source, 0, self.data)
        self.assertTrue(created)
        job.refresh_from_db()
        self.assertEqual(job.external_id, "0")
        self.assertEqual(Job.objects.count(), 1)

    def test_external_id_whitespace_is_trimmed(self):
        job, created = save_imported_job(self.source, " 123 ", self.data)
        self.assertTrue(created)
        job.refresh_from_db()
        self.assertEqual(job.external_id, "123")


class RemotiveDataTests(SimpleTestCase):
    def setUp(self):
        path = Path(__file__).resolve().parent / "test_data" / "remotive_job.json"
        with open(path, "r", encoding="utf-8") as f:
            self.vacancy = json.load(f)

    def test_mock_vacancy(self):
        job = self.vacancy
        self.assertEqual(job["id"], 123)
        self.assertEqual(job["title"], "Python Developer")
        self.assertIn("<p>", job["description"])

    def test_adapter_strips_spaces(self):
        raw_job = self.vacancy

        for field, result_field in (
            ("title", "title"),
            ("company_name", "company_name"),
            ("url", "original_url"),
        ):
            with self.subTest(field=field):
                padded_job = raw_job.copy()
                padded_job[field] = f"  {raw_job[field]}  "
                original = padded_job.copy()
                external_id, data = normalize_remotive_job(padded_job)
                self.assertEqual(data[result_field], raw_job[field])
                self.assertEqual(padded_job, original)

    def test_adapter_rejects_missing_required_fields(self):
        original_job = self.vacancy

        for field in ("title", "company_name", "url"):
            with self.subTest(field=field):
                raw_job = original_job.copy()
                del raw_job[field]
                before = raw_job.copy()
                with self.assertRaisesMessage(ValueError, field):
                    normalize_remotive_job(raw_job)
                self.assertEqual(raw_job, before)

    def test_adapter_rejects_invalid_required_fields(self):
        original_job = self.vacancy

        for field in ("title", "company_name", "url"):
            for value in (None, 123, "", "   "):
                with self.subTest(field=field, value=value):
                    raw_job = original_job.copy()
                    raw_job[field] = value
                    before = raw_job.copy()
                    with self.assertRaisesMessage(ValueError, field):
                        normalize_remotive_job(raw_job)
                    self.assertEqual(raw_job, before)

    def test_missing_description_becomes_empty_string(self):
        raw_job = self.vacancy.copy()
        del raw_job["description"]
        before = raw_job.copy()

        _, data = normalize_remotive_job(raw_job)

        self.assertEqual(data["description"], "")
        self.assertEqual(raw_job, before)

    def test_none_description_becomes_empty_string(self):
        raw_job = self.vacancy.copy()
        raw_job["description"] = None
        before = raw_job.copy()

        _, data = normalize_remotive_job(raw_job)

        self.assertEqual(data["description"], "")
        self.assertEqual(raw_job, before)

    def test_string_description_is_preserved(self):
        for description in ("", "   ", "  First line\nSecond line  ", self.vacancy["description"]):
            with self.subTest(description=description):
                raw_job = self.vacancy.copy()
                raw_job["description"] = description
                before = raw_job.copy()

                _, data = normalize_remotive_job(raw_job)

                self.assertEqual(data["description"], description)
                self.assertEqual(raw_job, before)

    def test_invalid_description_is_rejected(self):
        for description in (123, [], {}):
            with self.subTest(description=description):
                raw_job = self.vacancy.copy()
                raw_job["description"] = description
                before = raw_job.copy()

                with self.assertRaisesMessage(ValueError, "description"):
                    normalize_remotive_job(raw_job)

                self.assertEqual(raw_job, before)

    def test_adapter_works(self):
        raw_job = self.vacancy

        external_id, data = normalize_remotive_job(raw_job)
        self.assertEqual(external_id, "123")
        self.assertEqual(data["title"], "Python Developer")
        self.assertEqual(data["company_name"], raw_job["company_name"])
        self.assertEqual(data["original_url"], raw_job["url"])
        self.assertEqual(data["publication_date"], raw_job["publication_date"])
        self.assertEqual(data["description"], raw_job["description"])
        self.assertNotIn("url", data)
        self.assertNotIn("id", data)
        self.assertNotIn("external_id", data)


class PublicationDateTests(SimpleTestCase):
    def test_date_with_utc_offset(self):
        result = parse_publication_date("2026-09-18T16:43:22+00:00")
        expected = datetime(2026, 9, 18, 16, 43, 22, tzinfo=datetime_timezone.utc)

        self.assertEqual(result, expected)
        self.assertIsNotNone(result.utcoffset())

    def test_different_offsets_represent_same_instant(self):
        utc_date = parse_publication_date("2026-09-18T16:43:22+00:00")
        offset_date = parse_publication_date("2026-09-18T19:43:22+03:00")

        self.assertEqual(utc_date, offset_date)

    def test_date_without_timezone_is_rejected(self):
        with self.assertRaisesMessage(ValueError, "must include a timezone"):
            parse_publication_date("2026-09-18T16:43:22")

    def test_invalid_values_are_rejected(self):
        for value in (None, 123, "", "   ", "not-a-date"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_publication_date(value)

    def test_naive_date_uses_explicit_source_timezone(self):
        result = parse_publication_date(
            "2026-09-18T16:43:22", source_timezone=datetime_timezone.utc
        )
        expected = datetime(2026, 9, 18, 16, 43, 22, tzinfo=datetime_timezone.utc)

        self.assertEqual(result, expected)
        self.assertEqual(result.utcoffset(), timedelta(0))

    def test_existing_offset_is_not_overridden(self):
        result = parse_publication_date(
            "2026-09-18T19:43:22+03:00", source_timezone=datetime_timezone.utc
        )

        self.assertEqual(result.utcoffset(), timedelta(hours=3))
        self.assertEqual((result.hour, result.minute, result.second), (19, 43, 22))
