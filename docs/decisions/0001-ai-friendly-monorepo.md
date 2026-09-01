# 0001 — AI 友好应用型单仓库

- 状态：Accepted
- 日期：2026-08-31
- 决策者：项目维护者

## 背景

项目同时包含 Python 控制面、React 前端、版本化评测数据、部署配置和大量解释性材料。早期的 `backend/`、`frontend/`、`scenarios/` 结构能运行，但没有表达应用边界、内部依赖方向或文档权威性。不同 Coding Agent 需要反复搜索才能确定入口，也没有统一的实质变更记录。

## 决策

- 使用 `apps/api`、`apps/web`、`packages/scenarios` 和 `docs` 组织仓库。
- API 内采用 domain、application、runtime、infrastructure、interfaces 分层。
- 根 `AGENTS.md` 是所有 Agent 的唯一公共规范，子目录只补充局部规则。
- `PROJECT_MAP.yaml` 提供机器可读入口，目录 README 提供人类导航。
- Git 记录提交历史，结构化 change note 记录每个可独立验收的实质批次，ADR 记录长期决定。

## 备选方案

- **只新增文档、不移动源码**：风险最低，但无法让目录本身表达应用与职责边界。
- **按业务域把 Python 与 React 混合在顶层**：领域感更强，但跨语言构建和部署入口更难理解。
- **分别维护 AGENTS、CLAUDE、Cursor 规则**：初看兼容更直接，长期必然产生规则漂移。

## 后果

- 人类和 Agent 能从根入口在两次跳转内找到代码、权威文档与验证命令。
- 内部文件和 Python 导入路径发生破坏性变化，需要同步更新构建、Docker、CI 和文档。
- REST/SSE 与用户行为不因目录决定而改变。
- 后续实质修改必须承担 change note 和治理检查成本，以换取可追溯性。
