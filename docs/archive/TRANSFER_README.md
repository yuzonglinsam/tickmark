# 换电脑后从这里开始

这是 AI Credit Research Workbench 的源码交接包，日期 2026-10-11。解压后直接在项目文件夹启动 Claude Code，先完整读取 `CLAUDE.md`、`AGENTS.md`、`HANDOVER_CLAUDE.md`、`HANDOFF.md`、`README.md` 和 `docs/OPEN_SOURCE_AUDIT.md`，按确定的方案继续实际开发。

**本包带项目源码、Git 历史、交接文件、测试、现有报告示例和选定上游参考源码。** 新的深色 UI、披露比较和估值页面仍待实现；已有 FinRobot 移植代码是未集成草稿。不要把携带的历史 PDF 当成应用的实时数据。

## 路径、环境与凭证

旧文档中的 `/Users/yuzonglin/...` 是原电脑路径，执行命令时以当前解压目录为准。旧文档提到 `.env`、`.venv311` 和本机缓存已配置，指的是原电脑的检查点；这些不随 ZIP 转移。所有密钥需要在新电脑重新配置，不能把旧“配置存在”的记录当成当前状态。

Claude Code 可以自主安装 Python 3.11 和依赖，创建虚拟环境；首次真实 SEC/DeepSeek 请求前检查网络及服务器配置。无密钥时先做源码移植、UI 和离线验证，不要求重新讨论 PRD。macOS/Linux 的启动示例：

```bash
python3.11 -m venv .venv311
.venv311/bin/python -m pip install -r requirements.txt
.venv311/bin/python -m pip install --no-deps -e .
cp .env.example .env
# 在本机编辑 .env，配置 SEC_USER_AGENT 和 DEEPSEEK_API_KEY。
.venv311/bin/python -m unittest discover -s tests -q
.venv311/bin/python -m streamlit run app.py
```

Windows 使用 `py -3.11 -m venv .venv311` 和 `.venv311\Scripts\python.exe`；复制 `.env.example` 到 `.env`。不要将密钥发入聊天。ZIP 不包含 `.env`、Streamlit secrets、虚拟环境、运行中的 SQLite 或原始 SEC/AI 缓存；新环境必须重新取得真实数据。已配置 DeepSeek 型号是原检查点的记录，接手时核查实际可用配置。

## Git 与参考源码

ZIP 中的 `.git` 是从本地已提交分支复制出的独立 checkout，保留项目提交历史，去除 origin 及本机钩子/日志；不是原电脑的完整 `.git` 目录拷贝。可执行 `git status`、`git log` 后继续本地提交。GitHub 同步仍需用户明确授权。

`artifacts/transfer/upstream/` 包含方案相关的原始源码选集、许可证和 `UPSTREAM.json`（仓库、固定 commit、文件哈希）。它们不是完整可运行的上游仓库，也不是已接入的产品功能。这里的文件仅用于继续移植、比对与保留归属；如需更多模块，应按固定 commit 获取完整仓库。原始 `.cache/references/` 不随包迁移。

`artifacts/transfer/PACKAGE_MANIFEST.json` 列明本包项目 commit、源码选集与文件 SHA-256。`artifacts/transfer/upstream/` 属于 Git 忽略的交接资料；正式移植后将所选源码和许可证放入项目 vendor，并更新归属记录。不要把参考库携带的数据样本当作 live SEC 成果。

## 发给 Claude Code 的话

> 在当前解压后的项目目录继续开发。先读取 TRANSFER_README.md 与 CLAUDE.md，再完整阅读它们指定的交接文件。按 HANDOVER_CLAUDE.md 实际完成源码移植、深色 UI、披露比较、交互模型与报告体验，保留已验证财务合同。旧机器路径和“已有密钥”记录不适用于这台电脑；自主重建 Python 环境，必要时再找我配置密钥/账户。先展示真实可操作的本地成果，再推进公开部署；GitHub 同步前请求我授权。
