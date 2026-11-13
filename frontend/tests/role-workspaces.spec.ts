// FR02/06/07/11, W05/W08, NFR05/09: role dashboards and decisions against isolated APIs.
import {
  test,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";
import { reviewCompany } from "./company-queue";
const password = "Local-browser-test-42";
async function mutate(
  request: APIRequestContext,
  path: string,
  data: unknown,
  method = "POST",
) {
  const csrf = await (await request.get("/api/v1/auth/csrf")).json();
  return request.fetch("/api/v1" + path, {
    method,
    headers: { "X-CSRF-Token": csrf.csrf_token },
    data,
  });
}
async function login(request: APIRequestContext, email = "admin@example.test") {
  expect(
    (await mutate(request, "/auth/login", { email, password })).ok(),
  ).toBeTruthy();
}
async function company(request: APIRequestContext) {
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const email = `role-company-${suffix}@example.test`;
  const name = `Fictional Design Practice ${suffix}`;
  expect(
    (
      await mutate(request, "/auth/register", {
        role: "company",
        email,
        password,
        company_name: name,
        display_name: "Practice Recruiter",
      })
    ).ok(),
  ).toBeTruthy();
  await login(request, email);
  return { email, name };
}
async function noOverflow(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
}
async function scan(page: Page) {
  await page.waitForLoadState("networkidle");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(
    results.violations.map((item) => ({
      id: item.id,
      nodes: item.nodes.map((node) => node.target),
    })),
  ).toEqual([]);
}

test("admin and company home use the student visual system with real tasks at 360px, tablet and desktop", async ({
  browser,
}) => {
  test.setTimeout(90000);
  const adminContext = await browser.newContext();
  await login(adminContext.request);
  const admin = await adminContext.newPage();
  await openApp(admin);
  await expect(
    admin.locator(".role-destinations .role-destination"),
  ).toHaveCount(3);
  await expect(
    admin.getByRole("link", { name: "Review companies", exact: true }),
  ).toHaveAttribute("href", "#/verification");
  await expect(admin.locator(".admin-role-guide")).toHaveCount(0);
  const companyContext = await browser.newContext();
  await company(companyContext.request);
  const employer = await companyContext.newPage();
  await openApp(employer);
  await expect(
    employer.getByText("Company verification: pending", { exact: true }),
  ).toBeVisible();
  await expect(
    employer.getByRole("link", {
      name: "Complete company profile",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    employer.getByRole("link", {
      name: "Create your first listing",
      exact: true,
    }),
  ).toHaveCount(0);
  for (const [width, height] of [
    [1440, 1000],
    [768, 1000],
    [360, 800],
  ]) {
    for (const [name, page] of [
      ["admin", admin],
      ["company", employer],
    ] as const) {
      await page.setViewportSize({ width, height });
      await noOverflow(page);
      await expect(
        page.locator(".role-destination .workspace-art"),
      ).toHaveCount(3);
      await page.screenshot({
        path: `../.impeccable/review/${name}-workspace-new-${width}.png`,
        fullPage: true,
        animations: "disabled",
      });
      if (width !== 768) await scan(page);
    }
  }
  await openApp(employer, "/#/opportunities?new=1");
  await expect(
    employer.getByRole("heading", {
      name: "Create an opportunity",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    employer.getByRole("button", { name: "New listing", exact: true }),
  ).toBeDisabled();
  await adminContext.close();
  await companyContext.close();
});

test("verification has a focused mobile review, preserves validation errors and records the actual decision", async ({
  browser,
}) => {
  test.setTimeout(60000);
  const companyContext = await browser.newContext();
  const org = await company(companyContext.request);
  const adminContext = await browser.newContext();
  await login(adminContext.request);
  const list = await (
    await adminContext.request.get("/api/v1/admin/companies?limit=100")
  ).json();
  const record = list.items.find(
    (item: { company_name: string }) => item.company_name === org.name,
  );
  expect(record).toBeTruthy();
  const admin = await adminContext.newPage();
  await admin.setViewportSize({ width: 1440, height: 1000 });
  await openApp(admin, "/#/verification");
  await reviewCompany(admin, org.name);
  await expect(
    admin.getByRole("heading", { name: `Review ${org.name}`, exact: true }),
  ).toBeFocused();
  await expect(admin).toHaveURL(new RegExp(`#/verification/${record.id}$`));
  await admin.reload();
  await expect(
    admin.getByRole("heading", { name: `Review ${org.name}`, exact: true }),
  ).toBeVisible();
  await admin.screenshot({
    path: "../.impeccable/review/verification-new-1440.png",
    fullPage: true,
  });
  await scan(admin);
  await admin.setViewportSize({ width: 360, height: 800 });
  await expect(admin.locator(".verification-queue")).not.toBeVisible();
  await expect(admin.getByLabel("Decision", { exact: true })).toHaveValue("");
  await admin.getByLabel("Decision", { exact: true }).selectOption("verified");
  await admin
    .getByLabel("Reason for decision", { exact: true })
    .fill(
      "Fictional local organization evidence checked for an isolated acceptance test.",
    );
  await admin.route(
    `**/api/v1/admin/companies/${record.id}/verification`,
    (route) =>
      route.fulfill({
        status: 422,
        json: {
          error: {
            message: "Check the review reason.",
            fields: { reason: ["Fixture review reason needs correction."] },
          },
        },
      }),
  );
  await admin
    .getByRole("button", { name: "Confirm decision", exact: true })
    .click();
  await expect(
    admin.getByLabel("Reason for decision", { exact: true }),
  ).toHaveAttribute("aria-invalid", "true");
  await expect(
    admin.getByLabel("Reason for decision", { exact: true }),
  ).not.toHaveValue("");
  await noOverflow(admin);
  await admin.evaluate(() => window.scrollTo(0, 0));
  await admin.screenshot({
    path: "../.impeccable/review/verification-new-360.png",
    fullPage: true,
  });
  await scan(admin);
  await admin.unroute(`**/api/v1/admin/companies/${record.id}/verification`);
  await admin
    .getByRole("button", { name: "Confirm decision", exact: true })
    .click();
  await expect(admin.locator(".notice.success")).toHaveText(
    "Verification decision recorded.",
  );
  const verified = await (
    await adminContext.request.get(`/api/v1/admin/companies/${record.id}`)
  ).json();
  expect(verified.verification_status).toBe("verified");
  const employer = await companyContext.newPage();
  await openApp(employer);
  await expect(
    employer.getByRole("link", {
      name: "Create your first listing",
      exact: true,
    }),
  ).toBeVisible();
  await employer
    .getByRole("link", { name: "Create your first listing", exact: true })
    .click();
  await expect(employer).toHaveURL(/#\/opportunities\?new=1$/);
  await expect(
    employer.getByRole("heading", {
      name: "Create an opportunity",
      exact: true,
    }),
  ).toBeVisible();
  await employer.reload();
  await expect(
    employer.getByRole("heading", {
      name: "Create an opportunity",
      exact: true,
    }),
  ).toBeVisible();
  await employer.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(employer).toHaveURL(/#\/opportunities$/);
  await expect(
    employer.getByRole("heading", {
      name: "Create an opportunity",
      exact: true,
    }),
  ).toHaveCount(0);
  expect(
    (await companyContext.request.get("/api/v1/admin/companies")).status(),
  ).toBe(403);
  await adminContext.close();
  await companyContext.close();
});

test("failed dashboard and queue reads show retry rather than invented empty results", async ({
  page,
}) => {
  await login(page.request);
  await page.route("**/api/v1/admin/companies?**", (route) =>
    route.fulfill({
      status: 503,
      json: { error: { message: "Fixture queue unavailable." } },
    }),
  );
  await openApp(page);
  await expect(page.getByRole("alert")).toContainText(
    "Could not load companies",
  );
  await expect(
    page.getByRole("heading", { name: "No companies waiting", exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("link", { name: "Review companies", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Could not load organizations",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "No pending organizations",
      exact: true,
    }),
  ).toHaveCount(0);
  await page.unroute("**/api/v1/admin/companies?**");
  await page
    .getByRole("button", { name: "Retry loading", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Could not load organizations",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(page.locator(".verification-company").first()).toBeVisible();
});

test("a stale verification decision preserves the reason and refreshes to the recorded state", async ({
  browser,
}) => {
  const companyContext = await browser.newContext();
  const org = await company(companyContext.request);
  const adminContext = await browser.newContext();
  await login(adminContext.request);
  const list = await (
    await adminContext.request.get("/api/v1/admin/companies?limit=100")
  ).json();
  const record = list.items.find(
    (item: { company_name: string }) => item.company_name === org.name,
  );
  expect(record).toBeTruthy();
  const admin = await adminContext.newPage();
  await openApp(admin, `/#/verification/${record.id}`);
  await admin.getByLabel("Decision", { exact: true }).selectOption("verified");
  const reason = "Fictional evidence checked before the concurrent decision.";
  await admin.getByLabel("Reason for decision", { exact: true }).fill(reason);
  expect(
    (
      await mutate(
        adminContext.request,
        `/admin/companies/${record.id}/verification`,
        {
          status: "verified",
          expected_version: record.verification_version,
          reason: "Fictional concurrent review recorded through another tab.",
        },
        "PATCH",
      )
    ).ok(),
  ).toBeTruthy();
  await admin
    .getByRole("button", { name: "Confirm decision", exact: true })
    .click();
  await expect(admin.getByRole("alert")).toBeVisible();
  await expect(
    admin.getByLabel("Reason for decision", { exact: true }),
  ).toHaveValue(reason);
  await expect(
    admin.getByRole("button", { name: "Confirm decision", exact: true }),
  ).toBeDisabled();
  await admin
    .getByRole("button", { name: "Refresh company details", exact: true })
    .click();
  await expect(admin.locator(".verification-recorded")).toContainText(
    "This company is verified",
  );
  await expect(
    admin.getByRole("button", { name: "Confirm decision", exact: true }),
  ).toHaveCount(0);
  await adminContext.close();
  await companyContext.close();
});
