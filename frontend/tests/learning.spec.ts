import { openApp } from "./open-app";
// FR03/10/11: real content approval, quiz scoring, moderation and graceful provider failure.
import { test, expect, APIRequestContext } from "@playwright/test";
const password = "Local-browser-test-42";
async function mutate(
  request: APIRequestContext,
  path: string,
  data: unknown,
  method = "POST",
) {
  const bootstrap = await request.get("/api/v1/auth/csrf");
  const { csrf_token } = await bootstrap.json();
  return request.fetch("/api/v1" + path, {
    method,
    headers: { "X-CSRF-Token": csrf_token },
    data,
  });
}
test("published resources, save/react, quiz and report review work end to end", async ({
  browser,
}) => {
  test.setTimeout(90000);
  const suffix = Date.now();
  const title = `Interview preparation ${suffix}`;
  const adminContext = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    reducedMotion: "reduce",
  });
  await mutate(adminContext.request, "/auth/login", {
    email: "admin@example.test",
    password,
  });
  const admin = await adminContext.newPage();
  await openApp(admin, "/");
  await admin
    .getByRole("link", { name: "Learning content", exact: true })
    .click();
  await admin.getByRole("button", { name: "New resource" }).click();
  await admin.getByLabel("Title (required)", { exact: true }).fill(title);
  await admin
    .getByLabel("Summary (required)")
    .fill("Practical interview preparation using approved resources.");
  await admin
    .getByLabel("Resource text (required)")
    .fill(
      "Prepare examples of your work, read the company requirements, and practice explaining your skills. This is synthetic local test content.",
    );
  await admin
    .getByLabel("Topics (separate with commas)")
    .fill("interviews, preparation");
  await admin.getByLabel("Publication status").selectOption("published");
  await admin.getByLabel("Include a short quiz").check();
  await admin
    .getByLabel("Question (required)", { exact: true })
    .fill("What should you prepare before an interview?");
  for (const [i, value] of [
    "Examples of your work",
    "Nothing",
    "Someone else’s resume",
    "Private application data",
  ].entries())
    await admin.locator(`#option${i}`).fill(value);
  await admin.getByLabel("Correct answer option").selectOption("0");
  await admin
    .getByRole("button", { name: "Save resource", exact: true })
    .click();
  await admin
    .getByRole("button", { name: "Confirm publication", exact: true })
    .click();
  await expect(admin.locator(".notice.success")).toContainText("saved");
  const studentContext = await browser.newContext({
    viewport: { width: 360, height: 800 },
    reducedMotion: "reduce",
  });
  await mutate(studentContext.request, "/auth/register", {
    email: `learner-${suffix}@example.test`,
    display_name: "Resource Learner",
    role: "student",
    password,
  });
  await mutate(studentContext.request, "/auth/login", {
    email: `learner-${suffix}@example.test`,
    password,
  });
  const student = await studentContext.newPage();
  await openApp(student, "/");
  await student.getByRole("button", { name: "Open navigation" }).click();
  await student
    .locator(".sidebar")
    .getByRole("link", { name: "Learning", exact: true })
    .click();
  await student.getByLabel("Search resources").fill(title);
  await student.getByRole("button", { name: "Search", exact: true }).click();
  const feedEntry = student.locator(".resource-row").filter({ hasText: title });
  await feedEntry
    .getByRole("button", { name: `Save ${title}`, exact: true })
    .click();
  await expect(
    feedEntry.getByRole("button", {
      name: `Saved; remove saved resource ${title}`,
      exact: true,
    }),
  ).toHaveAttribute("aria-pressed", "true");
  await feedEntry
    .getByRole("button", {
      name: `Saved; remove saved resource ${title}`,
      exact: true,
    })
    .click();
  await feedEntry
    .getByRole("button", { name: `React to ${title}`, exact: true })
    .click();
  await expect(
    feedEntry.getByRole("button", {
      name: `Reacted; remove reaction to ${title}`,
      exact: true,
    }),
  ).toHaveAttribute("aria-pressed", "true");
  await feedEntry
    .getByRole("button", {
      name: `Reacted; remove reaction to ${title}`,
      exact: true,
    })
    .click();
  await student
    .locator(".resource-row")
    .getByRole("button", { name: title, exact: true })
    .click();
  await student
    .getByRole("button", { name: "Save resource", exact: true })
    .click();
  await expect(
    student.getByRole("button", { name: "Saved", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await student.getByRole("button", { name: "React", exact: true }).click();
  await expect(
    student.getByRole("button", { name: "Reacted", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await student.getByRole("button", { name: "Open quiz" }).click();
  await student
    .getByRole("radio", { name: "Examples of your work", exact: true })
    .check();
  await student.getByRole("button", { name: "Submit answers" }).click();
  await expect(
    student.getByText("You answered 1 of 1 correctly."),
  ).toBeVisible();
  await student.getByRole("button", { name: "Report resource" }).click();
  const reason = `Review test content ${suffix}`;
  await student.getByLabel("What needs attention? (required)").fill(reason);
  await student.getByRole("button", { name: "Submit report" }).click();
  await expect(student.locator(".notice.success")).toContainText(
    "Report submitted",
  );
  expect(
    await student.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await student.evaluate(() => window.scrollTo(0, 0));
  await student.screenshot({
    path: "../.impeccable/review/mobile-learning.png",
    fullPage: true,
    animations: "disabled",
  });
  await admin
    .getByRole("link", { name: "Content reports", exact: true })
    .click();
  const row = admin.locator("article").filter({ hasText: reason });
  await row.getByRole("button", { name: "Review report" }).click();
  await admin
    .getByLabel("Resolution (required)")
    .fill("Synthetic report reviewed; no production content involved.");
  await admin.getByRole("button", { name: "Confirm resolution" }).click();
  await expect(admin.locator(".notice.success")).toContainText(
    "resolution recorded",
  );
  await student.locator(".guidance-bubble-trigger").click();
  await student
    .getByLabel("Your question")
    .fill("How can I prepare for an OJT interview?");
  const guidanceReply = student.waitForResponse(
    (r) =>
      r.url().endsWith("/api/v1/assistant") && r.request().method() === "POST",
  );
  await student.getByRole("button", { name: "Ask for guidance" }).click();
  const guidanceResponse = await guidanceReply;
  if (guidanceResponse.status() === 503) {
    await expect(student.getByRole("alert")).toBeVisible();
    await expect(
      student.getByText(
        "Your applications and opportunities remain available.",
      ),
    ).toBeVisible();
  } else {
    expect(guidanceResponse.status()).toBe(200);
    expect((await guidanceResponse.json()).mode).toBe("retrieval");
    await expect(
      student.getByText("Approved resource lookup", { exact: true }),
    ).toBeVisible();
    await student.getByRole("button", { name: title, exact: true }).click();
    await expect(student.locator(".source-preview")).toContainText(
      "synthetic local test content",
    );
    await student.getByText("Rate this guidance", { exact: true }).click();
    await student.getByLabel("Helpfulness rating (optional)").selectOption("5");
    await student
      .getByRole("button", { name: "Share satisfaction rating", exact: true })
      .click();
    await expect(
      student.getByText("Thank you. Your satisfaction rating was saved."),
    ).toBeVisible();
  }
  expect((await studentContext.request.get("/api/v1/listings")).status()).toBe(
    200,
  );
  await student.evaluate(() => window.scrollTo(0, 0));
  await student.screenshot({
    path: "../.impeccable/review/mobile-assistant.png",
    fullPage: true,
    animations: "disabled",
  });
  await studentContext.close();
  await adminContext.close();
});
