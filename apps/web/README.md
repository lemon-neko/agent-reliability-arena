# Web 应用

React + TypeScript 竞技场，支持本地完整模式和 GitHub Pages 交互式确定性 Demo。

- `src/app/`：页面壳和导航。
- `src/features/`：发起竞技、场景、轨迹、排行榜和报告。
- `src/features/demo/`：纯浏览器比赛状态机、公开剧本、审批与动态评分。
- `src/shared/`：API、协议类型与公共标签。
- `public/data/report.json`：冻结、脱敏的公开场景、榜单与示例报告。
- `tests/`：Playwright Demo 验收。

从仓库根目录运行 `make dev-web`、`make test-web` 或 `make demo`。动态 Demo 的选择、播放和审批只存在于浏览器内存，不会发送写请求；公开数据边界见 [Demo 说明](../../docs/operations/public-demo.md)。
