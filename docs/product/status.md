# 项目状态

当前版本为 `v0.2.0`。本页是“已经实现、当前简化、未来规划”的权威边界。

## 已经实现

- `ara-step/1` HTTP Agent 协议：严格请求/响应模型、单步单工具、1 MB 响应限制、Content-Type、重定向、超时与地址范围校验。
- Agent Target 只保存凭证环境变量名称，不保存密钥值；支持本地 loopback 和公网 HTTPS 两种范围。
- `tool-agent-baseline/1.0.0` 的 12 个风险用例，覆盖注入、泄密、越权、审批、副作用、证据、恢复和资源失控。
- Quick 12、Standard 72、Deep 180 次确定性矩阵；固定版本与 Seed 生成完全一致的变体。
- 单次 Assessment 内 1–8 并发、测试级超时、失败隔离、取消状态和 SSE 增量进度。
- 每 Run 独立临时文件、SQLite、检索文档、Secret、模拟 HTTP 与模拟业务记录；所有工具意图进入有序脱敏 Trace。
- 六维 100 分确定性评分、A–E 等级、Critical/High 安全门禁和上线建议。
- 管理层摘要、技术 Finding、Canonical JSON、自包含 HTML 与浏览器打印 PDF。
- 脱敏 Attestation、三类验证等级、Registry 校验和只纳入可复现/官方复测结果的公开榜单生成器。
- 故意脆弱与加固参考 Agent；前者稳定触发 High/Critical，后者 Quick 基线达到 A。
- GitHub Pages 交互式 Standard Demo：在浏览器内动态推进 72 次测试、展示风险触发、Trace、报告和演示榜单。
- 原 Arena 的 Tournament、Run、REST/SSE、评分和前端功能区保持可用。

## 当前简化

- 并发由单个 Assessment 后台任务内的线程池完成，还不是跨 Worker 的 Run 级任务扇出。
- 取消是协作式的：停止调度/执行后续测试，不能强制终止已经进入同步 HTTP 调用的线程。
- 公开 Registry 当前没有真实第三方可复现条目；Pages 榜单中的四行均明确标注为演示数据。
- HTML 报告可由浏览器打印为 PDF，尚未提供服务端二进制 PDF Endpoint。
- `ara-step/1` 是固定协议，不支持任意厂商 JSON 映射；参考 Agent 与 Runner 共进程仅用于本地演示。
- 12 个公开用例可以被针对性优化；固定变体增加覆盖，但不等同于动态红队。
- Mock HTTP 与业务动作只使用 Fixture，不执行真实外部副作用，因此无法证明生产系统自身的鉴权或事务边界。
- Standard 的两次重复可显示通过率和离散程度，但不构成统计显著性结论。
- 原 Arena 的 LangGraph Checkpoint 仍是进程内实现，审批恢复仍有既有简化。

## 规划中，不得写成已完成

- 私有测试包编辑器、组织策略与基线差异报告。
- 跨 Worker Run 扇出、持久化取消、队列配额与大规模压测。
- 动态 LLM 红队、状态级差分 Oracle 和更强的语义证据裁判。
- 服务端 PDF 签名、证明链、官方复测自动化和正式第三方榜单运营。
- 浏览器/桌面 Agent、SaaS 租户、账号计费和企业身份集成。
- 风险趋势、失败聚类、置信区间和持续监控告警。

评分边界见[风险评估方法](risk-methodology.md)，公开流程见[公开排行榜与证明包](../operations/public-leaderboard.md)，事实证据见 [Evidence Ledger](../competition/evidence.md)。
