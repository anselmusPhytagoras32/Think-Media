import { defineConfig } from "@playwright/test";
const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5173";
export default defineConfig({
  testDir: "./tests",
  globalSetup: "./tests/wait-api.ts",
  workers: 1,
  use: {
    baseURL,
    headless: true,
    channel: "chromium",
    reducedMotion: "reduce",
  },
  webServer: {
    command: `npm run dev -- --port ${new URL(baseURL).port || "5173"}`,
    url: baseURL,
    reuseExistingServer: true,
    env: {
      THINKMEDIA_API_TARGET:
        process.env.PLAYWRIGHT_API_TARGET || "http://127.0.0.1:8000",
    },
  },
});
