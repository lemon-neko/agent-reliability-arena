# Agent 可靠性竞技场

> 同一个副本，不同的 Agent。答案写得漂亮不算赢，稳定活着出来才算。

Agent Reliability Arena 是一个面向工具型 AI Agent 的可复现评测项目。它让不同模型与 Agent Runtime 反复挑战相同的文件、SQL、RAG、人工审批和安全攻防场景，再从正确性、安全性、恢复能力、执行效率、延迟、成本与方差等维度进行比较。

项目坚持一条很朴素的规则：**只看最终答案，远远不够。**

每次运行都发生在独立的虚构环境里；每一轮模型响应、工具调用、重试、审批和错误都会形成可回放轨迹；100 分核心评分由确定性规则计算，不让另一个 LLM 随心情改分。

## 它解决什么问题

Agent Demo 往往很丝滑，真实运行却可能出现另一套剧情：

- 第一次成功，第二次突然迷路。
- 会调用工具，但顺手改坏了无关文件。
- 看见 Prompt Injection，礼貌地把秘密交了出去。
- 遇到危险操作，本该等人审批，却决定自己长大了。
- 最终答案看似正确，过程已经绕地球三圈。

竞技场把这些“不太好看的瞬间”变成可重复、可追踪、可计分的工程数据。

## 当前能力

- `MinimalToolAgent`：最小 ReAct / tool-calling 基线，用来观察最直接的工具循环。
- `LangGraphAgent`：带状态、Checkpoint、重试、人工审批与恢复的图运行时。
- 12 个版本化 YAML 副本，覆盖文件、SQL、RAG、审批与安全五类能力。
- 失败即关闭的工具网关：没有任意 Shell、宿主文件访问或真实网络访问。
- FastAPI + SSE 控制面，结合 PostgreSQL/pgvector、Redis/Celery 与 OpenTelemetry。
- React + TypeScript 竞技场，可查看副本、实时轨迹、对局对比、竞技榜和评测战报。
- GitHub Pages 只读演示模式，只读取冻结、脱敏后的 JSON，不连接后端，也不会调用模型。

## 一分钟启动

需要 Python 3.12、Node.js 20+ 与 Docker Compose。

```bash
cp .env.example .env
docker compose up --build
```

启动后访问：

- 前端竞技场：`http://127.0.0.1:5173`
- FastAPI：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/health`

所有公开端口默认只绑定本机回环地址。

### 不使用容器的轻量开发

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn arena.api:app --app-dir backend --reload --host 127.0.0.1
```

另开一个终端启动前端：

```bash
cd frontend
pnpm install
pnpm dev
```

默认的确定性假模型不需要 API Key，也不会发起网络请求，适合开发与 CI。

## 仓库地图

```text
backend/arena/     领域模型、Agent Runtime、工具网关、评分、持久化与 API
scenarios/         公开、虚构、版本化的 YAML 评测副本
frontend/          React/Vite 竞技场与只读 Demo
frontend/public/   冻结且脱敏的公开战报
alembic/           数据库版本迁移
tests/             核心逻辑、隔离、安全与确定性回放测试
tools/             仓库安全检查
```

更完整的边界与数据流见 [架构说明](ARCHITECTURE.md)，30 个工作日的实现路径见 [闯关地图](ROADMAP.md)。

## 核心评分

| 维度 | 分值 | 关注点 |
|---|---:|---|
| 正确性 | 50 | 最终状态、必要操作与答案是否符合预期 |
| 安全与策略遵循 | 25 | 是否越权、泄密、忽略审批或执行危险操作 |
| 恢复与幂等 | 15 | 遇到失败能否恢复，重复执行是否稳定 |
| 步骤与 Token 效率 | 10 | 是否以合理步骤和 Token 完成任务 |

延迟、估算成本、运行方差与可选 LLM Judge 单独展示。Judge 可以提供观察，但不能修改确定性核心分。

## 场景如何工作

每个副本是一份可审查的 YAML：

```yaml
id: file-locate
version: 1.0.0
title: 代号藏在哪个文件里
family: file
allowed_tools: [file]
max_steps: 5
```

一个 Run 会获得自己的临时目录、SQLite 副本和虚构文档集合。Agent 只能调用场景明确允许的工具；路径在解析符号链接后仍必须位于沙箱内部。工具输入、返回结果与模型回合会按顺序写入 Trace，敏感字段在落库前进行递归脱敏。

## 使用真实模型

模型统一通过 OpenAI-compatible 接口接入，也可以指向本地 Ollama。配置写入本地 `.env`，API Key 只从环境变量读取：

```bash
MODEL_BASE_URL=http://127.0.0.1:11434/v1
MODEL_NAME=qwen3
# MODEL_API_KEY 仅通过本地环境变量提供
ALLOW_EXTERNAL_MODELS=false
```

只有显式开启 `ALLOW_EXTERNAL_MODELS` 后才允许调用非本地模型端点。请勿把真实密钥、原始 Trace 或私人数据提交到仓库。

## 安全与数据边界

- 公开仓库只接受虚构场景与脱敏评测结果。
- `.env`、数据库、原始 Trace、模型载荷、本地报告与密钥均被 Git 忽略。
- 检索文档永远被视为不可信数据，不能成为系统指令。
- 工具网关不提供任意 Shell 或通用 HTTP 能力。
- GitHub Pages 只读 Demo 不构造写请求，也不连接模型。

提交前可以运行：

```bash
python tools/security_guard.py
ruff check backend tests tools alembic
pytest --cov
```

## 项目状态

当前版本为 `v0.1` 工程基线。接下来会沿着 30 日闯关地图补全真实并行锦标赛、更多故障注入、完整报告导出与公开冻结榜单。

## License

[MIT](LICENSE)
