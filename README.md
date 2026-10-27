# Church Management System API

Backend API for a multi-branch church: members and families, children's check-in, attendance and
follow-up, giving and Mobile Money payments, finance, events, messaging and reports. Each branch manages
its own records; headquarters sees consolidated data across all branches.

The build plan and progress live in [docs/ROADMAP.md](docs/ROADMAP.md).

## Local development

Requirements: [uv](https://docs.astral.sh/uv/) and Docker.

```bash
docker compose up -d          # PostgreSQL, Redis, Mailpit, SeaweedFS
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

| Service | Address |
|---|---|
| API | http://localhost:8000 |
| Mailpit (caught emails) | http://localhost:8025 |
| PostgreSQL | localhost:5433 (user `church`, password `church`) |
| S3 storage | http://localhost:8333 |

Background jobs (SMS, reminders, imports) need a worker and, for scheduled jobs, beat:

```bash
uv run celery -A config worker -l info
uv run celery -A config beat -l info
```

Install the git hooks once with `uv run pre-commit install`.
