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

## Environment limitation: Docker engine unavailable

`docker build` first failed on the Docker buildx lock under sandboxing; after permission was granted it reached Docker but reported that `dockerDesktopLinuxEngine` did not exist. This means Docker Desktop’s Linux engine was not running. No Compose or PostgreSQL test result is claimed. The host Django check and SQLite API tests were run separately; start Docker Desktop and run `docker compose up --build`, then `docker compose exec backend python manage.py test` to complete PostgreSQL verification.
