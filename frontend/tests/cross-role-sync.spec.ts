// FR01/04–07/11: changes must reach already-open roles, not just fresh page loads.
import { test, expect, type APIRequestContext } from "@playwright/test";
import { openApp } from "./open-app";
const password = "Local-browser-test-42";
async function mutate(request: APIRequestContext, path: string, data: unknown, method = "POST") {
  const csrf = await (await request.get("/api/v1/auth/csrf")).json();
  return request.fetch("/api/v1" + path, { method, headers: { "X-CSRF-Token": csrf.csrf_token }, data });
}
async function login(request: APIRequestContext, email: string, credential = password) {
  expect((await mutate(request, "/auth/login", { email, password: credential })).ok()).toBeTruthy();
}
async function registerCompany(request: APIRequestContext) {
  const suffix = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const email = `sync-company-${suffix}@example.test`;
  const name = `Workflow Company ${suffix}`;
  expect((await mutate(request, "/auth/register", { role: "company", email, password, company_name: name, display_name: "Workflow Owner" })).ok()).toBeTruthy();
  await login(request, email);
  return { email, name };
}
test("new local company registration updates an already-open administrator dashboard", async ({ browser }) => {
  const adminContext = await browser.newContext();
  await login(adminContext.request, "admin@example.test");
  const admin = await adminContext.newPage();
  await openApp(admin);
  const before = await (await adminContext.request.get("/api/v1/admin/companies?status=pending&limit=1")).json();
  const tile = admin.locator(".role-destination").first();
  await expect(tile).toContainText(`${before.total} awaiting verification`);
  const owner = await browser.newContext();
  await registerCompany(owner.request);
  await admin.bringToFront();
  await admin.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(tile).toContainText(`${before.total + 1} awaiting verification`, { timeout: 8000 });
  await owner.close(); await adminContext.close();
});
test("verification reaches the signed-in company and publication reaches the open student feed", async ({ browser }) => {
  test.setTimeout(60000);
  const ownerContext = await browser.newContext();
  const org = await registerCompany(ownerContext.request);
  const owner = await ownerContext.newPage();
  await openApp(owner);
  await expect(owner.getByText("Company verification: pending", { exact: true })).toBeVisible();
  const adminContext = await browser.newContext();
  await login(adminContext.request, "admin@example.test");
  const organizations = await (await adminContext.request.get("/api/v1/admin/companies?status=pending&limit=100")).json();
  const company = organizations.items.find((item: { company_name: string }) => item.company_name === org.name);
  expect(company).toBeTruthy();
  expect((await mutate(adminContext.request, `/admin/companies/${company.id}/verification`, { status: "verified", expected_version: company.verification_version, reason: "Isolated workflow test organization checked." }, "PATCH")).ok()).toBeTruthy();
  await owner.bringToFront();
  await owner.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(owner.getByText("Company verification: pending", { exact: true })).toHaveCount(0, { timeout: 8000 });
  await expect(owner.getByRole("link", { name: "Create your first listing", exact: true })).toBeVisible();
  const studentContext = await browser.newContext();
  await login(studentContext.request, "student@example.test", "ThinkMedia-Student-2026!");
  const student = await studentContext.newPage();
  await openApp(student);
  const title = `Functional OJT ${Date.now()}`;
  const draftResponse = await mutate(ownerContext.request, "/company/listings", { title, type: "ojt", location: "Legazpi City", skills: ["React"], description: "A real saved listing used only in the isolated workflow test.", requirements: "A valid PDF resume." });
  expect(draftResponse.status()).toBe(201);
  const draft = await draftResponse.json();
  expect((await mutate(ownerContext.request, `/company/listings/${draft.id}/publish`, {}, "POST")).ok()).toBeTruthy();
  await student.bringToFront();
  await student.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(student.getByText(title, { exact: true })).toBeVisible({ timeout: 8000 });
  const publicListing = await (await studentContext.request.get(`/api/v1/listings/${draft.id}`)).json();
  const ownedListing = await (await ownerContext.request.get(`/api/v1/company/listings?limit=100`)).json();
  const owned = ownedListing.items.find((item: { id: string }) => item.id === draft.id);
  expect(publicListing.company_id).toBe(company.id);
  expect(publicListing.company_name).toBe(org.name);
  expect(publicListing.title).toBe(owned.title);
  const updatedName = `Updated ${org.name}`;
  expect((await mutate(ownerContext.request, '/profiles/me', { company_name: updatedName }, 'PATCH')).ok()).toBeTruthy();
  await student.evaluate(() => window.dispatchEvent(new Event('focus')));
  await expect(student.locator('.consumer-company').filter({ hasText: updatedName })).toBeVisible({ timeout: 8000 });
  // Keep both task screens open before writing from the other session.
  await owner.locator('.sidebar').getByRole('link', { name: 'Applicants', exact: true }).click();
  await student.locator('.sidebar').getByRole('link', { name: 'My applications', exact: true }).click();
  const csrf = await (await studentContext.request.get('/api/v1/auth/csrf')).json();
  const submitted = await studentContext.request.post(`/api/v1/listings/${draft.id}/applications`, {
    headers: { 'X-CSRF-Token': csrf.csrf_token },
    multipart: { cover_letter: 'Isolated sync workflow application.', file: {
      name: 'resume.pdf', mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF'),
    } },
  });
  expect(submitted.status()).toBe(201);
  const application = await submitted.json();
  await owner.bringToFront();
  await owner.evaluate(() => window.dispatchEvent(new Event('focus')));
  await expect(owner.getByRole('button').filter({ hasText: title })).toBeVisible({ timeout: 8000 });
  await student.bringToFront();
  await student.evaluate(() => window.dispatchEvent(new Event('focus')));
  await student.getByRole('button').filter({ hasText: title }).click();
  expect((await mutate(ownerContext.request, `/applications/${application.id}/status`, { status: 'under_review' }, 'PATCH')).ok()).toBeTruthy();
  // Polling must update an active session even without a focus event or reload.
  await expect(student.locator('.detail-toolbar').getByText('Under review', { exact: true })).toBeVisible({ timeout: 9000 });
  expect((await mutate(ownerContext.request, `/applications/${application.id}/status`, { status: 'accepted' }, 'PATCH')).ok()).toBeTruthy();
  await expect(student.locator('.detail-toolbar').getByText('Accepted', { exact: true })).toBeVisible({ timeout: 9000 });
  // A profile refresh must not discard a listing the company is still writing.
  await owner.bringToFront();
  await owner.locator('.sidebar').getByRole('link', { name: 'My listings', exact: true }).click();
  await owner.getByRole('button', { name: 'New listing', exact: true }).click();
  await owner.getByLabel('Opportunity title').fill('Unsaved work must survive refresh');
  expect((await mutate(ownerContext.request, '/profiles/me', { display_name: 'Updated Workflow Owner' }, 'PATCH')).ok()).toBeTruthy();
  await owner.evaluate(() => window.dispatchEvent(new Event('focus')));
  await expect(owner.locator('.sidebar-account')).toContainText('Updated Workflow Owner', { timeout: 8000 });
  await expect(owner.getByLabel('Opportunity title')).toHaveValue('Unsaved work must survive refresh');
  await ownerContext.close(); await adminContext.close(); await studentContext.close();
});
