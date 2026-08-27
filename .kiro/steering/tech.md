# Tech Stack

## Runtime and tooling

- **Python 3.14** (pinned in `.python-version`, `requires-python = ">=3.14"`)
- **uv** for dependency and environment management. Always use uv; never call `pip`
  directly and never edit `uv.lock` by hand.
- Local virtualenv lives at `.venv/`.

## Frameworks and libraries

| Concern | Library |
| --- | --- |
| Web framework | Django 6.0+ |
| API (primary) | django-ninja |
| API (alternate) + schema | djangorestframework, drf-spectacular (+ sidecar) |
| Admin theme | django-unfold |
| Admin search | djangoql |
| Ops dashboard | dj-control-room (Redis, cache, Celery, URLs, signals panels) |
| Background tasks | celery[redis], django-celery-beat, django-celery-results |
| Cache | django-redis |
| Database | psycopg2-binary (Postgres), SQLite fallback |
| Audit logging | django-auditlog |
| CORS | django-cors-headers |
| Dev debugging | django-debug-toolbar |
| Config | python-dotenv |
| WSGI server | gunicorn |

## Commands

Prefix every Python command with `uv run`.

```bash
# Dependencies
uv sync                                  # install/refresh from uv.lock
uv add <package>                         # add a dependency (updates pyproject + lock)
uv remove <package>

# Django
uv run python manage.py check
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py startapp <name>
uv run python manage.py collectstatic --noinput
uv run python manage.py test                       # no tests exist yet

# Dev server (the user runs this; do not launch it from a tool call)
uv run python manage.py runserver

# Celery (each in its own terminal, run by the user)
uv run celery -A Sarai worker -l info
uv run celery -A Sarai beat -l info

# Production
uv run gunicorn Sarai.wsgi:application
```

`uv run python manage.py check` is the fast smoke test after touching settings, URLs, or
models. There is no configured linter, formatter, or test framework yet, so do not assume
`ruff`/`pytest` are available. If the user wants them, add them via `uv add --dev`.

## Configuration conventions

All environment-specific values are read in `Sarai/settings.py` through three helpers:

```python
env("KEY", default)        # string, treats "" as unset
env_bool("KEY", default)   # accepts 1/true/yes/on
env_list("KEY", default)   # comma-separated -> list[str]
```

Rules to follow:

- Never hardcode environment-specific values. Route them through `env*` helpers with a
  development-friendly default so the project keeps working with no `.env` present.
- Every new variable must be added to `.env.example` with a safe placeholder.
- `.env` is gitignored and must never be committed or read back into chat output.
- Settings are grouped by concern with `# ---` banner comments. Put new settings in the
  matching section, or add a new banner-delimited section.
- Celery is configured with the `CELERY_` prefix inside Django settings
  (`config_from_object("django.conf:settings", namespace="CELERY")`). Do not create a
  separate Celery config file.
- Behavior that should differ between dev and prod keys off `DEBUG` rather than a separate
  settings module. There is a single `settings.py`; keep it that way unless asked.

## Choosing an API framework

Both are wired up. Unless the user says otherwise, prefer **django-ninja** for new
endpoints: register the app's router in `Sarai/api.py` via `api.add_router(...)`. DRF is
available for anything needing its serializer/viewset ecosystem, and its defaults are
`SessionAuthentication` + `IsAuthenticated` with page-size-25 pagination.

New API endpoints require authentication by default. `auth=None` on a ninja endpoint (as
used by the health check) makes it public — call that out explicitly whenever you add one.
