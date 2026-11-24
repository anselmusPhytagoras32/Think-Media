// FR02/10/NFR02/05/09: preview, confirmation and safe internal result navigation.
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { openApp } from "./open-app";

test("assistant previews a profile change and saves only after explicit confirmation", async ({
  page,
}) => {
  const { csrf_token } = await (
    await page.request.get("/api/v1/auth/csrf")
  ).json();
  const login = await page.request.post("/api/v1/auth/login", {
    headers: { "X-CSRF-Token": csrf_token },
    data: {
      email: "student@example.test",
      password: "ThinkMedia-Student-2026!",
    },
  });
  expect(login.ok()).toBeTruthy();
  await page.route("**/api/v1/assistant/capabilities", (route) =>
    route.fulfill({
      json: {
        actions_available: true,
        prompts: [
          {
            label: "Find lessons",
            question: "Find resume preparation lessons",
          },
        ],
      },
    }),
  );
  let confirmations = 0;
  await page.route("**/api/v1/assistant", async (route) => {
    expect(route.request().postDataJSON().workspace).toBe(true);
    await route.fulfill({
      json: {
        answer: "Review the proposed change. Nothing has been saved yet.",
        sources: [],
        uncertainty: false,
        mode: "external",
        proposal: {
          id: "00000000-0000-4000-8000-000000000001",
          label: "Update my profile",
          changes: { Skills: ["Python", "React"] },
          expires_at: "2026-11-24T23:00:00+08:00",
        },
      },
    });
  });
  await page.route("**/api/v1/assistant/actions/*/confirm", async (route) => {
    confirmations++;
    await route.fulfill({
      json: { answer: "Your profile was updated.", href: "#/profile" },
    });
  });
  await openApp(page, "/#/assistant");
  await expect(
    page.getByRole("heading", { name: "ThinkMedia assistant", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Your question", exact: true })
    .fill("Set my skills to Python and React");
  await page
    .getByRole("button", { name: "Ask for guidance", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Update my profile", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Python, React", { exact: true })).toBeVisible();
  expect(confirmations).toBe(0);
  expect(
    (await new AxeBuilder({ page }).analyze()).violations.filter(
      (issue) => issue.impact === "critical" || issue.impact === "serious",
    ),
  ).toEqual([]);
  await page.screenshot({
    path: "../.local/assistant-proposal-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Confirm change", exact: true })
    .click();
  await expect(
    page
      .getByRole("region", { name: "Proposed change" })
      .getByText("Your profile was updated.", { exact: true }),
  ).toBeVisible();
  expect(confirmations).toBe(1);
  await expect(
    page.getByRole("button", { name: "Confirm change", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Open updated page", exact: true }),
  ).toHaveAttribute("href", "#/profile");
});

test("assistant shows public results, supports cancellation, and contains long preview text at 360px", async ({
  page,
}) => {
  const { csrf_token } = await (
    await page.request.get("/api/v1/auth/csrf")
  ).json();
  expect(
    (
      await page.request.post("/api/v1/auth/login", {
        headers: { "X-CSRF-Token": csrf_token },
        data: {
          email: "student@example.test",
          password: "ThinkMedia-Student-2026!",
        },
      })
    ).ok(),
  ).toBeTruthy();
  await page.setViewportSize({ width: 360, height: 800 });
  await page.route("**/api/v1/assistant", (route) =>
    route.fulfill({
      json: {
        answer: "Review the proposed change.",
        sources: [],
        uncertainty: false,
        mode: "external",
        proposal: {
          id: "00000000-0000-4000-8000-000000000002",
          label: "Create lesson draft",
          changes: {
            Title: "Explain an OJT project",
            Body: "A long fictional description. ".repeat(60),
          },
          expires_at: "2026-11-24T23:00:00+08:00",
        },
      },
    }),
  );
  await page.route("**/api/v1/assistant/actions/*/cancel", (route) =>
    route.fulfill({ json: { answer: "Proposed change cancelled." } }),
  );
  await openApp(page, "/#/assistant");
  await page
    .getByRole("textbox", { name: "Your question", exact: true })
    .fill("Prepare a draft");
  await page
    .getByRole("button", { name: "Ask for guidance", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Cancel change", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.getByText("Read proposed body", { exact: true }).click();
  expect(
    (await new AxeBuilder({ page }).analyze()).violations.filter(
      (issue) => issue.impact === "critical" || issue.impact === "serious",
    ),
  ).toEqual([]);
  await page.screenshot({
    path: "../.local/assistant-proposal-mobile.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Cancel change", exact: true })
    .click();
  await expect(
    page
      .getByRole("region", { name: "Proposed change" })
      .getByText("Proposed change cancelled.", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Confirm change", exact: true }),
  ).toHaveCount(0);
  await page.unroute("**/api/v1/assistant");
  await page.route("**/api/v1/assistant", (route) =>
    route.fulfill({
      json: {
        answer: "Published resources matching your request.",
        sources: [],
        uncertainty: false,
        mode: "external",
        results: [
          {
            id: "00000000-0000-4000-8000-000000000003",
            title: "Fictional OJT guide",
            summary: "A public practice guide.",
            href: "#/learning/00000000-0000-4000-8000-000000000003",
            kind: "lesson",
          },
          {
            id: "untrusted",
            title: "Unsafe model link",
            summary: "Must not become a link.",
            href: "https://evil.example",
            kind: "lesson",
          },
        ],
      },
    }),
  );
  await page
    .getByRole("textbox", { name: "Your question", exact: true })
    .fill("Find an OJT guide");
  await page
    .getByRole("button", { name: "Ask for guidance", exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: "Fictional OJT guide", exact: true }),
  ).toHaveAttribute("href", "#/learning/00000000-0000-4000-8000-000000000003");
  await expect(page.locator('a[href="https://evil.example"]')).toHaveCount(0);
});
