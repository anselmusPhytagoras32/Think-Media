// W01/W07/W08, FR10/11, NFR03/05/09: focused presentation acceptance regressions.
import { test, expect, type APIRequestContext } from "@playwright/test";
import { openApp } from "./open-app";

const password = "Local-browser-test-42";
async function mutate(request: APIRequestContext, path: string, data: unknown) {
  const bootstrap = await request.get("/api/v1/auth/csrf");
  const { csrf_token } = await bootstrap.json();
  return request.post("/api/v1" + path, {
    headers: { "X-CSRF-Token": csrf_token },
    data,
  });
}
async function student(request: APIRequestContext) {
  const email = `requirements-${Date.now()}-${Math.random().toString(36).slice(2)}@example.test`;
  expect(
    (
      await mutate(request, "/auth/register", {
        email,
        password,
        display_name: "Synthetic Requirements Learner",
        role: "student",
      })
    ).ok(),
  ).toBeTruthy();
  expect(
    (await mutate(request, "/auth/login", { email, password })).ok(),
  ).toBeTruthy();
}

test("guidance retains bounded exchanges, retries the failed question and clears private page memory", async ({
  page,
  context,
}) => {
  await student(context.request);
  let failNext = true;
  const requests: string[] = [];
  // Deterministic provider-boundary fixtures exercise failure and recovery; these are not AI evaluation results.
  await page.route("**/api/v1/assistant", async (route) => {
    const { question } = route.request().postDataJSON();
    requests.push(question);
    if (failNext) {
      failNext = false;
      await route.fulfill({
        status: 503,
        json: { error: { message: "Synthetic provider unavailable." } },
      });
    } else
      await route.fulfill({
        json: {
          answer: `Approved fixture response to ${question}`,
          sources: [],
          uncertainty: "Fixture has no matching source.",
          mode: "retrieval",
        },
      });
  });
  await page.setViewportSize({ width: 360, height: 800 });
  await openApp(page, "/#/assistant");
  await page
    .getByRole("textbox", { name: "Your question", exact: true })
    .fill("First fictional question");
  await page
    .getByRole("button", { name: "Ask for guidance", exact: true })
    .click();
  await expect(page.getByRole("alert")).toHaveText(
    "Synthetic provider unavailable.",
  );
  await page
    .getByRole("textbox", { name: "Your question", exact: true })
    .fill("A different draft");
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Guidance is ready");
  expect(requests.slice(0, 2)).toEqual([
    "First fictional question",
    "First fictional question",
  ]);
  const conversation = page.getByRole("region", {
    name: "Guidance conversation",
  });
  await expect(conversation.locator("article")).toHaveCount(1);
  for (let i = 2; i <= 11; i++) {
    await page
      .getByRole("textbox", { name: "Your question", exact: true })
      .fill(`Fictional question ${i}`);
    await page
      .getByRole("button", { name: "Ask for guidance", exact: true })
      .click();
    await expect(conversation).toContainText(
      `Approved fixture response to Fictional question ${i}`,
    );
  }
  await expect(conversation.locator("article")).toHaveCount(10);
  await expect(conversation).not.toContainText("First fictional question");
  expect(await page.evaluate(() => JSON.stringify(localStorage))).not.toContain(
    "Fictional question",
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../.impeccable/review/requirements-guidance-360.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Clear conversation", exact: true })
    .click();
  await expect(conversation.locator("article")).toHaveCount(0);
  await expect(page.getByRole("status")).toHaveText("Conversation cleared.");
});

test("publication requires confirmation, preserves edits on cancellation and records real publication", async ({
  page,
  context,
}) => {
  expect(
    (
      await mutate(context.request, "/auth/login", {
        email: "admin@example.test",
        password,
      })
    ).ok(),
  ).toBeTruthy();
  let writes = 0;
  await page.route("**/api/v1/admin/content", async (route) => {
    if (route.request().method() === "POST") writes++;
    await route.continue();
  });
  await openApp(page, "/#/content");
  await page.getByRole("button", { name: "New resource", exact: true }).click();
  const title = `Synthetic publication confirmation ${Date.now()}`;
  await page.getByLabel("Title (required)", { exact: true }).fill(title);
  await page
    .getByLabel("Summary (required)")
    .fill("Synthetic local acceptance fixture.");
  await page
    .getByLabel("Resource text (required)")
    .fill(
      "Fictional presentation preparation advice for a local automated acceptance test.",
    );
  await page.getByLabel("Publication status").selectOption("published");
  await page
    .getByRole("button", { name: "Save resource", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review publication" }),
  ).toBeFocused();
  await expect(
    page.getByRole("button", { name: "Save resource", exact: true }),
  ).toHaveCount(0);
  expect(writes).toBe(0);
  await page.getByRole("button", { name: "Keep editing", exact: true }).click();
  await expect(
    page.getByLabel("Title (required)", { exact: true }),
  ).toHaveValue(title);
  await page
    .getByRole("button", { name: "Save resource", exact: true })
    .click();
  await page.screenshot({
    path: "../.impeccable/review/requirements-publication.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Confirm publication", exact: true })
    .click();
  await expect(page.locator(".notice.success")).toContainText("saved");
  expect(writes).toBe(1);
  const resources = await context.request.get(
    `/api/v1/admin/content?q=${encodeURIComponent(title)}`,
  );
  expect(
    (await resources.json()).items.find(
      (item: { title: string }) => item.title === title,
    )?.status,
  ).toBe("published");
});

test("custom profile fields expose server errors without a repeated disclaimer footer", async ({
  page,
  context,
}) => {
  await student(context.request);
  await openApp(page, "/#/profile");
  await expect(page.locator(".workspace-demo-note")).toHaveCount(0);
  await expect(page.locator("details.privacy-disclosure")).toHaveCount(0);
  await page.route("**/api/v1/profiles/me", async (route) => {
    if (route.request().method() === "PATCH")
      await route.fulfill({
        status: 422,
        json: {
          error: {
            message: "Check your profile.",
            fields: { background: ["Synthetic background error."] },
          },
        },
      });
    else await route.continue();
  });
  await page
    .getByLabel("Background", { exact: true })
    .fill("Fictional background retained after failure.");
  await page.getByRole("button", { name: "Save profile", exact: true }).click();
  await expect(page.getByLabel("Background", { exact: true })).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  await expect(page.getByLabel("Background", { exact: true })).toHaveAttribute(
    "aria-describedby",
    "background-hint",
  );
  await expect(page.locator("#background-hint")).toHaveText(
    "Synthetic background error.",
  );
  await expect(page.getByLabel("Background", { exact: true })).toHaveValue(
    "Fictional background retained after failure.",
  );
});
