# Debugging record

Only issues actually encountered while building are recorded below.

## 1. TypeScript could not type React/JSX

- **Diagnosis:** direct `tsc -b` reported missing declarations for `react`, `react-dom/client`, JSX intrinsic elements, and the CSS side-effect import.
- **Root cause:** the initial minimal frontend package omitted `@types/react` and `@types/react-dom`; it also lacked Vite’s ambient client declaration.
- **Fix:** added those dev dependencies and `src/vite-env.d.ts`.
- **Verification:** `npm.cmd run build` completed TypeScript checking and Vite production bundling successfully.

## 2. Creator studio effect returned a Promise

- **Diagnosis:** TypeScript reported that `useEffect(load, [])` was invalid because `load` returns `Promise<void>`.
- **Root cause:** React effects may return only cleanup functions, not asynchronous work.
- **Fix:** wrapped it in a synchronous effect that invokes `void load()`.
- **Verification:** the final TypeScript build passed.

## 3. Nginx returned 502 after recreating the backend

- **Diagnosis:** Django was healthy but the browser received `502 Bad Gateway` after a backend rebuild.
- **Root cause:** Nginx had resolved the old Docker IP address of the recreated backend container and retained it.
- **Fix:** configured Docker’s DNS resolver (`127.0.0.11`) and used a variable upstream so Nginx resolves the backend dynamically. The Nginx configuration also now proxies `/admin/` to Django.
- **Verification:** the live `http://127.0.0.1/api/health/` request returned HTTP 200 through Nginx; GitHub OAuth and Django admin subsequently worked.

## Environment readiness resolved

Docker Desktop’s Linux engine was initially unavailable. Once started, Compose built all containers, PostgreSQL became healthy, and `docker compose exec backend python manage.py test --keepdb` passed all six tests against PostgreSQL.
