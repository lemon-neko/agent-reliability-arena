# 项目状态

当前版本为 `v0.1` 工程基线。本页是“已经实现、当前简化、未来规划”的权威边界。

## 已经实现

- MinimalToolAgent 与 LangGraphAgent 共用 Provider、Tool Gateway 和 Trace 语义。
- 确定性假模型与 OpenAI-compatible 模型边界。
- 12 个版本化 YAML 场景和可复现虚构 Fixture。
- File、SQL、Retrieval、Approval、Secret 五种受限工具。
- 每 Run 独立临时目录、SQLite 和文档集合；路径穿越与 symlink escape 防护。
- 有序 Trace、递归脱敏、REST 查询和 SSE 增量展示。
- 50/25/15/10 的确定性核心评分。
- Tournament 幂等创建、重复运行、审批 API、排行榜和 JSON 报告。
- PostgreSQL/pgvector、Redis/Celery、Alembic、OpenTelemetry 的工程接入。
- React 控制台与纯静态、无外部写入的交互式确定性 Demo：支持三类安全剧本、双 Agent 逐步竞速、人工审批、四维评分和完整 Trace 跳转。

## 当前简化

- LangGraph Checkpoint 使用进程内 `MemorySaver`，审批批准后会重新执行 Run，不是跨 Worker 恢复。
- Tournament 内的 Run 在一个 Celery 任务中顺序执行，不是 Run 级并行扇出。
- 正确性主要检查期望工具调用、参数、结果片段和答案片段，不检查完整最终文件或数据库状态。
- 恢复分主要依据完成状态和错误事件，不等同于故障注入与真实恢复能力。
- RAG 使用轻量关键词匹配，不使用 pgvector 召回。
- OpenTelemetry 尚未配置 Collector/Exporter；失败向量表尚未进入聚类流程。
- `ScenarioSpec.timeout_seconds` 尚未成为 Run 级硬超时。
- 前端对比和报告属于展示基线，没有完整逐步骤 Diff 和导出工作流。
- 公开动态 Demo 播放冻结的确定性剧本，不是现场模型推理，也不会把模拟结果写入排行榜。

## 规划中，不得写成已完成

- Run 级并行锦标赛和资源配额。
- 持久化 LangGraph Checkpoint、interrupt/resume 与 Worker 重启恢复。
- 最终状态 Oracle、无关副作用检测和更强幂等验证。
- 故障注入、重试 Trace、硬超时和恢复时间指标。
- Embedding 检索、失败聚类、重复运行方差和统计显著性。
- 多 Provider 配置、完整报告导出与正式冻结公开榜单。

实施顺序见 [路线图](roadmap.md)，参赛材料中的事实证据见 [Evidence Ledger](../competition/evidence.md)。
