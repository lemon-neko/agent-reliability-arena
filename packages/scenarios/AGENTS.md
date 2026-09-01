# 场景包规则

先遵守根目录 [AGENTS.md](../../AGENTS.md)。本目录只补充场景约束。

- 场景只能包含虚构数据、虚构 Secret 和可公开的 Prompt。
- `id + version` 唯一；破坏性语义变化必须提升版本。
- `expected` 和 `scripted_actions` 使用的工具必须在 `allowed_tools` 中。
- 场景必须可由确定性假模型运行，不依赖网络、时间或宿主状态。
- 修改场景模型或目录后运行 `make export-scenario-schema` 和 `make check-scenarios`。
