# 路线图

> WARM 知识。涉及阶段规划、技术栈取舍、MVP 范围或优先级排序时读取。

---

# 北极星

Sycamore 的路线图围绕一个判断标准展开：

> 能否在不增加明显认知负担的前提下，把真实工作碎片逐步训练成**可理解、可恢复、可迁移**的能力网络？

因此，路线图不以"功能丰富度"为优先级，而以"学习—复习—迁移"三层循环的可靠性为优先级。

> 当前版本：**v0.11.1** — 已交付 P0–P2 核心 CLI，处于真实使用验证期。

---

# 产品架构：六层蓝图

Sycamore 的产品逻辑分为六层，外加跨层的 LLM 智能服务层：

| 层 | 名称 | 职责 | LLM 参与度 |
|:--|:--|:--|:--:|
| **第 0 层** | 数据真相层 | AbilityNode、Relation、Event、Derived State 的持久化与一致性 | 不依赖 |
| **第 1 层** | 输入与升格层 | 低摩擦捕获 → clarify → promote | 可选辅助（归类建议/标题备选） |
| **第 2 层** | 学习建模层 | 结构化 Mental Model、边界、对比、最小任务 | 可选辅助（复述检查/边界草稿） |
| **第 3 层** | 复习与恢复层 | FSRS 调度、Recover Drill、失败分类、薄弱画像 | 可选辅助（生成恢复问题） |
| **第 4 层** | 迁移与应用层 | 变式识别、边界判断、组合任务、真实场景 | 推荐辅助（生成变式场景） |
| **第 5 层** | 图谱与编排层 | 扩展关系、Path View、Cluster Risk、Transfer Bundles | 可选辅助（关系建议） |
| **LLM 层** | 智能服务层 | 横跨 1–5 层，提供草稿/追问/变式/批判/建议 | — |

**核心原则**：每一层的数据真相不依赖 LLM。LLM 只负责"建议、追问、草拟、变式、批判"，不负责"结构、状态、调度、真相、记录"。

---

# 技术栈原则

## 最稳健选择

| 层面 | 选型 | 采用时机 | 理由 |
|------|------|----------|------|
| 语言 | Python 3.12+ | 已用 | 标准库强、CLI 生态成熟、SQLite 和文件处理简单。 |
| 包管理 | uv | 已用 | 依赖锁定、速度快、项目结构清晰。 |
| CLI | Typer | 已用 | 类型标注友好，命令定义清楚。 |
| 终端 UI | Rich | 已用 | 表格、颜色、状态展示足够。 |
| 数据库 | SQLite | 已用 | 本地优先、零运维、可备份。 |
| 数据访问 | sqlite3 + repository 封装 | 已用 | 避免 ORM 在早期放大 schema 复杂度。 |
| Markdown 元数据 | python-frontmatter | 已用 | 处理 YAML Front Matter。 |
| Markdown 区块 | 固定标题解析 + 测试 | 已用 | 只解析受控结构。 |
| 配置 | TOML + `tomllib` | 已用 | Python 标准库可读，用户可手改。 |
| 测试 | pytest | 已用 | 覆盖文件、数据库、CLI 行为。 |
| **间隔重复** | **FSRS-5 算法** | **Phase 1** | 科学建模记忆稳定性(S)、难度(D)、可提取性(R)。 |
| LLM 集成 | Provider Adapter + mock first | 已用(部分) | 不让核心功能依赖网络和模型稳定性。 |

## 暂不采用

| 技术 | 暂不采用原因 | 重新评估条件 |
|------|--------------|--------------|
| 后台 daemon / 常驻服务 | 增加跨平台运行和调试成本。Phase 1–3 为纯 CLI 手动触发。 | 需要自动推送复习提醒或文件监听时。 |
| FastAPI | 常驻服务会增加部署和状态复杂度。 | GUI 或第三方集成真正需要 API。 |
| SQLAlchemy / Alembic | 早期 schema 会频繁变动，ORM 迁移成本偏高。 | SQLite 表稳定并出现复杂查询。 |
| 向量数据库 | 会把产品推向查询系统，偏离能力训练。 | 节点质量足够高，且关键词检索明显不够。 |
| Web 前端 / GUI | 会稀释 CLI 核心循环的可靠性。 | CLI 日常使用稳定后。 |
| 插件系统 | 过早抽象。 | 出现 3 个以上稳定外部集成需求。 |

---

# 路线总览

```text
Phase 1A-0 ── NodeType 基础设施
Phase 1A ── Recover 改造（提取优先）
Phase 1B ── Scheduler 引入
       ↓
Phase 2  ── 学习建模层 + Clarify + Edit 引导
       ↓
Phase 3  ── 迁移与应用层
       ↓
Phase 4  ── 图谱增强（先服务迁移层）
       ↓
Phase 5  ── LLM 服务扩展与资产层候选
```

> Phase 1A 和 1B 分开是为了把"产品机制变化"（recover 改造）和"算法变化"（FSRS 调度器）解耦——
> 前者用户直接感知，后者工程风险更高，拆开验证更稳。

---

# Phase 0：历史交付（已完成）

> 当前状态：**v0.12.0** — P0–P2 全部交付，Phase 1A-0 / 1A 完成

## 已完成的阶段

| 阶段 | 版本 | 核心交付 |
|:--|:--:|:--|
| 文档与契约校准 | — | project-brief / architecture / data-contracts / conventions 基线定型 |
| P0 最小闭环 | v0.5.0 | init → capture → inbox → promote → query → sync → doctor |
| P0.7 Promote 增强 | v0.9.0 | --latest / --index / UUID 前缀 |
| P1 能力校准 | v0.10.0 | ReviewRun / mock+DeepSeek Provider / practice / stale / level set |
| P2 恢复与关系 | v0.11.1 | recover / link / graph / status --domain |
| Phase 1A-0 | v0.11.2 | NodeType 枚举 / 四种模板 / promote --type / schema v2 |
| Phase 1A | v0.12.0 | recall-first recover / fail-type / ratings / status --weak |

## 当前已有功能清单

```bash
# 第 0 层 — 数据真相
syca init                    # 初始化 SQLite + config + 目录
syca sync                    # Markdown → SQLite 索引同步
syca doctor                  # 一致性检查

# 第 1 层 — 捕获与升格
syca capture --note/--cheat/--link   # 低摩擦捕获
syca inbox                   # 查看 Inbox
syca promote [--latest|--index|<id>] # 升格为节点

# 第 2 层 — 学习建模（基础）
（节点模板含 Core Idea + Boundaries 占位，需手写）

# 第 3 层 — 复习（基础）
syca recover <node> [--pass|--fail]  # 恢复演练
syca status --stale          # 列出久未活动节点
syca review <node>           # LLM 批判性评审

# 第 4 层 — 迁移（暂无）

# 第 5 层 — 图谱（基础）
syca link <source> <target> --type   # 建关系
syca graph --domain <name>    # ASCII 能力图
syca status --domain <name>   # 域内新鲜度

# 跨层 — 等级与事件
syca practice <node>          # 追加实践记录
syca level set <node> L0-L3   # 调整等级
```

---

# Phase 1A-0：NodeType 基础设施

> **目标**：落地四种节点类型（Capability / Concept / Theorem / Process），让后续 recover、review、transfer 具备类型感知能力。
>
> 估算周期：**0.5 周** | 纯数据模型 + 模板 + CLI 参数，不改变现有命令语义

## 为什么在 Phase 1A 之前做？

Phase 1A 的 recover recall-first prompt 因类型而异（Capability 问步骤、Concept 问核心主张、Theorem 问直觉推导、Process 问机理），Phase 1B 的 FSRS 调度器需要按类型调整初始参数。没有 NodeType，后续所有阶段都要走"统一措辞"的妥协方案。

## 核心命令

```bash
syca promote <id> --type capability   # 默认，操作能力
syca promote <id> --type concept      # 概念框架
syca promote <id> --type theorem      # 定理模型
syca promote <id> --type process      # 系统机制
```

不指定 `--type` 时默认 `capability`，保证向后兼容。

## 交付物

### NodeType 枚举

- `sycamore/models/enums.py` 新增 `NodeType` StrEnum
- 四种值：`capability` / `concept` / `theorem` / `process`
- 每种类型携带：适用领域、核心关注点、考核方式（见 `data-contracts.md`）

### AbilityNode 模型扩展

- `AbilityNode` dataclass 新增 `node_type: str` 字段
- 默认值 `"capability"`

### SQLite Schema v2

- `ability_nodes` 表新增 `node_type TEXT NOT NULL DEFAULT 'capability'`
- `SCHEMA_VERSION` 升至 2
- 现有数据库 `sync` 时自动补齐默认值（不强制迁移）

### Markdown 模板

- 四种 `promote` 模板：`capability`（Steps/Pitfalls/Cheatsheet）、`concept`（Core Thesis/Historical Context/Critique/Apply To）、`theorem`（Formula/Intuition/Boundary Conditions/Counterexamples）、`process`（Mechanism/Parameters/Disturbance Response）
- Front matter 新增 `type: "capability"` 字段
- `sync` 从 front matter 读取 `type` 写入 `ability_nodes.node_type`
- `doctor` 校验 `type` 为合法枚举值

### promote_service 扩展

- 根据 `--type` 选择对应模板
- 种子化区块按类型差异化

## 退出标准

- `promote --type` 四种类型各自生成不同模板结构
- `sync` 正确将 front matter `type` 写入 SQLite
- `doctor` 报告非法 `type` 值
- 现有节点（无 `node_type`）sync 后默认设为 `capability`
- 测试覆盖：四种模板生成、sync 默认值、doctor 非法 type
- **Phase 1A-0 完成即发版**，版本号升至 **v0.11.2**

## 不做

- 不改动现有 capture / inbox / query / status 逻辑
- 不引入 interactive clarify（那是 Phase 2）
- 不改变 recover / review 的现有行为（类型感知留到 Phase 1A/1B）

---

# Phase 1A：Recover 改造（提取优先）

> **目标**：把 recover 从"展示后自评"升级为"先提取、再对照、分类失败"。
>
> 估算周期：**1 周** | 纯产品机制变化，不引入算法复杂度，用户直接感知

## 为什么先做这一层？

当前 recover 直接展示 Mental Model + Cheatsheet，用户读完即标记 --pass。这在认知科学上属于"再认"（recognition），不是"提取"（recall）。没有提取训练，后续任何间隔重复算法（包括 FSRS）都无法发挥作用——因为你从未真正检测过"是否记得"。

## 核心命令

```bash
syca recover <node>                # 新默认模式：recall-first
syca recover <node> --mode recall-first  # 只展示标题+线索
syca recover <node> --mode supported     # 展示局部提示
syca recover <node> --mode full          # 完整展示模式（旧行为）
syca recover <node> --hard         # 评级：记得但费力
syca recover <node> --easy         # 评级：轻松回忆
syca recover <node> --fail-type concept   # 失败类型：原理没懂
syca recover <node> --fail-type recall    # 失败类型：记不起来
syca recover <node> --fail-type procedure # 失败类型：步骤混乱
syca recover <node> --fail-type transfer  # 失败类型：一换场景不会
syca status --weak                 # 薄弱画像：常 fail 的节点/领域
```

## 交付物

### Recover 模式改造

- `--mode recall-first`（新默认）：只展示标题 + 等级 + 一句话线索
  用户尝试回忆后按任意键，再展开完整 Mental Model + Cheatsheet 对照
- `--mode supported`：展示标题 + 部分 Cheatsheet（作为提示）
- `--mode full`：当前行为 — 直接展示全部内容（保留为 fallback）
- 保留 `--pass` / `--fail`，新增 `--hard` / `--easy` 完整四级评分

### Fail-type 分类

- `--fail-type` 参数：`recall` / `concept` / `procedure` / `transfer`
- 存入 `capability_events` 的 `payload_json`，可被后续薄弱画像和调度器分析
- CLI 输出具体失败类型（"Recall Failed" / "Concept Failed" / …），而不仅是"Failed"

### 薄弱画像

- `syca status --weak`：分析各节点/各领域的失败类型分布
- 输出：`Node` / `Fail Count` / `Top Fail Type` / `Risk Level`
- 基于 Phase 1A 期间收集的 fail-type 数据，不依赖调度器

## 退出标准

- `--mode recall-first` 在展示答案前先要求用户尝试回忆
- `--fail-type` 记录在 `capability_events.payload_json` 中
- `syca status --weak` 能展示失败模式分布
- 测试覆盖：三种 recover 模式、fail-type 持久化、weak 列表
- **Phase 1A 完成即发版**，版本号升至 **v0.12.0**

## 不做

- 不改动 capture / promote / sync / doctor 现有逻辑
- 不引入调度器（在 Phase 1B 独立交付）
- 不删除 `status --stale`（标记为 legacy，在 Phase 1B 完成后评估）

---

# Phase 1B：Scheduler 引入（FSRS 驱动）

> **目标**：用 FSRS-5 算法科学驱动间隔重复，通过 `syca schedule` 手动获取到期复习项。
>
> 估算周期：**1.5–2 周** | 纯算法工程，成本集中在公式实现和状态持久化

## 为什么拆成独立 Phase？

Phase 1A 改的是"用户怎么 recover"（产品机制），Phase 1B 改的是"系统怎么决定什么时候 recover"（算法调度）。两者解耦后：（1）1A 可以独立验证提取模式是否被接受；（2）1B 的算法可以独立调试和测试；（3）如果 FSRS 实现复杂度过高，可以降级为更简单的调度策略而不影响 1A 的成果。

## 双轨过渡策略

> 旧 freshness 系统和新 scheduler 在 Phase 1B **并行运行**，不立即替换。

- `status --stale` 保留并标记为 `[legacy]`——仍基于 30 天阈值
- `syca schedule` 作为新入口——基于 FSRS 的 S、R、due_at
- 两者输出独立、互不覆盖
- 在 Phase 2 或 Phase 3 确认 scheduler 行为稳定后，再评估是否淡出 freshness

**原因**：减少用户心智突变、降低调试复杂度、避免旧命令语义突然失效。

## FSRS 映射关系

| FSRS 概念 | Sycamore 映射 | 说明 |
|:--|:--|:--|
| Card | AbilityNode（整个节点视为一个复习单元） | 每个节点有独立的 FSRS 状态 |
| Rating 1 (again) | `recover --fail` | 忘记录入（在 Phase 1A 已实现） |
| Rating 2 (hard) | `recover --hard` | 记得但费力（在 Phase 1A 已实现） |
| Rating 3 (good) | `recover --pass` | 正常回忆（在 Phase 1A 已实现） |
| Rating 4 (easy) | `recover --easy` | 轻松回忆（在 Phase 1A 已实现） |
| Stability (S) | 每节点 S 值 | S=30 表示 30 天后 R≈90% |
| Difficulty (D) | 每节点 D 值 | [1,10]，越高越难 |
| Retrievability (R) | 实时计算 | 由 S 和距上次天数推导 |
| Desired Retention | `config.toml` 配置 | 默认 90% |
| 调度触发器 | `syca schedule`（手动命令） | 无后台 daemon |

## 核心命令

```bash
syca schedule                       # 列出今天到期的复习项（按 R 升序）
syca schedule --domain shell        # 筛选领域
syca schedule --limit 10            # 控制单次输出量
```

（recover 的四级评分和 fail-type 已在 Phase 1A 实现，Phase 1B 直接利用。）

## 交付物

### FSRS 引擎（纯 Python 实现）

- `sycamore/core/scheduler.py`：实现 FSRS-5 核心算法（与 Anki 当前稳定版对齐）
  - **遗忘曲线** `R(t, S)` — 给定 S 和距上次天数 t，计算当前可提取概率
  - **回忆后新稳定性** `S'r` — 成功回忆后 S 的增长取决于 D、S、R 和评分 G
  - **遗忘后稳定性** `S'f` — 按 again 后 S 重置为 post-lapse stability
  - **难度更新** `D'` — 每次 review 后 D 向均值回归（避免 ease hell）
  - **首次初始化** `S0(G)`、`D0(G)` — 根据首次评分确定初始 S 和 D
  - **下次间隔** `I(r, S)` — 根据期望保留率 r 和 S 计算下次到期天数
  - 19 个默认参数（FSRS-5 官方默认值，与 Anki 一致）
- 四级评分输入（来自 Phase 1A 的 recover rating）
- 延迟复习处理（overdue review 按遗忘曲线正确计算当前 R 值）
- 无外部依赖，纯数学运算

### FSRS 状态存储

- 新增 SQLite 表 `node_scheduler_state`：
  ```sql
  CREATE TABLE node_scheduler_state (
      node_id TEXT PRIMARY KEY,
      stability REAL NOT NULL DEFAULT 0,
      difficulty REAL NOT NULL DEFAULT 5.0,
      due_at TEXT,               -- 下次到期时间
      last_review_at TEXT,       -- 上次复习时间
      last_rating INTEGER,       -- 上次评级 (1-4)
      review_count INTEGER DEFAULT 0,
      lapse_count INTEGER DEFAULT 0,
      FOREIGN KEY (node_id) REFERENCES ability_nodes(id) ON DELETE CASCADE
  );
  ```
- 节点首次 `recover`（任意 rating）时初始化 FSRS 状态
- 每次 recover 后更新 S、D、due_at
- `syca sync` 不覆盖 FSRS 状态（属于 SQLite 派生领域）

### syca schedule 命令

- 查询 `node_scheduler_state` 中 `due_at <= now` 的节点
- 按 R 升序排列（遗忘概率最高的优先）
- Rich 表格输出：`#`、`Title`、`Domain`、`Level`、`R%`、`Due`、`Overdue`
- `config.toml` 新增 `[scheduler]` 段：

  ```toml
  [scheduler]
  desired_retention = 0.9    # 期望保留率，默认 90%
  max_per_session = 20       # 单次 schedule 最大返回数
  ```

## 退出标准

- 新 promote 的节点在首次 `recover` 后自动获得初始 S/D 状态
- `syca schedule` 能根据 FSRS 状态正确排序到期节点
- 连续三次 `--pass` 后间隔显著拉长（验证 FSRS 核心行为）
- `--fail` 后间隔缩短，且 S 值重置为 post-lapse stability
- `syca schedule` 和 `syca status --stale [legacy]` 同时可用
- 测试覆盖：FSRS 核心公式、状态持久化、schedule 排序、延迟复习
- **Phase 1B 完成即发版**，版本号升至 **v0.13.0**

## 不做

- 不做后台推送（纯 CLI 手动 `syca schedule`）
- 不引入 FSRS 参数优化（使用 FSRS-5 默认参数，后续再评估）
- 不删除 `status --stale`（双轨过渡，Phase 2+ 再评估）

---

# Phase 2：学习建模层 + Edit 引导 + Clarify

> **目标**：让节点从"模板占位"变成"有结构、有类型、有引导、可验证完成度的可解释能力单元"。
>
> 估算周期：**2–3 周**

## 动机

当前节点模板只有 `Core Idea` + `Boundaries` 两个结构化块，且 `promote` 后直接落到空白 Markdown，没有引导流程。这导致很多节点止步于模板占位，从未真正完成"编码"。

真正决定"学新阶段是否成立"的，不是有没有归类成功（clarify），而是用户有没有把节点写成**可解释、可对比、可验证**的能力单元。因此 Phase 2 的主功能是 `edit`（结构化编辑引导），`clarify` 是辅助功能（帮助 capture → promote 的节点成形）。

## 核心命令

```bash
# 主功能：edit — 结构化编辑引导（Phase 2 核心）
syca edit <node>                   # 按区块逐步引导填写
syca check <node>                  # 检查节点完成度（draft/modeled/contrasted/reviewable）

# 辅助功能：clarify — 帮助 capture → promote 成形
syca clarify <capture-id>          # 归类引导 + 能力断言草稿

# 升格时指定节点类型
syca promote <id> --type capability
syca promote <id> --type concept
syca promote <id> --type theorem
syca promote <id> --type process
```

## 交付物

### edit 命令（主功能）

- `syca edit <node>` 按区块逐步引导：
  1. 先写一句话解释（Core Idea）
  2. 写它解决什么具体问题（Problem It Solves）
  3. 写一个反例或误用场景（Boundaries）
  4. 写容易混淆的概念及区分方法（Contrast）
  5. 写最小验证任务（Minimal Task）
  6. 判断自己当前 claimed level
- 每个步骤输出提示性问题和示例，用户输入后写入 Markdown
- 支持 `--block` 参数单独编辑某个区块（如 `--block contrast`）
- 支持跳过（不强制填完所有区块）

### clarify 命令（辅助功能）

- 位于 `capture` 和 `promote` 之间（非必选，可用 `--no-interactive` 跳过）
- 交互式问三个问题：
  1. 这是操作能力、概念框架、定理模型还是系统机制？→ 建议 `--type`
  2. 它解决什么具体问题？→ 建议能力断言草稿
  3. 你现在是"看懂了"还是会"自己做了"？→ 建议初始 claimed level
- 根据回答生成更准确的 promote 参数建议，但不强制采纳

### 节点类型模板

每种类型有不同的 Markdown 模板结构与考核方式（详见 `data-contracts.md` NodeType 枚举）：

| 类型 | 适用领域 | 核心区块 | 考核方式 |
|:--|:--|:--|:--|
| `capability` | IT、软件操作、外语 | 步骤 / 坑点 / Cheatsheet | 给定场景下能否正确执行？ |
| `concept` | 哲学、历史、经济、管理 | 核心主张 / 历史语境 / 批判 | 能否用该框架分析新事件？ |
| `theorem` | 数学、物理、算法 | 公式 / 直觉推导 / 极值边界 | 边界失效时能否识别反例？ |
| `process` | 化工、机械、生物 | 机理 / 参数妥协 / 物理安全 | 外部扰动时如何调节参数？ |

### 扩展 Mental Model 固定块

所有节点类型共享的区块：

- **Core Idea**：用自己的话解释本质（已有，保持）
- **Problem It Solves**：它解决什么问题（新增）
- **Boundaries**：适合/不适合/易误用（已有，保持）
- **Contrast**：与什么容易混淆，如何区分（新增）
- **Minimal Task**：最小可验证任务（新增）
- **Cheatsheet**：低频但实操必要的操作片段（已有，保持）

### 节点完成度（Completion State）

每个节点有明确的完成度状态，决定是否可进入复习和迁移：

| 状态 | 含义 | 条件 | 能否 recover/review | 能否 transfer |
|:--|:--|:--|:--:|:--:|
| `draft` | 刚 promote，关键区块仍为占位 | Core Idea 仍为模板占位文本 | ❌ | ❌ |
| `modeled` | 已完成核心建模 | Core Idea + Problem + Boundaries + Minimal Task 已非占位 | ✅ | ❌ |
| `contrasted` | 已完成对比校准 | 含 Contrast 且不为空 | ✅ | ✅（仅 A/B 层） |
| `reviewable` | 达到可高质量复习的质量 | modeled + contrasted + Cheatsheet 非空 | ✅ | ✅ |

- `syca check <node>` 输出当前完成度状态和缺失区块清单（非强制）
- `syca status` 可筛选 `--completion draft|modeled|contrasted|reviewable`
- 调度器和迁移层可基于完成度过滤节点（draft 不出现在 schedule 中；transfer 仅对 contrasted+ 生效）

## 退出标准

- `clarify` 能在 capture 和 promote 之间正确归类节点类型
- `promote --type capability|concept|theorem|process` 生成不同的模板结构
- `syca edit <node>` 按区块引导填入，每个区块之前展示提示问题
- `syca check <node>` 正确报告完成度状态和缺失区块
- 四类节点类型的 Markdown 模板均包含 `Contrast` 和 `Minimal Task`
- 测试覆盖：edit 引导流程、check 完成度判断、四种模板结构、completion state 过渡
- 版本号升至 **v0.14.0**

---

# Phase 3：迁移与应用层

> **目标**：让知识从"会复习"走向"会用"——变式识别、边界判断、组合任务。
>
> 估算周期：**3–4 周**

## 动机

Sycamore 当前的最高能力等级 L3 定义为"能迁移场景"，但没有对应的工具支撑迁移训练。用户不知道"会了"在 L3 意味着什么，也无法主动训练迁移。

## 核心命令

```bash
syca transfer <node>                 # 新：生成变式场景
syca challenge <node>                # 新：边界判断/组合任务
syca transfer <node> --mode compose  # 组合任务模式
syca challenge --domain shell        # 域内随机挑战
```

## 交付物

### transfer 命令

- 给出不显式点名知识点的场景，让用户自己判断用什么能力
- 分层输出：

| 层 | 类型 | 示例 |
|:--|:--|:--|
| A | 变式识别 | "想确认目录中哪些文件是隐藏的"（而不是直接问 `ls -la`） |
| B | 边界判断 | "已经知道目录里有什么，但想查看文件内容，继续用 `ls` 对吗？" |
| C | 组合任务 | "进入项目 → 确认路径 → 找出最近修改的日志 → 查看前 20 行" |
| D | 真实场景 | "排查为什么服务起不来：看日志 → 查端口 → 查进程 → 读配置" |

- 用户完成后果断记录 Event：

  ```python
  CapabilityEventType.TRANSFER_SUCCESS
  CapabilityEventType.TRANSFER_PARTIAL
  CapabilityEventType.TRANSFER_FAIL
  TRANSFER_FAIL_WRONG_SELECTION
  TRANSFER_FAIL_WRONG_COMPOSITION
  ```

### challenge 命令

- 基于图谱自动组装挑战：
  - 有 prerequisite 链时生成组合任务
  - 有 contrast 边时生成对比判断题
  - 有 composition 边时生成管道/搭配题
- `--domain` 参数跨节点出题

### 迁移结果反馈

- transfer/challenge 完成后记录到 `capability_events`
- FSRS 调度器可感知迁移失败：连续 transfer fail → 降级节点新鲜度
- `syca status --weak` 纳入 transfer 数据

### 迁移结果影响等级（Evidence Gap）

迁移不只是"练习"，它是 claimed level 是否可信的核心证据：

- **L3 必须有足够的 transfer success 证据**：没有 → 在 `status` 中高亮为 `claimed L3, not evidenced`
- **L2 至少需要 A/B 层迁移成功**：没有 → 标记为 `claimed L2, low transfer evidence`
- `syca status <node>` 输出 claimed level 与 evidence level 的差异（evidence gap）：
  - 当 claimed level 与 recover/transfer 数据矛盾时，输出 `[!] evidence gap` 标记

这与 `risk-gate.md`（风险门控）中的"等级制度与现实脱节"一致：recover + transfer 数据共同构成 evidence level。

## 退出标准

- `transfer <node>` 能生成至少 A/B 两层场景
- `challenge <node>` 在节点有 prerequisite 边时生成组合任务
- 迁移结果事件正确存入 SQLite
- 迁移失败影响 FSRS 调度
- `syca status <node>` 对 L3 节点展示 claimed vs transfer evidence 的 gap
- 版本号升至 **v0.15.0**

---

# Phase 4：图谱增强（先服务迁移层）

> **目标**：把能力图从"静态展示"变为迁移训练的基础设施——先做三种最直接服务迁移层的边类型，不做全语义图谱。
>
> 估算周期：**2–3 周**（缩边后大幅减少）

## 为什么先缩边？

图谱层的真正价值在 Phase 3（迁移）中已经显现：transfer/challenge 需要 composition 边来组装合任务，需要 contrast 边来生成对比判断题，需要 diagnostic 边来生成排障链。最务实的方式是先只做这三种**直接服务迁移层**的边类型，让图谱成为迁移训练的基础设施，而不是一个很全的知识语义系统。

## 核心命令

```bash
syca link <source> <target> --type contrast       # 新增：建混淆关系
syca link <source> <target> --type composition    # 新增：建组合关系
syca link <source> <target> --type diagnostic     # 新增：建排障关系
syca path --domain shell              # 新：学习路径展示
syca status --cluster-risk            # 新：薄弱簇检测
```

## 交付物

### EdgeType 扩展（核心 3 种）

从当前的 5 种**增量**引入 3 种直接服务迁移层的边类型：

| EdgeType | 含义 | 服务什么迁移功能 |
|:--|:--|:--|
| `contrast` | 容易混淆，需要区分 | Phase 3：challenge 生成对比判断题 |
| `composition` | 常组合使用（管道/搭配/顺序依赖） | Phase 3：transfer `--mode compose` 组装组合任务 |
| `diagnostic` | 故障排查链（现象→定位→解决） | Phase 3：challenge `--mode diagnose` 生成排障题 |

（`contrasts_with` 重命名为 `contrast`，保持 CLI 短命名风格。）

**延后**（不进入 Phase 4）：
- `alternative` — 与迁移训练无直接关系，纯语义表达
- `scenario` — 可用 tag 或 domain 替代，不需要单独边类型
- `similar_pattern` — 已有但使用率低，保留不动，不扩展

### Path View

- `syca path --domain shell`：
  - 展示域内 prerequisite + composition 链（学习 + 组合路径）
  - 用 `→` 链式展示："节点A → 节点B → 节点C"
  - 标注每个节点的 learning state（未学/学习中/已掌握/常忘）

### Cluster Risk

- `syca status --cluster-risk`：
  - 分析域内节点簇的 recover fail / transfer fail 密度
  - 当一个 domain 或一个 prerequisite + composition 链中出现大量 fail 时，标记为薄弱簇

## 退出标准

- 新增的 3 种 EdgeType 可正常建边和在图谱中展示
- `syca path --domain` 输出正确的 prerequisite 路径
- Cluster Risk 能基于 recover + transfer 数据辨识薄弱簇
- Phase 3 的 transfer/challenge 可利用 `contrast`、`composition`、`diagnostic` 边生成对应题目
- 版本号升至 **v0.16.0**

---

# Phase 5：LLM 服务扩展与资产层候选

> **启动条件**：Phase 1–4 成为日常使用工具，且出现明确的瓶颈。
>
> LLM 服务扩展按需推进，资产层候选不承诺全部实现。

## LLM 服务扩展

汇聚 Phase 1–4 中分散在各层的 LLM 辅助能力：

| 能力 | 服务层 | 实现方式 |
|:--|:--|:--|
| Capture 归类建议 | 第 1 层 | 新增 provider 方法，轻量 prompt |
| 标题备选生成 | 第 1 层 | 新增 provider 方法 |
| Core Idea 复述检查 | 第 2 层 | 新增 provider 方法 |
| 恢复问题生成 | 第 3 层 | 新增 provider 方法 |
| 变式场景生成 | 第 4 层 | 新增 provider 方法 |
| relation 建议 | 第 5 层 | 新增 provider 方法 |

所有 LLM 能力在 `enabled = false` 时自动降级为 mock 或提示文案。

## 资产层候选

| 方向 | 说明 | 启动信号 |
|:--|:--|:--|
| 资产引用与去重 | 管理 PDF、图片、链接等资产，内容 Hash 去重 | 节点中引用外部文件的需求增多 |
| 备份与恢复 | `syca backup create/restore` | 用户开始担心数据丢失 |
| 文件监听自动 sync | watchdog 监听 `nodes/` 目录变化 | 用户频繁在外部编辑器中修改节点 |
| Obsidian 兼容视图 | 节点文件可直接在 Obsidian 中浏览 | 用户日常在 Obsidian 中工作 |
| CLI 交互式 TUI | 基于 Textual 的增强交互 | CLI 纯表格模式已不够直观 |
| 语义检索 | 轻度 RAG 或 embeddings 搜索 | 关键词检索出现明确瓶颈 |
| FSRS 参数优化 | 基于用户历史 review 数据优化 19 个默认参数 | 积累 1000+ review 事件后 |
| 扩展 EdgeType（alternative/scenario） | 在 Phase 4 中延后的边类型 | contrast/composition/diagnostic 使用稳定后 |

---

# 风险门控

| 风险 | 观察信号 | 停止条件 | 应对 |
|:--|:--|:--|:--|
| FSRS 过于学术化 | 调度器复杂度超出 CLI 工具的直觉预期 | Phase 1 开发中发现公式实现不可控 | 先降级为 SM-2（Anki 旧算法），FSRS 作为 P2 候选 |
| Recover 改 recall-first 后用户抵触 | 用户认为"不给答案我记什么" | Phase 1 验收时用户明确反对 | 保持 `--mode full` 作为 fallback，默认不改 |
| Clarify 变成形式主义流程 | 用户每次都 `--no-interactive` 跳过 | 引导流程使用率 < 20% | 删除 clarify 命令，仅保留节点类型模板 |
| Inbox 持续堆积不升格 | 大量 capture 不进入正式节点 | Inbox > 200 条且无清理机制 | 实现 archive/discard + 定期清理提醒 |
| SQLite / Markdown 脑裂 | sync 或 doctor 发现 hash 不一致 | 出现正文丢失风险 | 暂停新功能，优先修复存储层 |
| 技术栈膨胀 | 引入外部依赖超出当前最小集合 | Phase 1–5 中任意阶段引入不必要的第三方库 | 回退到纯 Python + SQLite |
| 等级制度与现实脱节 | L2 节点长期无实践、L3 无迁移证据 | recover 数据与 claimed level 明显矛盾 | 在 `status` 中高亮 "claimed vs evidence" 差异 |

---

# 版本策略

## 已完成的版本路线

| 版本 | 阶段 | 核心交付 |
|:--:|:--|:--|
| 0.2.0 | — | memory bank 初始文档 |
| 0.3.0 | P0 | CLI 骨架、capture、inbox |
| 0.4.0 | P0 | promote、Markdown 节点 |
| 0.5.0 | P0 | sync、doctor、query |
| 0.6.0 | P1 | ReviewRun、review CLI |
| 0.7.0 | P1 | practice、stale、level set |
| 0.8.0 | P1 | reviews 管理、Provider 工厂 |
| 0.9.0 | P0.7 | promote 短入口 |
| 0.10.0 | P1.4 | DeepSeek Provider |
| 0.11.0 | P2 | recover、link、graph |
| 0.11.1 | P2 | graph ASCII 树、文档更新 |

## 规划中的版本路线

| 版本 | 阶段 | 核心交付 |
|:--:|:--|:--|
| **0.12.0** | **Phase 1A** | recover 三层模式、hard/easy 四级评分、fail-type、status --weak |
| **0.13.0** | **Phase 1B** | FSRS 引擎、`node_scheduler_state` 表、`syca schedule`、freshness 双轨 |
| 0.14.0 | Phase 2 | edit 引导、check 完成度、节点类型模板、clarify、completion state |
| 0.15.0 | Phase 3 | transfer、challenge、迁移事件、evidence gap（claimed vs evidenced level） |
| 0.16.0 | Phase 4 | contrast/composition/diagnostic 边、Path View、Cluster Risk |
| 0.17.0+ | Phase 5 | LLM 服务扩展、资产层候选 |

## 1.0.0 的条件

- Phase 1A+1B（复习层+调度器）在日常使用中足够可靠
- Phase 2（学习层）的 edit 引导和 completion state 能产生高质量节点
- Phase 3（迁移层）能稳定产出 transfer/challenge 并影响 evidence gap
- 不丢失用户正文
- Markdown 节点格式稳定
- SQLite schema 迁移策略稳定
- 测试覆盖核心路径

---

# 相关文档

| 文档 | 用途 |
|:--|:--|
| `memory_bank/project-brief.md` | 核心愿景、第一性原理、产品边界 |
| `memory_bank/architecture.md` | 技术栈、目录结构、核心流程 |
| `memory_bank/data-contracts.md` | 实体定义、SQLite 表、CLI 契约 |
| `memory_bank/conventions.md` | 代码规范、命名约定、版本规则 |
| `memory_bank/active-task.md` | 当前任务 Check-list |
| `memory_bank/progress.md` | 历次会话摘要 |
| `memory_bank/manuals/real-world-validation-guide.md` | Phase 1 之前的端到端验收手册（v0.11.1） |
