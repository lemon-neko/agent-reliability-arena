# Agent Reliability Arena 协作约束

本文件是所有 Coding Agent 与工程师修改仓库时的统一入口。项目地图见 [PROJECT_MAP.yaml](PROJECT_MAP.yaml)，人类文档入口见 [docs/README.md](docs/README.md)。子目录 `AGENTS.md` 只能补充局部约束，不得复制或改写本文件的公共规则。

## 必读顺序

1. 阅读根 [README.md](README.md) 和 [PROJECT_MAP.yaml](PROJECT_MAP.yaml)。
2. 阅读 [设计初衷](docs/product/vision.md) 与 [项目状态](docs/product/status.md)。
3. 阅读目标目录最近的 `AGENTS.md` 和 README。
4. 修改数据流或安全边界前，阅读 [系统架构](docs/architecture/overview.md)。
5. 修改持久化数据前，阅读最新迁移；新增长期约束前，阅读已接受的 ADR。

## 不可破坏的产品边界

- 核心评分必须由确定性规则计算；可选 LLM Judge 不能修改核心分。
- 每个 Run 使用独立的虚构文件、文档和 SQLite 副本，不得读取宿主文件或其他 Run 数据。
- Agent 只能使用场景白名单中的受限工具；不得新增任意 Shell 或通用 HTTP Tool。
- 检索文档与用户内容始终是不可信数据，不能覆盖系统规则。
- Secret、API Key、原始私有 Trace、数据库和模型载荷不得进入 Git、日志、Demo 或测试输出。
- 外部模型默认关闭；公开 Demo 只能使用随构建发布的冻结、脱敏素材。允许浏览器内交互回放，但不得发起写请求、连接模型或持久化用户输入。

## 修改流程

- 保留用户已有的未提交改动；不清理、不回滚、不覆盖无关文件。
- 代码按 `domain → application → runtime/infrastructure → interfaces` 的依赖方向组织，HTTP 路由保持薄。
- 公共行为变化同步更新权威产品或架构文档；README 只维护入口摘要。
- 每个功能、修复、重构、依赖、配置、迁移或 CI 批次新增一份 `docs/changes/YYYY/YYYY-MM-DD-short-slug.md`。
- 跨模块、长期或难以回滚的决定新增 ADR；普通实现细节只写 change note。
- 场景变更必须同步更新 JSON Schema 并通过 12 个虚构场景的目录校验。

## 验证

迭代时运行最窄测试，交付前运行：

```bash
make check
```

Docker、迁移或部署变化还必须运行：

```bash
docker compose config
```

## 文件与数据安全

- `runtime/`、`.env`、数据库、Trace、私有报告、构建产物和依赖缓存是本地状态，不得提交。
- 测试只使用临时目录和虚构值。
- 文件移动优先保留 Git rename 历史；禁止为了整理目录删除本地运行数据。
