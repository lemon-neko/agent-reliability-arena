---
date: 2026-09-01
type: feature
status: completed
components:
  - web
  - public-demo
  - competition
compatibility: compatible
---

# 浏览器内交互式确定性 Demo

## 原因

原公开 Demo 能浏览冻结场景、轨迹与榜单，但“发起竞技”在 Demo 模式下完全禁用，评委无法亲手触发运行、观察事件推进或参与人工审批。比赛现场还需要避免 API Key、模型延迟、网络波动和真实副作用，因此不适合直接把公开页面改成远程模型调用。

## 最终变化

- 新增 Prompt Injection、人工审批和路径穿越三个公开确定性剧本。
- 新增纯浏览器比赛状态机，支持双 Agent 逐步竞速、1×/2× 播放、人工审批暂停、重新播放和剧本切换。
- 新增四维评分结算、胜负原因及跳转完整 Trace 的交互闭环。
- Demo 全程只使用随构建发布的脱敏素材，用户选择与审批仅保存在页面内存。
- Playwright 覆盖审批暂停、评分完成、完整轨迹和“没有非 GET 请求”的安全边界。
- 同步更新产品状态、架构边界、运行说明、参赛脚本和 Evidence Ledger。

## 影响与兼容性

- REST、SSE、报告 JSON、场景格式和本地完整模式不变。
- GitHub Pages 从只读展板升级为交互式回放，但仍然没有外部写入、后端连接或模型调用。
- 公开榜单仍使用冻结示例数据，模拟比赛不会写入或改变排名。

## 验证

- `make demo`
- `make test-web`
- `make check`
- Playwright 验证页面运行期间没有非 GET 请求

## 回滚

移除 `features/demo/`，恢复 `App.tsx` 在 Demo 模式下使用原 `TournamentBuilder`，并恢复相关文档措辞即可。没有数据库、远程状态或用户数据需要回滚。

## 关联

- Commit：待提交后补充
- Issue/PR：无
