# Ahoum Sessions Marketplace

A deliberately small, deployable full-stack marketplace for discovering sessions, reserving seats, and publishing sessions as an enrolled creator. It uses React/TypeScript/Vite, Django REST Framework, PostgreSQL, GitHub OAuth, JWTs, Docker Compose, and Nginx under one origin.

## Quick start

1. Copy `.env.example` to `.env`. Generate a strong `DJANGO_SECRET_KEY` and unique database password; do not keep the example values.
2. Create a GitHub OAuth App. Set its callback URL to `http://localhost/api/auth/github/callback/` for local use, then put its client ID/secret in `.env`. The client secret stays only in the backend container.
3. Start Docker Desktop, then run `docker compose up --build` from this directory.
4. Open `http://localhost`. Nginx serves the frontend and proxies `/api` to Django.

Migrations run before Gunicorn starts. PostgreSQL data persists in the named `postgres_data` volume. The database has no public port mapping.

## Architecture

`browser → Nginx (:80) → frontend static container` and `browser → Nginx /api → Django/Gunicorn → PostgreSQL` share one origin. OAuth starts through Django, which stores a state and PKCE verifier in the server session. The callback exchanges the code server-side, sets a refresh token in an HttpOnly cookie, and redirects without putting a JWT in the URL. The React app then calls refresh and keeps the short-lived access JWT only in memory.

`User.role` is immutable through the profile API. A site administrator enrolls a Creator in Django admin (`/admin`) after normal account creation; this avoids arbitrary self-enrollment. A creator can only create or manage rows whose `creator_id` is their own.

## API summary

- `GET /api/sessions/`, `GET /api/sessions/:id/` — public catalog and detail
- `GET|PATCH /api/profile/` — signed-in profile; role is read-only
- `POST /api/sessions/:id/book/`, `GET /api/bookings/` — reservations and history
- `GET|POST /api/creator/sessions/`, `GET|PATCH|DELETE /api/creator/sessions/:id/` — creator studio
- `GET /api/auth/github/start/`, `GET /api/auth/github/callback/`, `POST /api/auth/refresh/`, `POST /api/auth/logout/` — OAuth/JWT lifecycle

Unsafe refresh/logout requests require Django’s CSRF cookie/header pair. Frontend requests use `credentials: include`; no token is saved to localStorage. OAuth cancellation, invalid state, unavailable OAuth configuration, and provider failures return an understandable callback message.

## Booking correctness and tests

Booking, creator capacity edits, and cancellation all lock the `Session` row inside a PostgreSQL transaction. Booking checks the session state, start time, duplicate booking, and active count only after acquiring that lock. A PostgreSQL partial unique constraint is a second backstop against duplicate active bookings. Cancellation is a soft state transition so booking history is preserved.

`backend/marketplace/tests.py` contains:

- a `TransactionTestCase` final-seat race using two threads/connections and a barrier; it asserts `[201, 409]` and one final active booking;
- duplicate and post-start booking tests;
- invalid JWT, User-to-Creator, and Creator-to-another-Creator authorization tests.

Run the backend suite against the Compose PostgreSQL service with `docker compose exec backend python manage.py test`. Do not treat SQLite as proof of locking correctness; the concurrency test is conditional on database row-lock support and is intended for PostgreSQL.

Verification completed in this workspace: `npm.cmd run build` passed (TypeScript + Vite production output); `manage.py check` passed; migrations were checked; and five Django API/rule tests passed using SQLite. The PostgreSQL-only concurrency test was correctly skipped because SQLite does not support `select_for_update`. Compose startup and the actual PostgreSQL concurrency run were not executed because Docker Desktop’s Linux engine was unavailable. See `DEBUGGING.md`.

## Deployment and HTTPS

Use a production `.env` with `DJANGO_DEBUG=false`, a long random secret key, non-example database password, actual domain in `DJANGO_ALLOWED_HOSTS`, `https://domain` in `CSRF_TRUSTED_ORIGINS`, and `COOKIE_SECURE=true`. Configure the GitHub OAuth callback as `https://domain/api/auth/github/callback/` and set both OAuth redirect URLs to that domain. Terminate TLS at a managed load balancer or extend Nginx with certificate renewal; ensure the proxy forwards `X-Forwarded-Proto`, then add Django `SECURE_PROXY_SSL_HEADER` and HSTS once HTTPS is confirmed. Keep PostgreSQL private to the Docker network and back up the named volume or managed database.

This repository does not claim a deployment: a domain, TLS approach, and GitHub OAuth App credentials still need to be supplied by the owner.

## Limitations and another day

The compact assignment intentionally omits cancellation by attendees, email notifications, pagination/search, audit logs, observability, rate limiting, creator-enrollment workflow UI, and automated CI. With another day I would add these, plus Playwright flows and an actual PostgreSQL CI job for the locking test.
