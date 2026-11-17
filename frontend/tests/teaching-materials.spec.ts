// FR03/11: instructor drafts, administrator moderation and student discovery.
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { openApp } from "./open-app";

const password = "Local-browser-test-42";

async function auth(request: APIRequestContext, action: "login" | "register", data: object) {
  const { csrf_token } = await (await request.get("/api/v1/auth/csrf")).json();
  const response = await request.post("/api/v1/auth/" + action, {
    headers: { "X-CSRF-Token": csrf_token },
    data,
  });
  expect(response.ok(), await response.text()).toBeTruthy();
}

async function openSubmission(page: Page, title: string) {
  await page.getByRole("button", { name: title, exact: true }).click();
  await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
}

async function publish(page: Page) {
  await page.getByRole("button", { name: "Approve and publish" }).click();
  await page.getByRole("button", { name: "Confirm publication" }).click();
  await expect(page.getByText("Submission approved and published.", { exact: true })).toBeVisible();
}

test("an instructor drafts materials, an administrator reviews them, and a student completes the lesson", async ({ browser }, info) => {
  test.setTimeout(120000);
  const suffix = Date.now();
  const category = "Project walkthrough " + suffix;
  const title = "Explain a prototype walkthrough " + suffix;
  const instructor = await browser.newContext({ viewport: { width: 360, height: 800 } });
  const admin = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const student = await browser.newContext();
  try {
    const email = "teaching-" + suffix + "@example.test";
    await auth(instructor.request, "register", { email, password, role: "instructor", display_name: "Demo Instructor" });
    await auth(instructor.request, "login", { email, password });
    await auth(admin.request, "login", { email: "admin@example.test", password });
    await auth(student.request, "login", { email: "student@example.test", password: "ThinkMedia-Student-2026!" });

    const author = await instructor.newPage();
    const review = await admin.newPage();
    const learner = await student.newPage();
    await openApp(author, "/#/authoring");
    await author.getByRole("button", { name: "New skill category" }).click();
    await author.getByLabel("Skill name").fill(category);
    await author.getByLabel("Description").fill("Describe a prototype to a reviewer.");
    await author.getByRole("button", { name: "Save draft" }).click();
    await expect(author.getByRole("heading", { name: category })).toBeVisible();
    await author.getByRole("button", { name: "Submit for review" }).click();
    await expect(author.getByText("Submitted for administrator review.")).toBeVisible();

    await openApp(review, "/#/content");
    await review.getByRole("link", { name: "Review instructor submissions" }).click();
    await openSubmission(review, category);
    await publish(review);

    await author.getByRole("button", { name: "Back to my materials" }).click();
    await author.getByRole("button", { name: "New lesson" }).click();
    await author.getByLabel("Lesson title").fill(title);
    await author.getByLabel("Summary").fill("Describe the purpose, input, action, and output.");
    await author.getByLabel("Lesson text").fill("Walk through a prototype with sample input.");
    await author.getByLabel("Find a skill category").fill(category);
    await author.getByRole("button", { name: "Add " + category }).click();
    await author.getByLabel("PDF attachment").setInputFiles("../presentation/fictional-resume.pdf");
    await author.getByRole("button", { name: "Add a reference link" }).click();
    await author.getByLabel("Link 1 label").fill("Example practice site");
    await author.getByLabel("Link 1 URL").fill("https://example.org/practice");
    await author.getByRole("button", { name: "Add a quiz question" }).click();
    await author.getByLabel("Question text").fill("What should the walkthrough start with?");
    await author.getByRole("textbox", { name: "Option 1", exact: true }).fill("The prototype's purpose");
    await author.getByRole("textbox", { name: "Option 2", exact: true }).fill("The file name");
    await author.getByLabel("Feedback after submission").fill("State the purpose before walking through the interface.");
    expect(await author.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    await author.screenshot({ path: info.outputPath("instructor-editor-360.png"), fullPage: true });
    await author.getByRole("button", { name: "Save draft" }).click();
    await expect(author.getByRole("heading", { name: title })).toBeVisible();
    await author.reload();
    await expect(author.getByRole("link", { name: "Download fictional-resume.pdf" })).toBeVisible();
    await author.getByRole("button", { name: "Submit for review" }).click();
    await expect(author.getByText("Submitted for administrator review.")).toBeVisible();
    expect((await (await student.request.get("/api/v1/content?q=" + encodeURIComponent(title))).json()).total).toBe(0);

    await review.getByRole("button", { name: "Back to review queue" }).click();
    await openSubmission(review, title);
    await expect(review.getByText("Quiz preview")).toBeVisible();
    await review.screenshot({ path: info.outputPath("administrator-learning-review.png"), fullPage: true });
    await review.getByLabel("Review feedback").fill("Include an example output.");
    await review.getByRole("button", { name: "Request changes" }).click();
    await expect(review.getByText("Changes requested.", { exact: true })).toBeVisible();
    await author.reload();
    await expect(author.getByText("Include an example output.")).toBeVisible();
    await author.getByRole("button", { name: "Edit draft" }).click();
    await author.getByLabel("Lesson text").fill("Walk through a prototype and show a sample output of three completed items.");
    await author.getByRole("button", { name: "Save draft" }).click();
    await expect(author.getByText("Draft saved.", { exact: true })).toBeVisible();
    await author.getByRole("button", { name: "Submit for review" }).click();
    await expect(author.getByText("Submitted for administrator review.")).toBeVisible();
    await review.reload();
    await publish(review);

    await openApp(learner, "/#/learning");
    await learner.getByLabel("Topic", { exact: true }).fill(category);
    await learner.getByRole("button", { name: "Search", exact: true }).click();
    await openSubmission(learner, title);
    await expect(learner.getByRole("link", { name: "Example practice site" })).toHaveAttribute("href", "https://example.org/practice");
    const download = learner.waitForEvent("download");
    await learner.getByRole("link", { name: "Download fictional-resume.pdf" }).click();
    expect((await download).suggestedFilename()).toBe("fictional-resume.pdf");
    await learner.getByRole("button", { name: "Open quiz" }).click();
    await learner.getByRole("radio", { name: "The prototype's purpose" }).check();
    await learner.getByRole("button", { name: "Submit answers" }).click();
    await expect(learner.getByText("You answered 1 of 1 correctly.")).toBeVisible();
    await expect(learner.getByText("State the purpose before walking through the interface.")).toBeVisible();
  } finally {
    await Promise.all([instructor.close(), admin.close(), student.close()]);
  }
});
