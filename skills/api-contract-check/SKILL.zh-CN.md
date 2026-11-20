# API 契约检查（中文版）

## 什么时候用

当你有一批**逐调用 JSONL 记录**，想检查：

- 每次成功调用是否都有明确的结束事件？
- 空文本/截断流有没有写清失败原因？
- `usage` 字段是否完整、非负？
- `first_token_s` 有没有说明是“首个任意事件”还是“首个可见文本”？

典型场景：API 兼容性审计、评测流水线体检、复现某个 API 问题报告。

## 什么时候不要用

- 不要拿它做模型能力排名；
- 不要用它断言“某 API 已修复/未修复”（除非有新调用证据）；
- 不要输入 prompt、题面、原始输出、密钥、客户数据；
- 不要把“0 条违规”当成“协议没问题”——它只说明记录可核对。

## 输入字段

每行一个 JSON，至少包含：

```text
call_id, provider, protocol, dataset, problem_id,
terminal_event, terminal_event_type, visible_text_chars,
failure_reason, usage, first_token_s, first_token_definition
```

完整字段见 `references/record-schema.md`。

## 怎么跑

```bash
python scripts/check_records.py records.jsonl --json report.json
```

返回：

- `total`：总记录数；
- `violating_records`：有违规的记录数；
- `violation_codes`：各类违规计数；
- `clean`：是否全部通过。

## 六条检查

| 编号 | 检查 |
|---|---|
| C1 | 声明有终止事件 → 必须有终止事件类型 |
| C2 | 无终止事件 + 空文本 → 必须有 failure_reason |
| C3 | 无终止事件 + 有文本 → 必须有 failure_reason |
| C4 | 必须有 usage，且不能为负 |
| C5 | 有 first_token_s → 必须声明 first_token_definition |
| C6 | failure_reason=max_tokens → finish_reason 必须可区分 |

## 失败怎么处理

- `FileNotFoundError`：检查路径，不要伪造记录；
- `JSONDecodeError`：报告行号，不要静默跳过；
- `clean=false`：当数据质量问题处理，不要当模型行为结论；
- 技能与工具冲突：以 `llm-api-contract` 工具为准，并记录版本。

## 数据边界

允许：公开题号、哈希、计数、状态、耗时、usage。

禁止：题面、prompt、模型原始输出、API key、客户数据、本机路径。

## 输出建议

除了 JSON 汇总，还应写一段简短说明：

- 总记录数、违规记录数、违规类型；
- 按协议/数据集拆分；
- 这个结果**不能证明**什么。

## 相关链接

- 工具：`llm-api-contract`（代码 DOI `10.5281/zenodo.24399656`）
- 背景：`10.5281/zenodo.24269158`
