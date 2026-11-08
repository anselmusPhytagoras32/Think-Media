import { defineConfig } from "@playwright/test";
// FR01–12/NFR03: never silently send synthetic browser writes to the demo API.
const apiTarget = process.env.PLAYWRIGHT_API_TARGET;
if (!apiTarget) {
  throw new Error(
    "Set PLAYWRIGHT_API_TARGET explicitly to the isolated browser API (normally http://127.0.0.1:8001). See docs/PRESENTATION_READINESS.md.",
  );
}
const targetURL = new URL(apiTarget);
if (
  targetURL.protocol !== "http:" ||
  !["127.0.0.1", "localhost"].includes(targetURL.hostname) ||
  !targetURL.port ||
  targetURL.port === "8000"
) {
  throw new Error(
    "Browser tests require a loopback disposable API, separate from presentation port 8000.",
  );
}
const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5174";
export default defineConfig({
  testDir: "./tests",
  globalSetup: "./tests/wait-api.ts",
  workers: 1,
  use: {
    baseURL,
    headless: true,
    channel: process.env.PLAYWRIGHT_CHANNEL || "chromium",
    reducedMotion: "reduce",
  },
  webServer: {
    command: `npm run dev -- --port ${new URL(baseURL).port || "5173"}`,
    url: baseURL,
    reuseExistingServer: true,
    env: {
      THINKMEDIA_API_TARGET: apiTarget,
    },
  },
});
