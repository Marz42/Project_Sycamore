# 项目术语表

> COLD 知识。遇到不理解的专有名词或缩写时查阅，防止 Agent 理解偏差。

---

# 业务术语

| 术语 | 英文 | 含义 | 备注 |
|------|------|------|------|
| 能力校准 | Capability Calibration | 判断自己对某项能力掌握到什么程度，以及边界在哪里。 | Sycamore 的核心目标之一。 |
| 能力恢复 | Capability Recovery | 一段时间未使用某项能力后，通过心智模型和 Cheatsheet 快速恢复判断与操作。 | 比“复习”更强调重新上手。 |
| 快速捕获 | Capture | 在不中断当前任务的情况下保存命令、片段、链接、问题或想法。 | P0 的真实入口。 |
| 捕获项 | CaptureItem | 尚未升格为正式能力节点的低摩擦输入。 | 属于 Inbox。 |
| 渐进式升格 | Progressive Promotion | 将少数有价值的 CaptureItem 整理为 AbilityNode。 | 反囤积原则的实现方式。 |
| Inbox | Inbox | 临时存放 CaptureItem 的缓冲区。 | 可以脏乱，但不能冒充能力库。 |
| 能力断言 | Capability Statement | 用一句话描述“我能做什么/解释什么/排查什么”。 | 节点标题应尽量采用这种形式。 |
| 能力节点 | Ability Node | Sycamore 的最小知识单位，表示一项可校准、可恢复、可实践的能力。 | 不等同于百科词条。 |
| 能力图 | Capability Graph | 能力节点及其关系构成的图状结构。 | 可用技能树视图展示，但底层不是严格树。 |
| 能力事件 | CapabilityEvent | 记录捕获、升格、实践、查询、评审、恢复等行为的事件。 | 用于推导 freshness。 |
| 新鲜度 | Freshness | 能力当前是否仍可直接调用，是否需要恢复。 | 不等同于历史等级。 |
| 心智模型 | Mental Model | 用户用自己的话描述的原理、机制、边界、类比和判断框架。 | 应进入大脑的部分。 |
| 速查表 | Cheatsheet | 低频但实操必要的命令、配置、参数和片段。 | 适合交给工具保存。 |
| 实践记录 | Practice Log | 用户真实使用某项能力的证据，包括场景、操作、结果和踩坑。 | 用于校准等级。 |
| 评审记录 | Review Notes | LLM 或用户对 Mental Model 的批判性反馈和后续修订摘要。 | 不代表事实认证。 |
| 评审运行 | ReviewRun | 一次不可变、结构化保存的 LLM 评审。 | 替代一次性聊天记录。 |
| 反囤积原则 | Anti-Hoarding Principle | 拒绝把未经编码和实践的资料大量丢进系统。 | 防止退化为资料库。 |
| 渐进式披露 | Progressive Disclosure | 默认展示高层摘要，需要时再展开细节。 | 用于查询体验。 |

---

# 技术术语

| 术语 | 缩写 | 含义 | 备注 |
|------|------|------|------|
| 命令行界面 | CLI | 用户通过终端命令使用系统。 | MVP 主界面。 |
| 本地优先 | Local First | 核心数据默认保存在用户本机。 | LLM 调用是显式可选行为。 |
| 内容寻址 | Content Addressing | 通过文件 Hash 管理资产，实现去重和稳定引用。 | P0 不实现完整能力。 |
| Front Matter | Front Matter | Markdown 文件顶部的 YAML 元数据块。 | 用于节点轻量元数据。 |
| SQLite FTS | FTS | SQLite Full-Text Search，全文检索能力。 | 可用于本地搜索。 |
| Provider Adapter | Provider Adapter | 对不同 LLM 厂商的统一适配层。 | 避免业务层绑定具体模型。 |
| ADR | Architecture Decision Record | 架构决策记录。 | 见 `decisions.md`。 |

---

# 命名约定

| 名称 | 含义 | 示例 |
|------|------|------|
| `CaptureItem` | 低摩擦捕获项 | `CaptureItem(kind="cheat")` |
| `AbilityNode` | 能力节点领域模型 | `AbilityNode(title=...)` |
| `AbilityEdge` | 能力节点关系 | `prerequisite` |
| `CapabilityEvent` | 能力相关事件 | `cheatsheet_queried` |
| `ReviewRun` | 一次结构化 LLM 评审运行 | `mentalModelHash` |
| `reviewStatus` | 节点评审状态 | `challenged` |
| `claimedLevel` | 用户声明或历史达到的能力等级 | `L0`、`L1`、`L2`、`L3` |
| `freshness` | 由事件和时间推导的新鲜度 | `stale` |
| `syca` | CLI 命令名 | `syca capture` |
| `SYCA_HOME` | 用户数据目录环境变量 | `SYCA_HOME=/tmp/sycamore-dev` |
