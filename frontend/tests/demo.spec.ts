import { expect, test } from "@playwright/test";

test("frozen demo exposes all read surfaces and disables writes", async ({ page }) => {
  await page.goto("/agent-reliability-arena/");
  await expect(page.getByText("Frozen public demo")).toBeVisible();
  await expect(page.getByRole("button", { name: "Read-only demo" })).toBeDisabled();

  await page.getByRole("button", { name: "Scenario library" }).click();
  await expect(page.locator(".scenario-grid article")).toHaveCount(12);

  await page.getByRole("button", { name: "Leaderboard" }).click();
  await expect(page.getByText("langgraph-fake")).toBeVisible();

  await page.getByRole("button", { name: "Live trace" }).click();
  await expect(page.getByText("Replayable trace")).toBeVisible();
  await expect(page.getByText("tool.request")).toBeVisible();
});
