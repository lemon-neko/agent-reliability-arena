# 公开排行榜与证明包

风险体检默认私有。只有 Agent 作者主动生成并通过 GitHub PR 提交脱敏 `Attestation v1` 时，结果才可能出现在公开排行榜。

## 提交流程

1. 使用 Agent 的明确版本运行 Standard Profile。
2. 在风险报告中确认没有 Endpoint、凭证、Prompt、Fixture 或原始 Trace。
3. 调用 `POST /api/v1/reports/{assessment_id}/attestation` 导出证明包。
4. 将文件命名为 `owner--agent--version.json`，提交到 `packages/registry/entries/`。
5. CI 校验 JSON Schema、Standard 测试包、Runner 版本、Hash 和隐私边界。
6. 维护者根据可复验程度更新验证等级；Pages 从审核后的 Registry 生成榜单。

## 验证等级

| 等级 | 含义 | 是否排名 |
|---|---|---|
| `self_reported` | 证明包格式有效，但未由项目方复验 | 否 |
| `reproducible` | 固定 Runner 能对公开 Endpoint 重跑 Standard 测试 | 是 |
| `verified` | 维护者在隔离环境执行额外复测 | 是 |

公开复验不会执行 PR 中的脚本或安装第三方仓库。它只从受信任默认分支运行本项目 Runner，并调用通过公网地址策略的 `ara-step/1` Endpoint。

## 排名规则

只对 `reproducible` 和 `verified` 条目排名，依次比较：门禁后的可靠性分、Critical 数、High 数、重复运行波动性和 Agent 名称。每一行必须显示 Agent 版本、测试包版本、Runner 版本、评测日期和验证等级。

证明包不包含原始报告，仅包含公开项目标识、分数、等级、结论、Finding 计数和 canonical report SHA-256。分数表达的是固定测试范围内的结果，不得宣传为绝对可信或正式合规认证。
