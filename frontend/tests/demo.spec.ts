import { expect, test } from "@playwright/test";

test("冻结演示开放全部只读页面并禁用写操作", async ({ page }) => {
  await page.goto("/agent-reliability-arena/");
  await expect(page.getByText("冻结公开演示")).toBeVisible();
  await expect(page.getByRole("button", { name: "公开演示只读" })).toBeDisabled();

  await page.getByRole("button", { name: "副本库" }).click();
  await expect(page.locator(".scenario-grid article")).toHaveCount(12);

  await page.getByRole("button", { name: "竞技榜" }).click();
  await expect(page.getByText("langgraph-fake")).toBeVisible();

  await page.getByRole("button", { name: "运行轨迹" }).click();
  await expect(page.getByText("可回放执行轨迹")).toBeVisible();
  await expect(page.getByText("tool.request")).toBeVisible();
});
