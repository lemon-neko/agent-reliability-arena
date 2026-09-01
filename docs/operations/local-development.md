# 本地开发

## 安装

```bash
make setup
```

命令会在根 `.venv` 中以 editable 模式安装 `apps/api`，并在 `apps/web` 安装前端依赖。

## 启动

终端一：

```bash
make dev-api
```

终端二：

```bash
make dev-web
```

默认使用 `fake://deterministic`，无需密钥或网络。真实模型通过 OpenAI-compatible 接口配置；只有 `ALLOW_EXTERNAL_MODELS=true` 时才允许非本地端点。

`runtime/` 保存本地 SQLite 和临时运行目录，属于本机状态。目录重构不会移动或删除现有数据库。
