# 更新档案

本目录记录已经实现并完成验证的实质修改批次，回答“为什么改、最终改了什么、如何验证和回滚”。它补充 Git 历史，不替代产品、架构或状态文档。

## 规则

- 文件名为 `YYYY/YYYY-MM-DD-short-slug.md`。
- 功能、修复、重构、依赖、配置、迁移、测试治理和 CI 批次必须记录。
- 纯文档修字以及 change note 自身维护可以豁免。
- 从 [模板](template.md) 创建，填写原因、变化、影响、兼容、验证、回滚和关联项。
- 完成后把记录加入下方索引；长期跨模块决定另建 ADR。

## 当前记录

| 日期 | 类型 | 更新 | 模块 |
|---|---|---|---|
| 2026-09-01 | fix | [Runtime 源码跟踪与 CI 一致性](2026/2026-09-01-runtime-source-tracking.md) | API、CI |
| 2026-09-01 | feature | [Agent 风险体检、报告与公开基准](2026/2026-09-01-agent-risk-assessment.md) | API、Web、风险包、Registry、文档 |
| 2026-09-01 | ci | [兼容 CI 的 Python 命令入口](2026/2026-09-01-ci-python-runner.md) | Makefile、CI |
| 2026-09-01 | feature | [浏览器内交互式确定性 Demo](2026/2026-09-01-interactive-demo.md) | Web、公开 Demo、参赛材料 |
| 2026-08-31 | refactor | [AI 友好单仓库重构](2026/2026-08-31-ai-friendly-restructure.md) | 全仓库 |
<!-- new-change -->
