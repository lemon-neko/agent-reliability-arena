---
date: 2026-09-01
type: ci
status: completed
components:
  - makefile
  - ci
compatibility: compatible
---

# 兼容 CI 的 Python 命令入口

## 原因

GitHub Actions 将后端开发依赖安装到 `setup-python` 提供的系统环境，而根 Makefile 强制调用仓库内 `.venv/bin/ruff` 和 `.venv/bin/pytest`，导致全新 CI Runner 在 lint 步骤报“文件不存在”。

## 最终变化

- Makefile 统一通过 Python 模块方式运行 Ruff、Pytest 和 Uvicorn。
- 仓库存在 `.venv/bin/python` 时优先使用本地虚拟环境；否则回退到 PATH 中的 `python3`。
- `make setup` 仍明确使用新建虚拟环境中的 Python 安装依赖。

## 影响与兼容性

本地命令和 CI 命令名称不变；已有 `.venv` 的开发者继续使用原虚拟环境，全新 Runner 可以直接使用已激活的系统 Python。

## 验证

- `make lint-api`
- `make test-api`
- `make check-governance`
- GitHub Actions `CI`

## 回滚

恢复 Makefile 中固定的 `.venv/bin/*` 路径即可；不涉及数据或远程状态回滚。

## 关联

- GitHub Actions Run：33464631150
- Commit：待提交后补充
- Issue/PR：无
