import { openApp } from "./open-app";
// NFR05/09: independent automated WCAG checks, alongside actual keyboard tests.
import { test, expect, APIRequestContext, Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
async function mutate(request: APIRequestContext, path: string, data: unknown) {
  const b = await request.get("/api/v1/auth/csrf");
  const { csrf_token } = await b.json();
  return request.post("/api/v1" + path, {
    headers: { "X-CSRF-Token": csrf_token },
    data,
  });
}
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
}
test("account and role workspaces pass automated accessibility scans", async ({
  browser,
}) => {
  test.setTimeout(180000);
  const password = "Local-browser-test-42";
  const context = await browser.newContext({
    viewport: { width: 360, height: 800 },
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  await openApp(page, "/");
  await scan(page);
  await page
    .getByRole("button", { name: "Create an account", exact: true })
    .click();
  await page.getByLabel("I’m joining as").selectOption("company");
  await scan(page);
  const email = `accessibility-${Date.now()}@example.test`;
  await mutate(context.request, "/auth/register", {
    email,
    password,
    display_name: "Accessibility Student",
    role: "student",
  });
  await mutate(context.request, "/auth/login", { email, password });
  await page.reload();
  await expect(
    page.getByText("Hello, Accessibility.", { exact: true }),
  ).toBeVisible();
  await scan(page);
  for (const label of [
    "My profile",
    "Opportunities",
    "Learning",
    "Suggestions",
  ]) {
    await page.getByRole("button", { name: "Open navigation" }).click();
    await page
      .locator(".sidebar")
      .getByRole("link", { name: new RegExp(label) })
      .click();
    await scan(page);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
  }
  await page.locator(".guidance-bubble-trigger").click();
  await scan(page);
  await page.getByRole("button", { name: "Close guidance", exact: true }).first().click();
  const companyContext = await browser.newContext({
    viewport: { width: 360, height: 800 },
    reducedMotion: "reduce",
  });
  const companyEmail = `accessibility-company-${Date.now()}@example.test`;
  await mutate(companyContext.request, "/auth/register", {
    email: companyEmail, password, display_name: "Company User", role: "company", company_name: "Accessibility Company",
  });
  await mutate(companyContext.request, "/auth/login", { email: companyEmail, password });
  const company = await companyContext.newPage();
  await openApp(company, "/");
  await scan(company);
  for (const label of ["My listings", "Applicants", "Company profile"]) {
    await company.getByRole("button", { name: "Open navigation" }).click();
    await company.locator(".sidebar").getByRole("link", { name: new RegExp(label) }).click();
    await scan(company);
    expect(await company.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
  const adminContext = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    reducedMotion: "reduce",
  });
  await mutate(adminContext.request, "/auth/login", {
    email: "admin@example.test",
    password,
  });
  const admin = await adminContext.newPage();
  await openApp(admin, "/");
  for (const label of [
    "Company verification",
    "Learning content",
    "Content reports",
    "Audit history",
  ]) {
    await admin
      .locator(".sidebar")
      .getByRole("link", { name: new RegExp(label) })
      .click();
    await scan(admin);
  }
  await context.close();
  await companyContext.close();
  await adminContext.close();
});
