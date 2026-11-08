# ThinkMedia web client

React + TypeScript + Vite. FR01–02, FR11 / NFR02–06, 09–10.

```bash
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Start FastAPI separately on port 8000 using ../backend/README.md. Vite proxies `/api` to FastAPI; requests use the real PostgreSQL-backed API, HttpOnly cookies and a freshly bootstrapped CSRF token for mutations. No mock application data or localStorage credentials.

```bash
npm run build
npx playwright install chromium
# Browser tests require an explicitly configured separate disposable API.
# See docs/PRESENTATION_READINESS.md for Windows/WSL commands.
PLAYWRIGHT_API_TARGET=http://127.0.0.1:8001 PLAYWRIGHT_BASE_URL=http://127.0.0.1:5174 npm test
```

Browser tests need a running API and a migrated disposable development database, separate from the backend test database. The verification test needs a synthetic `admin@example.test` administrator with password `Local-browser-test-42` provisioned only in that disposable DB. These are test-only values and no account is installed automatically. Never point tests at production.

All account/profile, verification, marketplace/application/review, learning/quiz/moderation, suggestions/ratings and resource-guidance flows use actual API routes. Optional guidance satisfaction feedback is persisted privately. External AI stays disabled; local approved-resource lookup is enabled only through the backend configuration. Build output lives in dist and is not deployment authorization.

The browser suite includes automated axe WCAG checks across account and role workspaces, plus real keyboard and end-to-end workflow checks. It waits for FastAPI health before running. On this test host Chromium uses `LD_LIBRARY_PATH=/tmp/thinkmedia-browser-runtime/usr/lib/x86_64-linux-gnu`; standard installations should install the normal Playwright Chromium system dependencies. These temporary extracted libraries and disposable databases do not survive a host reboot.
