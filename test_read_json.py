import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from readJSON import main


class SearchConsoleTests(unittest.TestCase):
    def run_console(self, jobs, answers):
        output = io.StringIO()
        with (
            patch("readJSON.load_jobs", return_value=jobs),
            patch("builtins.input", side_effect=answers) as user_input,
            redirect_stdout(output),
        ):
            main()
        return output.getvalue(), user_input.call_count

    def test_pages_and_invalid_input(self):
        jobs = [
            {
                "title": f"Python Job {number}",
                "company_name": "ACME",
                "publication_date": f"2026-10-{number:02d}T10:00:00",
            }
            for number in range(1, 8)
        ]
        output, calls = self.run_console(
            jobs, ["", "1", "2", "abc", "0", "999999", "q"]
        )
        self.assertEqual(calls, 7)
        self.assertEqual(output.count("Found: 7"), 1)
        self.assertIn("1. Python Job 7", output)
        self.assertIn("5. Python Job 3", output)
        self.assertIn("6. Python Job 2", output)
        self.assertIn("7. Python Job 1", output)
        self.assertEqual(output.count("Enter a positive whole number"), 2)
        self.assertIn("No jobs on this page", output)

    def test_no_matches_does_not_ask_for_page(self):
        jobs = [{"title": "Python Developer", "company_name": "ACME"}]
        output, calls = self.run_console(jobs, ["rust"])
        self.assertEqual(calls, 1)
        self.assertIn("No jobs found", output)

    def test_quit_before_selecting_page(self):
        jobs = [
            {
                "title": "Python Developer",
                "company_name": "ACME",
                "publication_date": "2026-10-01T10:00:00",
            }
        ]
        output, calls = self.run_console(jobs, ["python", "q"])
        self.assertEqual(calls, 2)
        self.assertIn("Found: 1", output)
        self.assertNotIn("1. Python Developer", output)


if __name__ == "__main__":
    unittest.main()
