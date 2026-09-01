# Evidence Ledger

本页把 v0.2 参赛主张绑定到可检查的工程证据。评审或宣传材料不得跳过“边界”列。

| 主张 | 状态 | 工程证据 | 边界 |
|---|---|---|---|
| 支持 `ara-step/1` HTTP Agent | 已实现 | [协议实现](../../apps/api/src/arena/runtime/step_protocol.py)、[协议测试](../../apps/api/tests/test_step_protocol.py) | 固定协议，不支持任意 JSON 映射 |
| Target 不持久化凭证值 | 已实现 | [领域模型](../../apps/api/src/arena/domain/risk.py)、[Store](../../apps/api/src/arena/infrastructure/store.py) | Worker 仍需安全配置环境变量 |
| 具有 12 个版本化风险用例 | 已实现 | [风险包](../../packages/risk-packs/tool-agent-baseline/v1)、[矩阵测试](../../apps/api/tests/test_risk_scenarios.py) | 公开用例可能被针对性优化 |
| Quick/Standard/Deep 为 12/72/180 Run | 已实现 | [矩阵生成器](../../apps/api/src/arena/runtime/risk_scenarios.py)、[测试](../../apps/api/tests/test_risk_scenarios.py) | Standard 两次重复不构成统计显著性 |
| 支持 1–8 并发与失败隔离 | 已实现 | [Service](../../apps/api/src/arena/application/service.py)、[API 测试](../../apps/api/tests/test_risk_api.py) | 单任务线程池，不是跨 Worker 扇出 |
| 支持超时与取消 | 已实现但有限制 | [风险引擎](../../apps/api/src/arena/application/risk_engine.py)、[协议测试](../../apps/api/tests/test_step_protocol.py) | 取消是协作式，不能强杀已开始的同步调用 |
| 工具只在独立合成沙箱执行 | 已实现 | [Tool Gateway](../../apps/api/src/arena/runtime/tools.py)、[风险引擎测试](../../apps/api/tests/test_risk_engine.py) | 不是 OS 级沙箱，不执行真实外部副作用 |
| HTTP 与业务动作是 Fixture-backed | 已实现 | [Mock 工具](../../apps/api/src/arena/runtime/tools.py)、[风险包](../../packages/risk-packs/tool-agent-baseline/v1) | 不验证生产系统自身权限与事务 |
| 六维评分与 Critical/High 门禁确定性 | 已实现 | [风险评分](../../apps/api/src/arena/domain/risk_evaluation.py)、[测试](../../apps/api/tests/test_risk_engine.py) | Oracle 只覆盖当前公开规则 |
| 加固参考 Agent 达 A，脆弱版本触发门禁 | 已实现 | [参考 Agent](../../apps/api/src/arena/runtime/reference_agents.py)、[引擎测试](../../apps/api/tests/test_risk_engine.py) | 参考实现不代表第三方 Agent |
| 输出 JSON 与自包含 HTML 报告 | 已实现 | [报告模块](../../apps/api/src/arena/application/reporting.py)、[报告测试](../../apps/api/tests/test_reporting_and_registry.py) | PDF 通过浏览器打印，不是服务端二进制 Endpoint |
| Attestation 不含私有报告内容 | 已实现 | [报告模块](../../apps/api/src/arena/application/reporting.py)、[脱敏测试](../../apps/api/tests/test_reporting_and_registry.py) | 作者仍需在提交前审阅公开标识 |
| 自报告不参与正式排名 | 已实现 | [Registry](../../apps/api/src/arena/infrastructure/registry.py)、[Registry 测试](../../apps/api/tests/test_reporting_and_registry.py) | 当前没有真实第三方正式条目 |
| 公开 Demo 动态展示 72 次测试 | 已实现 | [Demo 数据](../../apps/web/public/data/risk-demo.json)、[体检状态机](../../apps/web/src/features/assessment/RiskAuditDemo.tsx)、[E2E](../../apps/web/tests/demo.spec.ts) | 浏览器模拟，不连接真实 Agent，不发送写请求 |
| 本地完整 Demo 调用两个参考 Agent | 已实现 | [启动器](../../tools/demo_live.py)、[参考 Endpoint](../../apps/api/src/arena/interfaces/http/app.py) | 仅用于本地开发展示 |
| 原 Arena 仍可用 | 已实现 | [Arena UI](../../apps/web/src/features/arena/ArenaWorkspace.tsx)、[原引擎测试](../../apps/api/tests/test_engine.py) | Arena 仍保留既有简化 |
| 动态 LLM 红队、浏览器 Agent、SaaS 计费 | 规划中 | [项目状态](../product/status.md) | 不得描述为已实现 |

## 演示前核验

```bash
make check
docker compose config
```

如果任一证据文件或测试失效，先修正文档或实现，再使用对应主张。
