import { defineConfig, devices } from "@playwright/test";

// Runs against the compose demo stack; Playwright does not start the app.
// Use localhost, never 127.0.0.1: the session cookie is SameSite=Lax, so a
// page loaded from the alternate loopback hostname would not send it.
export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.RINAVI_WEB_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
  },
});
