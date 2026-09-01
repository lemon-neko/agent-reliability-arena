import { expect, test } from "@playwright/test";

test("交互演示可暂停审批、完成评分并查看完整轨迹", async ({ page }) => {
  const writeRequests: string[] = [];
  page.on("request", (request) => {
    if (request.method() !== "GET") writeRequests.push(`${request.method()} ${request.url()}`);
  });

  await page.goto("/agent-reliability-arena/");
  await expect(page.getByText("交互式公开演示")).toBeVisible();
  await expect(page.getByText("浏览器内确定性模拟 · 无 API KEY")).toBeVisible();

  await page.getByRole("button", { name: /人工审批/ }).click();
  await page.getByRole("button", { name: "开始动态演示" }).click();
  await expect(page.getByText("运行已暂停 · 等待你的决定")).toBeVisible();
  await expect(page.getByText("approval.decided")).toHaveCount(0);
  await page.getByRole("button", { name: "批准并继续" }).click();
  await expect(page.getByText("LangGraph Agent 胜出")).toBeVisible();
  await page.getByRole("button", { name: "查看 LangGraph 完整轨迹" }).click();
  await expect(page.getByText("记录人类决定")).toBeVisible();
  await expect(page.getByText("approval.decided")).toBeVisible();
  expect(writeRequests).toEqual([]);

  await page.getByRole("button", { name: "副本库" }).click();
  await expect(page.locator(".scenario-grid article")).toHaveCount(12);

  await page.getByRole("button", { name: "竞技榜" }).click();
  await expect(page.getByRole("cell", { name: "langgraph-fake", exact: true })).toBeVisible();
});
