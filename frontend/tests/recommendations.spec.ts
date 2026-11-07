import { openApp } from "./open-app";
// FR08–09: actual profile ranking, optional explicit rating, real resource navigation.
import { test, expect, APIRequestContext } from "@playwright/test";
const password = "Local-browser-test-42";
async function mutate(
  request: APIRequestContext,
  path: string,
  data: unknown,
  method = "POST",
) {
  const b = await request.get("/api/v1/auth/csrf");
  const { csrf_token } = await b.json();
  return request.fetch("/api/v1" + path, {
    method,
    headers: { "X-CSRF-Token": csrf_token },
    data,
  });
}
test("profile suggestions expose real resources and save optional ratings", async ({
  browser,
}) => {
  test.setTimeout(60000);
  const suffix = Date.now(),
    title = `React development preparation ${suffix}`;
  const admin = await browser.newContext();
  await mutate(admin.request, "/auth/login", {
    email: "admin@example.test",
    password,
  });
  const created = await mutate(admin.request, "/admin/content", {
    title,
    summary: "React web development preparation.",
    body: "React components and accessible web development. Synthetic local recommendation test content.",
    tags: ["React", "web development"],
    status: "published",
  });
  expect(created.status()).toBe(201);
  const resource = await created.json();
  const context = await browser.newContext({
    viewport: { width: 360, height: 800 },
    reducedMotion: "reduce",
  });
  const email = `suggestions-${suffix}@example.test`;
  await mutate(context.request, "/auth/register", {
    email,
    display_name: "Suggestion Student",
    role: "student",
    password,
  });
  await mutate(context.request, "/auth/login", { email, password });
  expect(
    (
      await mutate(
        context.request,
        "/profiles/me",
        {
          skills: ["React"],
          interests: ["web development"],
          program: "Computer Science",
        },
        "PATCH",
      )
    ).status(),
  ).toBe(200);
  const response = await context.request.get(
    "/api/v1/recommendations?limit=10",
  );
  expect(response.status()).toBe(200);
  const recommendations = await response.json();
  expect(
    recommendations.content.some(
      (s: { item: { id: string } }) => s.item.id === resource.id,
    ),
  ).toBeTruthy();
  expect(recommendations.alpha).toBe(1);
  const page = await context.newPage();
  await openApp(page, "/");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page
    .locator(".sidebar")
    .getByRole("link", { name: "Suggestions", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Suggestions for you" }),
  ).toBeVisible();
  const row = page.locator("article").filter({ hasText: title });
  await expect(row).toBeVisible();
  await row.getByLabel("Relevance rating (optional)").selectOption("5");
  await row.getByRole("button", { name: "Share rating", exact: true }).click();
  await expect(row.getByRole("status")).toContainText("rating was saved");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "../.impeccable/review/mobile-suggestions.png",
    fullPage: true,
    animations: "disabled",
  });
  await row.getByRole("button", { name: "Read resource", exact: true }).click();
  await expect(
    page.getByText(
      "React components and accessible web development. Synthetic local recommendation test content.",
      { exact: true },
    ),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: "Suggestions for you" }),
  ).toBeVisible();
  await context.close();
  await admin.close();
});
