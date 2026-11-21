# agent-skills（中文说明）

> 给 Agent 用的“可复用技能包”：把可核对、可复现、可审计的工作流，写成 `SKILL.md` + 脚本 + 测试。
>
> 主要面向：做 LLM 评测、API 集成、Agent 工程、研究复现的朋友。

## 现在有什么

| 技能 | 用途 | 状态 |
|---|---|---|
| [`api-contract-check`](skills/api-contract-check/SKILL.zh-CN.md) | 检查大模型 API 的流式记录：有没有明确结束、失败有没有原因、usage/首 token 字段是否可核对 | v0.1.0 |
| [`material-to-metakb`](skills/material-to-metakb/SKILL.md) | 素材→结构化→元知识库：抓取留档、文本层/扫描 OCR、清洗后核验、入库前核验、SQLite 入库与健康检查 | v0.1.0 |
| `paper-code-release` | 论文代码脱敏、测试、公开仓、DOI 发布流程 | 计划中 |
| `evidence-ledger` | 主张—证据分级—未知项登记 | 计划中 |

## 为什么做这个

现在很多 API 评测/Agent 工程，会碰到这些“不是模型能力，但会污染结论”的问题：

- 流式响应没有明确的结束事件，客户端只能猜；
- 空文本到底是模型没输出，还是流被截断，记录里分不清；
- `usage`、`first_token` 在不同协议下口径不一致；
- 跨协议比较时，延迟/成本/成功率其实不可比。

这个技能包就是把这些“协议层”问题做成**可离线运行的检查**。

## 快速体验

```bash
# 1. 进入技能目录
cd skills/api-contract-check

# 2. 用示例记录跑一遍（示例里故意有坏数据）
python scripts/check_records.py examples/records.sample.jsonl
```

输出会列出：

- `C2_EMPTY_NO_REASON`：空文本但没有失败原因；
- `C4_USAGE_MISSING`：缺 usage；
- `C6_MAX_TOKENS_NO_FINISH_REASON`：max_tokens 但没有 finish_reason。

> 示例有坏记录，所以命令返回 1 是正常的；没有坏记录才返回 0。

## 六条检查（C1–C6）

| 编号 | 检查什么 |
|---|---|
| C1 | 说“有终止事件”，就必须有终止事件类型 |
| C2 | 没有终止事件 + 空文本 → 必须有 failure_reason |
| C3 | 没有终止事件 + 有文本 → 必须有 failure_reason |
| C4 | 必须有 usage，且不能为负 |
| C5 | 有 first_token_s，就必须声明 first_token_definition |
| C6 | failure_reason=max_tokens 时，finish_reason 要能区分 |

## 不做什么

- 不是模型能力排行榜；
- 不评价“哪个模型更聪明”；
- 不包含 prompt、题面、原始输出、API key、客户数据；
- 看到“0 条违规”也不等于“协议没问题”，只说明记录足够规范、可以核对。

## 数据边界

允许：公开题号、哈希、计数、状态、耗时、usage。

禁止：题面、prompt、模型原始输出、密钥、客户数据、本机绝对路径。

## 相关链接

- 工具本体：`llm-api-contract`（代码 DOI：10.5281/zenodo.24399656）
- 背景报告：`10.5281/zenodo.24269158`
- Gitee（国内访问更快）：https://gitee.com/yin-kang83/agent-skills
- GitHub：https://github.com/yin-kang83/agent-skills

## 许可

- 代码：MIT
- 文档/技能说明：CC BY 4.0
