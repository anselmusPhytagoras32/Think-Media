// FR11 / NFR01/03/05/09/11: actual administrator snapshot and explicit error/empty states.
import { test, expect, type APIRequestContext } from "@playwright/test";
import { openApp } from "./open-app";

async function login(request: APIRequestContext) {
  const bootstrap = await request.get("/api/v1/auth/csrf");
  const { csrf_token } = await bootstrap.json();
  expect(
    (
      await request.post("/api/v1/auth/login", {
        headers: { "X-CSRF-Token": csrf_token },
        data: {
          email: "admin@example.test",
          password: "Local-browser-test-42",
        },
      })
    ).ok(),
  ).toBeTruthy();
}

test("administrator reads actual operations snapshot at 360px", async ({
  page,
  context,
}) => {
  await login(context.request);
  await page.setViewportSize({ width: 360, height: 800 });
  const response = page.waitForResponse(
    (value) =>
      value.url().endsWith("/api/v1/admin/operations") &&
      value.request().method() === "GET",
  );
  await openApp(page, "/#/audit");
  const actual = await response;
  expect(actual.status()).toBe(200);
  expect(actual.headers()["cache-control"]).toContain("no-store");
  const data = await actual.json();
  expect(data.scope).toBe("current_process");
  const panel = page.getByRole("region", {
    name: "Local operations",
    exact: true,
  });
  await expect(panel.getByRole("status")).toHaveText(
    "Operations snapshot refreshed.",
  );
  await expect(panel).toContainText("current API process since startup");
  await expect(panel).toContainText(
    "latest 512 API requests, including guidance",
  );
  const field = (label: string) =>
    panel
      .locator("dt")
      .filter({ hasText: new RegExp(`^${label}$`) })
      .locator("+ dd");
  // React development StrictMode may issue an initial snapshot and a second
  // active snapshot. The UI count must include at least the captured requests.
  expect(
    Number((await field("Completed requests").innerText()).replaceAll(",", "")),
  ).toBeGreaterThanOrEqual(data.requests.total);
  await expect(field("Applications stored")).toHaveText(
    new Intl.NumberFormat("en-PH").format(data.storage.application_count),
  );
  await expect(field("External AI calls used")).toHaveText(
    new Intl.NumberFormat("en-PH").format(data.assistant.calls_used),
  );
  await panel.getByText("Request counts by route", { exact: true }).click();
  await expect(panel).toContainText(
    "Personal identifiers, query strings and request contents are excluded.",
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await panel.scrollIntoViewIfNeeded();
  await panel.screenshot({
    path: "../.impeccable/review/operations-360.png",
  });
  await panel
    .getByRole("button", { name: "Refresh operations", exact: true })
    .click();
  await expect(panel.getByRole("status")).toHaveText(
    "Operations snapshot refreshed.",
  );
});

test("operations loading and unavailable state recover without simulated measurements", async ({
  page,
  context,
}) => {
  await login(context.request);
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  let unavailable = true;
  await page.route("**/api/v1/admin/operations", async (route) => {
    if (unavailable) {
      await pending;
      await route.fulfill({
        status: 503,
        json: { error: { message: "Synthetic snapshot unavailable." } },
      });
      return;
    }
    // Explicitly synthetic empty boundary fixture; not a real measurement or health result.
    await route.fulfill({
      json: {
        generated_at: "2026-11-07T12:00:00+08:00",
        started_at: "2026-11-07T12:00:00+08:00",
        scope: "current_process",
        requests: { total: 0, client_errors: 0, server_errors: 0 },
        latency: { sample_count: 0, window_limit: 512, p95_ms: null },
        routes: [],
        storage: {
          database_bytes: 0,
          application_count: 0,
          attachment_bytes: 0,
          expired_session_count: 0,
        },
        assistant: { mode: "disabled", calls_used: 0, call_budget: 0 },
      },
    });
  });
  await openApp(page, "/#/audit");
  const panel = page.getByRole("region", {
    name: "Local operations",
    exact: true,
  });
  await expect(panel.getByRole("status")).toHaveText(
    "Loading operations snapshot…",
  );
  await expect(
    panel.getByRole("button", { name: "Refresh operations", exact: true }),
  ).toBeDisabled();
  release();
  await expect(panel.getByRole("alert")).toContainText(
    "Synthetic snapshot unavailable.",
  );
  await expect(
    panel.getByText("Database storage", { exact: true }),
  ).toHaveCount(0);
  unavailable = false;
  await panel
    .getByRole("button", { name: "Refresh operations", exact: true })
    .click();
  await expect(panel.getByRole("alert")).toHaveCount(0);
  await expect(panel).toContainText("Not measured: no latency samples yet.");
  await panel.getByText("Request counts by route", { exact: true }).click();
  await expect(panel).toContainText(
    "No completed routes recorded in this process yet.",
  );
});
