# Job Atlas

A job aggregation website built as a learning project with Django and, later, React and TypeScript. It imports vacancies from documented public APIs and lets visitors search them in one place.

## Project status

Requirements stage. No application or import pipeline has been implemented yet. The existing GitHub repository is currently named `booking-app`; this README describes the new product direction.

## Goal

Build practical backend and full-stack skills through small tasks, implementation, code review, testing, and deployment. The audience is people looking for technology jobs, with a focus on opportunities relevant to Europe. Source coverage and eligibility restrictions must be shown honestly: remote does not automatically mean available in every country.

## MVP

- Import software development vacancies from one source: Remotive.
- Store normalized vacancies in PostgreSQL.
- Provide a public list and detail pages without requiring registration.
- Search by job title and company; filter by source category and candidate location where supplied.
- Sort by publication date and paginate results.
- Show the source, original listing link, and last successful synchronization time.
- Let visitors follow the source link to apply.
- Run synchronization manually through a Django management command initially.

## Data flow

External API → source adapter → validation and normalization → PostgreSQL → Django REST API → React interface.

Visitor requests read our database. They do not trigger upstream API requests. Start with a single Django application; introduce scheduled background work after manual imports are reliable.

## Initial source

[Remotive public API documentation](https://github.com/remotive-com/remote-jobs-api)

Endpoint: `GET https://remotive.com/api/remote-jobs?category=software-dev`

The provider recommends fetching at most four times per day. Listings have a 24-hour delay. Display Remotive attribution and the original Remotive listing link. Listings must remain accessible without collecting registrations or email addresses. Do not redistribute them to third-party job platforms. Review current provider terms before deployment or changing how the data is used.

Other providers will be evaluated individually for access requirements, permitted display, attribution, limits, available fields, and geographic coverage before integration.

## Data model outline

- **Source:** provider name and integration configuration.
- **Job:** source, external identifier, title, company, description, original URL, category, candidate location, employment type, salary text, publication time, last seen time, and availability status.
- **ImportRun:** source, start/end time, result, imported/updated counts, and error summary.

Fields absent from the source remain unknown. Salary text is preserved without guessing currency or payment period. Candidate location is preserved without inventing eligibility or visa information.

## Import rules

- A unique `(source, external_id)` identifies a vacancy; repeated imports update it rather than creating duplicates.
- Use explicit HTTP timeouts and handle HTTP errors, invalid JSON, and malformed records.
- Failed requests must not delete stored vacancies or mark the entire source inactive.
- Only a successful complete source snapshot can support marking absent listings inactive. A filtered or limited response does not prove a listing has closed.
- Preserve the source publication time separately from the local import time; handle source timezone ambiguity explicitly.
- Display imported descriptions as plain text initially. External HTML must be sanitized before any later HTML rendering.
- Preserve previously imported listings when a source is unavailable and expose synchronization freshness.
- Cross-source duplicate detection is a later feature; titles alone are not reliable identifiers.

## Planned stack

| Technology | Purpose |
| --- | --- |
| Python, Django | Models, imports, administration, and application logic |
| PostgreSQL | Persistent data and uniqueness constraints |
| Django REST Framework | Searchable, paginated public API |
| React, TypeScript | Job search interface |
| Celery, Redis | Scheduled synchronization and retries in a later stage |
| pytest, pytest-django | Import, API, and business rule tests |
| Git, GitHub Actions | Version control and automated checks |
| Docker Compose, Linux | Local services and deployment |

Versions and reproducible setup instructions will be added when the environment is configured.

## Roadmap

1. Explore an upstream API and understand HTTP and JSON.
2. Configure Django, PostgreSQL, and development tooling.
3. Implement models and a manual import command.
4. Test repeat imports, malformed data, and upstream failures using fixtures rather than live API calls.
5. Build the public REST API with search, filters, and pagination.
6. Build the React interface with loading, empty, and error states.
7. Add a second source through a separate adapter.
8. Introduce scheduled synchronization, controlled retries, and import monitoring.
9. Add CI, deploy, and document logs, backups, and recovery.

## Later features

Optional accounts and saved jobs, saved searches and alerts, improved location filters, and cross-source duplicate detection. Public job browsing remains available without an account. CV uploads, application processing, scraping, and paid subscriptions are outside the initial scope.

## Learning workflow

The author implements small tasks with clear acceptance criteria. Review covers correctness and the ability to explain the code. Particular topics include HTTP, JSON, SQL, migrations, idempotent imports, constraints, external failures, testing, background tasks, React state, and deployment.

## Running locally

Application code is not available yet. Verified setup instructions will be added with the first Django implementation.
