from datetime import timedelta

from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Job, Source


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
