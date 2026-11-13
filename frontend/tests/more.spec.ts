// FR01–11; NFR05/09: a real mobile route, correct role destinations and account actions.
import { test, expect, Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";
async function login(page: Page, email: string, password: string) {
  const csrf = await (await page.request.get("/api/v1/auth/csrf")).json();
  expect(
    (
      await page.request.post("/api/v1/auth/login", {
        headers: { "X-CSRF-Token": csrf.csrf_token },
        data: { email, password },
      })
    ).ok(),
  ).toBeTruthy();
}
test("More opens a full page from a scrolled mobile home and keeps normal navigation and account actions", async ({
  page,
}) => {
  await login(page, "student@example.test", "ThinkMedia-Student-2026!");
  await page.setViewportSize({ width: 360, height: 800 });
  await openApp(page);
  await expect(page.locator(".opportunity-card").first()).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  const more = page.getByRole("link", { name: "More navigation", exact: true });
  await more.click();
  await expect(page).toHaveURL(/#\/more$/);
  await expect(
    page.getByRole("heading", { name: "More", exact: true }),
  ).toBeVisible();
  await expect(more).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.locator("#main")).toBeFocused();
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe(
    "hidden",
  );
  await expect(page.locator("#main-sidebar")).toHaveAttribute("inert", "");
  const menu = page.getByRole("navigation", { name: "Workspace destinations" });
  await expect(
    menu.getByRole("link", { name: "Suggestions", exact: true }),
  ).toHaveAttribute("href", "#/suggestions");
  // FR10: guidance now opens in place from every workspace destination.
  const guidance = page.locator(".guidance-bubble-trigger");
  await guidance.click();
  await expect(
    page.getByRole("dialog", { name: "OJT guidance", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(guidance).toBeFocused();
  await expect(guidance).toHaveAttribute("aria-expanded", "false");
  await expect(
    menu.getByRole("link", { name: "Company verification", exact: true }),
  ).toHaveCount(0);
  await expect(
    menu.getByRole("link", { name: "My applications", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: "../.impeccable/review/more-360.png",
    fullPage: true,
  });
  await page.locator(".more-account").click();
  await expect(page).toHaveURL(/#\/profile$/);
  await page.goBack();
  await expect(page).toHaveURL(/#\/more$/);
  await page.reload();
  await expect(more).toHaveAttribute("aria-current", "page");
  await menu.getByRole("link", { name: "Learning", exact: true }).click();
  await expect(page).toHaveURL(/#\/learning$/);
  await more.click();
  await page
    .locator(".more-page")
    .getByRole("button", { name: "Sign out", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Login to your account", exact: true }),
  ).toBeVisible();
});
test("administrator More shows administration destinations and omits student-only work", async ({
  page,
}) => {
  await login(page, "admin@example.test", "Local-browser-test-42");
  await page.setViewportSize({ width: 390, height: 844 });
  await openApp(page, "/#/more");
  const menu = page.getByRole("navigation", { name: "Workspace destinations" });
  await expect(
    menu.getByRole("link", { name: "Company verification", exact: true }),
  ).toBeVisible();
  await expect(
    menu.getByRole("link", { name: "Audit history", exact: true }),
  ).toBeVisible();
  await expect(
    menu.getByRole("link", { name: "My applications", exact: true }),
  ).toHaveCount(0);
  await menu
    .getByRole("link", { name: "Company verification", exact: true })
    .click();
  await expect(page).toHaveURL(/#\/verification$/);
});
