// FR01–05 / NFR05/09: optional first use, persistence, recovery and keyboard access.
import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const welcomeKey = "thinkmedia.welcome.v1";
const headings = [
  "Get ready for your OJT.",
  "Find an opportunity that fits.",
  "Keep every application in view.",
];

async function scan(page: Page) {
  await page.waitForLoadState("networkidle");
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(
    result.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      nodes: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
}

test("first-use introduction has accessible steps and opens real registration", async ({
  page,
}) => {
  test.setTimeout(90000);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: headings[0] })).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  await page.locator(".onboarding-art").evaluate(async (node) => {
    await (node as HTMLImageElement).decode();
  });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "../.impeccable/review/illustrated-onboarding-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.setViewportSize({ width: 360, height: 800 });
  await page.screenshot({
    path: "../.impeccable/review/illustrated-onboarding-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
  await scan(page);
  await expect(page.locator(".onboarding")).toHaveAttribute("data-step", "1");

  await page.getByRole("button", { name: "Next", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: headings[1] })).toBeFocused();
  await scan(page);
  await page.getByRole("button", { name: "Back", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: headings[0] })).toBeFocused();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByRole("heading", { name: headings[2] })).toBeFocused();
  await expect(page.locator(".onboarding")).toHaveAttribute("data-step", "3");
  await scan(page);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Create your account", exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("I’m joining as")).toBeVisible();
  expect(
    await page.evaluate((key) => localStorage.getItem(key), welcomeKey),
  ).toBe("seen");
  await page.reload();
  await expect(page.locator(".onboarding")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Login to your account", exact: true }),
  ).toBeVisible();
});

test("introduction can be skipped, stays dismissed and can be replayed", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Skip introduction" }).click();
  await expect(
    page.getByRole("heading", { name: "Login to your account", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(page.locator(".onboarding")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Getting started", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: headings[0] })).toBeVisible();
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Login to your account", exact: true }),
  ).toBeVisible();
});

test("blocked browser storage does not prevent entry to the app", async ({
  page,
}) => {
  await page.addInitScript((key) => {
    const getItem = Storage.prototype.getItem;
    const setItem = Storage.prototype.setItem;
    Storage.prototype.getItem = function (name: string) {
      if (name === key)
        throw new DOMException("Storage is blocked", "SecurityError");
      return getItem.call(this, name);
    };
    Storage.prototype.setItem = function (name: string, value: string) {
      if (name === key)
        throw new DOMException("Storage is blocked", "SecurityError");
      return setItem.call(this, name, value);
    };
  }, welcomeKey);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: headings[0] })).toBeVisible();
  await page.getByRole("button", { name: "Skip introduction" }).click();
  await expect(page.locator(".onboarding")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Login to your account", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Show password" }).click();
  await expect(page.getByLabel(/^Password/)).toHaveAttribute("type", "text");
  await expect(page.locator(".onboarding")).toHaveCount(0);
});
