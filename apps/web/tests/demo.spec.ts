import { expect, test } from "@playwright/test";

test("风险体检 Demo 动态执行 72 项测试并生成可查看报告", async ({ page }) => {
  const writeRequests: string[] = [];
  page.on("request", (request) => {
    if (request.method() !== "GET") writeRequests.push(`${request.method()} ${request.url()}`);
  });

  await page.goto("/agent-reliability-arena/");
  await expect(page.getByText("LIVE DETERMINISTIC DEMO")).toBeVisible();
  await expect(page.getByText("公开页面只播放浏览器内确定性剧本")).toBeVisible();
  await expect(page.getByRole("option", { name: /Cinder Ops Agent/ })).toBeAttached();

  await page.getByRole("button", { name: /执行 72 项测试/ }).click();
  await expect(page.getByText("REPORT READY")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("高影响操作绕过人工审批")).toBeVisible();
  await page.getByRole("button", { name: /打开完整风险报告/ }).click();

  await expect(page.getByText("SAFETY GATE")).toBeVisible();
  await expect(page.getByText("不建议上线")).toBeVisible();
  await expect(page.locator(".report-grade b")).toHaveText("E");
  await expect(page.getByText("可复现的问题证据")).toBeVisible();

  await page.getByRole("button", { name: "公开基准" }).click();
  await expect(page.getByText("演示排行榜")).toBeVisible();
  await expect(page.getByText("Harbor Guard Agent")).toBeVisible();
  await expect(page.getByText("官方复测").first()).toBeVisible();

  await page.getByRole("button", { name: "竞技场" }).click();
  await expect(page.getByText("多 Agent 竞技场")).toBeVisible();
  await expect(page.getByText("浏览器内确定性模拟 · 无 API KEY")).toBeVisible();
  await expect(page.locator(".scenario-grid article")).toHaveCount(12);
  expect(writeRequests).toEqual([]);
});

test("风险 Demo 可以选择加固 Agent 并得到 A 级报告", async ({ page }) => {
  await page.goto("/agent-reliability-arena/");
  await page.getByLabel("被测 Agent").selectOption("demo-hardened");
  await page.getByRole("button", { name: /执行 72 项测试/ }).click();
  await expect(page.getByText("REPORT READY")).toBeVisible({ timeout: 15_000 });
  await page.getByRole("button", { name: /打开完整风险报告/ }).click();
  await expect(page.locator(".report-grade b")).toHaveText("A");
  await expect(page.getByText("建议上线")).toBeVisible();
  await expect(page.getByText("降级说明可以更具体")).toBeVisible();
});
