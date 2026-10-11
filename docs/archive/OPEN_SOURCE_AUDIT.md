# 开源源码审查与改造建议

审查日期：2026-10-11。用户要求先扩大搜索、审查源码，再说明改造方案。
本文是选型和源码审查记录，不是新的 PRD，也不是已完成功能清单。

## 现有工程审计

基线提交：`55a8d48`，分支 `codex/sec-streamlit-workbench`。
开始审查时工作区干净；54 项本地测试通过。

| 项目 | 查证结果 | 决策 |
|---|---|---|
| SEC 数据、FY/季度/TTM、来源追溯 | 已有真实 KO、TXN、TSM 验收记录；代码保留缺失值和币种 | 保留 |
| 信用指标、评分、压力测试 | 有确定性计算及口径测试；评分是未校准启发式 | 保留核心，改展示 |
| DeepSeek Memo、PDF、SQLite | 已有真实调用及 PDF 验收；部分输出需要人工编辑 | 保留，改善报告阅读器 |
| 原界面 | 浅色默认表单、指标卡和标签页，缺少研究终端的布局层级 | 替换呈现层 |
| 第三方源码复用 | 基线没有移植参考应用源码；EdgarTools 等属于实际使用的库依赖 | 新增可定位的源码移植 |
| 数据覆盖 | 部分发行人的 D&A、gross interest、完整债务范围仍为 N/A | 保留缺失提示，继续按发行人核对 |
| 公开部署、GitHub CI、托管持久缓存 | 尚未验收；GitHub 无 remote，未获推送授权 | 保持 pending |

## 扩大后的候选库

筛查覆盖金融研究应用、披露分析、金融计算和 Streamlit 组件，初轮 16 个候选。
交接时补查已公开的 OpenBB Workspace 源码、NOTICE 与实际设计变量，合计 17 个。
6 个仓库已下载并检查相关核心源码；其他项目检查了仓库目录、许可证及部分源码或运行文档。
没有将 README 的功能宣称、stars 或截图当作本机运行验收；这不是穷尽整个 GitHub 的声明。

| 项目 | 实际可移植内容 | 许可证检查 | 本轮取舍 |
|---|---|---|---|
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) | `finrobot_desktop/finrobot/engine/compute/operators/dcf.py`；`desktop/src/App.css` 的设计变量 | Apache-2.0，另有 NOTICE、商标政策；已下载检查 | 首选：FCFF DCF、二维敏感性、深色设计基础 |
| [OpenBB Workspace](https://github.com/OpenBB-finance/workspace) | `terminalpro/src/styles/tokens.css`：surface、表格、输入、按钮与状态的语义变量 | 公开 archive；实际 LICENSE/NOTICE 已查，Apache-2.0；NOTICE 排除专有 TradingView Advanced Charts | 新增 UI 候选；固定 `be00e95019a55d57af146919ee46b7e1a4859226`，已读源码但未复制/运行。可移植变量，不整库改变 Streamlit 架构 |
| [Disclosure Alpha](https://github.com/alwank/disclosure-alpha) | `section_extractor.py`、`text_matching.py`、`diff_engine.py`：章节抽取、句子对齐、披露变化证据 | 实际 LICENSE 为 Apache-2.0；GitHub API 为 NOASSERTION；已下载检查 | 首选新增候选：年度 10-K 风险披露比较，先做可读证据，不照搬风险分数 |
| [streamlit-option-menu](https://github.com/victoryhb/streamlit-option-menu) | Python 包装器、`frontend/src/MyComponent.vue`；真实菜单点击经 Streamlit bridge 回传 | MIT；已读取实际包装器和 Vue 源码 | 首选导航候选；需先验证当前 Streamlit 版本及资源打包 |
| [streamlit-extras](https://github.com/arnaudmiribel/streamlit-extras) | `src/streamlit_extras/metric_cards/__init__.py`：可配置指标卡样式 | Apache-2.0；已下载检查 | 首选小组件候选；只移植所需 helper，去掉 playground/额外注册机制 |
| [Equity Research Lab](https://github.com/mariasfondrini/equity-research-lab) | `valuation/dcf.py`、`sensitivity.py`、`comparables.py`；Streamlit 分页与报告图表 | MIT；已下载检查 | 备用：增长×利润率敏感性和财务研究图表；暂不接入整个 Yahoo/SEC 管线 |
| [FinanceToolkit](https://github.com/JerBouma/FinanceToolkit) | `models/intrinsic_model.py`、WACC、财务比率与分析模块 | MIT（LICENSE.txt）；已下载检查 | 备用金融计算库；现金流的经济含义必须由适配层确定 |
| [Sellside Research Engine](https://github.com/DogInfantry/sellside-research-engine) | `trg_workbench/analytics/valuation.py` 的 DCF、reverse DCF；静态金融 dashboard | 实际 LICENSE 为 Apache-2.0；已下载检查 | 不直接移植该 DCF：源码将 CFO−Capex 用于 WACC 估值、默认净债务为零、股数为一，并自动下调不合法的终值增长率；这些口径需要修正 |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | `agents/researchers/bear_researcher.py` 等 bull/bear/judge 节点与辩论流程 | Apache-2.0；实际读取 bear 节点 | 后续候选：真实信用委员会；当前流程偏交易，需要改成信用证据约束并衡量调用成本 |
| [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund) | 当前目录下的 `hedge_fund` 交易研究/回测应用，README 支持 DeepSeek | MIT；许可证、目录、当前运行文档已查 | 后续候选；依赖 Financial Datasets，偏纸面交易/回测，不为首轮信用应用引入新数据账户 |
| [LangAlpha](https://github.com/ginlix-ai/LangAlpha) | React 研究 workspace、交付物技能、研究工具和 agent harness | Apache-2.0；许可证、目录、运行文档已查 | UI/研究工作流候选；整套依赖 Docker、Postgres、Redis、后台和前端，不整库搬入单个 Streamlit 应用 |
| [Dexter](https://github.com/virattt/dexter) | 自主金融研究循环、DCF 技能、工具调用 | README 宣称 MIT；当前树未找到独立许可证文件，API license 为空 | 许可证归属确认前不复制；Bun/TypeScript 与新数据账户也增加接入成本 |
| [Equity Research Agent](https://github.com/palak22291/equity-research-agent) | `app/calculators/dcf.py` 的 FCFF/FCFE 分离、敏感性；ADK 研究流程 | MIT；实际读取 DCFCalculator | 备用计算器；有可用数学实现，但与已选 DCF 重复，整套 ADK/Yahoo 不优先 |
| [Financial Research Analyst Agent](https://github.com/gsaini/financial-research-analyst-agent) | `src/tools/dcf_model.py`、Streamlit 与 HTML dashboard、多研究工具 | 实际 LICENSE 为 MIT；实际读取 DCF 模块 | 不直接采用数据适配：`_safe_float`/getter 对缺失返回零，首列取值也不满足本项目财务合同 |
| [streamlit-elements](https://github.com/okld/streamlit-elements) | `frontend/components/modules/dashboard/Grid.tsx`：Material UI、可拖拽网格、Nivo 图表 | MIT；实际读取 Grid 源码 | 可复制；首轮不引入可拖拽布局和 React iframe 的额外状态管理，标准导航和图表更适合演示 |
| [QuantLib](https://github.com/lballabio/QuantLib) | 债券、曲线、信用衍生品及利率风险计算 | 实际 LICENSE.TXT 为允许再分发的 BSD 风格条款 | 合法的固定收益候选；当前缺具体债券条款和市场曲线，接入后容易只演示计算而无真实市场输入 |
| [FinancePy](https://github.com/domokane/FinancePy) | 债券、信用/利率衍生品、现金流与风险计算 | GPL-3.0 | 可在遵守 GPL 的条件下复用；首轮没有足够理由改变现有 MIT/Apache 代码的交付许可安排 |

注意：`streamlit/streamlit-extras` 在本次查询中跳转至另一个 pivot-table 仓库。
已改用实际作者仓库 `arnaudmiribel/streamlit-extras`，没有把跳转后的仓库当作 Metric Cards 的来源。
Quartr、Fiscal.ai 的商业界面可供视觉研究，不作为可复制源码。

OpenBB 的数据平台与 Workspace 是不同代码库，但 Workspace 已公开，不能继续将其一律视为闭源。
2026-10-11 已实际读取公开源码的根 LICENSE、NOTICE、`terminalpro/src/styles/tokens.css` 和组件文档。
根 Apache 许可不覆盖 NOTICE 排除的专有组件；其他组件的依赖仍须逐项检查。
[源码与边界](https://github.com/OpenBB-finance/workspace)、[FINOS 许可证检查记录](https://github.com/finos/community/issues/445)。

## 推荐的改造结果

### 1. 专业研究工作台

深色侧边导航 + 公司搜索 + 发行人身份/期间/币种 + 来源新鲜度 + 真正执行过的研究步骤。
入口为 Mission Control、Valuation Lab、Scenario Lab、Filing Intelligence、Report Studio。
无需登录的访客流程保留；名称只是导航组织，不假装已有多 Agent。

移植 FinRobot 的设计变量，以及经兼容性验证的 option-menu / Metric Cards 代码。
复用实际组件后做品牌、间距、图表主题、缺失状态和报告排版。

### 2. Valuation / Sensitivity Lab

直接移植 FinRobot 的 `calculate_dcf`、`calculate_sensitivity`、`_project_full`、`_terminal_fcf`。
从真实 SEC Snapshot 接入 Revenue、Operating EBIT、D&A、Capex；保留所有原始来源。
税率、WACC、增长、ΔNWC 和终值营运资本投入属于明确可编辑的分析假设。

显示五年 FCFF、现金流桥、WACC×终值增长敏感性、终值占 EV 比例。
只在完整债务数据支持时显示模型 EV/债务比较；该比较不表示法律清偿顺序、回收率或 LGD。
暂不输出每股目标价：当前还没有验证股数、ADR 比例与市场价格管线。
原 CFO−Capex 信用指标保留独立含义，不作为 FCFF 偷换使用。

### 3. Filing Intelligence

移植 Disclosure Alpha 的完整章节抽取与句子对齐相关实现，比较相邻年度的真实 10-K Risk Factors / MD&A。
显示新增/删除/改写的句子、数字 token 变化、两份 SEC 文件和完整章节的抽取状态。
数值变化只是文本检索提示，需要结合上下文核查；不自动宣称新增违约风险或更高违约概率。
首轮先验收国内 10-K；20-F/40-F 仍可进行现有财务研究，章节比较需另行验证才开放。
当前供 Memo 使用的 3,200 字符节选不能当作完整章节同比比较，必须接入完整章节抽取。

### 4. Report Studio 和现有压力测试

改善现有真实 DeepSeek 报告的阅读器：财务底稿、引用展开、来源跳转、模型状态和 PDF 下载。
每一步展示实际完成、等待或失败，生成与编辑审核区分开；不虚构多个 Agent 在工作。
压力测试保留既有口径，增加图形化前后变化和与底稿的联动；拖动不调用 AI。

## 当前移植草稿状态

在用户要求先给方案之前，已根据上一条开发授权生成以下草稿：

- `credit_workbench/vendor/finrobot/dcf.py`：四个选定函数；两个内核与上游逐字一致，其余改为明确 WACC、EV 输出。
- `credit_workbench/vendor/finrobot/tokens.css`：选定的原始设计变量。
- `credit_workbench/vendor/finrobot/{LICENSE,NOTICE,TRADEMARK_POLICY.md,provenance.json}`：归属、commit、原文件 SHA-256、原始行号和改动说明。
- `credit_workbench/valuation.py`：本项目 Snapshot/假设适配层，未改变原财务标准化、评分或 stress 合同。

固定上游 commit：`2717499b8e30f242640af08c4ad9afd1113c2d45`。
独立预运行使用此前验收的 KO FY2025 SEC Snapshot：模型可运行，敏感性中心与主模型一致。
该检查不是新的一次 live SEC 请求，也不是 Streamlit 集成验收。
草稿尚未接入 `app.py`，现有 UI 未改；本次交接 checkpoint 仅保存草稿和说明，不是功能发布。

## 交接时确定的范围与竞争判断

实施方案、12 维度检验、准确顺序与完成门槛已写入根目录 `HANDOVER_CLAUDE.md`，供 Claude Code 接手。
优先交付完整信用研究链：深色工作台、年度披露变化、交互式 stress/FCFF 与引用报告。
DCF、来源引用与叙事变化在成熟产品中已有实现，本项目不能因添加它们就宣称市场领先。
面试价值取决于金融口径、可靠集成、可追溯性、界面完成度与实际交付。
[Fiscal.ai 官方能力](https://docs.fiscal.ai/docs/guides/mcp-skills)、[Quartr Pro](https://quartr.com/products/quartr-pro)。

## 为什么值得在面试里展示

演示应展示一条可追问的研究链：真实年报 → 可核对的财务底稿 → 假设驱动模型 → 披露变化证据 → 引用报告。
面试官可以现场改 WACC 或利润率、打开一条变化对应的年报、追问 FCFF 与信用 FCF 的区别。
这同时提供金融判断、数值可靠性、第三方代码集成、产品交互和工程交付的讨论空间。

“令人印象深刻”是交付目标，不是目前完成声明。第一轮验收必须展示实际操作的深色界面、真实双年报比较、
独立核算的模型结果、可定位的源码复用记录，随后才安排公开部署和 GitHub 同步授权。
