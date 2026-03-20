# Invoice Management System — Code Review Checklist
> **Purpose:** AI agent execution checklist. Each item states the problem, affected file(s), and what to fix. No code is included — the agent writes the implementation.
> **Deployment:** FastAPI on Render.com free tier. Celery + Upstash Redis. Postgres via Render.
> **Research baseline:** FastAPI 2026 production standards, OWASP 2025, SQLAlchemy 2.0 async patterns, zhanymkanov/fastapi-best-practices.
> **Priority:** 🔴 Critical → 🟠 High → 🟡 Medium → 🟢 Low

---

## SECTION 1 — CONFIRMED BUGS

- [ ] **[1.1] 🔴 Logout does not work**
  - **Files:** `app/services/auth_service.py`, `app/api/v1/endpoints/auth.py`
  - `logout_user()` builds a `JSONResponse` with `delete_cookie()` but returns a plain dict instead. The route discards the response object. The cookie is never deleted. Users cannot log out.
  - Fix: Refactor so the `Response` object is passed into the service or handled directly in the route, ensuring `delete_cookie()` is called on the actual response that is returned to the client.

- [ ] **[1.2] 🔴 `change_invoice_status` logs wrong `old_status`**
  - **File:** `app/services/invoice_service.py`
  - `invoice.status` is assigned `new_status` before the logger fires. `old_status` in the log will always equal `new_status`.
  - Fix: Capture the old status value into a variable before the assignment, then use that variable in the log call.

- [ ] **[1.3] 🔴 `RecurrentBillResponse` has a field that does not exist on the model**
  - **File:** `app/schemas/recurrent_bill.py`
  - `invoice_id: int | None` is defined on the response schema but `RecurrentBill` is a one-to-many parent — it has no `invoice_id` column. This field always serializes as `None`.
  - Fix: Remove `invoice_id` from `RecurrentBillResponse`. If linked invoice IDs are needed, add `invoice_ids: list[int] = []` populated from the relationship.

- [ ] **[1.4] 🔴 `InvoiceResponse` silently drops the `client` relationship**
  - **Files:** `app/schemas/invoice.py`, `app/services/invoice_service.py`
  - `get_invoice_by_id` eagerly loads `Invoice.client` via `joinedload` but `InvoiceResponse` has no `client` field. The DB join runs and the data is discarded.
  - Fix: Add a nested client summary schema to `InvoiceResponse` so the loaded data is actually returned to callers.

- [ ] **[1.5] 🔴 Rate limiting is configured but never applied**
  - **Files:** `app/core/rate_limit.py`, `app/main.py`, `app/api/v1/endpoints/auth.py`
  - A `Limiter` instance is created in `rate_limit.py` but never registered on the FastAPI app and never used as a decorator on any route. All endpoints including `/auth/login` are completely open to brute force.
  - Fix: Register the limiter and its error handler on the app in `main.py`. Apply rate limit decorators to auth endpoints at minimum.

- [ ] **[1.6] 🟠 `init_db()` is called twice on startup**
  - **Files:** `app/config/database.py`, `app/main.py`
  - `database.py` calls `init_db()` at module import time. `main.py` lifespan also calls `init_db()`. Redundant and confusing.
  - Fix: Remove the bare `init_db()` call at the bottom of `database.py`. Keep only the lifespan call in `main.py`.

- [ ] **[1.7] 🟠 `get_db()` retry logic masks real errors and adds latency**
  - **File:** `app/config/database.py`
  - The dependency retries 3 times with exponential backoff on any exception. A misconfigured `DATABASE_URL` causes a 3.5-second delay before every request fails. `pool_pre_ping=True` already handles stale connections at the pool level.
  - Fix: Remove the manual retry loop. Simplify `get_db()` to a plain yield-and-close pattern. Rely on `pool_pre_ping` for connection health.

---

## SECTION 2 — SECURITY

- [ ] **[2.1] 🔴 Password maximum length is 12 characters**
  - **Files:** `app/schemas/user.py`, `app/schemas/auth.py`
  - `max_length=12` on the password field actively prevents strong passwords. OWASP 2025 requires no upper bound (minimum 64 characters allowed). This is weaker than most bank PINs.
  - Fix: Remove `max_length` from the password field or raise it to at least 128.

- [ ] **[2.2] 🔴 No refresh token endpoint — stolen access token is valid for 24 hours**
  - **Files:** `app/core/security.py`, `app/api/v1/endpoints/auth.py`
  - `create_refresh_token()` exists in `security.py` but is never called. There is no `/auth/refresh` endpoint. Access tokens default to 1440 minutes. A stolen token cannot be revoked and remains valid for its full lifetime.
  - Fix: Issue a short-lived access token (15–60 min) and a long-lived refresh token (7 days) on login. Store the refresh token in a separate `httpOnly` cookie. Create `POST /auth/refresh` to validate the refresh cookie and issue a new access token. Clear both cookies on logout.

- [ ] **[2.3] 🔴 CSRF protection is missing**
  - **File:** `app/main.py`
  - JWT is stored in `httpOnly` cookies. With `samesite="lax"`, cookies are sent on top-level cross-site navigations. Without CSRF protection a malicious site can trigger authenticated mutations by tricking a logged-in user.
  - Fix: Add `starlette-csrf` middleware to `main.py`. Exempt login, register, and health endpoints. Add the package to `requirements.txt`.

- [ ] **[2.4] 🟠 `COOKIE_SECURE` defaults to `False` — tokens sent over HTTP**
  - **File:** `app/config/settings.py`
  - Any environment where `COOKIE_SECURE` is not explicitly overridden will transmit JWT cookies over plain HTTP.
  - Fix: Change the default to `True`. Document the `COOKIE_SECURE=False` override in `.env.example` for local dev only.

- [ ] **[2.5] 🟠 `COOKIE_SAMESITE` should be `strict` not `lax`**
  - **File:** `app/config/settings.py`
  - `lax` allows cookies on top-level cross-site navigations. For an invoice management system there is no legitimate cross-site use case. `strict` provides stronger CSRF protection with no UX downside.
  - Fix: Change the default to `"strict"`.

- [ ] **[2.6] 🟠 `passlib` is unmaintained — security debt**
  - **Files:** `app/core/security.py`, `requirements.txt`
  - `passlib==1.7.4` last released in 2020, officially unmaintained. `pwdlib` and `argon2-cffi` are already in `requirements.txt` but unused in code.
  - Fix: Replace `passlib.CryptContext` in `security.py` with `pwdlib` directly. Remove `passlib` from `requirements.txt`.

- [ ] **[2.7] 🟠 `SECRET_KEY` has no minimum entropy validation**
  - **File:** `app/config/settings.py`
  - The production guard only checks if `SECRET_KEY` equals the default string. A developer could set `SECRET_KEY=abc123` and the app starts without warning.
  - Fix: Add a length check in `Settings.__init__` — raise `ValueError` if `SECRET_KEY` is shorter than 32 characters in production.

- [ ] **[2.8] 🟠 Email validator makes a live DNS lookup on every client create/update request**
  - **File:** `app/schemas/client.py`
  - `validate_email(value, check_deliverability=True)` performs a DNS MX record lookup on every `POST /client` and `PATCH /client/{id}`. Blocking network call inside a sync Pydantic validator — slow, unreliable, and prone to false rejections in restricted network environments.
  - Fix: Set `check_deliverability=False`. Run deliverability checks as a background task if needed.

- [ ] **[2.9] 🟠 `TrustedHostMiddleware` uses `"*"` in non-production — disables host validation**
  - **File:** `app/main.py`
  - `allowed_hosts=["*"]` disables host header validation entirely in development and staging.
  - Fix: Replace `"*"` with an explicit list of allowed local hosts for non-production environments.

- [ ] **[2.10] 🟡 CORS origins not locked down in staging**
  - **File:** `app/config/settings.py`
  - The production CORS guard only fires when `ENV == "production"`. Staging environments get permissive dev origins by default.
  - Fix: Require explicit `CORS_ORIGINS` in any non-local environment. Document in `.env.example`.

---

## SECTION 3 — PERFORMANCE & DATABASE

- [ ] **[3.1] 🟠 Entire `analytics_service.py` is N+1 queries**
  - **File:** `app/services/analytics_service.py`
  - Every analytics function loads all records into Python and iterates. `get_total_revenue()` fetches all paid invoices then accesses `invoice.items` per invoice — 1 query + N item queries per dashboard load. Same pattern in `get_outstanding_amount`, `get_overdue_amount`, `get_invoice_status_breakdown`, `get_monthly_revenue`, `get_top_clients`. At 1,000 invoices this is 1,000+ queries per request.
  - Fix: Rewrite all aggregate functions using SQLAlchemy `func.sum()`, `func.count()`, and `GROUP BY`. When Python iteration is unavoidable, use `selectinload` to batch-load relationships in a single query.

- [ ] **[3.2] 🟠 FastAPI is running sync DB sessions — migrate to async**
  - **Files:** `app/config/database.py`, all service files
  - All endpoints use sync `Session` from a sync engine. FastAPI runs sync routes in a threadpool which limits concurrency under load. The 2026 production standard is an async SQLAlchemy engine for FastAPI endpoints with a separate sync engine kept for Celery tasks.
  - Fix: Add an async engine using `asyncpg`. Create an `AsyncSession` dependency for FastAPI routes. Migrate service functions to `async def`. Keep the existing sync `SessionLocal` for Celery tasks only. Add `asyncpg` to `requirements.txt`.

- [ ] **[3.3] 🟠 Default `DATABASE_URL` points to SQLite — incompatible with Render Postgres**
  - **Files:** `app/config/settings.py`, `app/config/database.py`
  - Default is `sqlite:///bot.db`. Pool settings are silently ignored by SQLite. The app is deployed on Render with Postgres but nothing enforces this.
  - Fix: Add a startup guard that raises a clear error if a SQLite URL is detected in a non-development environment.

- [ ] **[3.4] 🟠 `/health` endpoint is static — does not validate database connectivity**
  - **File:** `app/main.py`
  - Returns `{"status": "healthy"}` unconditionally. Render's health check will report the service as up even when the database is down.
  - Fix: Add a readiness check that runs a lightweight DB query with a short timeout. Return `503` if it fails. Keep a separate static liveness route.

- [ ] **[3.5] 🟡 `limit/offset` pagination will degrade on large invoice datasets**
  - **Files:** `app/services/invoice_service.py`, `app/services/client_service.py`, `app/services/payment_service.py`
  - `OFFSET N` forces the DB to scan and discard N rows. At 50k+ records this becomes measurably slow.
  - Fix: Document the limitation and add a maximum page size cap. Plan migration to cursor-based pagination when invoice count grows past 50k rows.

---

## SECTION 4 — MISSING ENDPOINTS & FEATURES

- [ ] **[4.1] 🟠 Expense module is unreachable — no endpoints exist**
  - **Missing files:** `app/api/v1/endpoints/expenses.py`, `app/services/expense_service.py`
  - `Expense` model and schemas are fully defined but no endpoint file exists and the router is not registered. Expenses cannot be created, read, updated, or deleted via the API.
  - Fix: Create the endpoint file and service. Register the router in `app/api/v1/router.py` with prefix `/expenses`. Implement full CRUD matching the pattern in `clients.py`.

- [ ] **[4.2] 🟠 Recurrent bill module is unreachable — no endpoints exist**
  - **Missing files:** `app/api/v1/endpoints/recurrent_bills.py`, `app/services/recurrent_bill_service.py`
  - Same situation as expenses — model and schemas exist, no endpoints are registered.
  - Fix: Create endpoint file and service. Register router with prefix `/recurrent-bills`. Implement full CRUD.

- [ ] **[4.3] 🟠 Users cannot manage their own account — no user endpoints**
  - **Missing file:** `app/api/v1/endpoints/users.py`
  - `UserUpdate` schema exists but there are no user management routes. A registered user cannot change their password, update their username, or view their own profile.
  - Fix: Create `GET /users/me` and `PATCH /users/me` endpoints. Register under a `/users` prefix.

- [ ] **[4.4] 🟡 PDF invoice template has hardcoded company details**
  - **File:** `app/templates/pdf/invoice.html`
  - "Acme Corporation Ltd", a Lagos address, "support@acmecorp.com", and a fake phone number are hardcoded. Every invoice generated shows fake company data.
  - Fix: Add company detail fields to `app/config/settings.py`. Pass them into the Jinja2 template context in `pdf_service.py`. Replace hardcoded strings in the template with template variables.

- [ ] **[4.5] 🟡 Currency stored as opaque integer with no enum or symbol mapping**
  - **Files:** `app/models/invoice.py`, `app/schemas/invoice.py`, `app/services/email_service.py`, `app/templates/pdf/invoice.html`
  - `Invoice.currency` is `Mapped[int]` with `ge=1, le=4` — four mystery integers with no documented meaning. The PDF and email templates hardcode `₦`. The system is broken for any non-Naira invoice.
  - Fix: Define a `CurrencyCode` string enum (NGN, USD, GBP, EUR) with a symbol mapping dict. Change the model column from `int` to the enum. Update PDF and email services to derive the currency symbol dynamically. Create an Alembic migration to convert the integer column.

- [ ] **[4.6] 🟡 No company/business profile model**
  - Company identity is split between hardcoded template strings and settings fields. There is no data structure to support serving more than one business.
  - Fix: Create a `BusinessProfile` SQLAlchemy model (single row per deployment). Fetch it in `pdf_service.py` and `email_service.py` to replace both the hardcoded strings and the settings-based approach.

---

## SECTION 5 — TESTING

- [ ] **[5.1] 🟠 Zero test coverage — no test files exist**
  - **Directory:** `tests/`
  - `tests/conftest.py` sets up fixtures correctly but no test files exist. The entire application has zero automated test coverage.
  - Fix: Create the following test files using the existing `conftest.py` fixtures and a `TestClient` dependency override for `get_db`:
    - `tests/test_auth.py` — register, login, logout, protected endpoint without token
    - `tests/test_clients.py` — CRUD, duplicate email, 404 on missing ID, pagination
    - `tests/test_invoices.py` — create with items, valid/invalid status transitions, delete with payments blocked, PDF generation mocked
    - `tests/test_payments.py` — create payment updates invoice status, duplicate reference rejected, delete reverts invoice status
    - `tests/test_analytics.py` — dashboard returns correct shape, empty DB returns zeros not errors

- [ ] **[5.2] 🟠 Loose test scripts in repo root are not pytest tests and will not run in CI**
  - **Files:** `test_transaction.py`, `test_upstash.py` (repo root)
  - These are manual scripts, not pytest tests. They do not run under `pytest` and give false confidence.
  - Fix: Convert `test_transaction.py` into a proper pytest test in `tests/test_database.py`. Convert `test_upstash.py` into `tests/test_redis.py` with a `pytest.mark.skipif` guard when the Redis URL is not set. Delete the originals from root.

- [ ] **[5.3] 🟡 Celery tasks have no tests**
  - **Missing file:** `tests/test_tasks.py`
  - Email tasks, PDF tasks, and the overdue reminder scheduler have complex retry and error handling logic — none of it tested.
  - Fix: Create `tests/test_tasks.py`. Use `unittest.mock.patch` on email and PDF service functions. Use `celery_app.conf.task_always_eager = True` to run tasks synchronously in tests without a broker.

---

## SECTION 6 — DEPLOYMENT (Render.com)

- [ ] **[6.1] 🟠 No `render.yaml` — deployment is undocumented infrastructure**
  - **Missing file:** `render.yaml`
  - No infrastructure-as-code config for Render exists. Service topology (web + Celery worker + Celery beat), build commands, and environment variable requirements are not captured in the repo.
  - Fix: Create `render.yaml` defining the web service, the Celery worker, and the Celery beat scheduler. Include build command (`pip install -r requirements.txt && alembic upgrade head`), start commands for each service, and environment variable references.

- [ ] **[6.2] 🟠 Celery worker and beat startup are not documented**
  - **File:** `README.md`
  - No instructions exist for starting the Celery worker or beat scheduler. Any deploy without these running silently drops all email, PDF generation, and overdue reminder functionality.
  - Fix: Update README with explicit startup commands for the web server, Celery worker, and Celery beat. Clarify which are required for which features.

- [ ] **[6.3] 🟠 FastAPI version is outdated**
  - **File:** `requirements.txt`
  - `fastapi==0.122.0` — 13 minor versions behind `0.135.1` as of March 2026. Multiple bug fixes and security patches shipped since.
  - Fix: Update `fastapi` and `starlette` to current versions. Review the FastAPI changelog between 0.122 and 0.135 for breaking changes before upgrading.

- [ ] **[6.4] 🟢 README uses `--reload` without clarifying it is development only**
  - **File:** `README.md`
  - `uvicorn app.main:app --reload` must never run in production. The README presents it without context.
  - Fix: Separate dev and production startup commands in the README. Clearly label `--reload` as development only.

---

## SECTION 7 — OBSERVABILITY

- [ ] **[7.1] 🟡 Prometheus metrics are entirely commented out**
  - **Files:** `app/core/metrics.py`, `app/main.py`
  - `metrics.py` is 100% commented out. The `/metrics` route is commented out in `main.py`. The running app has no metrics exposure.
  - Fix: Uncomment `metrics.py`. Add `prometheus-client` to `requirements.txt` if not present. Uncomment the `/metrics` route. Add a request middleware that increments request counters and records duration per route.

- [ ] **[7.2] 🟡 Sentry is configured but never initialized**
  - **Files:** `app/config/settings.py`, `app/main.py`
  - `SENTRY_DSN` is in settings and `sentry-sdk==2.46.0` is in requirements but `sentry_sdk.init()` is never called. Errors are not reported to Sentry.
  - Fix: Call `sentry_sdk.init()` in the `lifespan` function in `main.py`, guarded by `if settings.SENTRY_DSN`.

---

## SECTION 8 — CODE QUALITY

- [ ] **[8.1] 🟡 Duplicate access token expiry settings**
  - **File:** `app/config/settings.py`
  - Both `ACCESS_TOKEN_EXPIRE_MINUTES` and `ACCESS_TOKEN_EXPIRATION` exist with the same default value. `security.py` uses `ACCESS_TOKEN_EXPIRATION`. Inconsistent naming and confusing duplication.
  - Fix: Remove `ACCESS_TOKEN_EXPIRE_MINUTES`. Use `ACCESS_TOKEN_EXPIRATION` as the single source of truth everywhere including the `cookie_max_age` computed field.

- [ ] **[8.2] 🟡 Domain-based project structure recommended as codebase grows**
  - **Directory:** `app/`
  - Current file-type structure (`models/`, `schemas/`, `services/`, `endpoints/`) will become difficult to navigate as more modules are added. The canonical FastAPI production reference recommends domain-based layout.
  - Fix: Plan and execute an incremental migration. Each domain (`auth`, `invoices`, `clients`, `payments`, `expenses`) owns its own `router.py`, `schemas.py`, `models.py`, and `service.py`. Start with `auth` as a pilot before migrating others.

- [ ] **[8.3] 🟢 `.env.example` file is missing**
  - **Missing file:** `.env.example`
  - No environment variable reference exists. `RESEND_API_KEY` is a required field — the app crashes at startup without it. New developers and AI agents have no reference for what variables are needed.
  - Fix: Create `.env.example` listing all variables from `settings.py` with placeholder values and inline comments.

- [ ] **[8.4] 🟢 `reset_database.py` is in repo root — dangerous location**
  - **File:** `reset_database.py`
  - A script that drops and recreates all database tables sitting in the repo root is an accident waiting to happen.
  - Fix: Move to `scripts/reset_database.py`. Add a hard environment guard that refuses to run unless `ENV=development` is explicitly set.

- [ ] **[8.5] 🟢 Loose root test scripts should be deleted after migration to `tests/`**
  - **Files:** `test_transaction.py`, `test_upstash.py`
  - Covered in [5.2]. Delete from root once converted to proper pytest tests.

---

## EXECUTION ORDER

| # | Task | Priority | Ref |
|---|------|----------|-----|
| 1 | Fix logout — cookie never deleted | 🔴 | 1.1 |
| 2 | Fix password max length (12 → 128) | 🔴 | 2.1 |
| 3 | Apply rate limiting to app and auth routes | 🔴 | 1.5 |
| 4 | Add refresh token endpoint | 🔴 | 2.2 |
| 5 | Add CSRF middleware | 🔴 | 2.3 |
| 6 | Fix `old_status` log bug | 🔴 | 1.2 |
| 7 | Fix `RecurrentBillResponse.invoice_id` | 🔴 | 1.3 |
| 8 | Add `client` field to `InvoiceResponse` | 🔴 | 1.4 |
| 9 | Set `COOKIE_SECURE` default to `True` | 🟠 | 2.4 |
| 10 | Set `COOKIE_SAMESITE` default to `strict` | 🟠 | 2.5 |
| 11 | Replace `passlib` with `pwdlib` | 🟠 | 2.6 |
| 12 | Add `SECRET_KEY` entropy validation | 🟠 | 2.7 |
| 13 | Disable live DNS check in email validator | 🟠 | 2.8 |
| 14 | Fix `TrustedHostMiddleware` wildcard | 🟠 | 2.9 |
| 15 | Rewrite analytics with SQL aggregates | 🟠 | 3.1 |
| 16 | Migrate to async SQLAlchemy for FastAPI | 🟠 | 3.2 |
| 17 | Add SQLite guard — enforce Postgres | 🟠 | 3.3 |
| 18 | Remove duplicate `init_db()` call | 🟠 | 1.6 |
| 19 | Add DB connectivity check to `/health` | 🟠 | 3.4 |
| 20 | Create expenses endpoints + service | 🟠 | 4.1 |
| 21 | Create recurrent bills endpoints + service | 🟠 | 4.2 |
| 22 | Create user `/me` endpoints | 🟠 | 4.3 |
| 23 | Update FastAPI to 0.135.1 | 🟠 | 6.3 |
| 24 | Write auth tests | 🟠 | 5.1 |
| 25 | Write invoice + payment tests | 🟠 | 5.1 |
| 26 | Move loose test scripts into `tests/` | 🟠 | 5.2 |
| 27 | Create `render.yaml` | 🟠 | 6.1 |
| 28 | Fix hardcoded PDF company details | 🟡 | 4.4 |
| 29 | Add `CurrencyCode` enum + migration | 🟡 | 4.5 |
| 30 | Simplify `get_db()` retry logic | 🟡 | 1.7 |
| 31 | Write Celery task tests | 🟡 | 5.3 |
| 32 | Initialize Sentry in lifespan | 🟡 | 7.2 |
| 33 | Uncomment Prometheus metrics | 🟡 | 7.1 |
| 34 | Remove duplicate `ACCESS_TOKEN_EXPIRE_MINUTES` | 🟡 | 8.1 |
| 35 | Plan domain-based structure migration | 🟡 | 8.2 |
| 36 | Update README startup commands | 🟢 | 6.4 |
| 37 | Create `.env.example` | 🟢 | 8.3 |
| 38 | Move `reset_database.py` to `scripts/` | 🟢 | 8.4 |

---

*Generated: 2026-03-20 | Research sources: FastLaunchAPI 2026 production guide, zhanymkanov/fastapi-best-practices, OWASP 2025 API Security Top 10, SQLAlchemy 2.0 async migration guide, Render.com FastAPI deployment docs.*
