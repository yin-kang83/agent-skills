# material-to-metakb · 素材 → 结构化 → 元知识库

> 技能 ID：`material-to-metakb`
> 适用：把公开/合法持有的资料（官网公告、PDF、题库 JSON、授课文本）经"抓取→抽取/OCR→清洗→核验→结构化→核验→入库"沉淀为可检索的元知识库。
> 定位：**证据优先、双门禁、原文不迁移**。本技能不含任何真实资料内容。

## 一、何时用

- 手上有一批 PDF/网页/JSON，需要变成可检索的结构化条目；
- PDF 有的是文本层、有的是扫描件，需要分流处理；
- 入库前需要"可回指来源"的证据链与门禁；
- 需要给素材打标签（主题/题型/考情），但**只保留标签、不复制原文**。

## 二、何时不要用

- 需要登录/扫码/付费墙、站点明确禁止抓取的来源；
- 没有授权却要把原文或实质改写件对外交付（出库须 clean-room 加工 + 人工签字）；
- 无 OCR 能力且不允许用系统 OCR——标注"需 OCR"，**不臆造文本**；
- 大批量并发抓取（应低频、逐条、可回溯）。

## 三、流程（九阶段，两道核验门禁）

### 1) 抓取与留档（fetch）

- 一手优先：官方公告 > 交易所/官网 > 权威媒体（仅线索）；
- 原始文件落**私有资料库根**（只读留底），不入 Git；
- 每个文件登记 `manifest.jsonl`：`{path, url, fetched_at, http_status, size, sha256, usage: internal_reference_only}`。

### 2) 抽取（extract，文本层优先）

- `pypdf` 逐页 `extract_text()`；`first_page_chars > 200` 视为可提取；
- 记录 `pages / chars / extractable`，供分流。

### 3) 扫描件 OCR（scanned）

- 渲染：`pypdfium2` 逐页 `page.render(scale=2.0).to_pil()` 存 PNG；**不要用 pypdf 的 page.images**（常只拿到共享 Logo）；
- OCR：Windows 内置 `Windows.Media.Ocr`（zh-Hans），脚本见 `scripts/windows_ocr.ps1`；
- **CJK 归一化必做**：Windows OCR 会在汉字间插空格，需去 CJK 间空白，否则关键词命中为 0；
- 记录 `pages_processed / page_failures / method`；失败页重试或标"需人工"。

### 4) 数据清洗（clean）

- 文本规范化：换行/全半角、页眉页脚/页码/水印、跨行断词；
- 结构识别：章节/题号/题型标题；识别不到标 `结构待核验`；
- 单位口径：万元/元、含税/不含税、累计/单季统一，不明标 `口径待核验`；
- 去重：内容 hash + 标题/编号；重复留一条记 `duplicate_of`；
- 异常：空白/乱码/错位页标 `issues[]`，空字段不猜测填充；
- 产物：`clean/*.jsonl` + `clean_report.json`。

### 5) 清洗后核验（clean-verify，第一道门禁）

- 完整性：清洗前后字符/行数变化在预期内（大幅缩水=截断）；
- 归一化正确性：CJK 归一不误删英文/数字空格；单位换算抽 5 条对原文；
- 抽样回指：5–10 条与原文副本比对；
- 异常清单：空白/乱码/错位页已标记；
- 产物：`clean_verify.json`（`PASS/FAIL` + 变更统计 + 抽样）；
- 失败即回退重清洗，**不进入结构化**。

### 6) 结构化（structure）

- 条目 schema（示例）：`{id, title, source_type, authority(official|third_party|unverified), domain, content, locator, retrieved_at, hash, usage}`；
- 标签 schema：`{source, topic_tags, topic_tag_counts, difficulty_signals, method, reliability}`；
- 纪律：原文不进交付物；自动标签统一标 `待核验`，第三方标 `third_party_unverified`。

### 7) 入库前核验（pre-ingest verify，第二道门禁）

1. **数据层**：JSON 合法、必填字段、hash 稳定、去重数一致；
2. **来源层**：每条回指 `source+locator`，抽 5–10 条回原页核对；
3. **语义/口径层**：单位/口径抽查，冲突标 `待核验` 不静默覆盖；
4. **目标库对齐**：先读表 schema 做字段映射预演，不通过不入库；
- 产物：`verify_sample.json` + `verify_record`；**FAIL 禁止入库**。

### 8) 入元知识库（ingest，仅接收 PASS 数据）

- 先读库表 schema（如 `PRAGMA table_info(<table>)`），按列插入；`id/hash` 去重；
- 首批 `--dry-run` → 插 1 条回读 → 通过后全量；
- 入库后只做**健康检查**：新增/跳过/失败计数、回读样本、检索抽 3 条；异常回滚该批。

### 9) 归档与续点

- 原始资料只读留底；仓库只放脚本/元数据/报告；记录"下次从哪继续"。

## 四、证据（必须能回指）

- 抓取：URL、HTTP 状态、SHA256、时间；
- 抽取：`pages/chars/extractable`；
- OCR：`pages_processed/page_failures/method`；
- 清洗：`clean_report.json`（条数/去重/异常）；
- 清洗后核验：`clean_verify.json`；
- 入库前核验：`verify_sample.json` + `verify_record`；
- 结论标：`已验证 / 判断 / 待核验`。

## 五、失败处理

| 现象 | 处理 |
|---|---|
| 文本层 0 字符 | 判扫描件 → OCR；不硬猜 |
| OCR ok 但 0 行 | 检查页图是否真实渲染；换 pypdfium2；放大后重试 |
| OCR 标签 0 命中 | 先做 CJK 空格归一化，再核关键词表 |
| 清洗后字符大幅缩水 | 查截断/编码/正则误删；`clean_verify` FAIL 则重清洗 |
| 清洗后乱码/截断 | 回退原文副本重抽，标 `issues`，不强行修语义 |
| 单位/口径混杂 | 逐条回指原文；无法判定标 `口径待核验` |
| 去重误杀/漏杀 | hash 后人工抽核；合并条目保留 `duplicate_of` |
| 核验 FAIL 但想入库 | **禁止**；修复重跑，宁可延迟 |
| 入库后才发现错误 | 按 id/hash 回滚该批，回退核验阶段，不"边入边改" |
| 抓取 403/反爬 | 降频/换官方接口；仍失败记 `_未取得`，不编造 |
| 大文件/超时 | 限页/分块样本先行；后台跑并留日志 |

## 六、边界

- 原始资料只读留底，只拷不删；
- 原文/OCR 文本/第三方内容**不入 Git、不进交付物、不对外转发**；
- 出库须 clean-room 加工 + 人工抽检签字，不得洗稿冒充自研；
- 不抓取需授权/付费墙/禁止抓取源；不伪造来源与 hash；密钥/隐私不落库。

## 七、快速开始

```bash
# 文本标签抽取 + 双门禁演示（合成样例，离线）
python skills/material-to-metakb/scripts/extract_tags.py \
  --text skills/material-to-metakb/examples/sample_exam_text.txt \
  --topics skills/material-to-metakb/examples/topics.json \
  --out /tmp/material-tags

# 离线测试
python -m pytest -q skills/material-to-metakb/tests
```

- OCR（可选）：`scripts/windows_ocr.ps1`（Windows.Media.Ocr，zh-Hans；MIT）；
- 未经授权的第三方内容不随本技能分发，请自备合法来源。
