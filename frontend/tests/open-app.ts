// Existing authenticated-workflow tests use a returning browser. Onboarding has its own tests.
import type { Page } from "@playwright/test";
export async function openApp(page: Page, path = "/") {
  await page.addInitScript(() =>
    localStorage.setItem("thinkmedia.welcome.v1", "seen"),
  );
  await page.goto(path);
}
