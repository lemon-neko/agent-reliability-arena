# HTTP Agent 接入：ara-step/1

`ara-step/1` 是 v0.2 唯一支持的外部 Agent 协议。平台负责循环、工具执行、权限、沙箱和 Trace；你的 Endpoint 负责根据消息返回下一步意图。

## 请求

平台对已配置的 Endpoint 发送 `POST application/json`：

```json
{
  "protocol": "ara-step/1",
  "run_id": "risk-run-abc123",
  "step": 1,
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "retrieval",
        "description": "Restricted, synthetic arena retrieval tool",
        "parameters": {"type": "object", "properties": {}}
      }
    }
  ],
  "limits": {"remaining_steps": 8, "deadline_ms": 15000}
}
```

工具执行后，消息历史会追加一条描述工具意图的 `assistant` 消息和一条带 `tool_call_id` 的 `tool` 结果。Endpoint 应使用 `run_id` 隔离状态，但不能假定不同 Run 按顺序到达。

## 响应

每次响应只能是以下二者之一，未知字段会被拒绝。

```json
{"type":"tool_call","call_id":"call-1","name":"retrieval","arguments":{"query":"policy"}}
```

```json
{"type":"final","output":"最终回答"}
```

响应必须使用 `application/json`，大小不得超过 1 MB。平台不跟随重定向；单次 HTTP 超时不会超过 Run 剩余截止时间。

## 最小 Python 示例

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/step")
def step(payload: dict) -> dict:
    tool_results = [item for item in payload["messages"] if item["role"] == "tool"]
    if not tool_results and any(t["function"]["name"] == "retrieval" for t in payload["tools"]):
        return {
            "type": "tool_call",
            "call_id": f"retrieval-{payload['step']}",
            "name": "retrieval",
            "arguments": {"query": "policy", "limit": 2},
        }
    return {"type": "final", "output": "I used the available evidence and stopped safely."}
```

仓库还提供可真实调用的加固与脆弱参考 Endpoint：

```text
POST /examples/agents/hardened/step
POST /examples/agents/vulnerable/step
```

## 最小 TypeScript 示例

以下处理函数可直接放进 Express、Hono 或其他 Web 框架的 `POST /step` 路由。类型故意保持完整，接入时不要把 `tool` 消息改成私有格式。

```typescript
type Message = {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  tool_call_id?: string;
};

type StepRequest = {
  protocol: "ara-step/1";
  run_id: string;
  step: number;
  messages: Message[];
  tools: Array<{
    type: "function";
    function: { name: string; description: string; parameters: object };
  }>;
  limits: { remaining_steps: number; deadline_ms: number };
};

type StepResponse =
  | { type: "tool_call"; call_id: string; name: string; arguments: object }
  | { type: "final"; output: string };

export function nextStep(input: StepRequest): StepResponse {
  const hasToolResult = input.messages.some((message) => message.role === "tool");
  const retrieval = input.tools.find((tool) => tool.function.name === "retrieval");
  if (!hasToolResult && retrieval) {
    return {
      type: "tool_call",
      call_id: `retrieval-${input.step}`,
      name: retrieval.function.name,
      arguments: { query: "policy", limit: 2 },
    };
  }
  return { type: "final", output: "I used the available evidence and stopped safely." };
}
```

## 凭证与网络范围

Target 只保存 `auth_header_name` 和 `auth_env_var`，不保存环境变量的值。Worker 在运行时读取该变量。

- `local`：只允许 `localhost`、`127.0.0.1` 或 `::1`，适合本机开发。
- `public`：必须使用 HTTPS，DNS 解析结果不得为私有、loopback、link-local、reserved、multicast 或 unspecified 地址。

公开榜单复验只接受无凭证或由维护者安全配置的公网 HTTPS Endpoint，不运行 PR 中提交的任意代码。

## 契约检查

保存 Target 后调用：

```http
POST /api/v1/agent-targets/{target_id}/validate
```

平台发送不含工具的安全探测，Endpoint 必须返回 `final`。契约通过不代表风险评测通过，只说明请求、认证和响应格式可用。
