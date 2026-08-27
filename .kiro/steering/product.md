# Product

**Sarai** is a social commerce backend for merchants. This repository (`core`) holds the
server-side application: REST API, admin/back-office, and background job processing.

The target user is a **small to medium sized online seller** — typically someone selling
through social channels who needs real commerce infrastructure behind the storefront.
Sarai is the merchant's operational backend, not a consumer-facing storefront.

Design for that audience: multi-tenant by merchant, sensible defaults over configuration
sprawl, and no assumption that the merchant has a technical team.

## Capability areas

The platform is scoped around these domains. Each is expected to become one or more local
Django apps.

**Catalog**
- Products and variants (options, SKUs, media)
- Inventory tracking and stock movements
- Pricing and promotions (discounts, campaigns, rules)

**Selling**
- Orders and order lifecycle
- Customers and customer profiles

**Integrations**
- Payment services via pluggable adapters
- Delivery/shipping services via pluggable adapters

**Retention (CEM)**
- Loyalty programs and customer retention/engagement

**Insight**
- Merchant analytics and reporting

**AI-assisted services (BYOK)**
- Catalog design assistance (product copy, structure, media suggestions)
- Campaign creation assistance
- **Bring Your Own Key**: merchants supply their own AI provider credentials. Treat those
  keys as secrets — encrypt at rest, never log them, never echo them in API responses or
  admin list views, and never commit them. Every AI feature must degrade gracefully when a
  merchant has no key configured.

**Support**
- Customer support service with ticketing

**Surfaces (cut across everything above)**
- REST API endpoints for each domain
- Admin dashboard coverage for every feature, not just a subset

## Cross-cutting expectations

- **Every feature needs both surfaces.** A domain is not done until it has API endpoints
  *and* admin dashboard coverage.
- **Payments and delivery are adapter-based.** Define a provider-agnostic interface and
  implement concrete providers behind it. Never let provider-specific details leak into
  order or checkout logic.
- **Money, stock, and orders are correctness-critical.** Use `Decimal` for money (never
  float), keep stock adjustments transactional, and prefer explicit state machines over
  free-form status strings.
- **Audit the sensitive domains.** django-auditlog is already wired up; register models
  where a merchant would need a paper trail — orders, inventory movements, pricing,
  payments, refunds.
- **Push slow work to Celery.** Analytics rollups, AI calls, notifications, and provider
  webhooks/retries belong in tasks, not request/response cycles.

## Current state

The project is freshly scaffolded. Infrastructure is wired up and running, but **none of
the domains above exist yet**:

- No local Django apps have been created (`INSTALLED_APPS` has an empty `# Local apps` section).
- No domain models, no business logic, no tests.
- The only endpoint is a health check at `GET /api/health`.

Treat this as greenfield. When asked to build a feature, expect to create a new Django app
rather than extend existing domain code, and check this list before assuming something is
already implemented.

## What is already provided

- **API surface** — two frameworks installed side by side: django-ninja (`/api/`) and DRF
  with an OpenAPI schema (`/api/schema/`, Swagger UI, ReDoc).
- **Admin** — Django admin themed with django-unfold, plus DjangoQL advanced search. This
  is the foundation for the merchant dashboard.
- **Operations dashboard** — Control Room panels under `/admin/` for inspecting Redis,
  cache, Celery, URLs, and signals.
- **Background work** — Celery with Redis as broker, results in the database, and DB-backed
  periodic schedules via django-celery-beat.
- **Audit trail** — django-auditlog middleware is active; model-level tracking is opt-in
  per model unless `AUDITLOG_INCLUDE_ALL_MODELS` is enabled.

## Deployment posture

Runs on SQLite with zero configuration for local development and switches to Postgres
automatically when `POSTGRES_DB` is set. Production hardening (SSL redirect, HSTS, secure
cookies, manifest static files) is gated behind `DEBUG` being off, so nothing extra needs
to be toggled by hand.
