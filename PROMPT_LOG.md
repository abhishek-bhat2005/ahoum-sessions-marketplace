# Prompt and AI work log

This is a factual record of material assistant usage during this build, not a claim of unaided authorship.

| Material prompt/work item | Tool/model if known | Output decision | Verification/correction |
| --- | --- | --- | --- |
| Build the Ahoum Sessions Marketplace using React/Vite, Django/DRF, PostgreSQL, GitHub OAuth, Docker Compose, and Nginx; backend/tests first. | Codex (GPT-5) | Accepted as the implementation scope. | Source layout, API, locking service, Compose, and docs were created. |
| Implement final-seat correctness. | Codex (GPT-5) | Accepted: transaction + `select_for_update` + conditional unique constraint. | PostgreSQL `TransactionTestCase` was added; it remains unexecuted because Docker is unavailable. |
| Initial compact React client. | Codex (GPT-5) | Accepted after corrections below. | Production build eventually passed. |
| **Correction 1:** `tsc` reported missing React/JSX declarations. | Local TypeScript compiler | Initial output rejected as incomplete. | Added `@types/react`, `@types/react-dom`, and Vite ambient types; build passed. |
| **Correction 2:** `useEffect(load, [])` returned a Promise. | Local TypeScript compiler | Initial output rejected. | Changed to synchronous effect invoking `void load()`; build passed. |
| **Correction 3:** Windows `npm.cmd run build` could not resolve `tsc`. | Local npm command | Initial script rejected. | Scripts now invoke package-local Node entry points; `npm.cmd run build` passed. |

No deployment, successful PostgreSQL test, OAuth login, or human review is claimed in this log.
