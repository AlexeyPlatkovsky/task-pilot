import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./browser-contract",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "node e2e/support/api-stub.mjs",
      url: "http://127.0.0.1:7154/api/health",
      env: {
        TASKPILOT_E2E_API_PORT: "7154",
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1",
      url: "http://127.0.0.1:3000",
      env: {
        TASKPILOT_API_TARGET: "http://127.0.0.1:7154",
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
