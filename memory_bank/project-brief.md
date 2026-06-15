# 项目身份卡片

| 字段 | 内容 |
|------|------|
| **项目名称** | Sycamore |
| **名称含义** | Seek more；悬铃木象征分叉、生长与长期庇护 |
| **一句话描述** | 面向跨领域学习者的能力校准与恢复工具 |
| **项目类型** | CLI 优先、本地优先的个人外脑；GUI 和 Web 后置 |
| **当前版本** | 0.11.2，见根目录 `VERSION` |
| **当前阶段** | P0 / P1 / P2 已交付，处于真实使用验证期 |

---

# 核心愿景

Sycamore 的目标不是成为另一个笔记软件，也不是替用户记住所有知识。它要帮助跨领域学习者在不断探索新领域时回答三个问题：

- 我现在会什么？
- 我会到什么程度？
- 当我一段时间后重新使用这项能力时，怎样最快恢复判断力和操作力？

它的核心价值不是“查得更快”，而是建立一套从零散经验到能力节点的渐进式系统：允许用户在忙碌场景下低摩擦捕获片段，再在合适时机把少数真正重要的片段升格为可恢复、可校准、可评审的能力。

---

# 问题陈述

跨领域学习者面对新知识时通常有六个矛盾：

- **广度带来快乐，也带来边界焦虑**：会很多东西，但不确定每项能力到底到什么程度。
- **理解与操作不同步**：知道概念，但动手时仍要查命令、参数、配置或边界条件。
- **外置大脑容易退化为资料库**：笔记越积越多，却没有提升自身抽象理解和迁移能力。
- **高质量记录与真实工作流冲突**：编码或排障时没有心智带宽写能力断言和完整 Mental Model。
- **静态能力等级会腐烂**：一次标记的 L2 半年后可能已经无法直接使用。
- **双存储系统容易脑裂**：SQLite 和 Markdown 如果同时保存同一字段，外部编辑后会产生冲突。

Sycamore 必须承认真实使用场景：用户经常不是在“学习模式”下录入，而是在“正在解决问题”的高压上下文中捕获。

---

# 产品定位

Sycamore 是一个 **能力校准与恢复工具**，不是通用知识库。

它将知识处理拆成两层：

- **低摩擦捕获层**：快速保存命令、片段、坑、想法和参考链接，不要求用户当场整理。
- **能力升格层**：把重要碎片整理成能力断言、心智模型、Cheatsheet、实践记录和评审对象。

产品主循环从原来的：

> Learn -> Encode -> Challenge -> Practice -> Recover

调整为：

> Capture -> Clarify -> Encode -> Challenge -> Practice -> Recover

- **Capture**：先保住现场信息，不打断当前任务。
- **Clarify**：事后判断这个片段是否值得进入正式能力体系。
- **Encode**：用自己的话写能力断言、Mental Model 和边界。
- **Challenge**：用 LLM 进行批判性评审。
- **Practice**：用真实任务、练习或踩坑记录证明能力。
- **Recover**：未来按需恢复抽象理解和实操细节。

---

# 第一性原理

## 1. 真实系统必须先接住低质量输入

如果系统只接受高质量能力节点，用户会在最需要它的时候放弃它。

因此，Sycamore 必须允许两类内容共存：

- `CaptureItem`：粗糙、临时、低摩擦，属于 Inbox。
- `AbilityNode`：结构化、可校准、可恢复，属于能力库。

反囤积原则不应体现在“禁止捕获”，而应体现在“捕获物不能自动冒充能力”。

## 2. 学习的最小高质量成果是能力断言

正式能力节点不应只是“Docker”“Shell”“FastAPI”这样的主题名，而应该是一句可验证的能力断言。

示例：

- 不推荐：`Docker Volume`
- 推荐：`我能解释 Docker volume 和 bind mount 的区别，并在部署时正确选择`

能力断言是升格后的目标，不是捕获时的门槛。

## 3. 大脑负责 Index，工具负责 Payload

大脑不需要记住每个命令参数，但必须知道：

- 什么时候需要这个工具？
- 它解决什么问题？
- 它的核心机制是什么？
- 它有哪些常见误用？
- 需要恢复细节时应该查哪里？

Sycamore 负责保存低频细节、实践证据、评审记录和恢复线索；大脑负责维护抽象模型和判断力。

## 4. 等级是事件推导，不是永久标签

能力等级不能只靠一次手动标记。Sycamore 应区分：

- `claimedLevel`：用户曾经声明或达到的水平。
- `evidenceLevel`：由实践、评审、恢复演练支持的水平。
- `freshness`：当前是否新鲜，是否需要恢复。

一个节点可以是 `L2 stale`：曾经理解并能变通，但当前需要恢复演练。

## 5. Markdown 正文优先，SQLite 负责索引和事件

Sycamore 采用双存储，但不能有双重真相。

原则：

- Markdown 是用户可读正文的 Single Source of Truth。
- SQLite 是索引、关系、事件、ReviewRun 和派生状态的 Single Source of Truth。
- 搜索索引必须可重建。
- CLI 写入 Markdown 前必须检测外部修改，避免静默覆盖。

---

# 核心概念

## CaptureItem

CaptureItem 是低摩擦捕获单元，用于保存当下不适合整理的内容。

适合捕获：

- 偏门命令。
- 临时排障步骤。
- 代码片段。
- 参考链接。
- 一句还没想清楚的理解。
- “这个以后值得整理”的提醒。

CaptureItem 不需要能力断言、Mental Model 或 Practice Log。它的状态只能是：

- `inbox`：等待处理。
- `promoted`：已升格到能力节点。
- `archived`：保留但不进入能力体系。
- `discarded`：确认无价值后丢弃。

## AbilityNode

AbilityNode 是正式能力库的最小单位，表示一项可校准、可恢复、可实践的能力。

每个节点至少包含：

- `Capability Statement`：一句话能力断言。
- `Claimed Level`：用户声明或历史达到的等级。
- `Freshness`：当前新鲜度，由时间和事件推导。
- `Mental Model`：抽象理解、机制、边界和类比。
- `Cheatsheet`：低频但实操必要的命令、配置和片段。
- `Practice Log`：真实练习、项目使用和踩坑记录。
- `Review Notes`：人类可读的评审摘要。
- `Node Type`：节点类型决定 Markdown 结构和考核方向。四种类型：`capability`（操作能力）、`concept`（概念框架）、`theorem`（定理模型）、`process`（系统机制）。详见 `data-contracts.md` NodeType 枚举。

## NodeType

每个 AbilityNode 属于以下四种类型之一：

| 类型 | 适用领域 | 核心问题 |
|:--|:--|:--|
| `capability` | IT、软件操作、外语 | 给你一个场景，你能做对吗？ |
| `concept` | 哲学、历史、经济学 | 给你一个新事件，能用这个框架分析吗？ |
| `theorem` | 数学、物理、算法 | 边界条件失效时能识别反例吗？ |
| `process` | 化工、机械、生物 | 外部扰动时如何调节参数维持稳定？ |

## CapabilityEvent

能力状态必须由事件修正。重要事件包括：

- `capture_created`
- `capture_promoted`
- `practice_logged`
- `cheatsheet_queried`
- `review_completed`
- `recovery_passed`
- `recovery_failed`
- `manual_level_changed`

事件让系统知道能力是否新鲜，而不是永久相信静态等级。

## Edge

连线表示能力节点之间的关系。Sycamore 保留技能树的视觉隐喻，但底层更接近能力图。

MVP 支持的关系：

- `prerequisite`：前置依赖。
- `related`：横向相关。
- `similar_pattern`：跨领域相似模式。
- `contrasts_with`：容易混淆或需要对照理解。
- `used_in_scenario`：在同一实操场景下共同使用。

`rationale` 不应在 P0 强制填写。边分为：

- `explicit`：用户写了理由，可信度高。
- `implicit`：快速建立，只有类型和时间。
- `suggested`：系统或 LLM 推荐，等待确认。
- `derived`：由共同标签、共同实践或共同查询推导。

## ReviewRun

LLM Review 是不可变评审记录，不是一段临时聊天。

每次 Review 必须保存：

- 被评审节点。
- Mental Model 的内容 Hash。
- Prompt 版本。
- Provider 和模型。
- 结构化问题。
- 用户决策。
- 原始输出归档路径。

Markdown 中只追加人类可读摘要；完整结构化数据保存在 SQLite 和 JSON 归档中。

---

# 字段所有权

| 数据 | Single Source of Truth | 说明 |
|------|------------------------|------|
| Mental Model / Cheatsheet / Practice Log | Markdown | 用户正文，以文件内容为准。 |
| `id` / `slug` / `title` / `domain` / `type` | Markdown front matter | CLI 可修改，但必须写回 Markdown。 |
| `claimedLevel` | Markdown front matter + 事件 | CLI 修改时记录事件并同步 front matter。 |
| `freshness` / `readiness` | SQLite 派生 | 不写入 Markdown，由事件和时间推导。 |
| Edge | SQLite | 可导出，但不写入每个节点正文。 |
| ReviewRun | SQLite + JSON 文件 | Markdown 只保存摘要。 |
| Search index | SQLite | 可重建，不是权威数据。 |

必须提供维护命令：

```bash
syca sync
syca doctor
```

---

# 核心功能模块

## 1. 快速捕获

目标：不打断当前任务。

```bash
syca capture --cheat "awk '{print $1}' access.log | sort | uniq -c"
syca capture --note "今天排查日志时 awk 字段分隔符卡住了"
syca capture --link "https://example.com/shell-awk"
```

P0 中，`capture` 比 `add` 更重要。

## 2. Inbox 管理与升格

```bash
syca inbox
syca promote <capture-id>
syca archive <capture-id>
syca discard <capture-id>
```

升格时才要求用户思考：

- 这能否变成能力断言？
- 它属于哪个领域？
- Cheatsheet 是否足够？
- 是否需要补 Mental Model？

## 3. 标准化 Markdown 节点

正式节点仍使用标准 Markdown，保证非侵入和可迁移。

推荐区块：

- `Capability`
- `Mental Model`
- `Cheatsheet`
- `Practice Log`
- `Review Notes`
- `References`

## 4. 渐进式查询

```bash
syca query "awk" --cheat
syca show "shell-log-processing"
syca list --stale
```

默认查询优先展示能力断言、等级、新鲜度、Cheatsheet 摘要和最近实践，不直接倾倒整篇正文。

## 5. 同步与一致性检查

```bash
syca sync
syca doctor
```

这是 P0 核心功能。没有可靠同步，后续能力图和 Review 都不可信。

## 6. LLM 苏格拉底评审

```bash
syca review "shell-log-processing"
```

评审必须遵守：

- 不代写用户的 Mental Model。
- 不覆盖用户原文。
- 不把评审结果标记为“事实已验证”。
- 默认只发送必要内容，避免泄露私人 Practice Log。
- 保存结构化 ReviewRun。

## 7. 能力图与恢复视图

```bash
syca link docker linux --type prerequisite
syca status --domain shell
syca recover "docker-volume"
```

图和恢复视图不进入 P0，必须等捕获、升格、同步和查询稳定后再做。

---

# MVP 边界

## P0：最小可信闭环

| 功能 | 简述 | 状态 |
|------|------|------|
| Capture | 低摩擦保存命令、笔记、链接和片段。 | 已完成 |
| Inbox | 查看、归档、丢弃捕获项。 | 已完成 |
| Promote | 将 CaptureItem 升格为 AbilityNode。 | 已完成 |
| Markdown 节点模板 | 生成标准能力节点文件。 | 已完成 |
| SQLite 本地索引 | 保存捕获项、节点索引、事件和搜索数据。 | 已完成 |
| Query Cheatsheet | 快速查询正式节点中的 Cheatsheet。 | 已完成 |
| Sync / Doctor | 检查 Markdown 与 SQLite 一致性。 | 已完成 |

## P1：能力校准

| 功能 | 简述 | 状态 |
|------|------|------|
| ReviewRun | 结构化 LLM 评审和 JSON 归档。 | 已完成 |
| CapabilityEvent | 用事件推导 freshness 和 readiness。 | 已完成 |
| Practice Log 工具 | 快速追加实践记录。 | 已完成 |
| 手动 Link | 支持弱关系与可选 rationale。 | 已完成 |
| Stale View | 显示需要恢复的能力节点。 | 已完成 |

## P2：能力地图与恢复训练

| 功能 | 简述 | 状态 |
|------|------|------|
| Recover Drill | 重新解释或按 Cheatsheet 完成任务。 | 已完成 |
| Graph View | 终端 ASCII 能力图。 | 已完成 |
| Asset 引用 | 管理 PDF、图片、链接等资料。 | 暂缓 |
| 语义检索 | 在节点质量稳定后再评估。 | 暂缓 |

## 明确不做

| 功能 | 不做理由 | 什么时候可能做 |
|------|----------|----------------|
| Web 管理后台 | 会稀释核心学习循环。 | CLI 闭环稳定后 |
| 一键剪藏到正式库 | 会污染能力体系。 | 只允许进入 Inbox |
| 自动生成完整笔记 | 会削弱用户主动编码。 | 可生成评审建议，不生成最终正文 |
| 多端同步 | 当前目标是个人本地使用。 | 数据模型稳定后 |
| 插件系统 | 属于过早抽象。 | 出现多个稳定外部集成需求后 |
| RAG 问答 | 容易把产品导向查询数据库。 | 节点质量足够高且检索需求明确后 |

---

# 稳健技术栈

MVP 采用最少运行部件、最少外部依赖、最容易测试和备份的技术栈。

| 层面 | 选型 | 理由 |
|------|------|------|
| 语言 | Python 3.12+ | 文件处理、CLI、SQLite、测试和 LLM 集成都成熟。 |
| 包管理 | uv | 快速、可锁定依赖、适合现代 Python 项目。 |
| CLI | Typer | 基于类型标注，命令清晰，适合个人工具。 |
| 终端输出 | Rich | 表格、分区、颜色和状态展示稳定。 |
| 数据库 | SQLite | 本地优先、零运维、易备份。 |
| 数据访问 | sqlite3 + 小型 repository 封装 | MVP 避免 ORM 复杂度，等 schema 稳定后再评估。 |
| Markdown 元数据 | python-frontmatter 或等价轻量库 | 处理 YAML Front Matter，避免手写解析。 |
| Markdown 区块解析 | markdown-it-py 或自定义受限解析器 | P0 只解析固定二级标题，保持可控。 |
| 配置 | TOML | Python 标准库支持 `tomllib` 读取，格式清晰。 |
| 测试 | pytest | 覆盖核心逻辑、CLI 和文件一致性。 |
| LLM | Provider Adapter | P1 引入，默认 mock，本地功能不依赖网络。 |

暂不引入：

- FastAPI / 常驻服务。
- SQLAlchemy / Alembic。
- 向量数据库。
- 前端框架。
- 后台任务队列。
- 插件系统。

---

# 成功指标

| 指标 | 定义 | 短期目标 |
|------|------|----------|
| 捕获摩擦 | 从想到保存到完成命令的时间。 | 10 秒内完成一次 capture。 |
| Inbox 升格率 | CaptureItem 中被升格为 AbilityNode 的比例。 | 不追求高，10%-30% 即可。 |
| 查询恢复速度 | 从搜索到可复制 Cheatsheet 的时间。 | 常见节点 10 秒内定位。 |
| 节点可信度 | 正式节点是否包含能力断言、Cheatsheet 和至少一条实践线索。 | P0 节点 70% 以上。 |
| 同步可靠性 | 外部编辑 Markdown 后 `sync/doctor` 是否能发现并修复索引。 | 不丢失正文。 |
| Stale 可见性 | 过期能力是否被标记为需要恢复。 | P1 实现后可见。 |

---

# 风险与约束

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Capture 变成垃圾箱 | 高 | 高 | Inbox 与 AbilityNode 严格隔离；定期清理。 |
| 强制升格造成抗拒 | 高 | 高 | Capture 不强制升格；只提醒，不惩罚。 |
| SQLite/Markdown 脑裂 | 中 | 高 | 字段所有权、mtime/hash、sync/doctor。 |
| LLM 造成新幻觉 | 中 | 高 | ReviewRun 只表示挑战，不表示认证。 |
| 等级腐烂 | 高 | 中 | claimedLevel + freshness + CapabilityEvent。 |
| 技术栈过度复杂 | 中 | 高 | P0 禁止 Web、ORM、RAG、常驻服务。 |

约束条件：

- 单人项目，优先选择低运维技术。
- 本地优先，核心数据默认不离开本机。
- Markdown 必须可被普通编辑器读取。
- LLM 只能作为可选增强能力，不能成为基础功能硬依赖。
- 数据模型变更必须同步更新 `data-contracts.md`。

---

# 项目元信息

| 字段 | 内容 |
|------|------|
| **仓库位置** | `F:/Lab/Project_Sycamore` |
| **核心记忆目录** | `memory_bank/` |
| **当前主要用户** | 项目作者本人 |
| **协作方式** | 通过 memory bank 维护长期上下文 |
