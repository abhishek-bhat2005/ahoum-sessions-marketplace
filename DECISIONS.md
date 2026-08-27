# Decisions

## Lock the session row, not a calculated availability value

**Alternatives:** application-only “remaining seats” math, optimistic updates/retries, or a database transaction with row locking.

**Choice:** every booking locks the `Session` row with `select_for_update()` in a transaction. It then checks duplicate, start time, and active count. Capacity changes and soft deletion acquire exactly the same lock.

**Trade-off:** competing reservations for one popular session wait briefly instead of racing. That small serialization cost is preferable to overselling. Application code supplies the workflow invariant (the ordering of lock and checks); PostgreSQL supplies the concurrency primitive. The conditional unique constraint on active `(user, session)` is a separate database invariant, so a code path accidentally bypassing the duplicate check cannot create a second active booking.

## Soft-cancel sessions

**Alternatives:** hard-delete with cascading bookings, hard-delete with protected foreign keys, or mark cancelled.

**Choice:** delete from the creator API changes `Session.status` to `CANCELLED` while booking rows remain protected.

**Trade-off:** cancelled sessions remain in storage and creator history, but it preserves reservation evidence and meets history requirements. The public catalog filters them out.

## Server-side OAuth with cookie refresh tokens

**Alternatives:** SPA OAuth handling, JWTs in localStorage, or server-side code exchange with a refresh cookie.

**Choice:** Django owns the GitHub code exchange and uses state plus PKCE. Access JWTs are returned only to JavaScript memory; refresh JWTs are HttpOnly, SameSite=Lax cookies scoped to the auth path. CSRF tokens protect cookie-authentication operations.

**Trade-off:** the frontend has an extra refresh request after callback, but it never receives the GitHub secret or a token in a URL/localStorage. State needs the Django session cookie, which is intentional.

## Administrator-managed creator enrollment

**Alternatives:** profile toggle, automatic creator status, or a review/admin-controlled role.

**Choice:** GitHub sign-in creates a normal User. A staff member changes `role` using Django admin; profile serialization makes it read-only.

**Trade-off:** enrollment is not self-service yet, but authorization cannot be escalated by editing a profile request.
