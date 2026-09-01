---
date: 2026-08-31
type: refactor
status: completed
components:
  - repository
  - api
  - web
  - scenarios
  - documentation
  - ci
compatibility: breaking-layout
---

# AI 友好单仓库重构

## 原因

原仓库按语言和早期实现自然生长，代码、场景、文档与运行入口缺少统一导航。人类需要反复搜索职责，Coding Agent 也无法快速确定权威文档、安全边界和修改后的记录要求；比赛介绍与工程事实分散，容易过度宣传预留能力。

## 最终变化

- 建立 `apps/api`、`apps/web`、`packages/scenarios` 和分域 `docs` 的应用型单仓库。
- Python 包按 domain、application、runtime、infrastructure、interfaces 分层，前端按 app、features、shared 分层。
- 新增根与局部 `AGENTS.md`、机器可读 `PROJECT_MAP.yaml` 和目录 README。
- 建立 ADR、结构化 change note、项目地图、文档链接和场景 Schema 检查。
- 汇总设计初衷、当前状态、证据台账和完整 AI 应用创新赛材料。
- 统一 Make、Docker Compose、Alembic、CI、Pages 和安全检查入口。

## 影响与兼容性

- REST、SSE、场景字段、报告 JSON 和前端行为保持不变。
- 旧 `backend/`、`frontend/`、`scenarios/`、根 Alembic 与旧 Python 模块路径不再提供兼容入口。
- 本地 `runtime/arena.db`、`.venv`、Node 缓存和私人运行数据不迁移、不删除。

## 验证

- `make check`
- `docker compose config`
- 全仓旧路径引用扫描

## 回滚

使用 Git 恢复本批次涉及的源码、配置和文档。数据库 Schema 与本地运行数据未改变，无需数据回滚。

## 关联

- ADR：[0001 — AI 友好应用型单仓库](../../decisions/0001-ai-friendly-monorepo.md)
- Commit：待提交后补充
- Issue/PR：无
