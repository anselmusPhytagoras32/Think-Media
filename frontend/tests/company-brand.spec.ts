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
test("mock company logo is shared across home, opportunity details and results", async ({
  page,
}) => {
  await signIn(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openApp(page);
  const card = page
    .locator(".opportunity-card")
    .filter({ hasText: "Demo Practice Studio (synthetic)" })
    .first();
  const logo = card.locator(".company-logo");
  await expect(logo).toBeVisible();
  const companyId = await logo.getAttribute("data-company-id");
  const src = await logo.getAttribute("src");
  expect(companyId).toBeTruthy();
  expect(src).toContain("demo-practice-studio.svg");
  await expect(card.locator(".opportunity-cover .product-artwork")).toHaveCount(
    0,
  );
  expect((await page.request.get(src!)).ok()).toBeTruthy();
  await card.locator("a").click();
  const detailLogo = page.locator(".company-detail-cover .company-logo");
  await expect(detailLogo).toHaveAttribute("data-company-id", companyId!);
  await expect(detailLogo).toHaveAttribute("src", src!);
  await page
    .getByRole("button", { name: "Back to opportunities", exact: true })
    .click();
  const rowLogo = page
    .locator(
      `.opportunity-company .company-logo[data-company-id="${companyId}"]`,
    )
    .first();
  await expect(rowLogo).toHaveAttribute("src", src!);
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
