import { openApp } from "./open-app";
// FR01–05/11, NFR05/09: local task navigation and truthful recovery with real API data.
import { test, expect, APIRequestContext } from "@playwright/test";
async function loginStudent(request: APIRequestContext) {
  const password = "Local-browser-test-42";
  const email = `workspace-${Date.now()}@example.test`;
  for (const [path, data] of [
    [
      "register",
      { email, password, display_name: "María Student", role: "student" },
    ],
    ["login", { email, password }],
  ] as const) {
    const token = await (await request.get("/api/v1/auth/csrf")).json();
    const response = await request.post(`/api/v1/auth/${path}`, {
      headers: { "X-CSRF-Token": token.csrf_token },
      data,
    });
    expect(response.ok()).toBeTruthy();
  }
}
test("real home, quick navigation, reload, browser Back and drawer focus", async ({
  page,
}) => {
  await loginStudent(page.request);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openApp(page, "/");
  await expect(page.getByText("Hello, María.", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "No applications yet" }),
  ).toBeVisible();
  await expect(page.locator(".welcome-panel,.chapter-art")).toHaveCount(0);
  await page.screenshot({
    path: "../.impeccable/review/ux-home-desktop.png",
    fullPage: true,
  });
  for (const width of [768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: `../.impeccable/review/ux-home-${width}.png`,
      fullPage: true,
    });
  }
  await page
    .getByRole("navigation", { name: "Quick navigation" })
    .getByRole("link", { name: "OJT opportunities" })
    .click();
  await expect(page).toHaveURL(/#\/opportunities$/);
  await page.getByRole("link", { name: "Skip to content" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main")).toBeFocused();
  await expect(page).toHaveURL(/#\/opportunities$/);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Available opportunities" }),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "Quick navigation" })
    .getByRole("link", { name: "Learning" })
    .click();
  await expect(page).toHaveURL(/#\/learning$/);
  await page.goBack();
  await expect(page).toHaveURL(/#\/opportunities$/);
  await page.getByRole("button", { name: "More navigation" }).click();
  await expect(
    page.getByRole("dialog", { name: "Navigation drawer" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "More navigation" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "More navigation" }).click();
  await page
    .getByRole("button", { name: "Getting started", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Get ready for your OJT." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page
    .getByRole("button", { name: "Go to workspace", exact: true })
    .click();
  await expect(page).toHaveURL(/#\/opportunities$/);
  await expect(
    page.getByRole("heading", { name: "Available opportunities" }),
  ).toBeVisible();
  expect((await page.request.get("/api/v1/auth/me")).status()).toBe(200);
});
test("home failure explains missing activity and retries against the real endpoint", async ({
  page,
}) => {
  await loginStudent(page.request);
  await page.route("**/api/v1/applications/me?limit=4", (route) =>
    route.abort(),
  );
  await openApp(page, "/");
  await expect(page.getByRole("alert")).toContainText(
    "Some recent activity could not be loaded",
  );
  await expect(
    page.getByRole("heading", { name: "No applications yet" }),
  ).toHaveCount(0);
  await page.unroute("**/api/v1/applications/me?limit=4");
  await page.getByRole("button", { name: "Reload activity" }).click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "No applications yet" }),
  ).toBeVisible();
});

test("resource URL changes clear old content and failed detail requests can retry", async ({
  page,
}) => {
  await loginStudent(page.request);
  const content = await (
    await page.request.get("/api/v1/content?limit=1")
  ).json();
  expect(content.items.length).toBeGreaterThan(0);
  const item = content.items[0];
  const url = `/#/learning/${item.id}`;
  await openApp(page, url);
  await expect(
    page.getByRole("heading", { name: item.title, exact: true }),
  ).toBeVisible();
  await page.evaluate(() => {
    window.location.hash = "#/learning/00000000-0000-0000-0000-000000000000";
  });
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: item.title, exact: true }),
  ).toHaveCount(0);
  await page.route(`**/api/v1/content/${item.id}`, (route) => route.abort());
  await openApp(page, url);
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: item.title, exact: true }),
  ).toHaveCount(0);
  await page.unroute(`**/api/v1/content/${item.id}`);
  await page
    .getByRole("button", { name: "Retry loading", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: item.title, exact: true }),
  ).toBeVisible();
});
