# Web 区域规则

先遵守根目录 [AGENTS.md](../../AGENTS.md)。本目录只补充前端约束。

- `app/` 只负责页面编排，业务视图放入 `features/`，协议类型与 API 客户端放入 `shared/`。
- Demo 模式必须保持纯静态且无外部写入；可使用内存状态播放冻结剧本，但不得构造写请求、连接模型、持久化用户输入或读取本地数据库。
- REST、SSE 与冻结报告类型必须和后端契约保持一致。
- 不提交 `node_modules`、`dist` 或 TypeScript build info。
- 前端修改至少运行 `make test-web`；Demo、路由或部署变化还需运行 `make demo`。
