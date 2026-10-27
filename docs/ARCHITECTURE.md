# Architecture

How the API is organised and the rules every module follows. Read this before adding a feature.

## Shape of the system

One Django project, one PostgreSQL database, one Celery worker pool. It is a modular monolith:
each business area is its own Django app with clear boundaries, but everything deploys together.
At 50 branches and 100,000 members (NFR-05) this is simpler to run and debug than separate services.

```
config/                 project wiring: settings, root URLs, the NinjaAPI instance, Celery app
  settings/             base.py shared; dev.py, test.py, prod.py per environment
apps/
  core/                 shared building blocks: base models, errors, pagination, files, health
  <module>/             one app per business area (branches, members, giving, ...)
docs/                   this file and the roadmap
```

## Inside an app

```
apps/members/
  models.py         tables only: fields, constraints, indexes. No business rules.
  services.py       every write: create, update, transfer, import. Takes the acting user.
  selectors.py      every read that is more than a lookup: search, filters, branch scoping.
  schemas.py        Ninja request and response schemas.
  api.py            the app's Router. Thin: parse input, call a service or selector, return.
  tasks.py          Celery tasks. Thin: load ids, call a service.
  tests/
    factories.py    factory_boy factories
    test_*.py
```

**Why services and selectors.** The same rule ("only a branch admin can transfer a member") must
hold whether the call comes from the API, a Celery task, a management command or a future admin
screen. If the rule lives in the endpoint, the other callers skip it. Keep endpoints and tasks
thin enough that there is nothing in them to test beyond wiring.

**Services:**

- Take the acting user as a keyword argument: `create_member(*, actor: User, branch: Branch, ...)`.
- Set `created_by` and `updated_by` from that actor. Never read the user from a thread-local.
- Check permissions and raise `Forbidden` / `NotFound` / `Conflict` from `apps.core.errors`, or
  Django's `ValidationError` for invalid data. All of these map to the standard error envelope.
- Run inside the request's transaction (`ATOMIC_REQUESTS`). Code outside a request (tasks,
  commands) wraps its own `transaction.atomic()`.

**Selectors** take the acting user and return querysets already limited to the branches that user
may see. An endpoint never calls `Model.objects` directly. Phase 1 adds the scoping layer
(task 1.7) and PostgreSQL row-level security behind it (task 1.8).

## Data conventions

| Topic | Rule |
|---|---|
| Base class | Every domain model inherits `apps.core.models.BaseModel`. |
| Primary keys | UUIDv7. Time-ordered for index locality, safe to generate offline on a phone. |
| Timestamps | Stored in UTC. The API returns ISO 8601 with offset. Display time zone is Africa/Accra. |
| Money | `DecimalField(max_digits=14, decimal_places=2)` plus a currency code. Never `float`. |
| Deleting | Financial records are never deleted, only reversed with a reason (NFR-14). Users are deactivated. Other records are deleted only where the spec allows it. |
| Personal data | Sensitive fields such as Ghana Card numbers are encrypted at rest (NFR-01). Consent is recorded (NFR-02). |
| Files | Use `UploadPath(prefix)` and `image_validators` / `document_validators` from `apps.core.files`. Files are private; URLs are signed and expire. |
| Choices | Fixed sets use `TextChoices`. Sets each church configures (giving types, statuses) are rows, not code (FR-30). |

## API conventions

- Base path `/api/v1`. A breaking change ships as `/api/v2`; installed mobile apps keep working.
- Resource paths are plural nouns: `/members`, `/members/{id}`, `/members/{id}/transfers`.
- Lists are paginated: `?page=2&page_size=25` returns `{items, count, page, page_size}`; at most 100
  per page.
- Filters are query parameters named after the field: `/members?status=active&branch=<id>`.
- Every error is `{"error": {"code", "message", "details"}}`. Clients branch on `code`.
  Validation errors put `[{loc, msg, type}]` in `details`.
- Interactive docs at `/api/v1/docs` in development; off in production unless `API_DOCS_ENABLED`.

## Background jobs

- Anything that talks to an outside service (SMS, email, payment providers) or takes more than a
  second runs in Celery.
- Pass ids to tasks, not model instances; load fresh data inside the task.
- Tasks are acknowledged after they finish, so a crashed worker re-runs them. Every task must be
  safe to run twice: check whether the SMS was already sent or the payment already recorded.
- Schedules live in `CELERY_BEAT_SCHEDULE` in `config/settings/base.py`.

## Testing

- pytest against real PostgreSQL, never SQLite: later phases rely on row-level security, trigram
  search and exclusion constraints, which SQLite would silently skip.
- Test services and selectors directly; test endpoints for wiring, permissions and response shape.
- Every endpoint gets a permission test per role (completed in task 14.1).
- Coverage must stay at or above 85%. CI enforces it.

## Commits

- One roadmap task per commit where possible, so history maps onto the roadmap.
- Subject: imperative, specific, at most 72 characters. "Encrypt Ghana Card numbers at rest",
  not "Update models" or "Fix bug".
- Body: why the change was made and what a reviewer needs to know, wrapped at 72 characters.
  Reference requirement IDs (FR-xx, NFR-xx) when the change implements one.
- Tick the task in `docs/ROADMAP.md` in the commit that finishes it.
