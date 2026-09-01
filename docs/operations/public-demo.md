# 交互式公开 Demo

公开 Demo 由四类随构建发布的素材组成：

- `apps/web/public/data/report.json`：场景、榜单和示例报告快照。
- `apps/web/src/features/demo/demoScripts.ts`：三个确定性比赛剧本及脱敏 Trace。
- `apps/web/public/data/risk-demo.json`：两个演示 Agent、12 个风险用例、双层报告和演示排行榜。
- `apps/web/public/data/public-leaderboard.json`：从审核 Registry 生成的真实公开条目；初始为空。

Vite 构建会把它们打包进静态站点，因此 Demo 不需要后端、模型或 API Key。风险主流程会动态播放 72 次 Standard 运行、逐条暴露 Finding、触发安全门禁并生成报告；Arena 入口继续提供双 Agent 竞速与模拟审批。这些状态只存在于浏览器内存。

文件只允许包含：

- 虚构场景名称与公开元数据。
- 已经脱敏的示例 Trace。
- 聚合评分与运行统计。
- 公开确定性剧本及模拟审批结果。

发布新快照或剧本时，应从参考 Agent 的虚构评测生成候选内容，人工检查密钥与私有载荷，再通过独立 Commit 替换。Demo 模式永远不读取本地数据库、模型配置或原始 Trace，也不得发送任何非 GET 请求。界面必须标注演示数据，不能把回放描述成实时 Endpoint 或模型推理。
