# 报名材料

## 项目名称

Agent Reliability Arena / Agent 可靠性竞技场

## 一句话介绍

让不同 AI Agent 在相同的受控副本里反复挑战，用可回放轨迹和确定性评分证明它们不只是“偶尔答对”，而是真的可靠。

## 约 150 字版本

Agent Reliability Arena 是一个工具型 AI Agent 的可复现评测平台。它把不同模型和 Runtime 放入相同版本的文件、SQL、RAG、审批与安全场景，在独立沙箱中记录每次模型回合、工具调用、错误和审批，再以确定性规则评估正确性、安全、恢复和效率。与只看最终答案或依赖 LLM 主观打分的方案不同，竞技场强调过程证据、最小权限和结果可重算。项目可无 API Key 本地运行，并提供脱敏、无外部写入的交互式公开 Demo。

## 约 500 字版本

今天的 Agent Demo 往往只回答“它这一次做成了吗”，却无法回答更重要的问题：重复运行还稳定吗？调用工具时有没有越权？检索到恶意指令会不会泄密？高风险动作是否真的等待人工批准？失败后能否解释和复现？

Agent Reliability Arena 把这些隐性风险转化为可重复的工程数据。平台使用版本化 YAML 定义文件、SQL、RAG、人工审批和安全副本，为每次运行创建独立的虚构文件、SQLite 与文档环境。Agent 只能使用场景明确允许的受限工具，没有任意 Shell、通用 HTTP 或宿主文件访问。模型回合、工具请求、工具结果、审批、错误、Token 与成本形成有序 Trace，敏感字段在展示和存储前递归脱敏。

系统的 100 分核心评分由确定性规则计算：正确性 50 分、安全与策略遵循 25 分、恢复 15 分、效率 10 分。相同 Run 可以得到相同分数，可选 LLM Judge 也无权覆盖核心分。这使评测从“看起来不错”升级为“有证据、可回放、能回归”。

当前项目已经打通场景、双 Runtime、模型适配、沙箱工具、Trace、评分、REST/SSE、持久化、排行榜、React 控制台和交互式确定性 Demo 的完整闭环。它可以服务 Agent 产品 QA、模型/Runtime 对比、安全回归和客户可靠性审计。下一阶段将补充 Run 级并行、持久化恢复、最终状态 Oracle、失败聚类和统计显著性，让可靠性成为 Agent 发布流程中的标准门槛。

## 核心创新

1. **从结果评测转向过程评测**：最终答案、工具副作用、审批、错误与成本进入同一 Trace。
2. **确定性核心评分**：避免 LLM-as-a-Judge 的随机性直接决定榜单。
3. **最小权限副本**：工具能力由场景白名单约束，安全不是一句 Prompt。
4. **开发与公开展示分离**：完整模式可运行模型，公开 Demo 只使用冻结脱敏素材做浏览器内交互回放。
5. **Runtime 可对照**：Minimal 和 LangGraph 共用 Provider、工具与评分边界，便于隔离 Runtime 影响。

## 技术方案

- Python 3.12、FastAPI、Pydantic、SQLAlchemy、Alembic。
- LangGraph 与 OpenAI-compatible/Ollama 模型边界。
- PostgreSQL/pgvector、Redis/Celery、OpenTelemetry。
- React、TypeScript、Vite、TanStack Query、Recharts、SSE。
- Docker Compose、Pytest、Ruff、Playwright、GitHub Actions 与 Pages。

## 应用与商业价值

- 为 Agent 产品提供上线前回归门槛和版本对比。
- 为模型、Prompt、Runtime 或 RAG 改造提供统一基准。
- 为企业提供可交付的 Agent Reliability Audit、修复建议和持续监控服务。
- 将失败轨迹沉淀为后续安全规则、场景库与产品质量资产。

## English abstract

Agent Reliability Arena is a reproducible evaluation platform for tool-using AI agents. It runs models and agent runtimes against the same versioned file, SQL, RAG, approval, and security scenarios inside isolated synthetic environments. Instead of judging only the final answer, it records model turns, tool calls, approvals, errors, latency, tokens, and cost as replayable traces. A deterministic 100-point core score measures correctness, safety, resilience, and efficiency; an optional LLM judge cannot override it. The project is local-first, works without paid APIs through a deterministic provider, and publishes a sanitized interactive demo with no external writes. Its goal is to turn agent reliability from a polished screenshot into inspectable engineering evidence.

**Keywords:** AI agents, reliability evaluation, tool use, deterministic scoring, trace replay, sandbox, safety, RAG, human approval.
