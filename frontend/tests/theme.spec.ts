// NFR03/05/09: local appearance preference, readable role workspaces, safe storage failure.
import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";

test("light and dark appearance can be changed at sign-in and survive reload", async ({
  page,
}) => {
  await openApp(page);
  await page
    .getByRole("button", { name: "Switch to dark mode", exact: true })
    .click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  expect(
    await page.evaluate(
      () => getComputedStyle(document.documentElement).colorScheme,
    ),
  ).toBe("dark");
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Switch to light mode", exact: true }),
  ).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  const scan = await new AxeBuilder({ page }).analyze();
  expect(
    scan.violations.filter(
      (issue) => issue.impact === "serious" || issue.impact === "critical",
    ),
  ).toEqual([]);
  await page.screenshot({
    path: "../.local/dark-signin-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 360, height: 800 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../.local/dark-signin-mobile.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Switch to light mode", exact: true })
    .click();
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.addInitScript(() => {
    Object.defineProperty(Storage.prototype, "getItem", {
      value() {
        throw new Error("Storage blocked");
      },
    });
    Object.defineProperty(Storage.prototype, "setItem", {
      value() {
        throw new Error("Storage blocked");
      },
    });
  });
  await page.reload();
  await page
    .getByRole("button", { name: "Skip introduction", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Switch to dark mode", exact: true })
    .click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});

async function signIn(page: Page, email: string, password: string) {
  const csrf = (await (await page.request.get("/api/v1/auth/csrf")).json())
    .csrf_token;
  expect(
    (
      await page.request.post("/api/v1/auth/login", {
        headers: { "X-CSRF-Token": csrf },
        data: { email, password },
      })
    ).ok(),
  ).toBeTruthy();
}

test("mobile More changes appearance across student pages and the chat", async ({
  page,
}) => {
  test.setTimeout(90000);
  await signIn(page, "student@example.test", "ThinkMedia-Student-2026!");
  await page.setViewportSize({ width: 360, height: 800 });
  await openApp(page, "/#/more");
  await page
    .locator("#main")
    .getByRole("button", { name: "Switch to dark mode", exact: true })
    .click();
  for (const route of [
    "overview",
    "learning",
    "opportunities",
    "profile",
    "assistant",
  ]) {
    await page.goto("/#/" + route);
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await expect(page.locator("#main h1").first()).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    const result = await new AxeBuilder({ page }).analyze();
    expect(
      result.violations.filter(
        (issue) => issue.impact === "serious" || issue.impact === "critical",
      ),
    ).toEqual([]);
    if (route === "opportunities")
      await page.screenshot({
        path: "../.local/dark-opportunities-mobile.png",
        fullPage: true,
      });
  }
  await page.setViewportSize({ width: 1440, height: 960 });
  await page.goto("/#/overview");
  await expect(page.locator("#main h1").first()).toBeVisible();
  await page.screenshot({
    path: "../.local/dark-home-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Switch to light mode", exact: true })
    .click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("dark appearance keeps instructor, company and administrator workspaces readable", async ({
  browser,
}) => {
  test.setTimeout(90000);
  for (const role of ["instructor", "company", "administrator"]) {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 960 },
    });
    const page = await context.newPage();
    if (role === "administrator") {
      await signIn(page, "admin@example.test", "Local-browser-test-42");
    } else {
      const csrf = (await (await page.request.get("/api/v1/auth/csrf")).json())
        .csrf_token;
      const email = `dark-${role}-${crypto.randomUUID()}@example.test`;
      const password = "Dark-mode-browser-2026!";
      expect(
        (
          await page.request.post("/api/v1/auth/register", {
            headers: { "X-CSRF-Token": csrf },
            data: {
              email,
              password,
              role,
              display_name: "Fictional dark mode check",
              ...(role === "company"
                ? { company_name: "Fictional dark mode company" }
                : {}),
            },
          })
        ).ok(),
      ).toBeTruthy();
      await signIn(page, email, password);
    }
    await openApp(page, "/#/overview");
    await page
      .getByRole("button", { name: "Switch to dark mode", exact: true })
      .click();
    const route =
      role === "administrator"
        ? "verification"
        : role === "instructor"
          ? "authoring"
          : "opportunities";
    await page.goto("/#/" + route);
    await expect(page.locator("#main h1").first()).toBeVisible();
    if (role === "instructor")
      await page
        .getByRole("button", { name: "New skill category", exact: true })
        .click();
    const result = await new AxeBuilder({ page }).analyze();
    expect(
      result.violations.filter(
        (issue) => issue.impact === "serious" || issue.impact === "critical",
      ),
    ).toEqual([]);
    await page.screenshot({
      path: `../.local/dark-${role}.png`,
      fullPage: true,
    });
    await context.close();
  }
});
