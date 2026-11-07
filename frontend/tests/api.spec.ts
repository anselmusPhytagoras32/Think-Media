import { test, expect } from "@playwright/test";
// FR01/02/11: proxy contract checks independent of browser installation.
test("real API denies unauthenticated private profile and admin reads", async ({
  request,
}) => {
  for (const path of [
    "/auth/me",
    "/profiles/me",
    "/admin/companies",
    "/admin/audit-events",
  ]) {
    const result = await request.get(`/api/v1${path}`);
    expect(result.status()).toBe(401);
    const body = await result.json();
    expect(body.error.code).toBeTruthy();
    expect(body.error.request_id).toBeTruthy();
  }
});
test("real API CSRF bootstrap and admin self-registration denial", async ({
  request,
}) => {
  const response = await request.get("/api/v1/auth/csrf");
  expect(response.ok()).toBeTruthy();
  const { csrf_token } = await response.json();
  const denied = await request.post("/api/v1/auth/register", {
    headers: { "X-CSRF-Token": csrf_token },
    data: {
      email: `elevation-${Date.now()}@example.test`,
      display_name: "Forbidden Admin",
      role: "administrator",
      password: "Local-browser-test-42",
    },
  });
  expect(denied.status()).toBe(422);
});
