// FR02/04/05/08; NFR05/09: discovery stays usable with real search/filter data and suggestion failure.
import { test, expect } from "@playwright/test";
import { openApp } from "./open-app";
import AxeBuilder from "@axe-core/playwright";

test("job-search layout prioritizes results and preserves combined filters through details", async ({
  page,
}) => {
  const csrf = await (await page.request.get("/api/v1/auth/csrf")).json();
  const login = await page.request.post("/api/v1/auth/login", {
    headers: { "X-CSRF-Token": csrf.csrf_token },
    data: {
      email: "student@example.test",
      password: "ThinkMedia-Student-2026!",
    },
  });
  expect(login.status()).toBe(200);
  const catalog = await (
    await page.request.get("/api/v1/listings?limit=100")
  ).json();
  const listing = catalog.items.find(
    (item: { title: string }) =>
      item.title === "Demo: Python and data OJT practice",
  );
  expect(listing).toBeTruthy();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openApp(page, "/#/opportunities");
  await expect(page.locator(".opportunity-result").first()).toBeVisible();
  await expect(page.locator(".suggestions-preview")).toHaveCount(0);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(
    (await page.locator(".opportunity-result h3").first().boundingBox())!.y,
  ).toBeLessThan(700);
  await page.route("**/api/v1/recommendations?*", (route) =>
    route.fulfill({
      status: 503,
      json: { error: { message: "Synthetic suggestion outage." } },
    }),
  );
  await page.getByRole("button", { name: "For you", exact: true }).click();
  await expect(
    page.getByText("Suggestions are unavailable.", { exact: false }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Browse all opportunities", exact: true })
    .click();
  await expect(page.locator(".opportunity-result").first()).toBeVisible();

  await page.setViewportSize({ width: 360, height: 800 });
  const filters = page.getByRole("button", { name: /Filters/ });
  await expect(filters).toHaveAttribute("aria-expanded", "false");
  await filters.click();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.getByLabel("Keyword", { exact: true }).fill(listing.title);
  await page.getByLabel("Location", { exact: true }).fill(listing.location);
  await page.getByLabel("Type", { exact: true }).selectOption(listing.type);
  await page.getByLabel("Skill", { exact: true }).fill(listing.skills[0]);
  const searched = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/v1/listings" &&
      url.searchParams.get("q") === listing.title &&
      url.searchParams.get("location") === listing.location &&
      url.searchParams.get("skill") === listing.skills[0] &&
      url.searchParams.get("type") === listing.type
    );
  });
  await page
    .getByRole("button", { name: "Apply filters", exact: true })
    .click();
  expect((await searched).ok()).toBeTruthy();
  await expect(
    page
      .locator(".opportunity-result")
      .getByRole("button", { name: listing.title, exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../.impeccable/review/opportunities-search-360.png",
    fullPage: true,
  });
  await page
    .locator(".opportunity-result")
    .getByRole("button", { name: "View opportunity", exact: false })
    .click();
  await expect(
    page.getByRole("button", { name: "Apply to opportunity", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Back to opportunities", exact: true })
    .click();
  await expect(page.getByLabel("Keyword", { exact: true })).toHaveValue(
    listing.title,
  );
  await expect(page.getByLabel("Location", { exact: true })).toHaveValue(
    listing.location,
  );
  await page.reload();
  await expect(page.getByLabel("Skill", { exact: true })).toHaveValue(
    listing.skills[0],
  );
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await expect(page).toHaveURL(/#\/opportunities$/);
  await expect(page.getByLabel("Keyword", { exact: true })).toHaveValue("");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({
    path: "../.impeccable/review/opportunities-search-1440.png",
    fullPage: true,
  });
  await page.unroute("**/api/v1/recommendations?*");
  await page.getByRole("button", { name: "For you", exact: true }).click();
  await page.locator(".preview-row .text-button").first().click();
  await expect(
    page.getByRole("button", { name: "Back to opportunities", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Back to opportunities", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "For you", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
});
