# KDP 上架自动化（KDP Publishing Automation）

> 技能 ID：`kdp-publishing-automation`
> 来源：本机实战沉淀（2026-11-26，《輪迴殿》卷一上架实操）
> 适配：Windows + Edge + Playwright CDP；Amazon KDP 后台；中文/英文电子书

---

## 一、何时用

- 要把一本已完成的电子书（docx/EPUB + 封面）上架 Amazon KDP；
- 需要批量上架系列书（多卷），且不想每次手工填 20+ 个字段；
- 已经完成稿件/封面/元数据准备，只差平台操作；
- 需要**在用户已登录的浏览器里自动填表**（登录态无法代持）。

## 二、何时不要用

- **账号未登录**：登录（含 2SV 短信）必须用户本人完成，脚本不代持凭证；
- **每周标题限额已满**：KDP 限制每种格式每周新建/提交各 2 种，超限会弹 `Title creation limit reached`（重置：周日 00:00 UTC）；
- 稿件未过质量门（字数/段落体/引号）——先修再上；
- 需要**简体中文 Kindle**：KDP 只支持 `Chinese (Traditional) (Beta)`，简体走 Google Play；
- 涉及账号安全操作（改密码、改收款、删账户）——不经脚本。

## 三、流程

### 阶段 0：前置检查

```powershell
# 1) 启动可接管浏览器（默认 profile + CDP 9223）
$py = "C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
& $py scripts/kdp_launch_edge.py

# 2) 让用户在弹出的窗口里手动登录 KDP（邮箱 + 密码 + 短信验证码）
# 3) 验证登录态
& $py scripts/kdp_check_login.py     # 或用 kdp_status 类脚本
```

判定：页面在 `https://kdp.amazon.com/en_US/bookshelf` 且能看到「Create new title or series」= 已登录。

### 阶段 1：配置

复制 `scripts/kdp_config.template.json` 为 `.json`，填：

| 字段 | 说明 |
|---|---|
| `language` | 繁体用 `Chinese (Traditional) (Beta)` |
| `title` / `subtitle` / `series_title` / `series_number` | 书名体系 |
| `author_first_name` / `author_last_name` | 中文笔名：first 填全名，last 留空 |
| `description` | 简介全文（`\n` 分段） |
| `keywords` | 7 个（必须填满） |
| `categories` | 每个含 `l1` / `l2` / `leaf`（**必须到叶子节点**） |
| `manuscript` / `cover` | 绝对路径 |
| `pricing` | 价格、版税、Select、DRM |

### 阶段 2：跑详情页

```powershell
& $py scripts/kdp_upload_all.py
```

脚本做：Bookshelf → Create new title → Kindle eBook → 详情页 → 填全部字段 → 分类 → 截图。

### 阶段 3：内容页（人工或扩展脚本）

```
1. Save and Continue
2. 上传 manuscript（繁体只支持 doc/docx）
3. Launch Previewer：核对章数 / 缩进 / 引号 / 末页
4. 上传 cover（1600×2560 / RGB / JPG）
```

### 阶段 4：AI 问卷

```
AI-generated content? → Yes
Text → Entire work, with extensive editing
Images → None（封面人工）
Translations → None
Tool → DeepSeek / ChatGPT / Claude
```

### 阶段 5：定价与发布

```
Territories → All territories
Price → 2.99（70% 价带 2.99–12.99）
Royalty → 70%
KDP Select → 不参加（保留多平台）
DRM → 不启用
→ Publish
```

### 阶段 6：上架后

```
Bookshelf 变 Live → 复制商品页 /dp/ 后 ASIN → 记入销售台账
Reports → Sales Dashboard（延迟 24–48h）
Author Central 建系列页
```

## 四、证据（每步必须留）

- **截图**：详情页填写后、内容页预览器、定价页、发布确认页；
- **字段回读**：`page.input_value()` 打印书名/副标/作者，确认不是空；
- **分类回读**：`Your title's current categories` 文本，确认是预期路径；
- **状态记录**：提交时间、`In Review → Live` 时间、ASIN；
- 失败时保留**页面原文**（弹窗文案、错误提示），不要只写"失败了"。

## 五、失败处理

| 现象 | 根因 | 处理 |
|---|---|---|
| `select_option` 超时 | 语言下拉是自定义组件，原生 select 被覆盖 | 用 JS 设 `#data-language-native` value + dispatch change |
| 分类选了不生效 | 没选到**叶子节点** | 级联到叶子再勾 checkbox |
| 勾错叶子 | `Add another category` 后 select 索引变化 | 用 `selects.length - 2` 动态算 |
| `Title creation limit reached` | 每周每格式限 2 个新标题 | 等周日 00:00 UTC 重置，配置已保存可重跑 |
| PowerShell 内联多行 Python 报错 | 引号被 shell 吃掉 | 永远写 `.py` 文件再执行 |
| CDP 连接失败 | Edge 未开或已关 | 重跑 `kdp_launch_edge.py` |
| 登录态失效 | Cookie 过期 | 请用户重新登录（2SV 无法代做） |
| 封面上传被拒 | 尺寸/DPI/格式 | 1600×2560 / RGB / 300DPI / JPG / <50MB |

## 六、边界

- **登录与 2SV 不经脚本**：只操作已登录会话；
- **不代持凭证**：不读、不存、不填账号密码；
- **不绕过限额**：限额是平台规则，等重置；
- **不做破坏性操作**：不删书、不改收款、不动账号设置；
- **AI 披露如实填**：填 No 被查实是封号级风险；
- **预期不夸大**：繁中版在 Amazon 无独立中文类目，`$0–50/月` 是正常区间，不是失败。

## 七、脚本清单

| 脚本 | 用途 |
|---|---|
| `scripts/kdp_launch_edge.py` | 用默认 profile + CDP 9223 启动 Edge |
| `scripts/kdp_upload_all.py` | 详情页全字段自动填写（读配置） |
| `scripts/kdp_step_fill_basic.py` | 基础字段（语言/书名/副标/作者/关键词/版权/成人） |
| `scripts/kdp_step_fill_description.py` | CKEditor iframe 填简介 |
| `scripts/kdp_config.template.json` | 配置模板 |

## 八、平台硬限制（实测 2026-11）

| 限制 | 内容 |
|---|---|
| 中文语言 | **只有 `Chinese (Traditional) (Beta)`**，无简体 |
| 繁体文件格式 | **只支持 Microsoft Word (doc/docx)**，不能 EPUB |
| 繁体排版 | 只支持**横排** |
| 每周限额 | 每种格式每周新建/提交各 **2 种**，周日 00:00 UTC 重置 |
| 70% 价带 | **$2.99–$12.99**（2026-07-07 起） |
| 收款 | 大陆银行卡不支持，须 PSP（Payoneer 等）+ KYC |
| 税表 | 不填默认扣 30%；中国税收居民 10%（W-8BEN，中美协定第 11 条第 2 款） |

## 九、最小可复现命令

```powershell
$py = "C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"

# 1. 起浏览器（用户随后手动登录）
& $py scripts/kdp_launch_edge.py

# 2. 用户登录后，跑详情页
& $py scripts/kdp_upload_all.py

# 3. 看截图确认
explorer "D:\tools\kdp_shots"
```
