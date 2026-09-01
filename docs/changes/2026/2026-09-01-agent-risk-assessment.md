---
date: 2026-09-01
type: feature
status: completed
components:
  - apps/api
  - apps/web
  - packages/risk-packs
  - packages/registry
  - docs
compatibility: additive
---

# Agent 风险体检、报告与公开基准

## 原因

原项目以 Arena 对照评测为主，无法直接接入团队已经存在的自研 HTTP Agent，也缺少批量风险测试、管理层报告和默认私有的公开证明流程。

## 最终变化

- 新增 `ara-step/1`、Agent Target、Assessment、TestRun、Finding、RiskReport 与 Attestation。
- 新增 12 个基准风险用例和固定 12/72/180 次测试矩阵。
- 变体真实改变 Prompt 包装、注入位置、权限组合和一次性工具故障计划。
- 新增 1–8 并发、超时、取消、失败隔离、SSE、六维评分和 Critical/High 门禁。
- 新增 Canonical JSON、自包含 HTML、浏览器打印 PDF、脱敏证明包和公开 Registry 生成器。
- 新增加固/脆弱参考 Agent、真实本地 Demo 与浏览器内 72 次动态公开 Demo。
- 将前端主导航调整为项目总览、Agent 项目、体检、执行、报告、公开基准和独立竞技场。
- 补齐 ESLint 9 Flat Config，并将前端静态检查纳入根 `make check`。

## 影响与兼容性

REST、SSE、场景字段、报告 JSON 和原 Arena 用户行为保持可用；新能力使用独立表和接口。内部版本升级至 `v0.2.0`。凭证值不进入数据库、报告或证明包；模拟 HTTP/业务工具不会触发真实外部副作用。

## 验证

- `make check`
- `docker compose config`（需要安装 Docker 的环境；当前本机未安装 Docker）
- 加固参考 Agent 的 Quick 评测达到 A 且无 High/Critical。
- 脆弱参考 Agent 触发 High/Critical 并被门禁至 E。
- Playwright 验证公开 Demo 完成 72 次评测、生成两种报告且无非 GET 请求。

## 回滚

回滚本批次代码和 `0002_risk_assessment` 迁移；删除新增风险表、风险包与 Registry 生成物即可恢复 v0.1 Arena 主界面。原 Arena 表和接口没有被改名或删除。

## 关联

- ADR：[0002 — 本地私有风险体检与主动公开证明](../../decisions/0002-private-risk-audit-and-public-attestation.md)
- Issue：无
- Commit：待提交
