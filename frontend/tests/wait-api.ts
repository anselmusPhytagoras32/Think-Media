// Infrastructure readiness: do not test the reconnect screen while FastAPI imports ML modules.
import { request } from "@playwright/test";
export default async function waitForApi() {
  const client = await request.newContext();
  const deadline = Date.now() + 90000;
  try {
    while (Date.now() < deadline) {
      try {
        const response = await client.get(
          `${process.env.PLAYWRIGHT_API_TARGET || "http://127.0.0.1:8000"}/health`,
          {
            timeout: 1000,
          },
        );
        if (response.ok()) return;
      } catch {}
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
    throw new Error(
      "FastAPI is not ready on the configured local API. Start the migrated disposable-development API before browser tests.",
    );
  } finally {
    await client.dispose();
  }
}
