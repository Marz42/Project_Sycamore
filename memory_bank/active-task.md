# 当前任务

> HOT 知识。本文件只记录当前最重要的一组任务。完成后应及时更新，避免 Agent 误以为旧任务仍在进行。

---

# 当前焦点

P0–P2 已交付，Phase 1A-0 已完成。当前阶段：**Phase 1A Recover 改造**（recall-first + fail-type + status --weak）。

当前命令流：

> init → capture → inbox → promote → query --cheat → sync → doctor → practice / review / recover → link → graph / status

---

# 本轮任务：Phase 1A-0 NodeType 基础设施

- [x] 新增 `NodeType` 枚举（`capability` / `concept` / `theorem` / `process`）
- [x] `AbilityNode` 模型新增 `node_type` 字段
- [x] SQLite `ability_nodes` 表新增 `node_type` 列（默认 `capability`），`SCHEMA_VERSION` → 2
- [x] 四种类型的 Markdown 模板（`markdown_store.py`）
- [x] `promote --type` CLI 参数 + service 逻辑
- [x] `sync` 解析 front matter `type` 写入索引（非法值默认 `capability`）
- [x] `doctor` 校验 `type` 为合法枚举值
- [x] 现有节点 sync 时自动补齐默认 `capability`
- [x] 测试覆盖：14 项新测试（templates/sync/doctor/CLI/migration）
- [x] 版本号升至 `v0.11.2`
- [x] Memory bank 全量同步（changelog / roadmap / project-brief）

---

# 本轮任务：Phase 1A Recover 改造

- [x] `recover --mode recall-first`：先展示标题+线索，用户回忆后再展开
- [x] `recover --mode supported`：展示局部提示
- [x] `recover --mode full`：完整展示（保留旧行为作为 fallback）
- [x] `recover --hard` / `--easy`：四级评分（hard/good/easy 补充现有 pass/fail）
- [x] `recover --fail-type recall|concept|procedure|transfer`：失败分类
- [x] `capability_events.payload_json` 写入 fail-type 数据
- [x] `syca status --weak`：薄弱画像（按节点/领域展示失败类型分布）
- [x] 类型感知 recover prompt：Capability 问步骤、Concept 问核心主张、Theorem 问直觉、Process 问机理
- [x] 测试覆盖：29 项新测试（prompt/modes/ratings/fail-types/weak/CLI）
- [x] 版本号升至 `v0.12.0`

---

# 已完成的文档校准 Check-list

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

## P2.1 能力恢复与关系

- [x] 实现 `syca recover <node-id>`（展示 drill；`--pass` / `--fail` 记录事件）。
- [x] 实现 `syca link SOURCE TARGET --type ...`（manual edge，`rationale` 可选）。
- [x] 实现 `syca graph --domain <name>`（域内 ASCII 能力图）。
- [x] 实现 `syca status --domain <name>`（域内新鲜度视图）。

## 文档与验证

- [x] 撰写 `memory_bank/manuals/real-world-validation-guide.md`。
- [x] 更新 `README.md`（中文）与 manuals。

---

# 当前限制

- LLM 需在 `config.toml` 中显式 `enabled = true` 且配置 `DEEPSEEK_API_KEY` 后才会调用 DeepSeek。
- Recover drill 为自评模式，暂不自动验证解释质量。
- 暂不实现 RAG、多端同步、Web、备份命令或插件系统。
- 暂不引入 ORM 或常驻服务。
- 修改数据模型或 CLI 契约前必须更新 `data-contracts.md` 和 `roadmap.md`。
