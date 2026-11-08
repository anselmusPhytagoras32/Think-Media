// FR08/09; NFR05/09: actual recommendation identities, opt-in feedback, and recoverable response states.
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";

test("suggestions keep feedback optional and recover honestly from refresh errors and empty results", async ({
  page,
}) => {
  const email = "suggestion-layout-" + Date.now() + "@example.test";
  const password = "Local-browser-test-42";
  for (const [path, data] of [
    [
      "/auth/register",
      {
        email,
        password,
        display_name: "Synthetic Layout Student",
        role: "student",
      },
    ],
    ["/auth/login", { email, password }],
    [
      "/profiles/me",
      {
        skills: ["React", "Python"],
        interests: ["web development"],
        program: "Computer Science",
      },
    ],
  ] as const) {
    const csrf = await (await page.request.get("/api/v1/auth/csrf")).json();
    const response = await page.request.fetch("/api/v1" + path, {
      method: path === "/profiles/me" ? "PATCH" : "POST",
      headers: { "X-CSRF-Token": csrf.csrf_token },
      data,
    });
    expect(response.ok()).toBeTruthy();
  }
  const response = await page.request.get("/api/v1/recommendations?limit=10");
  expect(response.ok()).toBeTruthy();
  const source = await response.json();
  expect(source.listings.length).toBeGreaterThan(0);
  expect(source.content.length).toBeGreaterThan(0);
  // Real item IDs/projections; only the transport response state is controlled below.
  const fixture = {
    ...source,
    listings: source.listings.slice(0, 1),
    content: source.content.slice(0, 1),
  };
  let phase: "available" | "error" | "empty" = "available";
  await page.route("**/api/v1/recommendations?*", (route) =>
    phase === "error"
      ? route.fulfill({
          status: 503,
          json: { error: { message: "Synthetic recommendation outage." } },
        })
      : route.fulfill({
          json:
            phase === "empty"
              ? { ...fixture, mode: "general", listings: [], content: [] }
              : fixture,
        }),
  );
  const ratingRequests: number[] = [];
  page.on("request", (request) => {
    if (
      request.method() === "POST" &&
      new URL(request.url()).pathname === "/api/v1/interactions"
    ) {
      const body = request.postDataJSON();
      if (body.event_type === "rating") ratingRequests.push(body.rating);
    }
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openApp(page, "/#/suggestions");
  const listing = page.locator(".suggestion-card-listing");
  const content = page.locator(".suggestion-card-content");
  await expect(listing).toContainText(fixture.listings[0].item.title);
  await expect(content).toContainText(fixture.content[0].item.title);
  await expect(listing.locator(".company-logo")).toHaveAttribute(
    "data-company-id",
    fixture.listings[0].item.company_id,
  );
  await expect(content.locator(".resource-artwork")).toHaveAttribute(
    "data-artwork-topic",
    /coding-data|web-portfolio|application-prep|general/,
  );
  await expect(
    listing.getByLabel("Relevance rating (optional)"),
  ).not.toBeVisible();
  expect(ratingRequests).toEqual([]);
  const ratingToggle = listing.getByRole("button", {
    name: "Rate relevance",
    exact: true,
  });
  await ratingToggle.click();
  await expect(ratingToggle).toHaveAttribute("aria-expanded", "true");
  await listing.getByLabel("Relevance rating (optional)").selectOption("4");
  expect(ratingRequests).toEqual([]);
  await ratingToggle.click();
  await expect(
    listing.getByLabel("Relevance rating (optional)"),
  ).not.toBeVisible();
  expect(ratingRequests).toEqual([]);
  await page.getByRole("button", { name: "Learning", exact: true }).click();
  await expect(listing).toHaveCount(0);
  await expect(content).toBeVisible();
  await page
    .getByRole("button", { name: "Opportunities", exact: true })
    .click();
  await expect(content).toHaveCount(0);
  await expect(listing).toBeVisible();
  await page
    .getByRole("button", { name: "All suggestions", exact: true })
    .click();
  for (const width of [1440, 768, 360]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 800 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    expect((await listing.locator("h3").boundingBox())!.y).toBeLessThan(
      width === 360 ? 600 : 700,
    );
    await page.screenshot({
      path: "../.impeccable/review/suggestions-layout-" + width + ".png",
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
  phase = "error";
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Suggestions are unavailable",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".suggestion-card")).toHaveCount(0);
  await expect(page.getByRole("alert")).toContainText("Try again");
  phase = "empty";
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "No opportunities to suggest yet",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "No resources to suggest yet",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".suggestion-mode")).toContainText(
    "A starting point",
  );
  await expect(
    page.getByRole("link", { name: "Browse all opportunities", exact: true }),
  ).toHaveAttribute("href", "#/opportunities");
  await expect(
    page.getByRole("link", {
      name: "Explore the learning library",
      exact: true,
    }),
  ).toHaveAttribute("href", "#/learning");
  await page
    .getByRole("button", {
      name: "Update your skills and interests",
      exact: true,
    })
    .click();
  await expect(page).toHaveURL(/#\/profile$/);
});
