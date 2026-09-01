# Agent 风险测试包

`tool-agent-baseline/v1/` 是 HTTP 工具型 Agent 的首个固定测试包，包含 12 个基准用例。运行器根据固定 Seed 将其扩展为 Quick、Standard 和 Deep 三种矩阵。

用例必须只包含虚构数据，并通过 [RiskCase JSON Schema](risk-case-v1.schema.json)。修改后运行：

```bash
make check-risk-packs
```

评分方法见[风险评估方法](../../docs/product/risk-methodology.md)，协议见[HTTP Agent 接入](../../docs/development/http-agent-protocol.md)。
