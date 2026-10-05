import unittest

from job_filters import filter_jobs, paginate_jobs, sort_jobs_by_date

mock_jobs = [
    {"title": "Python Developer", "company_name": "ACME"},
    {"title": "Java Developer", "company_name": "Example"},
]
big_job_list = [
    {"title": "New job", "publication_date": "2026-10-03T10:00:00"},
    {"title": "Old job", "publication_date": "2026-09-01T10:00:00"},
    {"title": "Middle job1", "publication_date": "2026-09-15T10:00:00"},
    {"title": "Middle job2", "publication_date": "2026-09-15T10:00:00"},
    {"title": "Middle job3", "publication_date": "2026-09-15T10:00:00"},
    {"title": "Middle job4", "publication_date": "2026-09-15T10:00:00"},
    {"title": "Middle job5", "publication_date": "2026-09-15T10:00:00"},
    {"title": "Middle job6", "publication_date": "2026-09-15T10:00:00"},
    {"title": "Middle job7", "publication_date": "2026-09-15T10:00:00"},
    {"title": "Middle job8", "publication_date": "2026-09-15T10:00:00"},
]


class FilterJobsTests(unittest.TestCase):
    def test_finds_python_job(self):
        result = filter_jobs(mock_jobs, "python")

        self.assertEqual(
            result, [{"title": "Python Developer", "company_name": "ACME"}]
        )

    def test_finds_python_job_capital(self):

        result = filter_jobs(mock_jobs, "PYTHON")

        self.assertEqual(
            result, [{"title": "Python Developer", "company_name": "ACME"}]
        )

    def test_finds_python_job_rust(self):

        result = filter_jobs(mock_jobs, "rust")

        self.assertEqual(result, [])

    def test_finds_python_job_empty_query(self):

        result = filter_jobs(mock_jobs, "")

        self.assertEqual(result, mock_jobs)

    def test_finds_python_job_non_founded(self):
        result = filter_jobs(mock_jobs, "vue")

        self.assertEqual(result, [])

    def test_sort_by_date(self):
        jobs = [
            {"title": "New job", "publication_date": "2026-10-03T10:00:00"},
            {"title": "Old job", "publication_date": "2026-09-01T10:00:00"},
            {"title": "Middle job", "publication_date": "2026-09-15T10:00:00"},
        ]
        sorted_jobs = [
            {"title": "New job", "publication_date": "2026-10-03T10:00:00"},
            {"title": "Middle job", "publication_date": "2026-09-15T10:00:00"},
            {"title": "Old job", "publication_date": "2026-09-01T10:00:00"},
        ]
        result = sort_jobs_by_date(jobs)

        self.assertEqual(result, sorted_jobs)

    def test_pagination_first_page(self):
        first_page = [
            {"title": "New job", "publication_date": "2026-10-03T10:00:00"},
            {"title": "Old job", "publication_date": "2026-09-01T10:00:00"},
            {"title": "Middle job1", "publication_date": "2026-09-15T10:00:00"},
        ]
        result = paginate_jobs(big_job_list, 1, 3)

        self.assertEqual(result, first_page)

    def test_pagination_second_page(self):
        first_page = [
            {"title": "Middle job2", "publication_date": "2026-09-15T10:00:00"},
            {"title": "Middle job3", "publication_date": "2026-09-15T10:00:00"},
            {"title": "Middle job4", "publication_date": "2026-09-15T10:00:00"},
        ]
        result = paginate_jobs(big_job_list, 2, 3)

        self.assertEqual(result, first_page)

    def test_pagination_7_item_per_page(self):
        amount = 7
        first_page = big_job_list[0:amount]
        result = paginate_jobs(big_job_list, 1, amount)

        self.assertEqual(result, first_page)

    def test_pagination_too_big_page_number(self):
        result = paginate_jobs(big_job_list, 55, 3)

        self.assertEqual(result, [])

    def test_pagination_last_partial_page(self):
        result = paginate_jobs(big_job_list, 4, 3)
        self.assertEqual(result, [big_job_list[-1]])

    def test_pagination_zero_page(self):
        with self.assertRaises(ValueError):
            paginate_jobs(big_job_list, page=0, page_size=3)

    def test_pagination_zero_page_size(self):
        with self.assertRaises(ValueError):
            paginate_jobs(big_job_list, page=1, page_size=0)


if __name__ == "__main__":
    unittest.main()
