# 测试与验收

## 标准命令

```bash
make test-api        # Pytest + branch coverage
make test-web        # TypeScript build + Playwright
make check-scenarios # 目录加载与 JSON Schema 一致性
make check-governance# 项目地图、文档链接、change note
make check           # 全部检查
```

## 变更要求

- 核心运行、评分和工具变化必须增加单元测试。
- REST/SSE、冻结报告或交互式 Demo 变化必须增加 API 或 E2E 验收。
- 路径、Docker、迁移或 CI 变化必须运行 `docker compose config`。
- 实质批次必须增加 change note；跨模块长期决定增加 ADR。
- 安全测试只使用虚构 Secret 和临时目录，不得打印真实环境值。

CI 与本地 `make check` 使用同一组入口，避免“本地能跑、CI 另有一套规则”。
