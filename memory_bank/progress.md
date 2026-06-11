# 会话进度日志

> 🔥 HOT 知识 — 记录每次 Agent 会话的摘要。每次对话开始时读取，了解项目历史。

---

## 会话记录

### 2026-06-11 - Project Brief 批判性审查

**完成事项**:
- [x] 阅读 `memory_bank/project-brief.md` 及 HOT memory bank 文档。
- [x] 从产品定位、MVP 范围、数据模型、AI 评审机制和验证路径角度审查 Sycamore 构想。

**踩坑记录**:
- memory bank 规则中写的是 `memory-bank/`，实际目录是 `memory_bank/`。
- `progress.md` 不存在，仅有 `progress.template.md`，本次按模板创建进度日志。

**遗留问题**:
- [ ] `project-brief.md` 后半部分仍有技术栈、MVP、成功指标、风险约束等模板占位。
- [ ] `architecture.md` 和 `data-contracts.md` 仍未沉淀实际架构与数据契约。

**下一步建议**:
- 先把 MVP 压缩为可在 1-2 周内验证的 CLI 闭环，再决定是否引入 Web、API 服务和复杂资产管理。

### 2026-06-11 - 产品初衷澄清

**完成事项**:
- [x] 明确 Sycamore 的核心动机：为跨领域学习过程提供能力锚点，而不是构建纯查询型知识库。
- [x] 明确产品张力：大脑保留高层抽象和能力判断，工具承载低频细节、实操速查与自我评审记录。

**踩坑记录**:
- 如果把所有内容都做成可检索资料库，项目会退化为轻量 Obsidian，而不是能力成长工具。
- 如果过度强调记忆和掌握，又会违背“外置大脑”的初衷，造成新的焦虑。

**遗留问题**:
- [ ] 需要把“能力锚点”“抽象理解”“低频细节外包”转化为具体节点模型和交互流程。
- [ ] 需要重新命名 AI 评审状态，避免 `已验证` 暗示 LLM 能担保事实正确。

**下一步建议**:
- 将第一版产品定义为“能力恢复与校准工具”，围绕 `Mental Model`、`Cheatsheet`、`Practice Log` 和 `Review` 四个核心区块设计 MVP。

### 2026-06-11 - 新知识学习机制讨论

**完成事项**:
- [x] 从第一性原理角度梳理 Sycamore 面对新知识时应支持的学习循环。
- [x] 明确系统应帮助用户完成能力假设、心智模型编码、细节外包、实操验证、LLM 评审和恢复演练。

**踩坑记录**:
- 学习辅助系统如果直接给答案，会削弱用户本身的抽象建模能力。
- 新知识不应以“主题”入库，而应转化为可验证的能力断言。

**遗留问题**:
- [ ] 需要把学习循环进一步转化为 CLI 命令和节点模板字段。

**下一步建议**:
- 设计 `syca learn` 或 `syca add` 的交互式流程，引导用户先定义能力目标，再填写 Mental Model、Cheatsheet 和 Practice Log。

### 2026-06-11 - Memory Bank 文档基线重写

**完成事项**:
- [x] 重写 `project-brief.md`，将 Sycamore 明确定位为“能力校准与恢复工具”。
- [x] 补齐 `architecture.md`，确立 CLI-first、local-first、library-before-service 的 MVP 架构。
- [x] 补齐 `data-contracts.md`，定义 AbilityNode、AbilityEdge、ReviewReport、Asset、SQLite 表草案、Markdown 节点格式和 CLI 契约。
- [x] 重写 `conventions.md`，替换通用模板为 Sycamore 专用工程、文档、数据和 LLM 评审规范。
- [x] 创建 `changelog.md`、`decisions.md`、`known-issues.md`、`glossary.md`，并删除已转化的 `.template.md` 文件。
- [x] 更新 `manuals/testing-guide.md` 和 `manuals/deploy.md`，移除前端/后端通用占位，改为 CLI 本地工具的测试与发布指南。
- [x] 更新 `active-task.md`，把下一步焦点转向 MVP 代码骨架。

**踩坑记录**:
- 原始模板中包含 Vue/FastAPI 等通用占位，若保留会误导后续实现方向。
- `verified`/“已验证”这类评审状态容易把 LLM 反馈误解为事实认证，已统一改为 `challenged`、`needs_revision`、`accepted_by_user` 等状态。

**遗留问题**:
- [ ] 尚未初始化 Python 项目骨架。
- [ ] 尚未实现 CLI、SQLite schema、Markdown 模板和 LLM review mock。
- [ ] `.cursor/rules/memory-bank-protocol.mdc` 仍写作 `memory-bank/`，与实际 `memory_bank/` 不一致。

**下一步建议**:
- 按 `active-task.md` 初始化 Python CLI 项目，先实现 AbilityNode 模型、Markdown 模板生成和 `syca add/list/show/query --cheat`。

### 2026-06-11 - Project Brief 设计校准问题

**完成事项**:
- [x] 批判性审查 `project-brief.md` 中的能力断言、连线理由、能力等级、双存储一致性和 LLM Review 持久化设计。
- [x] 明确当前设计需要从“强制高质量录入”调整为“低摩擦捕获 -> 渐进式升格”的产品机制。

**踩坑记录**:
- 如果 `add` 强制填写能力断言、Mental Model 和 Practice Log，真实编码场景下会造成录入瘫痪。
- 如果 SQLite 和 Markdown 同时保存同一可变字段且没有字段所有权，会出现 split-brain。

**遗留问题**:
- [ ] 需要在 `project-brief.md` 中补充 Inbox/Capture、渐进式承诺、能力新鲜度、字段所有权和 ReviewRun 设计。
- [ ] 需要在 `data-contracts.md` 中新增 CaptureItem、CapabilityEvent、ReviewRun 等实体或表结构草案。

**下一步建议**:
- 将 MVP P0 调整为：快速捕获、Markdown/SQLite 同步、Cheatsheet 查询、基础节点升格；LLM Review 和能力图可后移为 P1。

### 2026-06-11 - Capture-first Roadmap 设计

**完成事项**:
- [x] 更新 `project-brief.md`，将产品主循环调整为 `Capture -> Clarify -> Encode -> Challenge -> Practice -> Recover`。
- [x] 新增 `roadmap.md`，明确稳健技术栈、阶段路线、退出标准和风险门控。
- [x] 更新 `data-contracts.md`，加入 `CaptureItem`、`CapabilityEvent`、`ReviewRun`、字段所有权和新的 CLI 契约。
- [x] 更新 `architecture.md`，对齐 Capture-first、Local-first、Library-before-service 和 Markdown/SQLite 一致性策略。
- [x] 更新 `active-task.md`，将下一步开发任务改为 `init/capture/inbox/promote/query/sync/doctor`。
- [x] 更新 `glossary.md` 和 `changelog.md`，记录新术语和未发布变更。
- [x] 更新 `decisions.md`，追加 Capture-first 和轻量本地 CLI 技术栈 ADR。

**踩坑记录**:
- `project-brief.md` 一旦引入新实体，必须同步 `data-contracts.md` 和 `architecture.md`，否则 HOT 文档会互相冲突。
- 技术栈必须服务 P0 的可靠捕获和同步，不应提前引入 ORM、Web、RAG 或常驻服务。

**遗留问题**:
- [ ] 尚未初始化 Python 项目骨架。
- [ ] 尚未实现 SQLite schema、Markdown 模板、sync/doctor 和 CLI 命令。

**下一步建议**:
- 进入 P0.1 项目骨架开发：初始化 `pyproject.toml`、uv、pytest、基础包结构和最小 `syca` CLI。

### 2026-06-11 - 阶段 0 通过与 P0.1 骨架

**完成事项**:
- [x] 完成阶段 0 文档和契约一致性核查，未发现需要用户额外确认的设计分歧。
- [x] 修正 `roadmap.md` 阶段 0 勾选状态，并统一 `capture_promoted` 事件命名。
- [x] 同步 `AGENT_RULES.md` 与 `.cursor/rules/memory-bank-protocol.mdc` 的 `memory_bank/` 路径。
- [x] 将根 `README.md` 从模板库说明改为 Sycamore 项目说明。
- [x] 初始化 P0.1 Python 项目骨架：`pyproject.toml`、`.python-version`、`sycamore/` 包结构、最小 `syca` CLI、基础 pytest。
- [x] 使用 uv 创建 Python 3.12.12 虚拟环境并生成依赖锁。
- [x] 通过 `uv run syca version`、`uv run syca --help`、`uv run pytest`、`uv run ruff check .` 冒烟验证。

**踩坑记录**:
- 系统默认 `python` 是 3.11.9，但 uv 已安装 CPython 3.12.12；通过 `.python-version` 固定项目使用 3.12。
- Typer 在 `no_args_is_help=True` 下根级 `--version` 会被缺少命令拦截，因此 P0.1 改为显式 `syca version` 命令。

**遗留问题**:
- [ ] `init/capture/inbox/promote/query/sync/doctor` 目前只有命令入口，业务逻辑尚未实现。
- [ ] P0.2 需要实现 `SYCA_HOME`、`config.toml` 和 SQLite schema 初始化。
- [ ] P0.6 后续需要在真实数据目录逻辑出现后补充 `tmp_path` 隔离测试。

**下一步建议**:
- 进入 P0.2 本地数据目录：实现 `syca init`、`SYCA_HOME` 解析、默认目录创建、`config.toml` 和 SQLite schema 初始化。

### 2026-06-11 - P0.2/P0.3 init 与 capture 闭环

**完成事项**:
- [x] 完成 P0.2：`syca init`、`SYCA_HOME` 路径解析、`config.toml` 写入、SQLite schema 初始化（幂等）。
- [x] 完成 P0.3：`CaptureItem` 模型、`syca capture --note/--cheat/--link`、`syca inbox`、`capture_created` 事件。
- [x] 新增 `tests/test_init.py`、`tests/test_init_cli.py`、`tests/test_capture.py`，13 项测试全部通过。
- [x] 版本号升至 `0.3.0`。

**踩坑记录**:
- Rich 表格列宽会截断 inbox 内容预览，CLI 测试断言需避免依赖长字符串完整显示。
- Rich 控制台输出会把长路径折行，init CLI 测试不宜用完整路径字符串匹配。

**遗留问题**:
- [ ] P0.4 `promote`、Markdown 节点模板和 `capture_promoted` 事件尚未实现。
- [ ] P0.5 `query --cheat`、`sync`、`doctor` 尚未实现。

**下一步建议**:
- 进入 P0.4：实现 `AbilityNode` 模型、Markdown 模板生成和 `syca promote <capture-id>`。

### 2026-06-11 - P0.4 promote 升格闭环

**完成事项**:
- [x] 完成 P0.4：`AbilityNode` 模型、`Markdown` 模板、`syca promote`、 `capture_promoted` 事件。
- [x] 按捕获类型（note/cheat/link）种子化 Capability、Cheatsheet、References 区块。
- [x] 支持 `--title`、`--domain`、`--claimed-level`；未指定 title 时从捕获内容推导。
- [x] slug 冲突自动追加后缀；纯中文标题回退为 `node-<uuid-prefix>`。
- [x] DB 失败时回滚并删除已写 Markdown，避免孤儿索引。
- [x] 新增 `tests/test_promote.py`，19 项测试全部通过。
- [x] 版本号升至 `0.4.0`。

**踩坑记录**:
- 中文标题 slugify 后可能为空，需用 UUID 前缀兜底。
- front matter hash 必须从最终渲染文本切分计算，不能与 body 分开估算。

**遗留问题**:
- [ ] P0.5 `query --cheat`、`sync`、`doctor` 尚未实现。

**下一步建议**:
- 进入 P0.5：固定 Markdown 区块解析、hash 校验、`sync` 和 `doctor`。

### 2026-06-11 - P0.5 query / sync / doctor 闭环

**完成事项**:
- [x] 完成 P0.5：Markdown 区块解析、hash 计算、`syca query --cheat`、`syca sync`、`syca doctor`。
- [x] `query` 查询前自动 sync，确保索引与 Markdown 一致。
- [x] `doctor` 覆盖：缺失文件、孤儿 Markdown、Front Matter 缺失、hash 不一致、slug 冲突、无效 Edge。
- [x] 新增 `tests/test_markdown_parser.py`、`tests/test_sync_query_doctor.py`，26 项测试全部通过。
- [x] 版本号升至 `0.5.0`。

**踩坑记录**:
- sync 更新索引时不应覆盖 SQLite 中的 `review_status`。
- query 需过滤 Cheatsheet 占位提示文本，避免空结果误判。

**遗留问题**:
- [ ] P0 最小闭环已完成；P1 LLM Review 尚未实现。

**下一步建议**:
- 评估 P0 端到端手动验收，或进入 P1 ReviewRun mock 实现。

### 2026-06-11 - P0 端到端验收与 P1 启动

**完成事项**:
- [x] 用户完成 P0 全链路手动验收：`init -> capture -> inbox -> promote -> query --cheat -> sync -> doctor`。
- [x] 记录 promote UUID 摩擦反馈，写入 ADR-007、`known-issues.md`、`data-contracts.md`（P0.7 计划）。
- [x] 将 `active-task.md` 焦点切换至 P1；`roadmap.md` 标记 P0 完成。

**踩坑记录**:
- `syca promote <capture-id>` 需完整 UUID，从 inbox 复制 ID 是验收中最慢的步骤。

**遗留问题**:
- [ ] P0.7 promote 短入口（`--latest` / `--index` / 前缀匹配）尚未实现。
- [ ] P1 ReviewRun 与 mock review 尚未实现。

**下一步建议**:
- 提交 P0 代码与文档；启动 P1.1 ReviewRun + `syca review --dry-run` / mock review。

### 2026-06-11 - P0 提交与 P1.1 ReviewRun 启动

**完成事项**:
- [x] Git commit `f92ad01`：P0 全量实现与 memory bank（v0.5.0）。
- [x] 记录 promote UUID 摩擦：ADR-007、P0.7 backlog、`known-issues.md`。
- [x] P1.1：`ReviewRun`、`mock` Provider、`syca review --dry-run` / `syca review`。
- [x] Mental Model `### Core Idea` 提取与占位拒绝；`reviews/<id>.json` 归档。
- [x] 30 项测试通过；版本号升至 `0.6.0`（P1 代码待下次提交）。

**踩坑记录**:
- Review 应用 `### Core Idea` 而非整个 Mental Model 区块，否则模板占位会导致误判。
- `review_id` 须在写 JSON 与 insert_review_run 间保持一致。

**遗留问题**:
- [ ] P0.7 promote 短入口未实现。
- [ ] P1.2 practice / stale / level set 未实现。
- [ ] 真实 LLM Provider 未接入。

**下一步建议**:
- 实现 P0.7 promote 体验增强，或继续 P1.2 新鲜度命令。

### 2026-06-11 - P1.2 practice / stale / level set

**完成事项**:
- [x] `syca practice`：Practice Log 追加、`practice_logged` 事件、索引 hash 刷新。
- [x] `syca level set`：Front Matter + SQLite 等级更新、`manual_level_changed` 事件。
- [x] `syca status --stale`：CapabilityEvent 新鲜度推导，支持 `config.toml` 阈值。
- [x] 37 项测试通过；版本号升至 `0.7.0`。

**踩坑记录**:
- 新鲜度基准取 `max(node.created_at, 最近活动事件)`，避免新节点无事件时误判。

**遗留问题**:
- [ ] P0.7 promote 短入口未实现。
- [ ] 真实 LLM Provider 未接入。

**下一步建议**:
- P0.7 promote 体验增强，或 P1 真实 Provider 适配器。
