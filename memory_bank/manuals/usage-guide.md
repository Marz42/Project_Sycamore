# Sycamore v0.17.0 使用指南

> 本地优先的能力校准与恢复 CLI。从碎片捕获到迁移训练，完整的学习闭环。

---

## 快速开始

```bash
# 环境要求：Python 3.12+，推荐 uv
uv sync
uv run syca init        # 初始化数据目录（~/.sycamore/）
uv run syca version     # 确认版本：syca 0.17.0
```

---

## 命令速查表

### 第 1 层 — 输入与升格

| 命令 | 用途 | 示例 |
|:--|:--|:--|
| `capture --cheat "..."` | 捕获命令片段 | `syca capture --cheat "grep -r pattern ."` |
| `capture --note "..."` | 捕获笔记/想法 | `syca capture --note "理解了递归的本质"` |
| `capture --link "URL"` | 捕获参考链接 | `syca capture --link "https://..."` |
| `inbox` | 查看待处理捕获项 | `syca inbox` |
| `clarify [<id>]` | 分析并建议 promote 参数 | `syca clarify` （分析最新） |
| `promote [--latest\|--index N\|<id>]` | 升格为能力节点 | `syca promote --index 1 --title "我能..." --domain shell` |
| `promote --type concept\|theorem\|process` | 指定节点类型 | `syca promote --type concept --domain philosophy` |

### 第 2 层 — 学习建模

| 命令 | 用途 | 示例 |
|:--|:--|:--|
| `edit <node-id>` | 逐块交互式编辑 | `syca edit abc12345` |
| `edit <node-id> --block <name>` | 编辑单个区块 | `syca edit abc --block "Core Idea"` |
| `edit <node-id> --suggest` | LLM 辅助草稿 | `syca edit abc --suggest` |
| `check <node-id>` | 检查完成度 | `syca check abc12345` |
| `status --completion draft` | 按完成度筛选 | `syca status --completion draft` |

### 第 3 层 — 复习与恢复

| 命令 | 用途 | 示例 |
|:--|:--|:--|
| `recover <node-id>` | 回忆训练（recall-first） | `syca recover abc12345` |
| `recover <node-id> --mode full` | 完整展示（旧行为） | `syca recover abc --mode full` |
| `recover <node-id> --pass\|--hard\|--easy` | 记录评分 | `syca recover abc --hard` |
| `recover <node-id> --fail --fail-type concept` | 记录失败+分类 | `syca recover abc --fail --fail-type concept` |
| `review <node-id>` | LLM 批判性评审 | `syca review abc12345` |
| `review <node-id> --dry-run` | 预览评审 payload | `syca review abc --dry-run` |
| `reviews list <node-id>` | 查看历史评审 | `syca reviews list abc12345` |
| `practice <node-id> --note "..."` | 追加实践记录 | `syca practice abc --note "今天用在了..."` |
| `level set <node-id> L2` | 更新声明等级 | `syca level set abc L2` |
| `schedule` | FSRS 到期复习列表 | `syca schedule` |
| `schedule --domain shell` | 按领域筛选 | `syca schedule --domain shell` |

### 第 4 层 — 迁移训练

| 命令 | 用途 | 示例 |
|:--|:--|:--|
| `transfer <node-id> --level A` | 变式识别 | `syca transfer abc --level A` |
| `transfer <node-id> --level B` | 边界判断 | `syca transfer abc --level B` |
| `transfer <node-id> --level C` | 组合任务 | `syca transfer abc --level C` |
| `transfer <node-id> --outcome success` | 记录结果 | `syca transfer abc --level A --outcome success` |
| `challenge` | 随机挑战 | `syca challenge` |
| `challenge --domain shell` | 域内随机挑战 | `syca challenge --domain shell` |

### 第 5 层 — 图谱与诊断

| 命令 | 用途 | 示例 |
|:--|:--|:--|
| `link <src> <tgt> --type prerequisite` | 建前置关系 | `syca link abc def --type prerequisite` |
| `link <src> <tgt> --type contrast` | 建混淆关系 | `syca link abc def --type contrast` |
| `link <src> <tgt> --type composition` | 建组合关系 | `syca link abc def --type composition` |
| `graph --domain shell` | 域内 ASCII 图 | `syca graph --domain shell` |
| `path --domain shell` | 学习路径链 | `syca path --domain shell` |

### 状态与诊断

| 命令 | 用途 | 示例 |
|:--|:--|:--|
| `status --stale` | 过期节点 | `syca status --stale` |
| `status --domain shell` | 域内新鲜度 | `syca status --domain shell` |
| `status --weak` | 薄弱画像 | `syca status --weak` |
| `status --cluster-risk` | 薄弱簇检测 | `syca status --cluster-risk` |
| `status --completion draft` | 按完成度筛选 | `syca status --completion draft` |
| `sync` | 同步索引 | `syca sync` |
| `doctor` | 一致性检查 | `syca doctor` |
| `query <term> --cheat` | 搜索 Cheatsheet | `syca query "grep" --cheat` |

---

## 典型工作流

### 场景 1：学 Linux 命令

```bash
# 工作中顺手捕获
syca capture --cheat "cd /var/log"
syca capture --cheat "grep ERROR /var/log/*.log"
syca capture --cheat "tail -f /var/log/app.log"

# 事后整理
syca inbox                              # 查看待处理
syca clarify                            # 分析建议
syca promote --index 1 --title "我能切换工作目录" --domain shell
syca promote --index 2 --title "我能用 grep 过滤日志" --domain shell
syca promote --index 3 --title "我能实时追踪日志" --domain shell

# 深度编码
syca edit <node-id>                     # 填 Core Idea、Steps、Pitfalls
syca check <node-id>                    # 检查完成度

# 几周后复习
syca schedule                           # 看哪些到期了
syca recover <node-id>                  # recall-first 回忆训练
syca recover <node-id> --hard           # 费力但记得

# 迁移训练
syca challenge --domain shell           # 随机挑战
syca transfer <node-id> --level C       # 组合任务

# 建关系
syca link <cd-id> <grep-id> --type composition
syca graph --domain shell               # 查看能力图
```

### 场景 2：读一本书（哲学/历史）

```bash
# 用 Session 模式（未来）或批量 capture
syca capture --note "农业革命其实是小麦驯化了人类"
syca capture --note "想象的共同体：民族是构建出来的"

# 升格为概念节点
syca clarify
syca promote --index 1 --title "我能解释农业革命的陷阱" --domain history --type concept
syca promote --index 2 --title "我能用想象的共同体分析民族认同" --domain history --type concept

# 填写概念模板
syca edit <node-id>                     # Core Thesis / Historical Context / Critique
```

### 场景 3：学数学/算法

```bash
# 捕获定理
syca capture --note "主定理：T(n) = aT(n/b) + f(n) 的三种情况"

# 升格
syca promote --index 1 --title "我能应用主定理分析递归复杂度" --domain algorithms --type theorem

# 编码
syca edit <node-id>                     # Formula / Intuition / Boundary Conditions
```

---

## 节点类型指南

| 类型 | 何时使用 | 核心区块 |
|:--|:--|:--|
| `capability` | 操作类：命令、工具、流程 | Steps / Pitfalls / Cheatsheet |
| `concept` | 理论类：框架、主义、思想 | Core Thesis / Historical Context / Critique |
| `theorem` | 公式类：数学、算法 | Formula / Intuition / Boundary Conditions |
| `process` | 系统类：工程、生物、化工 | Mechanism / Parameters / Disturbance Response |

---

## 完成度状态

| 状态 | 条件 | 可复习？ |
|:--|:--|:--:|
| `draft` | 模板占位未替换 | ❌ |
| `modeled` | Core Idea + Boundaries + Minimal Task 已填写 | ✅ |
| `contrasted` | 含 Contrast 区块 | ✅ |
| `reviewable` | modeled + contrasted + Cheatsheet 非空 | ✅ |

---

## LLM 配置（可选）

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

编辑 `~/.sycamore/config.toml`：
```toml
[llm]
enabled = true
provider = "deepseek"
model = "deepseek-v4-pro"
```

启用后：
- `syca review <node>` — 批判性评审
- `syca edit <node> --suggest` — 区块填充建议
- `syca transfer <node>` — 高质量场景生成

无 LLM 时所有命令仍可正常使用（mock 回退）。

---

## 数据目录

```text
~/.sycamore/
├── config.toml          # 用户配置
├── sycamore.db          # SQLite 索引与状态
├── nodes/               # Markdown 能力节点
└── reviews/             # ReviewRun JSON 归档
```

- Markdown 是权威正文
- SQLite 是索引与派生状态
- 备份只需复制整个目录或 `nodes/` + `sycamore.db`
