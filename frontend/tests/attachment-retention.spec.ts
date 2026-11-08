// FR05/07; NFR03/05/09/11: synthetic file-state fixtures, real account sessions.
import {
  test,
  expect,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import { readFile } from "node:fs/promises";
import type { Application } from "../src/marketplace";
import { openApp } from "./open-app";

declare global {
  interface Window {
    retentionBlobCounts?: { created: number; revoked: number };
  }
}
const password = "Local-browser-test-42";
const id = "ad7846bf-a8bc-4f53-9e5b-4d333ced85b4";
const pdf = Buffer.from(
  "%PDF-1.4\nSynthetic private attachment fixture\n%%EOF\n",
);
async function mutate(request: APIRequestContext, path: string, data: unknown) {
  const bootstrap = await request.get("/api/v1/auth/csrf");
  return request.post("/api/v1" + path, {
    headers: { "X-CSRF-Token": (await bootstrap.json()).csrf_token },
    data,
  });
}
async function fixture(request: APIRequestContext): Promise<Application> {
  const email = `retention-${Date.now()}-${Math.random().toString(36).slice(2)}@example.test`;
  expect(
    (
      await mutate(request, "/auth/register", {
        email,
        password,
        role: "student",
        display_name: "Synthetic Retention Learner",
      })
    ).ok(),
  ).toBeTruthy();
  const login = await mutate(request, "/auth/login", { email, password });
  expect(login.ok()).toBeTruthy();
  const user = (await login.json()).user;
  return {
    id,
    reference: "TM-SYNTHETIC-RETENTION",
    listing_id: "cb477988-a9d0-4c91-a10b-fef069fb45ca",
    listing_title: "Synthetic attachment retention opportunity",
    company_name: "Synthetic Review Company",
    student_id: user.id,
    student_name: user.display_name,
    status: "accepted",
    cover_letter:
      "Fictional application text, preserved after attachment expiry.",
    attachment_name: "fictional-resume.pdf",
    attachment_available: true,
    attachment_deleted_at: null,
    created_at: "2026-10-01T09:00:00+08:00",
    history: [
      {
        actor_id: user.id,
        old_status: null,
        new_status: "submitted",
        created_at: "2026-10-01T09:00:00+08:00",
      },
      {
        actor_id: "d41bef79-846e-449f-bef7-6eab19d91910",
        old_status: "submitted",
        new_status: "under_review",
        created_at: "2026-10-02T10:00:00+08:00",
      },
      {
        actor_id: "d41bef79-846e-449f-bef7-6eab19d91910",
        old_status: "under_review",
        new_status: "accepted",
        created_at: "2026-10-03T10:00:00+08:00",
      },
    ],
  };
}
async function openFixture(page: Page, application: Application) {
  await page.route(`**/api/v1/applications/${id}`, (route) =>
    route.fulfill({ json: application }),
  );
  await openApp(page, `/#/applications/${id}`);
  await expect(
    page.getByRole("heading", { name: application.listing_title, exact: true }),
  ).toBeVisible();
}

test("expired metadata preserves the reference, decision and history at 360px", async ({
  page,
  context,
}) => {
  const application = await fixture(context.request);
  application.attachment_available = false;
  application.attachment_name = "expired.pdf";
  application.attachment_deleted_at = "2026-11-07T10:30:00+08:00";
  await page.setViewportSize({ width: 360, height: 800 });
  await openFixture(page, application);
  await expect(
    page.getByRole("heading", { name: "Attachment expired", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(application.reference, { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".detail-toolbar .status-badge")).toHaveText(
    "Accepted",
  );
  await expect(
    page.getByRole("heading", { name: "Status history", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".timeline li")).toHaveCount(3);
  const expiredNotice = page.getByRole("region", {
    name: "Attachment expired",
    exact: true,
  });
  const headingBounds = await expiredNotice.getByRole("heading").boundingBox();
  const explanationBounds = await expiredNotice
    .locator("p")
    .first()
    .boundingBox();
  if (!headingBounds || !explanationBounds)
    throw new Error("Expired-file notice must be visibly laid out.");
  expect(explanationBounds.y).toBeGreaterThanOrEqual(
    headingBounds.y + headingBounds.height - 1,
  );
  await expect(
    page.getByText("Expired (Asia/Manila):", { exact: false }),
  ).toContainText("Nov 7, 2026");
  await expect(page.getByRole("button", { name: /^Download / })).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Confirm status change", exact: true }),
  ).toHaveCount(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../.impeccable/review/expired-attachment-360.png",
    fullPage: true,
  });
});

test("an available private PDF downloads without leaving the application and releases its blob", async ({
  page,
  context,
}, testInfo) => {
  const application = await fixture(context.request);
  await page.addInitScript(() => {
    window.retentionBlobCounts = { created: 0, revoked: 0 };
    const create = URL.createObjectURL.bind(URL);
    const revoke = URL.revokeObjectURL.bind(URL);
    URL.createObjectURL = (blob) => {
      window.retentionBlobCounts!.created++;
      return create(blob);
    };
    URL.revokeObjectURL = (url) => {
      window.retentionBlobCounts!.revoked++;
      revoke(url);
    };
  });
  await page.route(`**/api/v1/applications/${id}/attachment`, (route) =>
    route.fulfill({
      contentType: "application/pdf",
      body: pdf,
      headers: {
        "Cache-Control": "no-store",
        "Content-Disposition": 'attachment; filename="fictional-resume.pdf"',
      },
    }),
  );
  await openFixture(page, application);
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download fictional-resume.pdf", exact: true })
    .click();
  const result = await download;
  expect(result.suggestedFilename()).toBe("fictional-resume.pdf");
  const saved = testInfo.outputPath("synthetic-private.pdf");
  await result.saveAs(saved);
  expect(await readFile(saved)).toEqual(pdf);
  await expect(page).toHaveURL(new RegExp(`#/applications/${id}$`));
  await expect(
    page.getByRole("status").filter({ hasText: "Download started." }),
  ).toBeVisible();
  await expect
    .poll(() => page.evaluate(() => window.retentionBlobCounts?.revoked))
    .toBe(1);
  expect(await page.evaluate(() => window.retentionBlobCounts?.created)).toBe(
    1,
  );
});

test("a 410 download race explains expiry in place and focuses the notice", async ({
  page,
  context,
}) => {
  const application = await fixture(context.request);
  await page.route(`**/api/v1/applications/${id}/attachment`, (route) =>
    route.fulfill({
      status: 410,
      json: {
        error: {
          code: "ATTACHMENT_EXPIRED",
          message: "Synthetic attachment expired under policy.",
        },
      },
    }),
  );
  await openFixture(page, application);
  await page
    .getByRole("button", { name: "Download fictional-resume.pdf", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Attachment expired", exact: true }),
  ).toBeFocused();
  await expect(page).toHaveURL(new RegExp(`#/applications/${id}$`));
  await expect(
    page.getByText(application.reference, { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".timeline li")).toHaveCount(3);
  await expect(page.getByRole("button", { name: /^Download / })).toHaveCount(0);
  await expect(
    page.getByText(
      "The application reference and status history remain available.",
      { exact: false },
    ),
  ).toBeVisible();
});

test("oversized download responses fail safely and keep a retry action", async ({
  page,
  context,
}) => {
  const application = await fixture(context.request);
  const oversized = Buffer.alloc(5 * 1024 * 1024 + 1, "x");
  await page.route(`**/api/v1/applications/${id}/attachment`, (route) =>
    route.fulfill({
      contentType: "application/pdf",
      body: oversized,
      headers: { "Content-Length": String(oversized.length) },
    }),
  );
  await openFixture(page, application);
  await page
    .getByRole("button", { name: "Download fictional-resume.pdf", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("5 MiB limit");
  await expect(
    page.getByRole("button", {
      name: "Download fictional-resume.pdf",
      exact: true,
    }),
  ).toBeEnabled();
  await expect(
    page.getByText(application.reference, { exact: true }),
  ).toBeVisible();
});
