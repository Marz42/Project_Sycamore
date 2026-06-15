# 架构总览

> HOT 知识。本文件记录 Sycamore 的技术栈、顶层目录结构和核心交互流程。写代码前必须先确认这里的约束。

---

# 架构原则

## Capture first

MVP 的首要目标不是创建完美能力节点，而是在真实工作流中低摩擦捕获信息。

优先支持：

- 快速捕获命令、片段、链接和想法。
- 管理 Inbox。
- 将少数捕获项升格为正式能力节点。
- 查询正式节点中的 Cheatsheet。
- 保证 Markdown 与 SQLite 一致。

## CLI first

CLI 是主界面。它必须服务于真实工作节奏，而不是要求用户进入完整笔记模式。

P0 命令：

- `syca init`
- `syca capture`
- `syca inbox`
- `syca promote`
- `syca query`
- `syca sync`
- `syca doctor`

## Local first

核心数据默认保存在本地：

- SQLite 保存 CaptureItem、索引、事件、关系和 ReviewRun。
- Markdown 保存正式能力节点正文。
- JSON 文件保存 ReviewRun 原始输出。
- 资产文件后续再纳入。

P0 不依赖网络。LLM 只在 P1 的 `review` 中作为可选能力出现。

## Plain files survive

Sycamore 损坏或卸载后，正式能力节点仍应能通过普通编辑器、Obsidian、ripgrep 等工具读取。

因此：

- 用户正文不只存在数据库里。
- 不用私有二进制格式保存核心内容。
- Markdown 文件路径必须稳定、可读、可备份。

## Library before service

MVP 不启动常驻 API 服务。核心逻辑沉淀为可测试的应用库，CLI 调用应用库。

未来 GUI 或 HTTP API 只能作为 core 层之外的适配器加入。

---

# 稳健技术栈

| 层面 | 选型 | 说明 |
|------|------|------|
| 语言 | Python 3.12+ | 文件处理、SQLite、CLI 和测试生态成熟。 |
| 包管理 | uv | 快速、可锁定依赖，适合现代 Python 项目。 |
| CLI 框架 | Typer | 类型标注友好，命令组织清晰。 |
| 终端展示 | Rich | 表格、状态、颜色和分区输出稳定。 |
| 数据库 | SQLite | 本地优先、零运维、可备份。 |
| 数据访问 | sqlite3 + repository 封装 | P0 避免 ORM 复杂度。 |
| Markdown 元数据 | python-frontmatter | 读写 YAML Front Matter。 |
| Markdown 区块 | 固定标题解析 + 测试 | P0 只支持受控结构，避免复杂 AST。 |
| 配置 | TOML + `tomllib` | Python 标准库可读，用户可手改。 |
| 测试 | pytest | 覆盖核心业务、文件、数据库和 CLI 行为。 |
| LLM | Provider Adapter + mock first | P1 引入，不影响 P0 离线使用。 |

暂不引入：

- FastAPI 或常驻服务。
- SQLAlchemy / Alembic。
- 向量数据库。
- Web 前端。
- 后台 daemon。
- 插件系统。

---

# 顶层目录规划

```text
Project_Sycamore/
├── memory_bank/                 # 项目长期记忆和产品/架构文档
├── sycamore/                    # Python 包，MVP 核心实现
│   ├── cli/                     # CLI 命令入口和参数解析
│   ├── core/                    # 应用服务和用例编排
│   ├── models/                  # 领域模型和枚举
│   ├── storage/                 # SQLite、Markdown、Review JSON 存储
│   ├── review/                  # P1: LLM Provider、Prompt、评审解析
│   └── utils/                   # 纯工具函数
├── tests/                       # 单元测试和 CLI 集成测试
├── pyproject.toml               # Python 项目配置
├── VERSION                      # 版本号真实来源
└── README.md                    # 项目说明（中文）
```

---

# 用户数据目录规划

```text
~/.sycamore/
├── sycamore.db                  # SQLite 元数据、捕获项、事件、索引
├── nodes/                       # 正式能力节点 Markdown
│   └── <slug>.md
├── reviews/                     # P1: ReviewRun 原始 JSON
├── assets/                      # P2+: 外部资产
└── config.toml                  # 编辑器、Provider、默认目录等配置
```

开发和测试必须支持：

```bash
SYCA_HOME=/tmp/sycamore-dev syca inbox
```

测试不得读写真实用户目录。

---

# 逻辑分层

## CLI 层

职责：

- 解析命令行参数。
- 调用 core 层用例。
- 将结果格式化为终端输出。
- 不直接写 SQL。
- 不直接解析 Markdown。

## Core 层

职责：

- 编排完整用例。
- 校验业务规则。
- 管理 Capture、Promote、Query、Sync、Doctor。
- 保持与 CLI、storage、review 解耦。

示例服务：

- `CaptureService`
- `PromotionService`
- `NodeService`
- `SearchService`
- `SyncService`
- `DoctorService`
- `ReviewService`（P1）

## Storage 层

职责：

- 管理 SQLite schema。
- 保存 CaptureItem、AbilityNode 索引、CapabilityEvent、Edge、ReviewRun。
- 读写 Markdown 节点文件。
- 计算和比较 mtime/hash。
- 读写 ReviewRun JSON 归档。

## Review 层

P1 引入。

职责：

- 构建评审 Prompt。
- 调用 LLM Provider。
- 解析结构化 ReviewRun。
- 不修改用户原文。

---

# 核心流程

## Capture

```text
User -> CLI capture
CLI -> Core: create capture item
Core -> Storage: insert capture_items
Core -> Storage: insert capability_events(capture_created)
CLI -> Terminal: print capture id
```

关键约束：

- 不要求能力断言。
- 不打开编辑器。
- 不创建 Markdown。
- 必须 10 秒内可完成。

## Promote

```text
User -> CLI promote <capture-id>
CLI -> Core: load capture item
Core -> Storage: reserve node id and slug
Core -> Markdown: create ability node file
Core -> SQLite: insert ability_nodes index
Core -> SQLite: update capture_items status
Core -> SQLite: insert capability_events(capture_promoted)
CLI -> Editor: optionally open Markdown
```

关键约束：

- 升格时才要求能力断言。
- Markdown 创建失败时不得污染 SQLite。
- SQLite 更新失败时不得留下孤儿状态，必须可由 doctor 发现。

## Query Cheatsheet

```text
User -> CLI query --cheat
CLI -> Core: search indexed nodes
Core -> Storage: ensure node index is fresh
Core -> Markdown: extract Cheatsheet block
Core -> SQLite: insert capability_events(cheatsheet_queried)
CLI -> Terminal: print focused result
```

关键约束：

- 默认查询正式节点，不把 Inbox 当作正式能力结果。
- 多个匹配项时展示候选。
- Cheatsheet 为空时提示用户补充。

## Sync

```text
User -> CLI sync
CLI -> Core: scan nodes directory
Core -> Markdown: read front matter and content hash
Core -> SQLite: update ability_nodes index
Core -> SQLite: insert capability_events(node_synced)
CLI -> Terminal: print sync summary
```

关键约束：

- Markdown 是正文和基础元数据的 SSOT。
- SQLite 搜索索引可重建。
- 不静默覆盖用户编辑。

## Doctor

```text
User -> CLI doctor
Core -> Storage: compare SQLite and filesystem
Core -> Storage: validate required fields
Core -> Terminal: report issues and suggested fixes
```

必须检查：

- SQLite 指向的 Markdown 不存在。
- Markdown 缺少 required front matter。
- content hash 不匹配。
- 孤儿 Markdown。
- slug 冲突。
- 无效 Edge。

## Review

P1 流程。

```text
User -> CLI review --dry-run
CLI -> Core: load node
Core -> Markdown: extract Mental Model
Core -> Review: build preview payload
User -> CLI review
Core -> Review: request critique
Review -> Core: ReviewRun
Core -> Storage: insert review_runs and write reviews/<id>.json
Core -> Markdown: append human-readable Review Notes if user confirms
```

关键约束：

- 不覆盖用户原文。
- 不标记为 verified。
- 默认只发送必要内容。
- 旧 Mental Model 的 ReviewRun 必须可识别。

---

# 数据一致性策略

## 字段所有权

- Markdown Front Matter 拥有 `id`、`slug`、`title`、`domain`、`claimedLevel`。
- Markdown 正文拥有 Mental Model、Cheatsheet、Practice Log、References。
- SQLite 拥有 CaptureItem、CapabilityEvent、Edge、ReviewRun 和派生状态。
- SQLite 中的 AbilityNode 是索引副本，不是正文权威。

## 冲突处理

P0 不做复杂自动 merge。

策略：

- 能从 Markdown 重建的，一律重建。
- 可能覆盖用户正文的，一律拒绝自动写入。
- `doctor` 报告问题和建议命令。
- 需要用户选择时，打开编辑器或提示手动修复。

---

# 未来扩展边界

## GUI

只能作为 core 层适配器加入，不能重写业务逻辑。

## HTTP API

只有 GUI、远程访问或第三方集成出现真实需求时才增加。

## RAG

不进入 P0/P1。只有节点质量稳定、引用资产规范、关键词检索不足时再评估。
