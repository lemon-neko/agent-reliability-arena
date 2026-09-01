---
date: 2026-09-01
type: fix
status: completed
components:
  - apps/api
  - ci
compatibility: compatible
---

# Runtime 源码跟踪与 CI 一致性

## 原因

根 `.gitignore` 中未锚定的 `runtime/` 规则误匹配了 `apps/api/src/arena/runtime/`，使本地已参与测试的 `ara-step/1`、风险场景和参考 Agent 源文件没有进入 Git。CI 因此无法导入这些模块；同时 Ruff 对 first-party 包的自动识别在本地与 CI 安装环境中存在差异。

## 最终变化

- 将私有运行数据、Trace 和报告忽略规则锚定到仓库根目录。
- 补交 `arena.runtime` 的包入口、Step Protocol、风险场景加载器和参考 Agent。
- 在 Ruff 配置中明确声明 `arena` 为 first-party 包，统一 import 排序结果。

## 影响与兼容性

不改变 REST、SSE、数据库 Schema、风险评分或前端行为。私有根目录 `runtime/`、`traces/` 和 `reports/private/` 仍被忽略；仅修正源码目录被误排除的问题。

## 验证

- `make check`
- GitHub Actions 后端可导入 `arena.runtime.step_protocol` 和 `arena.runtime.risk_scenarios`。
- GitHub Actions 前端构建与两项 Playwright Demo 测试通过。

## 回滚

恢复原忽略规则并移除新增跟踪的 runtime 源文件；这会使全新检出无法运行风险评测，因此只应与整个 v0.2 风险体检功能一起回滚。

## 关联

- Issue：无
- Commit：`8b14833`、`3cb76a2`
