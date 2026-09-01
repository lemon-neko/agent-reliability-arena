# 公开 Agent 证明包 Registry

`entries/` 只接收作者主动提交、通过 Schema 和隐私检查的 `Attestation v1`。本地原始 Trace、Endpoint、凭证、Prompt 与 Fixture 不得进入该目录。

验证等级：

- `self_reported`：只校验证明包结构，不参与正式排名。
- `reproducible`：使用固定 Standard 测试包从公开 Endpoint 复验，可进入排名。
- `verified`：由维护者在隔离环境再次复测，可进入排名并显示认证标记。

提交流程见[公开榜单说明](../../docs/operations/public-leaderboard.md)。格式见 [Attestation Schema](attestation-v1.schema.json)。
