# Web 应用

React + TypeScript 风险工作台，支持本地真实评测和 GitHub Pages 交互式确定性 Demo；原竞技场作为独立功能区保留。

- `src/app/`：页面壳和导航。
- `src/features/`：Agent 项目、风险评测、执行中心、报告、公开基准和竞技场。
- `src/features/assessment/`：真实评测表单与 72 次运行的纯浏览器 Demo。
- `src/features/demo/`：保留的 Arena 浏览器剧本。
- `src/shared/`：API、协议类型与公共标签。
- `public/data/risk-demo.json`：冻结、脱敏的风险用例、报告和演示榜单。
- `public/data/report.json`：原 Arena 场景、榜单与示例 Trace。
- `tests/`：Playwright Demo 验收。

从仓库根目录运行 `make dev-web`、`make test-web` 或 `make demo`。动态 Demo 的选择、播放和审批只存在于浏览器内存，不会发送写请求；公开数据边界见 [Demo 说明](../../docs/operations/public-demo.md)。
