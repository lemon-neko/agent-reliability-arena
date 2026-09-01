# 本地开发

## 安装

```bash
make setup
```

命令会在根 `.venv` 中以 editable 模式安装 `apps/api`，并在 `apps/web` 安装前端依赖。

## 启动

一条命令启动真实 API、两个参考 Agent Endpoint 和 Web：

```bash
make demo-live
```

打开 `http://127.0.0.1:5173`，使用以下本地 Target：

```text
http://127.0.0.1:8000/examples/agents/hardened/step
http://127.0.0.1:8000/examples/agents/vulnerable/step
```

也可以分终端启动：

终端一：

```bash
make dev-api
```

终端二：

```bash
make dev-web
```

风险体检不需要平台模型或 API Key；它通过 `ara-step/1` 调用被测 Agent。原 Arena 默认使用 `fake://deterministic`，无需密钥或网络。真实模型通过 OpenAI-compatible 接口配置；只有 `ALLOW_EXTERNAL_MODELS=true` 时才允许非本地端点。

只演示公开静态流程可运行 `make demo` 并打开 `http://127.0.0.1:4173/agent-reliability-arena/`。该模式会动态推进冻结的 72 次 Standard 数据，不连接真实 Agent 或后端。

`runtime/` 保存本地 SQLite、评测状态和临时运行目录，属于本机状态。目录重构不会移动或删除现有数据库。Agent 凭证值应放在未提交的环境变量中；Target 只填写变量名称。
