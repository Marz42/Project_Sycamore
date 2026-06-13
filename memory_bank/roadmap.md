# 路线图

> WARM 知识。涉及阶段规划、技术栈取舍、MVP 范围或优先级排序时读取。

---

# 北极星

Sycamore 的路线图围绕一个判断标准展开：

> 能否在不增加明显认知负担的前提下，把日常碎片逐步转化为可恢复、可校准的能力？

因此，路线图不以“功能丰富度”为优先级，而以“真实使用闭环的可靠性”为优先级。

---

# 技术栈原则

## 最稳健选择

| 层面 | 选型 | 采用时机 | 理由 |
|------|------|----------|------|
| 语言 | Python 3.12+ | P0 | 标准库强、CLI 生态成熟、SQLite 和文件处理简单。 |
| 包管理 | uv | P0 | 依赖锁定、速度快、项目结构清晰。 |
| CLI | Typer | P0 | 类型标注友好，命令定义清楚，适合个人 CLI 工具。 |
| 终端 UI | Rich | P0 | 表格、颜色、状态展示足够强，不需要 GUI。 |
| 数据库 | SQLite | P0 | 本地优先、零运维、可备份、可迁移。 |
| 数据访问 | sqlite3 + repository 封装 | P0 | 避免 ORM 在早期放大 schema 复杂度。 |
| Markdown 元数据 | python-frontmatter | P0 | 处理 YAML Front Matter，保持 Markdown 可读。 |
| Markdown 区块 | 固定标题解析 + 测试 | P0 | 只解析受控结构，降低复杂 Markdown AST 风险。 |
| 配置 | TOML + `tomllib` | P0 | Python 标准库可读，用户可手改。 |
| 测试 | pytest | P0 | 覆盖文件、数据库、CLI 和 sync 行为。 |
| LLM | Provider Adapter + mock first | P1 | 不让 P0 依赖网络和模型稳定性。 |

## 暂不采用

| 技术 | 暂不采用原因 | 重新评估条件 |
|------|--------------|--------------|
| FastAPI | 常驻服务会增加部署和状态复杂度。 | GUI 或第三方集成真正需要 API。 |
| SQLAlchemy / Alembic | 早期 schema 会频繁变动，ORM 迁移成本偏高。 | SQLite 表稳定并出现复杂查询。 |
| 向量数据库 | 会把产品推向查询系统，偏离能力校准。 | 节点质量足够高，且关键词检索明显不够。 |
| Web 前端 | 会稀释 P0 的捕获和同步可靠性。 | CLI 日常使用稳定后。 |
| 后台 daemon | 增加跨平台运行和调试成本。 | 需要自动同步、提醒或文件监听时。 |
| 插件系统 | 过早抽象。 | 出现 3 个以上稳定外部集成需求。 |

---

# 阶段 0：文档和契约校准

## 目标

把产品从“强制能力节点”校准为“低摩擦捕获 -> 渐进式升格 -> 能力恢复”。

## 交付物

- [x] 更新 `project-brief.md`。
- [x] 更新 `data-contracts.md`，加入 `CaptureItem`、`CapabilityEvent`、`ReviewRun`。
- [x] 更新 `architecture.md`，加入 Capture/Promote/Sync 流程和字段所有权。
- [x] 更新 `active-task.md`，把 P0 开发目标改为 Capture-first。

## 退出标准

- HOT 文档对 P0 范围没有明显冲突。
- P0 不再把 LLM Review 或能力图作为必需闭环。
- 数据一致性策略已写清楚。

---

# 阶段 1：P0 最小可信闭环

**状态**: 已完成（2026-06-11 端到端验收通过）。

## 目标

做出一个日常可用的本地 CLI：能快速捕获、管理 Inbox、升格为节点、查询 Cheatsheet，并可靠同步 Markdown 与 SQLite。

## 核心命令

```bash
syca init
syca capture --cheat "awk '{print $1}' access.log | sort | uniq -c"
syca capture --note "awk 字段分隔符今天踩坑"
syca inbox
syca promote <capture-id>
syca query "awk" --cheat
syca sync
syca doctor
```

## 交付物

- Python 项目骨架和 `pyproject.toml`。
- `sycamore/` 包结构。
- `CaptureItem`、`AbilityNode`、`CapabilityEvent` 的最小领域模型。
- SQLite 初始化和 schema 版本表。
- Markdown 节点模板生成。
- Capture/Inbox/Promote CLI。
- Cheatsheet 查询。
- `sync` 和 `doctor` 的基础一致性检查。
- pytest 覆盖核心文件和数据库行为。

## 不做

- 不接真实 LLM。
- 不做能力图。
- 不做恢复演练。
- 不做资产内容寻址。
- 不做 Web 或 API 服务。

## 退出标准

- 能在 10 秒内完成一次 capture。
- 能从 Inbox 升格一个 CaptureItem 为 Markdown AbilityNode。
- 外部编辑 Markdown 后，`syca sync` 能更新 SQLite 索引。
- `syca doctor` 能发现缺失文件、孤儿记录、slug 冲突。
- `syca query --cheat` 能稳定返回正式节点中的 Cheatsheet。
- 测试覆盖 P0 关键路径。

---

# 阶段 1.5：P0.7 Promote 体验增强

## 目标

降低 inbox 升格摩擦，无需复制完整 UUID 即可完成 promote。

## 候选交付

- `syca promote --latest`
- `syca promote --index <n>`
- `syca promote <short-id>`（UUID 前缀）
- 可选交互式 `syca promote`

## 启动条件

- P0 验收完成（已满足）。
- 可与 P1 并行，优先于 P1 中不依赖 Review 的 CLI 打磨。

---

# 阶段 2：P1 能力校准

**状态**: 已完成（v0.10.0，DeepSeek E2E 已验证）。

## 目标

让正式能力节点从“可查”变成“可校准”：记录实践证据、能力新鲜度和结构化 LLM 评审。

## 核心命令

```bash
syca practice <node-id>
syca review <node-id> --dry-run
syca review <node-id>
syca status --stale
syca level set <node-id> L2
```

## 交付物

- `ReviewRun` 结构化存储。
- Review JSON 原始归档。
- Prompt 版本管理。
- LLM Provider Adapter。
- mock Provider 和测试夹具。
- `CapabilityEvent` 推导 `freshness` / `readiness`。
- Practice Log 快速追加。
- stale 节点视图。

## 隐私门控

LLM Review 必须满足：

- 默认只发送 `Mental Model` 和必要元数据。
- Review 前可以预览将发送内容。
- 支持节点级 `llmAllowed`。
- 原始输出保存在本地。

## 退出标准

- Review 不覆盖用户原文。
- ReviewRun 可按节点、时间、promptVersion 查询。
- Mental Model 修改后，旧 ReviewRun 能标记为基于旧内容。
- stale 节点能基于事件和时间显示。

---

# 阶段 3：P2 能力恢复与关系

**状态**: 核心已交付（v0.11.1），待真实使用验证收官。

## 目标

让 Sycamore 不只是存储知识，而是主动帮助用户发现能力退化和跨领域连接。

## 核心命令

```bash
syca recover <node-id>
syca link SOURCE TARGET --type prerequisite
syca graph --domain shell
syca status --domain backend
```

## 交付物

- Recover Drill：重新解释 Mental Model 或按 Cheatsheet 完成任务。
- 手动 link，`rationale` 可选。
- Edge confidence：区分 explicit、implicit、suggested、derived。
- 终端文本图或列表图。
- 基础领域视图。

## 退出标准

- 用户能看到某个领域下哪些能力新鲜、哪些 stale。
- 关系图不会阻塞日常录入。
- rationale 是增强质量，而不是建边门槛。

---

# 阶段 4：P3 资产与扩展

## 目标

在核心闭环稳定后，补充资产管理、备份、GUI 或语义检索。

## 候选方向

- 资产引用和内容 Hash 去重。
- 备份与恢复命令。
- 文件监听和自动 sync。
- Obsidian 兼容视图。
- GUI 能力地图。
- 语义检索或 RAG。

## 启动条件

必须同时满足：

- P0/P1 已经成为日常使用工具。
- Inbox 没有持续失控。
- 节点质量足够稳定。
- 关键词检索或手动图谱已经出现明确瓶颈。

---

# 近期开发顺序

## 第 1 步：项目骨架

- 初始化 `pyproject.toml`。
- 配置 `uv`、pytest、ruff 或等价 lint 工具。
- 创建包结构。
- 建立最小 CLI 入口。

## 第 2 步：数据目录和配置

- 实现 `syca init`。
- 创建 `~/.sycamore/` 或 `SYCA_HOME`。
- 写入 `config.toml`。
- 初始化 SQLite。

## 第 3 步：Capture

- 实现 `syca capture --note`。
- 实现 `syca capture --cheat`。
- 实现 `syca inbox`。
- 保存 CaptureItem 到 SQLite。

## 第 4 步：Promote

- 生成 Markdown AbilityNode。
- 从 CaptureItem 填入 Cheatsheet 或初始备注。
- 写入 Front Matter。
- 记录 `capture_promoted` 事件。

## 第 5 步：Query 和 Sync

- 解析固定 Markdown 区块。
- 实现 `query --cheat`。
- 记录文件 mtime/hash。
- 实现 `sync` 和 `doctor`。

## 第 6 步：测试补齐

- 使用 `tmp_path` 隔离 `SYCA_HOME`。
- 覆盖 capture、promote、query、sync、doctor。
- 确保不读写真实用户目录。

---

# 风险门控

| 风险 | 观察信号 | 停止条件 | 应对 |
|------|----------|----------|------|
| Capture 失控 | Inbox 快速堆积但不升格 | Inbox 超过 100 条仍无清理机制 | 先做 archive/discard 和清理提醒。 |
| 同步不可靠 | 外部编辑后索引错乱 | 出现正文丢失风险 | 暂停新功能，优先 doctor/sync。 |
| LLM 过早侵入 | P0 依赖 API Key 才可用 | 本地功能不能离线跑 | 延后 Review，使用 mock。 |
| 技术栈膨胀 | 引入 Web/ORM/向量库 | P0 未稳定前新增重依赖 | 回退到 SQLite/Markdown/CLI。 |
| 能力等级失真 | 大量节点长期 L2 但无实践 | status 无法提示 stale | 优先实现 CapabilityEvent。 |

---

# 版本策略

当前 `0.11.1`。P0–P2 核心 CLI 已可用。

建议版本路线（历史）：

- `0.3.0`：P0 CLI 骨架和 Capture/Inbox 可用。
- `0.4.0`：Promote、Markdown 节点和 Cheatsheet 查询可用。
- `0.5.0`：Sync/Doctor 和数据一致性闭环可用。
- `0.6.0`：ReviewRun 和 mock/真实 Provider 可用。
- `0.7.0`：CapabilityEvent、freshness 和 stale view 可用。
- `0.8.0`：Review 管理与 Provider 工厂。
- `0.9.0`：Promote 短入口。
- `0.10.0`：DeepSeek Provider。
- `0.11.0`：Recover、link、graph、status --domain。
- `0.11.1`：graph ASCII 树形展示。

手工验收指南：`memory_bank/manuals/real-world-validation-guide.md`。

`1.0.0` 的条件：

- Markdown 数据格式稳定。
- SQLite migration 策略稳定。
- 不丢失用户正文。
- P0/P1 命令在日常使用中足够可靠。
