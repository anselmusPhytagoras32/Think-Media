// FR01–02/W01, NFR05/09: reference-led sign-in retains real account behavior.
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";
test("illustrated sign-in is readable on desktop, tablet and phone", async ({
  page,
}) => {
  test.setTimeout(90000);
  await openApp(page);
  await expect(
    page.getByRole("heading", { name: "Login to your account", level: 1 }),
  ).toBeVisible();
  await page
    .locator(".auth-illustration img")
    .evaluate((img) => (img as HTMLImageElement).decode());
  await page.evaluate(() => document.fonts.ready);
  for (const width of [1440, 768, 390, 360]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
    await page.evaluate(() => window.scrollTo(0, 0));
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await expect(page.getByLabel("Email address")).toBeVisible();
    await expect(page.getByLabel(/^Password/)).toBeVisible();
    if (width <= 390) {
      const mobileLayout = await page.evaluate(() => {
        const main = document.querySelector<HTMLElement>(".auth-main")!;
        const footer = document.querySelector<HTMLElement>(".auth-foot")!;
        const artwork =
          document.querySelector<HTMLElement>(".auth-illustration")!;
        const card = main.getBoundingClientRect();
        const footerBox = footer.getBoundingClientRect();
        const artBox = artwork.getBoundingClientRect();
        return {
          mainOverflow: getComputedStyle(main).overflowY,
          pageHeight: document.documentElement.scrollHeight,
          footerAfterCard:
            footerBox.top >= card.top && footerBox.bottom <= card.bottom,
          artworkAtPageTop: artBox.top <= 1 && artBox.width >= innerWidth - 2,
        };
      });
      expect(mobileLayout.mainOverflow).toBe("visible");
      expect(mobileLayout.footerAfterCard).toBeTruthy();
      expect(mobileLayout.artworkAtPageTop).toBeTruthy();
      expect(mobileLayout.pageHeight).toBeLessThanOrEqual(900);
    }
    await page.screenshot({
      path: `../.impeccable/review/signin-scene-${width}.png`,
      fullPage: true,
      animations: "disabled",
    });
    if (width === 1440 || width === 360) {
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      expect(
        results.violations.map((x) => ({
          id: x.id,
          nodes: x.nodes.map((n) => n.target),
        })),
      ).toEqual([]);
    }
  }
});
test("sign-in preserves role registration, password visibility and real student login", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openApp(page);
  await page
    .getByRole("button", { name: "Create an account", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Create your account", level: 1 }),
  ).toBeVisible();
  await page.getByLabel("I’m joining as").selectOption("company");
  await expect(page.getByLabel("Company name")).toBeVisible();
  await expect(
    page.getByRole("region", { name: "How demo data is used" }),
  ).toContainText("Use fictional account details and sample PDFs only.");
  await expect(page.locator("details.privacy-disclosure")).toHaveCount(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollHeight > window.innerHeight,
    ),
  ).toBeTruthy();
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await expect(
    page.getByRole("button", { name: "Getting started" }),
  ).toBeVisible();
  await page.getByLabel("I’m joining as").selectOption("student");
  await expect(page.getByLabel("Company name")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Sign in", exact: true })
    .first()
    .click();
  await page.getByLabel("Email address").fill("student@example.test");
  await page.getByLabel(/^Password/).fill("ThinkMedia-Student-2026!");
  await page
    .getByRole("button", { name: "Show password", exact: true })
    .click();
  await expect(page.getByLabel(/^Password/)).toHaveAttribute("type", "text");
  await page
    .getByRole("button", { name: "Hide password", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Sign in", exact: true })
    .last()
    .click();
  await expect(
    page.getByRole("heading", { name: "Find your next opportunity." }),
  ).toBeVisible();
  expect((await page.request.get("/api/v1/auth/me")).status()).toBe(200);
  expect((await page.request.get("/api/v1/admin/companies")).status()).toBe(
    403,
  );
});
