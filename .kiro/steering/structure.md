# Project Structure

## Layout

```
core/                          # repo root, also the Django BASE_DIR
├── manage.py                  # entrypoint; DJANGO_SETTINGS_MODULE = "Sarai.settings"
├── pyproject.toml             # project metadata + dependencies (uv)
├── uv.lock                    # lockfile — never edit by hand
├── .python-version            # 3.14
├── .env                       # local secrets, gitignored
├── .env.example               # documented template, committed
├── db.sqlite3                 # dev database, gitignored
└── Sarai/                     # project configuration package
    ├── __init__.py            # re-exports celery_app so autodiscovery works
    ├── settings.py            # single settings module, section-banner organized
    ├── urls.py                # root URLconf
    ├── api.py                 # django-ninja NinjaAPI root + router registration
    ├── celery.py              # Celery app
    ├── asgi.py
    └── wsgi.py
```

Note the capitalized `Sarai/` package name — imports are `from Sarai.settings import ...`,
not `sarai`. Keep that casing exactly.

## Directories created on demand

These are referenced by settings but do not exist yet. Create them only when needed:

- `templates/` — project-level template dir (already in `TEMPLATES["DIRS"]`).
- `static/` — extra static sources; only added to `STATICFILES_DIRS` if the folder exists.
- `staticfiles/` — `collectstatic` output. Gitignored, never edit.
- `media/` — user uploads. Gitignored.

## Adding a local Django app

Apps are created as top-level packages next to `manage.py` (Django's default from
`startapp`), not nested under an `apps/` directory.

1. `uv run python manage.py startapp <name>`
2. Register it in `INSTALLED_APPS` under the `# Local apps` comment at the end of the list.
   Ordering in that list is deliberate — `unfold` entries must stay above
   `django.contrib.admin`, and the Control Room block keeps base → panels → dashboard order.
   Do not reshuffle existing entries.
3. Wire up the URLs:
   - django-ninja: define a `Router` in `<app>/api.py` and register it in `Sarai/api.py`
     with `api.add_router("/<name>/", <name>_router)`.
   - Anything else: `include()` it from `Sarai/urls.py`.
4. Celery tasks go in `<app>/tasks.py` — `autodiscover_tasks()` picks them up automatically
   with no extra registration.
5. Admin classes go in `<app>/admin.py`. Use django-unfold's `ModelAdmin` base so the theme
   applies, and mix in `DjangoQLSearchMixin` where advanced search is useful.
6. Opt models into audit logging in `<app>/apps.py` (`ready()`) or `<app>/admin.py` with
   `auditlog.register(Model)`, unless `AUDITLOG_INCLUDE_ALL_MODELS` is on.

## URL map

| Path | Purpose |
| --- | --- |
| `/admin/` | Django admin (unfold-themed) |
| `/admin/dj-control-room/` | Control Room dashboard |
| `/admin/dj-{redis,cache,celery,urls,signals}-panel/` | individual ops panels |
| `/api/` | django-ninja API (`/api/health` is the only endpoint today) |
| `/api/schema/` | OpenAPI schema (DRF / drf-spectacular) |
| `/api/schema/swagger-ui/`, `/api/schema/redoc/` | schema browsers |
| `/__debug__/` | debug toolbar, `DEBUG` only |

Ordering matters in `Sarai/urls.py`: all Control Room panel routes are declared **before**
`path("admin/", admin.site.urls)` because the admin URLconf would otherwise swallow them.
Add new `admin/`-prefixed routes above that line.

## Code style

Existing code follows these patterns — match them:

- Module-level docstrings on every file in `Sarai/`.
- Imports grouped stdlib → third-party → local, with local imports relative inside the
  `Sarai` package (`from .api import api`).
- Double-quoted strings and trailing commas in multi-line literals.
- `pathlib.Path` for filesystem paths, built off `BASE_DIR` — no string concatenation.
- Comments explain *why* a line is order-sensitive or non-obvious, not what it does.
