// FR10/W07, NFR03/05/09: real shell, bounded fixtures, no live-provider requests.
import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";

async function signIn(page: Page) {
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
  await openApp(page);
}

test("guidance keeps the composer visible across phone, tablet, desktop and short viewports", async ({
  page,
}) => {
  test.setTimeout(90000);
  await signIn(page);
  await page.locator(".guidance-bubble-trigger").click();
  const panel = page.getByRole("dialog", { name: "OJT guidance", exact: true });
  for (const [width, height] of [
    [1440, 1000],
    [768, 900],
    [360, 800],
    [390, 844],
    [844, 390],
  ]) {
    await page.setViewportSize({ width, height });
    await expect(panel).toBeVisible();
    await expect(panel).toHaveAttribute("aria-modal", String(width <= 720));
    await expect(
      panel.getByRole("textbox", { name: "Your question", exact: true }),
    ).toBeInViewport();
    await expect(
      panel.getByRole("button", { name: "Ask for guidance", exact: true }),
    ).toBeInViewport();
    const box = await panel.boundingBox();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.y).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(width + 1);
    expect(box!.y + box!.height).toBeLessThanOrEqual(height + 1);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    if (width === 360 || width === 1440) {
      await page.screenshot({
        path: `../.impeccable/review/guidance-new-${width}.png`,
        animations: "disabled",
      });
      expect(
        (
          await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
            .analyze()
        ).violations,
      ).toEqual([]);
    }
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  const original = (await panel.boundingBox())!.width;
  await panel.getByRole("button", { name: "Expand guidance panel" }).click();
  expect((await panel.boundingBox())!.width).toBeGreaterThan(original);
  await panel.getByRole("button", { name: "Reduce guidance panel" }).click();
  await page.keyboard.press("Escape");
  await expect(panel).not.toBeVisible();
  await expect(page.locator(".guidance-bubble-trigger")).toBeFocused();
});

test("suggestions, pending answers, sources, retry and clearing work inside the mobile sheet", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await signIn(page);
  const resource = (
    await (await page.request.get("/api/v1/content?limit=1")).json()
  ).items[0];
  expect(resource).toBeTruthy();
  let release: (() => void) | undefined;
  let fail = false;
  const requested: string[] = [];
  await page.route("**/api/v1/assistant", async (route) => {
    requested.push(route.request().postDataJSON().question);
    if (fail) {
      fail = false;
      await route.fulfill({
        status: 503,
        json: { error: { message: "Fixture guidance unavailable." } },
      });
      return;
    }
    if (requested.length === 1)
      await new Promise<void>((resolve) => {
        release = resolve;
      });
    await route.fulfill({
      json: {
        answer:
          "Fictional approved guidance for layout verification.\n\n" +
          "Prepare examples of your skills. ".repeat(60),
        sources: [{ id: resource.id, title: resource.title }],
        uncertainty: false,
        mode: "external",
      },
    });
  });
  await page.locator(".guidance-bubble-trigger").click();
  const panel = page.getByRole("dialog", { name: "OJT guidance", exact: true });
  const input = panel.getByRole("textbox", {
    name: "Your question",
    exact: true,
  });
  await panel
    .getByRole("button", { name: "Interview prep", exact: true })
    .click();
  await expect(input).toBeFocused();
  await expect(input).toHaveValue("How can I prepare for an OJT interview?");
  expect(requested).toHaveLength(0);
  await panel
    .getByRole("button", { name: "Ask for guidance", exact: true })
    .click();
  await expect(
    panel.getByText("Looking through your resources…", { exact: true }),
  ).toBeVisible();
  await expect(
    panel.getByRole("button", { name: "Looking for guidance", exact: true }),
  ).toBeDisabled();
  release!();
  await expect(panel.getByRole("status")).toContainText("Guidance is ready");
  await expect(input).toBeInViewport();
  await expect(input).toHaveValue("");
  await panel
    .getByRole("button", { name: resource.title, exact: true })
    .click();
  await expect(panel.locator(".source-preview h3")).toBeFocused();
  await panel
    .getByRole("button", { name: "Close source", exact: true })
    .click();
  await expect(
    panel.getByRole("button", { name: resource.title, exact: true }),
  ).toBeFocused();
  await expect(input).toBeInViewport();
  await page.screenshot({
    path: "../.impeccable/review/guidance-new-answer-360.png",
    animations: "disabled",
  });
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  fail = true;
  await input.fill("A fictional follow-up question");
  await panel
    .getByRole("button", { name: "Ask for guidance", exact: true })
    .click();
  await expect(panel.getByRole("alert")).toHaveText(
    "Fixture guidance unavailable.",
  );
  await expect(input).toHaveValue("A fictional follow-up question");
  await panel.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(panel.getByRole("status")).toContainText("Guidance is ready");
  expect(requested.slice(-2)).toEqual([
    "A fictional follow-up question",
    "A fictional follow-up question",
  ]);
  await panel
    .getByRole("button", { name: "Clear conversation", exact: true })
    .click();
  await expect(
    panel
      .getByRole("region", { name: "Guidance conversation" })
      .locator("article"),
  ).toHaveCount(0);
  await expect(input).toBeFocused();
});

test("mobile sheet contains keyboard focus and closing restores the page and draft", async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await signIn(page);
  const originalOverflow = await page.evaluate(
    () => document.body.style.overflow,
  );
  await page.locator(".guidance-bubble-trigger").click();
  const panel = page.getByRole("dialog", { name: "OJT guidance", exact: true });
  await expect(panel).toHaveAttribute("aria-modal", "true");
  await panel
    .getByRole("textbox", { name: "Your question", exact: true })
    .fill("A private page-memory draft");
  for (let index = 0; index < 12; index++) {
    await page.keyboard.press(index % 2 ? "Shift+Tab" : "Tab");
    expect(
      await panel.evaluate((element) =>
        element.contains(document.activeElement),
      ),
    ).toBeTruthy();
  }
  await page.keyboard.press("Escape");
  await expect(panel).not.toBeVisible();
  await expect(page.locator(".guidance-bubble-trigger")).toBeFocused();
  expect(await page.evaluate(() => document.body.style.overflow)).toBe(
    originalOverflow,
  );
  await page.locator(".guidance-bubble-trigger").click();
  await expect(
    panel.getByRole("textbox", { name: "Your question", exact: true }),
  ).toHaveValue("A private page-memory draft");
  expect(await page.evaluate(() => JSON.stringify(localStorage))).not.toContain(
    "private page-memory draft",
  );
});
