// FR01–11 / NFR03/05/09: responsive shell, truthful preferences and keyboard navigation.
import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";
async function signIn(page: Page) {
  const { csrf_token } = await (
    await page.request.get("/api/v1/auth/csrf")
  ).json();
  const result = await page.request.post("/api/v1/auth/login", {
    headers: { "X-CSRF-Token": csrf_token },
    data: {
      email: "student@example.test",
      password: "ThinkMedia-Student-2026!",
    },
  });
  expect(result.status()).toBe(200);
}
test("sidebar collapses with keyboard labels, remembers choice and preserves navigation", async ({
  page,
}) => {
  await signIn(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openApp(page);
  const sidebar = page.locator("#main-sidebar");
  await page
    .getByRole("button", { name: "Collapse sidebar", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("button", { name: "Expand sidebar", exact: true }),
  ).toHaveAttribute("aria-expanded", "false");
  expect((await sidebar.boundingBox())!.width).toBeLessThan(120);
  const learning = sidebar.getByRole("link", { name: "Learning", exact: true });
  await learning.focus();
  await expect(page.getByRole("tooltip")).toHaveText("Learning");
  await page.screenshot({
    path: "../.impeccable/review/sidebar-collapsed-1440.png",
    // Keep the viewport stable: full-page capture scrolls and dismisses tooltips.
    fullPage: false,
    animations: "disabled",
  });
  const controlRect = (await learning.boundingBox())!;
  const tooltipRect = (await page.getByRole("tooltip").boundingBox())!;
  await page.mouse.move(
    controlRect.x + controlRect.width / 2,
    controlRect.y + controlRect.height / 2,
  );
  // Travel through the padding; locator.hover() jumps over this gap.
  await page.mouse.move(
    tooltipRect.x + tooltipRect.width / 2,
    tooltipRect.y + tooltipRect.height / 2,
    { steps: 12 },
  );
  await expect(page.getByRole("tooltip")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("tooltip")).toHaveCount(0);
  await expect(learning).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#\/learning$/);
  await expect(
    page.getByRole("heading", { name: "Learning resources", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Expand sidebar", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Expand sidebar", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Collapse sidebar", exact: true }),
  ).toHaveAttribute("aria-expanded", "true");
  await page.reload();
  expect((await sidebar.boundingBox())!.width).toBeGreaterThan(180);
});
test("shell adapts to desktop, tablet and drawer without overlap or trapped scroll", async ({
  page,
}) => {
  test.setTimeout(90000);
  await signIn(page);
  await page.setViewportSize({ width: 1920, height: 1000 });
  await openApp(page);
  await expect(page.locator(".opportunity-card").first()).toBeVisible();
  for (const width of [1920, 1440, 1024, 768, 360]) {
    await page.setViewportSize({ width, height: width === 360 ? 800 : 1000 });
    await page.evaluate(() => window.scrollTo(0, 0));
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    if (width > 720) {
      const sidebar = await page.locator("#main-sidebar").boundingBox();
      const content = await page.locator(".workspace").boundingBox();
      expect(content!.x).toBeGreaterThanOrEqual(
        sidebar!.x + sidebar!.width - 1,
      );
    }
    if (width >= 1440) {
      const intro = await page.locator(".consumer-intro").boundingBox();
      const pocket = await page.locator(".application-pocket").boundingBox();
      expect(pocket!.x).toBeGreaterThan(intro!.x + intro!.width);
      expect(Math.abs(pocket!.y - intro!.y)).toBeLessThan(8);
    }
    await page.screenshot({
      path: `../.impeccable/review/layout-${width}.png`,
      fullPage: true,
      animations: "disabled",
    });
  }
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Navigation drawer" }),
  ).toBeVisible();
  expect(await page.evaluate(() => document.body.style.overflow)).toBe(
    "hidden",
  );
  await expect(
    page
      .locator("#main-sidebar")
      .getByRole("link", { name: "Learning", exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 1024, height: 800 });
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe(
    "hidden",
  );
  await expect(
    page.getByRole("button", { name: "Expand sidebar", exact: true }),
  ).toBeFocused();
  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(
    axe.violations.map((x) => ({
      id: x.id,
      nodes: x.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
});
test("blocked sidebar storage does not prevent collapsing or reaching account controls", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const get = Storage.prototype.getItem,
      set = Storage.prototype.setItem;
    Storage.prototype.getItem = function (key) {
      if (key === "thinkmedia.sidebar.v1")
        throw new DOMException("Blocked", "SecurityError");
      return get.call(this, key);
    };
    Storage.prototype.setItem = function (key, value) {
      if (key === "thinkmedia.sidebar.v1")
        throw new DOMException("Blocked", "SecurityError");
      return set.call(this, key, value);
    };
  });
  await signIn(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openApp(page);
  await page
    .getByRole("button", { name: "Collapse sidebar", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Expand sidebar", exact: true }),
  ).toBeVisible();
  await page
    .locator("#main-sidebar")
    .getByRole("link", { name: /My profile/ })
    .click();
  await expect(page).toHaveURL(/#\/profile$/);
  await page
    .getByRole("button", { name: "Expand sidebar", exact: true })
    .click();
  await expect(
    page
      .locator("#main-sidebar")
      .getByRole("button", { name: "Sign out", exact: true }),
  ).toBeVisible();
});
