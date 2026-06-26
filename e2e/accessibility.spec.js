const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

test("pages have no critical or serious automated accessibility issues", async ({ page }) => {
  for (const path of ["/", "/rekomendasi", "/tentang"]) {
    await page.goto(path);

    const results = await new AxeBuilder({ page }).analyze();
    const blockingViolations = results.violations.filter((violation) => ["critical", "serious"].includes(violation.impact));

    expect(blockingViolations).toEqual([]);
  }
});
