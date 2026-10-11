# Tickmark 接手验收 · 2026-10-11

**结论：Needs revision。界面和功能展示有明显价值，但金融结论与“已验证”承诺尚不能完全兑现。**

审查基线为 `806ddc1`，不是只按 README 评价。完整阅读了 AGENTS、Claude 交接、README 和相关计算代码；安装依赖、执行工程门槛、扫描全部发行人文件，实际访问 SEC、DeepSeek 和网页。此次只修改问答滚动 effect 的返回行为，另按用户要求配置本机 `.env`；没有重做视觉、调整金融定义或批量重生成 Memo。

## 已确认能工作的部分

- Python 66 项测试通过；TypeScript、ESLint、Next 生产构建通过，生成 507 个页面。
- 497 家独立 CIK、37,170 条来源记录、474 份双语 Memo，与交接数量一致。
- 所检查的财务事实及指标来源 ID 均能解析到来源表；双语 Memo 的 7,584 条陈述均不含阿拉伯数字，已保存的 passage ID 均可解析。
- 名单外的 SHAK 实时 SEC 分析成功，返回 `live: true`；不是预设 ticker 演示。
- 真实 DeepSeek KO 问答成功；SHAK 实时英文及繁体中文 Memo 各生成 8 条陈述。
- 网页的衰退 preset 能使 KO 的风险分档从 Significant 变为 Aggressive；繁中切换、来源抽屉可操作。
- 实际下载 shadcn button 源码后进行比对，本地与上游文本高度一致；这部分确有源码移植。金融模块不能因此宣称移植了 FinRobot 或 FinanceToolkit。

注意：ID 能解析只证明来源存在，不证明文字结论正确、数据范围完整或所有数据均逐项与财报复核。此处是本地验证，没有公开部署或 GitHub CI 运行证明。

## 必须修复的信用与可信度问题

### P1 · 问答的“verified”会给错误陈述背书

`api/index.py:203` 的校验只在全公司、全期间数值池中查找近似数值，忽略币种、正负号和陈述对应的指标。

直接使用 KO 真实文件，下面三句都得到 `verified: true`：

- `FY2025 debt was CNY 45.492bn.`（公司报表币种为 USD）
- `FY2025 debt was USD -45.492bn.`（真实为正数）
- `FY2025 revenue was USD 45.492bn.`（匹配到的其实是 debt）

真实问答还将 CFO/debt 的 `0.16x` 匹配到了 `sector median om`，并把可从上下文推导的分派合计以及债务附注中存在的信贷额度标为未验证。这会同时出现误报和漏报。

**修复要求：**让回答携带结构化 metric、period、currency、unit、value 和证据引用；代码按明确绑定校验，再渲染文字。数值存在校验不能宣称整句事实已验证。

### P1 · 缺失股息或回购被当成零

`engine/credit_workbench/export.py:141` 使用 `or 0`。全部发行人的主年度中，122 家发布了该指标，但股息或回购至少有一项未提供数值。

例如 ACN 的 dividends 是 `null`，buybacks 是 4,619,497,000，仍发布 Shareholder returns / FCF 为 42.48%。其中一些公司可能实际上没有股息；当前数据并没有提供“已确认零”的证据，因此不能用缺失标签代替零。

另有 332 家有股东回报率，却未在该指标的证据中保留股息、回购输入来源；前端 `METRIC_INPUTS` 也遗漏这两个输入。Debt/capital 及 revenue growth 存在相似的证据输入不全问题。

**修复要求：**未知组合为 N/A，已证实零才为零；所有分子、分母及跨期输入保留证据。

### P1 · KO 的债务范围不完整，却被标为 full

网页 FY2025 债务为 USD 45.492bn。其 [2025 10-K](https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/ko-20251231.htm) Note 2 另披露待售业务的当期长期借款 USD 398m 和非流动长期借款 USD 850m。Note 11 明确说明该部分已重分类进待售负债。当前来源组件未包含这两项，却给出 `debt_scope.completeness = full`。

本次确认漏掉这两项合计 USD 1.248bn；不据此宣称其他借款均已完整核对。源 HTML 和自定义 XBRL 标签摘录已保存。

全部样本另有 127 家同时标为 full 并有 not_tagged 项。这不是 127 家债务数值都错误的证据，但说明 full 只表示选中的标签块含 current 部分，不能表示完整债务范围已完成对账。

**修复要求：**恢复财报层自定义标签及债务附注对账；区分“标准标签覆盖”与“已对账完整”。

### P1 · 无数字 Memo 仍会产生错误金融结论

KO 已保存 Memo 的两条具体反例：

- 说营运现金流覆盖资本开支及股息。实际 CFO 为 USD 7.408bn，capex 加股息为 USD 10.891bn，不能覆盖。
- 说净杠杆低于行业中位数。页面对应值为 2.38x，中位数为 2.30x，方向相反。

英文与繁中都有这些错误。引用可解析、文字没有数字，仍然不能防止比较方向和现金流结论错误。

**修复要求：**把覆盖关系、同业比较方向等事实判断交给代码；模型解释这些判断，校验报告文本是否矛盾。先修验收 Demo 的公司，再考虑批量重生成；批量操作仍须用户批准。

### P2 · 前后端并未使用相同的压力规则

前端 `lib/issuer.ts:92` 对 EBITDA 施加冲击，Python `stress.py:10` 对 EBIT 施加冲击并保持 D&A 固定，且 Python 不支持前端的债务冲击。

KO FY2025 同样输入 -20%：实际前端函数输出 EBITDA USD 11.8496bn，Python 输出 USD 12.0596bn，相差 USD 210m。不能声称两者相同。两种情景定义各自可以有用途，必须明确选定并统一接口。

### P2 · 财务代理值的命名和可比较性

主年度中 64 家使用 cash interest paid 代替 interest expense；51 家使用 pretax income + interest 代替 operating income；16 家 D&A 只有 depreciation。

底层 note 有披露，主界面仍使用通用 EBIT、EBITDA、interest 标签，同业比较及分档会混合不同口径。Cash paid 不等于权责发生制费用，pretax 推导包含非经营项目。

**修复要求：**保留代理能力但显式携带口径及质量状态；严格口径指标和代理指标分开，不能凭披露小字认定完全可比。

## 现场发现并已作最小修复的问题

在本次 Codex 浏览器环境点击 Ask preset，React 提示 effect 返回 Promise，随后报 `destroy is not a function`，页面崩溃。

`components/issuer/ask-panel.tsx` 改为 block-bodied effect，调用滚动方法但不返回其结果。没有改视觉。必须验证问答完成、抽屉关闭与再次打开；1440×900 和 390×844 前后截图保存在本机审计目录。浏览器滚动方法的具体返回行为可能因环境不同；这是本次环境的可复现缺陷，不声称所有浏览器都会崩溃。

## 交付和运行的剩余限制

- 没有公开部署证明。Vercel 函数、重写及超时约束尚未在真实部署中验收。
- 当前网页没有 PDF 导出入口；只有 Memo Markdown copy。旧 Python PDF 模块存在不等于新产品已接入。
- GitHub 链接当前指向 github.com 根页面，仓库没有 remote；推送仍需用户明确授权。
- 实时缓存和额度计数在进程内，跨进程、服务器重启、serverless 扩容不共享；不能宣称持久缓存或可靠全局限额。
- THIRD_PARTY 有源码来源说明，但仓库只存在项目自己的 LICENSE，没有保留所复制源码对应的上游完整许可文本及版权声明。发布前补齐。
- Memo fingerprint 仅包含年度 filing 和核心 facts，不含同业、扩展现金流指标、风险方法及提示词版本。本次 fingerprint 均匹配，不能因此证明这些其他上下文变化已触发重生成。

## 推荐顺序

1. 先修 verified 绑定、缺失值与证据输入、债务对账及 Memo 事实一致性。
2. 统一压力接口及代理指标质量状态，增加能击中上述实际缺陷的测试。
3. 保留当前视觉，接回 PDF，补许可文件，打磨 KO/其他代表公司演示。
4. 最后再部署并验收真实站点。不要继续增加 DCF 或新 Agent 来掩盖核心错误。

这已经具有专业展示基础；决定能否成为强简历项目的下一步是可靠性。若面试官只看首页，容易留下好印象；若现场追问当前数据范围及 AI 校验，现版本会露出上述问题。

## 本机复现材料

忽略目录 `artifacts/codex-audit/` 中有 `audit.py`、`audit.json`、`scenario-audit.cjs`、`scenario-js.json`、实时 SHAK 与 KO API 返回、财报 HTML、自定义标签摘录和截图。分析不使用生产 Mock 数据。涉及错误文字的探针只是校验器反例，不是产品输出。

```bash
.venv/bin/python artifacts/codex-audit/audit.py
node artifacts/codex-audit/scenario-audit.cjs
```

环境配置在本机忽略的 `.env`；密钥不进入报告、截图或 Git。
