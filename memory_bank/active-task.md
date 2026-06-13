# 当前任务

> HOT 知识。本文件只记录当前最重要的一组任务。完成后应及时更新，避免 Agent 误以为旧任务仍在进行。

---

# 当前焦点

P1 能力校准与 DeepSeek Provider 已完成。当前进入 **P2 能力恢复与关系**（recover、link、graph、status --domain）。

P0 主循环：

> init -> capture -> inbox -> promote -> query --cheat -> sync -> doctor

---

# 本轮文档校准 Check-list

- [x] 更新 `project-brief.md`，加入 Capture-first、渐进式升格、字段所有权、能力新鲜度和 ReviewRun。
- [x] 创建 `roadmap.md`，定义稳健技术栈、阶段路线、退出标准和风险门控。
- [x] 更新 `data-contracts.md`，加入 `CaptureItem`、`CapabilityEvent`、`ReviewRun` 和新的 CLI 契约。
- [x] 更新 `architecture.md`，对齐 Capture-first 和本地一致性策略。
- [x] 更新本文件，校准下一步开发任务。

---

# 下一步开发 Check-list

## P0.1 项目骨架

- [x] 初始化 Python 项目骨架和 `pyproject.toml`。
- [x] 配置 uv、pytest 和基础 lint/format 工具。
- [x] 创建 `sycamore/` 包结构。
- [x] 实现最小 `syca` CLI 入口。

## P0.2 本地数据目录

- [x] 实现 `syca init`。
- [x] 支持 `SYCA_HOME` 指定数据目录。
- [x] 创建 `config.toml`。
- [x] 初始化 SQLite schema。

## P0.3 Capture / Inbox

- [x] 实现 `CaptureItem` 领域模型。
- [x] 实现 `syca capture --note`。
- [x] 实现 `syca capture --cheat`。
- [x] 实现 `syca capture --link`。
- [x] 实现 `syca inbox`。

## P0.4 Promote / Node

- [x] 实现 `AbilityNode` 领域模型。
- [x] 实现 Markdown 节点模板生成。
- [x] 实现 `syca promote <capture-id>`。
- [x] 记录 `capture_promoted` 事件。

## P0.5 Query / Sync / Doctor

- [x] 实现固定 Markdown 区块解析。
- [x] 实现 `syca query --cheat`。
- [x] 实现文件 hash / front matter hash。
- [x] 实现 `syca sync`。
- [x] 实现 `syca doctor`。

## P0.6 测试

- [x] 建立 pytest 测试入口，后续涉及数据目录时使用 `tmp_path` 隔离 `SYCA_HOME`。
- [x] 覆盖 init、capture、inbox、promote、query、sync、doctor。
- [x] 确保测试不会读写真实 `~/.sycamore/`（全部通过 `SYCA_HOME` fixture 隔离）。

## P0.7 Promote 体验增强（待做，用户验收反馈）

- [x] 支持 `syca promote --latest`（升格最新 inbox 条目）。
- [x] 支持 `syca promote --index <n>`（对应 `syca inbox` 列表序号）。
- [x] 支持 `syca promote <short-id>`（UUID 前缀，唯一时匹配）。
- [x] 无参数 `syca promote` 默认升格最新 inbox 条目。

> 背景：P0 仅支持完整 UUID，端到端验收中从 inbox 复制 `capture-id` 摩擦偏高。保留 UUID 精确匹配，补充更短、更符合 CLI 节奏的升格入口。

## P1.1 ReviewRun 基础

- [x] 实现 `ReviewRun` 领域模型与 repository。
- [x] 实现 Mental Model 区块提取与 hash。
- [x] 实现 mock LLM Provider 与 Prompt 版本常量。
- [x] 实现 `syca review <node-id> --dry-run`。
- [x] 实现 `syca review <node-id>`（写入 ReviewRun JSON + SQLite，记录 `review_completed`）。

## P1.2 能力新鲜度

- [x] 实现 `syca practice <node-id>` 快速追加 Practice Log。
- [x] 实现 `syca status --stale`。
- [x] 实现 `syca level set <node-id> <level>`。

## P1.3 Review 完善

- [x] 实现 `syca reviews list <node-id>`（含 outdated 标记）。
- [x] 实现 `syca reviews accept|ignore|revised <review-id>`。
- [x] 实现 Provider 工厂（mock 默认，可选 http）。
- [x] 支持节点级 `llmAllowed: false` 隐私门控。

## P1.4 DeepSeek Provider

- [x] 新增根目录 `.env.example`（DeepSeek 默认：`deepseek-v4-pro` / `https://api.deepseek.com`）。
- [x] CLI 启动时加载 `.env`（不覆盖已有环境变量）。
- [x] 实现 `DeepSeekReviewProvider`（OpenAI 兼容 `/chat/completions`）。
- [x] 默认 `config.toml` `[llm]` 指向 DeepSeek（`enabled = false` 时仍走 mock）。

## P2.1 能力恢复与关系（进行中）

- [x] 实现 `syca recover <node-id>`（展示 drill；`--pass` / `--fail` 记录事件）。
- [x] 实现 `syca link SOURCE TARGET --type ...`（manual edge，`rationale` 可选）。
- [x] 实现 `syca graph --domain <name>`（域内关系列表）。
- [x] 实现 `syca status --domain <name>`（域内新鲜度视图）。

---

# 当前限制

- LLM 需在 `config.toml` 中显式 `enabled = true` 且配置 `DEEPSEEK_API_KEY` 后才会调用 DeepSeek。
- Recover drill 为自评模式，暂不自动验证解释质量。
- 暂不实现能力图、恢复演练、RAG、多端同步、Web 或插件系统。
- 暂不引入 ORM 或常驻服务。
- 修改数据模型或 CLI 契约前必须更新 `data-contracts.md` 和 `roadmap.md`。
