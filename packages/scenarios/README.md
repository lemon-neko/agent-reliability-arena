# 可靠性场景包

`catalog/` 保存 12 个版本化 YAML 副本，覆盖文件、SQL、RAG、人工审批与安全五类能力。场景格式由 [JSON Schema](scenario-v1.schema.json) 描述，权威 Python 类型是 `ScenarioSpec`。

新增场景时：

1. 复制 [示例场景](example.yaml)。
2. 使用新的 kebab-case ID 和语义版本。
3. 只声明任务真正需要的工具。
4. 提供确定性 `scripted_actions` 与 `scripted_answer`。
5. 运行 `make check-scenarios`。
