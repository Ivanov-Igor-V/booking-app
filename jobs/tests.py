from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Job


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

    def test_missing_or_blank_query_returns_all_jobs(self):
        for params in ({}, {"q": ""}, {"q": "   "}):
            with self.subTest(params=params):
                response = self.client.get(reverse("job_list"), params)
                self.assertEqual(
                    list(response.context["jobs"]),
                    [self.other, self.newer, self.older],
                )

    def test_no_matches(self):
        response = self.client.get(reverse("job_list"), {"q": "rust"})
        self.assertEqual(list(response.context["jobs"]), [])
        self.assertContains(response, "No jobs found")
