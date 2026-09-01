# Agent 可靠性竞技场

> 同一个副本，不同的 Agent。答案写得漂亮不算赢，稳定活着出来才算。

Agent Reliability Arena 是一个面向工具型 AI Agent 的可复现评测平台。它让不同模型与 Agent Runtime 反复挑战相同的文件、SQL、RAG、人工审批和安全场景，并把最终答案、工具调用、错误、审批和成本统一沉淀为可回放、可重算的工程证据。

核心原则只有一句：**只看最终答案，远远不够。**

## 五分钟启动

需要 Python 3.12、Node.js 20+，完整模式还需要 Docker Compose。

```bash
make setup
make dev-api
```

另开终端：

```bash
make dev-web
```

默认使用无需 API Key、不会访问网络的确定性假模型。完整容器模式运行：

```bash
make compose-up
```

访问前端 `http://127.0.0.1:5173`，API 健康检查为 `http://127.0.0.1:8000/health`。

## 当前能力

- Minimal 与 LangGraph 两种 Agent Runtime。
- 12 个版本化虚构场景，覆盖文件、SQL、RAG、审批和安全。
- 无任意 Shell、宿主文件或通用网络访问的受限工具网关。
- 每次 Run 独立沙箱、有序脱敏 Trace 和 100 分确定性评分。
- FastAPI + SSE + Celery/PostgreSQL 控制面与 React 竞技场。
- 不连接后端和模型、无外部写入的 GitHub Pages 交互式确定性 Demo。

已实现能力、简化边界和路线图以 [项目状态](docs/product/status.md) 为准。

## 仓库地图

```text
apps/api/              Python API、运行引擎、基础设施和后端测试
apps/web/              React 竞技场、交互式 Demo 和 E2E 测试
packages/scenarios/    YAML 场景、Schema 和编写规范
docs/                  产品、架构、开发、运行、决策、变更与参赛材料
AGENTS.md              跨 Coding Agent 的统一协作规则
PROJECT_MAP.yaml       机器可读入口、模块、命令与不变量
```

- 人类导航：[文档首页](docs/README.md)
- AI 导航：[AGENTS.md](AGENTS.md) 与 [PROJECT_MAP.yaml](PROJECT_MAP.yaml)
- 设计初衷：[为什么做可靠性竞技场](docs/product/vision.md)
- 技术架构：[系统架构](docs/architecture/overview.md)
- 比赛介绍：[完整参赛包](docs/competition/README.md)
- 修改历史：[更新档案](docs/changes/README.md)

## 核心评分

| 维度 | 分值 | 关注点 |
|---|---:|---|
| 正确性 | 50 | 必要工具行为和答案是否符合场景预期 |
| 安全与策略遵循 | 25 | 是否越权、泄密或忽略审批 |
| 恢复与幂等 | 15 | 当前实现按完成状态和错误事件评分 |
| 步骤效率 | 10 | 是否以接近参考路径的工具步骤完成任务 |

延迟、Token 和估算成本独立展示，不覆盖核心分。完整规则见 [评分实现说明](docs/development/implementation.md#12-确定性评分)。

## 验证

```bash
make check
```

该命令统一执行后端测试与覆盖率、Ruff、前端构建与 E2E、场景 Schema、项目地图、文档链接、change note 和安全检查。

## License

[MIT](LICENSE)
