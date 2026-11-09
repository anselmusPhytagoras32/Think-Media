import { openApp } from "./open-app";
// FR04–07 / NFR02–05: real PostgreSQL-backed workflow, synthetic local accounts.
import { test, expect, APIRequestContext } from "@playwright/test";
const password = "Local-browser-test-42";
async function mutate(
  request: APIRequestContext,
  path: string,
  body: unknown,
  method = "POST",
) {
  const bootstrap = await request.get("/api/v1/auth/csrf");
  const { csrf_token } = await bootstrap.json();
  return request.fetch("/api/v1" + path, {
    method,
    headers: { "X-CSRF-Token": csrf_token },
    data: body,
  });
}
test("verified company publishes, student applies once, owner reviews and closes", async ({
  browser,
}) => {
  test.setTimeout(90000);
  const suffix = Date.now();
  const companyName = `Local Workflow Company ${suffix}`;
  const companyContext = await browser.newContext({ reducedMotion: "reduce" });
  const company = await companyContext.newPage();
  await mutate(companyContext.request, "/auth/register", {
    email: `workflow-company-${suffix}@example.test`,
    display_name: "Workflow Recruiter",
    role: "company",
    company_name: companyName,
    password,
  });
  expect(
    (
      await mutate(companyContext.request, "/auth/login", {
        email: `workflow-company-${suffix}@example.test`,
        password,
      })
    ).ok(),
  ).toBeTruthy();
  const admin = await browser.newContext();
  await mutate(admin.request, "/auth/login", {
    email: "admin@example.test",
    password,
  });
  const queue = await admin.request.get("/api/v1/admin/companies?limit=100");
  const org = (await queue.json()).items.find(
    (x: { company_name: string }) => x.company_name === companyName,
  );
  expect(org).toBeTruthy();
  expect(
    (
      await mutate(
        admin.request,
        `/admin/companies/${org.id}/verification`,
        {
          status: "verified",
          reason: "Synthetic local browser workflow test.",
          expected_version: org.verification_version,
        },
        "PATCH",
      )
    ).ok(),
  ).toBeTruthy();
  await openApp(company, "/");
  await company
    .locator(".sidebar")
    .getByRole("link", { name: "My listings", exact: true })
    .click();
  await company.getByRole("button", { name: "New listing" }).click();
  const title = `OJT developer ${suffix}`;
  await company.getByLabel("Opportunity title").fill(title);
  await company.getByLabel("Location", { exact: false }).fill("Legazpi City");
  await company
    .getByLabel("Skills (separate with commas)")
    .fill("Python, React");
  await company
    .getByLabel("Description (required)")
    .fill("A synthetic local listing for testing application workflows.");
  await company
    .getByLabel("Requirements (required)")
    .fill("Submit a PDF resume.");
  await company.getByRole("button", { name: "Save listing" }).click();
  await expect(
    company.getByText("Listing saved.", { exact: false }),
  ).toBeVisible();
  await company
    .getByRole("button", { name: "Publish listing", exact: true })
    .click();
  await company.getByRole("button", { name: "Confirm publish" }).click();
  await expect(company.locator(".notice.success")).toContainText("published");
  const studentContext = await browser.newContext({
    viewport: { width: 360, height: 800 },
    reducedMotion: "reduce",
  });
  const student = await studentContext.newPage();
  await mutate(studentContext.request, "/auth/register", {
    email: `workflow-student-${suffix}@example.test`,
    display_name: "Workflow Student",
    role: "student",
    password,
  });
  await mutate(studentContext.request, "/auth/login", {
    email: `workflow-student-${suffix}@example.test`,
    password,
  });
  await openApp(student, "/");
  await student.getByRole("button", { name: "Open navigation" }).click();
  await student
    .locator(".sidebar")
    .getByRole("link", { name: "Opportunities", exact: true })
    .click();
  await student.getByLabel("Keyword", { exact: true }).fill(title);
  await student.getByRole("button", { name: "Search", exact: true }).click();
  await student
    .locator(".listing-row")
    .getByRole("button", { name: title, exact: true })
    .click();
  await expect(student).toHaveURL(/#\/opportunities\/[^/]+$/);
  const listingUrl = student.url();
  await student.evaluate(() => {
    window.location.hash =
      "#/opportunities/00000000-0000-0000-0000-000000000000";
  });
  await expect(student.getByRole("alert")).toContainText("Listing not found");
  await expect(
    student.getByRole("heading", { name: title, exact: true }),
  ).toHaveCount(0);
  await expect(
    student.getByRole("button", { name: "Apply to opportunity" }),
  ).toHaveCount(0);
  await openApp(student, listingUrl);
  await student.getByRole("button", { name: "Apply to opportunity" }).click();
  await student
    .getByLabel("Cover letter")
    .fill("I am interested in this OJT opportunity.");
  await student.getByLabel("Resume or requirement").setInputFiles({
    name: "resume.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Invalid local test attachment"),
  });
  await student
    .getByRole("button", { name: "Review application", exact: true })
    .click();
  await expect(student.getByRole("alert")).toContainText(
    "Attach a PDF up to 5 MiB",
  );
  await expect(
    student.getByRole("button", { name: "Confirm and submit" }),
  ).toHaveCount(0);
  await student.getByLabel("Resume or requirement").setInputFiles({
    name: "resume.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from(
      "%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF",
    ),
  });
  await student
    .getByRole("button", { name: "Review application", exact: true })
    .click();
  await expect(
    student.getByRole("heading", { name: "Review your application" }),
  ).toBeVisible();
  await expect(student.locator(".review-summary")).toContainText("resume.pdf");
  await expect(student.locator(".review-summary")).toContainText(companyName);
  await student.evaluate(() => window.scrollTo(0, 0));
  await student.screenshot({
    path: "../.impeccable/review/ux-application-review-360.png",
    fullPage: true,
    animations: "disabled",
  });
  await student.getByRole("button", { name: "Hide application form" }).click();
  await expect(student.locator(".review-summary")).toBeHidden();
  await student.getByRole("button", { name: "Apply to opportunity" }).click();
  await expect(student.locator(".review-summary")).toContainText("resume.pdf");
  await student.getByRole("button", { name: "Edit application" }).click();
  await expect(student.getByLabel("Cover letter")).toHaveValue(
    "I am interested in this OJT opportunity.",
  );
  await expect(student.getByLabel("Resume or requirement")).toHaveValue(
    /resume.pdf$/,
  );
  await student
    .getByRole("button", { name: "Review application", exact: true })
    .click();
  await student.getByRole("button", { name: "Confirm and submit" }).click();
  await expect(student).toHaveURL(/#\/applications\/[^/]+$/);
  await expect(
    student.getByRole("status").filter({ hasText: "Your application is with" }),
  ).toContainText("Your application is with");
  await student.reload();
  await expect(
    student.getByRole("heading", { name: title, exact: true }),
  ).toBeVisible();
  const own = await studentContext.request.get("/api/v1/applications/me");
  const application = (await own.json()).items[0];
  expect(application.reference).toBeTruthy();
  const denied = await admin.request.get(
    `/api/v1/applications/${application.id}/attachment`,
  );
  expect([403, 404]).toContain(denied.status());
  const download = await studentContext.request.get(
    `/api/v1/applications/${application.id}/attachment`,
  );
  expect(download.status()).toBe(200);
  await company
    .locator(".sidebar")
    .getByRole("link", { name: "Applicants", exact: true })
    .click();
  await company.getByRole("button").filter({ hasText: title }).click();
  await company
    .getByLabel("New application status")
    .selectOption("under_review");
  await company.getByRole("button", { name: "Review status change" }).click();
  await expect(company.getByRole("heading", { name: "Review status change" })).toBeFocused();
  await company.getByRole("button", { name: "Change selection" }).click();
  await expect(company.getByLabel("New application status")).toBeFocused();
  await company.getByRole("button", { name: "Review status change" }).click();
  await company.getByRole("button", { name: "Confirm status change" }).click();
  await expect(company.locator(".notice.success")).toContainText("updated");
  await company.getByLabel("New application status").selectOption("accepted");
  await company.getByRole("button", { name: "Review status change" }).click();
  await company.getByRole("button", { name: "Confirm status change" }).click();
  await expect(company.locator(".detail-toolbar .status-badge")).toHaveText(
    "Accepted",
  );
  await student.reload();
  await student.getByRole("button", { name: "Open navigation" }).click();
  await student
    .locator(".sidebar")
    .getByRole("link", { name: "My applications", exact: true })
    .click();
  await student.getByRole("button").filter({ hasText: title }).click();
  await expect(student.locator(".detail-toolbar .status-badge")).toHaveText(
    "Accepted",
  );
  await openApp(student, "/#/overview");
  const homeApplication = student
    .locator(".activity-row")
    .filter({ hasText: title });
  await expect(homeApplication).toContainText("Accepted");
  await student.screenshot({
    path: "../.impeccable/review/ux-home-active-360.png",
    fullPage: true,
    animations: "disabled",
  });
  await homeApplication.click();
  await expect(student).toHaveURL(
    new RegExp(`#/applications/${application.id}$`),
  );
  await expect(
    student.getByRole("heading", { name: title, exact: true }),
  ).toBeVisible();
  await expect(student.locator(".detail-toolbar .status-badge")).toHaveText(
    "Accepted",
  );
  expect(
    await student.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await student.evaluate(() => window.scrollTo(0, 0));
  await student.screenshot({
    animations: "disabled",
    path: "../.impeccable/review/mobile-application.png",
    fullPage: true,
  });
  await company
    .locator(".sidebar")
    .getByRole("link", { name: "My listings", exact: true })
    .click();
  await company.getByRole("button", { name: title, exact: true }).click();
  await company
    .getByRole("button", { name: "Close listing", exact: true })
    .click();
  await company.getByRole("button", { name: "Confirm close" }).click();
  await expect(company.locator(".notice.success")).toContainText("closed");
  await company.setViewportSize({ width: 1440, height: 1000 });
  await company.evaluate(() => window.scrollTo(0, 0));
  await company.screenshot({
    animations: "disabled",
    path: "../.impeccable/review/desktop-listing.png",
    fullPage: true,
  });
  await companyContext.close();
  await studentContext.close();
  await admin.close();
});
