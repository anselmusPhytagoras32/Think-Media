// FR01–05/08, NFR02/05/09: real student account, actual discovery/search and private role access.
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";
test("local consumer account can discover, filter and open actual opportunities on mobile", async ({
  page,
}) => {
  test.setTimeout(90000);
  const token = await (await page.request.get("/api/v1/auth/csrf")).json();
  const response = await page.request.post("/api/v1/auth/login", {
    headers: { "X-CSRF-Token": token.csrf_token },
    data: {
      email: "student@example.test",
      password: "ThinkMedia-Student-2026!",
    },
  });
  expect(response.status()).toBe(200);
  expect((await response.json()).user.role).toBe("student");
  expect((await page.request.get("/api/v1/admin/companies")).status()).toBe(
    403,
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await openApp(page);
  await expect(
    page.getByRole("heading", { name: "Find your next opportunity." }),
  ).toBeVisible();
  await expect(page.locator(".opportunity-card").first()).toBeVisible();
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(
      [
        ...document.querySelectorAll<HTMLImageElement>(
          ".discovery-categories img",
        ),
      ].map((img) => img.decode()),
    );
  });
  const images = await page
    .locator(".discovery-categories img")
    .evaluateAll((imgs) => imgs.map((img) => (img as HTMLImageElement).src));
  expect(new Set(images).size).toBe(3);
  for (const width of [390, 360, 768, 1440]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
    await page.evaluate(() => window.scrollTo(0, 0));
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: `../.impeccable/review/consumer-${width}.png`,
      fullPage: true,
      animations: "disabled",
    });
  }
  await page.setViewportSize({ width: 360, height: 800 });
  for (const width of [360, 1440]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 800 });
    const card = page.locator(".opportunity-card-link").first();
    await card.focus();
    await expect(card).toBeFocused();
    await card.scrollIntoViewIfNeeded();
    await page.screenshot({
      path: `../.impeccable/review/consumer-focus-${width}.png`,
      fullPage: true,
      animations: "disabled",
    });
  }
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("button", { name: "Apply to opportunity" }),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: "Find your next opportunity." }),
  ).toBeVisible();
  await page.setViewportSize({ width: 360, height: 800 });
  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(
    axe.violations.map((x) => ({
      id: x.id,
      nodes: x.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
  await page
    .getByRole("searchbox", { name: "Search opportunities" })
    .fill("Python");
  await page
    .getByRole("button", { name: "Search opportunities", exact: true })
    .click();
  await expect(page).toHaveURL(/#\/opportunities\?search=Python$/);
  await expect(page.getByLabel("Keyword", { exact: true })).toHaveValue(
    "Python",
  );
  await expect(
    page
      .locator(".listing-row")
      .filter({ hasText: "Demo: Python and data OJT practice" }),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Keyword", { exact: true })).toHaveValue(
    "Python",
  );
  await page
    .locator(".listing-row")
    .first()
    .getByRole("button", { name: "View opportunity", exact: false })
    .click();
  await expect(
    page.getByRole("button", { name: "Apply to opportunity" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Back to opportunities" }).click();
  await expect(page.getByLabel("Keyword", { exact: true })).toHaveValue(
    "Python",
  );
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await expect(page).toHaveURL(/#\/opportunities$/);
  await page.reload();
  await expect(page.getByLabel("Keyword", { exact: true })).toHaveValue("");
  await openApp(page, "/#/overview");
  await page.locator(".category-ojt").click();
  await expect(page.getByLabel("Type", { exact: true })).toHaveValue("ojt");
});
