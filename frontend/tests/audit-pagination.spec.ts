// FR11, NFR05/09/11: bounded audit streams and operations rows on desktop/mobile.
import { test, expect } from "@playwright/test";
import { openApp } from "./open-app";

test("administrator can page audit streams independently and page route counts", async ({ page }) => {
  const csrf = await (await page.request.get("/api/v1/auth/csrf")).json();
  expect((await page.request.post("/api/v1/auth/login", {
    headers: { "X-CSRF-Token": csrf.csrf_token },
    data: { email: "admin@example.test", password: "Local-browser-test-42" },
  })).ok()).toBeTruthy();

  for (const [path, prefix] of [
    ["audit-events", "Verification event"],
    ["content-events", "Content event"],
  ]) {
    await page.route(`**/api/v1/admin/${path}*`, async (route) => {
      const url = new URL(route.request().url());
      const offset = Number(url.searchParams.get("offset") || 0);
      const limit = Number(url.searchParams.get("limit") || 20);
      await route.fulfill({ json: {
        total: 45,
        limit,
        offset,
        items: Array.from({ length: Math.min(limit, 45 - offset) }, (_, index) => ({
          id: `${path}-${offset + index}`,
          action: `${prefix} ${offset + index + 1}`,
          reason: "Recorded review",
          actor_id: "00000000-0000-0000-0000-000000000001",
          created_at: "2026-11-14T08:00:00+08:00",
        })),
      } });
    });
  }
  await page.route("**/api/v1/admin/operations", async (route) => {
    await route.fulfill({ json: {
      generated_at: "2026-11-14T08:00:00+08:00",
      started_at: "2026-11-14T07:00:00+08:00",
      scope: "current_process",
      requests: { total: 45, client_errors: 0, server_errors: 0 },
      latency: { sample_count: 0, window_limit: 512, p95_ms: null },
      routes: Array.from({ length: 45 }, (_, index) => ({ method: "GET", route: `/route-${index + 1}`, count: 1 })),
      storage: { database_bytes: 0, application_count: 0, attachment_bytes: 0, expired_session_count: 0 },
      assistant: { mode: "disabled", calls_used: 0, call_budget: 0 },
    } });
  });

  await page.setViewportSize({ width: 360, height: 800 });
  await openApp(page, "/#/audit");
  const verification = page.getByRole("region", { name: "Company verification" });
  const content = page.getByRole("region", { name: "Content and moderation" });
  await expect(verification.getByRole("heading", { name: "Verification event 1", exact: true })).toBeVisible();
  await expect(content.getByRole("heading", { name: "Content event 1", exact: true })).toBeVisible();
  await verification.getByRole("button", { name: "Next" }).click();
  await expect(verification.getByRole("heading", { name: "Verification event 21", exact: true })).toBeVisible();
  await expect(verification.getByRole("heading", { name: "Company verification" })).toBeInViewport();
  await expect(verification.getByText("21–40 of 45")).toBeVisible();
  await expect(content.getByRole("heading", { name: "Content event 1", exact: true })).toBeVisible();
  await verification.getByRole("button", { name: "Next" }).click();
  await expect(verification.getByRole("heading", { name: "Verification event 41", exact: true })).toBeVisible();
  await expect(verification.getByText("41–45 of 45")).toBeVisible();
  await expect(verification.getByRole("button", { name: "Next" })).toBeDisabled();
  await content.getByRole("button", { name: "Next" }).click();
  await expect(content.getByRole("heading", { name: "Content event 21", exact: true })).toBeVisible();
  await verification.getByRole("button", { name: "Previous" }).click();
  await expect(verification.getByRole("heading", { name: "Verification event 21", exact: true })).toBeVisible();

  await page.getByText("Request counts by route").click();
  const routes = page.getByRole("navigation", { name: "Request route pages" });
  await expect(page.getByText("GET /route-1 — 1 requests")).toBeVisible();
  await routes.getByRole("button", { name: "Next" }).click();
  await expect(page.getByText("GET /route-21 — 1 requests")).toBeVisible();
  await expect(page.getByText("Request counts by route")).toBeInViewport();
  await expect(page.getByText("GET /route-1 — 1 requests")).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.screenshot({ path: "../.impeccable/review/audit-pagination-360.png", fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.screenshot({ path: "../.impeccable/review/audit-pagination-1440.png", fullPage: true });
});
