# 报名材料

## 项目名称

Agent Reliability Arena / Agent 风险体检与公开基准

## 一句话介绍

把自研 HTTP Agent 接入一次，自动执行 12–180 次可复现风险测试，输出带 Trace 证据、修复建议和上线门禁的私有报告，并可选择提交公开基准。

## 200 字以内作品简介

Agent Reliability Arena 是面向自研工具型 Agent 的自动化风险体检平台。接入 HTTP Endpoint 后，可并发执行 12–180 次提示词注入、泄密、越权、审批绕过、副作用、幻觉、故障恢复与资源失控测试，生成确定性评分、风险证据、修复建议和上线结论。私有数据默认留在本机，作者可主动提交脱敏证明参与公开基准。演示：[lemon-neko.github.io/agent-reliability-arena](https://lemon-neko.github.io/agent-reliability-arena/)

## 约 500 字版本

当一个 Agent 获得文件、数据库、检索和业务工具后，“回答得像人”不再等于“可以上线”。真正的风险来自过程：检索内容中的恶意指令是否会改变行为，密钥是否会进入回答，未授权工具是否被调用，高影响操作是否绕过人工审批，故障重试是否造成重复副作用，以及任务是否陷入无限循环。

Agent Reliability Arena 把这些问题转化为自动化风险测试。用户只需让自研 Agent 实现轻量的 `ara-step/1` HTTP 协议，选择 Quick、Standard 或 Deep 测试包，平台便会在本地并发执行 12、72 或 180 次确定性测试。Agent 每一步只能返回一个工具意图；文件、SQL、检索、Secret、模拟 HTTP 和高影响业务动作均由平台在独立合成沙箱中执行，因此不会触碰真实外部系统。

系统不只检查最终答案，还记录工具意图、权限拒绝、审批顺序、错误、重试和耗时，生成可回放的脱敏 Trace。六个风险维度组成 100 分，Critical 风险会把等级限制为 E，High 风险限制为 D。最终报告同时服务管理者和工程师：前者看到 A–E 等级、上线建议与首要风险，后者看到每项 Finding 的预期/实际结果、证据事件、复现命令和修复建议。报告可导出 Canonical JSON、自包含 HTML，并用浏览器打印为 PDF。

所有私有 Prompt、Fixture、凭证和完整 Trace 默认留在本机。作者只有主动导出最小化 Attestation 并通过审核，才会进入公开榜单；自报告不参与正式排名。项目还保留原 Arena，用于比较模型和 Runtime。我们希望把 Agent 安全从一次演示升级为发布前可重复、可追责、可持续回归的工程门槛。

## 核心创新

1. **从 Agent 对战升级为自研 Agent 体检**：HTTP 接入后自动执行风险矩阵，不要求迁移业务 Runtime。
2. **工具意图与副作用分离**：Agent 只提议动作，平台在合成 Fixture 中执行、阻断并留证。
3. **确定性门禁**：固定测试包、Seed、Trace 和 Oracle；Critical/High 不能被平均分掩盖。
4. **双层报告**：管理层结论与工程级 Finding 使用同一证据源。
5. **私有结果与公开证明分离**：默认本地，公开只提交最小脱敏 Attestation，并标注验证等级。
6. **可操作的公开 Demo**：浏览器内动态推进 72 次测试，清楚标注演示数据且不发送写请求。

## 技术方案

- Python 3.12、FastAPI、Pydantic、SQLAlchemy、Alembic。
- `ara-step/1`、独立合成沙箱、受限 Tool Gateway、确定性 Oracle。
- PostgreSQL/pgvector、Redis/Celery、SSE、OpenTelemetry。
- React、TypeScript、Vite、TanStack Query、Recharts。
- JSON Schema、Attestation Registry、Pytest、Ruff、Playwright、GitHub Actions 与 Pages。

## 应用与商业价值

- 为 Agent 产品提供上线前 Quick/Standard/Deep 发布门禁。
- 为 Prompt、模型、RAG、权限或工具改造提供版本回归对比。
- 提供一次性风险体检、深度审计与修复计划、持续 CI 风险回归服务。
- 将失败 Trace 和修复验证沉淀为企业自己的 Agent 质量资产。

## English abstract

Agent Reliability Arena is a local-first risk assessment platform for custom tool-using agents. After implementing the lightweight `ara-step/1` HTTP protocol, an agent can be tested across 12, 72, or 180 deterministic runs covering prompt injection, data leakage, unauthorized tools, approval bypass, unsafe side effects, unsupported claims, failure recovery, idempotency, and resource control. The platform executes all tool operations inside isolated synthetic fixtures, records sanitized traces, applies deterministic severity gates, and produces executive and engineering reports with reproducible findings and remediation guidance. Private prompts, credentials, fixtures, and full traces stay local by default. Authors may opt in to a public benchmark by submitting a minimal attestation; self-reported entries are not formally ranked. The project turns agent safety from a polished demo into an inspectable release gate.

**Keywords:** AI agents, risk assessment, agent security, deterministic evaluation, trace evidence, release gate, prompt injection, tool safety.
