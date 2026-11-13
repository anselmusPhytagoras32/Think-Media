// FR04/W03; NFR05/09: identity follows the actual company across home, results and detail.
import { test, expect } from "@playwright/test";
import { openApp } from "./open-app";
async function signIn(page: import("@playwright/test").Page) {
  const csrf = await (await page.request.get("/api/v1/auth/csrf")).json();
  expect(
    (
      await page.request.post("/api/v1/auth/login", {
        headers: { "X-CSRF-Token": csrf.csrf_token },
        data: {
          email: "student@example.test",
          password: "ThinkMedia-Student-2026!",
        },
      })
    ).status(),
  ).toBe(200);
}
test("saved company identity is shared across home, opportunity details and results", async ({
  page,
}) => {
  await signIn(page);
  const catalog = await (await page.request.get('/api/v1/listings?limit=1')).json();
  const saved = catalog.items[0];
  expect(saved).toBeTruthy();
  const initials = saved.company_name.trim().split(/\s+/).slice(0, 2).map((word: string) => Array.from(word)[0]).join('').toUpperCase();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openApp(page);
  const card = page
    .locator(".opportunity-card")
    .filter({ hasText: saved.title })
    .first();
  const logo = card.locator(".company-logo");
  await expect(logo).toBeVisible();
  const companyId = await logo.getAttribute("data-company-id");
  expect(companyId).toBeTruthy();
  expect(companyId).toBe(saved.company_id);
  await expect(logo).toHaveText(initials);
  await expect(card.locator('img.company-logo')).toHaveCount(0);
  await expect(card.locator('.consumer-company')).toHaveText(saved.company_name);
  await expect(card.locator(".opportunity-cover .product-artwork")).toHaveCount(
    0,
  );
  await card.locator("a").click();
  const detailLogo = page.locator(".company-detail-cover .company-logo");
  await expect(detailLogo).toHaveAttribute("data-company-id", companyId!);
  await expect(detailLogo).toHaveText(initials);
  await page
    .getByRole("button", { name: "Back to opportunities", exact: true })
    .click();
  await page.getByLabel('Keyword', { exact: true }).fill(saved.title);
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  const rowLogo = page
    .locator(
      `.opportunity-company .company-logo[data-company-id="${companyId}"]`,
    )
    .first();
  await expect(rowLogo).toHaveText(initials);
  await expect(page.locator(".company-detail-cover")).toHaveCount(0);
});
test("other company identities get a named fallback rather than another mock employer logo", async ({
  page,
}) => {
  await signIn(page);
  const catalog = await (
    await page.request.get("/api/v1/listings?limit=1")
  ).json();
  const fixture = {
    ...catalog.items[0],
    company_id: "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
    company_name: "Fictional Cedar Labs",
  };
  await page.route("**/api/v1/listings?*", (route) =>
    route.fulfill({
      json: { items: [fixture], total: 1, limit: 20, offset: 0 },
    }),
  );
  await openApp(page, "/#/opportunities");
  const result = page.locator(".opportunity-result").first();
  await expect(
    result.getByText("Fictional Cedar Labs", { exact: true }),
  ).toBeVisible();
  await expect(result.locator(".company-logo-fallback")).toHaveText("FC");
  await expect(result.locator("img.company-logo")).toHaveCount(0);
});
