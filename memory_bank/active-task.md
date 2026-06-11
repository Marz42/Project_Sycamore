# 当前任务

> HOT 知识。本文件只记录当前最重要的一组任务。完成后应及时更新，避免 Agent 误以为旧任务仍在进行。

---

# 当前焦点

P0 最小可信闭环已完成端到端验收。当前进入 **P1 能力校准**（ReviewRun、mock Provider、practice / stale 等）。

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

- [ ] 支持 `syca promote --latest`（升格最新 inbox 条目）。
- [ ] 支持 `syca promote --index <n>`（对应 `syca inbox` 列表序号）。
- [ ] 支持 `syca promote <short-id>`（UUID 前缀，唯一时匹配）。
- [ ] 可选：无参数 `syca promote` 交互式选择 inbox 条目。

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

---

# 当前限制

- P1 首轮仍使用 mock Provider，不接真实 LLM API。
- 暂不实现能力图、恢复演练、RAG、多端同步、Web 或插件系统。
- 暂不引入 ORM 或常驻服务。
- 修改数据模型或 CLI 契约前必须更新 `data-contracts.md` 和 `roadmap.md`。
