// FR03/08; NFR05/09: actual catalog topics and stable semantic artwork, including suggestion failure.
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";

test("resource detail keeps its illustration bounded and its title readable at every viewport", async ({
  page,
}) => {
  const csrf = await (await page.request.get("/api/v1/auth/csrf")).json();
  expect(
    (
      await page.request.post("/api/v1/auth/login", {
        headers: { "X-CSRF-Token": csrf.csrf_token },
        data: {
          email: "student@example.test",
          password: "ThinkMedia-Student-2026!",
        },
      })
    ).ok(),
  ).toBeTruthy();
  const catalog = await (
    await page.request.get(
      "/api/v1/content?q=Demo%20guide%3A%20Practice%20Python&limit=20",
    )
  ).json();
  const resource = catalog.items.find(
    (item: { title: string }) =>
      item.title === "Demo guide: Practice Python and SQL safely",
  );
  expect(resource).toBeTruthy();
  for (const width of [1440, 768, 360]) {
    await page.setViewportSize({ width, height: width === 360 ? 800 : 1000 });
    await openApp(page, `/#/learning/${resource.id}`);
    const detail = page.locator(".learning-detail");
    const title = detail.getByRole("heading", {
      name: resource.title,
      exact: true,
    });
    const image = detail.locator(".library-detail-art");
    await expect(title).toBeVisible();
    await expect(image).toBeVisible();
    const imageBox = (await image.boundingBox())!;
    const titleBox = (await title.boundingBox())!;
    const panelBox = (await detail.boundingBox())!;
    expect(imageBox.width).toBeLessThanOrEqual(320);
    expect(imageBox.height).toBeLessThanOrEqual(240);
    expect(titleBox.width).toBeGreaterThan(Math.min(280, panelBox.width - 60));
    expect(titleBox.height).toBeLessThan(160);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await expect(
      detail.getByRole("button", { name: "Open quiz", exact: true }),
    ).toBeVisible();
    await page.screenshot({
      path: `../.impeccable/review/resource-detail-${width}.png`,
      fullPage: true,
    });
  }
});

test("learning library keeps real resources primary, searches topics and preserves semantic artwork", async ({
  page,
}) => {
  const csrf = await (await page.request.get("/api/v1/auth/csrf")).json();
  const login = await page.request.post("/api/v1/auth/login", {
    headers: { "X-CSRF-Token": csrf.csrf_token },
    data: {
      email: "student@example.test",
      password: "ThinkMedia-Student-2026!",
    },
  });
  expect(login.status()).toBe(200);
  const catalog = await (
    await page.request.get("/api/v1/content?limit=100")
  ).json();
  const actualTopics = new Set(
    catalog.items.flatMap((item: { tags: string[] }) => item.tags),
  );
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openApp(page, "/#/learning");
  await expect(page.locator(".library-resource-card").first()).toBeVisible();
  await expect(page.locator(".suggestions-preview")).toHaveCount(0);
  expect(
    (await page.locator(".library-resource-card h3").first().boundingBox())!.y,
  ).toBeLessThan(900);
  await page.getByRole("button", { name: "For you", exact: true }).click();
  const suggestedResource = page
    .locator(".suggestions-preview .preview-row .text-button")
    .first();
  await expect(suggestedResource).toBeVisible();
  await suggestedResource.click();
  await expect(
    page.getByRole("button", { name: "Back to resources", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Back to resources", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "For you", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page
    .getByRole("button", { name: "All resources", exact: true })
    .click();
  const topics = page
    .getByRole("group", { name: "Explore learning topics" })
    .getByRole("button");
  const topic = (await topics.first().innerText()).trim();
  expect(actualTopics.has(topic)).toBeTruthy();
  const topicRequest = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/v1/content" &&
      url.searchParams.get("tag") === topic
    );
  });
  await topics.first().click();
  expect((await topicRequest).ok()).toBeTruthy();
  await expect(page.getByLabel("Topic", { exact: true })).toHaveValue(topic);
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await expect(page.getByLabel("Topic", { exact: true })).toHaveValue("");
  for (const [title, artwork] of [
    ["Demo guide: Prepare your OJT application", "application-prep"],
    ["Demo guide: Build a React portfolio", "web-portfolio"],
    ["Demo guide: Practice Python and SQL safely", "coding-data"],
  ]) {
    await page.getByLabel("Search resources", { exact: true }).fill(title);
    const searched = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname === "/api/v1/content" &&
        url.searchParams.get("q") === title
      );
    });
    await page.getByRole("button", { name: "Search", exact: true }).click();
    expect((await searched).ok()).toBeTruthy();
    const card = page
      .locator(".library-resource-card")
      .filter({ hasText: title });
    await expect(card.locator("img")).toHaveAttribute(
      "data-artwork-topic",
      artwork,
    );
    const source = await card.locator("img").getAttribute("src");
    await card.getByRole("button", { name: title, exact: true }).click();
    await expect(page.locator(".library-detail-art")).toHaveAttribute(
      "src",
      source!,
    );
    await page
      .getByRole("button", { name: "Back to resources", exact: true })
      .click();
    await expect(
      page.getByLabel("Search resources", { exact: true }),
    ).toHaveValue(title);
  }
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await page.route("**/api/v1/recommendations?*", (route) =>
    route.fulfill({
      status: 503,
      json: { error: { message: "Synthetic suggestion outage." } },
    }),
  );
  await page.getByRole("button", { name: "For you", exact: true }).click();
  await expect(
    page.getByText("Suggestions are unavailable.", { exact: false }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Browse all resources", exact: true })
    .click();
  await expect(page.locator(".library-resource-card").first()).toBeVisible();
  for (const width of [1440, 360]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 800 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: `../.impeccable/review/learning-library-${width}.png`,
      fullPage: true,
    });
  }
  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(
    axe.violations.map((violation) => ({
      id: violation.id,
      nodes: violation.nodes.map((node) => node.target),
    })),
  ).toEqual([]);
});
