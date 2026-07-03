import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e/functional",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 0 : 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "node e2e/support/start-taskpilot-api.mjs",
      url: "http://127.0.0.1:7153/api/health",
      env: {
        TASKPILOT_E2E_API_PORT: "7153",
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1",
      url: "http://127.0.0.1:3000",
      env: {
        TASKPILOT_API_TARGET: "http://127.0.0.1:7153",
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
