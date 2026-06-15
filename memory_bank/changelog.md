# 变更日志

> WARM 知识。记录项目版本发布历史和重要未发布变更。格式遵循 Keep a Changelog，版本号遵循 SemVer。

---

## [Unreleased]

## [0.11.2] - 2026-06-12

### Added

- `NodeType` 枚举：`capability` / `concept` / `theorem` / `process`。
- `promote --type` 参数：升格时指定节点类型，默认 `capability`。
- 四种 Markdown 模板：capability（Steps/Pitfalls/Cheatsheet）、concept（Core Thesis/Historical Context/Critique/Apply To）、theorem（Formula/Intuition/Boundary Conditions/Counterexamples）、process（Mechanism/Parameters/Disturbance Response）。
- Markdown front matter 新增 `type` 字段。

### Changed

- SQLite schema v2：`ability_nodes` 表新增 `node_type` 列，`SCHEMA_VERSION` → 2。
- `sync` 从 front matter 解析 `type`，非法值默认回退为 `capability`。
- `doctor` 校验 `type` 合法性。
- `database.py` 新增迁移机制，v1 数据库自动添加 `node_type` 列。

---

## [0.11.1] - 2026-06-11

### Added

- `syca graph --domain` ASCII 树形展示（prerequisite 树、其他关系箭头列表、`[unlinked]` 分区）。
- `memory_bank/manuals/real-world-validation-guide.md` 端到端手工验收指南。

### Changed

- `README.md` 改为中文，反映 v0.11.1 命令与文档索引。
- 更新 `deploy.md`、`testing-guide.md`、`roadmap.md`、`active-task.md`。

### Fixed

- Rich 控制台不再吞掉 `[prerequisite]` 等 section 标记（`markup=False`）。

---

## [0.11.0] - 2026-06-11

### Added

- `syca recover`：Recovery Drill 展示与 `--pass` / `--fail` 事件记录。
- `syca link`：手动建立 `ability_edges` 关系。
- `syca graph --domain`：域内能力关系列表。
- `syca status --domain`：域内新鲜度视图。

---

## [0.10.0] - 2026-06-11

### Added

- 新增 `.env.example`：DeepSeek 默认 `deepseek-v4-pro`、`https://api.deepseek.com`。
- 实现 `DeepSeekReviewProvider`（OpenAI 兼容 chat completions + JSON critique）。
- CLI 启动时自动加载 `.env`（cwd 与 `SYCA_HOME`）。

### Changed

- 默认 `config.toml` `[llm]` provider 改为 `deepseek`；`enabled = false` 时 review 仍用 mock。

---

## [0.9.0] - 2026-06-11

### Added

- `syca promote` 无参默认升格最新 inbox 条目；支持 `--latest`、`--index <n>`、UUID 前缀匹配。
- `syca inbox` 显示 `#` 序号与 ID 前 8 位，便于快速 promote。

---

## [0.8.0] - 2026-06-11

### Added

- 实现 `syca reviews list|accept|ignore|revised` 与 ReviewRun outdated 检测。
- 实现 Review Provider 工厂：默认 mock，可选 `http` endpoint。
- 支持节点 Front Matter `llmAllowed: false` 隐私门控。
- `config.toml` 扩展 `[llm]` 配置项（provider、endpoint、model、api_key_env）。

---

## [0.7.0] - 2026-06-11

### Added

- 实现 `syca practice`：追加 Practice Log、刷新索引、记录 `practice_logged`。
- 实现 `syca level set`：更新 Markdown `claimedLevel` 与 `manual_level_changed` 事件。
- 实现 `syca status --stale`：基于 CapabilityEvent 推导新鲜度（默认 30 天，可配置）。
- `config.toml` 新增 `[freshness] stale_after_days`。

---

## [0.6.0] - 2026-06-11

### Added

- 实现 `ReviewRun` 模型、`review_repository` 与 `reviews/*.json` 原始归档。
- 实现 mock Review Provider（`p1-critique-v1` prompt）。
- 实现 `syca review <node-id> --dry-run` 与 `syca review <node-id>`。
- 评审后更新节点 `review_status` 为 `challenged`，记录 `review_completed` 事件。
- 支持 node id / slug / UUID 前缀解析（与后续 P0.7 方向一致）。

---

## [0.5.0] - 2026-06-11

### Added

- 实现固定 Markdown 区块解析（`## Cheatsheet` 等标题）。
- 实现 content / front matter hash 计算与校验。
- 实现 `syca sync`：从 `nodes/*.md` 刷新 SQLite 索引并记录 `node_synced` 事件。
- 实现 `syca query <term> --cheat`：搜索 Cheatsheet 并记录 `cheatsheet_queried` 事件。
- 实现 `syca doctor`：检查缺失文件、孤儿 Markdown、hash 不一致、slug 冲突和无效 Edge。
- 新增 parser / sync / query / doctor 测试。

---

## [0.4.0] - 2026-06-11

### Added

- 实现 `AbilityNode` 领域模型与 `node_repository`。
- 实现 Markdown 节点模板生成：按捕获类型填充 Capability、Cheatsheet、References 等区块。
- 实现 `syca promote <capture-id>`，支持 `--title`、`--domain`、`--claimed-level`。
- 升格时写入 `nodes/<slug>.md`、更新 `capture_items` 状态并记录 `capture_promoted` 事件。
- 新增 promote 单元测试与 CLI 集成测试。

---

## [0.3.0] - 2026-06-11

### Added

- 实现 `syca init`：创建 `SYCA_HOME` 数据目录、`config.toml`、SQLite schema 和 `nodes/`、`reviews/`、`assets/` 子目录。
- 实现 `syca capture --note/--cheat/--link` 与 `syca inbox`，写入 `CaptureItem` 并记录 `capture_created` 事件。
- 新增 `paths`、`database`、`schema`、`config_store`、`capture_repository`、`init_service`、`capture_service` 模块。
- 新增 init / capture / inbox 单元测试与 CLI 测试，全部通过 `SYCA_HOME` 隔离。

### Changed

- 将 Sycamore 的产品定位收敛为“能力校准与恢复工具”。
- 明确 MVP 以 CLI、本地 SQLite、标准 Markdown、Capture/Inbox/Promote 和同步检查为核心，LLM 评审后移到 P1。
- 将原模板化 memory bank 文档整理为可执行的产品、架构和数据契约基线。
- 将 MVP 路线从 AbilityNode-first 调整为 Capture-first，先解决低摩擦捕获、Inbox、升格、查询和同步。
- 将技术栈收敛为 Python 3.12+、uv、Typer、Rich、SQLite、Markdown/front matter、pytest，暂缓 Web、ORM、RAG 和常驻服务。

### Added

- 新增核心实体定义：`AbilityNode`、`AbilityEdge`。
- 新增能力学习循环：`Learn -> Encode -> Challenge -> Practice -> Recover`。
- 新增 LLM 评审边界：只做批判性反馈，不代写、不覆盖、不标记为事实认证。
- 新增核心实体定义：`CaptureItem`、`CapabilityEvent`、`ReviewRun`，替代一次性 `ReviewReport` 思路。
- 新增 `roadmap.md`，记录阶段路线、退出标准、技术栈取舍和风险门控。
- 新增 Python P0.1 项目骨架、`pyproject.toml`、`syca` CLI 入口和基础 CLI 测试。

---

## [0.2.0] - 2026-06-11

### Added

- 建立 memory bank 目录和基础项目文档。
- 确立 Sycamore 作为个人外脑与能力锚定工具的初始方向。
