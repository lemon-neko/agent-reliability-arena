# Evidence Ledger

本页把参赛主张绑定到可检查的工程证据，并标明当前边界。评审或宣传材料不得跳过状态列。

| 主张 | 状态 | 工程证据 | 边界 |
|---|---|---|---|
| 具有 12 个版本化虚构副本 | 已实现 | [场景目录](../../packages/scenarios/catalog)、[目录测试](../../apps/api/tests/test_scenarios_and_tools.py) | 当前全部为 v1.0.0 |
| 支持 Minimal 与 LangGraph Runtime | 已实现 | [Agent Runtime](../../apps/api/src/arena/runtime/agents.py)、[引擎测试](../../apps/api/tests/test_engine.py) | LangGraph Checkpoint 仅进程内 |
| 无需 API Key 可运行 | 已实现 | [Deterministic Provider](../../apps/api/src/arena/runtime/providers.py) | 假模型按公开脚本行动，不代表真实模型质量 |
| 支持 OpenAI-compatible/Ollama | 已实现 | [Provider 边界](../../apps/api/src/arena/runtime/providers.py)、[模型配置](../../apps/api/src/arena/infrastructure/config.py) | 当前只从环境配置一组真实模型 |
| 每个 Run 使用独立沙箱 | 已实现 | [Sandbox](../../apps/api/src/arena/runtime/sandbox.py)、[场景初始化](../../apps/api/src/arena/runtime/scenarios.py) | 不是不可信代码的 OS 级沙箱 |
| 不提供任意 Shell 或通用 HTTP | 已实现 | [Tool Gateway](../../apps/api/src/arena/runtime/tools.py) | Provider 自身仍按配置访问模型端点 |
| 防路径穿越和 symlink escape | 已实现 | [Sandbox 测试](../../apps/api/tests/test_scenarios_and_tools.py) | 仅覆盖受限 FileTool 路径 |
| Trace 有序并在落库前脱敏 | 已实现 | [Trace Recorder](../../apps/api/src/arena/runtime/tracing.py)、[脱敏测试](../../apps/api/tests/test_engine.py) | 规则需要随新凭证格式扩展 |
| 核心分是确定性的 | 已实现 | [Evaluator](../../apps/api/src/arena/domain/evaluation.py)、[重复评分测试](../../apps/api/tests/test_engine.py) | 当前 Oracle 以调用与文本匹配为主 |
| 支持人工审批 | 已实现但简化 | [Approval API](../../apps/api/src/arena/interfaces/http/app.py)、[审批测试](../../apps/api/tests/test_api.py) | 批准后重新执行，不是持久化 resume |
| 支持后台 Tournament | 已实现但简化 | [Celery Task](../../apps/api/src/arena/infrastructure/tasks.py)、[Service](../../apps/api/src/arena/application/service.py) | Tournament 内 Run 当前顺序执行 |
| 支持实时轨迹 | 已实现 | [SSE API](../../apps/api/src/arena/interfaces/http/app.py)、[Trace UI](../../apps/web/src/features/trace/TracePanels.tsx) | Store 轮询间隔为 250ms |
| 支持公开交互式 Demo | 已实现 | [Demo 状态机](../../apps/web/src/features/demo/InteractiveDemo.tsx)、[确定性剧本](../../apps/web/src/features/demo/demoScripts.ts)、[E2E](../../apps/web/tests/demo.spec.ts) | 只在浏览器内播放冻结剧本；不是实时模型推理，榜单也不是第三方模型正式排名 |
| 支持失败向量聚类 | 仅预留 | [Store 表定义](../../apps/api/src/arena/infrastructure/store.py) | 尚未生成 Embedding 或聚类 |
| 支持 Run 级并行与断点恢复 | 规划中 | [项目状态](../product/status.md)、[路线图](../product/roadmap.md) | 不得描述为已实现 |

## 演示前核验

```bash
make check
docker compose config
```

如果任一证据文件或测试失效，先修正文档或实现，再使用对应主张。
