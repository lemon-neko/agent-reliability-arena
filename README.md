# Agent Reliability Arena

> 给自研 Agent 做一次可复现的上线前风险体检。

Agent Reliability Arena v0.2 面向 HTTP 工具型 Agent 自动执行 12–180 次隔离测试，检查 Prompt Injection、敏感信息泄露、越权工具、审批绕过、危险副作用、幻觉、故障恢复和资源失控，并生成管理层与开发者都能使用的风险报告。

[在线动态 Demo](https://lemon-neko.github.io/agent-reliability-arena/) · [设计初衷](docs/product/vision.md) · [风险评估方法](docs/product/risk-methodology.md) · [HTTP Agent 接入协议](docs/development/http-agent-protocol.md)

## 五分钟体验

需要 Python 3.12、Node.js 20+ 和 pnpm。

```bash
make setup
make demo-live
```

访问 `http://127.0.0.1:5173`。在“Agent 项目”注册以下任一内置参考 Endpoint：

```text
http://127.0.0.1:8000/examples/agents/hardened/step
http://127.0.0.1:8000/examples/agents/vulnerable/step
```

也可以分别启动：

```bash
make dev-api
make dev-web
```

## 产品主流程

```text
注册 ara-step/1 Endpoint
→ 验证协议
→ 选择 Quick / Standard / Deep
→ 并发执行隔离测试
→ 查看 Trace 与风险 Finding
→ 导出 JSON / HTML / PDF
→ 可选提交脱敏证明包
```

- Quick：12 次运行，用于接入冒烟。
- Standard：36 个逻辑测试 × 2 次重复，共 72 次，用于发布门禁和公开证明。
- Deep：60 个逻辑测试 × 3 次重复，共 180 次，用于深度回归。

所有真实工具动作由平台受控网关执行。Agent Endpoint 只返回一个 `tool_call` 或 `final`，不会直接获得宿主文件、数据库、Shell 或通用网络能力。公开 Demo 是浏览器内确定性回放，不连接 Agent，不产生写请求。

## 仓库地图

```text
apps/api/              FastAPI、风险执行引擎、Arena 与持久化
apps/web/              风险工作台、公开 Demo、报告与竞技场
packages/scenarios/    原 Arena 版本化场景
packages/risk-packs/   风险测试包与 RiskCase Schema
packages/registry/     公开脱敏证明包与排行榜 Registry
docs/                  产品、架构、接入、运维、决策和参赛材料
```

AI 协作入口见 [AGENTS.md](AGENTS.md) 和 [PROJECT_MAP.yaml](PROJECT_MAP.yaml)，当前已实现边界见[项目状态](docs/product/status.md)。

## 验证

```bash
make check
docker compose config
```

## License

[MIT](LICENSE)
