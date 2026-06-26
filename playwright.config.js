const { defineConfig, devices } = require("@playwright/test");

const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5000";

module.exports = defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: ".\\.venv\\Scripts\\python.exe -m flask --app app run --host 127.0.0.1 --port 5000",
    url: baseURL,
    reuseExistingServer: true,
    timeout: 30000,
    env: {
      FLASK_DEBUG: "0",
    },
  },
  projects: [
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1366, height: 768 } },
    },
    {
      name: "tablet-chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 768, height: 1024 } },
    },
    {
      name: "mobile-chromium",
      use: { ...devices["Pixel 5"], viewport: { width: 390, height: 844 } },
    },
    {
      name: "small-mobile-chromium",
      use: { ...devices["Pixel 5"], viewport: { width: 320, height: 568 } },
    },
  ],
});
