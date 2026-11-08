import { openApp } from "./open-app";
// FR01/02/11, NFR05/09/10 — browser checks against real FastAPI + PostgreSQL.
import { test, expect } from "@playwright/test";
const password = "Local-browser-test-42";
test("student registration, profile persistence, logout and mobile layout", async ({
  page,
}) => {
  const email = `student-${Date.now()}@example.test`;
  await page.setViewportSize({ width: 360, height: 800 });
  await openApp(page, "/");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await page.getByLabel("Full name").fill("José Student");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel(/^Password/).fill(password);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .last()
    .click();
  await expect(page.getByText("Hello, José.", { exact: true })).toBeVisible();
  await expect(page.locator(".sidebar")).toHaveAttribute("inert", "");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(
    page.getByRole("button", { name: "Close navigation" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Open navigation" }),
  ).toBeFocused();
  await page.getByRole("link", { name: "Complete your profile" }).click();
  await page
    .getByLabel("Institution", { exact: true })
    .fill("Bicol University");
  await page.getByLabel("Course or program").fill("BS Computer Science");
  await page
    .getByLabel("Skills", { exact: true })
    .fill("Python, communication");
  await page.getByRole("button", { name: "Save profile" }).click();
  await expect(page.getByRole("status")).toContainText("saved");
  await expect(
    page.getByRole("link", { name: "Continue to opportunities", exact: true }),
  ).toHaveAttribute("href", "#/opportunities");
  await page.reload();
  await expect(page).toHaveURL(/#\/profile$/);
  await expect(page.getByLabel("Institution", { exact: true })).toHaveValue(
    "Bicol University",
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.getByLabel("Interests", { exact: true }).focus();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    animations: "disabled",
    path: "../.impeccable/review/mobile.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible();
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel(/^Password/).fill(password);
  await page
    .getByRole("button", { name: "Sign in", exact: true })
    .last()
    .click();
  await expect(page.getByText("Hello, José.", { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    animations: "disabled",
    path: "../.impeccable/review/desktop.png",
    fullPage: true,
  });
});
test("invalid credentials are readable and do not enter workspace", async ({
  page,
}) => {
  await openApp(page, "/");
  await page.getByLabel("Email address").fill("absent@example.test");
  await page.getByLabel(/^Password/).fill(password);
  await page
    .getByRole("button", { name: "Sign in", exact: true })
    .last()
    .click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible();
});
test("company profile and administrator verification use real role-protected endpoints", async ({
  browser,
}) => {
  const companyContext = await browser.newContext();
  const company = await companyContext.newPage();
  await openApp(company, "/");
  await company
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await company.getByLabel("I’m joining as").selectOption("company");
  const name = `Browser company ${Date.now()}`;
  await company.getByLabel("Full name").fill("Test Recruiter");
  await company.getByLabel("Company name").fill(name);
  await company
    .getByLabel("Email address")
    .fill(`company-${Date.now()}@example.test`);
  await company.getByLabel(/^Password/).fill(password);
  await company
    .getByRole("button", { name: "Create account", exact: true })
    .last()
    .click();
  await expect(
    company.getByText("Company verification: pending"),
  ).toBeVisible();
  await company
    .getByRole("link", { name: "View profile", exact: true })
    .click();
  await company.getByLabel("Contact email").fill("recruiting@example.test");
  await company.getByLabel("Contact phone").fill("+63 912 345 6789");
  await company.getByRole("button", { name: "Save profile" }).click();
  await expect(company.getByRole("status")).toContainText("saved");
  const denied = await company.request.get("/api/v1/admin/companies");
  expect(denied.status()).toBe(403);
  const adminContext = await browser.newContext();
  const admin = await adminContext.newPage();
  await openApp(admin, "/");
  await admin.getByLabel("Email address").fill("admin@example.test");
  await admin.getByLabel(/^Password/).fill(password);
  await admin
    .getByRole("button", { name: "Sign in", exact: true })
    .last()
    .click();
  await admin
    .getByRole("link", { name: "Review companies", exact: true })
    .click();
  const row = admin.locator("article").filter({ hasText: name });
  await row.getByRole("button", { name: "Review", exact: true }).click();
  await admin
    .getByLabel("Reason for decision")
    .fill(
      "Synthetic local test organization; verification workflow test only.",
    );
  await admin.getByRole("button", { name: "Confirm decision" }).click();
  await expect(admin.locator(".notice.success")).toContainText(
    "decision recorded",
  );
  await company.reload();
  await expect(company).toHaveURL(/#\/profile$/);
  await expect(company.locator(".profile-aside .badge")).toHaveText("verified");
  await companyContext.close();
  await adminContext.close();
});
